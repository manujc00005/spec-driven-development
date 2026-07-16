# Tasks: graphify-first-class-integration

## Phase 1: Preparation

- [x] T001 - Create `scripts/graphify.test.sh` skeleton following the `check-consistency.test.sh` pattern: temp-sandbox helper, stub `graphify` executable factory (records invocations to a log file), assert helpers. Covers: AC-001 (infrastructure).

## Phase 2: Implementation

- [x] T002 - Rewrite `hooks/graphify-stale-reminder.sh`: canonical path resolution (`.graphify/GRAPH_REPORT.md` → root fallback), staleness check unchanged, auto-refresh branch (CLI on PATH + missing/stale + no fresh lock + `SDD_GRAPHIFY_AUTO` != 0 → lock file `.graphify/.update.lock` with 10-min expiry, detached `graphify update . --no-description --no-label`, "refreshing in background" systemMessage), exit 0 always, foreground <2s. Covers: AC-001, AC-002, AC-005.
- [x] T003 - Port T002 behavior to `hooks/graphify-stale-reminder.ps1` with full parity (`Start-Process` detached, same lock/env/messages). Covers: AC-001, AC-002, AC-005.
- [x] T004 - Add `SessionStart` Graphify hook entry to `settings.template.json` (powershell command) and `settings.template.sh.json` (bash command), matching existing entry conventions (timeout, statusMessage). Covers: AC-004.
- [x] T005 - Create `scripts/setup-graphify.sh` (modeled on `wire-hooks.sh`: `--project-dir`, `--yes`, `-h`; log/warn helpers): npm check (absent → guidance + exit 0), install `@sentropic/graphify` if CLI not on PATH (confirm unless `--yes`), `graphify detect . --scope committed` + `graphify update . --no-description --no-label` (surface CLI errors with guidance, non-fatal), idempotent `.gitignore` append of `.graphify/`, scaffold `docs/GRAPHIFY.md` + `docs/PROJECT_GRAPH.md` from `docs/_templates/` (central-dir first, repo fallback; never overwrite). Covers: AC-006, AC-007, AC-008.
- [x] T006 - Create `scripts/setup-graphify.ps1` with parity to T005. Covers: AC-006, AC-007, AC-008.
- [x] T007 - Update `skills/graphify-context/SKILL.md`: canonical path + fallback (replace "at project root"), graph-first doctrine as Step 1, CLI query preference (`review-context`, `affected-flows`, `tree`, `path`), heuristics labeled explicit fallback, auto-refresh awareness. Covers: AC-003, AC-010.
- [x] T008 - Update `skills/context-manager/SKILL.md`: same canonical path + graph-first reading-list derivation before any Glob/Grep sweep; heuristic scan as fallback only. Covers: AC-003, AC-010.
- [x] T009 - Update `skills/project-init/SKILL.md` (new Graphify adoption step recommending `setup-graphify`, default yes) and `skills/sdd-onboard/SKILL.md` Step 4b (offer `setup-graphify` when `.graphify/` absent; keep current scaffolding when present). Covers: AC-009.
- [x] T010 - Update docs: `docs/INSTALL.md` §Graphify (canonical path, setup script, auto-refresh, `SDD_GRAPHIFY_AUTO`), `hooks/README.md` (truthful wiring + new behavior), `docs/SDD-ORCHESTRATION.md` (graph-first strategy), `docs/_templates/GRAPHIFY.md` (setup script section, auto-refresh, 0.17.1 ID-collision caveat), `CLAUDE.md.example` (graph-first rule). Covers: AC-003, AC-008, AC-010.

## Phase 3: Tests

- [x] T011 - Implement hook test cases in `scripts/graphify.test.sh`: fresh→silent, absent→reminder, stale→warning, legacy-root fallback, stale+stub CLI→lock+invocation+fast exit, `SDD_GRAPHIFY_AUTO=0`→no invocation, expired lock ignored. Covers: AC-001, AC-002, AC-005.
- [x] T012 - Implement setup-script test cases in `scripts/graphify.test.sh`: double-run idempotency (single `.gitignore` line, docs not clobbered), no-npm guidance + exit 0, `--yes` non-interactive. Covers: AC-006, AC-007.
- [x] T013 - Add assertions to `scripts/check-consistency.sh`: hooks+skills reference `.graphify/GRAPH_REPORT.md`; no stale "at project root" claims; both settings templates contain the SessionStart graphify entry; docs AND `project-init`/`sdd-onboard` skills reference `setup-graphify`. Run full harness + `check-consistency.test.sh` + `wire-hooks.sh --dry-run` scratch verification. Covers: AC-003, AC-004, AC-009, AC-011.

## Phase 4: Review

- [x] T014 - Run `/spec-review`, `/qa-review`, and `/security-review` (hook spawns background process; script installs npm package) against the spec; fix findings. Covers: all ACs.
