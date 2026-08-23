---
name: sdd-workspace-init
description: Initialize a folder of related projects as a fully-wired SDD workspace, end to end - detect projects, build or refresh each one's Graphify graph, write the .sdd-workspace/ map (projects, dependencies, contracts, decisions), install the generated-state machinery (board, drift, link scripts + workspace skills + hooks), and link every child project back to the workspace layer. Idempotent - re-run to fill gaps; it never overwrites what exists. Use when the user says "init this workspace", "set up SDD across these projects", or asks for one place that knows what every project does. For the mapping phase alone, /sdd-workspace-onboarding still works standalone.
triggers:
  - When the user says "init the workspace", "sdd-workspace-init", or "set up SDD across these projects"
  - When several related repos share a folder and no .sdd-workspace/ exists, or it exists but children are not linked
---

## SDD Contract

```yaml
category: workspace-lifecycle
inputs: [workspace-root, child-project-manifests, graphify-reports?]
outputs:
  - .sdd-workspace/ (map + scripts + BOARD.md + HOW-TO-WORK.md + workspace.json)
  - .claude/skills/{sdd-status,sdd-workspace-link}/ + .claude/settings.json hooks
  - SDD-WORKSPACE block in each child's instruction file
side_effects: writes only listed outputs; never overwrites existing files; no commit/push
composes: [sdd-workspace-onboarding, graphify]
```

## Purpose

One command that leaves a multi-project folder in the state where **any later session — root or
child — has the full picture**: what each project is, how they connect, what is active, and the
rules for working across them. It exists because the pieces ship separately and every workspace
was assembling them by hand, usually incompletely: onboarding builds the map but writes nothing
inside children, so the governance layer stays invisible to the 90% of sessions that open inside
a repo.

**The principle every phase serves: state is generated; rules are written.** Documentation that
copies state (versions, counts, statuses) goes stale and then lies with authority. So the map
records *structure and evidence*, the board *derives* state, and drift *checks* the documents
against the data files they cite.

## Workflow

Run phases in order. Each phase is skippable if its output already exists — say so and move on.
**Never overwrite an existing file**: report "exists, kept" instead. The only exception is a file
whose header marks it as generated.

### Phase 0 — Preconditions

Confirm the working directory is the workspace root (contains ≥2 project directories). If
`.sdd-workspace/` already exists, announce **refresh mode**: only gaps get filled.

### Phase 1 — Detect projects, then ask

Detect candidates by manifest markers (`package.json`, `pyproject.toml`, `pom.xml`, `go.mod`,
`Cargo.toml`, a `specs/` dir). Present the list and **get explicit confirmation** — which repos
participate is a decision, not an inference. Write the confirmed list to
`.sdd-workspace/workspace.json` as `{"projects": [...]}`. Board and link read it from there.

### Phase 2 — Graphify per project (with consent)

For each confirmed project, if `graphify` is on PATH: run `graphify update . --scope all
--no-description --no-label` (local AST extraction — **no LLM tokens**; say so when asking).
Missing Graphify never blocks (onboarding D006): record `Context completeness: partial` and
continue. Never load a `graph.json`; consume only `GRAPH_REPORT.md` and scoped queries.

### Phase 3 — The map

Delegate to **`/sdd-workspace-onboarding`** — it is the mapping phase of this skill and remains
usable standalone. It writes `WORKSPACE_CONTEXT.md`, `PROJECTS.md`, `DEPENDENCY_GRAPH.md`
(evidence + confidence per edge), `INTEGRATION_CONTRACTS.md`, `SHARED_DECISIONS.md`,
`guardrails/`, honoring its own token rules and stop conditions. Per-project purpose ("what does
each project do") lives in `PROJECTS.md` rows and, when depth is wanted, one fiche per project —
bounded sources only, never whole-repo reads.

### Phase 4 — The machinery

Copy from this skill's `templates/` into the workspace, skipping anything that exists:

| Template | Destination | Role |
|---|---|---|
| `board.mjs` | `.sdd-workspace/scripts/` | Generates `BOARD.md`; `--list` for humans, `--check` for CI |
| `drift.mjs` | `.sdd-workspace/scripts/` | Declarative contract-drift checks — fill `CONTRACTS` with the workspace's real contracts as Phase 3 finds them; with none it exits 0 and says so |
| `link-workspace.mjs` | `.sdd-workspace/scripts/` | Links children (Phase 5) |
| `HOW-TO-WORK.md` | `.sdd-workspace/` | The working guide; complete its `[fill in]` section |
| `workspace-skills/*` | `.claude/skills/` | `/sdd-status` and `/sdd-workspace-link` |
| `settings-hooks.json` | merge into `.claude/settings.json` | Three SessionStart hooks |

Then run `node .sdd-workspace/scripts/board.mjs` — the first `BOARD.md` is the phase's proof.

### Phase 5 — Link the children

Run `node .sdd-workspace/scripts/link-workspace.mjs`. Every child's instruction file gains the
delimited SDD-WORKSPACE block: which workspace it belongs to, what to read first, the three
cross-repo rules. This is the half onboarding deliberately does not do — without it, a session
inside a child never sees the layer.

### Phase 6 — Verify and report

`board.mjs --check` runs; `link-workspace.mjs --check` exits 0; `drift.mjs` runs. Report: projects
detected, graphs built/refreshed/absent, files written vs. kept, warnings the first board raised
(these are findings, not noise), and what needs a human: confirming inferred dependency edges,
declaring contracts in `drift.mjs`, completing `HOW-TO-WORK.md` §7.

## Stop conditions

- A candidate project's role is unclear → ask, don't guess. Same for edges with no evidence.
- `.claude/settings.json` exists but is invalid JSON → stop and show it; merging into a broken
  file hides the breakage.
- Any write target exists with different content → keep, report, continue.

## Forbidden

- No `git add`, `git commit`, `git push` — root or children.
- No reading a whole project; no loading `graph.json`; no hypothesis-free cross-repo grep.
- No secrets: config names may be recorded, values never.
- No installs beyond copying this skill's templates; Graphify is *used* if present, never installed unprompted.
- No overwriting: not the map, not an existing script, not a child's instruction file outside the delimited block.

## Output format

End with: **Projects** (confirmed list) · **Graphs** (fresh / stale-kept / absent) · **Written /
kept** (two lists) · **Board says** (the first board's summary line + warnings) · **Needs a
human** (edges to confirm, contracts to declare, guide section to fill).
