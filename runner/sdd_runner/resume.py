"""Idempotent re-entry — spec 031 FR-011 (and FR-008's durable attempt state).

The rule this module exists to enforce: **completed tasks are not re-delegated,
findings are not duplicated, and counters never reset.** Everything it returns is
read from the persisted document. Nothing is inferred, defaulted or guessed.

When the state cannot be reconstructed faithfully, this module raises
`UnresumableState` and the run stops. That is the whole design: a resume that
quietly rebuilds a plausible-looking state is worse than no resume, because the
caps and the budget it then enforces are fiction.

Distinguishing a live run from a dead one
-----------------------------------------
`ACTIVE` means "a runner is inside the loop". After a SIGTERM it also means "a
runner *was* inside the loop", and those need different answers: the first must
be refused, the second must be recoverable. The document records the pid and host
of the writer, so:

  * `ACTIVE`, same host, pid alive   -> concurrent run, REFUSE
  * `ACTIVE`, same host, pid dead    -> interrupted run, RECOVERABLE
  * `ACTIVE`, different host         -> cannot verify, BLOCK for a human

The third case fails closed on purpose. Guessing that a remote pid is dead is how
two runners end up in the same worktree.
"""

import os
from dataclasses import dataclass, field

from . import closure as closure_mod
from . import state as state_mod
from .counters import CounterState, FindingRow
from .policy import PROTOCOL_VERSION, RECOVERABLE_RESULTS, TERMINAL_RESULTS  # noqa: F401

# Attempts-row objectives. Must match loop.py.
TASK_COMPLETE_OBJECTIVE = "task complete"
IMPLEMENTATION_OBJECTIVE = "implementation"
REPAIR_OBJECTIVE_PREFIX = "repair "

class UnresumableState(RuntimeError):
    """The run cannot continue. Carries what is wrong and what a human must do."""

    def __init__(self, reason, remediation):
        super().__init__("%s\n  remediation: %s" % (reason, remediation))
        self.reason = reason
        self.remediation = remediation


class ConcurrentRun(RuntimeError):
    """A live runner already owns this feature folder."""


@dataclass
class ResumeState:
    completed_tasks: set = field(default_factory=set)
    blocked_tasks: set = field(default_factory=set)
    implemented_tasks: set = field(default_factory=set)
    budget_used: int = 0
    budget_cap: int = 0
    iteration: int = 0
    attempt_seq: int = 0
    counters: CounterState = None
    approvals: dict = field(default_factory=dict)
    open_escalations: list = field(default_factory=list)
    prior_result: str = ""
    recovered_from_interrupt: bool = False
    closure: dict = None
    entry: str = "ready"       # spec 041 D007: a document without the field is a `ready` entry


def _pid_alive(pid):
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True          # exists, owned by someone else
    except (OverflowError, ValueError):
        return False
    return True


def _require(fields, key, doc_path):
    if key not in fields:
        raise UnresumableState(
            "the State section of %s has no %r field, so the runner cannot rebuild that part of "
            "the run" % (doc_path, key),
            "this document was not written by this runner, or it was truncated. Inspect it, and "
            "either finish the run by hand or delete it to start a fresh run.")
    return fields[key]


def _int(value, key, doc_path):
    try:
        return int(str(value).strip().split()[0])
    except (ValueError, IndexError):
        raise UnresumableState(
            "the State field %r in %s is not a number: %r" % (key, doc_path, value),
            "the state file is corrupt. Inspect it and correct the field, or delete it to start "
            "a fresh run.")


def _parse_counters(raw, max_iterations, doc_path):
    """`domain=streak:0,invocations:3,reapprovals:1; security=streak:1,...`"""
    counters = CounterState(max_iterations=max_iterations)
    for chunk in [c.strip() for c in (raw or "").split(";") if c.strip()]:
        if "=" not in chunk:
            raise UnresumableState(
                "the State 'counters' field in %s is malformed near %r" % (doc_path, chunk),
                "the counters cannot be rebuilt, and a reset counter would silently widen every "
                "cap. Inspect the state file, or delete it to start a fresh run.")
        name, values = chunk.split("=", 1)
        row = counters.reviewer(name.strip())
        for pair in [p for p in values.split(",") if p.strip()]:
            if ":" not in pair:
                raise UnresumableState(
                    "the State 'counters' field in %s is malformed near %r" % (doc_path, pair),
                    "inspect the state file, or delete it to start a fresh run.")
            key, value = pair.split(":", 1)
            key, value = key.strip(), value.strip()
            if not value.lstrip("-").isdigit():
                raise UnresumableState(
                    "counter %r for reviewer %r is not a number: %r"
                    % (key, name.strip(), value),
                    "inspect the state file, or delete it to start a fresh run.")
            if key == "streak":
                row.no_progress_streak = int(value)
            elif key == "invocations":
                row.total_invocations = int(value)
            elif key == "reapprovals":
                row.clean_reapprovals = int(value)
    return counters


def render_counters(counters):
    return "; ".join(
        "%s=streak:%d,invocations:%d,reapprovals:%d"
        % (name, c.no_progress_streak, c.total_invocations, c.clean_reapprovals)
        for name, c in sorted(counters.reviewers.items()))


def render_approvals(approvals):
    """`domain@T001=abc123; security@T001=abc123` - keyed by reviewer AND task."""
    return "; ".join("%s=%s" % (key, fp) for key, fp in sorted(approvals.items()))


def _parse_approvals(raw, doc_path):
    approvals = {}
    for chunk in [c.strip() for c in (raw or "").split(";") if c.strip()]:
        if "=" not in chunk:
            raise UnresumableState(
                "the State 'approvals' field in %s is malformed near %r" % (doc_path, chunk),
                "inspect the state file, or delete it to start a fresh run.")
        reviewer, fingerprint = chunk.split("=", 1)
        approvals[reviewer.strip()] = fingerprint.strip()
    return approvals


def _load_findings(doc, counters, doc_path):
    try:
        headers, rows = state_mod.parse_table(doc.body("Findings"))
    except ValueError as exc:
        raise UnresumableState(
            "the Findings registry in %s is corrupt: %s" % (doc_path, exc),
            "a partially readable registry would duplicate findings or lose a REJECT count. "
            "Inspect the table, or delete the state file to start a fresh run.")
    if not rows:
        return
    if headers != state_mod.FINDING_COLUMNS:
        raise UnresumableState(
            "the Findings registry in %s uses columns this runner does not write: %s"
            % (doc_path, headers),
            "this document was written by a different executor. Resuming it would mean guessing "
            "at its finding state. Finish that run with the executor that started it.")
    for row in rows:
        identity = row["Reviewer:finding"]
        if ":" not in identity:
            raise UnresumableState(
                "finding identity %r in %s is not <reviewer>:<finding-id>" % (identity, doc_path),
                "inspect the registry, or delete the state file to start a fresh run.")
        reviewer, finding_id = identity.split(":", 1)
        rejects = row.get("REJECTs", "0").strip() or "0"
        if not rejects.isdigit():
            raise UnresumableState(
                "the REJECT count for %r in %s is not a number: %r"
                % (identity, doc_path, rejects),
                "a lost REJECT count silently widens the per-finding cap. Inspect the registry, "
                "or delete the state file to start a fresh run.")
        counters.findings[identity] = FindingRow(
            identity=identity,
            reviewer=reviewer,
            finding_id=finding_id,
            task=row.get("Task", "").strip().lstrip("-") or "",
            task_ref=row.get("Repair task", "").strip().lstrip("-") or "",
            severity=row.get("Severity", ""),
            required_action=row.get("Required action", ""),
            status=row.get("Status", "open"),
            first_seen=int(row["First seen"]) if row.get("First seen", "").isdigit() else 0,
            last_seen=int(row["Last seen"]) if row.get("Last seen", "").isdigit() else 0,
            reject_total=int(rejects),
            repair_done=row.get("Repair done", "no").strip().lower() in ("yes", "true"),
            synthetic=row.get("Synthetic", "no").strip().lower() in ("yes", "true"),
            resolving_verdict=row.get("Resolving verdict/fingerprint", ""),
        )


def _load_attempts(doc, doc_path):
    """Return (completed, blocked, implemented, highest_attempt_number).

    `implemented` is what stops a resume from repairing the same finding twice:
    a worker that already came back DONE for this task did its work, and what is
    pending is the review, not another delegation.
    """
    try:
        headers, rows = state_mod.parse_table(doc.body("Attempts"))
    except ValueError as exc:
        raise UnresumableState(
            "the Attempts table in %s is corrupt: %s" % (doc_path, exc),
            "the attempt history is what proves a task was already done. Inspect the table, or "
            "delete the state file to start a fresh run.")
    if not rows:
        return set(), set(), set(), 0     # spec 041 D009: was 3 values, and inspect unpacks 4
    if headers != state_mod.ATTEMPT_COLUMNS:
        raise UnresumableState(
            "the Attempts table in %s uses columns this runner does not write: %s"
            % (doc_path, headers),
            "this document was written by a different executor. Resuming it would mean guessing "
            "which tasks already ran. Finish that run with the executor that started it.")

    completed, blocked, implemented, highest = set(), set(), set(), 0
    for row in rows:
        attempt = row.get("Attempt", "")
        if attempt.startswith("A-") and attempt[2:].isdigit():
            highest = max(highest, int(attempt[2:]))
        lifecycle = row.get("Lifecycle", "").strip()
        if lifecycle and lifecycle not in state_mod.LIFECYCLE:
            raise UnresumableState(
                "attempt %s in %s has lifecycle %r, which is not one of %s"
                % (attempt, doc_path, lifecycle, "/".join(state_mod.LIFECYCLE)),
                "inspect the table, or delete the state file to start a fresh run.")
        task = row.get("Task", "").strip()
        if not task or task == "-":
            continue
        if row.get("Agent", "").strip() != "worker":
            continue
        outcome = row.get("Outcome", "").strip()
        objective = row.get("Objective", "").strip()
        # A task is complete ONLY when the loop wrote the explicit completion row,
        # which it does after every required reviewer approved. A worker response
        # of DONE is not that: its review may still reject.
        if objective == TASK_COMPLETE_OBJECTIVE and lifecycle == "VERIFIED" and outcome == "DONE":
            completed.add(task)
        elif outcome == "BLOCKED":
            blocked.add(task)
        if outcome == "DONE" and (objective == IMPLEMENTATION_OBJECTIVE
                                  or objective.startswith(REPAIR_OBJECTIVE_PREFIX)):
            implemented.add(task)
    return completed, blocked - completed, implemented, highest


def _open_escalations(doc):
    return [line.strip() for line in doc.body("Escalations").splitlines()
            if "waiting" in line.lower() and line.strip().startswith("-")]


def inspect(doc, doc_path, max_iterations, hostname, pid_alive=_pid_alive):
    """Decide what to do with an existing ORCHESTRATION.md.

    Returns a ResumeState. Raises ConcurrentRun or UnresumableState.
    """
    fields = state_mod.parse_fields(doc.body("State"))
    result = doc.run_result()

    if fields.get("writer") != "sdd_runner":
        raise UnresumableState(
            "%s was not written by this runner (State 'writer' is %r)"
            % (doc_path, fields.get("writer")),
            "the phase-1 executor owns that document. Finish the run with the executor that "
            "started it, or archive the file and start a fresh runner run.")

    if result is None:
        raise UnresumableState(
            "%s has no recognizable Run result" % doc_path,
            "without a run result the runner cannot tell a finished run from an interrupted one. "
            "Inspect the file, or delete it to start a fresh run.")

    # spec 042 FR-010. Checked before any field that carries STATE is believed —
    # pid, host, caps, counters, findings, attempts, closure — because the version
    # is what fixes those fields' meaning. Two checks precede it, `writer` and the
    # presence of a run result, and both fail closed; an earlier draft of this
    # comment claimed the version came first, which was not true.
    try:
        written_under = doc.protocol_version()
    except state_mod.UnknownProtocolVersion as exc:
        raise UnresumableState(
            "%s records an unreadable protocol version %r" % (doc_path, exc.raw),
            "the field must be a positive integer. This core implements protocol version %d; "
            "inspect the file, or archive it and start a fresh run." % PROTOCOL_VERSION)
    if written_under > PROTOCOL_VERSION:
        raise UnresumableState(
            "%s was written under protocol version %d, and this core implements %d"
            % (doc_path, written_under, PROTOCOL_VERSION),
            "a newer executor owns that run. Finish it with the executor that started it, or "
            "archive the file and start a fresh run.")

    if result in TERMINAL_RESULTS:
        raise UnresumableState(
            "%s records a completed run (Run result: %s)" % (doc_path, result),
            "there is nothing to resume. Archive the state file if you want to run this feature "
            "again.")

    if result == "ABORTED" and not doc.resumable():
        raise UnresumableState(
            "%s records a terminal abort (resumable: no)" % doc_path,
            "031 makes unsafe and corrupt-provenance aborts terminal. A fresh human-controlled "
            "run is required; this runner will not re-enter.")

    recovered = False
    if result == "ACTIVE":
        recorded_host = fields.get("runner host", "")
        recorded_pid = fields.get("runner pid", "")
        if recorded_host != hostname:
            raise UnresumableState(
                "%s records an ACTIVE run on host %r, and this is %r"
                % (doc_path, recorded_host, hostname),
                "this runner cannot tell whether that run is still alive. Confirm it is dead, "
                "then set the Run result to ABORTED with 'resumable: yes' before re-entering.")
        if not recorded_pid.isdigit():
            raise UnresumableState(
                "%s records an ACTIVE run with an unreadable pid %r" % (doc_path, recorded_pid),
                "confirm no runner is still running against this feature, then set the Run result "
                "to ABORTED with 'resumable: yes' before re-entering.")
        if pid_alive(int(recorded_pid)):
            raise ConcurrentRun(
                "an ACTIVE run (pid %s on %s) already owns %s; refusing to start a second runner"
                % (recorded_pid, recorded_host, doc_path))
        recovered = True         # ACTIVE but the writer is gone: an interrupted run

    cap = _int(_require(fields, "max-delegations", doc_path), "max-delegations", doc_path)
    used = _int(_require(fields, "delegations used", doc_path), "delegations used", doc_path)
    if used > cap:
        raise UnresumableState(
            "%s records %d delegations used against a cap of %d" % (doc_path, used, cap),
            "the budget is inconsistent, and re-entering would run on a number nobody can trust. "
            "Inspect the file, or delete it to start a fresh run.")

    body = doc.body("Closure delta")
    closure_record = None
    if "frozen fingerprint" in body:
        try:
            closure_record = closure_mod.parse(body)
        except closure_mod.CorruptClosureRecord as exc:
            raise UnresumableState(
                "the Closure delta section of %s is corrupt: %s" % (doc_path, exc),
                "the freeze record is what proves the run was closed safely. A partially readable "
                "one would let the runner claim a closure it cannot demonstrate. Inspect it, or "
                "delete the state file to start a fresh run.")

    counters = _parse_counters(fields.get("counters", ""), max_iterations, doc_path)
    _load_findings(doc, counters, doc_path)
    completed, blocked, implemented, highest = _load_attempts(doc, doc_path)

    recorded_completed = {t.strip() for t in fields.get("completed tasks", "").split(",")
                          if t.strip()}
    if recorded_completed != completed:
        raise UnresumableState(
            "%s disagrees with itself about completed tasks: State says %s, the Attempts table "
            "says %s" % (doc_path, sorted(recorded_completed) or "none", sorted(completed)
                         or "none"),
            "one of the two is wrong and the runner will not choose between them. Reconcile them "
            "by hand, or delete the state file to start a fresh run.")

    return ResumeState(
        completed_tasks=completed,
        blocked_tasks=blocked,
        implemented_tasks=implemented,
        budget_used=used,
        budget_cap=cap,
        iteration=_int(fields.get("iteration", "0"), "iteration", doc_path),
        attempt_seq=highest,
        counters=counters,
        approvals=_parse_approvals(fields.get("approvals", ""), doc_path),
        open_escalations=_open_escalations(doc),
        prior_result=result,
        recovered_from_interrupt=recovered,
        closure=closure_record,
        entry=fields.get("entry", "ready"),
    )
