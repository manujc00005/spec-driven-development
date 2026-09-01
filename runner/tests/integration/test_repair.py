"""The repair / re-review cycle — spec 040 T016 (driver capability: T025).

implement -> review REJECT -> repair -> re-review -> APPROVE, or abort by
reviewer cap, per-finding cap, or budget. Deterministic, stub backend, no
provider call.
"""

import itertools
import os
import socket
import tempfile
import unittest

from sdd_runner import exits, state
from sdd_runner.backends.stub import StubBackend
from sdd_runner.log import RunLog
from sdd_runner.loop import Loop
from tests.support import GREEN_BASELINE, finalization_keys, make_repo

HOST = socket.gethostname()

# T001 mentions auth, so it requires BOTH domain and security review. Two
# reviewers is what makes a loop-level flip-flop possible at all: with one
# reviewer an APPROVE ends the task before it can change its mind.
TASKS_TWO_REVIEWERS = """# Tasks: fixture

## Phase 2: Implementation

- [ ] T001 - Add auth to the endpoint. Covers: AC-001. Verify: the suite passes.
- [ ] T002 - Do the second thing. Covers: AC-001. Verify: the suite passes.
"""

TASKS_ONE_REVIEWER = """# Tasks: fixture

## Phase 2: Implementation

- [ ] T001 - Do the first thing. Covers: AC-001. Verify: the suite passes.
"""


def done():
    return "Implemented.\n\n```yaml\nstatus: DONE\ndecisions: []\n```\n"


def approve():
    return "Looks right.\n\n```yaml\nverdict: APPROVE\nfindings: []\n```\n"


def reject(finding_id, severity="High", action="Persist before proceeding"):
    return ("One real problem.\n\n```yaml\nverdict: REJECT\nfindings:\n"
            "  - id: %s\n    severity: %s\n    evidence: a.py:1\n"
            "    summary: the thing is wrong\n    required_action: %s\n```\n"
            % (finding_id, severity, action))


class RepairHarness(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.counter = itertools.count()
        self.repo = None

    def make(self, tasks=TASKS_TWO_REVIEWERS):
        self.repo, self.feature_dir = make_repo(self.tmp.name, tasks=tasks)

    def run_once(self, script, max_iterations=3, max_delegations=None):
        """`script` is {agent-name: [responses...]}, consumed per agent in order."""
        stub = StubBackend(script={k: list(v) for k, v in script.items()})
        log = RunLog(os.path.join(self.feature_dir, "run.jsonl"),
                     clock=lambda: next(self.counter), environ={})
        loop = Loop(self.repo, self.feature_dir, stub, log,
                    max_iterations=max_iterations, max_delegations=max_delegations,
                    clock=lambda: 0, hostname=HOST, pid=os.getpid(),
                    baseline_cmd=GREEN_BASELINE)
        return loop.run(), stub, loop, log

    # -- helpers ---------------------------------------------------------
    def doc(self):
        return state.Orchestration.load(os.path.join(self.feature_dir, "ORCHESTRATION.md"))

    def fields(self):
        return state.parse_fields(self.doc().body("State"))

    def findings_rows(self):
        _headers, rows = state.parse_table(self.doc().body("Findings"))
        return rows

    def tasks_text(self):
        with open(os.path.join(self.feature_dir, "TASKS.md"), encoding="utf-8") as fh:
            return fh.read()

    @staticmethod
    def dispatches(log, agent=None):
        return [e for e in log.events
                if e["event"] == "dispatch" and (agent is None or e["agent"] == agent)]

    def set_result(self, result, resumable="yes"):
        doc = self.doc()
        doc.set_body("Run result", "\n%s\n\nresumable: %s\n\n" % (result, resumable))
        doc.save(os.path.join(self.feature_dir, "ORCHESTRATION.md"))


class RejectRegistersWork(RepairHarness):
    def test_a_reject_records_the_finding_schedules_a_repair_and_completes_nothing(self):
        self.make(TASKS_ONE_REVIEWER)
        outcome, stub, loop, log = self.run_once(
            {"implementer": [done()], "domain-reviewer": [reject("DOM-001")]},
            max_delegations=2)

        self.assertEqual(outcome.code, exits.BUDGET_EXHAUSTED)   # stopped before the repair
        self.assertNotEqual(self.doc().run_result(), "DONE")
        self.assertEqual(self.fields()["completed tasks"], "")

        rows = self.findings_rows()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["Reviewer:finding"], "domain:DOM-001")
        self.assertEqual(rows[0]["Status"], "open")
        self.assertEqual(rows[0]["Repair done"], "no")
        self.assertEqual(rows[0]["Task"], "T001")

        # 031 FR-007: the finding became a TASKS.md item traceable to it.
        self.assertIn("(from DOM-001)", self.tasks_text())
        self.assertEqual(rows[0]["Repair task"], "T002")


class RejectThenRepairThenApprove(RepairHarness):
    def test_reject_then_repair_then_approve(self):
        self.make(TASKS_ONE_REVIEWER)
        script = {"implementer": [done(), done()],
                  "domain-reviewer": [reject("DOM-001"), approve()]}
        script.update(finalization_keys())
        outcome, stub, loop, log = self.run_once(script)

        self.assertEqual(outcome.code, exits.OK)
        self.assertEqual(outcome.result, "DONE")
        self.assertEqual(self.fields()["completed tasks"], "T001")

        # implementation, review, repair, re-review, plus the one finalization call
        # 040 still owns: final-conformance-reviewer (D034).
        self.assertEqual(stub.invocations, 5)
        self.assertEqual(len(self.dispatches(log, "worker")), 2)
        self.assertEqual(len(self.dispatches(log, "domain")), 2)

        row = self.findings_rows()[0]
        self.assertEqual(row["Status"], "resolved")
        self.assertEqual(row["Repair done"], "yes")
        self.assertEqual(row["REJECTs"], "0", "a repair that worked is not a failed repair")

        self.assertTrue(any(e["event"] == "repair-done" for e in log.events))
        # The repair task is checked off once its finding resolves.
        self.assertIn("- [x] T002 - Repair DOM-001", self.tasks_text())

    def test_the_repair_brief_carries_the_required_action(self):
        self.make(TASKS_ONE_REVIEWER)
        script = {"implementer": [done(), done()],
                  "domain-reviewer": [reject("DOM-001", action="Wrap the write in a transaction"),
                                      approve()]}
        script.update(finalization_keys())
        _outcome, stub, _loop, _log = self.run_once(script)
        repair_prompt = stub.calls[2]["prompt"]
        self.assertIn("domain:DOM-001", repair_prompt)
        self.assertIn("Wrap the write in a transaction", repair_prompt)


class RepairFailsUntilCap(RepairHarness):
    def test_reject_then_repair_then_reject_until_cap(self):
        """The same finding re-reported after every repair: the reviewer cap ends it."""
        self.make(TASKS_ONE_REVIEWER)
        outcome, stub, loop, log = self.run_once({
            "implementer": [done()] * 8,
            "domain-reviewer": [reject("DOM-001")] * 8,
        }, max_iterations=3, max_delegations=40)

        self.assertEqual(outcome.code, exits.CAP_ABORT)
        self.assertEqual(outcome.result, "ABORTED")
        self.assertTrue(outcome.resumable, "a cap abort is recoverable")
        self.assertNotEqual(self.doc().run_result(), "DONE")

        # Re-reporting the SAME id every round resolves nothing, so the reviewer's
        # no-progress streak reaches the cap first. The per-finding total is the
        # other rule, and FlipFlop is what exercises it.
        abort = [e for e in log.events if e["event"] == "abort"][-1]
        self.assertEqual(abort["scope"], "reviewer")
        self.assertIn("domain", outcome.reason)
        self.assertIn("resolved nothing", outcome.reason)

        row = self.findings_rows()[0]
        self.assertEqual(row["Status"], "open")
        self.assertEqual(int(row["REJECTs"]), 2, "two repairs landed and both failed")
        self.assertEqual(len(self.dispatches(log, "worker")), 3,
                         "implementation plus two repairs")

    def test_a_reviewer_that_rejects_without_a_repair_landing_trips_the_streak_cap(self):
        """Malformed verdicts are not repairable, so the no-progress streak ends it."""
        self.make(TASKS_ONE_REVIEWER)
        outcome, stub, _loop, log = self.run_once({
            "implementer": [done()] * 8,
            "domain-reviewer": ["I approve, honest."] * 8,      # no block at all
        }, max_iterations=3, max_delegations=40)

        self.assertEqual(outcome.code, exits.CAP_ABORT)
        self.assertIn("domain", outcome.reason)
        # A synthetic finding is not worker-repairable: no repair is delegated.
        self.assertEqual(len(self.dispatches(log, "worker")), 1)
        self.assertTrue(all(r["Synthetic"] == "yes" for r in self.findings_rows()))


class FlipFlop(RepairHarness):
    """The per-finding cap, and the case only it can catch.

    A reviewer that alternates between two findings makes PROGRESS every round -
    each REJECT resolves the one it stops re-reporting - so its no-progress
    streak resets to zero every time and never reaches the cap. What accumulates
    is the per-finding failed-repair total: DOM-001 is repaired, comes back,
    is repaired, comes back. 031 keeps both counters precisely because a streak
    reset by intervening progress would miss this.

    Round by round, with one reviewer alternating DOM-001 / DOM-002:

        R1  REJECT [DOM-001]                     DOM-001 total 0, streak 1
        R2  repair DOM-001; REJECT [DOM-002]     DOM-001 resolved -> streak 0
        R3  repair DOM-002; REJECT [DOM-001]     DOM-001 total 1, streak 0
        R4  repair DOM-001; REJECT [DOM-002]     DOM-002 total 1, streak 0
        R5  repair DOM-002; REJECT [DOM-001]     DOM-001 total 2, streak 0
        R6  repair DOM-001; REJECT [DOM-002]     DOM-002 total 2, streak 0
        R7  repair DOM-002; REJECT [DOM-001]     DOM-001 total 3 -> ABORT
    """

    ALTERNATING = [reject("DOM-001"), reject("DOM-002")] * 6

    def test_flip_flop_detected_at_loop_level(self):
        self.make(TASKS_ONE_REVIEWER)
        outcome, stub, loop, log = self.run_once({
            "implementer": [done()] * 12,
            "domain-reviewer": list(self.ALTERNATING),
        }, max_iterations=3, max_delegations=60)

        self.assertEqual(outcome.code, exits.CAP_ABORT)
        self.assertEqual(outcome.result, "ABORTED")
        self.assertTrue(outcome.resumable)

        abort = [e for e in log.events if e["event"] == "abort"][-1]
        self.assertEqual(abort["scope"], "finding",
                         "the per-finding cap must be what fired, not the streak")
        self.assertIn("domain:DOM-001", outcome.reason)
        self.assertIn("failed repairs", outcome.reason)

        row = [r for r in self.findings_rows()
               if r["Reviewer:finding"] == "domain:DOM-001"][0]
        self.assertEqual(int(row["REJECTs"]), 3)

        streak = int(self.fields()["counters"].split("domain=streak:")[1].split(",")[0])
        self.assertLess(streak, 3, "the streak cap must NOT have been reached")

    def test_it_terminates_well_short_of_the_budget(self):
        self.make(TASKS_ONE_REVIEWER)
        outcome, stub, _loop, _log = self.run_once({
            "implementer": [done()] * 30,
            "domain-reviewer": [reject("DOM-001"), reject("DOM-002")] * 15,
        }, max_iterations=3, max_delegations=60)
        self.assertEqual(outcome.code, exits.CAP_ABORT)
        self.assertLess(stub.invocations, 20,
                        "a cap, not the budget ceiling, is what ends a flip-flop")

    def test_the_second_finding_keeps_its_own_independent_count(self):
        self.make(TASKS_ONE_REVIEWER)
        self.run_once({
            "implementer": [done()] * 12,
            "domain-reviewer": list(self.ALTERNATING),
        }, max_iterations=3, max_delegations=60)
        rows = {r["Reviewer:finding"]: r for r in self.findings_rows()}
        self.assertEqual(int(rows["domain:DOM-001"]["REJECTs"]), 3)
        self.assertEqual(int(rows["domain:DOM-002"]["REJECTs"]), 2)
        self.assertEqual(len(rows), 2, "two identities, two rows, no duplicates")


class BudgetDuringTheCycle(RepairHarness):
    def test_budget_exhausted_before_repair_dispatch(self):
        self.make(TASKS_ONE_REVIEWER)
        outcome, stub, _loop, log = self.run_once({
            "implementer": [done()] * 4,
            "domain-reviewer": [reject("DOM-001")] * 4,
        }, max_delegations=2)

        self.assertEqual(outcome.code, exits.BUDGET_EXHAUSTED)
        self.assertEqual(stub.invocations, 2, "the repair call is never made")
        self.assertEqual(len(self.dispatches(log, "worker")), 1)
        self.assertTrue(outcome.resumable)
        self.assertEqual(self.doc().run_result(), "ABORTED")
        self.assertTrue(self.doc().resumable())

    def test_budget_exhausted_before_rereview_dispatch(self):
        self.make(TASKS_ONE_REVIEWER)
        outcome, stub, _loop, log = self.run_once({
            "implementer": [done()] * 4,
            "domain-reviewer": [reject("DOM-001")] * 4,
        }, max_delegations=3)

        self.assertEqual(outcome.code, exits.BUDGET_EXHAUSTED)
        self.assertEqual(stub.invocations, 3, "the re-review call is never made")
        self.assertEqual(len(self.dispatches(log, "worker")), 2)   # implement + repair
        self.assertEqual(len(self.dispatches(log, "domain")), 1)
        # The repair landed and is recorded, so re-entry re-reviews instead of repairing.
        self.assertEqual(self.findings_rows()[0]["Repair done"], "yes")


class ResumeAcrossTheCycle(RepairHarness):
    def _stop_after_repair(self):
        """Run until the repair has landed but the re-review has not been made."""
        self.make(TASKS_ONE_REVIEWER)
        outcome, stub, _loop, _log = self.run_once({
            "implementer": [done()] * 4,
            "domain-reviewer": [reject("DOM-001")] * 4,
        }, max_delegations=3)
        self.assertEqual(outcome.code, exits.BUDGET_EXHAUSTED)
        return stub

    def test_resume_after_repair_before_rereview(self):
        self._stop_after_repair()
        script = {"implementer": [done()] * 4, "domain-reviewer": [approve()] * 4}
        script.update(finalization_keys())
        outcome, stub, _loop, log = self.run_once(script, max_delegations=30)

        self.assertEqual(outcome.code, exits.OK)
        first = self.dispatches(log)[0]
        self.assertEqual(first["agent"], "domain",
                         "the pending work was the re-review, not another repair")
        self.assertEqual(self.fields()["completed tasks"], "T001")

    def test_no_duplicate_repair_on_resume(self):
        self._stop_after_repair()
        script = {"implementer": [done()] * 4, "domain-reviewer": [approve()] * 4}
        script.update(finalization_keys())
        _outcome, _stub, _loop, log = self.run_once(script, max_delegations=30)

        self.assertEqual(self.dispatches(log, "worker"), [],
                         "no worker delegation at all: the repair already landed")
        rows = self.findings_rows()
        self.assertEqual(len(rows), 1, "the finding must not be duplicated")
        self.assertEqual(rows[0]["Status"], "resolved")
        # And exactly one repair task exists for it.
        self.assertEqual(self.tasks_text().count("(from DOM-001)"), 1)

    def test_the_reject_count_survives_re_entry(self):
        self.make(TASKS_ONE_REVIEWER)
        self.run_once({
            "implementer": [done()] * 4,
            "domain-reviewer": [reject("DOM-001")] * 4,
        }, max_delegations=5)
        before = int(self.findings_rows()[0]["REJECTs"])
        self.assertGreaterEqual(before, 1)

        script = {"implementer": [done()] * 4, "domain-reviewer": [approve()] * 4}
        script.update(finalization_keys())
        _outcome, _stub, loop2, _log = self.run_once(script, max_delegations=30)
        self.assertEqual(loop2.counters.findings["domain:DOM-001"].reject_total, before,
                         "a re-entry must not reset the per-finding counter")


class ConvergenceIsRequiredForDone(RepairHarness):
    def test_no_done_without_all_tasks_converged(self):
        self.make(TASKS_TWO_REVIEWERS)
        outcome, stub, _loop, _log = self.run_once({
            "implementer": [done()] * 12,
            # T001 converges; T002's reviewer never lets go.
            "domain-reviewer": [approve(), reject("DOM-009"), reject("DOM-009"),
                                reject("DOM-009"), reject("DOM-009"), reject("DOM-009")],
            "security-reviewer": [approve()] * 12,
        }, max_iterations=3, max_delegations=60)

        self.assertNotEqual(outcome.code, exits.OK)
        self.assertNotEqual(self.doc().run_result(), "DONE")
        self.assertEqual(self.fields()["completed tasks"], "T001",
                         "only the task that actually converged is complete")


if __name__ == "__main__":
    unittest.main()
