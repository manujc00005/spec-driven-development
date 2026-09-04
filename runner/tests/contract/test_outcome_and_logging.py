"""The render/notify condition, and the last-resort handler — spec 042 repairs.

Both reviewers landed on the same gap from different sides: the internal-error
path was unobserved output. `RunOutcome.ran` decides whether an invocation prints
a run result and whether the `--notify` sink hears about it, and nothing asserted
it; the redaction and the guarded log write that were added for security:SEC-004
had no test either.
"""

import io
import json
import os
import tempfile
import unittest

from sdd_runner import RunRequest, policy, run
from sdd_runner.log import RunLog
from sdd_runner.protocol import Diagnostic, RunOutcome
from tests import support


class TheOutcomeDisposition(unittest.TestCase):
    """`loop_completed` is stated by the core; `ran` reports it and nothing else.

    This class used to pin the defect. It asserted `ran == (terminal result AND no
    diagnostics)`, which was a faithful transcription of the pre-042 CLI *for the
    shapes the pre-042 CLI could produce* — and became wrong the moment a
    successful outcome carried a diagnostic, a shape that did not exist before
    T053. The tests were green and the behaviour was broken, which is what "411
    tests do not validate this combination" means.

    The fix is a contract change, not a special case: disposition and diagnostics
    are independent facts, and the core states both.
    """

    @staticmethod
    def _pre_042(outcome):
        """What the pre-042 CLI did, for the shapes it could produce."""
        return (outcome.result in ("DONE", "PAUSED", "ABORTED")
                and not outcome.diagnostics)

    # (name, outcome, expected disposition, comparable to the pre-042 CLI?)
    SHAPES = [
        ("gate refusal", RunOutcome(10, "REFUSED"), False, True),
        ("containment refusal", RunOutcome(10, "REFUSED",
                                           diagnostics=(Diagnostic("GATE", "x"),)),
         False, True),
        ("dry run", RunOutcome(0, "PLANNED"), False, True),
        ("converged", RunOutcome(0, "DONE", reason="core complete",
                                 loop_completed=True), True, True),
        ("paused", RunOutcome(11, "PAUSED", reason="human-gated",
                              loop_completed=True), True, True),
        ("cap abort", RunOutcome(12, "ABORTED", reason="domain",
                                 loop_completed=True), True, True),
        ("budget abort", RunOutcome(13, "ABORTED", reason="budget",
                                    loop_completed=True), True, True),
        ("backend precondition", RunOutcome(14, "REFUSED",
                                            diagnostics=(Diagnostic("BACKEND", "x"),)),
         False, True),
        ("internal error", RunOutcome(70, "ABORTED", resumable=False,
                                      diagnostics=(Diagnostic("INTERNAL", "x"),)),
         False, True),
        # The shape the pre-042 CLI could never produce, and the one the old
        # inference got wrong: the loop converged AND something went wrong beside it.
        ("converged with a lost transcript",
         RunOutcome(0, "DONE", reason="core complete", loop_completed=True,
                    diagnostics=(Diagnostic("INTERNAL", "run.jsonl lost 3 event(s)"),)),
         True, False),
    ]

    def test_every_shape_matches_the_declared_disposition(self):
        for name, outcome, expected, _comparable in self.SHAPES:
            with self.subTest(shape=name):
                self.assertEqual(outcome.loop_completed, expected)
                self.assertEqual(outcome.ran, expected, "`ran` must report, not decide")

    def test_the_baseline_shapes_still_match_what_the_pre_042_cli_did(self):
        for name, outcome, _expected, comparable in self.SHAPES:
            if not comparable:
                continue
            with self.subTest(shape=name):
                self.assertEqual(outcome.loop_completed, self._pre_042(outcome),
                                 "%s renders differently than it used to" % name)

    def test_the_new_shape_is_deliberately_not_what_the_old_inference_said(self):
        """The whole defect, stated as an assertion."""
        outcome = dict((n, o) for n, o, _e, _c in self.SHAPES)[
            "converged with a lost transcript"]
        self.assertFalse(self._pre_042(outcome),
                         "the old inference must disagree here, or there was no defect")
        self.assertTrue(outcome.loop_completed,
                        "a converged run must report its result even when something "
                        "else went wrong beside it")

    def test_disposition_never_consults_diagnostics(self):
        """Structural: the property may not grow a second condition (T057)."""
        import ast
        import inspect as _inspect
        import textwrap
        source = textwrap.dedent(_inspect.getsource(RunOutcome.ran.fget))
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute):
                self.assertNotEqual(node.attr, "diagnostics",
                                    "`ran` consults diagnostics again")
        with_diag = RunOutcome(0, "DONE", loop_completed=True,
                               diagnostics=(Diagnostic("INTERNAL", "x"),))
        without = RunOutcome(0, "DONE", loop_completed=True)
        self.assertEqual(with_diag.ran, without.ran)

    def test_a_result_value_alone_does_not_make_a_run(self):
        """It is not inferred from the result either."""
        self.assertFalse(RunOutcome(0, "DONE").loop_completed)
        self.assertFalse(RunOutcome(0, "ACTIVE").loop_completed)

    def test_the_dead_constant_is_gone(self):
        self.assertFalse(hasattr(policy, "OUTCOME_RESULTS"),
                         "a constant with no consumer was reinstated")


class TheLastResortHandler(unittest.TestCase):
    def _raising_run(self, message):
        from sdd_runner import loop as loop_mod
        original = loop_mod.Loop.run

        def boom(_self):
            raise RuntimeError(message)

        loop_mod.Loop.run = boom
        self.addCleanup(lambda: setattr(loop_mod.Loop, "run", original))

    def _run(self, tmp, message):
        repo, feature = support.make_repo(tmp)
        script = os.path.join(tmp, "s.json")
        with open(script, "w", encoding="utf-8") as fh:
            json.dump([support.fixture("worker_done.md")], fh)
        self._raising_run(message)
        outcome = run(RunRequest(repo=repo, feature=feature, backend="stub",
                                 stub_script=script, baseline=support.GREEN_BASELINE))
        return outcome, feature

    def test_it_reports_a_named_exit_code_and_is_not_resumable(self):
        with tempfile.TemporaryDirectory() as tmp:
            outcome, _feature = self._run(tmp, "boom")
        self.assertEqual(outcome.exit_code, 70)
        self.assertEqual(outcome.result, "ABORTED")
        self.assertFalse(outcome.resumable)
        self.assertFalse(outcome.ran, "an internal error never renders a run result")

    def test_it_records_the_exception_type_even_when_the_message_is_empty(self):
        """`str(exc)` on `raise ValueError()` is `''` — the operator got nothing."""
        with tempfile.TemporaryDirectory() as tmp:
            outcome, feature = self._run(tmp, "")
            with io.open(os.path.join(feature, "run.jsonl"), encoding="utf-8") as fh:
                events = [json.loads(line) for line in fh if line.strip()]
        self.assertIn("RuntimeError", outcome.diagnostics[0].text)
        internal = [e for e in events if e.get("event") == "internal-error"]
        self.assertTrue(internal)
        self.assertEqual(internal[0]["exception_type"], "RuntimeError")
        self.assertIn("Traceback", internal[0]["traceback"])

    def test_a_secret_in_the_exception_message_reaches_neither_sink(self):
        """The log redacted it and stderr did not — one line apart (security:SEC-004)."""
        secret = "sk-test-DEADBEEF-not-a-real-credential"
        os.environ["SDD_TEST_TOKEN"] = secret
        self.addCleanup(os.environ.pop, "SDD_TEST_TOKEN", None)
        with tempfile.TemporaryDirectory() as tmp:
            outcome, feature = self._run(tmp, "auth failed for %s" % secret)
            with io.open(os.path.join(feature, "run.jsonl"), encoding="utf-8") as fh:
                transcript = fh.read()
        self.assertNotIn(secret, outcome.diagnostics[0].text,
                         "the credential reached stderr")
        self.assertIn(RunLog.__module__ and "[REDACTED]", outcome.diagnostics[0].text)
        self.assertNotIn(secret, transcript)


class TheTranscriptIsEvidenceNotControlFlow(unittest.TestCase):
    """security:SEC-004's third clause — `RunLog.emit` now keeps its promise."""

    def test_a_failing_write_does_not_raise_into_the_caller(self):
        with tempfile.TemporaryDirectory() as tmp:
            unwritable = os.path.join(tmp, "no-such-dir", "run.jsonl")
            log = RunLog(unwritable, clock=lambda: 0)
            record = log.emit("something", detail="happened")
        self.assertEqual(record["event"], "something")
        self.assertEqual(log.events[-1]["event"], "something",
                         "the event is still in memory when the file is not")
        self.assertTrue(log.write_failures, "the loss must be recorded, not silent")

    def test_the_docstring_is_now_implemented(self):
        self.assertIn("Never raises into the loop on a write failure", RunLog.__doc__)

    def test_the_loss_stops_the_run_rather_than_annotating_it(self):
        """security:SEC-008, then D015 — silence was one wrong answer; a footnote was the other.

        Swallowing the write failure stopped a coded exit becoming a traceback, and
        then recorded the loss only in memory: an anti-forensics primitive handed to
        the party the log exists to record. The first repair surfaced it as a
        diagnostic **on an otherwise successful outcome**, which the maintainer
        refused — a run with no audit trail must not report success. It is now a
        gate: exit 70, `ABORTED`, not resumable, and the loop stops at the first
        failed write.
        """
        with tempfile.TemporaryDirectory() as tmp:
            repo, feature = support.make_repo(tmp)
            script = os.path.join(tmp, "s.json")
            with open(script, "w", encoding="utf-8") as fh:
                json.dump(([support.fixture("worker_done.md"), support.approve_block()] * 2)
                          + support.finalization_flat(), fh)
            # `run.jsonl` cannot be appended to: a directory now occupies its name.
            os.mkdir(os.path.join(feature, "run.jsonl"))
            outcome = run(RunRequest(repo=repo, feature=feature, backend="stub",
                                     stub_script=script, baseline=support.GREEN_BASELINE))
        self.assertEqual(outcome.exit_code, 70)
        self.assertEqual(outcome.result, "ABORTED")
        self.assertFalse(outcome.loop_completed)
        self.assertFalse(outcome.resumable)
        self.assertTrue(outcome.diagnostics, "a lost transcript reached nobody")
        text = " ".join(d.text for d in outcome.diagnostics)
        self.assertIn("audit transcript unavailable", text)
        self.assertNotIn("Traceback", text)

    def test_a_run_whose_transcript_is_intact_converges_silently(self):
        """The signal must be a signal, not noise on every run."""
        with tempfile.TemporaryDirectory() as tmp:
            repo, feature = support.make_repo(tmp)
            script = os.path.join(tmp, "s.json")
            with open(script, "w", encoding="utf-8") as fh:
                json.dump(([support.fixture("worker_done.md"), support.approve_block()] * 2)
                          + support.finalization_flat(), fh)
            outcome = run(RunRequest(repo=repo, feature=feature, backend="stub",
                                     stub_script=script, baseline=support.GREEN_BASELINE))
        self.assertEqual(outcome.diagnostics, ())
        self.assertTrue(outcome.ran)


class UnreadableInputsGetACodeNotATraceback(unittest.TestCase):
    """security:SEC-006 and SEC-009(b) — the branches nothing exercised.

    `TASKS.md` and `SPEC.md` are read at three points before the loop, and each
    read escaped as a traceback and exit 1 until it was wrapped. The repairs were
    made one at a time and each was checked off against a `Verify:` clause no test
    performed.
    """

    def _commit_bytes(self, repo, relative, payload):
        import subprocess
        path = os.path.join(repo, relative)
        with open(path, "wb") as fh:
            fh.write(payload)
        subprocess.run(["git", "-C", repo, "add", "-A"], capture_output=True)
        subprocess.run(["git", "-C", repo, "commit", "-qm", "corrupt"], capture_output=True)

    def test_a_non_utf8_tasks_file_returns_a_code(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, feature = support.make_repo(tmp)
            self._commit_bytes(repo, os.path.join("specs", "features", "900-fixture",
                                                  "TASKS.md"),
                               b"# Tasks\n- [ ] T001 - \xff\xfe bad bytes\n")
            outcome = run(RunRequest(repo=repo, feature=feature, dry_run=True))
        self.assertIn(outcome.exit_code, (10,))
        self.assertTrue(outcome.diagnostics or outcome.gate.refusals)

    def test_a_non_utf8_spec_file_returns_a_code(self):
        """This read runs on EVERY entry, before the one that was widened first."""
        with tempfile.TemporaryDirectory() as tmp:
            repo, feature = support.make_repo(tmp)
            self._commit_bytes(repo, os.path.join("specs", "features", "900-fixture",
                                                  "SPEC.md"),
                               b"# Spec\n\n## Status\n\nReady \xff\xfe\n")
            outcome = run(RunRequest(repo=repo, feature=feature, dry_run=True))
        self.assertEqual(outcome.exit_code, 10)
        self.assertTrue(outcome.diagnostics)
        self.assertIn("could not be read", outcome.diagnostics[0].text)


if __name__ == "__main__":
    unittest.main()
