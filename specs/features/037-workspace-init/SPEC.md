# Feature Spec: workspace-init

## Status

Estado: Merged
Blocked-by: —
Parent: —

> `Merged` 2026-08-23, **and it should not have been on that date**. Corrected 2026-08-24 —
> see *Shipped half-integrated* below. Becomes `Live` when `/sdd-workspace-init` runs end-to-end
> on a fresh workspace.
>
> Verified at close: template scripts syntax-checked, and the board template run against a real
> six-project workspace producing output identical to that workspace's tuned copy (105 specs,
> same rows, same real-WIP figure).

### Shipped half-integrated — recorded 2026-08-24

This spec was marked `Merged` while `scripts/check-consistency.sh` was **red**, which its own
definition forbids: `Merged` requires the gates to have passed. They were never run before the
commit. A follow-up commit (`fecc644`) had to restore the baseline, fixing **nine errors** in this
skill's own `SKILL.md` — none of them parser bugs:

- `outputs` was a YAML block list where 71 of 72 skills use a flow list, and one item contained a
  comma inside braces that a flow list would have split.
- Six required contract keys were missing: `writes_code`, `writes_specs`, `analysis_only`,
  `primary_agent`, `profile_scope`, `provider_specific`.
- `composes` is not in the schema.
- `category: workspace-lifecycle` is not in the enum (its sibling uses `lifecycle`).
- The description ran 662 characters against a 400 cap.

**The cost was not cosmetic.** `check-consistency.sh` is entry-gate condition 6 of
`/sdd-orchestrate`, so while it was red **no `--autonomous` run could start anywhere in this
repo**, for any spec.

**Root cause: AC-01 was the wrong criterion.** It verified that the *templates* parsed
(`node --check`, JSON valid) and said nothing about the skill's own contract — so it passed while
the artifact it shipped was invalid. A criterion that green-lights a broken deliverable is a
defect in the criterion, not an oversight in the execution. AC-01 is corrected below and AC-07
added; the durable fix is the pre-push gate (T008) so the suite cannot be skipped by forgetting.
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
  sdd-workspace-link}/SKILL.md`. All `.mjs` pass `node --check`; the JSON parses. **And
  `bash scripts/check-consistency.sh` exits 0** — the templates parsing says nothing about whether
  the skill itself satisfies the contract schema, which is precisely how this shipped broken.
- **AC-02** Template scripts hardcode no project list: `.sdd-workspace/workspace.json` if present,
  else marker-based auto-detection. `SDD_WS_ROOT` overrides root for testing.
- **AC-03** The board template, pointed at a real multi-project workspace, produces the same spec
  census, grouping and real-WIP figure as that workspace's hand-tuned copy.
- **AC-04** `profiles.json` lists the skill in the same profile as onboarding, satisfying the
  install integrity check (spec 034).
- **AC-05** Onboarding's SKILL.md cross-references init as the end-to-end flow.
- **AC-06** SKILL.md forbids: overwriting existing files, git operations, whole-project reads,
  `graph.json` loads, unprompted installs. Never-overwrite is stated per phase.
- **AC-07** A local pre-push gate runs `check-consistency.sh` and the repo's test suite, so the
  baseline cannot go red on `main` by forgetting to run it. CI already ran it — but only on
  push-to-`main`, which is the worst place to discover the break.
