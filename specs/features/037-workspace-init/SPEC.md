# Feature Spec: workspace-init

## Status

Estado: Merged
Blocked-by: —
Parent: —

> `Merged` 2026-08-23 — implemented, template scripts syntax-checked and the board template
> verified against a real six-project workspace (identical output to that workspace's tuned
> copy: 105 specs, same rows, same real-WIP figure). Becomes `Live` when `/sdd-workspace-init`
> runs end-to-end on a fresh workspace.
>
> **Deliberately absent artifacts:** no PLAN.md (the design was settled in the field: every
> template here is an extraction of machinery already built, debugged and in daily use in
> `lead-platform-workspace`; the only open decision — orchestrator vs. monolith rewrite of
> onboarding — is recorded below) and no DECISIONS.md (the three decisions fit in the SPEC and
> none supersedes an existing axis).

## Problem

`sdd-workspace-onboarding` builds the `.sdd-workspace/` map and — by design — writes nothing
inside child projects. Three gaps follow, all observed in a real workspace:

1. **The governance layer is invisible where sessions actually open.** Five child repos had zero
   references to `.sdd-workspace/`; a feature there recorded that the workspace's
   `INFRASTRUCTURE.md` "was not consulted" (its audit finding H-5).
2. **State was hand-maintained and went stale in days.** The root `CLAUDE.md` declared an active
   initiative whose legs had closed, under an identifier that existed nowhere else.
3. **Setup was manual assembly.** Board/drift/link scripts, workspace skills and hooks had to be
   built per workspace; nothing shipped them.

## Goal

One skill — `/sdd-workspace-init` — that takes a folder of related projects to fully-wired
Workspace SDD: detect → confirm → Graphify per project → map (delegating to onboarding) →
generated-state machinery → child linking → verification. Idempotent: re-run fills gaps, never
overwrites.

## Non-goals

- Rewriting `sdd-workspace-onboarding`. It becomes init's mapping phase and stays standalone —
  **decision D1**: orchestrator-over-phases beats a monolith because the map alone is still a
  valid use, and its token rules/stop conditions are already battle-tested.
- A merged cross-project graph (workspace decision D002 elsewhere: per-project graphs only).
- Auto-filling drift contracts — **decision D2**: contracts are workspace-specific; the template
  ships a declarative skeleton plus one worked example, and empty-CONTRACTS exits 0 with a
  message, because "no contracts declared" is a fact, not an error.
- Localized template output — **decision D3**: templates ship in English (framework language);
  a workspace may adapt its copies, and init never overwrites adapted copies.

## Acceptance criteria

- **AC-01** `skills/sdd-workspace-init/` ships SKILL.md + templates: `board.mjs`, `drift.mjs`,
  `link-workspace.mjs`, `HOW-TO-WORK.md`, `settings-hooks.json`, `workspace-skills/{sdd-status,
  sdd-workspace-link}/SKILL.md`. All `.mjs` pass `node --check`; the JSON parses.
- **AC-02** Template scripts hardcode no project list: `.sdd-workspace/workspace.json` if present,
  else marker-based auto-detection. `SDD_WS_ROOT` overrides root for testing.
- **AC-03** The board template, pointed at a real multi-project workspace, produces the same spec
  census, grouping and real-WIP figure as that workspace's hand-tuned copy.
- **AC-04** `profiles.json` lists the skill in the same profile as onboarding, satisfying the
  install integrity check (spec 034).
- **AC-05** Onboarding's SKILL.md cross-references init as the end-to-end flow.
- **AC-06** SKILL.md forbids: overwriting existing files, git operations, whole-project reads,
  `graph.json` loads, unprompted installs. Never-overwrite is stated per phase.
