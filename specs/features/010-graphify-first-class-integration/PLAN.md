# Implementation Plan: graphify-first-class-integration

## Summary

Repair and complete the Graphify integration: point all consumers at the canonical `.graphify/GRAPH_REPORT.md` path (with legacy root fallback), actually wire the hook into the settings templates, upgrade the hook from reminder-only to non-blocking background auto-refresh, add an idempotent `setup-graphify` adoption script (sh + ps1), hook adoption into `project-init`/`sdd-onboard`, and codify a graph-first token-saving strategy in the context skills and docs. Everything degrades gracefully when Graphify is absent.

## Related spec

`specs/features/010-graphify-first-class-integration/SPEC.md`

## Impacted areas

- `hooks/graphify-stale-reminder.sh` / `.ps1` — path fix + auto-refresh + lock + opt-out (FR-001, FR-005, FR-006, FR-012)
- `settings.template.json` / `settings.template.sh.json` — new `SessionStart` entry (FR-004)
- `scripts/setup-graphify.sh` / `.ps1` — new (FR-007, FR-008)
- `skills/graphify-context/SKILL.md`, `skills/context-manager/SKILL.md` — path + graph-first strategy (FR-002, FR-010)
- `skills/project-init/SKILL.md`, `skills/sdd-onboard/SKILL.md` — adoption step (FR-009)
- `docs/INSTALL.md`, `hooks/README.md`, `docs/SDD-ORCHESTRATION.md`, `docs/_templates/GRAPHIFY.md`, `CLAUDE.md.example` — doc corrections + strategy (FR-003, FR-011)
- `scripts/graphify.test.sh` — new fixture-driven tests for hook + setup script
- `scripts/check-consistency.sh` — new assertions (AC-011)

## Proposed approach

1. **Canonical path resolution** — a small shared convention (duplicated in each hook variant, as the repo does today): `RESOLVED=.graphify/GRAPH_REPORT.md` if present, else root `GRAPH_REPORT.md`, else absent. Skills describe the identical order in prose.
2. **Hook upgrade (keep the name `graphify-stale-reminder`)** — same file, extended behavior so profiles.json and README references stay valid:
   - Resolve report path (step 1). Fresh → silent exit 0.
   - Missing/stale + `graphify` NOT on PATH (or `SDD_GRAPHIFY_AUTO=0`) → current reminder message, exit 0.
   - Missing/stale + CLI available + no fresh lock → write `.graphify/.update.lock` (ignore locks >10 min old), spawn `graphify update . --no-description --no-label` detached (`nohup ... & disown` / `Start-Process`), print "refreshing in background" systemMessage, exit 0 immediately. Background wrapper removes the lock on completion regardless of outcome.
3. **Settings templates** — add a `SessionStart` hook entry alongside `project-init-check` in both templates (ps1 command in `settings.template.json`, sh command in `settings.template.sh.json`, matching existing conventions). `wire-hooks` propagates it with no code change.
4. **`setup-graphify.{sh,ps1}`** — modeled on `wire-hooks` structure (`--project-dir`, `--yes`/`-Yes`, `--dry-run` optional, log/warn helpers, `set -euo pipefail`): npm check → install `@sentropic/graphify` if not on PATH (confirm unless `--yes`) → `graphify detect . --scope committed` → `graphify update . --no-description --no-label` → ensure `.graphify/` in `.gitignore` (exact-line idempotent append) → copy `docs/_templates/GRAPHIFY.md` → `docs/GRAPHIFY.md` and `PROJECT_GRAPH.md` → `docs/PROJECT_GRAPH.md` if missing. Template source resolves like wire-hooks: `$CENTRAL_DIR` first, repo fallback.
5. **Skills** — `graphify-context` and `context-manager`: replace "at project root" with the resolution order; restructure so the graph path is Step 1 (graph-first): when the report exists, build the reading list from it, and when the CLI is available prefer `graphify review-context <file>` / `affected-flows <file>` / `tree` / `path` over Glob/Grep sweeps; heuristics become the explicit fallback branch. `project-init` gains a "Graphify adoption (default: yes)" step; `sdd-onboard` Step 4b gains the "offer setup-graphify when `.graphify/` absent" branch.
6. **Docs** — fix `docs/INSTALL.md` §Graphify and `hooks/README.md` (path + real wiring + auto-refresh + `SDD_GRAPHIFY_AUTO`); update `SDD-ORCHESTRATION.md`, `GRAPHIFY.md` template (setup script section + auto-refresh + 0.17.1 ID-collision caveat), `CLAUDE.md.example` (graph-first rule).
7. **Tests** — `scripts/graphify.test.sh` following the `check-consistency.test.sh` pattern: temp sandbox per case, stub `graphify` executable prepended to PATH, cases for AC-001/002/005/006/007. Add harness assertions to `check-consistency.sh` (canonical path present in hook+skills, SessionStart wiring present in both templates, setup script referenced in docs).

## Alternatives considered

- **PostToolUse (Write|Edit) auto-refresh** — rejected: fires dozens of times per session for a whole-repo graph generation; staleness threshold is 7 days, so per-session granularity (SessionStart) is sufficient and far cheaper.
- **git post-commit hook for refresh** — rejected: SDD ships Claude Code hooks, not git hooks; installing git hooks into user repos is invasive and outside the framework's contract.
- **New hook name (`graphify-auto-update`)** — rejected: renaming breaks `profiles.json`, README tables, and installed copies; extending the existing hook keeps every reference valid.
- **Copying `setup-graphify` into each project / adding a `scripts` category to `profiles.json`** — rejected: no precedent (`wire-hooks` runs from the checkout), schema change ripples into both installers; run-from-checkout gets updates for free.
- **Auto-installing the npm package from the hook** — rejected: hooks must never perform network installs (security + surprise); installation stays in the user-invoked script with confirmation.
- **Dropping the legacy root fallback** — rejected for now: one `-f` check buys backwards compatibility for any pre-006 layout.

## Dependencies

- `@sentropic/graphify` (external npm, user-installed; stubbed in tests — not required for CI).
- `python3` (already required by installers; only if setup script needs JSON edits — current design does not).
- `pwsh` optional for ps1 smoke tests; otherwise parity by review (existing repo convention).

## Risks

- **Detached background spawn from a Claude Code hook** may behave differently across shells/platforms (zombie processes, session teardown killing children). Mitigation: `nohup`+`disown` with output to `/dev/null`, lock with age-based expiry so a killed refresh self-heals next session.
- **Lock races** (two sessions starting simultaneously): acceptable worst case is one redundant refresh; lock check keeps it rare.
- **Stub-based tests can't catch real CLI quirks** (e.g. `detect` failing without git). Mitigation: script surfaces CLI stderr and exits with guidance; manual E2E documented as optional.
- **ps1 parity drift** — no Windows runner here. Mitigation: line-by-line parity review + harness assertions that check both variants for the canonical path.
- **Skill prose changes are unenforceable at runtime** (graph-first is doctrine, not code). Mitigation: make the instruction imperative and place it as Step 1; harness asserts the key phrases exist.

## Test strategy

- **Unit (hook)**: `scripts/graphify.test.sh` sandbox cases — fresh report silent; absent → reminder; stale → warning; legacy root fallback; stale+stub CLI → lock created, stub invoked with `update . --no-description --no-label`, exit <2s; `SDD_GRAPHIFY_AUTO=0` → stub NOT invoked; stale lock (>10 min) ignored.
- **Unit (setup script)**: sandbox with stub graphify — double run idempotent (single `.gitignore` line, templates not clobbered); no-npm PATH → message + exit 0; `--yes` skips prompt.
- **Integration**: `wire-hooks.sh --dry-run` on a scratch project shows the SessionStart merge; `check-consistency.sh` passes with new assertions.
- **Manual**: optional real-npm E2E (documented); ps1 parity review.
- **Regression**: full existing `check-consistency.sh` + `check-consistency.test.sh` suite still green.

## Rollback strategy

Pure additive/file-level change in the framework repo: revert the commit(s). Installed projects: re-run `wire-hooks` from a reverted checkout is additive (old entry would linger — remove the `SessionStart` graphify entry manually or restore the timestamped `settings.json.bak-*` the script creates). `SDD_GRAPHIFY_AUTO=0` provides an immediate kill-switch for auto-refresh without any rollback. Setup script artifacts (`.graphify/`, docs) are inert files; deleting them restores pre-adoption state.

## PLAN verification checklist

- [x] The plan covers all acceptance criteria.
- [x] The plan avoids behavior outside the spec.
- [x] Risks are documented.
- [x] Test strategy is documented.
- [x] Rollback strategy is documented.
- [x] SPEC.md status has been updated to `Ready`.
