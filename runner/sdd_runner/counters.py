"""Convergence counters — spec 031 FR-009, as corrected by spec 032 (D017/D008).

Caps detect STAGNATION, never workload. Getting this backwards is a known defect
(031 D017): gating every reviewer invocation against one counter aborts any
feature with more tasks than the cap.

Three numbers per reviewer and one per finding:

  * no-progress streak      GATES, cap max-iterations
  * total invocations       audit only, NEVER gates
  * clean re-approvals      audit only, gates nothing
  * per-finding REJECT total GATES, cap max-iterations, monotonic

The per-finding rule is the one most easily got wrong, so it is stated here
verbatim from skills/sdd-orchestrate/SKILL.md: count a REJECT carrying the same
`<reviewer>:<finding-id>` "only when a repair attempt for that finding has
already completed with a worker DONE" — that is, count FAILED REPAIRS, not
re-reports, and not attempts that never produced a change. A BLOCKED attempt is
not a failed repair.
"""

from dataclasses import dataclass, field


@dataclass
class ReviewerCounters:
    no_progress_streak: int = 0     # gates
    total_invocations: int = 0      # audit only
    clean_reapprovals: int = 0      # audit only


@dataclass
class FindingRow:
    """One row of the durable Findings registry (031 FR-007)."""

    identity: str                   # "<reviewer>:<finding-id>"
    reviewer: str
    finding_id: str
    task: str = ""
    severity: str = ""
    required_action: str = ""
    status: str = "open"            # open | resolved
    first_seen: int = 0
    last_seen: int = 0
    reject_total: int = 0           # gates; counts failed repairs only
    repair_done: bool = False       # a worker DONE has landed for this finding
    resolving_verdict: str = ""
    resolving_fingerprint: str = ""


class CounterState:
    """Owns the reviewer counters and the Findings registry for one run."""

    def __init__(self, max_iterations: int = 3):
        self.max_iterations = max_iterations
        self.reviewers = {}
        self.findings = {}

    # -- helpers ---------------------------------------------------------
    def reviewer(self, name: str) -> ReviewerCounters:
        return self.reviewers.setdefault(name, ReviewerCounters())

    def open_findings(self, reviewer: str):
        return [r for r in self.findings.values()
                if r.reviewer == reviewer and r.status == "open"]

    def record_repair_done(self, identity: str):
        """A worker completed a repair attempt for this finding with DONE.

        Only after this does a subsequent REJECT on the same identity count as a
        failed repair.
        """
        row = self.findings.get(identity)
        if row is not None:
            row.repair_done = True

    # -- the two gating rules --------------------------------------------
    def record_reject(self, reviewer: str, findings: list, iteration: int,
                      fingerprint: str = "") -> dict:
        """Apply a REJECT verdict. Returns a summary of what it changed."""
        counters = self.reviewer(reviewer)
        counters.total_invocations += 1

        previously_open = {r.identity for r in self.open_findings(reviewer)}
        reported = set()

        for item in findings:
            identity = "%s:%s" % (reviewer, item.get("id"))
            reported.add(identity)
            row = self.findings.get(identity)
            if row is None:
                row = FindingRow(
                    identity=identity,
                    reviewer=reviewer,
                    finding_id=str(item.get("id")),
                    severity=str(item.get("severity", "")),
                    required_action=str(item.get("required_action", "")),
                    first_seen=iteration,
                )
                self.findings[identity] = row
            else:
                # Re-report: update the row, never allocate another task.
                row.severity = str(item.get("severity", row.severity))
                row.required_action = str(item.get("required_action", row.required_action))
                row.status = "open"
                row.resolving_verdict = ""
                row.resolving_fingerprint = ""
                # Count a failed repair only, per SKILL.md.
                if row.repair_done:
                    row.reject_total += 1
                    row.repair_done = False
            row.last_seen = iteration

        # A REJECT that resolves at least one previously open finding of that
        # reviewer is PROGRESS, even when it raises new ones.
        resolved = previously_open - reported
        for identity in resolved:
            row = self.findings[identity]
            row.status = "resolved"
            row.resolving_verdict = "REJECT (not re-reported at iteration %d)" % iteration
            row.resolving_fingerprint = fingerprint

        if resolved:
            counters.no_progress_streak = 0
        else:
            counters.no_progress_streak += 1

        return {
            "reviewer": reviewer,
            "resolved": sorted(resolved),
            "reported": sorted(reported),
            "no_progress_streak": counters.no_progress_streak,
        }

    def record_approve(self, reviewer: str, fingerprint: str = "",
                       clean_reapproval: bool = False) -> dict:
        """Apply an APPROVE verdict.

        An APPROVE resolves every currently open finding owned by that reviewer
        for the approved fingerprint, and resets its no-progress streak.
        """
        counters = self.reviewer(reviewer)
        counters.total_invocations += 1
        if clean_reapproval:
            counters.clean_reapprovals += 1

        resolved = []
        for row in self.open_findings(reviewer):
            row.status = "resolved"
            row.resolving_verdict = "APPROVE"
            row.resolving_fingerprint = fingerprint
            resolved.append(row.identity)

        counters.no_progress_streak = 0
        return {"reviewer": reviewer, "resolved": sorted(resolved), "no_progress_streak": 0}

    def invalidate_approvals(self):
        """Any implementation change invalidates non-matching approvals (031 FR-011).

        Handled by the driver against recorded fingerprints; the counters keep no
        approval state of their own beyond the registry rows.
        """
        return None

    # -- gate checks ------------------------------------------------------
    def would_exceed(self, reviewer: str) -> bool:
        """Pre-check: could this call exceed a gating cap? An over-cap call is never made."""
        return self.reviewer(reviewer).no_progress_streak >= self.max_iterations

    def breached(self):
        """Return (kind, name) for the first cap breached, or None."""
        for name, counters in sorted(self.reviewers.items()):
            if counters.no_progress_streak >= self.max_iterations:
                return ("reviewer", name)
        for identity, row in sorted(self.findings.items()):
            if row.reject_total >= self.max_iterations:
                return ("finding", identity)
        return None
