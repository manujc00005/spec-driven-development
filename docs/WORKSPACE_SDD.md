# Workspace SDD

Spec-Driven Development scaled from one project to a **folder of related projects**. Shipped by
this repo since `specs/features/025-workspace-sdd-graphify-onboarding/`.

Per-project SDD answers *what are we building here and why*. Workspace SDD answers the question no
single project can: **how do these projects depend on each other, and what breaks if I change
this one?**

## Why workspace-level SDD?

Most real features do not respect repository boundaries. A single change — "capture marketing
consent on the lead form" — routinely lands across:

- a **backend API** that owns the data model and the endpoint,
- an embeddable **widget** that collects the input,
- a **shared SDK** that both the widget and third parties call,
- a **WordPress plugin** that vendors the SDK,
- a **frontend admin** that displays and exports the value,
- a **CRM / lead platform** that consumes the resulting event.

Six repositories, six release cadences, one feature. Without a workspace layer, three things go
wrong every single session:

1. **The map is rebuilt from scratch.** That the widget calls `POST /v1/leads`, that the SDK wraps
   it, that the plugin pins SDK `^2.4` — all of it lives in someone's head and is rediscovered by
   reading code.
2. **Rediscovery is the expensive kind.** With no map, "who consumes this endpoint?" means a broad
   grep across every repository, or reading them in full. That is precisely the token burn
   `/context-manager` and `/graphify-context` exist to prevent — and both of those stop at the
   project boundary.
3. **Blast radius is undeclared.** Nothing states which projects a feature may touch, so nothing
   stops an agent from editing all six.

Workspace SDD records the map **once**, with evidence, and every later session reads the map
instead of the repositories.

## Core idea

> **Graphify maps code-level dependencies. Workspace SDD maps project-level dependencies.**

Two layers, deliberately separate:

| | Graphify | Workspace SDD |
|---|---|---|
| **Scope** | Inside one project | Between projects |
| **Produces** | `.graphify/GRAPH_REPORT.md` per project | `.sdd-workspace/` at the workspace root |
| **Edges are** | Imports, calls, module dependencies | REST calls, events, webhooks, shared packages, env vars |
| **Derived** | Automatically, by the tool | By hand, from manifests and descriptors, **with evidence** |
| **Required?** | No — optional accelerator | The layer this document describes |

Graphify never produces a cross-project edge, and Workspace SDD never re-derives an intra-project
one. Neither replaces reading the code: both narrow *where* to look.

Graphify stays **per project**. There is no merged workspace-wide graph — a super-graph across six
repositories is bigger than any one report and could not be consumed within a bounded context,
which would recreate the exact cost this layer exists to avoid.

## Folder structure

`.sdd-workspace/` lives at the **workspace root** — the folder containing the projects — never
inside a project.

```
.sdd-workspace/
├── WORKSPACE_CONTEXT.md          # purpose, included projects, workflow rules, context strategy
├── PROJECTS.md                   # one row per project: path, type, stack, owns, contracts, graph status
├── DEPENDENCY_GRAPH.md           # project → project edges, each with evidence and confidence
├── INTEGRATION_CONTRACTS.md      # REST, events, webhooks, shared packages, env vars, auth, data ownership
├── SHARED_DECISIONS.md           # workspace-wide decisions (seeded with D001–D010)
├── guardrails/
│   └── WORKSPACE_GUARDRAILS.md   # prohibitions and stop conditions
└── specs/
    ├── README.md
    └── features/
        └── <feature-slug>/
            ├── SPEC.md
            ├── PLAN.md
            ├── TASKS.md
            ├── DECISIONS.md
            ├── IMPACT_MAP.md      # affected + unaffected projects — the boundary
            ├── PROJECT_CHANGES.md # per-project change table
            └── VALIDATION.md      # per-project, cross-project and contract validation
```

Templates for every one of these files ship in
[`_templates/workspace/`](_templates/workspace/).

**This does not replace per-project specs.** A change confined to one project keeps using that
project's own `specs/features/**`. The rule is mechanical: more than one project in the impact set
→ workspace spec; otherwise → project spec.

Both workspace shapes are supported. Projects are detected by **manifest and structure markers**,
not by `.git` presence, so a folder of independent clones and a monorepo with `packages/*` are both
valid workspaces.

## Token-saving strategy

The point of the layer is that a session spends its context on the *change*, not on rediscovering
the system. That means a strict reading ladder — each rung is only climbed when the one above it is
insufficient:

1. **`.sdd-workspace/` documents.** Cheapest and most specific. `PROJECTS.md` and
   `DEPENDENCY_GRAPH.md` usually answer "which projects are involved" outright.
2. **Per-project `.graphify/GRAPH_REPORT.md`.** A bounded summary of one project's internals — read
   only for the projects the previous rung identified.
3. **Manifests, README, API descriptors.** `package.json`, `pom.xml`, `pyproject.toml`,
   `composer.json`, `openapi.yaml`, `*.proto`, `docs/ARCHITECTURE.md` where a project was already
   SDD-onboarded.
4. **A bounded reading list.** Named files, written into `IMPACT_MAP.md` before anything is opened.
5. **Concrete implementation files.** Only those on the list, only for projects named as affected.

Standing exclusions at every rung:

- **Never read every project in full.** Not at onboarding, not during a feature.
- **Never load `.graphify/graph.json`.** It is the complete machine-readable graph; loading it
  defeats the token-saving purpose Graphify exists for. Use `GRAPH_REPORT.md`, or Graphify's
  scoped read-only queries.
- **Never grep across every project without a hypothesis.** A cross-project search needs a named
  symbol, route or package and a reason to expect it somewhere specific.

## Graphify usage

Graphify is an **optional external tool**. Workspace SDD uses it when it is there and works without
it when it is not.

- **It runs per project.** Each project keeps its own `.graphify/`; see
  [`_templates/GRAPHIFY.md`](_templates/GRAPHIFY.md) and `scripts/setup-graphify.sh` for adopting
  it in a project.
- **Workspace SDD consumes the reports**, resolved as `.graphify/GRAPH_REPORT.md` (canonical) or a
  legacy root `GRAPH_REPORT.md`.
- **Going deeper uses scoped queries**, never a bulk read: `graphify review-context <file>`,
  `graphify affected-flows <file>`, `graphify tree <node>`, `graphify path <a> <b>`.
- **A project with `graph.json` but no report counts as "report missing".** The JSON is not a
  fallback — propose `graphify update` instead.
- **When Graphify is absent**, fall back to bounded `Read`/`Grep`/`Glob` over manifests, README and
  API descriptors, and record **Context completeness: partial** in `WORKSPACE_CONTEXT.md`. A map
  built from manifests is worth far more than no map.
- **Nothing is installed or run unprompted.** The flow may propose `scripts/setup-graphify.sh`;
  approving it is the user's call.

The code is always the source of truth. `GRAPH_REPORT.md` and `.sdd-workspace/` narrow where to
look; where either disagrees with the code, the code wins and the artifact is corrected.

## Cross-project feature workflow

1. **Read `.sdd-workspace/`** — context, projects, dependency graph, integration contracts,
   guardrails. Nothing else yet.
2. **Create the feature spec** under `.sdd-workspace/specs/features/<slug>/` (SPEC, PLAN, TASKS,
   DECISIONS), using the same SDD discipline as a project spec.
3. **Create `IMPACT_MAP.md`** — affected projects, **unaffected** projects, contracts touched,
   risks, implementation order, validation plan, bounded reading list. Naming what is *out* of
   scope is what turns the map into a boundary.
4. **Get the affected-project list approved** before any file is opened for editing.
5. **Build the bounded reading list** from graph reports and contracts — not from a repo sweep.
6. **Implement one project at a time**, in the order the impact map states. Contract-owning
   projects go first (see the guardrail below).
7. **Validate contracts** at each boundary crossed: per-project checks, then cross-project, then
   the contract itself.
8. **Close with evidence** — `PROJECT_CHANGES.md` and `VALIDATION.md` filled in from what actually
   ran, not from what was planned.

Every relationship recorded along the way carries evidence and a confidence marker —
`Confirmed`, `Inferred - requires confirmation`, or `Unknown - requires confirmation`. An inference
presented as fact is how a map becomes actively misleading, so there is no unmarked middle ground.

## Guardrails

These are the workspace-scope equivalents of the per-task file boundary that keeps single-project
work honest. They ship as
[`_templates/workspace/WORKSPACE_GUARDRAILS.md`](_templates/workspace/WORKSPACE_GUARDRAILS.md).

**Prohibitions**

- **No broad edits.** No change touching many projects "while we're in there".
- **No implementation before the impact map.** The map is written and approved first.
- **No project outside the impact map.** If it is not listed as affected, it is not edited.
- **No silent contract changes.** A REST shape, event schema, webhook payload, shared-package API
  or env var changes in `INTEGRATION_CONTRACTS.md` **before** any dependent project implements
  against it.
- **No secrets.** No reading, copying or writing `.env` files, tokens or credentials — in any
  project.
- **No `git add .`.** Staging is explicit and per file, and is the user's decision.
- **No `git commit`, no `git push`.** In the workspace root or in any child project.
- **No invented dependencies.** No edge without evidence.
- **No wholesale `graph.json` load.**
- **No full-repository reads** across the workspace.

**Stop conditions** — halt and ask rather than proceed:

- A needed project is not in the impact map.
- Project ownership is unknown.
- A dependency is unclear or only inferred, and the next step depends on it being real.
- A contract the change relies on is undocumented.
- Graphify is unavailable *and* the fallback context is not sufficient to answer the question.
- The user has not approved modifying a given project.

## Related documents

- [`AGENTIC_ROUTING.md`](AGENTIC_ROUTING.md) — the six lifecycle agents; `codebase-researcher`'s
  workspace mode.
- [`_templates/GRAPHIFY.md`](_templates/GRAPHIFY.md) — adopting Graphify in a single project.
- [`../skills/sdd-workspace-onboarding/SKILL.md`](../skills/sdd-workspace-onboarding/SKILL.md) —
  the `/sdd-workspace-onboarding` flow.
- [`../adapters/codex/prompts/sdd-workspace-onboarding.md`](../adapters/codex/prompts/sdd-workspace-onboarding.md)
  — the prompt-based Codex counterpart.
