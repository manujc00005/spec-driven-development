"""A run without a durable record is not a run — spec 042 D015.

The maintainer's policy, and the reasoning behind it: a scheduler must be able to
trust the exit code. Two outcomes were refused, both of which the tree has had at
some point:

  * `main`'s: the first `log.emit` raises, the handler's second `emit` raises
    again, and the process dies with a traceback and **exit 1** — reproduced from
    a temporary extraction of `main`, not assumed;
  * T053's: exit **0**, `run result: DONE` and `run-finished`, with the lost
    transcript mentioned on stderr — a converged run reported successfully with
    no evidence for anything it did.

What replaces them: the loop stops at the **first** failed write, before any
further delegation, and the invocation reports `INTERNAL_ERROR` / `ABORTED` /
`resumable=False` with a redacted diagnostic and no traceback.
"""

import ast
import io
import json
import os
import tempfile
import unittest

from sdd_runner import RunRequest, exits, loop as loop_mod, run
from sdd_runner.log import AuditUnavailable, RunLog
from tests import support


class OnlyOneRouteToTheLog(unittest.TestCase):
    """One bypass is all it takes for a run to continue past its own record."""

    def _loop_tree(self):
        with io.open(loop_mod.__file__, encoding="utf-8") as fh:
            return ast.parse(fh.read())

    def test_no_direct_log_emit_outside_the_wrapper(self):
        offenders = []
        for node in ast.walk(self._loop_tree()):
            if not isinstance(node, ast.FunctionDef) or node.name == "_emit":
                continue
            for inner in ast.walk(node):
                if (isinstance(inner, ast.Call) and isinstance(inner.func, ast.Attribute)
                        and inner.func.attr == "emit"
                        and isinstance(inner.func.value, ast.Attribute)
                        and inner.func.value.attr == "log"):
                    offenders.append("%s (line %d)" % (node.name, inner.lineno))
        self.assertEqual(offenders, [],
                         "these bypass the audit gate: %s" % offenders)

    def test_the_wrapper_exists_and_is_the_one_that_calls_the_writer(self):
        wrapper = [n for n in ast.walk(self._loop_tree())
                   if isinstance(n, ast.FunctionDef) and n.name == "_emit"]
        self.assertEqual(len(wrapper), 1)
        calls = [c for c in ast.walk(wrapper[0])
                 if isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute)
                 and c.func.attr == "emit"]
        self.assertTrue(calls, "the wrapper no longer writes anything")

    def test_the_loop_still_records_a_lot(self):
        """A guard over zero call sites passes for the wrong reason."""
        with io.open(loop_mod.__file__, encoding="utf-8") as fh:
            source = fh.read()
        self.assertGreater(source.count("self._emit("), 30)


class TheWriterKeepsItsPromiseAndTheLoopDecides(unittest.TestCase):
    """Two responsibilities, deliberately separate."""

    def test_the_writer_never_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = RunLog(os.path.join(tmp, "nope", "run.jsonl"), clock=lambda: 0)
            record = log.emit("x", detail="y")
        self.assertEqual(record["event"], "x")
        self.assertTrue(log.write_failures)

    def test_the_wrapper_raises_on_the_first_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, feature = support.make_repo(tmp)
            log = RunLog(os.path.join(tmp, "nope", "run.jsonl"), clock=lambda: 0)
            loop = loop_mod.Loop(repo, feature, backend=None, log=log)
            with self.assertRaises(AuditUnavailable) as caught:
                loop._emit("plan", unchecked=2)
        self.assertEqual(caught.exception.event, "plan")
        self.assertTrue(caught.exception.failures)

    def test_the_wrapper_is_transparent_when_the_write_succeeds(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, feature = support.make_repo(tmp)
            log = RunLog(os.path.join(tmp, "run.jsonl"), clock=lambda: 0)
            loop = loop_mod.Loop(repo, feature, backend=None, log=log)
            record = loop._emit("plan", unchecked=2)
        self.assertEqual(record["event"], "plan")
        self.assertEqual(log.write_failures, [])


class AnUnwritableTranscriptStopsTheRun(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo, self.feature = support.make_repo(self.tmp.name)

    def _script(self, name="s.json"):
        path = os.path.join(self.tmp.name, name)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(([support.fixture("worker_done.md"), support.approve_block()] * 2)
                      + support.finalization_flat(), fh)
        return path

    def _run(self):
        return run(RunRequest(repo=self.repo, feature=self.feature, backend="stub",
                              stub_script=self._script(),
                              baseline=support.GREEN_BASELINE))

    def test_the_whole_policy_on_one_run(self):
        os.mkdir(os.path.join(self.feature, "run.jsonl"))
        outcome = self._run()

        with self.subTest("exit code a scheduler can branch on"):
            self.assertEqual(outcome.exit_code, exits.INTERNAL_ERROR)
        with self.subTest("not a completed run"):
            self.assertEqual(outcome.result, "ABORTED")
            self.assertFalse(outcome.loop_completed)
            self.assertFalse(outcome.ran)
        with self.subTest("not resumable without a maintainer"):
            self.assertFalse(outcome.resumable)
        with self.subTest("an explicit diagnostic, redacted, with no traceback"):
            self.assertTrue(outcome.diagnostics)
            text = outcome.diagnostics[0].text
            self.assertIn("audit transcript unavailable", text)
            self.assertNotIn("Traceback", text)
            self.assertEqual(outcome.diagnostics[0].channel, "INTERNAL")

    def test_it_stops_before_any_further_delegation(self):
        """The point of stopping at the FIRST failure rather than at the end."""
        os.mkdir(os.path.join(self.feature, "run.jsonl"))
        outcome = self._run()
        self.assertEqual(outcome.exit_code, exits.INTERNAL_ERROR)
        state = os.path.join(self.feature, "ORCHESTRATION.md")
        if os.path.exists(state):
            with io.open(state, encoding="utf-8") as fh:
                body = fh.read()
            self.assertNotIn("| A-001 ", body,
                             "a delegation was attempted after the audit trail was gone")

    def test_a_run_with_an_intact_log_still_converges_and_records(self):
        """The control. A gate that blocks everything is not a gate.

        It asserts convergence and a written transcript, **not** notification: this
        test installs no notifier, and its previous name claimed something it did
        not test (`maintainer:MNT-009`). The notification side is covered end to
        end by `tests/integration/test_transcript_loss_reporting.py`, which runs
        the CLI with a real `--notify` sink.
        """
        outcome = self._run()
        self.assertEqual(outcome.exit_code, exits.OK, outcome.reason)
        self.assertEqual(outcome.result, "DONE")
        self.assertTrue(outcome.loop_completed)
        self.assertEqual(outcome.diagnostics, ())
        with io.open(os.path.join(self.feature, "run.jsonl"), encoding="utf-8") as fh:
            self.assertGreater(len([l for l in fh if l.strip()]), 5,
                               "the transcript is the evidence; it must be there")


if __name__ == "__main__":
    unittest.main()
