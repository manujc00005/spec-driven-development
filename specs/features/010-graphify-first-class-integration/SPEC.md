# Feature Spec: graphify-first-class-integration

## Status

Done

## Problem

The Graphify integration shipped in feature 006 is de facto broken and underused:

1. **Wrong detection path.** Graphify writes its output to `.graphify/GRAPH_REPORT.md`, but every consumer looks for `GRAPH_REPORT.md` at the project root:
   - `skills/graphify-context/SKILL.md:24` ("at project root")
   - `skills/context-manager/SKILL.md:27` ("at project root")
   - `hooks/graphify-stale-reminder.sh:8` and `.ps1:5` (`GRAPH_REPORT="GRAPH_REPORT.md"`)
   - `docs/INSTALL.md:264` ("in a project's root")
   Meanwhile `docs/_templates/GRAPHIFY.md` and SPEC 006 (FR-2) correctly say `.graphify/GRAPH_REPORT.md`. Consequence: the hook always reports "not found" and both skills always fall back to heuristics, even when a real graph exists.
2. **Hook never runs.** `hooks/README.md:21` claims `graphify-stale-reminder` is "Wired by default", but neither `settings.template.json` nor `settings.template.sh.json` registers it, and `scripts/wire-hooks.{sh,ps1}` does not wire it either. Installed projects never execute it.
3. **No adoption path.** There is no script to help an existing SDD project install Graphify and generate its first graph; GRAPHIFY.md documents manual steps only. New projects (via `project-init` / `sdd-onboard`) are not guided to adopt it.
4. **No refresh automation.** The graph goes stale silently; the only mechanism is a reminder (which never fires, see #2). Nothing regenerates it.
5. **Weak token-saving doctrine.** Skills mention the graph as optional input, but nothing instructs Claude to *prefer* graph queries (`graphify review-context`, `affected-flows`, `tree`, `path`) over broad Glob/Grep/Read scans when the graph is available.

## Goal

Make Graphify a first-class, self-maintaining accelerator in SDD:

- Detection works against the real path (`.graphify/GRAPH_REPORT.md`), with root fallback for backwards compatibility.
- The stale-reminder/auto-update hook is actually wired in installed projects.
- One idempotent script (`setup-graphify`) lets any existing SDD project adopt Graphify; new projects are guided to run it by default during init/onboarding.
- The graph refreshes automatically via a non-blocking SessionStart strategy when Graphify is installed and the graph is missing or stale.
- SDD skills follow an explicit "graph-first" context strategy that reduces tokens: consult the graph/CLI before scanning the repository.

Doctrine preserved: Graphify remains an **accelerator, never a source of truth**; everything degrades gracefully and never blocks when Graphify is absent.

## Non-goals

- Bundling, vendoring, or forking `@sentropic/graphify` (it stays an external npm tool).
- Making Graphify mandatory for any SDD workflow step.
- Fixing upstream Graphify bugs (e.g. the node-ID basename collision seen in 0.17.1) — only documenting the known caveat.
- Regenerating the graph in CI.
- Auto-running `npm install -g` without explicit user consent inside hooks (installation only happens via the adoption script the user invokes).
- Changing the two-file model: `.graphify/GRAPH_REPORT.md` (raw, gitignored) vs `docs/PROJECT_GRAPH.md` (curated, versioned).

## Users / Actors

- Solo developers using the SDD framework in their projects (existing and new).
- Claude Code sessions executing SDD skills (`context-manager`, `graphify-context`, `spec-plan`, `spec-analyze`, `spec-review`) and hooks.
- The framework installer (`install.sh` / `install.ps1`) and profile system (`profiles.json`).

## Current behavior

- `graphify-stale-reminder.{sh,ps1}` checks `GRAPH_REPORT.md` at project root → always "not found" in real projects → permanent noise suggesting to run Graphify even when the graph exists. Additionally, the hook is not registered in either settings template, so in practice it never runs at all.
- `graphify-context` and `context-manager` skills instruct Claude to look for the report at project root → always miss it → always fall back to heuristic scanning, wasting tokens.
- No `setup-graphify` script exists. `docs/_templates/GRAPHIFY.md` documents manual installation.
- `sdd-onboard` Step 4b detects `.graphify/` (correct path) and scaffolds `docs/PROJECT_GRAPH.md`, but nothing offers to set Graphify up when absent. `project-init` does not mention Graphify.
- Nothing ever refreshes the graph automatically.

## Desired behavior

- All consumers resolve the report via a single canonical order: `.graphify/GRAPH_REPORT.md` first, then root `GRAPH_REPORT.md` as legacy fallback.
- The Graphify hook is wired on `SessionStart` in both settings templates and by `wire-hooks.{sh,ps1}`; it fires once per session.
- The hook, when the graph is missing/stale **and** the `graphify` CLI is installed, triggers a background, lock-protected `graphify update . --no-description --no-label` (auto-refresh). When the CLI is absent it only prints the existing reminder. It always exits 0 and never blocks the session.
- `scripts/setup-graphify.{sh,ps1}` performs adoption end-to-end: verify npm, install `@sentropic/graphify` (with consent prompt / `--yes` flag), run `graphify detect . --scope committed` + `graphify update . --no-description --no-label`, ensure `.graphify/` is gitignored, scaffold `docs/GRAPHIFY.md` and `docs/PROJECT_GRAPH.md` from templates if missing. Idempotent; safe to re-run.
- `install.sh` / `install.ps1` copy `setup-graphify.{sh,ps1}` into the target project (same mechanism as hooks), and `profiles.json` core profile lists it.
- `project-init` and `sdd-onboard` recommend (and offer to run) `setup-graphify` as a default step; onboarding of a project that already has `.graphify/` keeps current behavior.
- Skills adopt a graph-first token-saving strategy: when the report exists (and optionally the CLI is available), `context-manager` and `graphify-context` derive the reading list from graph queries (`review-context`, `affected-flows`, `tree`, `path`) instead of repo-wide scans; broad Glob/Grep is the fallback, not the default. `docs/SDD-ORCHESTRATION.md`, `docs/_templates/GRAPHIFY.md`, and `CLAUDE.md.example` document the strategy.

## Functional requirements

- FR-001: `hooks/graphify-stale-reminder.{sh,ps1}` MUST resolve the report as `.graphify/GRAPH_REPORT.md`, falling back to root `GRAPH_REPORT.md` if the former is absent.
- FR-002: `skills/graphify-context/SKILL.md` and `skills/context-manager/SKILL.md` MUST reference the same canonical resolution order (`.graphify/GRAPH_REPORT.md`, then root fallback).
- FR-003: `docs/INSTALL.md` and `hooks/README.md` MUST be corrected to state the canonical path and the actual wiring status.
- FR-004: Both settings templates (`settings.template.json`, `settings.template.sh.json`) MUST register the Graphify hook on `SessionStart`. No `wire-hooks` code change is expected: it merges the template's `hooks` key, so the new entry propagates automatically (verified via `wire-hooks.sh --dry-run`).
- FR-005: The hook MUST auto-refresh the graph when ALL of: `graphify` CLI on PATH, graph missing or >7 days older than newest source file, no concurrent refresh lock. Refresh runs in background (detached), writes a lock file under `.graphify/` (e.g. `.graphify/.update.lock`), and the hook itself exits 0 immediately in all cases.
- FR-006: Auto-refresh MUST be opt-out via environment variable `SDD_GRAPHIFY_AUTO=0` (hook falls back to reminder-only behavior).
- FR-007: `scripts/setup-graphify.sh` and `.ps1` MUST exist, be idempotent, and: check for npm (exit 0 with clear message if absent), install `@sentropic/graphify` globally after user confirmation (skippable with `--yes`; skip install if already on PATH), run `graphify detect . --scope committed` and `graphify update . --no-description --no-label`, append `.graphify/` to `.gitignore` if missing, and scaffold `docs/GRAPHIFY.md` + `docs/PROJECT_GRAPH.md` from `docs/_templates/` when missing.
- FR-008: `setup-graphify.{sh,ps1}` MUST be distributed following the `wire-hooks` precedent: shipped in `scripts/`, run from the framework checkout against a target project (`--project-dir`), and referenced from `install.sh` / `install.ps1` final guidance, `docs/INSTALL.md`, and `docs/_templates/GRAPHIFY.md`. (`profiles.json` has no `scripts` category; extending its schema is out of scope.)
- FR-009: `skills/project-init/SKILL.md` MUST include a Graphify adoption step (recommend/offer `setup-graphify`) for new projects; `skills/sdd-onboard/SKILL.md` Step 4b MUST offer `setup-graphify` when `.graphify/` is absent (keeping current scaffolding behavior when present).
- FR-010: `skills/context-manager/SKILL.md` and `skills/graphify-context/SKILL.md` MUST define the graph-first strategy: when the report exists, derive the bounded reading list from it (and from `graphify review-context` / `affected-flows` / `tree` / `path` when the CLI is available) BEFORE any repo-wide Glob/Grep; heuristic scanning is explicitly the fallback path only.
- FR-011: `docs/SDD-ORCHESTRATION.md`, `docs/_templates/GRAPHIFY.md`, and `CLAUDE.md.example` MUST document the graph-first token-saving strategy and the auto-refresh behavior.
- FR-012: All new/changed behavior MUST degrade gracefully: with no Graphify installed and no report present, every hook, script, and skill works exactly as today (reminder text only, heuristic fallback), exit code 0.

## Non-functional requirements

- Performance: the hook must complete in <2s in the foreground (staleness check only); the actual graph regeneration runs detached and never delays session start. `find` scans keep the existing `-maxdepth 5` bound.
- Security: hooks never execute network operations or package installs; only the user-invoked `setup-graphify` script installs software, and only after explicit confirmation (or `--yes`). No secrets touched. Lock file prevents concurrent CLI spawns.
- Observability: hook emits its existing one-line `systemMessage` JSON; auto-refresh emits a distinct message ("refreshing graph in background"). The setup script prints each step and a final summary.
- Maintainability: `.sh` and `.ps1` variants stay behaviorally identical (existing repo convention); consistency harness (`scripts/check-consistency.sh`) assertions updated to cover the new path and wiring.

## API / Interface changes

- New CLI surface: `scripts/setup-graphify.sh [--yes]` and `scripts/setup-graphify.ps1 [-Yes]`.
- New env var contract: `SDD_GRAPHIFY_AUTO=0` disables auto-refresh.
- Hook contract unchanged otherwise: JSON `systemMessage` on stdout, exit 0 always.
- New script surface accepting `--project-dir <path>` (default: current directory), matching the `wire-hooks` convention. `profiles.json` is unchanged (no `scripts` category exists; not added).

## Data model changes

None (no database). File-level artifacts only: `.graphify/.update.lock` (transient, gitignored via `.graphify/`).

## Edge cases

- Both `.graphify/GRAPH_REPORT.md` and root `GRAPH_REPORT.md` exist → `.graphify/` wins.
- `graphify` CLI not on PATH → reminder-only, no refresh attempt, exit 0.
- npm not installed when running `setup-graphify` → clear message, exit 0 (nothing broken).
- Stale/orphaned lock file (previous refresh crashed) → lock older than a threshold (e.g. 10 minutes) is ignored/replaced.
- Auto-refresh fails (CLI error, huge repo timeout) → failure is silent for the session (background), lock removed; next session retries.
- `SDD_GRAPHIFY_AUTO=0` set → reminder-only behavior.
- Re-running `setup-graphify` on an already-adopted project → no duplicate `.gitignore` lines, no template overwrites, graph refreshed.
- Project without git (`--scope committed` may fail) → script surfaces Graphify's error, exits non-fatally with guidance.
- macOS vs Linux `stat` differences → keep the existing dual `stat -c/-f` fallback in the hook.
- Windows: `.ps1` variants replicate all of the above including background start (`Start-Process`) and lock handling.
- Known upstream caveat: Graphify 0.17.1 node-ID collision on equal basenames — documented in GRAPHIFY.md troubleshooting, not fixed here.

## Acceptance criteria

- AC-001: With a fixture `.graphify/GRAPH_REPORT.md` (fresh), `graphify-stale-reminder.sh` produces no output and exits 0; with the fixture absent it prints the "not found" reminder; with the fixture >7 days older than a newer source file it prints the staleness warning. Same for `.ps1`.
- AC-002: With only a legacy root `GRAPH_REPORT.md`, the hook still detects it (fallback) and behaves as AC-001.
- AC-003: `grep` finds no remaining "at project root" / bare `GRAPH_REPORT.md`-at-root references in the two skills, `docs/INSTALL.md`, or `hooks/README.md`; all state `.graphify/GRAPH_REPORT.md` (+ fallback).
- AC-004: `settings.template.json` and `settings.template.sh.json` both contain a `SessionStart` entry invoking the Graphify hook; `wire-hooks.sh --dry-run` against a scratch project shows it being merged.
- AC-005: With a fake `graphify` executable on PATH and a stale graph, running the hook creates the lock, spawns the background refresh (fake CLI invoked with `update . --no-description --no-label`), and returns exit 0 in <2s. With `SDD_GRAPHIFY_AUTO=0` the fake CLI is NOT invoked.
- AC-006: Running `setup-graphify.sh --yes` twice in a scratch project (with a fake/real graphify) yields: `.graphify/` gitignored exactly once, `docs/GRAPHIFY.md` and `docs/PROJECT_GRAPH.md` present and not clobbered on second run, graph files generated, exit 0 both times.
- AC-007: `setup-graphify.sh` on a machine without npm prints an actionable message and exits 0.
- AC-008: `scripts/setup-graphify.sh` and `.ps1` exist and are executable; `install.sh` final guidance, `docs/INSTALL.md`, and `docs/_templates/GRAPHIFY.md` reference the script.
- AC-009: `project-init` and `sdd-onboard` SKILL.md files contain the Graphify adoption step (verifiable by grep for `setup-graphify`).
- AC-010: `context-manager` and `graphify-context` SKILL.md files instruct graph-first context derivation with heuristic scan explicitly labeled as fallback; `CLAUDE.md.example` and `docs/SDD-ORCHESTRATION.md` document the strategy.
- AC-011: `scripts/check-consistency.sh` passes with updated assertions covering the canonical path and hook wiring.

## Test scenarios

- Unit (hook, bash): fixture-driven tests exercising AC-001/002/005 (present-fresh, present-stale, absent, legacy-root, lock present, `SDD_GRAPHIFY_AUTO=0`, no CLI), following the `scripts/check-consistency.test.sh` pattern.
- Unit (script, bash): AC-006/007 in a temp scratch dir with a stubbed `graphify` on PATH.
- Integration: `install.sh` into a scratch project → assert files copied and settings wired (AC-004/008); run consistency harness (AC-011).
- E2E (manual, optional): real `npm install -g @sentropic/graphify` on this machine, run `setup-graphify.sh` against a real project, open a Claude session and observe the hook + skills reading `.graphify/GRAPH_REPORT.md`.
- Manual: PowerShell variants smoke-tested on Windows or via `pwsh` if available; otherwise reviewed for parity.

## Assumptions

- `SessionStart` is the best-fitting Claude Code hook event for auto-refresh: it fires once per session (not per edit), staleness >7 days makes per-session granularity sufficient, and a detached background run keeps it non-blocking. PostToolUse-per-edit was rejected as too hot/expensive for a whole-repo graph generation.
- `graphify update . --no-description --no-label` is the correct low-cost refresh command (matches GRAPHIFY.md) and does not require re-running `detect` once `.graphify/` exists.
- The graphify CLI writes only under `.graphify/` during `update`, so a background run cannot corrupt working-tree source files.
- `.ps1` hook parity can be verified by review if no Windows/pwsh runtime is available on this machine.
- Legacy root `GRAPH_REPORT.md` fallback is worth keeping for one release; no known project actually uses root placement (guinda-spa uses `.graphify/`), but the cost is one extra `-f` check.
- Testing on this machine uses a stubbed `graphify` executable; the real npm package is not required for CI-able tests.
- `wire-hooks.{sh,ps1}` merges the template `hooks` key generically, so wiring the new SessionStart entry requires only template edits (verified against `scripts/wire-hooks.sh` behavior).
- Distribution of `setup-graphify` follows the `wire-hooks` precedent (run from the framework checkout with `--project-dir`); `install.sh` does not copy repo scripts into projects and `profiles.json` has no `scripts` category — extending either is out of scope.
- This repo has no `specs/CONSTITUTION.md`; the governing conventions are the repo's own (sh/ps1 parity, hooks exit 0, consistency harness).

## Open questions

- **Deferred:** whether Graphify versions >0.17.1 fix the basename node-ID collision. Documented as a troubleshooting caveat in `docs/_templates/GRAPHIFY.md`; revalidate when upgrading the CLI. Not a dependency of this feature.
