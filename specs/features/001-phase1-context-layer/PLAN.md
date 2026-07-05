# Plan: Phase 1 — Context layer + Graphify integration

## Approach

Seven independent deliverables, all additive. Three are templates (docs/_templates/), three are
skills (skills/<name>/SKILL.md), one is a hook pair (.ps1 + .sh). No dependencies between them —
can be implemented in any order.

## Files to CREATE

| File | Purpose | AC |
|---|---|---|
| `docs/_templates/PROJECT_CONTEXT.md` | Template for project purpose, bounded contexts, service map | AC-001 |
| `docs/_templates/TECH_STACK.md` | Template for stack versions, build tool, commands | AC-001 |
| `docs/_templates/ARCHITECTURE.md` | Template for layers, services, boundaries, diagram | AC-001 |
| `skills/context-manager/SKILL.md` | Skill: decide minimal reading list before implementing | AC-002 |
| `skills/graphify-context/SKILL.md` | Skill: interpret GRAPH_REPORT.md, impact analysis, graceful degradation | AC-003 |
| `skills/sdd-onboard/SKILL.md` | Skill: onboard existing project, scaffold context docs | AC-004 |
| `hooks/graphify-stale-reminder.ps1` | Hook: warn if GRAPH_REPORT.md is stale (Windows) | AC-005 |
| `hooks/graphify-stale-reminder.sh` | Hook: warn if GRAPH_REPORT.md is stale (macOS/Linux) | AC-005, AC-007 |

## Files NOT touched

- Existing 33 skills (no internal changes).
- `C:\ProgramData\ClaudeConfig\*`.
- `settings.local.json` (any location).
- `install.ps1` / `install.sh` (profile flag is Phase 2).
- `settings.template.json` (hook wiring deferred to Phase 2).
- Application code in any target project.

## Design decisions

- **Templates live in `docs/_templates/`** (project context docs), separate from `specs/_templates/`
  (SDD lifecycle docs). When `sdd-onboard` scaffolds a project, it copies from `docs/_templates/`.
- **Skills are guidance-only** — they instruct Claude what to read and in what order, but don't execute
  external tools or modify files beyond `docs/` and `specs/`.
- **Graphify is optional everywhere** — every reference checks for file existence first.
- **Hook is reminder-only** (exit 0) — never blocks.
- **Maven is the default build tool** in all templates and detection logic; Gradle is secondary fallback.

## Verification

- `bash -n` on both `.sh` files.
- Secret scan on all new files.
- `git status` + `git diff` for author review.
