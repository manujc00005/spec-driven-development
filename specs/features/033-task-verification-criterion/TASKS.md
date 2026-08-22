# Tasks: task-verification-criterion

## Phase 1: Format

- [x] T001 - Fix the clause syntax in `specs/_templates/TASKS.md`: a task line gains
  `Verify: <how anyone checks this is done>` after `Covers:`. State that the criterion may be a
  command or a human check, and that nothing in the framework executes it. Covers: AC-001, AC-006,
  AC-008.

## Phase 2: Producer and gate

- [x] T002 - `skills/spec-plan/SKILL.md`: emit the clause in the TASKS.md template it writes, and
  require it on every task it produces. When a task's outcome cannot be stated as a criterion, report
  that rather than inventing one. Covers: AC-001, AC-009.
  Verify: `grep -A2 'TASKS.md template' skills/spec-plan/SKILL.md` shows a task line carrying `Verify:`.

- [x] T003 - `skills/spec-analyze/SKILL.md`: return a blocking finding when a task list produced
  after this change has a missing or empty clause on a task item. The detection unit is the bullet
  plus its continuation lines, and the clause is the one following `Covers:` — never a physical-line
  or raw-content match; see D002 and both its revisions. A file where no task line carries one is legacy and passes
  untouched. Covers: AC-002, AC-007.
  Verify: `skills/spec-analyze/SKILL.md` contains a section defining the task-item detection unit and the positional test after `Covers:`.

- [x] T008 - (from DOM-001) The template's only human-check example is the blanket phrase SPEC edge
  case 1 forbids, and omits edge case 7's requirement that a human criterion name who checks and
  against what. Add that constraint to the template and fix the example. Allowed files:
  `specs/_templates/TASKS.md` ONLY. Covers: AC-006.
  Verify: `specs/_templates/TASKS.md` states that a human criterion names who checks and against what, and its human example names both.

## Phase 3: Consumer and parity

- [x] T004 - `skills/sdd-orchestrate/SKILL.md`: read the clause as the task-level stop condition when
  present, without changing cap semantics, abort classes or re-entry rules. Covers: AC-004.
  Verify: `grep -n 'Verify' skills/sdd-orchestrate/SKILL.md` shows the clause used as a stop condition in step 2 and recorded in the attempt row, and nowhere else.

- [x] T005 - Mirror the rule in `specs/_templates/SDD-GUARDRAILS.md` and the two Codex prompts named
  in FR-006, so the adapters state the same contract. Covers: AC-005.
  Verify: the same four contract elements appear in `specs/_templates/SDD-GUARDRAILS.md` and both Codex prompts named in FR-006.

## Phase 4: Backward compatibility and review

- [x] T006 - Run the AC-003/AC-007 check: every existing `specs/features/*/TASKS.md` must still pass,
  and adding one clause to a legacy file must not make it blocking. Record the file count checked.
  Covers: AC-003, AC-007.
  Verify: the probe over every `specs/features/*/TASKS.md` reports zero false adoptions, and its counts are recorded in this feature's evidence.

- [x] T007 - `./scripts/check-consistency.sh` exits 0 and leaves the tree unchanged. Covers: AC-008.
  Verify: `./scripts/check-consistency.sh` exits 0 and `git status --porcelain` is byte-identical before and after it.

## Phase 5: Record (from CONF-005)

- [x] T009 - AC-008 has two halves and only the first is covered: no task verifies that the loop's
  own record shows the criterion and the result for a task it closed. Add that check to this
  feature's evidence by closing this very task through the loop and citing its record.
  Covers: AC-004, AC-008.
  Verify: `specs/features/033-task-verification-criterion/ORCHESTRATION.md` contains a
  `Current task verification` field naming this task's criterion and its result, and the Attempts
  row for this task records the same, with no field left as a placeholder.
