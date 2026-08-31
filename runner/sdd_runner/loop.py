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

from . import blocks, exits, resume as resume_mod, state, tasks as tasks_mod
from .backends import BackendPrecondition
from .budget import Budget, BudgetExhausted, default_cap
from .counters import CounterState
from .escalation import classify_all
from .resume import ConcurrentRun, UnresumableState
from .retry import DelegationFailedClosed, RetryPolicy, call_with_retry

REVIEWERS = ("domain", "security", "final-conformance")
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
                 retry_policy=None, notify=None, hostname=None, pid=None):
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
        self.approvals = {}            # reviewer -> fingerprint it approved
        self.completed_tasks = set()
        self.resumed = None            # the ResumeState this run re-entered from

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
        proc = subprocess.run(["git", "-C", self.repo, "status", "--porcelain=v1"],
                              capture_output=True, text=True)
        digest = hashlib.sha256()
        excluded = ("ORCHESTRATION.md", "run.jsonl", "PR_DESCRIPTION.md")
        for line in sorted(proc.stdout.splitlines()):
            path = line[3:].strip()
            if any(path.endswith(x) for x in excluded):
                continue
            digest.update(line.encode("utf-8"))
            full = os.path.join(self.repo, path)
            if os.path.isfile(full):
                with open(full, "rb") as fh:
                    digest.update(hashlib.sha256(fh.read()).digest())
        diff = subprocess.run(["git", "-C", self.repo, "diff", "HEAD"],
                              capture_output=True, text=True)
        digest.update(diff.stdout.encode("utf-8"))
        return digest.hexdigest()[:16]

    # -- state ------------------------------------------------------------
    def _load_or_create_state(self, unchecked_count):
        """Create a fresh document, or re-enter an existing one (031 FR-011).

        Raises ConcurrentRun or UnresumableState. Never guesses.
        """
        if not os.path.exists(self.state_path):
            cap = self.max_delegations_override or default_cap(unchecked_count)
            doc = state.new_document(self.feature_dir, "runner", self.clock(),
                                     {"max_iterations": self.counters.max_iterations,
                                      "max_delegations": cap,
                                      "pid": self.pid, "host": self.hostname})
            doc.save(self.state_path)
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
        self.attempt_seq = resumed.attempt_seq
        self.iteration = resumed.iteration
        self.resumed = resumed

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

    def _attempt_row(self, attempt, task, agent, objective, lifecycle, scope,
                     pre, post, outcome):
        self.doc.append_line("Attempts", "| " + " | ".join([
            attempt, task or "-", agent, objective, lifecycle,
            ";".join(scope or []) or "-", pre or "-", post or "-",
            outcome or "-", str(self.clock()),
        ]) + " |")

    def _delegate(self, agent, objective, path_scope, task=""):
        self.attempt_seq += 1
        attempt = "A-%03d" % self.attempt_seq
        pre = self.fingerprint()
        self._attempt_row(attempt, task, agent, objective, "DISPATCHED", path_scope,
                          pre, "", "")
        self._persist("DELEGATE", task or "%s -> %s" % (attempt, agent))
        self.log.emit("dispatch", attempt=attempt, agent=agent, task=task, objective=objective,
                      scope=list(path_scope), pre_fingerprint=pre,
                      budget_used=self.budget.used, budget_cap=self.budget.cap)

        system = self._system_prompt(agent)
        response = call_with_retry(
            lambda timeout: self.backend.run(system, objective, path_scope, timeout),
            self.retry_policy, self.budget, self.sleep,
            on_attempt=lambda n: self.log.emit("attempt", attempt=attempt, n=n, agent=agent),
            reason="%s/%s" % (attempt, agent))

        post = self.fingerprint()
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
        pending = tasks_mod.unchecked(tasks_text)

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

        unconverged = [t.id for t in runnable if t.id not in self.completed_tasks]
        if unconverged:
            # Every task was PROCESSED; that is not the same as converged. Reporting
            # DONE here would be a false claim, and - worse for T013 - a later
            # re-entry would read DONE and refuse to resume work that never landed.
            reason = ("processed every task but %d did not converge: %s"
                      % (len(unconverged), ", ".join(unconverged)))
            self.log.emit("not-converged", tasks=unconverged)
            return self._finish("PAUSED", exits.NOT_CONVERGED, reason, resumable=True)

        return self._finish("DONE", exits.OK, "all unchecked tasks converged", resumable=False)

    def _process_task(self, task):
        self.iteration += 1
        attempt, response, fingerprint, _pre = self._delegate(
            "worker", "Implement %s - %s" % (task.id, task.title), [self.repo], task=task.id)
        completion = blocks.parse_worker(response.text)
        self.log.emit("completion", task=task.id, status=completion.status,
                      malformed=completion.malformed, errors=completion.errors)
        self._attempt_row(attempt, task.id, "worker", "completion", "RESPONDED", [self.repo],
                          "", fingerprint, completion.status)

        if not completion.done:
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
            # Auto-resolvable: record and continue. The deep-reasoner call and the
            # DECISIONS.md write are T014's work, not this one's.
            self.log.emit("escalation-auto", task=task.id,
                          questions=[c.question for c in classifications])
        else:
            for identity in [i for i, r in self.counters.findings.items()
                             if r.task == task.id and r.status == "open"]:
                self.counters.record_repair_done(identity)

        approved_by = []
        for reviewer in self._required_reviewers(task):
            if self.counters.would_exceed(reviewer):
                reason = ("reviewer %r reached the no-progress cap (%d)"
                          % (reviewer, self.counters.max_iterations))
                self.log.emit("abort", kind="cap", detail=reason)
                return self._finish("ABORTED", exits.CAP_ABORT, reason, resumable=True)
            verdict = self._review(reviewer, task, fingerprint)
            if verdict is not None and verdict.approved:
                approved_by.append(reviewer)
            breach = self.counters.breached()
            if breach:
                reason = "%s %r failed to converge" % breach
                self.log.emit("abort", kind="cap", detail=reason)
                return self._finish("ABORTED", exits.CAP_ABORT, reason, resumable=True)

        required = self._required_reviewers(task)
        if completion.done and all(r in approved_by for r in required):
            self.completed_tasks.add(task.id)
            self._attempt_row(attempt, task.id, "worker", "task complete", "VERIFIED",
                              [self.repo], "", fingerprint, "DONE")
            self.log.emit("task-complete", task=task.id, reviewers=required)
            self._persist("TASK COMPLETE", task.id)
        return None

    def _required_reviewers(self, task):
        required = ["domain"]
        haystack = (task.raw or "").lower()
        if any(trigger in haystack for trigger in SECURITY_TRIGGERS):
            required.append("security")
        return required

    def _review(self, reviewer, task, fingerprint):
        attempt, response, post, _pre = self._delegate(
            reviewer, "Review the diff for %s - %s" % (task.id, task.title), [self.repo],
            task=task.id)
        verdict = blocks.parse_reviewer(response.text, reviewer, self.iteration)
        self.log.emit("verdict", reviewer=reviewer, task=task.id, verdict=verdict.verdict,
                      synthetic=verdict.synthetic, malformed=verdict.malformed,
                      errors=verdict.errors, findings=[f.get("id") for f in verdict.findings])
        self._attempt_row(attempt, task.id, reviewer, "verdict", "VERIFIED", [self.repo],
                          "", post, verdict.verdict)

        if verdict.approved:
            summary = self.counters.record_approve(reviewer, post)
            self.approvals[reviewer] = post
        else:
            summary = self.counters.record_reject(reviewer, verdict.findings, self.iteration, post)
            for item in verdict.findings:
                row = self.counters.findings.get("%s:%s" % (reviewer, item.get("id")))
                if row is not None and not row.task:
                    row.task = task.id
            # Any implementation change invalidates non-matching approvals (031 FR-011).
            self.approvals = {r: fp for r, fp in self.approvals.items() if fp == post}
        self.log.emit("counters", reviewer=reviewer,
                      no_progress_streak=self.counters.reviewer(reviewer).no_progress_streak,
                      total_invocations=self.counters.reviewer(reviewer).total_invocations,
                      resolved=summary.get("resolved", []))
        self._persist("REVIEW", "%s -> %s" % (reviewer, verdict.verdict))
        return verdict

    def _write_findings(self):
        rows = []
        for identity, row in sorted(self.counters.findings.items()):
            rows.append({
                "Reviewer:finding": identity,
                "Task": row.task or "-",
                "Severity": row.severity or "-",
                "Required action": (row.required_action or "-").replace("|", "/"),
                "Status": row.status,
                "REJECTs": row.reject_total,
                "Repair done": "yes" if row.repair_done else "no",
                "First seen": row.first_seen,
                "Last seen": row.last_seen,
                "Resolving verdict/fingerprint": (row.resolving_verdict or "-").replace("|", "/"),
            })
        self.doc.set_body("Findings", state.render_table(state.FINDING_COLUMNS, rows))

    def _finish(self, result, code, reason, resumable=True, escalations=None):
        self.doc.set_body("Run result",
                          "\n%s\n\nresumable: %s\n\nreason: %s\n\n"
                          % (result, "yes" if resumable else "no", reason))
        self._persist("END", reason)
        self.log.emit("finish", result=result, code=code, reason=reason,
                      budget_used=self.budget.used, budget_cap=self.budget.cap,
                      completed=sorted(self.completed_tasks))
        return Outcome(code, result, reason, resumable, escalations or [])
