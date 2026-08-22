# Implementation Plan: task-verification-criterion

## Summary

Add a `Verify:` clause to the task-line format so a task records how anyone checks it is done, not
only which requirement it serves. Documentation-level contract across two skills, two templates and
two Codex prompts. Additive: every existing `TASKS.md` stays valid.

## Related spec

[SPEC.md](SPEC.md)

## Impacted areas

- `skills/spec-plan/SKILL.md` — emits the clause; reports when a task has no checkable criterion.
- `skills/spec-analyze/SKILL.md` — the blocking finding.
- `skills/sdd-orchestrate/SKILL.md` — reads the clause as a task-level stop condition.
- `specs/_templates/TASKS.md`, `specs/_templates/SDD-GUARDRAILS.md`.
- `adapters/codex/prompts/` — the two prompts named in FR-006.

## Context budget

### Reading list

This feature folder; the five files above; one existing `TASKS.md` as a backward-compatibility
sample. No whole-repo scans; `specs/features/*/TASKS.md` is read only by the AC-003 check.

### Model routing

`fast-worker` throughout — every task is a bounded text edit whose shape the SPEC already fixes.
`deep-reasoner` only if a reviewer finds a contradiction between the new clause and the 031 loop
protocol, which the non-goals forbid changing.

## Proposed approach

Order is dependency-first: the format is defined once (template), then the producer emits it, then
the gate enforces it, then the consumer reads it, then parity and backward compatibility are
verified. Defining the format last would make every earlier task guess at it.

The one irreversible decision is the **clause syntax**, because it becomes a documentation contract
two adapters and thirty existing files must agree with. Everything else is reversible text.

## Alternatives considered

- **A separate `VERIFICATION.md` per feature.** Rejected: it splits a task from its own done
  criterion, and the loop would have to correlate two files to close one task.
- **Machine-executable criteria only.** Rejected by AC-006: some real criteria are human judgement,
  and forcing executability would push people to write a fake command.
- **Backfilling existing task lists.** Rejected by the non-goals; the field is additive and
  AC-003/AC-007 exist to prove old files still pass.

## Dependencies

None outside the repository.

## Risks

- **Format churn.** If the clause syntax changes after the adapters adopt it, three surfaces drift.
  Mitigated by fixing the syntax in the template first.
- **Gate false positives.** An over-strict `spec-analyze` finding would block every legacy file;
  AC-003 and AC-007 are the guard.
- **Scope creep into a runner.** FR-010 and the non-goals forbid executing the clause; any task that
  starts building a runner is out of scope.

## Test strategy

- Integration: `./scripts/check-consistency.sh` before and after.
- Backward compatibility: run the `spec-analyze` rule against every existing `specs/features/*/TASKS.md`
  and confirm none becomes blocking (AC-003, AC-007).
- Manual: none.

## Rollback strategy

Text-only across six files on a dedicated branch; revert the branch. No migration, no generated
artifact, nothing installed.

## PLAN verification checklist

- [x] The plan covers all acceptance criteria (AC-001..AC-009).
- [x] The plan avoids behavior outside the spec.
- [x] The Context budget section is filled.
- [x] Risks are documented.
- [x] Test strategy is documented.
- [x] Rollback strategy is documented.
- [x] SPEC.md status has been updated to `Ready`.
