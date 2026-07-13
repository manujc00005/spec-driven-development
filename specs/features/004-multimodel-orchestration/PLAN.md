# Implementation Plan: Phase 4 — Multi-model orchestration

## Status

Active

## Strategy

Ship the orchestration layer through the exact channels the repo already uses:

1. **Agents become a first-class shipped artifact type**, parallel to skills/hooks/templates:
   - New top-level `agents/` directory in the repo (source of truth).
   - `profiles.json` gains `agents` / `plannedAgents` arrays (core profile ships
     `deep-reasoner`, `fast-worker`; other profiles omit the key — installers tolerate that).
   - Both installers copy shipped agents to `<central>/agents/` with the existing
     new/identical/differs/-Force semantics and the existing shipped-item integrity check.
2. **Agent delivery to consumers is per-file copy, never a link.** `~/.claude/agents` and
   `<project>/.claude/agents` commonly contain user/project-authored agents (this machine
   has 9); a junction would hide them. Copy semantics: create dir if missing, add missing
   files, skip identical, skip differing without force, back up + overwrite with force.
   - `install.ps1` / `install.sh`: only under the existing `-LinkUserClaude` /
     `--link-user-claude` opt-in (that flag already means "touch my personal config").
   - `link-project.ps1` / `link-project.sh`: always (that script's whole purpose is wiring
     one project), same safety semantics.
3. **The orchestration command is a skill** (`skills/sdd-orchestrate/SKILL.md`), because in
   this repo slash commands are skills — there is no `.claude/commands/` convention.
4. **Rules ship via `CLAUDE.md.example`** inside `<!-- SDD-ORCHESTRATION:START/END -->`
   markers. Installers keep never writing a real CLAUDE.md; projects merge the block
   manually (documented), which preserves AC-012 by construction.
5. **Documentation**: new `docs/SDD-ORCHESTRATION.md`; surgical updates to `README.md`
   (command list, repo structure, orchestration section) and `docs/INSTALL.md` (agents in
   the install/link flows, verification, rollback).

## Model compatibility (verified on this machine)

- Claude Code `2.1.207`.
- Live model: `claude-fable-5` (Fable available on this account).
- Valid subagent model aliases: `opus`, `sonnet`, `haiku`, `fable` (exposed by the live
  Agent tool; agent frontmatter is the documented source of an agent's model).
- Existing recognized agents at `~/.claude/agents/*.md` use `name:` + `description:`
  frontmatter — `model:` and `tools:` are additional supported keys.
- Frontmatter uses **aliases** (`opus`, `sonnet`), not dated IDs, so agents track upgrades.

## Fallback design (documentation + skill logic, not scripts)

| Missing | Behavior |
|---|---|
| Fable | Run the main session on Sonnet (`claude --model sonnet` or `/model`); agents unchanged. |
| Opus | Delegate deep-reasoning to `fast-worker`-class Sonnet in a separate context via Agent-tool `model` override; record in DECISIONS.md that the preferred model was not used. |
| Sonnet | Use the nearest available model via Agent-tool `model` override; never invent IDs. |
| `deep-reasoner`/`fast-worker` not installed | Skill falls back to general-purpose subagents with explicit model override and the same delegation brief. |

## Files

Create:
- `agents/deep-reasoner.md` — Opus analyst, read-only tools, fixed report format.
- `agents/fast-worker.md` — Sonnet implementer, delimited tasks, fixed report format.
- `agents/README.md` — what ships here, copy-not-link rationale, customization.
- `skills/sdd-orchestrate/SKILL.md` — classification + phases + delegation policy.
- `docs/SDD-ORCHESTRATION.md` — full documentation.
- `specs/features/004-multimodel-orchestration/*` — this feature.

Modify:
- `profiles.json` — version bump, `$comment` update, core `agents`/`plannedAgents`,
  core skill `sdd-orchestrate`.
- `install.ps1`, `install.sh` — agent resolution, integrity check, central copy,
  per-file user copy under the opt-in flag.
- `link-project.ps1`, `link-project.sh` — per-file agent copy into the project.
- `CLAUDE.md.example` — managed orchestration block.
- `README.md`, `docs/INSTALL.md` — inventory and flow updates.

## Compatibility & idempotence

- All new installer logic reuses the existing patterns (hash/cmp compare, skip-on-diff,
  timestamped backups, dry-run branch on every write) — a second run is a no-op.
- Profiles without `agents` keys resolve to empty sets (PowerShell: property may not
  exist; bash/python: `pdef.get("agents", [])`), so old forks of profiles.json keep
  working.
- The `settings.local.json` exclusion applies to every new copy path (agents are copied
  through the same guarded helpers or equivalent per-file logic that never touches
  excluded names).

## Test strategy

- Syntax: `bash -n install.sh`; PowerShell `Parser::ParseFile` on both .ps1 scripts.
- Frontmatter: YAML parse of both agents + new skill via python3.
- Behavior (temp dirs under the session scratchpad, never real config):
  1. Install to fresh temp central dir → agents/skill present.
  2. Re-run → zero `(new)`/`(overwritten)` lines (idempotence).
  3. `--dry-run` to another fresh dir → dir not created.
  4. Fake claude-home with a pre-existing user agent → user agent untouched, two SDD
     agents added; re-run → no-op.
  5. link-project against a temp project → agents copied, settings.local.json untouched.

## Rollback

Delete `agents/`, `skills/sdd-orchestrate/`, `docs/SDD-ORCHESTRATION.md`, revert the five
modified files (git checkout), and remove `deep-reasoner.md`/`fast-worker.md` from any
`agents/` directory they were copied into. No other state exists.
