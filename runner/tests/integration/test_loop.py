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
import subprocess
import tempfile
import unittest

from sdd_runner import exits, state
from sdd_runner.backends.stub import StubBackend
from sdd_runner.log import RunLog
from sdd_runner.loop import Loop
from tests.support import GREEN_BASELINE, TASKS, finalization_flat, fixture, make_repo

FOUR_TASKS = """# Tasks: fixture

## Phase 2: Implementation

- [ ] T001 - First. Covers: AC-001. Verify: the suite passes.
- [ ] T002 - Second. Covers: AC-001. Verify: the suite passes.
- [ ] T003 - Third. Covers: AC-001. Verify: the suite passes.
- [ ] T004 - Fourth. Covers: AC-001. Verify: the suite passes.
"""


class LoopHarness(unittest.TestCase):
    def build(self, script, tasks=TASKS, max_iterations=3, max_delegations=None, notify=None,
              environ={}):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        repo, feature_dir = make_repo(self.tmp.name, tasks=tasks)
        stub = StubBackend(script=list(script))
        counter = itertools.count()
        log = RunLog(os.path.join(feature_dir, "run.jsonl"), clock=lambda: next(counter),
                     environ=environ)
        loop = Loop(repo, feature_dir, stub, log, max_iterations=max_iterations,
                    max_delegations=max_delegations, clock=lambda: 0, notify=notify,
                    baseline_cmd=GREEN_BASELINE)
        return loop, stub, repo, feature_dir, log


class Converge(LoopHarness):
    def test_two_tasks_converge_and_leave_no_commit(self):
        script = ([fixture("worker_done.md"), fixture("reviewer_approve.md")] * 2
                  + finalization_flat())
        loop, stub, repo, feature_dir, log = self.build(script)
        outcome = loop.run()

        self.assertEqual(outcome.code, exits.OK)
        self.assertEqual(outcome.result, "DONE")
        self.assertEqual(stub.invocations, 4 + len(finalization_flat()))

        doc = state.Orchestration.load(os.path.join(feature_dir, "ORCHESTRATION.md"))
        self.assertEqual(doc.run_result(), "DONE")
        for section in ("State", "Attempts", "Findings", "Delegation log",
                        "Escalations", "Cap changes", "Closure delta", "Run result"):
            self.assertIsNotNone(doc.get(section), "missing 031 section %r" % section)

        # FR-012: the runner creates no commit.
        out = subprocess.run(["git", "-C", repo, "log", "--oneline"],
                             capture_output=True, text=True).stdout.strip().splitlines()
        self.assertEqual(len(out), 1, "the runner must not commit")

    def test_every_decision_is_reconstructible_from_run_jsonl_alone(self):
        script = ([fixture("worker_done.md"), fixture("reviewer_approve.md")] * 2
                  + finalization_flat())
        loop, stub, repo, feature_dir, log = self.build(script)
        loop.run()
        with open(os.path.join(feature_dir, "run.jsonl"), encoding="utf-8") as fh:
            lines = fh.read().splitlines()
        events = [json.loads(l)["event"] for l in lines]
        for required in ("plan", "dispatch", "response", "completion", "verdict",
                         "counters", "finalize-start", "freeze", "core-complete", "finish"):
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

    def test_a_technical_question_is_classified_auto_but_still_stops_the_run(self):
        """Auto-resolvable is a classification, not a capability yet.

        Resolving it needs the deep-reasoner call and the DECISIONS.md write that
        T014 owns. Until then the run stops: continuing would either review work
        the worker never did, or re-delegate the same blocked task forever. It is
        recorded as auto-resolvable, it is NOT written into the waiting list, and
        no notification is sent - those are for human-gated questions.
        """
        sent = []
        script = [fixture("worker_blocked.md")]
        loop, stub, repo, feature_dir, log = self.build(script, notify=sent.append)
        outcome = loop.run()
        self.assertEqual(outcome.code, exits.HUMAN_ESCALATION)
        self.assertEqual(outcome.result, "PAUSED")
        self.assertTrue(outcome.resumable)
        self.assertIn("auto-resolvable", outcome.reason)
        self.assertTrue(any(e["event"] == "escalation-auto" for e in log.events))
        self.assertEqual(sent, [], "an auto-resolvable question notifies nobody")
        doc = state.Orchestration.load(os.path.join(feature_dir, "ORCHESTRATION.md"))
        self.assertNotIn("waiting", doc.body("Escalations"))


class FingerprintIdentifiesTheTree(LoopHarness):
    """AUDIT-7: the fingerprint identified uncommitted work, not the tree.

    It was built from `git status --porcelain` plus `git diff HEAD` — both of
    which describe the delta from HEAD. An agent that commits moves HEAD and
    empties both, so two fingerprints either side of a delegation that changed
    the repository came out identical. Every approval, the freeze and the
    closure delta rest on this value.
    """

    def _loop(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        repo, feature_dir = make_repo(self.tmp.name, tasks=TASKS)
        log = RunLog(os.path.join(feature_dir, "run.jsonl"), clock=lambda: 0, environ={})
        return Loop(repo, feature_dir, StubBackend(script=["x"]), log, clock=lambda: 0,
                    baseline_cmd=GREEN_BASELINE), repo

    @staticmethod
    def _commit(repo, message):
        subprocess.run(["git", "-C", repo, "add", "-A"], capture_output=True, check=True)
        subprocess.run(["git", "-C", repo, "commit", "-qm", message],
                       capture_output=True, check=True)

    def test_a_commit_changes_the_fingerprint(self):
        loop, repo = self._loop()
        before = loop.fingerprint()
        with open(os.path.join(repo, "impl.py"), "w", encoding="utf-8") as fh:
            fh.write("# work an agent did\n")
        self._commit(repo, "agent committed its work")
        self.assertNotEqual(loop.fingerprint(), before,
                            "a committed change must not look like an unchanged tree")

    def test_committing_is_distinguishable_from_never_having_changed(self):
        loop, repo = self._loop()
        clean = loop.fingerprint()
        with open(os.path.join(repo, "impl.py"), "w", encoding="utf-8") as fh:
            fh.write("# work\n")
        dirty = loop.fingerprint()
        self._commit(repo, "commit it")
        committed = loop.fingerprint()
        self.assertEqual(len({clean, dirty, committed}), 3,
                         "clean, dirty and committed must be three distinct states")

    def test_an_empty_commit_still_moves_the_fingerprint(self):
        """HEAD is part of the identity, so history changes count."""
        loop, repo = self._loop()
        before = loop.fingerprint()
        subprocess.run(["git", "-C", repo, "commit", "-q", "--allow-empty", "-m", "empty"],
                       capture_output=True, check=True)
        self.assertNotEqual(loop.fingerprint(), before)


class ReadOnlyAgentsMayNotWrite(LoopHarness):
    """SEC-002 / 031 FR-008: an out-of-scope write fails closed.

    Every attempt records an allowed-path scope, and nothing checked it: the
    scope was the whole repo for every agent and no code compared it against
    what actually changed. The reviewers' own contracts say "Read-only - it
    never modifies code", so their recorded scope is empty and any change during
    their delegation is an unattributed-path write.

    031's abort contract puts unexplained out-of-scope writes with corrupt
    provenance: ABORTED, resumable: no, never guess.
    """

    class WritingReviewer(StubBackend):
        def __init__(self, script, repo):
            super().__init__(script=script)
            self.repo = repo

        def run(self, system_prompt, task_prompt, path_scope, timeout):
            response = super().run(system_prompt, task_prompt, path_scope, timeout)
            if "domain-reviewer" in (system_prompt or ""):
                with open(os.path.join(self.repo, "sneaky.py"), "w", encoding="utf-8") as fh:
                    fh.write("# written by a read-only agent\n")
            return response

    def build_writing(self, script):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        repo, feature_dir = make_repo(self.tmp.name, tasks=TASKS)
        stub = self.WritingReviewer(list(script), repo)
        counter = itertools.count()
        log = RunLog(os.path.join(feature_dir, "run.jsonl"), clock=lambda: next(counter),
                     environ={})
        loop = Loop(repo, feature_dir, stub, log, clock=lambda: 0,
                    baseline_cmd=GREEN_BASELINE)
        return loop, stub, repo, feature_dir, log

    def test_a_reviewer_that_writes_aborts_the_run_unresumably(self):
        loop, stub, repo, feature_dir, log = self.build_writing(
            [fixture("worker_done.md"), fixture("reviewer_approve.md")])
        outcome = loop.run()

        self.assertEqual(outcome.code, exits.STATE_UNRESUMABLE)
        self.assertEqual(outcome.result, "ABORTED")
        self.assertFalse(outcome.resumable, "031 makes unexplained out-of-scope writes terminal")
        self.assertIn("domain", outcome.reason)
        self.assertIn("outside its recorded scope", outcome.reason)

        doc = state.Orchestration.load(os.path.join(feature_dir, "ORCHESTRATION.md"))
        self.assertEqual(doc.run_result(), "ABORTED")
        self.assertFalse(doc.resumable())

    def test_the_scope_recorded_for_a_reviewer_is_empty(self):
        loop, stub, repo, feature_dir, log = self.build(
            [fixture("worker_done.md"), fixture("reviewer_approve.md")] + finalization_flat())
        loop.run()
        scopes = {e["agent"]: e["scope"] for e in log.events if e["event"] == "dispatch"}
        self.assertEqual(scopes["domain"], [])
        self.assertEqual(scopes["worker"], [repo])

    def test_a_worker_writing_is_not_an_out_of_scope_write(self):
        class WritingWorker(self.WritingReviewer):
            def run(self, system_prompt, task_prompt, path_scope, timeout):
                response = StubBackend.run(self, system_prompt, task_prompt, path_scope, timeout)
                if "implementer" in (system_prompt or ""):
                    with open(os.path.join(self.repo, "impl.py"), "w", encoding="utf-8") as fh:
                        fh.write("# ordinary work\n")
                return response

        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        repo, feature_dir = make_repo(self.tmp.name, tasks=TASKS)
        stub = WritingWorker([fixture("worker_done.md"), fixture("reviewer_approve.md")] * 2
                             + finalization_flat(), repo)
        counter = itertools.count()
        log = RunLog(os.path.join(feature_dir, "run.jsonl"), clock=lambda: next(counter),
                     environ={})
        outcome = Loop(repo, feature_dir, stub, log, clock=lambda: 0,
                       baseline_cmd=GREEN_BASELINE).run()
        self.assertNotEqual(outcome.code, exits.STATE_UNRESUMABLE)


class CommitsDuringDelegationAreDetected(LoopHarness):
    """AC-018: a delegated agent that COMMITS must not look like a clean tree.

    The fingerprint was built from `git status --porcelain` plus `git diff HEAD`,
    and both measure the delta *from* HEAD. An agent that commits moves HEAD and
    empties both, so afterwards the tree reads as pristine — which is exactly the
    state these tests assert before checking that staleness was still detected.
    Detection therefore cannot come from status or diff; it can only come from
    `HEAD` being part of the identity.
    """

    class CommittingReviewer(StubBackend):
        """A read-only agent that commits. Its contract forbids writing at all."""

        def __init__(self, script, repo):
            super().__init__(script=script)
            self.repo = repo

        def run(self, system_prompt, task_prompt, path_scope, timeout):
            response = super().run(system_prompt, task_prompt, path_scope, timeout)
            if "domain-reviewer" in (system_prompt or ""):
                with open(os.path.join(self.repo, "sneaked.py"), "w", encoding="utf-8") as fh:
                    fh.write("# committed from inside a delegation\n")
                subprocess.run(["git", "-C", self.repo, "add", "-A"],
                               capture_output=True, check=True)
                subprocess.run(["git", "-C", self.repo, "commit", "-qm", "agent commit"],
                               capture_output=True, check=True)
            return response

    def _build_committing(self, script):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        repo, feature_dir = make_repo(self.tmp.name, tasks=TASKS)
        stub = self.CommittingReviewer(list(script), repo)
        counter = itertools.count()
        log = RunLog(os.path.join(feature_dir, "run.jsonl"), clock=lambda: next(counter),
                     environ={})
        loop = Loop(repo, feature_dir, stub, log, clock=lambda: 0,
                    baseline_cmd=GREEN_BASELINE)
        return loop, stub, repo, feature_dir, log

    @staticmethod
    def _tree_is_pristine(repo):
        """Status and diff over the REVIEWABLE tree, excluding what the loop writes.

        `ORCHESTRATION.md` and `run.jsonl` are the runner's own bookkeeping and
        are excluded from the fingerprint too, so including them here would be
        measuring something the fingerprint never looks at.
        """
        excluded = ("ORCHESTRATION.md", "run.jsonl", "PR_DESCRIPTION.md", "TASKS.md")
        raw = subprocess.run(["git", "-C", repo, "status", "--porcelain", "-uall"],
                             capture_output=True, text=True).stdout
        status = "\n".join(line for line in raw.splitlines()
                            if not any(line.strip().endswith(x) for x in excluded)).strip()
        pathspec = ["."] + [":(exclude)*%s" % name for name in excluded]
        diff = subprocess.run(["git", "-C", repo, "diff", "HEAD", "--"] + pathspec,
                              capture_output=True, text=True).stdout.strip()
        return status, diff

    def test_a_reviewer_that_commits_is_caught_though_the_tree_reads_clean(self):
        loop, stub, repo, feature_dir, log = self._build_committing(
            [fixture("worker_done.md"), fixture("reviewer_approve.md")])
        outcome = loop.run()

        # The tree the commit left behind is pristine: nothing modified, nothing
        # untracked, no diff against HEAD.
        status, diff = self._tree_is_pristine(repo)
        self.assertEqual(status, "", "the commit must leave no status entries")
        self.assertEqual(diff, "", "the commit must leave no diff against HEAD")

        # And it was still caught, which can only be because HEAD is hashed.
        self.assertEqual(outcome.code, exits.STATE_UNRESUMABLE)
        self.assertEqual(outcome.result, "ABORTED")
        self.assertFalse(outcome.resumable)
        self.assertIn("outside its recorded scope", outcome.reason)
        self.assertTrue(any(e["event"] == "out-of-scope-write" for e in log.events))

    def test_the_fingerprints_recorded_for_that_delegation_differ(self):
        loop, stub, repo, feature_dir, log = self._build_committing(
            [fixture("worker_done.md"), fixture("reviewer_approve.md")])
        loop.run()
        event = [e for e in log.events if e["event"] == "out-of-scope-write"][0]
        self.assertNotEqual(event["pre_fingerprint"], event["post_fingerprint"])


class SecretsNeverReachTheArtifacts(LoopHarness):
    """AC-012 in full: the sentinel must be absent from BOTH files.

    The regression this pins: on the human-gated escalation path the worker's
    question is copied verbatim into the Escalations section of
    ORCHESTRATION.md. Redaction living only in the run.jsonl writer let a
    credential an agent echoed land in the state file in clear (D025).
    """

    SENTINEL = "sk-ant-sentinel-never-log-0001"

    def _blocked_with_secret(self):
        return ("Stopped.\n\n```yaml\nstatus: BLOCKED\ndecisions:\n"
                "  - What pricing tier applies, and do I bill it with key %s?\n```\n"
                % self.SENTINEL)

    def setUp(self):
        self._saved = os.environ.get("ANTHROPIC_API_KEY")
        os.environ["ANTHROPIC_API_KEY"] = self.SENTINEL
        self.addCleanup(self._restore)

    def _restore(self):
        if self._saved is None:
            os.environ.pop("ANTHROPIC_API_KEY", None)
        else:
            os.environ["ANTHROPIC_API_KEY"] = self._saved

    def test_a_secret_an_agent_echoes_reaches_neither_artifact(self):
        # environ=None means the real environment, as the CLI uses it.
        loop, stub, repo, feature_dir, log = self.build([self._blocked_with_secret()],
                                                        environ=None)
        outcome = loop.run()
        self.assertEqual(outcome.code, exits.HUMAN_ESCALATION)

        for name in ("ORCHESTRATION.md", "run.jsonl"):
            with self.subTest(artifact=name):
                with open(os.path.join(feature_dir, name), encoding="utf-8") as fh:
                    body = fh.read()
                self.assertNotIn(self.SENTINEL, body)
                self.assertIn("[REDACTED]", body)

    def test_the_escalation_is_still_legible_after_redaction(self):
        """Redaction removes the secret, not the question."""
        loop, stub, repo, feature_dir, log = self.build([self._blocked_with_secret()],
                                                        environ=None)
        loop.run()
        doc = state.Orchestration.load(os.path.join(feature_dir, "ORCHESTRATION.md"))
        escalations = doc.body("Escalations")
        self.assertIn("waiting", escalations)
        self.assertIn("What pricing tier applies", escalations)


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
