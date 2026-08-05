# Tasks: Token economy as a first-class framework principle

## Phase 1: Preparation

- [x] T001 - Write `docs/TOKEN_ECONOMY.md`: principle statement ("Context is a
  budget"), rule→mechanism mapping table with repo paths, and a "not covered"
  note (no telemetry, no hard enforcement). Keep ≤120 lines. Covers: AC-002.

## Phase 2: Implementation

- [x] T002 - README: replace the "Model cost awareness" bullet in
  `## 📐 Design principles` with a "Context is a budget" principle naming the
  four mechanisms; add a ≤5-line usage-based-pricing paragraph to
  `## 🎯 Why it exists`; link to `docs/TOKEN_ECONOMY.md`. Covers: AC-001.
- [x] T003 - Add an identical `## Context budget` section (subsections
  `Reading list`, `Model routing`) to BOTH `specs/_templates/PLAN.md` and the
  embedded PLAN template in `skills/spec-plan/SKILL.md`; add the matching PLAN
  verification checklist item in the skill. Covers: AC-003.
- [x] T004 - `skills/spec-analyze/SKILL.md`: add a context-budget item to the
  Analysis checklist and a corresponding Output-format section, stating the
  warning-when-missing / blocker-when-empty rule explicitly. Covers: AC-004.
- [x] T005 - Add a `## Token economy` section (concrete rules, no placeholders)
  to `specs/_templates/CONSTITUTION.md`. Covers: AC-005.
- [x] T006 - Add a single one-line cross-reference to `docs/TOKEN_ECONOMY.md`
  in the `## Token economy` section of `CLAUDE.md.example` (no rule text
  duplicated). Covers: AC-006.
- [x] T007 - Codex parity: mirror the spec-analyze context-budget check into
  `adapters/codex/prompts/sdd-spec-analyze.md`; add "Context budget" to the
  PLAN section enumeration in `adapters/codex/prompts/sdd-spec-plan.md`; update
  `adapters/codex/PARITY.md` to reflect the status honestly. Covers: AC-007.

## Phase 3: Tests

- [x] T008 - Structural verification: `git grep -c "## Context budget"` returns
  exactly the two template files; every path in the `TOKEN_ECONOMY.md` table
  resolves; no `TODO:`/placeholder in the new CONSTITUTION section. Covers:
  AC-002, AC-003, AC-005.
- [x] T009 - Regression + behavioral: run `bash scripts/check-consistency.sh`
  (must stay exit 0, new top-level doc must not trigger orphan-template); run
  `/spec-analyze` on this feature (filled section → pass) and on feature 019
  (missing → warning, not blocker). Covers: AC-004, AC-008.

## Phase 4: Review

- [x] T010 - Confirm dogfooding (this PLAN's `## Context budget` is filled),
  single-source discipline (no rule duplicated across files), and README tone
  consistency; then run `/spec-review`. Covers: AC-001, AC-006, AC-008.
