# Feature Spec: project-scaffolding-parity

## Status

Done

## Problem

Projects initialized from this template do not end up with the same SDD structure. Real case: `proycto-cumbre` has `specs/README.md`, `specs/CLAUDE-SDD.md` and `specs/SDD-GUARDRAILS.md` (hand-written there), while a project initialized later (`lead-platform`) got none of them — nothing in this repo scaffolds those files. Additionally, the hook guardrails ship and get linked but are never registered in any `settings.json` (the merge is a manual, undocumented step, and `install.sh` does not even copy `settings.template.sh.json` to the central directory), so hooks like `project-init-check.sh` — which would have caught the missing scaffolding — never run.

## Goal

Any project initialized with `/project-init` gets the complete, identical `specs/` structure, and there is a supported, safe, one-command way to wire the shipped hooks into a project's `.claude/settings.json`.

## Non-goals

- Changing the safety model: installers still never write `settings.json` or `CLAUDE.md` directly; hook wiring stays an explicit opt-in command.
- Auto-wiring hooks at user (`~/.claude`) level — the shipped hook commands are project-relative (`${CLAUDE_PROJECT_DIR}/.claude/hooks/...`).
- Retrofitting existing projects (done manually per project).

## Users / Actors

- Template owner initializing new projects.
- `install.sh` / `link-project.sh` users on macOS/Linux, `install.ps1` / `link-project.ps1` on Windows.

## Current behavior

`/project-init` creates only `specs/CONSTITUTION.md` + `specs/features/`. `specs/_templates/` has no template for the specs README, the per-project guardrails instance, or the domain review triggers file. `install.sh` copies `settings.template.json` but not `settings.template.sh.json`. No script merges hook wiring into a project's settings; `/sdd` does not check whether the project is initialized.

## Desired behavior

- `specs/_templates/` ships `SPECS-README.md`, `SDD-GUARDRAILS.md` and `CLAUDE-SDD.md`; the `core` profile installs them.
- `/project-init` scaffolds all four `specs/` support files (CONSTITUTION + the three above), filling `CLAUDE-SDD.md` domain triggers from the interview.
- `scripts/wire-hooks.sh` / `scripts/wire-hooks.ps1` merge the hook wiring from the platform settings template into `<project>/.claude/settings.json` — idempotent, backup first, never touching `settings.local.json`.
- `install.sh` copies both settings templates and points at `wire-hooks`; `link-project` prints the same hint.
- `/sdd` starts with a bootstrap check: missing `specs/CONSTITUTION.md` → recommend `/project-init` first.

## Functional requirements

- FR-001: Three new templates in `specs/_templates/`, listed in the `core` profile.
- FR-002: `/project-init` creates/updates `specs/README.md`, `specs/SDD-GUARDRAILS.md`, `specs/CLAUDE-SDD.md` alongside `CONSTITUTION.md`, deriving domain review triggers from the interview.
- FR-003: `scripts/wire-hooks.sh` merges the `hooks` key from `settings.template.sh.json` into the project's `.claude/settings.json`: creates the file if absent, dedupes by command string, backs up before modifying, `--dry-run` supported, exits non-zero on missing template.
- FR-004: `scripts/wire-hooks.ps1` does the same on Windows from `settings.template.json`.
- FR-005: `install.sh` and `install.ps1` copy `settings.template.sh.json` as a root file and print a final note about `wire-hooks`; `link-project.sh` / `.ps1` print the same hint.
- FR-006: `/sdd` performs the bootstrap check before complexity detection.
- FR-007: `docs/INSTALL.md` documents hook wiring; README count markers stay consistent (`check-consistency.sh` green).

## Non-functional requirements

- Bash 3.2 compatible (macOS stock bash); python3 allowed (install.sh already requires it).
- Idempotent and safe to re-run, matching the repo's existing safety model.

## API / Interface changes

New commands: `scripts/wire-hooks.sh`, `scripts/wire-hooks.ps1`. Extended skills: `project-init`, `sdd`.

## Data model changes

None.

## Edge cases

- `.claude/settings.json` absent → created with only the `hooks` key.
- `.claude/settings.json` present with other keys → untouched except appending missing hook entries.
- Hook entry already wired (same command) → skipped, run is a no-op.
- `settings.local.json` → never read, never written.
- python3 missing → clean error message, exit 2 (same contract as check-consistency.sh).

## Acceptance criteria

- AC-001: `bash scripts/check-consistency.sh` exits 0 after the change (templates on disk ⇔ profiles.json ⇔ README counts).
- AC-002: Running `wire-hooks.sh --project-dir <tmp>` twice produces a settings.json with the template's hook entries exactly once, plus a `.bak-*` only for the first (mutating) run.
- AC-003: `wire-hooks.sh` on a project with a pre-existing unrelated settings.json preserves every existing key.
- AC-004: `install.sh --dry-run` lists `settings.template.sh.json` as a root file to copy.
- AC-005: `/project-init` (skill text) instructs creation of the four `specs/` files with no `TODO:` left in CONSTITUTION and CLAUDE-SDD after the interview.

## Test scenarios

- Unit: none (shell + docs).
- Integration: AC-002/AC-003 executed against a temp dir; AC-001/AC-004 executed directly.
- Manual: review of skill/doc text.

## Assumptions

- python3 present on dev machines (already required by install.sh and check-consistency.sh).

## Open questions

None blocking.
