"""The loop against the stub backend — deterministic, no provider call.

What these prove: what the RUNNER does with a given response. What they cannot
prove: what a provider will actually send. Spec 032's PLAN rejects scripted
reviewers as evidence about the loop's real behaviour, and that limit is
recorded here rather than left implicit.
"""

import itertools
import json
import os
import socket
import tempfile
import unittest

from sdd_runner import exits, state
from sdd_runner.backends.stub import StubBackend
from sdd_runner.log import RunLog
from sdd_runner.loop import Loop
from tests.support import TASKS, fixture, make_repo

FOUR_TASKS = """# Tasks: fixture

## Phase 2: Implementation

- [ ] T001 - First. Covers: AC-001. Verify: the suite passes.
- [ ] T002 - Second. Covers: AC-001. Verify: the suite passes.
- [ ] T003 - Third. Covers: AC-001. Verify: the suite passes.
- [ ] T004 - Fourth. Covers: AC-001. Verify: the suite passes.
"""


class LoopHarness(unittest.TestCase):
    def build(self, script, tasks=TASKS, max_iterations=3, max_delegations=None, notify=None):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        repo, feature_dir = make_repo(self.tmp.name, tasks=tasks)
        stub = StubBackend(script=list(script))
        counter = itertools.count()
        log = RunLog(os.path.join(feature_dir, "run.jsonl"), clock=lambda: next(counter),
                     environ={})
        loop = Loop(repo, feature_dir, stub, log, max_iterations=max_iterations,
                    max_delegations=max_delegations, clock=lambda: 0, notify=notify)
        return loop, stub, repo, feature_dir, log


class Converge(LoopHarness):
    def test_two_tasks_converge_and_leave_no_commit(self):
        script = [fixture("worker_done.md"), fixture("reviewer_approve.md")] * 2
        loop, stub, repo, feature_dir, log = self.build(script)
        outcome = loop.run()

        self.assertEqual(outcome.code, exits.OK)
        self.assertEqual(outcome.result, "DONE")
        self.assertEqual(stub.invocations, 4)

        doc = state.Orchestration.load(os.path.join(feature_dir, "ORCHESTRATION.md"))
        self.assertEqual(doc.run_result(), "DONE")
        for section in ("State", "Attempts", "Findings", "Delegation log",
                        "Escalations", "Cap changes", "Closure delta", "Run result"):
            self.assertIsNotNone(doc.get(section), "missing 031 section %r" % section)

        # FR-012: the runner creates no commit.
        import subprocess
        out = subprocess.run(["git", "-C", repo, "log", "--oneline"],
                             capture_output=True, text=True).stdout.strip().splitlines()
        self.assertEqual(len(out), 1, "the runner must not commit")

    def test_every_decision_is_reconstructible_from_run_jsonl_alone(self):
        script = [fixture("worker_done.md"), fixture("reviewer_approve.md")] * 2
        loop, stub, repo, feature_dir, log = self.build(script)
        loop.run()
        with open(os.path.join(feature_dir, "run.jsonl"), encoding="utf-8") as fh:
            lines = fh.read().splitlines()
        events = [json.loads(l)["event"] for l in lines]
        for required in ("plan", "dispatch", "response", "completion", "verdict",
                         "counters", "finish"):
            self.assertIn(required, events)


class RejectThenFix(LoopHarness):
    def test_a_reject_registers_the_finding_and_a_later_approve_resolves_it(self):
        script = [fixture("worker_done.md"), fixture("reviewer_reject.md"),
                  fixture("worker_done.md"), fixture("reviewer_approve.md")]
        loop, stub, repo, feature_dir, log = self.build(script)
        loop.run()
        row = loop.counters.findings["domain:DOM-001"]
        self.assertEqual(row.status, "resolved")
        self.assertEqual(row.resolving_verdict, "APPROVE")
        self.assertEqual(loop.counters.reviewer("domain").no_progress_streak, 0)


class MalformedResponses(LoopHarness):
    def test_an_unparseable_review_becomes_a_synthetic_reject_never_an_approve(self):
        script = [fixture("worker_done.md"), fixture("missing_block.md"),
                  fixture("worker_done.md"), fixture("reviewer_approve.md")]
        loop, stub, repo, feature_dir, log = self.build(script)
        loop.run()
        verdicts = [e for e in log.events if e["event"] == "verdict"]
        self.assertTrue(verdicts[0]["synthetic"])
        self.assertEqual(verdicts[0]["verdict"], "REJECT")

    def test_an_unparseable_worker_response_blocks_and_never_reports_done(self):
        script = [fixture("malformed_yaml.md"), fixture("reviewer_approve.md"),
                  fixture("worker_done.md"), fixture("reviewer_approve.md")]
        loop, stub, repo, feature_dir, log = self.build(script)
        loop.run()
        completions = [e for e in log.events if e["event"] == "completion"]
        self.assertEqual(completions[0]["status"], "BLOCKED")
        self.assertTrue(completions[0]["malformed"])


class BudgetRefusal(LoopHarness):
    def test_the_n_plus_first_delegation_is_never_dispatched(self):
        script = [fixture("worker_done.md"), fixture("reviewer_approve.md")] * 4
        loop, stub, repo, feature_dir, log = self.build(
            script, tasks=FOUR_TASKS, max_delegations=3)
        outcome = loop.run()
        self.assertEqual(outcome.code, exits.BUDGET_EXHAUSTED)
        self.assertEqual(outcome.result, "ABORTED")
        self.assertTrue(outcome.resumable)
        # Observed by counting stub invocations, not by reading code.
        self.assertEqual(stub.invocations, 3)


class CapAbort(LoopHarness):
    def test_a_stagnating_reviewer_aborts_recoverably_naming_itself(self):
        script = [fixture("worker_done.md"), fixture("reviewer_reject.md")] * 4
        loop, stub, repo, feature_dir, log = self.build(
            script, tasks=FOUR_TASKS, max_iterations=3)
        outcome = loop.run()
        self.assertEqual(outcome.code, exits.CAP_ABORT)
        self.assertIn("domain", outcome.reason)
        self.assertTrue(outcome.resumable)
        # The abort fires as soon as the cap is breached - at the end of task 3's
        # review - so task 4's worker is never dispatched: 3 workers + 3 reviews.
        self.assertEqual(stub.invocations, 6)
        self.assertEqual(loop.counters.reviewer("domain").total_invocations, 3)


class HumanEscalation(LoopHarness):
    def test_a_gated_question_pauses_the_run_and_notifies_once(self):
        sent = []
        script = [fixture("worker_blocked_human.md")]
        loop, stub, repo, feature_dir, log = self.build(script, notify=sent.append)
        outcome = loop.run()

        self.assertEqual(outcome.code, exits.HUMAN_ESCALATION)
        self.assertEqual(outcome.result, "PAUSED")
        self.assertEqual(len(sent), 1)
        self.assertEqual(sent[0]["event"], "human-escalation")
        self.assertIn("money", sent[0]["triggers"])
        self.assertTrue(json.dumps(sent[0]))          # the sink receives valid JSON

        doc = state.Orchestration.load(os.path.join(feature_dir, "ORCHESTRATION.md"))
        self.assertIn("waiting", doc.body("Escalations"))
        self.assertIn("overage", doc.body("Escalations"))   # verbatim question

    def test_a_technical_question_does_not_pause_the_run(self):
        script = [fixture("worker_blocked.md"), fixture("reviewer_approve.md"),
                  fixture("worker_done.md"), fixture("reviewer_approve.md")]
        loop, stub, repo, feature_dir, log = self.build(script)
        outcome = loop.run()
        self.assertNotEqual(outcome.code, exits.HUMAN_ESCALATION)
        self.assertTrue(any(e["event"] == "escalation-auto" for e in log.events))


class ConcurrentRun(LoopHarness):
    def test_a_second_runner_refuses_before_any_provider_call(self):
        script = [fixture("worker_done.md"), fixture("reviewer_approve.md")] * 2
        loop, stub, repo, feature_dir, log = self.build(script)
        # ACTIVE, written by a pid that is genuinely alive on this host: a live
        # concurrent runner, not an interrupted one.
        doc = state.new_document(feature_dir, "runner", 0,
                                 {"max_iterations": 3, "max_delegations": 25,
                                  "pid": os.getpid(), "host": socket.gethostname()})
        doc.save(os.path.join(feature_dir, "ORCHESTRATION.md"))

        outcome = loop.run()
        self.assertEqual(outcome.code, exits.CONCURRENT_RUN)
        self.assertEqual(stub.invocations, 0, "no provider call may be made")


if __name__ == "__main__":
    unittest.main()
