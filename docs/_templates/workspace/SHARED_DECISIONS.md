# Shared Decisions

> Template for `.sdd-workspace/SHARED_DECISIONS.md`. Decisions that bind **every** project in the
> workspace. See [`../../WORKSPACE_SDD.md`](../../WORKSPACE_SDD.md).

**Last updated:** `YYYY-MM-DD`

A decision belongs here when a single project cannot own it — because it constrains how projects
relate, or because changing it in one place would break another. Decisions internal to one project
stay in that project's own `specs/features/**/DECISIONS.md`.

D001–D010 are the **workspace baseline**. They ship with every workspace and are inherited from
`specs/features/025-workspace-sdd-graphify-onboarding/DECISIONS.md`. Amend them deliberately; add
workspace-specific decisions from D011 onward.

---

## Baseline decisions

### D001 — Workspace SDD works above project-level SDD, not instead of it

`.sdd-workspace/` records project-level structure: which projects exist, what they own, how they
connect, what contracts bind them. Work confined to one project keeps using that project's own
`specs/features/**`. The rule for choosing is mechanical: more than one project in the impact set →
workspace spec; otherwise → project spec.

### D002 — Graphify runs per project; there is no merged workspace graph

Each project keeps its own `.graphify/` and its own `GRAPH_REPORT.md`. Workspace SDD consumes those
reports and never merges them. A super-graph across every repository would be larger than any single
report and could not be consumed within a bounded context — recreating the exact cost this layer
exists to avoid. Cross-project edges are therefore derived from manifests, descriptors and
configuration, and recorded by hand with evidence.

### D003 — `.graphify/graph.json` is never loaded wholesale

Bounded access only: `GRAPH_REPORT.md`, or Graphify's scoped read-only queries
(`review-context`, `affected-flows`, `tree`, `path`). Loading the raw graph defeats the token-saving
purpose Graphify exists for. A project with `graph.json` but no report counts as *report missing* —
the JSON is not a fallback.

### D004 — Every cross-project dependency carries evidence or an explicit confidence marker

Every relationship in `DEPENDENCY_GRAPH.md` carries an `Evidence` line and a `Confidence` value from
a closed vocabulary: `Confirmed`, `Inferred - requires confirmation`, `Unknown - requires
confirmation`. The value of this layer is that later sessions trust it instead of re-reading the
code; trust requires distinguishing what was observed from what was guessed.

### D005 — Every cross-project feature starts with `IMPACT_MAP.md`

Affected projects, **unaffected** projects, contracts touched, risks, implementation order,
validation plan, bounded reading list — approved before implementation begins. Naming what is out of
scope is what converts a plan into a boundary; an affected-only list bounds nothing.

### D006 — Missing Graphify never blocks onboarding

Without a `GRAPH_REPORT.md`, the flow falls back to bounded `Read`/`Grep`/`Glob` over manifests,
README and API descriptors, and records **Context completeness: partial**. It may propose
`scripts/setup-graphify.sh`; it never installs or runs anything unprompted. A map built from
manifests is worth far more than no map.

### D007 — Source code remains the source of truth; Graphify is an accelerator

`GRAPH_REPORT.md` and `.sdd-workspace/` narrow *where to look*. Neither is authoritative about what
the code does. Where they disagree with the code, the code wins and the artifact is corrected.
Staleness is recorded per project in `PROJECTS.md`.

### D008 — No project may be modified unless it is listed in `IMPACT_MAP.md`

Only projects named as affected in the approved map may be edited. Needing a project outside it is a
**stop condition**: halt, amend the map, get re-approval, resume. This is the workspace-scope
analogue of a per-task file boundary.

### D009 — Integration contracts are updated before dependent implementation

A change to a cross-project contract (REST shape, event schema, webhook payload, shared-package API,
env var) is written into `INTEGRATION_CONTRACTS.md` **before** any dependent project implements
against it. Silent contract changes are forbidden. `IMPACT_MAP.md`'s implementation order must
therefore place the contract update first.

### D010 — Workspace SDD supports both multi-repo folders and monorepos

Projects are detected by manifest and structure markers, not by `.git` presence. A folder of
independent clones and a monorepo with `packages/*` are both valid workspaces — the relationships
this layer records are identical in both shapes.

---

## Workspace-specific decisions

Add from D011 onward, using the same shape.

### D011 — `<title: the decision, stated as a rule>`

**Date:** `YYYY-MM-DD` · **Status:** `Proposed` | `Accepted` | `Superseded by DNNN`
**Projects bound:** `<which projects this constrains — or "all">`

**Context:** `<what forced the decision; what was ambiguous or in conflict>`

**Decision:** `<what was decided, precisely enough to be checkable>`

**Reasoning:** `<why this over the alternatives>`

**Consequences:** `<what this now requires or forbids; what has to change elsewhere>`
