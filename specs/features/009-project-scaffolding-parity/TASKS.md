# Tasks: project-scaffolding-parity

## Phase 1: Preparation

- [x] T001 - Author `specs/_templates/SPECS-README.md`, `SDD-GUARDRAILS.md`, `CLAUDE-SDD.md`. Covers: FR-001.
- [x] T002 - Register the three templates in `profiles.json` (core). Covers: FR-001, AC-001.

## Phase 2: Implementation

- [x] T003 - Extend `skills/project-init/SKILL.md` to scaffold and fill the four `specs/` files. Covers: FR-002, AC-005.
- [x] T004 - Add `scripts/wire-hooks.sh` (bash 3.2 + python3 merge, backup, dry-run, idempotent). Covers: FR-003, AC-002, AC-003.
- [x] T005 - Add `scripts/wire-hooks.ps1` (PowerShell counterpart). Covers: FR-004.
- [x] T006 - `install.sh`/`install.ps1`: copy `settings.template.sh.json`; final NOTE about wire-hooks; hint in `link-project.sh`/`.ps1`. Covers: FR-005, AC-004.
- [x] T007 - Add bootstrap check to `skills/sdd/SKILL.md`. Covers: FR-006.

## Phase 3: Tests

- [x] T008 - Run AC-002/AC-003 against a temp dir; `install.sh --dry-run`; `check-consistency.sh --fix` + test harness green. Covers: AC-001..AC-004.

## Phase 4: Review

- [x] T009 - Update `docs/INSTALL.md`; final read-through of skill texts; mark spec Done. Covers: FR-007.
