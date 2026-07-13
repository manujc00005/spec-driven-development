# Decisions: Phase 4 — Multi-model orchestration

## D001 — Agents are delivered by per-file copy, never by junction/symlink

**Status:** Active

`~/.claude/agents` on the reference machine is a real directory containing 9 user-authored
agents (angular, api-design, database, gdpr-spain, java-spring, nextjs-react, security,
seo, testing). Junctioning it to `<central>/agents` (the skills/hooks pattern) would hide
those agents behind a `.bak` move. Agent files are therefore copied file-by-file,
additively, with the installer's standard skip-on-diff / `-Force`+backup semantics — into
`~/.claude/agents` (only under the existing `-LinkUserClaude`/`--link-user-claude` opt-in)
and into `<project>/.claude/agents` (via link-project). Trade-off accepted: agent updates
require re-running the installer instead of propagating instantly through a link.

## D002 — `/sdd-orchestrate` is a skill, not a `.claude/commands` file

**Status:** Active

Every slash command in this repo is a skill (`skills/<name>/SKILL.md`); no
`.claude/commands/` convention exists here. Introducing one would create a second
distribution channel (violates AC-022). The command ships as a core-profile skill.

## D003 — Orchestration rules ship in `CLAUDE.md.example` under managed markers; installers still never write CLAUDE.md

**Status:** Active

The installers' documented safety invariant is "never writes CLAUDE.md or settings.json
directly". Auto-editing existing CLAUDE.md files (even between markers) would break that
invariant and risk corrupting user customizations. The orchestration section is added to
`CLAUDE.md.example` wrapped in `<!-- SDD-ORCHESTRATION:START -->` /
`<!-- SDD-ORCHESTRATION:END -->` so a human (or an explicit prompt) can merge or refresh
exactly that block into any real CLAUDE.md without touching the rest. No prior managed-
block convention existed in the repo; these markers are the first and are documented.

## D004 — Model aliases (`opus`, `sonnet`) instead of dated model IDs

**Status:** Active

Verified on Claude Code 2.1.207: the Agent tool exposes model aliases `sonnet`, `opus`,
`haiku`, `fable`, and agent frontmatter is the documented source of an agent's model.
Dated IDs (e.g. `claude-opus-4-8`) would pin agents to a snapshot and rot on upgrade;
aliases track the account's current model for each tier. Fable is available on this
account (this integration itself ran on `claude-fable-5`).

## D005 — Fallback is operational guidance + skill logic, not installer code

**Status:** Active

Model availability is an account/runtime property that a file-copy installer cannot probe
or toggle. The fallback matrix (Fable→Sonnet orchestrator; Opus→Sonnet deep-reasoner with
a DECISIONS.md note; Sonnet→nearest available; missing agents→general-purpose subagent +
explicit model override) lives in `skills/sdd-orchestrate/SKILL.md` and
`docs/SDD-ORCHESTRATION.md`, where the orchestrating model can actually act on it.

## D006 — `deep-reasoner` tools limited to `Read, Grep, Glob` (no Bash)

**Status:** Active

Bash would allow writes through shell commands, defeating "does not modify code by
default". Cost: the deep-reasoner cannot run tests or `git log` itself; it must reason
from files, and the orchestrator runs any commands whose output the analysis needs.
Conservative choice per the integration brief.

## D007 — Profiles without an `agents` key stay valid (backward compatibility)

**Status:** Active

Only the `core` profile declares `agents`. Both installers treat a missing `agents` /
`plannedAgents` key as an empty list, so pre-Phase-4 forks or trimmed copies of
`profiles.json` keep installing without errors. The shipped-item integrity check (hard
error if a declared agent file is missing from `agents/`) matches skills/hooks/templates.

## D008 — No enforcement hook for delegation in this phase

**Status:** Active

The brief allows policy via instructions; a PreToolUse hook policing Agent-tool calls
would be novel machinery with false-positive risk and was not required by any AC.
Delegation discipline lives in the skill, the agent instructions, and the CLAUDE.md
block. Revisit only if drift is observed in practice.

## D009 — Phase 4 held at In Review pending live agent-recognition check (AC-017)

**Status:** Superseded (by D010 — the live check passed on 2026-07-13)

`/spec-review` returned PASS and `/qa-review` returned PASS on structural evidence
(installer invariants, agent frontmatter/tools, profiles.json semantics, link-project
additive copy, CLAUDE.md.example markers, secret scan, destructive-command grep — all
clean). AC-017 (agents and command recognized by Claude Code) is **PASS structural /
NOT RUN live**: the two agents were never deployed to the real `~/.claude/agents` and no
new Claude Code session has confirmed live discovery. Per the SDD lifecycle, SPEC.md is
therefore deliberately kept at **In Review**, not advanced to Done, until the live check
in TASKS.md ("Pending before Done") passes. This decision records why Done was withheld
even though every runnable verification passed, so a future session does not mistake the
In Review status for unfinished implementation.

Note on commit hygiene (informational, not a decision to act on): Phase 4 was committed
together with Phase 3 in `c8cfa37` (message "phase 3") and pushed; the maintainer
accepted this mixed, already-published commit rather than rewrite history. No code impact.

## D010 — Phase 4 closed: AC-017 live check passed

**Status:** Active

**Date:** 2026-07-13

The gate recorded in D009 was cleared. The user ran the real deploy (`install.ps1`, then
`install.ps1 -LinkUserClaude`) and confirmed in a **fresh Claude Code session** that:

- `deep-reasoner` is available and uses `model: opus`,
- `fast-worker` is available and uses `model: sonnet`,
- `/sdd-orchestrate` is available.

AC-017 is therefore **PASS live** (previously PASS structural only — that distinction was
maintained honestly from the Phase 4 close through the Phase 5 audit until this
verification). With the last open AC verified, SPEC.md advanced `In Review → Done`. The
reproducible live-check procedure is retained in `TASKS.md` for re-verification after
future `git pull` + reinstall cycles. D009 is superseded by this decision.
