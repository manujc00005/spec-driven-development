# Implementation Plan: project-scaffolding-parity

## Summary

Ship the three missing per-project `specs/` files as templates, teach `/project-init` to scaffold them, add an explicit opt-in hook-wiring script pair, copy the sh settings template in the installers, and add a bootstrap check to `/sdd`.

## Related spec

`specs/features/009-project-scaffolding-parity/SPEC.md`

## Impacted areas

`specs/_templates/` (+3 files), `profiles.json` (core.templates), `skills/project-init/SKILL.md`, `skills/sdd/SKILL.md`, `scripts/` (+2 files), `install.sh`, `install.ps1`, `link-project.sh`, `link-project.ps1`, `docs/INSTALL.md`, `README.md` (count markers via `check-consistency.sh --fix`).

## Proposed approach

1. Author the three templates in English with `TODO:` markers for project-specific content (same convention as `CONSTITUTION.md`). `SDD-GUARDRAILS.md` is a generic instance of the `sdd-guardrails` skill doctrine (state machine, source-of-truth matrix, active plan rule, consistency gate, naming hygiene, units & money safety, deployment coupling, scope change protocol, pre-implementation checklist) without project-specific case references.
2. Register them in the `core` profile so both installers ship them.
3. Extend `/project-init` Step 1/3/Output to scaffold and fill all four files.
4. `wire-hooks.sh`: bash 3.2 arg parsing + python3 JSON merge (same dependency posture as `install.sh`); `wire-hooks.ps1`: native PowerShell JSON. Merge = for each hook event, append template matcher-groups whose command strings are not already present anywhere in that event; write only on change, with timestamped backup.
5. Installers: add `settings.template.sh.json` to the root-file copy loop; add a final NOTE pointing at `wire-hooks`; same hint at the end of `link-project`.
6. `/sdd`: bootstrap check section before complexity detection.
7. `check-consistency.sh --fix` to update README count markers; run its test harness.

## Alternatives considered

- **Installers merging `settings.json` directly**: rejected — violates the repo's documented safety model ("never writes settings.json"); an explicit, separate command keeps the model intact.
- **Wiring hooks at `~/.claude/settings.json` (user level)**: rejected — shipped hook commands are `${CLAUDE_PROJECT_DIR}`-relative and belong with per-project linking.
- **Making `project-init-check.sh` scaffold files itself**: rejected — hooks should observe and warn, not write project files.

## Dependencies

python3 (already required), PowerShell 5+ for the `.ps1` counterpart.

## Risks

- JSON merge corrupting a user's settings → mitigated: backup before write, dedupe-only additive merge, `--dry-run`, never `settings.local.json`.
- README count drift → mitigated by running the CI checker locally.
- Template content drifting from the `sdd-guardrails` skill doctrine over time → accepted; noted inside the template header.

## Test strategy

Execute AC-002/AC-003 against a temp project dir (twice-run idempotency, preservation of unrelated keys); `check-consistency.sh` + its test harness; `install.sh --dry-run` inspection.

## Rollback strategy

Revert the commits; no state outside the repo except optional `.bak-*` files created next to user settings by explicit runs.
