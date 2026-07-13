# Feature Spec: Phase 4 — Multi-model orchestration (Fable / Opus / Sonnet)

## Status

In Review

## Problem

The SDD framework has no explicit multi-model delegation layer. Every phase of the workflow
(discovery, spec, plan, implement, QA) runs in the main session on whatever model the user
happens to have selected, so:

- Expensive reasoning models get used for mechanical work (boilerplate, tests, formatting).
- The main context gets polluted with long implementation diffs and file dumps.
- There is no documented policy for when to delegate to a subagent, which model to pick,
  or how to keep two subagents from editing the same files concurrently.
- The repo ships skills and hooks through `profiles.json` + `install.ps1`/`install.sh`, but
  has no concept of shipping **agents** (`.claude/agents/*.md`), even though Claude Code
  2.1.x supports project- and user-level agent definitions with `model:` and `tools:`
  frontmatter.

## Goal

Integrate a multi-model orchestration layer into the existing SDD system — not a parallel
system — where the main session (Fable when available) classifies tasks, keeps its context
clean, delegates deep reasoning to an Opus agent (`deep-reasoner`) and mechanical
implementation to a Sonnet agent (`fast-worker`), reviews the results, keeps the SDD
documents in sync, and validates against acceptance criteria. Ship it through the existing
source of truth (repo → `profiles.json` → installers → central dir → linked locations) so
both new and already-initialized projects receive it idempotently.

## Non-goals

- No third-party plugins or external tools.
- No replacement of existing skills, hooks, or workflow commands.
- No automatic modification of any real `CLAUDE.md` (user-level or central) — the
  installers' "never write CLAUDE.md" invariant is preserved.
- No stack-specific agents (the existing `~/.claude/agents/*` specialists stay untouched).
- No enforcement hooks for delegation (policy lives in the skill + agent instructions).

## Functional requirements

- FR-1: A `deep-reasoner` agent definition exists, pinned to Opus, restricted to read-only
  tools, returning a fixed structured report format, and never modifying code by default.
- FR-2: A `fast-worker` agent definition exists, pinned to Sonnet, with read/edit/execute
  tools, that only accepts well-delimited tasks and stops when it hits an undocumented
  architectural decision.
- FR-3: A `/sdd-orchestrate` skill exists that accepts a free-form goal, classifies it
  (Level 1 trivial / Level 2 normal / Level 3 high-risk / Level 4 investigation), and runs
  Discovery → Specify → Plan → Tasks → Implement → QA → Close with explicit delegation
  rules, reusing the existing `/spec-*` conventions and documents.
- FR-4: Level 4 (analysis/audit/investigation/review/design) requests never trigger
  implementation.
- FR-5: Parallel fast-worker delegations must never overlap on files, contracts,
  migrations, domain state, or high-conflict shared tests.
- FR-6: Model fallback is documented and non-blocking: Fable→Sonnet as orchestrator,
  Opus→Sonnet as deep-reasoner (with a note in DECISIONS.md that the preferred model was
  not used), Sonnet→nearest available; no invented model identifiers.
- FR-7: `profiles.json` declares agents per profile (`agents` / `plannedAgents`), with the
  same shipped-vs-planned integrity semantics as skills/hooks/templates.
- FR-8: `install.ps1` and `install.sh` install shipped agents into `<central>/agents/` with
  the existing copy-safely semantics (new / identical-skip / differs-skip / -Force+backup),
  and — only under the existing opt-in linking flag — copy agent files **per-file,
  additively** into `~/.claude/agents/` (never a junction/symlink, because that directory
  commonly contains user-authored agents).
- FR-9: `link-project.ps1` and `link-project.sh` copy agent files per-file, additively,
  into `<project>/.claude/agents/` with the same safety semantics.
- FR-10: `CLAUDE.md.example` gains an orchestration section wrapped in
  `<!-- SDD-ORCHESTRATION:START -->` / `<!-- SDD-ORCHESTRATION:END -->` markers so projects
  can merge/update it without losing customizations.
- FR-11: `docs/SDD-ORCHESTRATION.md` documents architecture, responsibilities,
  classification, cost control, install/update, usage examples, fallback, troubleshooting,
  and rollback.
- FR-12: `README.md` and `docs/INSTALL.md` are updated so the shipped inventory and the
  install/link flows stay accurate.

## Non-functional requirements

- Idempotent: running any installer twice produces zero changes the second time.
- Additive: nothing existing is deleted; no overwrite without `-Force`/`--force` + backup.
- Secrets: `.env` and `settings.local.json` are never copied (existing exclusion reused);
  no credentials in any new file.
- No destructive commands introduced in any script or documentation.
- Compatible with the existing junction/symlink layout (`~/.claude/skills` → central).
- Only verified Claude Code 2.1.207 capabilities are used (agent frontmatter `name`,
  `description`, `model`, `tools`; model aliases `opus`/`sonnet`; skills as slash commands).

## Edge cases

- `~/.claude/agents` does not exist → created, files copied.
- `~/.claude/agents` exists with user agents → only the two SDD agents are added; existing
  files untouched; same-name file that differs is skipped without `-Force`.
- A profile in `profiles.json` has no `agents` key → treated as empty, no error.
- A shipped agent declared in `profiles.json` but missing from `agents/` on disk → hard
  error (manifest integrity), consistent with skills/hooks/templates.
- Fable/Opus/Sonnet unavailable → documented fallback, never a hard block.
- Second `/sdd-orchestrate` run on the same feature → resumes via existing docs, does not
  duplicate SPEC/PLAN/TASKS.

## Acceptance criteria

AC-001 Orchestrator documented: classifies tasks and decides delegation (skill + docs + CLAUDE.md.example block).
AC-002 `deep-reasoner` agent exists, `model: opus`, fallback documented.
AC-003 `fast-worker` agent exists, `model: sonnet`, fallback documented.
AC-004 `deep-reasoner` does not modify code by default (read-only `tools:` + instruction).
AC-005 `fast-worker` receives delimited tasks and defers open architectural decisions.
AC-006 Reusable command `/sdd-orchestrate` exists as a skill (repo convention for commands).
AC-007 Flow supports analysis-only (Level 4) without implementing.
AC-008 Flow supports SPEC → PLAN → TASKS → IMPLEMENT → QA.
AC-009 New projects receive the integration (installer + link-project ship agents/skill/rules).
AC-010 Existing projects update without losing customizations (additive copy, skip-on-diff).
AC-011 Installation is idempotent (verified by double run).
AC-012 CLAUDE.md is never wholly replaced (installers still never write CLAUDE.md; example uses managed markers).
AC-013 No secrets or local settings copied (existing exclusions still active; agents path additive).
AC-014 No destructive commands introduced.
AC-015 Fable has a documented fallback.
AC-016 Model selection validated against installed version (2.1.207; aliases verified against live session/agent list).
AC-017 Agents and command are recognized by Claude Code (frontmatter matches the 9 already-recognized user agents; skill matches existing recognized skills).
AC-018 Reproducible verifications exist (documented validation commands, runnable on temp dirs).
AC-019 Documentation covers install, usage, fallback, rollback.
AC-020 No commits, no push.
AC-021 Compatible with the existing SDD (no existing file semantics changed).
AC-022 No second source of truth (everything ships from this repo through profiles.json).
AC-023 Parallel tasks cannot modify overlapping files (explicit rule in skill + fast-worker).
AC-024 QA validates the acceptance criteria with evidence (final report).

## Assumptions

- Claude Code agent frontmatter `model:` accepts the aliases `opus` and `sonnet` (verified:
  the live Agent tool exposes exactly these aliases, and agent definitions are documented
  as the source of each agent's model). Full IDs are avoided so the aliases track model
  upgrades.
- Fable availability is account-level and cannot be toggled from a script; fallback is
  therefore documented operational guidance, not code.

## Dependencies

- profiles.json v0.3.0 schema (extended, backward-compatible).
- Existing installer safety utilities (exclusion patterns, copy-safely, backups).

## Risks

- R-1: A future Claude Code version changes agent frontmatter → aliases chosen over IDs to
  minimize this; documented in troubleshooting.
- R-2: Per-file agent copy (vs junction) means agent updates require re-running the
  installer → documented explicitly in INSTALL and SDD-ORCHESTRATION docs.
- R-3: Central dirs installed before this phase lack `agents/` until the installer is
  re-run → the skill degrades gracefully (falls back to general-purpose subagents with
  explicit model override) and documents the fix.

## Expected test cases

- Installer double-run to a fresh temp central dir: second run prints no `(new)` lines.
- `--dry-run` writes nothing.
- Temp central dir contains `agents/deep-reasoner.md` + `agents/fast-worker.md`.
- A planted `settings.local.json` in a source tree is never copied.
- Per-file agent copy into a fake `~/.claude/agents` with a pre-existing user agent leaves
  that agent untouched.
- `bash -n install.sh` and PowerShell parser accept both installers.
- Frontmatter of both agents and the new skill parses as YAML with required keys.
