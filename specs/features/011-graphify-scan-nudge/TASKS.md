# Tasks: graphify-scan-nudge

## Phase 1: Implementation

- [x] T001 - Create `hooks/graphify-scan-reminder.sh` (stdin consume, opt-out, report resolution, 30-min TTL marker, nudge, exit 0). Covers: AC-001, AC-002, AC-003.
- [x] T002 - Create `hooks/graphify-scan-reminder.ps1` with parity. Covers: AC-001, AC-002, AC-003.
- [x] T003 - Wire `PreToolUse` `Grep|Glob` entry in both settings templates; add to `profiles.json` core hooks; document in `hooks/README.md`; refresh README counts (`check-consistency.sh --fix`). Covers: AC-004.

## Phase 2: Tests

- [x] T004 - Extend `scripts/graphify.test.sh`: no-report silent, report→nudge, TTL throttle, TTL expiry re-nudge, opt-out. Run harness + wire-hooks dry-run. Covers: AC-001..004.
