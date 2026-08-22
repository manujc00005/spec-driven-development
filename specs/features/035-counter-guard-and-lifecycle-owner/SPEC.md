# Feature Spec: counter-guard-and-lifecycle-owner

## Status

Ready

## Problem

Spec 032 closed with two deferred items, both recorded in its `CALIBRATION.md` and `DECISIONS.md`
rather than fixed, because both fall outside a calibration spec's scope.

1. **The per-finding counter rules are prose with no guard.** D008 and D010 changed how
   `sdd-orchestrate` counts per-finding REJECTs — count failed repairs, not re-reports, and only
   once an attempt has completed with a worker `DONE`. Both live as sentences in
   `skills/sdd-orchestrate/SKILL.md`. `scripts/check-consistency.sh` validates contracts and
   artifacts, not counter semantics, so nothing would catch an edit that reworded the rule back into
   the defect 032 found.

2. **A spec executed outside `/spec-implement` has no owner for `Ready → In Progress`.** D009
   recorded this when spec 032 hit it: its own D001 routed every calibration run to the maintainer's
   session, so `/spec-implement` never ran, and the spec sat at `Ready` with eight criteria closed by
   execution. Guardrails section 11 assigns each transition to exactly one skill and leaves no path
   for legitimate execution outside that one. 032 resolved it with a recorded decision, which is a
   workaround, not a rule.

## Goal

The counter rules are protected by something that fails when they regress, and a spec whose work is
legitimately driven outside `/spec-implement` has a documented, owned path to `In Review`.

## Non-goals

- **No change to the counter semantics themselves.** D008 and D010 are settled and were verified by
  spec 032's T014. This spec guards them; it does not revisit them.
- **No new lifecycle state.** The fix is about who may perform an existing transition, not about
  adding one.
- **No retrofit of past specs.** Specs already closed keep their recorded workarounds.

## Users / Actors

Maintainer, and any future session running `sdd-orchestrate` or the SDD lifecycle skills.

## Current behavior

`evals/scenarios/` holds behavioural scenarios that measure whether a skill changes model behaviour
across a control and a treatment arm. No scenario covers `sdd-orchestrate`. `skills/spec-review`
accepts only `In Progress` as the input state for its transition, and `sdd-guardrails` section 11
states the ownership rule without an exception.

## Desired behavior

- A committed eval scenario exercises the per-finding counter rule, so a reworded rule shows up as a
  measurable behavioural change rather than as silence.
- `/spec-review` accepts `Ready` as an input state **only** when `DECISIONS.md` records an accepted
  decision explaining why `/spec-implement` was bypassed, and says so in its output. Guardrails
  section 11 documents the exception with the same condition.

## Functional requirements

- FR-001: A scenario file under `evals/scenarios/` exercises the behaviour D008 and D010 define, in
  the format `scripts/skill-eval.sh` parses.
- FR-002: `/spec-review` may perform `Ready → In Review` when, and only when, a recorded accepted
  decision in the feature's `DECISIONS.md` explains why `/spec-implement` did not run. Absent that
  decision, `Ready` is refused exactly as today.
- FR-003: `sdd-guardrails` section 11 documents the exception, its condition, and why it is not a
  licence to skip implementation.

## Non-functional requirements

- The eval scenario must be runnable by the existing harness without changing the harness.
- `scripts/check-consistency.sh` must stay green.

## API / Interface changes

`skills/spec-review/SKILL.md` and `skills/sdd-guardrails/SKILL.md` gain the exception. No skill
contract block changes.

## Data model changes

None.

## Edge cases

- A feature at `Ready` with **no** such decision → `/spec-review` refuses, unchanged from today.
- A decision that exists but is `Proposed` rather than `Accepted` → refused; the exception requires
  an accepted decision.

## Acceptance criteria

- AC-001: `evals/scenarios/` contains a scenario for the per-finding counter whose sections parse
  under `scripts/skill-eval.sh`'s reader, verified by running the reader against it (FR-001).
- AC-002: `skills/spec-review/SKILL.md` states the `Ready` exception, its exact condition, and that
  the reviewer must name the decision it relied on (FR-002).
- AC-003: `sdd-guardrails` section 11 documents the same exception with the same condition (FR-003).
- AC-004: `scripts/check-consistency.sh` exits 0 and leaves the tree unchanged.

## Test scenarios

- Integration: `scripts/check-consistency.sh`.
- Manual: parse the new scenario with the harness reader; no full eval run is required, since running
  it costs provider quota and this spec only requires that the scenario exists and parses.

## Assumptions

- The eval harness's scenario format is stable; spec 022 owns it and this spec does not change it.

## Open questions

None.
