"""What a run reports, and when it is entitled to report anything at all.

Spec 042 T057, **narrowed by T060/D015**. T057 fixed a real defect — a converged
run stopped printing `run result:` and stopped emitting `run-finished` because the
disposition was inferred from the absence of diagnostics — and fixed it in a way
the maintainer then refused: it made a run whose `run.jsonl` had been lost report
exit 0, `DONE` and `run-finished` anyway.

D015 settles it: an audit failure is a **gate**, not a footnote. A run without a
durable record is not a run, so it reports exit 70 / `ABORTED` / not resumable,
and the loop stops at the first failed write. The disposition contract T057
introduced is unchanged and still right; what changed is that this path no longer
reaches a successful outcome at all. The audit-gate behaviour is covered by
`tests/contract/test_audit_gate.py`; what remains here is the disposition contract
and the internal-error baseline.

Driven through the real CLI in a real subprocess, with a real `--notify` sink,
because that is where the coupling lived. `--notify` is executed without a shell
with a fixed argv and the event delivered as JSON on stdin, so the sink here is a
small script that appends what it reads.
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest

from sdd_runner import exits
from tests.support import GREEN_BASELINE, approve_block, finalization_flat, fixture, make_repo

RUNNER_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def converging_script():
    return ([fixture("worker_done.md"), approve_block()] * 2) + finalization_flat()


class ConvergedRunWithALostTranscript(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo, self.feature_dir = make_repo(self.tmp.name)
        self.sink = os.path.join(self.tmp.name, "notified.jsonl")

    def _notify_script(self):
        """A sink that appends whatever arrives on stdin, one line per call."""
        path = os.path.join(self.tmp.name, "sink.py")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("import sys\n"
                     "open(%r, 'a').write(sys.stdin.read() + '\\n')\n" % self.sink)
        return path

    def _script(self, payload):
        path = os.path.join(self.tmp.name, "script.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh)
        return path

    def _run(self, *extra):
        env = dict(os.environ, PYTHONPATH=RUNNER_ROOT)
        argv = [sys.executable, "-m", "sdd_runner",
                "--repo", self.repo, "--feature", "specs/features/900-fixture",
                "--backend", "stub", "--stub-script", self._script(converging_script()),
                "--baseline", GREEN_BASELINE[0],
                "--notify", "%s %s" % (sys.executable, self._notify_script())]
        with open(os.devnull, "rb") as devnull:
            return subprocess.run(argv + list(extra), stdin=devnull, capture_output=True,
                                  text=True, env=env, timeout=180)

    def _events(self):
        if not os.path.exists(self.sink):
            return []
        with open(self.sink, encoding="utf-8") as fh:
            return [json.loads(line) for line in fh if line.strip()]

    def _break_the_transcript(self):
        """`run.jsonl` cannot be appended to: a directory occupies its name."""
        os.mkdir(os.path.join(self.feature_dir, "run.jsonl"))

    # -- the combination that was missing ---------------------------------
    def test_a_lost_transcript_is_a_gate_not_a_footnote_on_a_success(self):
        """Superseded expectation, kept as the record of what changed (D015).

        This test asserted exit 0, `run result: DONE` and one `run-finished` on
        this path — T057's answer, and the one the maintainer refused: a scheduler
        must be able to trust the exit code, and an exit 0 that says DONE while the
        audit trail is gone is a lie it will believe. The assertions below are the
        inverse, and they are here rather than deleted so the change is visible in
        the file that used to claim the opposite.
        """
        self._break_the_transcript()
        proc = self._run()

        with self.subTest("exit code a scheduler can branch on"):
            self.assertEqual(proc.returncode, exits.INTERNAL_ERROR, proc.stderr)
        with self.subTest("stderr carries the audit diagnostic, with no traceback"):
            self.assertIn("audit transcript unavailable", proc.stderr)
            self.assertNotIn("Traceback", proc.stderr)
        with self.subTest("no terminal result is reported"):
            self.assertNotIn("run result:", proc.stdout)
        with self.subTest("zero run-finished reaches the sink"):
            self.assertEqual([e for e in self._events()
                              if e.get("event") == "run-finished"], [])

    def test_an_intact_run_converges_reports_and_notifies(self):
        """The control, and the reason the gate is a gate rather than a blanket refusal."""
        proc = self._run()
        self.assertEqual(proc.returncode, exits.OK, proc.stderr)
        self.assertIn("run result: DONE", proc.stdout)
        self.assertNotIn("audit transcript", proc.stderr)
        finished = [e for e in self._events() if e.get("event") == "run-finished"]
        self.assertEqual(len(finished), 1)
        self.assertEqual(finished[0]["result"], "DONE")


class AnInternalErrorStillReportsNothingTerminal(unittest.TestCase):
    """The baseline for exit 70, preserved exactly — it is not a completed run.

    An exception can be raised *after* the loop starts, and the pre-042 CLI
    returned from that path before printing or notifying. That is why the field is
    `loop_completed` and not `execution_started`.

    **This class runs the CLI adapter, with a notifier installed.** Its first
    version called `protocol.run()` directly and built a sink path it never used,
    so the half of the claim that matters — *no `run-finished` is emitted* — was
    asserted by nothing at all: the notifier lives in `__main__`, and no `__main__`
    ran (`maintainer:MNT-003`). A negative assertion about a component the test
    never instantiates is not evidence.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo, self.feature_dir = make_repo(self.tmp.name)
        self.sink = os.path.join(self.tmp.name, "notified.jsonl")

    def _notify_script(self):
        path = os.path.join(self.tmp.name, "sink.py")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("import sys\n"
                     "open(%r, 'a').write(sys.stdin.read() + '\\n')\n" % self.sink)
        return path

    def _events(self):
        if not os.path.exists(self.sink):
            return []
        with open(self.sink, encoding="utf-8") as fh:
            return [json.loads(line) for line in fh if line.strip()]

    def _run_cli_with_a_raising_loop(self):
        """`__main__.main` in-process, so the patch holds; the sink is a real subprocess."""
        import io as _io
        from contextlib import redirect_stderr, redirect_stdout
        from sdd_runner import loop as loop_mod
        from sdd_runner.__main__ import main

        original = loop_mod.Loop.run

        def boom(_self):
            raise RuntimeError("deliberate failure for the internal-error CLI test")

        loop_mod.Loop.run = boom
        self.addCleanup(lambda: setattr(loop_mod.Loop, "run", original))

        script = os.path.join(self.tmp.name, "s.json")
        with open(script, "w", encoding="utf-8") as fh:
            json.dump([fixture("worker_done.md")], fh)

        out, err = _io.StringIO(), _io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = main(["--repo", self.repo, "--feature", "specs/features/900-fixture",
                         "--backend", "stub", "--stub-script", script,
                         "--baseline", GREEN_BASELINE[0],
                         "--notify", "%s %s" % (sys.executable, self._notify_script())])
        return code, out.getvalue(), err.getvalue()

    def test_the_cli_exits_70_reports_nothing_terminal_and_notifies_nobody(self):
        code, stdout, stderr = self._run_cli_with_a_raising_loop()

        with self.subTest("exit code"):
            self.assertEqual(code, exits.INTERNAL_ERROR)
        with self.subTest("the diagnostic reaches stderr"):
            self.assertIn("[INTERNAL]", stderr)
            self.assertIn("RuntimeError", stderr)
        with self.subTest("no terminal result is reported"):
            self.assertNotIn("run result:", stdout)
            self.assertNotIn("reason:", stdout)
        with self.subTest("zero run-finished events"):
            self.assertEqual([e for e in self._events()
                              if e.get("event") == "run-finished"], [])

    def test_the_notifier_was_really_installed(self):
        """Otherwise the assertion above passes because nothing could ever fire.

        The sink must be reachable: a converged run through the same code path
        delivers exactly one event to it. Without this, `assertEqual([], [])` is
        satisfied by a notifier that does not exist — which is the defect
        `maintainer:MNT-003` recorded.
        """
        import io as _io
        from contextlib import redirect_stderr, redirect_stdout
        from sdd_runner.__main__ import main

        script = os.path.join(self.tmp.name, "s.json")
        with open(script, "w", encoding="utf-8") as fh:
            json.dump(converging_script(), fh)
        out, err = _io.StringIO(), _io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = main(["--repo", self.repo, "--feature", "specs/features/900-fixture",
                         "--backend", "stub", "--stub-script", script,
                         "--baseline", GREEN_BASELINE[0],
                         "--notify", "%s %s" % (sys.executable, self._notify_script())])
        self.assertEqual(code, exits.OK, err.getvalue())
        self.assertEqual(len([e for e in self._events()
                              if e.get("event") == "run-finished"]), 1,
                         "the sink is unreachable, so the negative assertion proves nothing")

    def test_the_outcome_itself_says_the_loop_did_not_complete(self):
        from sdd_runner import RunRequest, loop as loop_mod, run

        original = loop_mod.Loop.run
        loop_mod.Loop.run = lambda _self: (_ for _ in ()).throw(
            RuntimeError("deliberate failure"))
        self.addCleanup(lambda: setattr(loop_mod.Loop, "run", original))

        script = os.path.join(self.tmp.name, "s2.json")
        with open(script, "w", encoding="utf-8") as fh:
            json.dump([fixture("worker_done.md")], fh)
        outcome = run(RunRequest(repo=self.repo, feature=self.feature_dir,
                                 backend="stub", stub_script=script,
                                 baseline=GREEN_BASELINE))

        self.assertEqual(outcome.exit_code, exits.INTERNAL_ERROR)
        self.assertEqual(outcome.result, "ABORTED")
        self.assertTrue(outcome.diagnostics)
        self.assertIn("RuntimeError", outcome.diagnostics[0].text)
        self.assertFalse(outcome.loop_completed,
                         "an exception is not a completed run, whenever it was raised")
        self.assertFalse(outcome.ran)
        self.assertFalse(outcome.resumable)


class TheNotifyConditionIsGuarded(unittest.TestCase):
    """`maintainer:MNT-003` — the consumer side of the disposition contract.

    The producer is mutation-covered: falsifying `loop_completed=True` turns the
    suite red. The *consumer* was not: dropping `outcome.loop_completed` from
    `__main__`'s notify condition would make an internal error emit
    `run-finished`, and nothing checked the condition's shape.
    """

    def test_the_notify_condition_reads_loop_completed(self):
        import ast
        import io as _io
        import sdd_runner.__main__ as cli
        with _io.open(cli.__file__, encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        main_fn = next(n for n in tree.body
                       if isinstance(n, ast.FunctionDef) and n.name == "main")
        guards = []
        for node in ast.walk(main_fn):
            if isinstance(node, ast.If):
                names = {a.attr for a in ast.walk(node.test)
                         if isinstance(a, ast.Attribute)}
                if "notify" in ast.dump(node.test) or "awaiting_human" in names:
                    guards.append(names)
        self.assertTrue(guards, "the notify branch moved; re-derive this guard")
        self.assertTrue(any("loop_completed" in g for g in guards),
                        "the notify condition no longer requires loop_completed: an "
                        "internal error would emit run-finished")
        self.assertTrue(any("awaiting_human" in g for g in guards),
                        "a paused run would be notified twice")


if __name__ == "__main__":
    unittest.main()
