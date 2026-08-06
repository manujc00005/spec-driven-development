# Tasks: Query-first graph access

`install*.{sh,ps1}`, `hooks/**`, `settings.template*.json`, `profiles.json` and every child project
are out of bounds for all tasks. No task stages, commits or pushes.

The ladder block is written once in T001 and copied verbatim; every later task reuses that wording.

## Phase 1: Doctrine

- [x] **T001** — Rewrite the Behavior section of `skills/graphify-context/SKILL.md` around the
  five-rung ladder, with report-reading demoted to rung 4 and its condition stated. Keep the
  graceful-degradation section intact and add the "CLI absent → report is rung 1" condition.
  *Files: `skills/graphify-context/SKILL.md`.* Covers: AC-001, FR-001.

- [x] **T002** — Update `docs/TOKEN_ECONOMY.md`'s rule table: the graph row names the access ladder
  and points at `skills/graphify-context/SKILL.md`.
  *Files: `docs/TOKEN_ECONOMY.md`.* Covers: AC-006, FR-006.

## Phase 2: Consumers

- [x] **T003** — `skills/context-manager/SKILL.md` step 1 leads with the query path; report reading
  becomes the fallback branch.
  *Files: `skills/context-manager/SKILL.md`.* Covers: AC-002, FR-002.

- [x] **T004** — `agents/codebase-researcher.md`: state the ladder **and** the no-Bash request
  protocol — name the exact command and hand back, never fall through to the report as a silent
  default. Verify no instruction requires a tool the agent lacks.
  *Files: `agents/codebase-researcher.md`.* Covers: AC-005, FR-005.

- [x] **T005** — `skills/sdd-workspace-onboarding/SKILL.md` token rules: `graphify summary` per
  project above report reading. Stay under the 600-line cap.
  *Files: `skills/sdd-workspace-onboarding/SKILL.md`.* Covers: AC-003, FR-003.

- [x] **T006** — `docs/WORKSPACE_SDD.md`: updated ladder plus the measured comparison table so the
  ordering is visibly evidence-backed.
  *Files: `docs/WORKSPACE_SDD.md`.* Covers: AC-004, AC-010, FR-004, FR-009.

- [x] **T007** — `adapters/codex/prompts/sdd-workspace-onboarding.md`: same ladder.
  *Files: `adapters/codex/prompts/sdd-workspace-onboarding.md`.* Covers: AC-007, FR-008.

## Phase 3: Enforcement

- [x] **T008** — Add the `graph-ladder` check to `scripts/check-consistency.sh`: each doctrine
  artifact must name the scoped-query commands. Presence only — not order (PLAN §4).
  *Files: `scripts/check-consistency.sh`.* Covers: AC-008, FR-007.

- [x] **T009** — Add two cases to `scripts/check-consistency.test.sh` proving the check fires when
  the mention is removed from `graphify-context/SKILL.md` and from `codebase-researcher.md`.
  *Files: `scripts/check-consistency.test.sh`.* Covers: AC-009, TS-2, TS-3.

## Phase 4: Record and validate

- [x] **T010** — CHANGELOG `[Unreleased]` entry stating the inversion and the measured ratio.
  *Files: `CHANGELOG.md`.*

- [x] **T011** — Run `check-consistency.sh`, `check-consistency.test.sh`, `json.tool profiles.json`.
  All must pass. Re-read `agents/codebase-researcher.md` against its tool grant.
  *Files: none.* Covers: AC-012.
