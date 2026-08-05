---
name: sdd-workspace-onboarding
description: Onboard a folder containing several related projects into Workspace SDD. Detects the projects, consumes each one's Graphify report when present, and writes a .sdd-workspace/ map of stacks, dependencies, contracts, ownership and risks. Reads bounded sources only — never a whole project, never graph.json. Not for a single repository; that is /sdd-onboard.
triggers:
  - When the user says "onboard this workspace" or "set up SDD across these projects"
  - When a session opens in a folder holding several related repositories or packages
  - Before planning a feature that will span more than one project
  - When the user asks "how do these projects depend on each other"
---

## SDD Contract

```yaml
category: lifecycle
inputs: [workspace-root, GRAPH_REPORT.md?, project-manifests, api-descriptors]
outputs: [.sdd-workspace/PROJECTS.md, .sdd-workspace/DEPENDENCY_GRAPH.md, .sdd-workspace/INTEGRATION_CONTRACTS.md, .sdd-workspace/WORKSPACE_CONTEXT.md, .sdd-workspace/SHARED_DECISIONS.md, .sdd-workspace/guardrails/WORKSPACE_GUARDRAILS.md]
side_effects: writes-specs
writes_code: false
writes_specs: true
analysis_only: false
primary_agent: codebase-researcher
secondary_agents: [solution-architect]
profile_scope: all
provider_specific: false
```

# SDD Workspace Onboarding

## Purpose

Onboard a folder containing multiple related projects into Workspace SDD: detect the projects, and
produce a bounded, evidence-backed map of how they depend on each other — without reading any
project in full.

> **Graphify maps code-level dependencies. Workspace SDD maps project-level dependencies.**

Doctrine, folder contract and rationale: [`docs/WORKSPACE_SDD.md`](../../docs/WORKSPACE_SDD.md).
Templates for every output file: [`docs/_templates/`](../../docs/_templates/).

This skill writes **only** to `.sdd-workspace/` at the workspace root. It does not implement
anything, in any project.

## Inputs

| Input | Required | Default |
|---|---|---|
| **Workspace root** | Yes | The current directory |
| **Include / exclude list** | No | All detected projects; vendored and build dirs always excluded |
| **May Graphify be run?** | No | **No.** Without an explicit yes, the flow only *proposes* a refresh |
| **May project docs be created?** | No | **No.** Without an explicit yes, nothing is written inside a child project |

Ask for the last two before step 2 if they were not stated. Both default to no.

## Workflow

### 1. Detect candidate projects

Glob one and two levels deep for manifest markers — `package.json`, `pom.xml`, `build.gradle*`,
`pyproject.toml`, `go.mod`, `Cargo.toml`, `composer.json`, `*.csproj`, `Gemfile` — plus monorepo
markers (`pnpm-workspace.yaml`, `turbo.json`, `lerna.json`, a root `workspaces` field).

Detection is by **manifest and structure, not `.git`**: a folder of clones and a monorepo with
`packages/*` are both valid workspaces.

Always exclude: `node_modules/`, `vendor/`, `.venv/`, `dist/`, `build/`, `target/`, `.git/`.

**Present the list and stop.** Confirm inclusions and exclusions before reading anything further.
Record excluded paths and the reason — an excluded path is out of bounds for every later feature.

### 2. Summarise each project, from bounded sources only

Per confirmed project, in this order, stopping as soon as the questions below are answered:

1. `<project>/.graphify/GRAPH_REPORT.md` (canonical) or a legacy root `GRAPH_REPORT.md`.
2. The manifest — name, version, dependencies, published package name.
3. `README` — first ~60 lines. Purpose and public surface, not the install instructions.
4. API descriptors — `openapi.yaml` / `openapi.json`, `*.proto`, `schema.graphql`.
5. `docs/ARCHITECTURE.md`, `docs/PROJECT_CONTEXT.md` if the project was already SDD-onboarded.

Answer four questions per project: **type/stack**, **what it owns**, **what it publishes that
others may consume**, **what it appears to consume**.

**Graphify handling**

Graphify is an **optional external tool, adopted per project**. A workspace where no project has it
onboards fine — the map is smaller and says so. Its absence never blocks this flow.

- Report present → use it. Note its date; if older than the project's newest source, mark **stale**
  and still use it for orientation.
- Report missing → this project is in **fallback mode**. Say so in `PROJECTS.md`. If the user
  approved a Graphify run, propose the exact command
  (`scripts/setup-graphify.sh --project-dir <path>`) and wait. Never run it unprompted.
- `graph.json` present without a report → still "report missing". **Never read `graph.json`.**
- Graphify not installed at all → whole run is fallback mode; `WORKSPACE_CONTEXT.md` records
  **Context completeness: partial**.

Need more depth on one project? Use Graphify's scoped read-only queries
(`review-context`, `affected-flows`, `tree`, `path`) — never a bulk read.

### 3. Derive relationships, with evidence

Cross-project edges come from manifests, descriptors and configuration — **not** from Graphify,
which never crosses a project boundary. Look for:

- A project's published package name appearing in another's dependencies.
- A route from one project's descriptor appearing in another's client code or config.
- Matching event or topic names between a producer and a consumer.
- Env vars in one project naming another project's origin, URL or key.

Each edge gets `From / To / Reason / Contract / Evidence / Confidence / Risk`. `Confidence` is a
closed vocabulary: `Confirmed` (observed and cited), `Inferred - requires confirmation` (suggested
by a name match or convention), `Unknown - requires confirmation` (believed, no evidence found).

**Never write an edge without evidence.** Two projects being in the same folder is not evidence.

### 4. Write `.sdd-workspace/PROJECTS.md`

Inventory from step 2 — one row per project: `Project | Path | Type | Stack | Owns | Public
contracts | Graphify status`. Add the detection-evidence table and the excluded-paths table.

### 5. Write `.sdd-workspace/DEPENDENCY_GRAPH.md`

The relationship blocks from step 3, plus a Mermaid overview (solid = `Confirmed`, dashed =
`Inferred`/`Unknown`), plus ownership collisions and cycles as their own tables.

### 6. Write `.sdd-workspace/INTEGRATION_CONTRACTS.md`

Sections: REST APIs, events, webhooks, shared packages, environment variables, auth boundaries,
data ownership. Each entry names the owning project and its consumers. Record config **names**,
never secret values.

### 7. Write `.sdd-workspace/WORKSPACE_CONTEXT.md` and the guardrails

`WORKSPACE_CONTEXT.md`: purpose, included projects, excluded paths, workflow rules, the context
ladder, Graphify status per project, ownership, known unknowns, owner notes.

Then `SHARED_DECISIONS.md` (seeded with the D001–D010 baseline),
`guardrails/WORKSPACE_GUARDRAILS.md`, and `specs/README.md` from
`WORKSPACE_FEATURE_README.md`.

If `.sdd-workspace/` already exists, update in place — and show a diff before touching any
human-authored section (`Owner notes`, workspace-specific decisions).

### 8. Report unknowns

Close with what could not be determined, not with a summary that implies completeness: projects in
fallback mode, `Inferred` edges awaiting confirmation, unknown ownership, undocumented contracts,
and the exact next step for each.

## Token rules

The reading ladder — each rung only when the one above is insufficient:

1. Existing `.sdd-workspace/` documents.
2. Per-project `.graphify/GRAPH_REPORT.md`, only for projects the previous rung named.
3. Manifests, README, API descriptors, `docs/ARCHITECTURE.md`.
4. A bounded reading list, written down before anything is opened.
5. Concrete implementation files — only those on the list.

Standing exclusions:

- **Never read all files in a project**, or all projects.
- **Never load `.graphify/graph.json`.** Bounded access only.
- **Never grep across every project without a hypothesis** — a cross-project search needs a named
  symbol, route or package and a reason to expect it somewhere specific.
- **Defer implementation files entirely.** Onboarding does not open them; a feature's
  `IMPACT_MAP.md` does.

## Stop conditions

Halt and ask rather than guess:

- Project ownership is unknown.
- A dependency is unclear, and the next step depends on it being real.
- A contract that a relationship implies is undocumented.
- Graphify is unavailable **and** the fallback sources cannot answer a question the map needs.
- The user has not approved modifying a project (including a Graphify refresh inside it).
- Two projects claim ownership of the same data.
- A detected path is ambiguous — a project, or a subdirectory of one?
- A later feature needs a project that its `IMPACT_MAP.md` does not list as affected. Halt, amend
  the map, get it re-approved, then resume.

## Forbidden

- **No implementation.** No application code, config or dependency change, in any project.
- **No writes outside `.sdd-workspace/`**, except a user-approved Graphify context refresh.
- **No project outside `IMPACT_MAP.md`.** Once cross-project work begins, only projects that map
  lists as *affected* may be edited — everything else, including projects it lists as unaffected,
  is read-only. Reading a non-affected project to understand a contract is expected; writing to one
  is not.
- **No `git add .`, no commit, no push** — workspace root or child project.
- **No secrets.** Never read, copy, print or write `.env` files, tokens or keys. Names only.
- **No `graph.json` load.**
- **No broad grep across every project.**
- **No invented dependencies.** No edge without evidence and a confidence marker.
- **No Graphify install or run without explicit approval.**

## Output format

```markdown
# Workspace onboarding: <workspace root>

## Projects detected
<N included, M excluded — one line each, with the detection marker>

## Graphify coverage
<X of N projects have a report; which are stale; which are in fallback mode>
**Context completeness:** Complete | Partial

## Relationships found
<count by confidence: N Confirmed, M Inferred, K Unknown>

## Files written
- .sdd-workspace/WORKSPACE_CONTEXT.md
- .sdd-workspace/PROJECTS.md
- .sdd-workspace/DEPENDENCY_GRAPH.md
- .sdd-workspace/INTEGRATION_CONTRACTS.md
- .sdd-workspace/SHARED_DECISIONS.md
- .sdd-workspace/guardrails/WORKSPACE_GUARDRAILS.md
- .sdd-workspace/specs/README.md

## Unknowns requiring confirmation
<each, with what would resolve it>

## Suggested next steps
<e.g. refresh Graphify for project X; confirm ownership of Y; confirm the inferred X→Y edge>
```

## What this skill does NOT do

- Does not build a merged workspace-wide graph — Graphify stays per project.
- Does not replace per-project specs; single-project work keeps its own `specs/features/**`.
- Does not implement, install, configure MCP, or create agents.
- Is never the source of truth — the code is. `.sdd-workspace/` narrows where to look.
