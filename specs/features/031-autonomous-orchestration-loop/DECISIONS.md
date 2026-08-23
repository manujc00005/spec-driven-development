# Decisions: autonomous-orchestration-loop

## Decision log

### D001 - Hub-and-blackboard coordination

**Date:** 2026-08-20

**Status:** Accepted

**Context:** Direct peer-to-peer agent messages are difficult to order, resume, and audit, and
Codex cannot provide equivalent native subagent routing.

**Decision:** The orchestrator is the hub. `TASKS.md`, `DECISIONS.md`, reviewer/worker blocks, and
`ORCHESTRATION.md` are the blackboard through which all coordination passes.

**Reasoning:** Durable files survive context compression, provide an audit trail, and keep the
protocol provider-neutral.

**Consequences:** Agents do not coordinate directly. The orchestrator persists every state change
before taking the next action.

### D002 - No autonomous commits in phase 1

**Date:** 2026-08-20

**Status:** Accepted

**Context:** Checkpoint commits would help crash recovery, but existing worker contracts and the
feature's safety boundary forbid agents from committing or pushing.

**Decision:** Phase 1 leaves an unstaged working tree in a dedicated branch/worktree. Checkpoint
commits are deferred to the phase-2 SDK runner.

**Reasoning:** Preserving the existing authority boundary is more important than adding a second
recovery mechanism; file-based state plus the worktree already bounds recovery.

**Consequences:** The autonomous loop must never invoke commit/push/merge. Recovery depends on the
working tree and `ORCHESTRATION.md`.

### D003 - Structured blocks alone drive control flow

**Date:** 2026-08-20

**Status:** Accepted

**Context:** Human-readable review prose is not a stable machine gate, as the repository's earlier
rendered-message matching failure demonstrated.

**Decision:** Reviewers retain prose but end with a YAML verdict block; workers end with a YAML
completion block. The orchestrator branches only on those blocks and fails closed on malformed or
missing structure.

**Reasoning:** A narrow explicit protocol is auditable and can later be parsed by the SDK runner.

**Consequences:** A malformed block can never be inferred as approval from surrounding prose.

### D004 - The orchestrator skill owns the schemas

**Date:** 2026-08-20

**Status:** Accepted

**Context:** Copying full schemas into five agent files would create multiple definitions that can
drift.

**Decision:** `skills/sdd-orchestrate/SKILL.md` is the canonical schema owner. Agent output sections
state the mandatory fields and reference that canonical contract rather than independently
redefining its semantics.

**Reasoning:** One source of truth minimizes coupling while keeping standalone agent output clear.

**Consequences:** Schema changes must update the skill first and then verify all five references.

### D005 - Conservative escalation classifier

**Date:** 2026-08-20

**Status:** Accepted

**Context:** Autonomous resolution is useful only when it cannot silently make product, legal,
financial, destructive, or public-contract choices.

**Decision:** A blocker is auto-resolvable only when it is purely technical, reversible, in scope,
and touches no human-gated domain. Any human-gated trigger wins and routes to the maintainer.

**Reasoning:** False escalation costs time; false autonomy can change the product or create
irreversible harm.

**Consequences:** Borderline cases pause. Contradictions with the SPEC route through
`/spec-update`.

### D006 - Markdown state with diff fingerprints

**Date:** 2026-08-20

**Status:** Accepted

**Context:** Conversation state is lost under compaction, while opaque JSON would weaken the
human-readable audit trail.

**Decision:** Persist state and append-only run evidence in per-feature `ORCHESTRATION.md`; bind
each APPROVE to a fingerprint of the reviewed diff.

**Reasoning:** Markdown is readable without tooling, and fingerprints make selective invalidation
on re-entry deterministic enough for phase 1.

**Consequences:** The file is authoritative over conversation memory. A changed fingerprint
invalidates only the associated approval.

### D007 - Sequential Codex degradation preserves protocol, not concurrency

**Date:** 2026-08-20

**Status:** Accepted

**Context:** The Codex adapter models agents as roles in one session and does not provide the
Claude adapter's native Agent-tool isolation.

**Decision:** Codex runs the same state machine sequentially in one context with the same files,
blocks, caps, and escalation rules.

**Reasoning:** Behavioral protocol parity is attainable; claiming concurrency or deterministic
permission parity is not.

**Consequences:** `PARITY.md` must explicitly preserve the limitation and the installed Codex CLI
must be smoke-tested before closure.

### D008 - Do not add an installable ORCHESTRATION template

**Date:** 2026-08-20

**Status:** Accepted

**Context:** Files under `specs/_templates/` are installable artifacts that must be registered in
`profiles.json`; the SPEC explicitly excludes installer and profile changes.

**Decision:** Put the canonical initial `ORCHESTRATION.md` scaffold in the autonomous section of
the orchestrator skill and create the per-feature artifact on first entry. Do not add
`specs/_templates/ORCHESTRATION.md` in this feature.

**Reasoning:** This satisfies the per-run data model without widening the shipped-template surface
or contradicting the repository's consistency checker.

**Consequences:** Future reuse as a general lifecycle template would require a separate spec that
updates the core profile and counts.

### D009 - Verification and calibration gates

**Date:** 2026-08-20

**Status:** Accepted

**Context:** The shipped change is markdown-only, but its behavior is a stateful protocol whose
acceptance criteria cannot be proven by inspection alone.

**Decision:** Use `scripts/check-consistency.sh` plus its self-test as the baseline/exit suite, and
use a disposable uncommitted demo feature for behavioral calibration. Persist only evidence in
`CALIBRATION.md`.

**Reasoning:** The scripts cover repository contract drift; the seeded run covers control flow,
resumption, escalation, and convergence without polluting numbered feature history.

**Consequences:** There is no application build/typecheck/lint target for this diff. A real small
feature run and Codex smoke test remain mandatory before `/spec-close`.

### D010 - Status gate distinguishes first entry from re-entry

**Date:** 2026-08-20

**Status:** Accepted

**Context:** FR-002 requires `Status: Ready` at the entry gate, while FR-011 requires resuming a run
whose owning lifecycle skills may already have advanced the same spec to `In Progress` or
`In Review`.

**Decision:** A first autonomous entry (no valid `ORCHESTRATION.md`) requires exactly `Ready`. A
re-entry identified by an existing state file for the same feature may accept `In Progress` or
`In Review` when the run is ACTIVE, PAUSED, or ABORTED with `resumable: yes`; every other status or
non-resumable run refuses. Re-entry never edits status directly.

**Reasoning:** Applying the first-entry predicate to resumed runs would make the mandated resume
path impossible. The state file provides the durable evidence that this is re-entry rather than a
gate bypass.

**Consequences:** AC-002 calibrates `Status != Ready` on first entry. AC-005 separately calibrates
the allowed resumed lifecycle states and rejects a mismatched or terminal state file.

### D011 - Fingerprint the reviewable tree, not the state file

**Date:** 2026-08-20

**Status:** Accepted

**Context:** Plain `git diff` omits untracked files, while including `ORCHESTRATION.md` in its own
fingerprint would change the fingerprint every time the audit log is updated.

**Decision:** The canonical fingerprint hashes the tracked diff plus sorted untracked file paths
and contents, excluding `ORCHESTRATION.md` and generated calibration/PR evidence that does not
belong to the implementation under review. After the fully reviewed fingerprint is frozen, expected
owning-skill lifecycle writes are captured in the separate closure delta defined by D015; they are
not silently excluded before that boundary.

**Reasoning:** Review approvals must bind to every implementation artifact without becoming
self-invalidating because orchestration metadata advanced.

**Consequences:** The skill specifies the inclusion/exclusion rule rather than a platform-specific
one-liner. Providers may implement the hashing command differently but must produce the same input
set deterministically.

### D012 - Calibration harness owns a disposable baseline commit

**Date:** 2026-08-20

**Status:** Accepted

**Context:** The autonomous entry gate correctly requires a clean tree, but a newly created demo
feature and the candidate contract are dirty until they have a git baseline.

**Decision:** The calibration harness may create one local baseline commit on its disposable branch
before invoking the loop. That setup commit is not made by the autonomous loop, is never pushed,
and the whole branch/worktree is deleted after evidence is collected.

**Reasoning:** Weakening or bypassing the clean-tree gate would fail to test the shipped contract.
Separating fixture setup from the observed loop preserves the no-auto-commit invariant.

**Consequences:** AC-007 command-log inspection begins after the baseline commit and must show zero
commit/push/merge commands by either provider run. The retained repository receives no fixture
commit.

### D013 - Recoverable aborts use monotonic caps

**Date:** 2026-08-20

**Status:** Accepted

**Context:** The original contract made cap exhaustion `ABORTED`, while authenticated re-entry
rejected terminal results. That made the advertised cap overrides useless after the most common
non-convergence stop and left no safe distinction between remediable exhaustion and corrupt state.

**Decision:** `ABORTED` carries `resumable: yes|no`. Cap exhaustion and a remediable verification
failure are resumable; corrupt/mismatched provenance or unsafe unexplained writes are not. On
authenticated re-entry, overrides may only increase effective caps. Stored counters never reset,
and every cap change is appended to the audit log before another delegation.

**Reasoning:** A budget must remain a hard bound for each invocation without turning a deliberate
human decision to spend more into a fresh run that loses history.

**Consequences:** D010's authenticated re-entry includes `PAUSED` and `ABORTED + resumable: yes`.
Calibration must prove refusal without a higher cap, preservation of counters, and successful
resume only after a monotonic increase.

### D014 - Delegations are recoverable attempts, not atomic calls

**Date:** 2026-08-20

**Status:** Accepted

**Context:** An agent can write files and the session can die before its response or task checkbox
is persisted. A single `current task` field cannot distinguish “nothing happened” from “partial
implementation exists”, and blindly re-delegating could duplicate or overwrite useful work.

**Decision:** Persist an attempt record before every delegation with a stable ID, lifecycle,
objective, allowed-path scope, and pre-fingerprint. Persist response, post-fingerprint, validation,
and outcome afterward. Re-entry reconciles the real tree: unchanged work may retry; attributable
changed work is verified/reviewed and marked `RECOVERED`; unexplained or out-of-scope changes fail
closed for maintainer inspection.

**Reasoning:** This is the strongest crash recovery phase 1 can provide without checkpoint commits
or a transactional SDK runner.

**Consequences:** Dirty-path attribution derives from durable pre-call scope, not retrospective
conversation memory. The calibration interrupts after a real file write and before a completion
block, and also seeds an out-of-scope path. Non-resumable recovery preserves the aborted audit file
and restarts only from the recorded clean baseline in a fresh dedicated worktree.

### D015 - Current-tree approvals and an explicit closure boundary

**Date:** 2026-08-20

**Status:** Accepted

**Context:** Re-running only a rejecting reviewer after a fix leaves other reviewers approved on an
older fingerprint. Separately, `/spec-review` and `/spec-close` legitimately modify lifecycle
metadata after final approval, which would recursively stale the approval if treated like an
implementation change.

**Decision:** Any implementation change invalidates every required APPROVE whose fingerprint no
longer matches, and all stale reviewers must re-run before final conformance. Once the complete
review set approves, freeze that implementation fingerprint. Owning lifecycle skills and generated
audit/PR evidence may then create only a recorded closure delta; lifecycle-only deltas do not stale
the frozen approval, while any production, test, requirement, plan, task-content, or decision change
returns the loop to review (or `/spec-update` when requirements changed).

**Reasoning:** Review gates must describe one coherent implementation snapshot, while status
ownership must remain with the lifecycle skills without producing an impossible self-invalidating
terminal state.

**Consequences:** The old “re-run only the rejecting reviewer” wording is removed. AC-008 tests
cross-review invalidation and AC-010 tests both allowed and unexpected closure deltas.

### D016 - Findings and cost accounting are explicit state

**Date:** 2026-08-20

**Status:** Accepted

**Context:** Encoding `(from SEC-003)` only in a task title is insufficient for deduplication and
does not let a maintainer reconstruct the finding lifecycle from `ORCHESTRATION.md` alone. The term
“delegation budget” also did not say whether retries and deep-reasoner calls consume it.

**Decision:** Add a findings registry keyed by reviewer plus finding ID, mapping to one stable task
and recording first/last seen iteration, action, status, and resolving verdict/fingerprint. Count
every worker, reviewer, deep-reasoner, and structured-output retry against the delegation budget;
log but do not count deterministic local commands or same-context owning-skill calls.

**Reasoning:** Explicit identity prevents duplicate repair work, and explicit accounting makes the
cost backstop testable and provider-neutral.

**Consequences:** `ORCHESTRATION.md` alone can reconstruct finding convergence. AC-009 verifies
deduplication and AC-006 verifies exact counter behavior.

### D017 - Spec updated: caps measure stagnation, not workload

**Date:** 2026-08-21

**Status:** Accepted

**Context:**

An audit of the implemented protocol found that the iteration cap gated *every* reviewer
invocation against a single monotonic per-reviewer counter
([SKILL.md:270](../../../skills/sdd-orchestrate/SKILL.md:270),
[SKILL.md:318](../../../skills/sdd-orchestrate/SKILL.md:318),
[SKILL.md:378](../../../skills/sdd-orchestrate/SKILL.md:378)). Because the loop processes one task
at a time ([SKILL.md:175](../../../skills/sdd-orchestrate/SKILL.md:175)) and runs `domain-reviewer`
on every implemented diff ([SKILL.md:188](../../../skills/sdd-orchestrate/SKILL.md:188)), while
D015 invalidates and re-runs every stale approval after any change, a reviewer consumed one
iteration per task regardless of whether it ever disagreed. With `max-iterations=3` the run aborted
on the fourth implemented task even on a fully converging feature — this spec's own 16-task queue
could never have completed. The T009 calibration already showed the symptom: `domain=3/3` exhausted
in a two-step fixture where domain never rejected once
([CALIBRATION.md:102](CALIBRATION.md:102)). The defect originated in FR-009's wording, not in the
implementation, which followed the spec faithfully.

**Decision:**

FR-009 now defines two non-convergence counters instead of one invocation counter. Per reviewer:
consecutive **no-progress** REJECTs, reset by an APPROVE *or* by any REJECT that resolves at least
one of that reviewer's open findings — so a reviewer finding a genuinely different defect each
round keeps iterating. Per finding identity: total REJECTs on the same `<reviewer>:<finding-id>`,
which catches flip-flops a consecutive counter misses. Clean re-approvals consume neither cap. The
delegation budget becomes the sole global monotonic backstop and its default is now task-relative,
`max(25, 6 × unchecked tasks at first entry)`. Not changed: monotonic re-entry, the increase-only
override rule, fail-closed malformed handling, and D015 invalidation.

**Reasoning:**

The cap exists to detect disagreement that will not converge (AC-006), not to bound how much work
a feature contains. Conflating the two made unattended completion impossible for any feature larger
than the cap and pushed the maintainer back into the loop every three tasks — defeating the goal.
Cost is a separate concern and belongs to the delegation budget, which is why that budget must
scale with the queue it has to absorb.

**Consequences:**

T002 and T004 are `[NEEDS REVIEW]`: the skill's cap logic and `ORCHESTRATION.md` counter fields
must be rewritten, and T013's abort calibration re-specified against the consecutive counter. New
AC-011 and new T017 calibrate the four cap behaviors on a fixture with more tasks than
`max-iterations`, since the current three-step fixture is structurally unable to detect this class
of bug. Risk introduced: the `6 ×` budget factor is an estimate with no calibration evidence yet.

### D018 - Spec updated: user-facing discoverability and symmetric provider evidence

**Date:** 2026-08-21

**Status:** Accepted

**Context:**

The same audit found two scope gaps. `docs/SDD-ORCHESTRATION.md`, the user-facing orchestration
guide, documents only the free-form invocation and never mentions autonomous mode, and `CHANGELOG.md`
has no entry although the ten most recent feature commits all carry one. Neither file appeared in
the SPEC, the PLAN's impacted areas, or any task, so no reviewer could have flagged their absence.
Separately, every behavioral PASS in `CALIBRATION.md` comes from Codex; the Claude Code run was
blocked by a session quota ([CALIBRATION.md:131](CALIBRATION.md:131)), leaving the primary adapter
with no runtime evidence.

**Decision:**

Add FR-014 and AC-012 for the documentation and changelog, and AC-013 requiring behavioral evidence
from both providers before closure, with an unavailable provider recorded as an explicit
`/spec-close` blocker rather than omitted. Add T018, T019, and T020 to cover them.

**Reasoning:**

A flagship capability that only exists in a skill contract is undiscoverable by the people meant to
use it. And the framework's own Codex-parity rule means Codex must be covered *as well as* Claude
Code, never instead of it — a Codex-only pass on the primary adapter's flagship feature inverts
that rule.

**Consequences:**

Three new tasks and two new acceptance criteria. `Done` now depends on a Claude Code run that is
currently quota-blocked, so closure may legitimately stall on an external limit — which is the
intended honest outcome rather than a silent pass.

### D019 - Spec updated: tiered closure standard, and what defers to a follow-up

**Date:** 2026-08-21

**Status:** Accepted

**Context:**

A conformance pass over the evidence found six criteria fully evidenced, five partial and one
(AC-005) with none at all, plus a stale evidence matrix that contradicted its own per-run verdicts.
The open work — T012, T014, T016, T021, T022 — is evidence, not known defects, so "finish
everything" and "close now" were both defensible and the standard had to be stated rather than
assumed.

**Decision:**

`Done` uses a tiered standard: a criterion protecting against **silent loss of work or a false
claim of success** must be fully evidenced; a criterion whose failure mode is only an abort firing
too early or too late may close with the gap documented in `CALIBRATION.md`. On that basis T012
(AC-005 interrupted-write recovery) is blocking and stays in 031, T016 stays because it is the pass
that caught the stale matrix, and T014, T021 and T022 defer to a follow-up. The maintainer's real
non-seeded run stays a closure requirement and becomes T023 with an explicit owner. Provider
asymmetry is documented in `PARITY.md` rather than closed by re-running five criteria.

**Reasoning:**

A framework whose selling point is that completion requires reviewable evidence cannot sign `Done`
over unevidenced criteria without hollowing out the claim. But requiring every clause of every
criterion would block indefinitely on low-consequence edge cases. The dividing line that survives
both objections is consequence: T012 is the only gap that can corrupt a maintainer's working tree,
because an unproven recovery path either reimplements blindly over partial writes or fails to
fail-closed on unattributed paths. The rest can only mis-time an abort, which is visible and
recoverable.

**Consequences:**

031 closes after T012, T016 and T023. T014, T021 and T022 move to a follow-up spec, and AC-006,
AC-007, AC-008, AC-010 and AC-011 will close as PARTIAL with the gap named in the matrix — an
explicit, auditable debt rather than an unstated one. Risk accepted: those five clauses ship
unexercised.

### D020 - The T023 provenance break is tolerated, and the limitation is recorded with it

**Date:** 2026-08-23

**Status:** Accepted

**Context:**

T023's run executed in a worktree that was destroyed before the third conformance round could read
it, leaving its branch orphaned. The conformance gate refused to certify from a prose report and
raised the question as CONF-014, addressed to the maintainer and blocking this spec's close. This
spec had meanwhile been marked `Done`, so the repository asserted two incompatible things about it.

**Decision:**

The break does not disqualify the run as T023 evidence. CONF-014 is closed.

**Reasoning:**

T023 guards one flaw: evidence contaminated by a fixture the reviewing agent designed. The run does
not have it - spec 033 is a real feature, nothing was seeded, and its findings are of a kind no
fixture produces. The destroyed worktree cost re-auditability of the execution environment, which is
a different property. The content was reconstructed with git rather than recalled, and approved by a
gate that read the files.

Re-running was rejected as settlement by attrition, which the gate itself warned against. Carrying
it as open debt was rejected as the worst option: prudent-looking, and assigned to nobody.

**Consequences:**

The assurance this run offers is bounded: its execution environment cannot be re-audited, so the
findings must be re-derived from the recorded content rather than by replay. That limitation is
written into the T023 section rather than left implicit. This spec's `Done` status is now consistent
with its own evidence record.
