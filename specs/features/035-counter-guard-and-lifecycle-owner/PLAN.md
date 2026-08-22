# Implementation Plan: counter-guard-and-lifecycle-owner

## Summary

Two small, independent changes: a committed eval scenario for the per-finding counter, and a
conditional exception in `/spec-review` plus its guardrail entry.

## Related spec

[SPEC.md](SPEC.md)

## Impacted areas

- `evals/scenarios/orchestrate-per-finding-counter.md` — new.
- `skills/spec-review/SKILL.md` — the `Ready` exception.
- `skills/sdd-guardrails/SKILL.md` — section 11 entry.

## Context budget

### Reading list

- This feature folder; `evals/scenarios/decomposer.md` as the format exemplar; `scripts/skill-eval.sh`
  sections 80–95 for the parser's required sections; `skills/spec-review/SKILL.md`;
  `skills/sdd-guardrails/SKILL.md` section 11; spec 032's `DECISIONS.md` D008/D009/D010.

### Model routing

Main session throughout. Both changes are small, decided, and text-only; delegating would cost more
context than it saves.

## Proposed approach

The eval scenario follows the committed format exactly — the harness reads `System prompt`,
`User message` and `Detection pattern` by section name, so the scenario is written against those
names rather than against prose conventions.

The `/spec-review` exception is written as a **conjunction**, not a softening: `Ready` is accepted
only with an accepted decision that names why `/spec-implement` was bypassed, and the reviewer must
cite that decision in its output. Without the citation the exception is unauditable, which would make
it exactly the silent status edit guardrails section 11 exists to prevent.

## Alternatives considered

- **Assert the counter prose in `check-consistency.sh`.** Rejected: asserting exact sentences in a
  document is brittle, fails on harmless rewording, and teaches people to work around the check
  rather than respect the rule.
- **Give `Ready → In Progress` to a new skill.** Rejected: a lifecycle state whose only purpose is to
  be passed through adds ceremony without adding verification.
- **Let `/spec-review` accept `Ready` unconditionally.** Rejected outright: that removes the
  protection instead of scoping it, and any spec could then reach `In Review` without implementation.

## Dependencies

None.

## Risks

- **The eval scenario cannot be validated by running it here** without provider quota. Mitigated by
  requiring only that the harness's reader parses it, which is what AC-001 asserts — and by saying so
  rather than implying the scenario was measured.
- **The exception could be abused** as a general bypass. Mitigated by the conjunction and the
  citation requirement.

## Test strategy

- `scripts/check-consistency.sh` before and after.
- Parse the new scenario with the harness's own section reader.

## Rollback strategy

Three text files; revert the branch.

## PLAN verification checklist

- [x] The plan covers all acceptance criteria (AC-001..AC-004).
- [x] The plan avoids behavior outside the spec.
- [x] The Context budget section is filled.
- [x] Risks are documented.
- [x] Test strategy is documented.
- [x] Rollback strategy is documented.
- [x] SPEC.md status has been updated to `Ready`.
