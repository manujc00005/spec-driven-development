# Tasks: counter-guard-and-lifecycle-owner

## Phase 2: Implementation

- [x] T001 - Write `evals/scenarios/orchestrate-per-finding-counter.md` in the committed scenario
  format, exercising the D008/D010 rule. Done when the harness's section reader extracts a non-empty
  `System prompt`, `User message` and `Detection pattern`. Covers: AC-001.

- [x] T002 - Add the conditional `Ready` exception to `skills/spec-review/SKILL.md`: accepted only
  with an accepted decision explaining why `/spec-implement` was bypassed, and the reviewer must name
  that decision in its output. Covers: AC-002.

- [x] T003 - Document the same exception and condition in `skills/sdd-guardrails/SKILL.md` section 11.
  Covers: AC-003.

## Phase 3: Tests

- [x] T004 - Run `./scripts/check-consistency.sh`; it must exit 0 and leave `git status --porcelain`
  as it found it. Parse the new scenario with the harness's reader and record the extracted sections.
  Covers: AC-001, AC-004.

## Phase 4: Review

- [x] T005 - `/spec-review`, `/qa-review`, `/spec-close`. Covers: AC-001, AC-002, AC-003, AC-004.
