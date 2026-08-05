# Workspace Context

> Template for `.sdd-workspace/WORKSPACE_CONTEXT.md`. Written by `/sdd-workspace-onboarding`;
> maintained by hand afterwards. See [`../WORKSPACE_SDD.md`](../WORKSPACE_SDD.md).

**Workspace root:** `<absolute or ~-relative path>`
**Last updated:** `YYYY-MM-DD`
**Context completeness:** `Complete` | `Partial — Graphify unavailable for N project(s)` | `Partial — see unknowns`

## Workspace purpose

<What this group of projects is, as a system. Two to five sentences. What does the whole thing do
for a user that no single project does alone? Name the product, not the repositories.>

## Included projects

Full detail in [`PROJECTS.md`](PROJECTS.md). This is the at-a-glance list.

| Project | Role in the system |
|---|---|
| `<project-dir>` | `<one line: what it is responsible for>` |
| `<project-dir>` | `<one line>` |

### Excluded from this workspace

| Path | Reason |
|---|---|
| `node_modules/`, `vendor/`, `.venv/` | Vendored dependencies — never treated as projects |
| `<path>` | `<why the user excluded it — it is out of bounds for every workspace feature>` |

> An excluded path is out of bounds for every workspace feature until this table changes.

## Workflow rules

- Single-project change → that project's own `specs/features/**`. Cross-project change → a
  workspace spec under `.sdd-workspace/specs/features/<slug>/`.
- Every cross-project feature starts with an approved `IMPACT_MAP.md`.
- No project is modified unless it is listed as **affected** in that map.
- Integration contracts are updated in [`INTEGRATION_CONTRACTS.md`](INTEGRATION_CONTRACTS.md)
  **before** any dependent project implements against them.
- Full guardrails and stop conditions: [`guardrails/WORKSPACE_GUARDRAILS.md`](guardrails/WORKSPACE_GUARDRAILS.md).

## Context strategy

Reading ladder — each rung only when the one above is insufficient:

1. These workspace documents.
2. `<project>/.graphify/GRAPH_REPORT.md`, only for projects the previous rung named.
3. Manifests, `README`, API descriptors (`openapi.yaml`, `*.proto`), `docs/ARCHITECTURE.md`.
4. The bounded reading list in the feature's `IMPACT_MAP.md`.
5. Concrete implementation files — only those on the list.

Standing exclusions: never read every project in full; never load `.graphify/graph.json`; never
grep across every project without a hypothesis.

### Graphify status

| Project | Report present | Last generated | Notes |
|---|---|---|---|
| `<project-dir>` | Yes / No | `YYYY-MM-DD` | `<stale? refresh proposed?>` |

<If any project lacks a report: state that its section of this workspace map was built from
manifests and README only, and is therefore **partial**.>

## Ownership

| Area | Owner | Contact / notes |
|---|---|---|
| `<project or contract>` | `<person or team>` | `<Unknown - requires confirmation, if unknown>` |

## Known unknowns

Anything the onboarding run could not determine. Each stays here until confirmed by a human.

- `Unknown - requires confirmation` — `<what is unknown, and what would resolve it>`
- `Inferred - requires confirmation` — `<what was inferred, from what evidence>`

## Owner notes

<Free-form. Conventions, release order, environments, gotchas, anything a new session should know
that is not derivable from the code. This section is human-authored — an onboarding re-run must
show a diff before touching it.>
