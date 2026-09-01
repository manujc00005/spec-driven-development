"""The driver — spec 031 FR-001/FR-008/FR-010/FR-011, spec 040 FR-005/FR-012/FR-013.

Composition only: every rule it applies lives in one of the core modules, which
each cite the 031 FR they implement. This file decides ORDER, not semantics.

Hard prohibitions (spec 040 FR-012): the driver never runs `git commit`,
`git push` or `git merge`, never edits a spec `Status` line, and never writes
outside the feature folder and the delegated agents' path scope.
"""

import hashlib
import os
import socket
import subprocess
import time
from dataclasses import dataclass, field

from . import blocks, closure as closure_mod, exits, resume as resume_mod, state
from . import tasks as tasks_mod
from .backends import BackendPrecondition
from .budget import Budget, BudgetExhausted, default_cap
from .counters import CounterState
from .escalation import classify_all
from .resume import ConcurrentRun, UnresumableState
from .retry import DelegationFailedClosed, RetryPolicy, call_with_retry

REVIEWERS = ("domain", "security", "final-conformance")

# Agents whose own contracts say "Read-only - it never modifies code". Their
# recorded allowed-path scope is therefore EMPTY, and any change to the tree
# during their delegation is an out-of-scope write (031 FR-008, SEC-002). The
# worker legitimately writes, so it keeps the repo scope.
READ_ONLY_AGENTS = REVIEWERS

# The terminal phase of the closure record on 040's side of the `_finalize` seam.
# It is NOT "CLOSED": the feature lifecycle is not closed by this runner, and a
# phase word that implied otherwise would be the claim D034 removed.
CORE_COMPLETE = "CORE-COMPLETE"

AGENT_FILES = {
    "worker": "agents/implementer.md",
    "domain": "agents/domain-reviewer.md",
    "security": "agents/security-reviewer.md",
    "final-conformance": "agents/final-conformance-reviewer.md",
    "deep-reasoner": "agents/deep-reasoner.md",
}

# Level-3 triggers for security review. Do not invent a second trigger list.
SECURITY_TRIGGERS = ("auth", "authorization", "personal data", "payment", "migration",
                     "upload", "secret", "public api", "schema", "persistence")


class UnattributedWrite(RuntimeError):
    """A read-only agent changed the tree.

    031's abort contract files unexplained out-of-scope writes with corrupt
    provenance: ABORTED, resumable: no, never guess.
    """


@dataclass
class Outcome:
    code: int
    result: str                    # DONE | PAUSED | ABORTED
    reason: str = ""
    resumable: bool = True
    escalations: list = field(default_factory=list)
    remediation: str = ""


class Loop:
    def __init__(self, repo, feature_dir, backend, log, max_iterations=3,
                 max_delegations=None, clock=time.time, sleep=lambda s: None,
                 retry_policy=None, notify=None, hostname=None, pid=None,
                 baseline_cmd=None):
        self.repo = repo
        self.feature_dir = feature_dir
        self.backend = backend
        self.log = log
        self.clock = clock
        self.sleep = sleep
        self.notify = notify
        self.retry_policy = retry_policy or RetryPolicy()
        self.counters = CounterState(max_iterations=max_iterations)
        self.max_delegations_override = max_delegations
        self.hostname = hostname or socket.gethostname()
        self.pid = pid if pid is not None else os.getpid()
        self.budget = None
        self.doc = None
        self.attempt_seq = 0
        self.iteration = 0
        # "<reviewer>@<task>" -> the fingerprint that reviewer approved for that
        # task. Keyed by task on purpose: an APPROVE of T001's diff is not an
        # approval of T002's work, and a reviewer-only key would let one leak into
        # the next task whenever the tree happened not to move.
        self.approvals = {}
        self.completed_tasks = set()
        self.implemented_tasks = set()   # a worker came back DONE; the review is what is pending
        self.resumed = None              # the ResumeState this run re-entered from
        self.closure = None              # the persisted freeze/closure record, if any
        self.baseline_cmd = baseline_cmd  # PLAN-mandated verification, when declared

    # -- paths ------------------------------------------------------------
    @property
    def state_path(self):
        return os.path.join(self.feature_dir, "ORCHESTRATION.md")

    @property
    def tasks_path(self):
        return os.path.join(self.feature_dir, "TASKS.md")

    # -- fingerprints -----------------------------------------------------
    def fingerprint(self):
        """Canonical content fingerprint of the reviewable tree (031 FR-011).

        Lifecycle artifacts the loop writes itself are excluded: including them
        would make every state write invalidate its own approvals.
        """
        # `-uall` is load-bearing: without it a wholly-untracked directory collapses
        # to a single `?? src/` line and every file created inside it is invisible
        # to the fingerprint.
        digest = hashlib.sha256()
        # HEAD is part of the identity (AUDIT-7). Without it the fingerprint
        # describes *uncommitted work*, not the tree: `git status` and
        # `git diff HEAD` both measure the delta from HEAD, so an agent that
        # commits empties both and two fingerprints either side of a delegation
        # that changed the repository come out identical.
        head = subprocess.run(["git", "-C", self.repo, "rev-parse", "HEAD"],
                              capture_output=True, text=True)
        digest.update(head.stdout.strip().encode("utf-8"))
        proc = subprocess.run(
            ["git", "-C", self.repo, "status", "--porcelain=v1", "-uall"],
            capture_output=True, text=True)
        # TASKS.md is loop bookkeeping, not implementation: the runner itself
        # writes repair rows into it (031 FR-007) and checks them off when their
        # finding resolves. Counting those writes as an implementation change
        # would invalidate an approval the runner had just been given and force a
        # re-review of a tree nobody touched.
        excluded = ("ORCHESTRATION.md", "run.jsonl", "PR_DESCRIPTION.md", "TASKS.md")
        for line in sorted(proc.stdout.splitlines()):
            path = line[3:].strip()
            if any(path.endswith(x) for x in excluded):
                continue
            digest.update(line.encode("utf-8"))
            full = os.path.join(self.repo, path)
            if os.path.isfile(full):
                with open(full, "rb") as fh:
                    digest.update(hashlib.sha256(fh.read()).digest())
        # The same exclusions must apply to the diff, not only to the file walk:
        # a tracked TASKS.md the runner edited shows up in `git diff HEAD` even
        # though it never appears as an untracked status line.
        pathspec = ["."] + [":(exclude)*%s" % name for name in excluded]
        diff = subprocess.run(["git", "-C", self.repo, "diff", "HEAD", "--"] + pathspec,
                              capture_output=True, text=True)
        digest.update(diff.stdout.encode("utf-8"))
        return digest.hexdigest()[:16]

    # -- state ------------------------------------------------------------
    def _load_or_create_state(self, unchecked_count):
        """Create a fresh document, or re-enter an existing one (031 FR-011).

        Raises ConcurrentRun or UnresumableState. Never guesses.
        """
        if not os.path.exists(self.state_path):
            # Publish the COMPLETE document atomically (AUDIT-6). The earlier form
            # claimed the path with an empty `O_EXCL` file and filled it in
            # afterwards, which excluded correctly but left a window where a
            # contender loaded a truncated document and exited 16 - blaming the
            # state instead of the other runner. `create_exclusive` closes both:
            # nothing is visible until it is whole, and only one contender can
            # make it visible at all.
            cap = self.max_delegations_override or default_cap(unchecked_count)
            doc = state.new_document(self.feature_dir, "runner", self.clock(),
                                     {"max_iterations": self.counters.max_iterations,
                                      "max_delegations": cap,
                                      "pid": self.pid, "host": self.hostname})
            try:
                doc.create_exclusive(self.state_path)
            except FileExistsError:
                raise ConcurrentRun(
                    "another runner published %s while this one was starting; refusing to "
                    "start a second runner" % self.state_path)
            return doc, None

        doc = state.Orchestration.load(self.state_path)
        resumed = resume_mod.inspect(doc, self.state_path,
                                     self.counters.max_iterations, self.hostname)
        return doc, resumed

    def _adopt(self, resumed):
        """Restore the persisted run. Counters and budget are never reset."""
        self.counters = resumed.counters
        self.counters.max_iterations = self.counters.max_iterations
        self.approvals = dict(resumed.approvals)
        self.completed_tasks = set(resumed.completed_tasks)
        self.implemented_tasks = set(resumed.implemented_tasks)
        self.attempt_seq = resumed.attempt_seq
        self.iteration = resumed.iteration
        self.resumed = resumed
        self.closure = resumed.closure

        cap = resumed.budget_cap
        if self.max_delegations_override is not None:
            if self.max_delegations_override < cap:
                raise UnresumableState(
                    "the stored delegation cap is %d and this invocation asked for %d"
                    % (cap, self.max_delegations_override),
                    "031 FR-009 lets re-entry only INCREASE an effective cap. Re-run without the "
                    "override, or pass a value at or above %d." % cap)
            cap = self.max_delegations_override
        self.budget = Budget(cap, used=resumed.budget_used)
        if cap != resumed.budget_cap:
            self.doc.append_line(
                "Cap changes",
                "- max-delegations %d -> %d, explicit override on re-entry, at %s"
                % (resumed.budget_cap, cap, self.clock()))

    def _state_fields(self, phase, note=""):
        return {
            "writer": "sdd_runner",
            "phase": phase,
            "current task": note or "none",
            "current attempt": "A-%03d" % self.attempt_seq if self.attempt_seq else "none",
            "iteration": str(self.iteration),
            "max-iterations": str(self.counters.max_iterations),
            "max-delegations": str(self.budget.cap),
            "delegations used": str(self.budget.used),
            "completed tasks": ", ".join(sorted(self.completed_tasks)),
            "counters": resume_mod.render_counters(self.counters),
            "approvals": resume_mod.render_approvals(self.approvals),
            "runner pid": str(self.pid),
            "runner host": self.hostname,
        }

    def _persist(self, phase, note=""):
        """Write state BEFORE proceeding past any transition (031 FR-008)."""
        self.doc.set_body("State", state.render_fields(self._state_fields(phase, note)))
        self._write_findings()
        self.doc.save(self.state_path)

    def _mark_active(self):
        self.doc.set_body("Run result", "\nACTIVE\n\nresumable: yes\n\n")

    # -- delegation -------------------------------------------------------
    def _system_prompt(self, agent):
        path = os.path.join(self.repo, AGENT_FILES[agent])
        if os.path.isfile(path):
            with open(path, encoding="utf-8") as fh:
                return fh.read()
        return "# %s\n(agent file not found at %s)" % (agent, AGENT_FILES[agent])

    @staticmethod
    def _cell(value):
        """One markdown table cell: single line, no pipes, bounded."""
        text = " ".join(str(value or "-").split()).replace("|", "/")
        return (text[:117] + "...") if len(text) > 120 else (text or "-")

    def _attempt_row(self, attempt, task, agent, objective, lifecycle, scope,
                     pre, post, outcome):
        self.doc.append_line("Attempts", "| " + " | ".join([
            attempt, task or "-", agent, self._cell(objective), lifecycle,
            ";".join(scope or []) or "-", pre or "-", post or "-",
            outcome or "-", str(self.clock()),
        ]) + " |")

    @staticmethod
    def _is_read_only(agent):
        return agent in READ_ONLY_AGENTS

    def _scope_for(self, agent):
        """The allowed-path scope recorded for this attempt, and enforced after it."""
        return [] if self._is_read_only(agent) else [self.repo]

    def _delegate(self, agent, prompt, path_scope, task="", objective=None):
        # 031: prove `Delegations used + 1 <= effective max delegations` BEFORE
        # allocating the attempt. An over-budget call is never made, and it never
        # leaves a dangling DISPATCHED row behind either.
        if not self.budget.can_dispatch():
            raise BudgetExhausted(self.budget.used, self.budget.cap)
        self.attempt_seq += 1
        attempt = "A-%03d" % self.attempt_seq
        pre = self.fingerprint()
        objective = objective or prompt
        self._attempt_row(attempt, task, agent, objective, "DISPATCHED", path_scope,
                          pre, "", "")
        self._persist("DELEGATE", task or "%s -> %s" % (attempt, agent))
        self.log.emit("dispatch", attempt=attempt, agent=agent, task=task, objective=objective,
                      scope=list(path_scope), pre_fingerprint=pre,
                      budget_used=self.budget.used, budget_cap=self.budget.cap)

        system = self._system_prompt(agent)
        response = call_with_retry(
            lambda timeout: self.backend.run(system, prompt, path_scope, timeout),
            self.retry_policy, self.budget, self.sleep,
            on_attempt=lambda n: self.log.emit("attempt", attempt=attempt, n=n, agent=agent),
            reason="%s/%s" % (attempt, agent))

        post = self.fingerprint()
        if self._is_read_only(agent) and post != pre:
            # 031 FR-008: "a change outside the recorded scope fails closed as an
            # unattributed-path escalation". Its abort contract files unexplained
            # out-of-scope writes with corrupt provenance - terminal, never guessed.
            self._attempt_row(attempt, task, agent, objective, "FAILED", path_scope,
                              pre, post, "OUT-OF-SCOPE WRITE")
            self.log.emit("out-of-scope-write", attempt=attempt, agent=agent, task=task,
                          pre_fingerprint=pre, post_fingerprint=post)
            raise UnattributedWrite(
                "%s (%s) changed the tree outside its recorded scope: it is a read-only agent, "
                "yet the fingerprint moved from %s to %s during its delegation"
                % (agent, attempt, pre, post))
        self.doc.append_line("Delegation log",
                             "- %s %s: dispatched, responded (pre %s -> post %s)"
                             % (attempt, agent, pre, post))
        self.log.emit("response", attempt=attempt, agent=agent, post_fingerprint=post,
                      chars=len(response.text or ""), backend=response.backend)
        return attempt, response, post, pre

    # -- the circuit ------------------------------------------------------
    def run(self):
        with open(self.tasks_path, encoding="utf-8") as fh:
            tasks_text = fh.read()
        pending = tasks_mod.independently_runnable(tasks_text)

        try:
            self.doc, resumed = self._load_or_create_state(len(pending))
        except ConcurrentRun as exc:
            self.log.emit("refused", kind="concurrent", reason=str(exc))
            return Outcome(exits.CONCURRENT_RUN, "ABORTED", str(exc), resumable=True)
        except UnresumableState as exc:
            self.log.emit("refused", kind="unresumable", reason=exc.reason,
                          remediation=exc.remediation)
            return Outcome(exits.STATE_UNRESUMABLE, "ABORTED", exc.reason,
                           resumable=False, remediation=exc.remediation)

        if resumed is None:
            cap = self.max_delegations_override or default_cap(len(pending))
            self.budget = Budget(cap)
        else:
            try:
                self._adopt(resumed)
            except UnresumableState as exc:
                self.log.emit("refused", kind="unresumable", reason=exc.reason,
                              remediation=exc.remediation)
                return Outcome(exits.STATE_UNRESUMABLE, "ABORTED", exc.reason,
                               resumable=False, remediation=exc.remediation)
            if resumed.open_escalations:
                reason = ("re-entry blocked: %d escalation(s) are still waiting for a maintainer "
                          "answer" % len(resumed.open_escalations))
                self.log.emit("refused", kind="open-escalation",
                              escalations=resumed.open_escalations)
                return Outcome(exits.HUMAN_ESCALATION, "PAUSED", reason, resumable=True,
                               escalations=resumed.open_escalations,
                               remediation="answer them in DECISIONS.md and clear the 'waiting' "
                                           "rows from the Escalations section, then re-enter")
            self.log.emit("resume", prior_result=resumed.prior_result,
                          recovered_from_interrupt=resumed.recovered_from_interrupt,
                          completed=sorted(resumed.completed_tasks),
                          blocked=sorted(resumed.blocked_tasks),
                          budget_used=resumed.budget_used, budget_cap=self.budget.cap,
                          counters=resume_mod.render_counters(self.counters),
                          findings=sorted(self.counters.findings))

        runnable = [t for t in pending if t.id not in self.completed_tasks]
        skipped = [t.id for t in pending if t.id in self.completed_tasks]
        self._mark_active()
        self.log.emit("plan", unchecked=len(pending), runnable=[t.id for t in runnable],
                      skipped=skipped, budget_cap=self.budget.cap,
                      budget_used=self.budget.used,
                      max_iterations=self.counters.max_iterations,
                      resumed=resumed is not None)
        self._persist("PLAN", "%d runnable, %d already complete" % (len(runnable), len(skipped)))

        escalations = []
        for task in runnable:
            try:
                outcome = self._process_task(task)
            except BudgetExhausted as exc:
                self.log.emit("abort", kind="budget", detail=str(exc))
                return self._finish("ABORTED", exits.BUDGET_EXHAUSTED, str(exc), resumable=True)
            except DelegationFailedClosed as exc:
                self.log.emit("abort", kind="delegation-failed-closed", detail=str(exc))
                return self._finish("ABORTED", exits.INTERNAL_ERROR, str(exc), resumable=True)
            except UnattributedWrite as exc:
                self.log.emit("abort", kind="unattributed-write", detail=str(exc))
                return self._finish("ABORTED", exits.STATE_UNRESUMABLE, str(exc),
                                    resumable=False)
            except BackendPrecondition as exc:
                self.log.emit("abort", kind="backend", detail=str(exc))
                return self._finish("ABORTED", exits.BACKEND_PRECONDITION, str(exc),
                                    resumable=True)
            if outcome is not None:
                if outcome.result == "PAUSED":
                    escalations.extend(outcome.escalations)
                    return self._finish("PAUSED", exits.HUMAN_ESCALATION, outcome.reason,
                                        resumable=True, escalations=escalations)
                return outcome

        # Every task was PROCESSED; that is not the same as the RUN being closed.
        # Finalization is what may say DONE (031 FR-013).
        try:
            return self._finalize(runnable)
        except BudgetExhausted as exc:
            self.log.emit("abort", kind="budget", phase="finalization", detail=str(exc))
            return self._finish("ABORTED", exits.BUDGET_EXHAUSTED, str(exc), resumable=True)
        except DelegationFailedClosed as exc:
            self.log.emit("abort", kind="delegation-failed-closed", phase="finalization",
                          detail=str(exc))
            return self._finish("ABORTED", exits.INTERNAL_ERROR, str(exc), resumable=True)
        except UnattributedWrite as exc:
            self.log.emit("abort", kind="unattributed-write", phase="finalization",
                          detail=str(exc))
            return self._finish("ABORTED", exits.STATE_UNRESUMABLE, str(exc), resumable=False)
        except BackendPrecondition as exc:
            self.log.emit("abort", kind="backend", phase="finalization", detail=str(exc))
            return self._finish("ABORTED", exits.BACKEND_PRECONDITION, str(exc), resumable=True)

    # -- one task's convergence cycle ------------------------------------
    def _open_findings_for(self, task_id):
        return [r for r in self.counters.findings.values()
                if r.task == task_id and r.status == "open"]

    def _needs_implementation(self, task):
        """Is a worker delegation the next thing this task needs?

        Yes when it has never been implemented, and yes when a finding against it
        is still awaiting its repair. No when the work landed and what is pending
        is the review - which is what stops a resume from repairing twice.
        """
        # A synthetic malformed-block finding is not repairable by a worker: no
        # code change fixes a reviewer's formatting. The next round simply
        # re-reviews, and the reviewer's no-progress cap ends it if it persists.
        pending_repairs = [r for r in self._open_findings_for(task.id)
                           if not r.repair_done and not r.synthetic]
        if pending_repairs:
            return True
        return task.id not in self.implemented_tasks

    def _process_task(self, task):
        """implement -> review -> repair -> re-review, until converged, cap or budget.

        Termination is not this loop's own invention: the per-reviewer no-progress
        streak, the per-finding failed-repair total, and the monotonic delegation
        budget each end it, and 031 makes the budget the global backstop for the
        case where a reviewer keeps finding genuinely new defects.
        """
        while True:
            if self._needs_implementation(task):
                outcome = self._implement(task)
                if outcome is not None:
                    return outcome

            required = self._required_reviewers(task)
            current = self.fingerprint()
            # An APPROVE is valid only for the fingerprint it was given on, so any
            # change re-schedules EVERY stale required reviewer, not only the one
            # that rejected (031 FR-011).
            stale = [r for r in required
                     if self.approvals.get("%s@%s" % (r, task.id)) != current]
            if not stale:
                self._complete(task)
                return None

            for reviewer in stale:
                if self.counters.would_exceed(reviewer):
                    reason = ("reviewer %r reached the no-progress cap (%d) on %s"
                              % (reviewer, self.counters.max_iterations, task.id))
                    self.log.emit("abort", kind="cap", scope="reviewer", reviewer=reviewer,
                                  task=task.id, detail=reason)
                    return self._finish("ABORTED", exits.CAP_ABORT, reason, resumable=True)

                self._review(reviewer, task, current)

                breach = self.counters.breached()
                if breach:
                    kind, name = breach
                    if kind == "finding":
                        row = self.counters.findings[name]
                        reason = ("finding %s failed to converge: %d failed repairs at the cap of "
                                  "%d. Required action still unmet: %s"
                                  % (name, row.reject_total, self.counters.max_iterations,
                                     row.required_action or "(none recorded)"))
                    else:
                        reason = ("reviewer %r failed to converge: %d consecutive rejects that "
                                  "resolved nothing" % (name, self.counters.max_iterations))
                    self.log.emit("abort", kind="cap", scope=kind, name=name, task=task.id,
                                  detail=reason)
                    return self._finish("ABORTED", exits.CAP_ABORT, reason, resumable=True)

    def _implement(self, task):
        """Delegate the initial implementation, or the repair a finding is waiting on."""
        self.iteration += 1
        pending = [r for r in self._open_findings_for(task.id)
                   if not r.repair_done and not r.synthetic]
        if pending:
            row = pending[0]
            objective = "%s%s" % (resume_mod.REPAIR_OBJECTIVE_PREFIX, row.identity)
            brief = ("Repair %s - %s\nFinding %s (%s): %s\nRequired action: %s"
                     % (task.id, task.title, row.identity, row.severity,
                        row.finding_id, row.required_action))
        else:
            row = None
            objective = resume_mod.IMPLEMENTATION_OBJECTIVE
            brief = "Implement %s - %s" % (task.id, task.title)

        attempt, response, post, _pre = self._delegate(
            "worker", brief, self._scope_for("worker"), task=task.id, objective=objective)
        completion = blocks.parse_worker(response.text)
        self.log.emit("completion", task=task.id, kind=objective, status=completion.status,
                      malformed=completion.malformed, errors=completion.errors,
                      finding=row.identity if row else None)
        self._attempt_row(attempt, task.id, "worker", objective, "RESPONDED", [self.repo],
                          "", post, completion.status)

        if not completion.done:
            return self._handle_block(task, completion)

        self.implemented_tasks.add(task.id)
        if row is not None:
            # Only a subsequent APPROVE resolves the finding (031 FR-007). What a
            # worker DONE establishes is that a repair was ATTEMPTED, which is the
            # precondition for the next REJECT to count as a failed repair.
            self.counters.record_repair_done(row.identity)
            self.log.emit("repair-done", task=task.id, finding=row.identity)
        self._persist("IMPLEMENTED", task.id)
        return None

    def _handle_block(self, task, completion):
        classifications = classify_all(completion.decisions)
        for c in classifications:
            self.log.emit("escalation", task=task.id, gated=c.gated, trigger=c.trigger,
                          question=c.question, reason=c.reason)
        gated = [c for c in classifications if c.gated]
        if gated:
            self.doc.set_body("Escalations", "\n" + "\n".join(
                "- **waiting** (%s) on %s: %s" % (c.trigger, task.id, c.question)
                for c in gated) + "\n\n")
            self._persist("ESCALATED", task.id)
            if self.notify:
                self.notify({"event": "human-escalation", "task": task.id,
                             "questions": [c.question for c in gated],
                             "triggers": [c.trigger for c in gated]})
            return Outcome(exits.HUMAN_ESCALATION, "PAUSED",
                           "human-gated escalation on %s" % task.id,
                           escalations=[c.question for c in gated])
        # Auto-resolvable: recorded, and the run stops rather than looping on a
        # worker that cannot proceed. The deep-reasoner call and the DECISIONS.md
        # write are T014's work, not this one's.
        self.log.emit("escalation-auto", task=task.id,
                      questions=[c.question for c in classifications])
        reason = ("worker BLOCKED on %s with a technically auto-resolvable question, and "
                  "automatic resolution is not implemented yet (T014)" % task.id)
        return Outcome(exits.HUMAN_ESCALATION, "PAUSED", reason, resumable=True,
                       escalations=[c.question for c in classifications])

    def _complete(self, task):
        self.completed_tasks.add(task.id)
        self._set_task_checkbox(task.id, True)
        self.attempt_seq += 1
        self._attempt_row("A-%03d" % self.attempt_seq, task.id, "worker",
                          resume_mod.TASK_COMPLETE_OBJECTIVE, "VERIFIED", [self.repo],
                          "", self.fingerprint(), "DONE")
        self.log.emit("task-complete", task=task.id,
                      reviewers=self._required_reviewers(task))
        self._persist("TASK COMPLETE", task.id)

    def _required_reviewers(self, task):
        required = ["domain"]
        haystack = (task.raw or "").lower()
        if any(trigger in haystack for trigger in SECURITY_TRIGGERS):
            required.append("security")
        return required

    def _review(self, reviewer, task, fingerprint):
        # A review scheduled only because the fingerprint moved, on a reviewer with
        # nothing open, is a clean re-approval: it consumes budget and gates nothing.
        had_open = bool([r for r in self.counters.open_findings(reviewer)
                         if r.task == task.id])
        attempt, response, post, _pre = self._delegate(
            reviewer, "Review the diff for %s - %s" % (task.id, task.title),
            self._scope_for(reviewer), task=task.id, objective="verdict")
        verdict = blocks.parse_reviewer(response.text, reviewer, self.iteration)
        self.log.emit("verdict", reviewer=reviewer, task=task.id, verdict=verdict.verdict,
                      synthetic=verdict.synthetic, malformed=verdict.malformed,
                      errors=verdict.errors, findings=[f.get("id") for f in verdict.findings])
        self._attempt_row(attempt, task.id, reviewer, "verdict", "VERIFIED", [self.repo],
                          "", post, verdict.verdict)

        if verdict.approved:
            resolved_before = {r.identity for r in self.counters.open_findings(reviewer)}
            summary = self.counters.record_approve(reviewer, post,
                                                   clean_reapproval=not had_open)
            self.approvals["%s@%s" % (reviewer, task.id)] = post
            self._close_repair_tasks(resolved_before)
        else:
            summary = self.counters.record_reject(reviewer, verdict.findings, self.iteration,
                                                  post, synthetic=verdict.synthetic)
            for item in verdict.findings:
                row = self.counters.findings.get("%s:%s" % (reviewer, item.get("id")))
                if row is not None and not row.task:
                    row.task = task.id
            if not verdict.synthetic:
                self._schedule_repairs(task, reviewer, verdict.findings)
            # Any implementation change invalidates non-matching approvals, and it
            # re-schedules EVERY stale required reviewer, not only the one that
            # rejected (031 FR-011).
            self.approvals = {k: fp for k, fp in self.approvals.items() if fp == post}
        self.log.emit("counters", reviewer=reviewer,
                      no_progress_streak=self.counters.reviewer(reviewer).no_progress_streak,
                      total_invocations=self.counters.reviewer(reviewer).total_invocations,
                      clean_reapprovals=self.counters.reviewer(reviewer).clean_reapprovals,
                      resolved=summary.get("resolved", []))
        self._persist("REVIEW", "%s -> %s" % (reviewer, verdict.verdict))
        return verdict

    # -- findings become tasks (031 FR-007) -------------------------------
    def _schedule_repairs(self, task, reviewer, findings):
        """One unchecked TASKS.md item per NEW finding identity. Never a second."""
        with open(self.tasks_path, encoding="utf-8") as fh:
            text = fh.read()
        changed = False
        for item in findings:
            finding_id = str(item.get("id"))
            identity = "%s:%s" % (reviewer, finding_id)
            existing = tasks_mod.task_for_finding(text, finding_id)
            row = self.counters.findings.get(identity)
            if existing is not None:
                # Re-reporting updates the registry row; it never allocates a
                # second task for the same identity.
                if row is not None and not row.task_ref:
                    row.task_ref = existing.id
                self.log.emit("repair-task-reused", finding=identity, task=existing.id)
                continue
            new_id = tasks_mod.next_task_id(text)
            text = tasks_mod.append_finding_task(
                text, new_id, "Repair %s for %s" % (finding_id, task.id), finding_id,
                task.covers, str(item.get("required_action", "")))
            if row is not None:
                row.task_ref = new_id
            changed = True
            self.log.emit("repair-task-created", finding=identity, task=new_id,
                          covers=task.covers)
        if changed:
            with open(self.tasks_path, "w", encoding="utf-8") as fh:
                fh.write(text)

    def _close_repair_tasks(self, identities):
        """Check off the repair tasks whose findings this APPROVE resolved."""
        refs = [self.counters.findings[i].task_ref for i in identities
                if i in self.counters.findings and self.counters.findings[i].task_ref]
        if not refs:
            return
        with open(self.tasks_path, encoding="utf-8") as fh:
            text = fh.read()
        for ref in refs:
            text = tasks_mod.check_task(text, ref)
        with open(self.tasks_path, "w", encoding="utf-8") as fh:
            fh.write(text)
        self.log.emit("repair-tasks-closed", tasks=sorted(refs))

    def _write_findings(self):
        rows = []
        for identity, row in sorted(self.counters.findings.items()):
            rows.append({
                "Reviewer:finding": identity,
                "Task": row.task or "-",
                "Repair task": row.task_ref or "-",
                "Severity": row.severity or "-",
                "Required action": (row.required_action or "-").replace("|", "/"),
                "Status": row.status,
                "REJECTs": row.reject_total,
                "Repair done": "yes" if row.repair_done else "no",
                "Synthetic": "yes" if row.synthetic else "no",
                "First seen": row.first_seen,
                "Last seen": row.last_seen,
                "Resolving verdict/fingerprint": (row.resolving_verdict or "-").replace("|", "/"),
            })
        self.doc.set_body("Findings", state.render_table(state.FINDING_COLUMNS, rows))

    def _set_task_checkbox(self, task_id, checked):
        """Lifecycle bookkeeping: 031's DONE condition 1 reads TASKS.md itself."""
        with open(self.tasks_path, encoding="utf-8") as fh:
            text = fh.read()
        updated = (tasks_mod.check_task(text, task_id) if checked
                   else tasks_mod.uncheck_task(text, task_id))
        if updated != text:
            with open(self.tasks_path, "w", encoding="utf-8") as fh:
                fh.write(updated)

    # -- finalization (031 FR-013) ----------------------------------------
    def _blocked(self, code, reason, remediation, result="PAUSED", resumable=True):
        self.log.emit("finalization-blocked", code=code, reason=reason,
                      remediation=remediation)
        outcome = self._finish(result, code, reason, resumable=resumable)
        outcome.remediation = remediation
        return outcome

    def _finalize(self, runnable):
        """Prove the run is closed, or refuse to say it is.

        Every check below answers one of 031's six DONE conditions, or FR-013's
        freeze and closure-delta contract. None of them is skippable, and a check
        that cannot be evaluated blocks rather than passes.
        """
        self.log.emit("finalize-start", completed=sorted(self.completed_tasks))

        # The state-only conditions are re-checked on EVERY entry, freeze or no
        # freeze. They cost nothing, and skipping them on re-entry would let a run
        # close over an open finding or an unchecked task that appeared in between.
        outcome = self._state_preconditions(runnable)
        if outcome is not None:
            return outcome

        record = self.closure
        if record is None or record.get("phase") in (None, "", "OPEN"):
            outcome = self._delegating_preconditions()
            if outcome is not None:
                return outcome
            outcome = self._freeze()
            if outcome is not None:
                return outcome
            record = self.closure
        else:
            # Re-entry after a freeze: the frozen fingerprint must still describe
            # the implementation, or the freeze is void and the run goes back.
            current = self.fingerprint()
            if record["frozen_fingerprint"] != current:
                return self._blocked(
                    exits.CLOSURE_NOT_PROVEN,
                    "the implementation changed after the freeze: frozen %s, now %s"
                    % (record["frozen_fingerprint"], current),
                    "031 FR-013 returns this run to REVIEW. Re-enter to re-review the changed "
                    "tree; the freeze is discarded, not repaired.")
            self.log.emit("freeze-reused", fingerprint=record["frozen_fingerprint"],
                          phase=record["phase"])

        return self._close(record)

    def _state_preconditions(self, runnable):
        """The DONE conditions answerable from state and the tree, with no delegation."""
        unconverged = [t.id for t in runnable if t.id not in self.completed_tasks]
        if unconverged:
            return self._blocked(
                exits.NOT_CONVERGED,
                "%d task(s) did not converge: %s" % (len(unconverged), ", ".join(unconverged)),
                "re-enter to continue their implement/review cycle")

        open_findings = sorted(r.identity for r in self.counters.findings.values()
                               if r.status == "open")
        if open_findings:
            return self._blocked(
                exits.NOT_CONVERGED,
                "%d finding(s) still open: %s" % (len(open_findings), ", ".join(open_findings)),
                "only an APPROVE from the owning reviewer on the current fingerprint resolves a "
                "finding; re-enter to repair and re-review them")

        escalations = [ln for ln in self.doc.body("Escalations").splitlines()
                       if "waiting" in ln.lower() and ln.strip().startswith("-")]
        if escalations:
            return self._blocked(
                exits.HUMAN_ESCALATION,
                "%d escalation(s) still waiting for a maintainer answer" % len(escalations),
                "answer them in DECISIONS.md and clear the waiting rows, then re-enter")

        if self.budget.cap <= 0 or self.budget.used > self.budget.cap:
            return self._blocked(
                exits.STATE_UNRESUMABLE,
                "the delegation budget is inconsistent: %d used against a cap of %d"
                % (self.budget.used, self.budget.cap),
                "the run cannot be declared closed on a number nobody can trust. Inspect "
                "ORCHESTRATION.md.", result="ABORTED", resumable=False)

        with open(self.tasks_path, encoding="utf-8") as fh:
            tasks_text = fh.read()
        unchecked = [t.id for t in tasks_mod.unchecked(tasks_text)]
        if unchecked:
            return self._blocked(
                exits.NOT_CONVERGED,
                "%d TASKS.md item(s) are still unchecked: %s"
                % (len(unchecked), ", ".join(unchecked)),
                "031's first DONE condition is that every TASKS.md item is checked. A repair "
                "task is checked only when its finding resolves.")

        return None

    def _delegating_preconditions(self):
        """The conditions that cost delegations: stale re-review, then conformance."""
        outcome = self._refresh_stale_approvals()
        if outcome is not None:
            return outcome
        return self._final_conformance()

    def _refresh_stale_approvals(self):
        """A later task's change stales an earlier task's approval (031 FR-011)."""
        with open(self.tasks_path, encoding="utf-8") as fh:
            tasks_text = fh.read()
        by_id = {t.id: t for t in tasks_mod.parse(tasks_text)}

        current = self.fingerprint()
        stale = []
        for task_id in sorted(self.completed_tasks):
            task = by_id.get(task_id)
            if task is None:
                return self._blocked(
                    exits.STATE_UNRESUMABLE,
                    "task %s is recorded complete but no longer exists in TASKS.md" % task_id,
                    "the runner will not close a run whose task list moved under it. Reconcile "
                    "TASKS.md, or start a fresh run.", result="ABORTED", resumable=False)
            for reviewer in self._required_reviewers(task):
                if self.approvals.get("%s@%s" % (reviewer, task_id)) != current:
                    stale.append((reviewer, task))

        if not stale:
            return None

        self.log.emit("stale-approvals", count=len(stale),
                      pairs=["%s@%s" % (r, t.id) for r, t in stale], fingerprint=current)

        for reviewer, task in stale:
            if self.counters.would_exceed(reviewer):
                return self._blocked(
                    exits.CAP_ABORT,
                    "reviewer %r reached the no-progress cap while re-reviewing stale approvals"
                    % reviewer,
                    "raise --max-iterations explicitly on re-entry, or resolve the disagreement "
                    "by hand", result="ABORTED")
            verdict = self._review(reviewer, task, current)
            if not verdict.approved:
                # Back to REVIEW: the task is no longer converged, so it must not
                # stay marked complete or a re-entry would skip it.
                self.completed_tasks.discard(task.id)
                self._set_task_checkbox(task.id, False)
                self._persist("REVIEW", task.id)
                return self._blocked(
                    exits.NOT_CONVERGED,
                    "re-reviewing the stale approval of %s returned REJECT from %r; the run "
                    "returns to REVIEW" % (task.id, reviewer),
                    "re-enter to repair the finding and re-review")

        return self._refresh_stale_approvals()

    def _final_conformance(self):
        """031 step 6: run final-conformance-reviewer exactly once on the evidence chain."""
        current = self.fingerprint()
        if self.approvals.get("final-conformance@run") == current:
            return None
        with open(self.tasks_path, encoding="utf-8") as fh:
            tasks_text = fh.read()
        objective = "final conformance"
        attempt, response, post, _pre = self._delegate(
            "final-conformance",
            "Verify SPEC -> PLAN -> TASKS -> DIFF -> TESTS -> REVIEW for %s. Tasks:\n%s"
            % (self.feature_dir, tasks_text[:2000]),
            self._scope_for("final-conformance"), task="-", objective=objective)
        verdict = blocks.parse_reviewer(response.text, "final-conformance", self.iteration)
        self.log.emit("verdict", reviewer="final-conformance", task="-",
                      verdict=verdict.verdict, synthetic=verdict.synthetic,
                      errors=verdict.errors,
                      findings=[f.get("id") for f in verdict.findings])
        self._attempt_row(attempt, "-", "final-conformance", objective, "VERIFIED",
                          [self.repo], "", post, verdict.verdict)

        if not verdict.approved:
            self.counters.record_reject("final-conformance", verdict.findings, self.iteration,
                                        post, synthetic=verdict.synthetic)
            self._persist("REVIEW", "final conformance REJECT")
            return self._blocked(
                exits.NOT_CONVERGED,
                "final-conformance-reviewer returned REJECT: %s"
                % ", ".join(f.get("id", "?") for f in verdict.findings),
                "re-enter to address its findings; the run does not close on a rejected "
                "conformance review")
        self.counters.record_approve("final-conformance", post)
        self.approvals["final-conformance@run"] = post
        self._persist("FINAL CONFORMANCE", "APPROVE")
        return None

    def _verification(self):
        """031's second DONE condition. Honest about the case where it cannot be met."""
        if not self.baseline_cmd:
            return closure_mod.VERIFY_NOT_DECLARED
        before = subprocess.run(["git", "-C", self.repo, "status", "--porcelain"],
                                capture_output=True, text=True).stdout
        proc = subprocess.run(self.baseline_cmd, cwd=self.repo, capture_output=True, text=True)
        after = subprocess.run(["git", "-C", self.repo, "status", "--porcelain"],
                               capture_output=True, text=True).stdout
        self.log.emit("verification", command=list(self.baseline_cmd),
                      returncode=proc.returncode, hermetic=before == after)
        if proc.returncode != 0:
            return "%s (exit %d)" % (closure_mod.VERIFY_FAILED, proc.returncode)
        if before != after:
            return closure_mod.VERIFY_MUTATED
        return closure_mod.VERIFY_PASS

    def _freeze(self):
        """Record the fully approved implementation fingerprint and the tree behind it."""
        verification = self._verification()
        if verification == closure_mod.VERIFY_NOT_DECLARED:
            # 031 makes a green, non-mutating verification a CONDITION of DONE.
            # Recording it as unobserved and closing anyway turned that condition
            # into a log line: the runner could report DONE having verified
            # nothing (AUDIT-1, D036). Only PASS closes.
            return self._blocked(
                exits.CLOSURE_NOT_PROVEN,
                "no verification command was declared, so condition 2 of 031's termination "
                "contract cannot be met and this run cannot close",
                "re-enter with --baseline '<command>' naming the suite that proves this feature; "
                "it must exit 0 and leave the tree unchanged", result="PAUSED")
        if verification != closure_mod.VERIFY_PASS:
            return self._blocked(
                exits.NOT_CONVERGED,
                "the declared verification command did not pass: %s" % verification,
                "get the verification green and hermetic, then re-enter", result="ABORTED")

        fingerprint = self.fingerprint()
        frozen = closure_mod.tree_map(self.repo)
        self.closure = {"frozen_fingerprint": fingerprint, "phase": "FROZEN",
                        "verification": verification, "frozen": frozen, "delta": []}
        self._persist_closure()
        self.log.emit("freeze", fingerprint=fingerprint, paths=len(frozen),
                      verification=verification)
        return None

    def _persist_closure(self):
        self.doc.set_body("Closure delta", closure_mod.render(
            self.closure["frozen_fingerprint"], self.closure["frozen"],
            self.closure["delta"], self.closure["phase"], self.closure["verification"]))
        self._persist(self.closure["phase"], "closure")

    def _close(self, record):
        """Record terminal core evidence and stop at the D034 boundary.

        This is where spec 040's supported surface ends (FR-008, FR-017, FR-018,
        AC-019). The core proves the six state conditions, the freshness of every
        approval, final conformance and a green non-mutating baseline, and it
        records the frozen fingerprint and tree map. It stops there.

        What deliberately does NOT happen here: delegating the owning lifecycle
        skills (`/spec-review`, `/spec-close`, `/pr-description`), computing a
        closure delta over what those skills changed, and requiring
        `PR_DESCRIPTION.md`. Those need a provider that can actually run a skill,
        and 040 certifies no such provider — the stub answering `APPROVE` on their
        behalf proved only that the stub was asked. They belong to the follow-up
        `Finalizer` spec, which begins at this seam (AUDIT-9).

        The frozen tree map persisted below is the hand-off datum: what the
        Finalizer will compare its closure delta against.
        """
        self.closure["phase"] = CORE_COMPLETE
        self.closure["delta"] = []
        self._persist_closure()
        self.log.emit("core-complete", fingerprint=record["frozen_fingerprint"],
                      verification=record["verification"], paths=len(record["frozen"]),
                      handoff="lifecycle delegation, closure delta and PR-description "
                              "evidence are outside spec 040 (D034)")
        return self._finish(
            "DONE", exits.OK,
            "core complete: frozen at %s, verification %s, %d path(s) recorded for the "
            "finalization hand-off. Lifecycle closure is outside this runner's scope."
            % (record["frozen_fingerprint"], record["verification"], len(record["frozen"])),
            resumable=False)

    def _finish(self, result, code, reason, resumable=True, escalations=None):
        self.doc.set_body("Run result",
                          "\n%s\n\nresumable: %s\n\nreason: %s\n\n"
                          % (result, "yes" if resumable else "no", reason))
        self._persist("END", reason)
        self.log.emit("finish", result=result, code=code, reason=reason,
                      budget_used=self.budget.used, budget_cap=self.budget.cap,
                      completed=sorted(self.completed_tasks))
        return Outcome(code, result, reason, resumable, escalations or [])
