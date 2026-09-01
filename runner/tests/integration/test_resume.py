"""Idempotent re-entry — spec 031 FR-011, spec 040 T013.

Deterministic, stub backend, no provider call. The property every test here
defends: **re-entry never re-delegates completed work, never duplicates a
finding, never resets a counter, and never continues on a state it could not
read.**
"""

import itertools
import os
import re
import socket
import tempfile
import unittest

from sdd_runner import exits, resume, state
from sdd_runner.backends.stub import StubBackend
from sdd_runner.log import RunLog
from sdd_runner.loop import Loop
from tests.support import GREEN_BASELINE, TASKS, finalization_flat, fixture, make_repo

HOST = socket.gethostname()
DEAD_PID = 999_999          # not a live process; asserted below


class ResumeHarness(unittest.TestCase):
    """Builds one repo that several sequential runs share, as a real resume would."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo, self.feature_dir = make_repo(self.tmp.name, tasks=TASKS)
        self.counter = itertools.count()

    @property
    def state_path(self):
        return os.path.join(self.feature_dir, "ORCHESTRATION.md")

    def run_once(self, script, max_iterations=3, max_delegations=None, pid=None, notify=None):
        stub = StubBackend(script=list(script))
        log = RunLog(os.path.join(self.feature_dir, "run.jsonl"),
                     clock=lambda: next(self.counter), environ={})
        loop = Loop(self.repo, self.feature_dir, stub, log,
                    max_iterations=max_iterations, max_delegations=max_delegations,
                    clock=lambda: 0, notify=notify, hostname=HOST,
                    pid=pid if pid is not None else os.getpid(),
                    baseline_cmd=GREEN_BASELINE)
        return loop.run(), stub, loop, log

    def doc(self):
        return state.Orchestration.load(self.state_path)

    def fields(self):
        return state.parse_fields(self.doc().body("State"))

    def tasks_text(self):
        with open(os.path.join(self.feature_dir, "TASKS.md"), encoding="utf-8") as fh:
            return fh.read()

    def set_result(self, result, resumable="yes"):
        doc = self.doc()
        doc.set_body("Run result", "\n%s\n\nresumable: %s\n\n" % (result, resumable))
        doc.save(self.state_path)

    def set_field(self, key, value):
        doc = self.doc()
        fields = state.parse_fields(doc.body("State"))
        fields[key] = value
        doc.set_body("State", state.render_fields(fields))
        doc.save(self.state_path)


class DeadPidAssumption(unittest.TestCase):
    def test_the_fixture_pid_really_is_dead(self):
        """If this ever fails the resume tests are testing nothing."""
        self.assertFalse(resume._pid_alive(DEAD_PID))


class ResumeAfterCompletedTask(ResumeHarness):
    def test_a_completed_task_is_not_re_delegated(self):
        # Run 1: T001 converges, then the script runs out mid-T002.
        first, stub1, _loop, _log = self.run_once([
            fixture("worker_done.md"), fixture("reviewer_approve.md"),
        ])
        self.assertEqual(first.code, exits.BACKEND_PRECONDITION)   # stub exhausted on T002
        self.assertEqual(stub1.invocations, 3)
        self.assertEqual(self.fields()["completed tasks"], "T001")

        # Run 2: only T002 may be dispatched.
        second, stub2, loop2, log2 = self.run_once(
            [fixture("worker_done.md"), fixture("reviewer_approve.md")] + finalization_flat())
        self.assertEqual(second.code, exits.OK)
        self.assertEqual(stub2.invocations, 2 + len(finalization_flat()),
                         "T001 must not be re-delegated")
        plan = [e for e in log2.events if e["event"] == "plan"][0]
        # T001 does not even appear as pending: converging checked its box in
        # TASKS.md, which is what 031's first DONE condition reads.
        self.assertEqual(plan["runnable"], ["T002"])
        self.assertIn("- [x] T001", self.tasks_text())
        self.assertEqual(self.fields()["completed tasks"], "T001, T002")

    def test_the_budget_carries_over_and_never_resets(self):
        self.run_once([fixture("worker_done.md"), fixture("reviewer_approve.md")])
        used_after_first = int(self.fields()["delegations used"])
        self.assertGreater(used_after_first, 0)

        _second, _stub, loop2, log2 = self.run_once([
            fixture("worker_done.md"), fixture("reviewer_approve.md"),
        ])
        resume_event = [e for e in log2.events if e["event"] == "resume"][0]
        self.assertEqual(resume_event["budget_used"], used_after_first)
        self.assertGreater(loop2.budget.used, used_after_first)


class ResumeAfterBlockedTask(ResumeHarness):
    def test_a_human_gated_block_pauses_and_re_entry_refuses_while_it_is_open(self):
        sent = []
        first, stub1, _loop, _log = self.run_once([fixture("worker_blocked_human.md")],
                                                  notify=sent.append)
        self.assertEqual(first.code, exits.HUMAN_ESCALATION)
        self.assertEqual(self.doc().run_result(), "PAUSED")
        self.assertEqual(len(sent), 1)

        second, stub2, _loop2, log2 = self.run_once([fixture("worker_done.md")])
        self.assertEqual(second.code, exits.HUMAN_ESCALATION)
        self.assertEqual(stub2.invocations, 0,
                         "no work may be dispatched while an escalation waits")
        refusal = [e for e in log2.events if e["event"] == "refused"][0]
        self.assertEqual(refusal["kind"], "open-escalation")

    def test_once_the_escalation_is_answered_the_task_is_retried_not_skipped(self):
        self.run_once([fixture("worker_blocked_human.md")])
        doc = self.doc()
        doc.set_body("Escalations", "\n- **resolved** (money) on T001: answered in DECISIONS.md\n\n")
        doc.save(self.state_path)

        second, stub2, _loop2, log2 = self.run_once(
            [fixture("worker_done.md"), fixture("reviewer_approve.md"),
             fixture("worker_done.md"), fixture("reviewer_approve.md")] + finalization_flat())
        self.assertEqual(second.code, exits.OK)
        plan = [e for e in log2.events if e["event"] == "plan"][0]
        self.assertEqual(plan["skipped"], [], "a blocked task was never completed")
        self.assertEqual(plan["runnable"], ["T001", "T002"])

    def test_a_technical_block_stops_the_run_and_completes_nothing(self):
        outcome, stub, _loop, _log = self.run_once([
            fixture("worker_blocked.md"), fixture("reviewer_approve.md"),
            fixture("worker_done.md"), fixture("reviewer_approve.md"),
        ])
        # T001 came back BLOCKED. The run stops there rather than reviewing work
        # the worker never did, and nothing is marked complete.
        self.assertEqual(outcome.code, exits.HUMAN_ESCALATION)
        self.assertEqual(self.fields()["completed tasks"], "")
        self.assertEqual(stub.invocations, 1, "no review is dispatched for un-done work")

    def test_a_blocked_task_is_retried_from_scratch_on_re_entry(self):
        self.run_once([fixture("worker_blocked.md")])
        _outcome, _stub, _loop, log2 = self.run_once([
            fixture("worker_done.md"), fixture("reviewer_approve.md"),
            fixture("worker_done.md"), fixture("reviewer_approve.md"),
        ])
        plan = [e for e in log2.events if e["event"] == "plan"][0]
        self.assertEqual(plan["skipped"], [])
        self.assertEqual(plan["runnable"], ["T001", "T002"])


class ResumeWithExhaustedBudget(ResumeHarness):
    def test_re_entry_without_an_increase_refuses_to_dispatch(self):
        first, _stub, _loop, _log = self.run_once(
            [fixture("worker_done.md")] * 4, max_delegations=2)
        self.assertEqual(first.code, exits.BUDGET_EXHAUSTED)

        second, stub2, _loop2, _log2 = self.run_once(
            [fixture("worker_done.md")] * 4, max_delegations=2)
        self.assertEqual(second.code, exits.BUDGET_EXHAUSTED)
        self.assertEqual(stub2.invocations, 0, "an exhausted budget dispatches nothing")

    def test_a_lower_cap_on_re_entry_is_refused_outright(self):
        self.run_once([fixture("worker_done.md")] * 4, max_delegations=4)
        second, stub2, _loop2, _log2 = self.run_once(
            [fixture("worker_done.md")] * 4, max_delegations=2)
        self.assertEqual(second.code, exits.STATE_UNRESUMABLE)
        self.assertIn("only INCREASE", second.remediation)
        self.assertEqual(stub2.invocations, 0)

    def test_an_explicit_increase_resumes_and_is_logged_as_a_cap_change(self):
        self.run_once([fixture("worker_done.md")] * 4, max_delegations=2)
        second, stub2, loop2, _log2 = self.run_once(
            [fixture("worker_done.md"), fixture("reviewer_approve.md"),
             fixture("worker_done.md"), fixture("reviewer_approve.md")] + finalization_flat(),
            max_delegations=20)
        self.assertEqual(second.code, exits.OK)
        self.assertEqual(loop2.budget.cap, 20)
        self.assertIn("max-delegations 2 -> 20", self.doc().body("Cap changes"))


class ResumeWithCorruptState(ResumeHarness):
    def _expect_block(self, needle):
        outcome, stub, _loop, log = self.run_once([fixture("worker_done.md")] * 4)
        self.assertEqual(outcome.code, exits.STATE_UNRESUMABLE)
        self.assertEqual(stub.invocations, 0, "a corrupt state must dispatch nothing")
        self.assertTrue(outcome.remediation, "a block must tell the human what to do")
        self.assertIn(needle, outcome.reason)
        return outcome

    def setUp(self):
        super().setUp()
        self.run_once([fixture("worker_done.md"), fixture("reviewer_approve.md")])
        self.set_result("PAUSED")

    def test_missing_budget_field(self):
        doc = self.doc()
        fields = state.parse_fields(doc.body("State"))
        del fields["delegations used"]
        doc.set_body("State", state.render_fields(fields))
        doc.save(self.state_path)
        self._expect_block("delegations used")

    def test_non_numeric_budget_field(self):
        self.set_field("delegations used", "lots")
        self._expect_block("not a number")

    def test_budget_used_above_its_cap(self):
        self.set_field("delegations used", "9999")
        self._expect_block("against a cap of")

    def test_malformed_counters_field(self):
        self.set_field("counters", "domain=streak:banana")
        self._expect_block("not a number")

    def test_state_and_attempts_disagree_about_completed_tasks(self):
        self.set_field("completed tasks", "T001, T002")
        self._expect_block("disagrees with itself")

    def test_corrupt_findings_table(self):
        doc = self.doc()
        doc.set_body("Findings", doc.body("Findings").rstrip() + "\n| only | two |\n\n")
        doc.save(self.state_path)
        self._expect_block("corrupt")

    def test_unknown_lifecycle_value_in_attempts(self):
        doc = self.doc()
        body = doc.body("Attempts").replace("VERIFIED", "MAYBE", 1)
        doc.set_body("Attempts", body)
        doc.save(self.state_path)
        self._expect_block("lifecycle")

    def test_a_document_written_by_another_executor_is_refused(self):
        self.set_field("writer", "sdd-orchestrate")
        outcome = self._expect_block("not written by this runner")
        self.assertIn("executor that started it", outcome.remediation)

    def test_a_terminal_abort_is_not_re_entered(self):
        self.set_result("ABORTED", resumable="no")
        self._expect_block("terminal abort")

    def test_a_completed_run_is_not_re_entered(self):
        self.set_result("DONE")
        self._expect_block("completed run")

    def test_an_unreadable_run_result_blocks(self):
        doc = self.doc()
        doc.set_body("Run result", "\nwho knows\n\n")
        doc.save(self.state_path)
        self._expect_block("no recognizable Run result")


class ConcurrencyAndInterruption(ResumeHarness):
    def setUp(self):
        super().setUp()
        self.run_once([fixture("worker_done.md"), fixture("reviewer_approve.md")])

    def test_a_live_active_run_is_rejected(self):
        self.set_result("ACTIVE")
        self.set_field("runner pid", str(os.getpid()))
        self.set_field("runner host", HOST)
        outcome, stub, _loop, log = self.run_once([fixture("worker_done.md")] * 4)
        self.assertEqual(outcome.code, exits.CONCURRENT_RUN)
        self.assertEqual(stub.invocations, 0)
        self.assertEqual([e for e in log.events if e["event"] == "refused"][0]["kind"],
                         "concurrent")

    def test_an_interrupted_run_whose_writer_is_gone_resumes(self):
        """ACTIVE + dead pid on this host == SIGTERM, not a second runner."""
        self.set_result("ACTIVE")
        self.set_field("runner pid", str(DEAD_PID))
        self.set_field("runner host", HOST)
        outcome, stub, _loop, log = self.run_once(
            [fixture("worker_done.md"), fixture("reviewer_approve.md")] + finalization_flat())
        self.assertEqual(outcome.code, exits.OK)
        resumed = [e for e in log.events if e["event"] == "resume"][0]
        self.assertTrue(resumed["recovered_from_interrupt"])
        self.assertEqual(resumed["completed"], ["T001"])
        self.assertEqual(stub.invocations, 2 + len(finalization_flat()),
                         "only the unfinished task is re-delegated")

    def test_an_active_run_on_another_host_blocks_rather_than_guessing(self):
        self.set_result("ACTIVE")
        self.set_field("runner pid", str(DEAD_PID))
        self.set_field("runner host", "some-other-machine")
        outcome, stub, _loop, _log = self.run_once([fixture("worker_done.md")] * 4)
        self.assertEqual(outcome.code, exits.STATE_UNRESUMABLE)
        self.assertIn("another host" if False else "ACTIVE run on host", outcome.reason)
        self.assertEqual(stub.invocations, 0)

    def test_an_active_run_with_an_unreadable_pid_blocks(self):
        self.set_result("ACTIVE")
        self.set_field("runner pid", "")
        outcome, stub, _loop, _log = self.run_once([fixture("worker_done.md")] * 4)
        self.assertEqual(outcome.code, exits.STATE_UNRESUMABLE)
        self.assertIn("unreadable pid", outcome.reason)
        self.assertEqual(stub.invocations, 0)


class TheCreateWindowIsAtomic(ResumeHarness):
    """AUDIT-6: `os.path.exists` then write is a race, and the pid check misses it.

    Two runners entering that window both saw "no state file" and both created
    one. The pid/host check only catches a run that had already written its
    state, so it cannot close this. The claim is now `O_CREAT|O_EXCL`, which
    either wins the path or fails.

    The window is reproduced by making the existence check lie — the file is
    there, the check says it is not — which is exactly what the second runner
    observes when the first has not written yet.
    """

    def test_a_runner_that_loses_the_race_refuses_rather_than_overwriting(self):
        from sdd_runner import loop as loop_mod

        stub = StubBackend(script=[fixture("worker_done.md")])
        log = RunLog(os.path.join(self.feature_dir, "run.jsonl"),
                     clock=lambda: next(self.counter), environ={})
        loop = Loop(self.repo, self.feature_dir, stub, log, clock=lambda: 0,
                    hostname=HOST, pid=os.getpid())

        # The rival got there first and has claimed the path but written nothing.
        with open(self.state_path, "w", encoding="utf-8") as fh:
            fh.write("")

        real_exists = os.path.exists
        os.path.exists = lambda p: False if p == self.state_path else real_exists(p)
        try:
            with self.assertRaises(loop_mod.ConcurrentRun):
                loop._load_or_create_state(2)
        finally:
            os.path.exists = real_exists

        with open(self.state_path, encoding="utf-8") as fh:
            self.assertEqual(fh.read(), "", "the loser must not overwrite the winner's claim")
        self.assertEqual(stub.invocations, 0)

    def test_the_winner_creates_normally(self):
        stub = StubBackend(script=[fixture("worker_done.md")])
        log = RunLog(os.path.join(self.feature_dir, "run.jsonl"),
                     clock=lambda: next(self.counter), environ={})
        loop = Loop(self.repo, self.feature_dir, stub, log, clock=lambda: 0,
                    hostname=HOST, pid=os.getpid())
        doc, resumed = loop._load_or_create_state(2)
        self.assertIsNone(resumed)
        self.assertEqual(doc.run_result(), "ACTIVE")


class ResumeDoesNotDuplicate(ResumeHarness):
    def test_findings_are_not_duplicated_and_counters_do_not_reset(self):
        # Run 1: domain rejects DOM-001 twice across the two tasks.
        self.run_once([fixture("worker_done.md"), fixture("reviewer_reject.md"),
                       fixture("worker_done.md"), fixture("reviewer_reject.md")])
        first_fields = self.fields()
        self.assertIn("domain=streak:2", first_fields["counters"])
        self.set_result("PAUSED")

        # Run 2: the registry has one row, and the streak continues from 2.
        _outcome, _stub, loop2, log2 = self.run_once([
            fixture("worker_done.md"), fixture("reviewer_reject.md"),
            fixture("worker_done.md"), fixture("reviewer_approve.md"),
        ])
        resumed = [e for e in log2.events if e["event"] == "resume"][0]
        self.assertEqual(resumed["findings"], ["domain:DOM-001"])
        self.assertIn("domain=streak:2", resumed["counters"])

        _headers, rows = state.parse_table(self.doc().body("Findings"))
        identities = [r["Reviewer:finding"] for r in rows]
        self.assertEqual(identities, ["domain:DOM-001"], "the finding must not be duplicated")

    def test_the_second_run_dispatches_only_the_unfinished_task(self):
        """The whole point: resuming costs no re-work."""
        _first, stub1, _loop1, _log1 = self.run_once([
            fixture("worker_done.md"), fixture("reviewer_approve.md"),
        ])
        self.assertEqual(stub1.invocations, 3)      # T001 worker + review, then T002 worker
        self.assertEqual(self.fields()["completed tasks"], "T001")
        self.assertIn("- [x] T001", self.tasks_text())

        outcome, stub2, _loop2, log2 = self.run_once(
            [fixture("worker_done.md"), fixture("reviewer_approve.md")] + finalization_flat())
        self.assertEqual(outcome.code, exits.OK)
        self.assertEqual(stub2.invocations, 2 + len(finalization_flat()),
                         "only T002 is dispatched; T001 is never delegated again")
        # Only task delegations count: the finalization calls legitimately quote
        # the whole of TASKS.md, T001 included.
        tasks_seen = {e["task"] for e in log2.events
                      if e["event"] == "dispatch" and e["task"] not in ("", "-")}
        self.assertEqual(tasks_seen, {"T002"})


class ResumeIsPersistedBeforeProceeding(ResumeHarness):
    def test_the_run_is_marked_active_while_it_runs_and_settled_at_the_end(self):
        self.run_once([fixture("worker_done.md"), fixture("reviewer_approve.md")])
        # The script ran out mid-T002, so the run aborted rather than finishing DONE.
        self.assertIn(self.doc().run_result(), ("ABORTED", "PAUSED"))
        fields = self.fields()
        self.assertEqual(fields["writer"], "sdd_runner")
        self.assertEqual(fields["runner host"], HOST)
        self.assertTrue(fields["runner pid"].isdigit())


if __name__ == "__main__":
    unittest.main()
