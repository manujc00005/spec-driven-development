# Feature Spec: autonomous-loop-residual-calibration

## Status

Ready

## Problem

Spec 031 shipped the autonomous orchestration loop with five acceptance criteria closed as
**PARTIAL**: each has real observed evidence for some clauses and none for the rest. D019 accepted
that debt deliberately, on the grounds that every remaining clause fails in a way that mis-times an
abort — visible and recoverable — rather than corrupting a working tree. That reasoning justifies
deferring the work; it does not make the work unnecessary. Left unwritten, the debt decays into the
same thing it was meant not to be: an unstated gap between what the framework claims and what it
has observed.

Three behaviors ship unexercised:

1. **The delegation-budget abort** (AC-006). Every abort observed so far fired on non-convergence.
   The budget — now task-relative at `max(25, 6 × unchecked tasks)` — has never actually stopped a
   run, so the one backstop against an unbounded loop is the one nobody has watched work.
2. **Cap re-entry** (AC-006). A recoverable abort must refuse an unchanged or lower cap and resume
   only with a higher one, preserving counters and logging the change. Unproven in both directions.
3. **The cap model's remaining two clauses** (AC-011 c and d) and the **safety and closure sweep**
   (AC-007, AC-010): a flip-flop finding aborting on the per-finding counter, a reviewer rejecting
   past the cap while resolving a prior finding each round and legitimately continuing, a
   non-autonomous invocation still behaving as before, and a seeded non-lifecycle post-approval
   change invalidating final conformance.

Clause (d) carries a known residual risk 031 recorded but could not close: the progress rule trusts
reviewers to reuse finding ids honestly, so a reviewer allocating a fresh id each round while
drifting to a new concern reads as progress and is bounded only by the delegation budget.

## Goal

Every acceptance criterion 031 closed as PARTIAL reaches full observed evidence, and the
id-reuse residual risk is either shown to be tolerable or given a mitigation.

## Non-goals

- **No protocol redesign.** This spec calibrates what 031 built. A defect found here becomes a
  scoped fix with its own decision record, not a rewrite.
- **No re-running the five Codex-only criteria on Claude Code.** That asymmetry was accepted in
  D019 and documented in `PARITY.md`.
- **No new autonomous-mode features**, and no change to the cap model unless calibration proves it
  wrong.

## Users / Actors

Maintainer, orchestrator session, and the same delegated agents 031 uses.

## Current behavior

`sdd-orchestrate --autonomous` implements all of the above; none of it has been observed running.
The evidence matrix in `specs/features/031-autonomous-orchestration-loop/CALIBRATION.md` names each
gap.

## Desired behavior

Each gap has a seeded calibration run recorded in this feature's `CALIBRATION.md`, with the same
discipline 031 used: a disposable worktree on a non-default branch, a green hermetic baseline, real
subagents rather than narrated ones, and a fixture sized against the threshold it exercises.

## Functional requirements

- FR-001: A run whose delegation budget is exhausted aborts recoverably, naming the budget and the
  count, and is distinguishable in its record from a non-convergence abort.
- FR-002: Re-entry after a cap-exhaustion abort refuses an omitted, equal or lower cap and resumes
  only on an explicit increase, preserving every counter and appending the cap change before work.
- FR-003: A finding alternating REJECT/APPROVE past `max-iterations` aborts on the per-finding
  counter while no per-reviewer streak ever reaches the cap.
- FR-004: A reviewer rejecting more than `max-iterations` times in a row while resolving a prior
  finding each round runs to a legitimate DONE.
- FR-005: A non-autonomous `sdd-orchestrate` invocation behaves exactly as before autonomous mode
  existed, and the default-branch refusal holds on the primary adapter.
- FR-006: A seeded non-lifecycle change made after the implementation freeze invalidates final
  conformance and returns the loop to REVIEW, while lifecycle-only writes do not.
- FR-007: The id-reuse residual risk is assessed against a reviewer that allocates a fresh finding
  id each round while drifting; the outcome is either a recorded tolerance with its reasoning or a
  mitigation specified for a follow-up.

## Non-functional requirements

- Observability: every run's evidence must be reconstructable from its `CALIBRATION.md` entry alone.
- Maintainability: fixtures must be sized against the thresholds they exercise — 031 learned that a
  three-step fixture cannot detect a cap defect — and must not be able to read the spec that
  documents their own seeds, which contaminated one 031 run.

## API / Interface changes

None expected. A calibration-driven fix would touch `skills/sdd-orchestrate/SKILL.md` only.

## Data model changes

None.

## Edge cases

- A calibration run reveals a real protocol defect → record it as a decision here and scope the fix;
  do not silently patch the skill mid-run.
- The budget and a non-convergence cap would trip on the same call → the record must state which
  fired first and why, since conflating them is the exact confusion D017 fixed.

## Acceptance criteria

- AC-001: A recorded run shows a budget-exhaustion abort with `resumable: yes`, naming the budget,
  and its record is unambiguously distinct from a non-convergence abort (FR-001).
- AC-002: A recorded run shows re-entry refused for omitted, equal and lower caps, and accepted for
  a higher one with counters preserved and the cap change logged (FR-002).
- AC-003: A recorded run shows the per-finding abort firing while every per-reviewer streak stays
  below the cap (FR-003).
- AC-004: A recorded run shows a reviewer exceeding `max-iterations` consecutive rejections and
  still reaching DONE because each round resolved a prior finding (FR-004).
- AC-005: A recorded run shows a non-autonomous invocation unchanged and the default-branch refusal
  firing on Claude Code (FR-005).
- AC-006: A recorded run shows a seeded post-approval production change invalidating final
  conformance, and lifecycle-only writes not doing so (FR-006).
- AC-007: The id-reuse risk has a written verdict backed by an observed run (FR-007).
- AC-008: 031's evidence matrix is updated so no criterion it closed as PARTIAL remains PARTIAL
  without a reason that outlived this spec.

## Test scenarios

- Unit / Integration: none beyond `scripts/check-consistency.sh` if any contract changes.
- E2E: one seeded calibration run per acceptance criterion.
- Manual: none required; 031's T023 covers the real-feature run.

## Assumptions

- The 031 protocol is correct as written and these runs confirm rather than redesign it. If two or
  more runs find genuine defects, that assumption is wrong and this spec should stop and re-plan.
- Fixtures can be built without a real provider quota beyond ordinary subagent use.

## Open questions

- OQ-1 (non-blocking): should the id-reuse mitigation, if one is needed, live in the reviewer agent
  contracts or in the orchestrator's finding-registry logic? Answerable only after AC-007's run.

## Contracted services

Contracted services not declared → all billable add-ons treated as NOT contracted (conservative
default). Run `/project-init` to declare them.
