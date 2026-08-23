# Tasks: mindset-reminder-hook

**Ordering:** T001 precedes T005 (tests drive the hook through stdin, so its interface must exist).
T002–T004 precede T007 (`check-consistency` validates declaration against disk).

## Phase 1: Preparation

- [x] T001 - Write `hooks/scope-keeper-reminder.sh`: consume stdin, read `session_id` via
  `hooks/lib/claude-json.sh`, sanitise it to `[A-Za-z0-9_-]`, throttle on a marker in the system
  temp dir, emit the `[scope-keeper]` system message, honour `SDD_SCOPE_REMINDER=0`, and **exit 0
  on every path**. Covers: AC-001, AC-002, AC-003, AC-004, AC-005, AC-006, AC-007, AC-008. (D002, D003, D004)

## Phase 2: Implementation

- [x] T002 - Port it to `hooks/scope-keeper-reminder.ps1` with identical messages and exit codes.
  Covers: AC-012.

- [x] T003 - Declare `scope-keeper-reminder` under the `core` profile in `profiles.json`.
  Covers: AC-010. (FR-006)

- [x] T004 - Wire `PreToolUse` / `Edit|Write|NotebookEdit` into `settings.template.json` and
  `settings.template.sh.json`, matching the existing entries' timeout and `statusMessage` shape.
  Covers: AC-011. (FR-007)

## Phase 3: Tests

- [x] T005 - `scripts/mindset-hook.test.sh` covering AC-001..AC-009, including the traversal case
  and the excerpt-vs-skill corroboration. Covers: AC-001..AC-009.

- [x] T006 - `scripts/mindset-hook.test.ps1` mirroring AC-001..AC-008. Covers: AC-012.

- [x] T007 - Wire both suites into `.github/workflows/consistency.yml` (bash into `check`,
  PowerShell into `windows-syntax`); confirm `check-consistency.sh` and `shellcheck -S error` stay
  green. Covers: AC-010, AC-013.

## Phase 4: Review

- [x] T008 - Apply D005 to the user's global `~/.claude/CLAUDE.md`: replace the pure pointer with
  the two or three load-bearing scope rules as text. Outside the repo, so not CI-enforced.

- [x] T009 - Document the hook and `SDD_SCOPE_REMINDER=0` in `CLAUDE.md.example` and `CHANGELOG.md`.
  Covers: AC-013. (FR-009)

- [x] T010 - Manual live check: reminder appears before the first edit of a session and not before
  the second.
  **DEFERRED (2026-08-23) → DEBT-008.** The session that wrote the hook started before the hook
  was wired, so it could not observe itself. AC-002/AC-003 assert the same behaviour through
  crafted payloads; what is unproven is the delivery path, not the hook.