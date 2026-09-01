"""Finalization, freeze and closure delta — spec 031 FR-013, spec 040 T014.

The property under test throughout: **the runner says DONE only when it can
demonstrate the run is closed.** Every path that cannot demonstrate it must stop
with a reason and a remediation, and must leave the record readable.
"""

import itertools
import os
import socket
import subprocess
import tempfile
import unittest

from sdd_runner import closure, exits, state
from sdd_runner.backends import Response
from sdd_runner.backends.stub import StubBackend
from sdd_runner.log import RunLog
from sdd_runner.loop import Loop
from tests.support import GREEN_BASELINE, approve_block, finalization_keys, make_repo

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
                 baseline_cmd=GREEN_BASELINE):
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
        self.assertEqual(len(self.events(log, "core-complete")), 1,
                         "the run ends on 040's side of the seam (D034)")
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

    def test_an_undeclared_verification_blocks_the_close(self):
        """AUDIT-1: recording condition 2 as unobserved and closing anyway.

        031 makes a green, non-mutating verification a CONDITION of DONE. The
        runner used to write "NOT DECLARED" into the closure record and reach
        DONE regardless — the condition became a log line, and a run could report
        success having verified nothing.
        """
        self.make(ONE_TASK)
        outcome, _stub, _loop, _log = self.run_once(self.converging_script(),
                                                    baseline_cmd=None)
        self.assertEqual(outcome.code, exits.CLOSURE_NOT_PROVEN)
        self.assertEqual(outcome.result, "PAUSED")
        self.assertTrue(outcome.resumable)
        self.assertIn("condition 2", outcome.reason)
        self.assertIn("--baseline", outcome.remediation)
        self.assertNotEqual(self.doc().run_result(), "DONE")

    def test_a_declared_green_verification_closes_and_is_recorded(self):
        self.make(ONE_TASK)
        outcome, _stub, _loop, _log = self.run_once(self.converging_script(),
                                                    baseline_cmd=["true"])
        self.assertEqual(outcome.code, exits.OK)
        record = closure.parse(self.doc().body("Closure delta"))
        self.assertEqual(record["verification"], closure.VERIFY_PASS)

    def test_a_verification_that_mutates_the_tree_blocks(self):
        self.make(ONE_TASK)
        script = os.path.join(self.tmp.name, "mutate.sh")
        with open(script, "w", encoding="utf-8") as fh:
            fh.write("#!/bin/sh\necho mutated >> agents/implementer.md\n")
        os.chmod(script, 0o755)
        outcome, _stub, _loop, _log = self.run_once(self.converging_script(),
                                                    baseline_cmd=[script])
        self.assertEqual(outcome.code, exits.NOT_CONVERGED)
        self.assertIn(closure.VERIFY_MUTATED, outcome.reason)
        self.assertNotEqual(self.doc().run_result(), "DONE")


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


class CommittedWorkStalesApprovals(FinalizationHarness):
    """AC-018, approval half: a commit must invalidate an approval like any change.

    `MutatingStub` writes a file; this one commits it. Afterwards the reviewable
    tree is byte-for-byte what it was before the delegation as far as
    `git status` and `git diff HEAD` are concerned — the change is only visible
    in `HEAD`. If the fingerprint did not include it, T001's approval would still
    match and the freeze would happen over a tree nobody re-reviewed.
    """

    class CommittingWorker(StubBackend):
        def __init__(self, script, repo):
            super().__init__(script=script)
            self.repo = repo
            self.commits = 0

        def run(self, system_prompt, task_prompt, path_scope, timeout):
            response = super().run(system_prompt, task_prompt, path_scope, timeout)
            if "implementer" in (system_prompt or ""):
                self.commits += 1
                target = os.path.join(self.repo, "impl-%d.py" % self.commits)
                with open(target, "w", encoding="utf-8") as fh:
                    fh.write("# work %d\n" % self.commits)
                subprocess.run(["git", "-C", self.repo, "add", "-A"],
                               capture_output=True, check=True)
                subprocess.run(["git", "-C", self.repo, "commit", "-qm",
                                "worker commit %d" % self.commits],
                               capture_output=True, check=True)
            return response

    def test_a_committing_worker_stales_the_earlier_approval(self):
        self.make(TWO_TASKS)
        script = {"implementer": [done()] * 6, "domain-reviewer": [approve_block()] * 6}
        script.update(finalization_keys(each=2))

        stub = self.CommittingWorker({k: list(v) for k, v in script.items()}, self.repo)
        log = RunLog(os.path.join(self.feature_dir, "run.jsonl"),
                     clock=lambda: next(self.counter), environ={})
        loop = Loop(self.repo, self.feature_dir, stub, log, clock=lambda: 0, hostname=HOST,
                    pid=os.getpid(), max_delegations=40, baseline_cmd=GREEN_BASELINE)
        outcome = loop.run()

        # The commits left the reviewable tree looking untouched.
        status = subprocess.run(["git", "-C", self.repo, "status", "--porcelain", "-uall"],
                                capture_output=True, text=True).stdout
        leftover = [l for l in status.splitlines()
                    if not l.strip().endswith(("ORCHESTRATION.md", "run.jsonl",
                                               "PR_DESCRIPTION.md", "TASKS.md"))]
        self.assertEqual(leftover, [], "the worker's changes were committed, not left dirty")

        stale = self.events(log, "stale-approvals")
        self.assertTrue(stale, "T002's commit must have staled T001's approval")
        self.assertIn("domain@T001", stale[0]["pairs"])
        self.assertEqual(outcome.code, exits.OK, "fresh re-reviews close the run")


class ClosureRecord(FinalizationHarness):
    """The record 040 writes at the seam, and the delta machinery it hands over.

    The frozen map is persisted for a consumer this spec does not implement: the
    follow-up `Finalizer` compares its closure delta against it (AUDIT-9). The
    delta half of `closure.py` is therefore still asserted here, but directly —
    driving it through a lifecycle dispatch is exactly what D034 removed.
    """

    def test_the_frozen_record_is_persisted_with_an_empty_delta(self):
        self.make(ONE_TASK)
        outcome, _stub, _loop, _log = self.run_once(self.converging_script())
        self.assertEqual(outcome.code, exits.OK)

        body = self.doc().body("Closure delta")
        record = closure.parse(body)
        self.assertEqual(record["phase"], "CORE-COMPLETE")
        self.assertTrue(record["frozen_fingerprint"])
        self.assertTrue(record["frozen"], "the frozen tree map must be persisted")
        self.assertEqual(record["delta"], [],
                         "040 observes no delta; the section stays readable and empty")
        self.assertIn("### Frozen tree", body)
        self.assertIn("### Observed delta", body)

    def test_the_handed_over_delta_still_catches_a_post_freeze_production_change(self):
        """The consumer 040 hands to must be able to catch this; the seam is not.

        Previously this ran through a lifecycle skill that wrote `production.py`
        after the freeze. That dispatch no longer exists, so the guarantee is
        asserted where it actually lives — over the frozen map this runner
        persists.
        """
        self.make(ONE_TASK)
        outcome, _stub, _loop, _log = self.run_once(self.converging_script())
        self.assertEqual(outcome.code, exits.OK)
        frozen = closure.parse(self.doc().body("Closure delta"))["frozen"]

        with open(os.path.join(self.repo, "production.py"), "w", encoding="utf-8") as fh:
            fh.write("# written after the freeze\n")

        delta = closure.observe(self.repo, self.feature_dir, frozen)
        unexpected = closure.unexpected(delta)
        self.assertEqual([r["Path"] for r in unexpected], ["production.py"])
        self.assertIn("not on the closure allowlist", unexpected[0]["Rule"])


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
        """Leave a durable `FROZEN` record: a process that died between two writes.

        `_freeze` persists `FROZEN` and `_close` then persists the terminal phase,
        so `FROZEN` is a real on-disk state whenever a run is interrupted between
        them. It used to be reachable by starving the budget, because three
        lifecycle delegations stood between the freeze and the close; with those
        gone (D034) nothing is dispatched in that gap, so the state is constructed
        instead of provoked. What is under test is the re-entry, not how the
        record got there.
        """
        self.make(ONE_TASK)
        outcome, _stub, _loop, log = self.run_once(self.converging_script())
        self.assertEqual(outcome.code, exits.OK)
        self.assertTrue(self.events(log, "freeze"), "the freeze must have been recorded")

        doc = self.doc()
        body = doc.body("Closure delta")
        self.assertIn("- phase: CORE-COMPLETE", body)
        doc.set_body("Closure delta", body.replace("- phase: CORE-COMPLETE", "- phase: FROZEN", 1))
        doc.set_body("Run result", "\nPAUSED\n\nresumable: yes\n\n")
        doc.save(self.state_path)
        return outcome

    def test_resume_after_freeze_before_done(self):
        self._freeze_but_stop()
        before = closure.parse(self.doc().body("Closure delta"))
        self.assertEqual(before["phase"], "FROZEN")

        outcome, stub, _loop, log = self.run_once(self.converging_script())
        self.assertEqual(outcome.code, exits.OK)
        self.assertTrue(self.events(log, "freeze-reused"), "the freeze must be reused")
        self.assertEqual(self.events(log, "freeze"), [], "and never recomputed")

        # Nothing at all is dispatched: no task work, no second conformance review,
        # and — since D034 — no lifecycle step either.
        self.assertEqual([e["agent"] for e in self.events(log, "dispatch")], [])
        self.assertEqual(stub.invocations, 0)

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

        outcome, stub, _loop, _log = self.run_once(self.converging_script())
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
        outcome, stub, _loop, _log = self.run_once(self.converging_script())
        self.assertEqual(outcome.code, exits.STATE_UNRESUMABLE)
        self.assertEqual(stub.invocations, 0)

    def test_an_implementation_change_after_the_freeze_voids_it_on_re_entry(self):
        self._freeze_but_stop()
        with open(os.path.join(self.repo, "production.py"), "w", encoding="utf-8") as fh:
            fh.write("# someone edited the tree between runs\n")

        outcome, stub, _loop, _log = self.run_once(self.converging_script())
        self.assertEqual(outcome.code, exits.CLOSURE_NOT_PROVEN)
        self.assertIn("changed after the freeze", outcome.reason)
        self.assertEqual(stub.invocations, 0, "nothing is dispatched on a void freeze")
        self.assertNotEqual(self.doc().run_result(), "DONE")


class LifecycleRefusalsAreNotThisRunnersProblem(FinalizationHarness):
    """What the old lifecycle gate tested, inverted by D034.

    These two scripts used to stop the run: a `/spec-close` that refused, and a
    `/spec-review` whose answer carried no readable verdict block. The runner no
    longer dispatches either, so the scripted responses are never consumed and the
    run closes on its own core evidence.

    Kept rather than deleted because a leaking boundary would revive exactly these
    two paths, and a green here would be the loudest possible symptom.
    """

    def _script_with(self, step, response):
        script = self.converging_script()
        script["lifecycle:" + step] = [response]
        return script

    def test_a_refusing_spec_close_does_not_stop_a_run_it_is_never_asked_about(self):
        self.make(ONE_TASK)
        outcome, stub, _loop, log = self.run_once(
            self._script_with("spec-close", reject("CLOSE-001")))

        self.assertEqual(outcome.code, exits.OK)
        self.assertEqual(self.doc().run_result(), "DONE")
        self.assertEqual([e["agent"] for e in self.events(log, "dispatch")
                          if e["agent"].startswith("lifecycle:")], [])
        self.assertNotIn("CLOSE-001", self.doc().body("Findings"))

    def test_an_unreadable_lifecycle_response_is_never_read(self):
        self.make(ONE_TASK)
        outcome, _stub, _loop, log = self.run_once(
            self._script_with("spec-review", "Yeah looks fine to me."))
        self.assertEqual(outcome.code, exits.OK)
        self.assertEqual(self.events(log, "lifecycle"), [])


class CoreBoundary(FinalizationHarness):
    """AC-019 / D034: a converged stub run stops at the core side of `_finalize`.

    040's supported surface ends at the freeze. Lifecycle delegation
    (`/spec-review`, `/spec-close`, `/pr-description`), the closure delta over
    what those skills change, and PR-description evidence belong to the follow-up
    provider spec (AUDIT-9). Their absence is the contract, not an omission: a run
    that dispatched them would be claiming a hand-off 040 never certified.
    """

    def _script_that_would_satisfy_lifecycle(self):
        """A script that WOULD answer every lifecycle step, if one were dispatched.

        Deliberately over-supplied. If the boundary ever leaks, the run does not
        fail on a missing scripted response and quietly look like a harness bug —
        it succeeds, and the assertions below are the only thing that catches it.
        """
        script = {"implementer": [done()] * 3,
                  "domain-reviewer": [approve_block()] * 3,
                  "final-conformance-reviewer": [approve_block()]}
        for step in ("spec-review", "spec-close", "pr-description"):
            script["lifecycle:" + step] = [approve_block()]
        return script

    def test_a_converged_run_dispatches_no_lifecycle_skill(self):
        self.make(ONE_TASK)
        outcome, _stub, _loop, log = self.run_once(self._script_that_would_satisfy_lifecycle())

        self.assertEqual(outcome.code, exits.OK)
        self.assertEqual(outcome.result, "DONE")
        self.assertEqual(self.events(log, "lifecycle"), [])
        self.assertEqual(self.events(log, "lifecycle-skipped"), [])
        self.assertEqual([e["agent"] for e in self.events(log, "dispatch")
                          if e["agent"].startswith("lifecycle:")], [])

    def test_a_converged_run_computes_no_closure_delta(self):
        self.make(ONE_TASK)
        outcome, _stub, _loop, log = self.run_once(self._script_that_would_satisfy_lifecycle())
        self.assertEqual(outcome.code, exits.OK)
        self.assertEqual(self.events(log, "closure-delta"), [])
        self.assertEqual(closure.parse(self.doc().body("Closure delta"))["delta"], [])

    def test_a_converged_run_creates_no_pr_description(self):
        self.make(ONE_TASK)
        outcome, _stub, _loop, _log = self.run_once(self._script_that_would_satisfy_lifecycle())
        self.assertEqual(outcome.code, exits.OK)
        self.assertFalse(os.path.exists(os.path.join(self.feature_dir, "PR_DESCRIPTION.md")))

    def test_the_terminal_core_evidence_is_recorded(self):
        self.make(ONE_TASK)
        outcome, _stub, loop, log = self.run_once(self._script_that_would_satisfy_lifecycle())
        self.assertEqual(outcome.code, exits.OK)

        record = closure.parse(self.doc().body("Closure delta"))
        self.assertEqual(record["phase"], "CORE-COMPLETE")
        self.assertEqual(record["verification"], closure.VERIFY_PASS)
        self.assertEqual(record["frozen_fingerprint"], loop.fingerprint())
        self.assertTrue(record["frozen"], "the frozen tree map is the hand-off datum")
        self.assertTrue(self.events(log, "core-complete"))


if __name__ == "__main__":
    unittest.main()
