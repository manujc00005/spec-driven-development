"""Finalization, freeze and closure delta — spec 031 FR-013, spec 040 T014.

The property under test throughout: **the runner says DONE only when it can
demonstrate the run is closed.** Every path that cannot demonstrate it must stop
with a reason and a remediation, and must leave the record readable.
"""

import itertools
import os
import socket
import tempfile
import unittest

from sdd_runner import closure, exits, state
from sdd_runner.backends import Response
from sdd_runner.backends.stub import StubBackend
from sdd_runner.log import RunLog
from sdd_runner.loop import Loop
from tests.support import approve_block, finalization_keys, make_repo

HOST = socket.gethostname()

ONE_TASK = """# Tasks: fixture

## Phase 2: Implementation

- [ ] T001 - Do the first thing. Covers: AC-001. Verify: the suite passes.
"""

TWO_TASKS = """# Tasks: fixture

## Phase 2: Implementation

- [ ] T001 - Do the first thing. Covers: AC-001. Verify: the suite passes.
- [ ] T002 - Do the second thing. Covers: AC-001. Verify: the suite passes.
"""


def done():
    return "Implemented.\n\n```yaml\nstatus: DONE\ndecisions: []\n```\n"


def reject(fid="DOM-001"):
    return ("Problem.\n\n```yaml\nverdict: REJECT\nfindings:\n  - id: %s\n    severity: High\n"
            "    evidence: a.py:1\n    summary: wrong\n    required_action: fix it\n```\n" % fid)


class MutatingStub(StubBackend):
    """A worker that actually changes the tree, so approvals can go stale.

    A stub that writes nothing keeps the fingerprint constant, which would make
    every staleness test pass for the wrong reason.
    """

    def __init__(self, script, repo):
        super().__init__(script=script)
        self.repo = repo
        self._writes = 0

    def run(self, system_prompt, task_prompt, path_scope, timeout):
        response = super().run(system_prompt, task_prompt, path_scope, timeout)
        if "implementer" in (system_prompt or ""):
            self._writes += 1
            src = os.path.join(self.repo, "src")
            os.makedirs(src, exist_ok=True)
            with open(os.path.join(src, "impl_%d.py" % self._writes), "w",
                      encoding="utf-8") as fh:
                fh.write("# change %d\n" % self._writes)
        return response


class FinalizationHarness(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.counter = itertools.count()

    def make(self, tasks=ONE_TASK):
        self.repo, self.feature_dir = make_repo(self.tmp.name, tasks=tasks)

    def run_once(self, script, mutating=False, max_delegations=None, max_iterations=3,
                 baseline_cmd=None):
        script = {k: list(v) for k, v in script.items()}
        stub = (MutatingStub(script, self.repo) if mutating else StubBackend(script=script))
        log = RunLog(os.path.join(self.feature_dir, "run.jsonl"),
                     clock=lambda: next(self.counter), environ={})
        loop = Loop(self.repo, self.feature_dir, stub, log, max_iterations=max_iterations,
                    max_delegations=max_delegations, clock=lambda: 0, hostname=HOST,
                    pid=os.getpid(), baseline_cmd=baseline_cmd)
        return loop.run(), stub, loop, log

    def converging_script(self, tasks=1, each=1):
        script = {"implementer": [done()] * (tasks + 2),
                  "domain-reviewer": [approve_block()] * (tasks + 2)}
        script.update(finalization_keys(each=each))
        return script

    # -- state helpers ---------------------------------------------------
    @property
    def state_path(self):
        return os.path.join(self.feature_dir, "ORCHESTRATION.md")

    def doc(self):
        return state.Orchestration.load(self.state_path)

    def fields(self):
        return state.parse_fields(self.doc().body("State"))

    def tasks_text(self):
        with open(os.path.join(self.feature_dir, "TASKS.md"), encoding="utf-8") as fh:
            return fh.read()

    def write_tasks(self, text):
        with open(os.path.join(self.feature_dir, "TASKS.md"), "w", encoding="utf-8") as fh:
            fh.write(text)

    def set_result(self, result, resumable="yes"):
        doc = self.doc()
        doc.set_body("Run result", "\n%s\n\nresumable: %s\n\n" % (result, resumable))
        doc.save(self.state_path)

    def events(self, log, name):
        return [e for e in log.events if e["event"] == name]


class HappyPath(FinalizationHarness):
    def test_all_tasks_approved_then_done(self):
        self.make(ONE_TASK)
        outcome, stub, loop, log = self.run_once(self.converging_script())

        self.assertEqual(outcome.code, exits.OK)
        self.assertEqual(outcome.result, "DONE")
        self.assertFalse(outcome.resumable, "a closed run is not re-entered")
        self.assertEqual(self.doc().run_result(), "DONE")

        self.assertEqual(len(self.events(log, "freeze")), 1)
        self.assertEqual(len(self.events(log, "closure-delta")), 1)
        self.assertEqual([e["step"] for e in self.events(log, "lifecycle")],
                         ["spec-review", "spec-close", "pr-description"])
        self.assertIn("- [x] T001", self.tasks_text())

    def test_the_runner_still_creates_no_commit(self):
        import subprocess
        self.make(ONE_TASK)
        self.run_once(self.converging_script())
        out = subprocess.run(["git", "-C", self.repo, "log", "--oneline"],
                             capture_output=True, text=True).stdout.strip().splitlines()
        self.assertEqual(len(out), 1)

    def test_the_verification_condition_is_recorded_when_declared(self):
        self.make(ONE_TASK)
        outcome, _stub, _loop, log = self.run_once(self.converging_script(),
                                                   baseline_cmd=["true"])
        self.assertEqual(outcome.code, exits.OK)
        record = closure.parse(self.doc().body("Closure delta"))
        self.assertEqual(record["verification"], "PASS")

    def test_a_red_verification_blocks_the_freeze(self):
        self.make(ONE_TASK)
        outcome, _stub, _loop, _log = self.run_once(self.converging_script(),
                                                    baseline_cmd=["false"])
        self.assertNotEqual(outcome.code, exits.OK)
        self.assertIn("verification command did not pass", outcome.reason)
        self.assertNotEqual(self.doc().run_result(), "DONE")

    def test_an_undeclared_verification_is_recorded_as_unobserved_not_as_passed(self):
        """031's second DONE condition cannot be met without a declared command.

        The runner does not pretend otherwise: the closure record says so in
        writing, and so does the run's reason line.
        """
        self.make(ONE_TASK)
        outcome, _stub, _loop, _log = self.run_once(self.converging_script())
        record = closure.parse(self.doc().body("Closure delta"))
        self.assertIn("NOT DECLARED", record["verification"])
        self.assertIn("unobserved", record["verification"])
        self.assertIn("NOT DECLARED", outcome.reason)


class BlockingConditions(FinalizationHarness):
    def _converge_then_pause(self, with_finding=False):
        self.make(ONE_TASK)
        if with_finding:
            script = {"implementer": [done(), done()],
                      "domain-reviewer": [reject("DOM-001"), approve_block()]}
            script.update(finalization_keys())
        else:
            script = self.converging_script()
        outcome, _stub, _loop, _log = self.run_once(script)
        self.assertEqual(outcome.code, exits.OK)
        return outcome

    def test_open_finding_blocks_done(self):
        self._converge_then_pause(with_finding=True)
        doc = self.doc()
        body = doc.body("Findings")
        rows = body.replace("| resolved |", "| open |")
        self.assertNotEqual(rows, body, "the fixture must actually reopen a finding")
        doc.set_body("Findings", rows)
        doc.set_body("Run result", "\nPAUSED\n\nresumable: yes\n\n")
        doc.save(self.state_path)

        outcome, stub, _loop, _log = self.run_once(self.converging_script())
        self.assertNotEqual(outcome.code, exits.OK)
        self.assertEqual(outcome.code, exits.NOT_CONVERGED)
        self.assertIn("still open", outcome.reason)
        self.assertTrue(outcome.remediation)
        self.assertNotEqual(self.doc().run_result(), "DONE")

    def test_pending_escalation_blocks_done(self):
        self._converge_then_pause()
        doc = self.doc()
        doc.set_body("Escalations",
                     "\n- **waiting** (money) on T001: what tier do we bill?\n\n")
        doc.set_body("Run result", "\nPAUSED\n\nresumable: yes\n\n")
        doc.save(self.state_path)

        outcome, stub, _loop, _log = self.run_once(self.converging_script())
        self.assertEqual(outcome.code, exits.HUMAN_ESCALATION)
        self.assertEqual(stub.invocations, 0, "nothing is dispatched while one waits")
        self.assertNotEqual(self.doc().run_result(), "DONE")

    def test_no_done_when_repair_task_left_open(self):
        self.make(ONE_TASK)
        script = {"implementer": [done(), done()],
                  "domain-reviewer": [reject("DOM-001"), approve_block()]}
        script.update(finalization_keys())
        outcome, _stub, _loop, _log = self.run_once(script)
        self.assertEqual(outcome.code, exits.OK)
        self.assertIn("- [x] T002 - Repair DOM-001", self.tasks_text())

        # Re-open the repair task by hand and re-enter.
        self.write_tasks(self.tasks_text().replace("- [x] T002", "- [ ] T002"))
        self.set_result("PAUSED")
        outcome2, stub2, _loop2, _log2 = self.run_once(self.converging_script())
        self.assertEqual(outcome2.code, exits.NOT_CONVERGED)
        self.assertIn("T002", outcome2.reason)
        self.assertIn("unchecked", outcome2.reason)
        self.assertNotEqual(self.doc().run_result(), "DONE")

    def test_no_done_on_budget_invalid(self):
        """`used > cap` cannot arise in a healthy run, so the guard is exercised directly.

        `Budget.charge` refuses past the cap, which is exactly why a corrupted or
        hand-edited number is the only way to reach this state - and precisely why
        finalization re-checks it instead of trusting it.
        """
        self.make(ONE_TASK)
        _outcome, _stub, loop, _log = self.run_once(self.converging_script())
        loop.budget.used = loop.budget.cap + 5
        blocked = loop._state_preconditions([])
        self.assertEqual(blocked.code, exits.STATE_UNRESUMABLE)
        self.assertIn("budget is inconsistent", blocked.reason)
        self.assertEqual(blocked.result, "ABORTED")
        self.assertFalse(blocked.resumable)

    def test_a_corrupted_budget_in_the_state_file_blocks_re_entry(self):
        self._converge_then_pause()
        doc = self.doc()
        fields = state.parse_fields(doc.body("State"))
        fields["delegations used"] = str(int(fields["max-delegations"]) + 10)
        doc.set_body("State", state.render_fields(fields))
        doc.set_body("Run result", "\nPAUSED\n\nresumable: yes\n\n")
        doc.save(self.state_path)

        outcome, stub, _loop, _log = self.run_once(self.converging_script())
        self.assertEqual(outcome.code, exits.STATE_UNRESUMABLE)
        self.assertEqual(stub.invocations, 0)


class StaleApprovals(FinalizationHarness):
    """A later task's change stales an earlier task's approval (031 FR-011)."""

    def _script(self, domain):
        script = {"implementer": [done()] * 6, "domain-reviewer": list(domain)}
        script.update(finalization_keys(each=2))
        return script

    def test_final_freeze_rereviews_stale_approvals(self):
        self.make(TWO_TASKS)
        outcome, stub, loop, log = self.run_once(
            self._script([approve_block()] * 6), mutating=True, max_delegations=40)

        stale = self.events(log, "stale-approvals")
        self.assertTrue(stale, "T002's write must have staled T001's approval")
        self.assertIn("domain@T001", stale[0]["pairs"])

        self.assertEqual(outcome.code, exits.OK, "fresh approvals close the run")
        self.assertEqual(self.doc().run_result(), "DONE")

        # The freeze happened after the re-review, on a fingerprint every required
        # reviewer had approved.
        record = closure.parse(self.doc().body("Closure delta"))
        self.assertEqual(record["frozen_fingerprint"], loop.fingerprint())

    def test_stale_approval_blocks_done_when_the_rereview_rejects(self):
        self.make(TWO_TASKS)
        domain = [approve_block(), approve_block(), reject("DOM-050")] + [approve_block()] * 4
        outcome, stub, loop, log = self.run_once(self._script(domain), mutating=True,
                                                 max_delegations=40)

        self.assertNotEqual(outcome.code, exits.OK)
        self.assertEqual(outcome.code, exits.NOT_CONVERGED)
        self.assertIn("returns to REVIEW", outcome.reason)
        self.assertNotEqual(self.doc().run_result(), "DONE")

        # The task must not stay marked complete, or a resume would skip it.
        self.assertNotIn("- [x] T001", self.tasks_text())
        self.assertNotIn("T001", self.fields()["completed tasks"].split(", "))

    def test_no_freeze_is_recorded_when_finalization_blocks(self):
        self.make(TWO_TASKS)
        domain = [approve_block(), approve_block(), reject("DOM-050")] + [approve_block()] * 4
        _outcome, _stub, _loop, log = self.run_once(self._script(domain), mutating=True,
                                                    max_delegations=40)
        self.assertEqual(self.events(log, "freeze"), [],
                         "a freeze must never be recorded before the conditions hold")


class ClosureDeltaRecord(FinalizationHarness):
    def test_closure_delta_persisted(self):
        self.make(ONE_TASK)
        outcome, _stub, loop, _log = self.run_once(self.converging_script())
        self.assertEqual(outcome.code, exits.OK)

        body = self.doc().body("Closure delta")
        record = closure.parse(body)
        self.assertEqual(record["phase"], "CLOSED")
        self.assertTrue(record["frozen_fingerprint"])
        self.assertTrue(record["frozen"], "the frozen tree map must be persisted")
        self.assertIn("### Frozen tree", body)
        self.assertIn("### Observed delta", body)

        # Everything observed after the freeze is a generated artifact.
        for row in record["delta"]:
            self.assertEqual(row["Classification"], closure.ALLOWED, row)

    def test_an_unexpected_change_after_the_freeze_invalidates_closure(self):
        self.make(ONE_TASK)

        class SabotagingStub(StubBackend):
            def __init__(self, script, repo):
                super().__init__(script=script)
                self.repo = repo

            def run(self, system_prompt, task_prompt, path_scope, timeout):
                # A lifecycle skill that touches production code: exactly what the
                # closure allowlist exists to catch.
                if "lifecycle:spec-close" in (system_prompt or ""):
                    with open(os.path.join(self.repo, "production.py"), "w",
                              encoding="utf-8") as fh:
                        fh.write("# written after the freeze\n")
                return super().run(system_prompt, task_prompt, path_scope, timeout)

        script = {k: list(v) for k, v in self.converging_script().items()}
        stub = SabotagingStub(script, self.repo)
        log = RunLog(os.path.join(self.feature_dir, "run.jsonl"),
                     clock=lambda: next(self.counter), environ={})
        loop = Loop(self.repo, self.feature_dir, stub, log, clock=lambda: 0,
                    hostname=HOST, pid=os.getpid())
        outcome = loop.run()

        self.assertEqual(outcome.code, exits.CLOSURE_NOT_PROVEN)
        self.assertIn("production.py", outcome.reason)
        self.assertIn("returns the run to REVIEW", outcome.remediation)
        self.assertNotEqual(self.doc().run_result(), "DONE")

        record = closure.parse(self.doc().body("Closure delta"))
        self.assertEqual(record["phase"], "INVALID")
        unexpected = [r for r in record["delta"] if r["Classification"] == closure.UNEXPECTED]
        self.assertEqual([r["Path"] for r in unexpected], ["production.py"])


class ClosureAllowlistIsPathExact(FinalizationHarness):
    """SEC-001: the allowlist matched by basename, so it matched repo-wide.

    A generated artifact is allowed because of WHERE it is, not what it is
    called. Matching `os.path.basename` let any `src/PR_DESCRIPTION.md` or
    `lib/run.jsonl` change after the freeze and be audited as expected — and this
    is the last gate before DONE.
    """

    def test_a_generated_name_outside_the_feature_folder_is_unexpected(self):
        self.make(ONE_TASK)
        for path in ("src/PR_DESCRIPTION.md", "lib/run.jsonl",
                     "deep/nested/CALIBRATION.md", "ORCHESTRATION.md"):
            with self.subTest(path=path):
                classification, _rule = closure.classify(self.repo, self.feature_dir, path)
                self.assertEqual(classification, closure.UNEXPECTED)

    def test_the_real_generated_artifacts_are_still_allowed(self):
        self.make(ONE_TASK)
        rel = os.path.relpath(self.feature_dir, self.repo)
        for name in closure.GENERATED:
            with self.subTest(name=name):
                classification, rule = closure.classify(
                    self.repo, self.feature_dir, os.path.join(rel, name))
                self.assertEqual(classification, closure.ALLOWED, rule)

    def test_a_run_still_closes_cleanly(self):
        self.make(ONE_TASK)
        outcome, _stub, _loop, _log = self.run_once(self.converging_script())
        self.assertEqual(outcome.code, exits.OK)


class ResumeAcrossFinalization(FinalizationHarness):
    def _freeze_but_stop(self):
        """Budget lets final-conformance run and the freeze happen, but no lifecycle step."""
        self.make(ONE_TASK)
        outcome, _stub, _loop, log = self.run_once(self.converging_script(),
                                                   max_delegations=3)
        self.assertEqual(outcome.code, exits.BUDGET_EXHAUSTED)
        self.assertTrue(self.events(log, "freeze"), "the freeze must have been recorded")
        return outcome

    def test_resume_after_freeze_before_done(self):
        self._freeze_but_stop()
        before = closure.parse(self.doc().body("Closure delta"))
        self.assertEqual(before["phase"], "FROZEN")

        outcome, stub, _loop, log = self.run_once(self.converging_script(),
                                                  max_delegations=20)
        self.assertEqual(outcome.code, exits.OK)
        self.assertTrue(self.events(log, "freeze-reused"), "the freeze must be reused")
        self.assertEqual(self.events(log, "freeze"), [], "and never recomputed")

        # No task work and no second conformance review: only the lifecycle steps.
        self.assertEqual([e["agent"] for e in self.events(log, "dispatch")],
                         ["lifecycle:spec-review", "lifecycle:spec-close",
                          "lifecycle:pr-description"])

        after = closure.parse(self.doc().body("Closure delta"))
        self.assertEqual(after["frozen_fingerprint"], before["frozen_fingerprint"],
                         "the frozen fingerprint must survive re-entry unchanged")
        self.assertEqual(after["frozen"], before["frozen"],
                         "and so must the frozen tree map")

    def test_corrupt_closure_delta_blocks_resume(self):
        self._freeze_but_stop()
        doc = self.doc()
        body = doc.body("Closure delta")
        doc.set_body("Closure delta", body.replace("### Observed delta", "### Something Else"))
        doc.save(self.state_path)

        outcome, stub, _loop, _log = self.run_once(self.converging_script(),
                                                   max_delegations=20)
        self.assertEqual(outcome.code, exits.STATE_UNRESUMABLE)
        self.assertEqual(stub.invocations, 0, "a corrupt freeze record dispatches nothing")
        self.assertIn("Closure delta", outcome.reason)
        self.assertIn("corrupt", outcome.reason)
        self.assertTrue(outcome.remediation)

    def test_a_declared_frozen_path_count_that_does_not_match_blocks_resume(self):
        self._freeze_but_stop()
        doc = self.doc()
        body = doc.body("Closure delta")
        doc.set_body("Closure delta", body.replace("- frozen paths:", "- frozen paths: 999 #",
                                                   1).replace("999 # ", "999\n- ignored:"))
        doc.save(self.state_path)
        outcome, stub, _loop, _log = self.run_once(self.converging_script(),
                                                   max_delegations=20)
        self.assertEqual(outcome.code, exits.STATE_UNRESUMABLE)
        self.assertEqual(stub.invocations, 0)

    def test_an_implementation_change_after_the_freeze_voids_it_on_re_entry(self):
        self._freeze_but_stop()
        with open(os.path.join(self.repo, "production.py"), "w", encoding="utf-8") as fh:
            fh.write("# someone edited the tree between runs\n")

        outcome, stub, _loop, _log = self.run_once(self.converging_script(),
                                                   max_delegations=20)
        self.assertEqual(outcome.code, exits.CLOSURE_NOT_PROVEN)
        self.assertIn("changed after the freeze", outcome.reason)
        self.assertEqual(stub.invocations, 0, "no lifecycle step runs on a void freeze")
        self.assertNotEqual(self.doc().run_result(), "DONE")


class LifecycleGate(FinalizationHarness):
    def test_a_refusing_lifecycle_skill_stops_the_run_and_keeps_the_freeze(self):
        self.make(ONE_TASK)
        script = self.converging_script()
        script["lifecycle:spec-close"] = [reject("CLOSE-001")]
        outcome, _stub, _loop, _log = self.run_once(script)

        self.assertEqual(outcome.code, exits.CLOSURE_NOT_PROVEN)
        self.assertIn("/spec-close refused", outcome.reason)
        self.assertIn("never write the status", outcome.remediation.lower().replace(
            "forbids writing the status", "never write the status"))
        self.assertNotEqual(self.doc().run_result(), "DONE")
        record = closure.parse(self.doc().body("Closure delta"))
        self.assertEqual(record["phase"], "LIFECYCLE:spec-review",
                         "the step that passed is recorded; the one that refused is not")

    def test_an_unreadable_lifecycle_response_is_a_refusal(self):
        self.make(ONE_TASK)
        script = self.converging_script()
        script["lifecycle:spec-review"] = ["Yeah looks fine to me."]
        outcome, _stub, _loop, _log = self.run_once(script)
        self.assertEqual(outcome.code, exits.CLOSURE_NOT_PROVEN)
        self.assertIn("/spec-review refused", outcome.reason)


if __name__ == "__main__":
    unittest.main()
