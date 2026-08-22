# Tasks: task-verification-criterion

## Phase 1: Format

- [x] T001 - Fix the clause syntax in `specs/_templates/TASKS.md`: a task line gains
  `Verify: <how anyone checks this is done>` after `Covers:`. State that the criterion may be a
  command or a human check, and that nothing in the framework executes it. Covers: AC-001, AC-006,
  AC-008.

## Phase 2: Producer and gate

- [ ] T002 - `skills/spec-plan/SKILL.md`: emit the clause in the TASKS.md template it writes, and
  require it on every task it produces. When a task's outcome cannot be stated as a criterion, report
  that rather than inventing one. Covers: AC-001, AC-009.

- [ ] T003 - `skills/spec-analyze/SKILL.md`: return a blocking finding when a task list produced
  after this change has a missing or empty clause on a task item. The detection unit is the bullet
  plus its continuation lines, and the clause is the one following `Covers:` — never a physical-line
  or raw-content match; see D002 and both its revisions. A file where no task line carries one is legacy and passes
  untouched. Covers: AC-002, AC-007.

- [x] T008 - (from DOM-001) The template's only human-check example is the blanket phrase SPEC edge
  case 1 forbids, and omits edge case 7's requirement that a human criterion name who checks and
  against what. Add that constraint to the template and fix the example. Allowed files:
  `specs/_templates/TASKS.md` ONLY. Covers: AC-006.

## Phase 3: Consumer and parity

- [ ] T004 - `skills/sdd-orchestrate/SKILL.md`: read the clause as the task-level stop condition when
  present, without changing cap semantics, abort classes or re-entry rules. Covers: AC-004.

- [ ] T005 - Mirror the rule in `specs/_templates/SDD-GUARDRAILS.md` and the two Codex prompts named
  in FR-006, so the adapters state the same contract. Covers: AC-005.

## Phase 4: Backward compatibility and review

- [ ] T006 - Run the AC-003/AC-007 check: every existing `specs/features/*/TASKS.md` must still pass,
  and adding one clause to a legacy file must not make it blocking. Record the file count checked.
  Covers: AC-003, AC-007.

- [ ] T007 - `./scripts/check-consistency.sh` exits 0 and leaves the tree unchanged. Covers: AC-008.
