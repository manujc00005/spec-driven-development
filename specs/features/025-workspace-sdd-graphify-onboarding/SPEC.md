# Feature Spec: Workspace SDD — Graphify-aware multi-project onboarding

## Status

Done

> **Numbering note.** This feature was requested as `024`. `024` was already taken by
> `specs/features/024-delivery-operations-profile/` (in flight at the time of writing), so this
> spec claims `025`. See D011.

## Problem

SDD is a **per-project** framework today. `/sdd-onboard` reads one repository, `/project-init`
scaffolds one `specs/` tree, `profiles.json` activates skills for one stack, and every artifact the
framework produces (`SPEC.md`, `PLAN.md`, `docs/ARCHITECTURE.md`, `.graphify/GRAPH_REPORT.md`) is
scoped to a single project root.

Real features are not scoped that way. A single change — "add a consent field to the lead capture
flow" — can land in a backend API, an embeddable widget, a shared SDK, a WordPress plugin, an admin
frontend and a CRM platform, each in its own repository, each with its own owner and its own
release cadence. Nothing in the framework describes the relationships *between* those repositories.

Three concrete consequences:

1. **Cross-project context is reconstructed from scratch every session.** The knowledge that the
   widget talks to the backend over `POST /v1/leads`, that the SDK wraps that call, and that the
   WordPress plugin vendors the SDK, lives only in the maintainer's head. Each new session
   rediscovers it by reading code.
2. **Rediscovery is the expensive kind.** With no map, the only way to answer "who consumes this
   endpoint?" across six repositories is a broad `Grep` over all of them, or reading each project
   in full. Both are exactly the token-burning patterns `context-manager` and `graphify-context`
   exist to prevent — but both of those skills stop at the project boundary.
3. **Blast radius is unbounded and undeclared.** Without a recorded impact set, nothing states
   which projects a feature may touch. An agent asked to "make the widget send consent" has no
   documented reason not to also edit the SDK, the plugin and the backend in the same pass.

Graphify already solves the *intra*-project half of this: it maps code-level dependencies inside
one repository and publishes a bounded summary at `.graphify/GRAPH_REPORT.md`. Nothing consumes
those reports across projects, and nothing maps the edges *between* projects.

## Goal

Introduce a **workspace layer** that sits above per-project SDD:

- A documented `/sdd-workspace-onboarding` flow that reads a folder containing several related
  projects, detects them, and produces a bounded, evidence-backed map of how they relate.
- A `.sdd-workspace/` artifact layer (projects, dependency graph, integration contracts, workspace
  context, shared decisions, guardrails) that later sessions read *instead of* re-reading the
  repositories.
- A per-project Graphify strategy: use each project's existing `.graphify/GRAPH_REPORT.md` when it
  exists, propose a refresh when it does not and the user approves, degrade to bounded
  `Read`/`Grep`/`Glob` when Graphify is absent — and never load `.graphify/graph.json` wholesale.
- A cross-project feature workflow gated on `IMPACT_MAP.md`: no project may be modified unless it
  is listed there.

The organising sentence, repeated verbatim in the docs and the skill:

> **Graphify maps code-level dependencies. Workspace SDD maps project-level dependencies.**

This feature ships **design, documentation, templates, one skill and one Codex prompt**. It ships
no orchestration code, no installer change and no agent.

## Non-goals

- **No product feature implementation.** Nothing in a child project is built here.
- **No modification of child-project application code.** The onboarding flow reads child projects;
  the only write it may ever propose inside one is a Graphify context refresh, and only with
  explicit approval.
- **Graphify is not made mandatory.** Its absence degrades the flow, never blocks it (D006).
- **No wholesale `graph.json` load.** Not by this flow, not by any artifact it produces (D003).
- **No monolithic workspace graph.** Graphify stays per-project; there is no merged super-graph
  (D002).
- **Per-project specs are not replaced.** `specs/features/**` inside each project remains the unit
  of record for single-project work (D001).
- **Monorepo is not assumed** — and neither is multi-repo. Both shapes are supported (D010).
- **No Graphify install without confirmation.** The flow may *propose* `scripts/setup-graphify.sh`;
  it never runs an install unprompted.
- **No new agent in this feature.** A `workspace-researcher` agent is named as a possible future
  phase only (D013).
- **No MCP configuration.**
- **No installer, hook or settings-template change.** `install.sh`, `install.ps1`, `hooks/**` and
  `settings.template*.json` are out of bounds (FR-012).

## Users / Actors

| Actor | Interest |
|---|---|
| **Solo maintainer of several related repos** | Wants a session to understand the whole system without paying to re-read it each time. Primary user. |
| **`codebase-researcher` agent** | Gains a workspace mode: read `.sdd-workspace/` first, project Graphify reports second, bounded files last. |
| **A future contributor** | Reads `.sdd-workspace/` to learn what talks to what and who owns which contract. |
| **Framework CI (`check-consistency.sh`)** | Enforces that the workspace artifacts, skill and prompt exist and that no document claims Graphify is required or that `graph.json` should be loaded. |

## Current behavior

- `/sdd-onboard` onboards exactly one project; it has no notion of sibling repositories.
- `graphify-context` interprets one `.graphify/GRAPH_REPORT.md` for one project.
- `context-manager` builds a bounded reading list inside one project root.
- `docs/AGENTIC_ROUTING.md` already forbids loading `graph.json` wholesale, but only as a rule for
  the six lifecycle agents — no artifact records cross-project structure.
- Nothing in `docs/`, `skills/` or `adapters/` mentions a workspace at all.

## Desired behavior

Given a folder such as:

```
~/Proyectos/acme/
├── acme-api/
├── acme-widget/
├── acme-sdk/
├── acme-wp-plugin/
└── acme-admin/
```

running `/sdd-workspace-onboarding` in that folder:

1. **Detects** candidate projects by manifest/VCS markers, presents the list, and asks for
   include/exclude confirmation before reading anything further.
2. **Summarises each project** from bounded sources only: `.graphify/GRAPH_REPORT.md` when present,
   otherwise manifests (`package.json`, `pom.xml`, `pyproject.toml`, `composer.json`, …), `README`,
   API descriptors (`openapi.yaml`, `*.proto`), and `docs/ARCHITECTURE.md` if the project was
   already SDD-onboarded.
3. **Proposes**, per project with no report, a Graphify refresh — as a command for the user to
   approve, never an automatic run.
4. **Infers relationships with evidence.** Every edge carries a file/line or manifest citation and
   a confidence marker: `Confirmed`, `Inferred - requires confirmation`, or
   `Unknown - requires confirmation`. No unevidenced edge is written (D004).
5. **Writes `.sdd-workspace/`** at the workspace root: `WORKSPACE_CONTEXT.md`, `PROJECTS.md`,
   `DEPENDENCY_GRAPH.md`, `INTEGRATION_CONTRACTS.md`, `SHARED_DECISIONS.md`,
   `guardrails/WORKSPACE_GUARDRAILS.md`, and a `specs/` subtree seeded with a feature README.
6. **Reports unknowns explicitly** rather than filling gaps with plausible guesses.

Afterwards, a cross-project feature begins with a workspace spec and an `IMPACT_MAP.md`; no project
outside that map may be touched (D005, D008).

## Functional requirements

**Documentation and design**

- **FR-001** — `docs/WORKSPACE_SDD.md` exists and explains: why workspace-level SDD, the core idea
  sentence, the `.sdd-workspace/` folder structure, the token-saving strategy, per-project Graphify
  usage, the cross-project feature workflow, and the guardrails.
- **FR-002** — The `/sdd-workspace-onboarding` flow is fully specified in
  `skills/sdd-workspace-onboarding/SKILL.md`, including purpose, inputs, workflow, token rules,
  stop conditions and forbidden actions.
- **FR-003** — A provider-neutral Codex counterpart exists as a prompt under
  `adapters/codex/prompts/`, described as prompt-based with no native-agent claim.

**Templates**

- **FR-004** — Ten templates exist under `docs/_templates/`, flat and `WORKSPACE_`-prefixed so the
  installer can copy them by name (D014): `WORKSPACE_CONTEXT.md`,
  `WORKSPACE_PROJECTS.md`, `WORKSPACE_DEPENDENCY_GRAPH.md`, `WORKSPACE_INTEGRATION_CONTRACTS.md`,
  `WORKSPACE_SHARED_DECISIONS.md`,
  `WORKSPACE_GUARDRAILS.md`, `WORKSPACE_FEATURE_README.md`, `WORKSPACE_IMPACT_MAP.md`,
  `WORKSPACE_PROJECT_CHANGES.md`, `WORKSPACE_VALIDATION.md`. All ten are declared in
  `profiles.json` so `install.sh` actually ships them.
- **FR-005** — `WORKSPACE_PROJECTS.md` carries the columns
  `Project | Path | Type | Stack | Owns | Public contracts | Graphify status`.
- **FR-006** — `DEPENDENCY_GRAPH.md` carries a per-relationship block with
  `From / To / Reason / Contract / Evidence / Confidence / Risk`, plus a Mermaid placeholder.
- **FR-007** — `INTEGRATION_CONTRACTS.md` carries sections for REST APIs, events, webhooks, shared
  packages, environment variables, auth boundaries and data ownership.
- **FR-008** — `SHARED_DECISIONS.md` ships D001–D010 as the workspace decision baseline.
- **FR-009** — `IMPACT_MAP.md` carries affected projects, unaffected projects, contracts touched,
  risks, implementation order, validation plan and a bounded reading list.

**Behavioral rules the flow must encode**

- **FR-010** — The flow prefers `.graphify/GRAPH_REPORT.md`; when it is absent it uses bounded
  fallback reading and marks the resulting context **partial** in `WORKSPACE_CONTEXT.md`.
- **FR-011** — The flow never reads `.graphify/graph.json`, and no shipped artifact instructs
  anyone to.
- **FR-012** — The flow modifies nothing outside the workspace root's `.sdd-workspace/`, except a
  user-approved Graphify context refresh inside a child project. It never stages, commits or
  pushes.

**Framework consistency**

- **FR-013** — `scripts/check-consistency.sh` verifies: `docs/WORKSPACE_SDD.md` exists; the skill
  exists; all ten workspace templates exist; the Codex workspace prompt exists whenever
  `adapters/codex/` exists; no shipped document asserts Graphify is required; no shipped document
  instructs loading `graph.json` wholesale.
- **FR-014** — `scripts/check-consistency.test.sh` gains cases proving each new check fails when
  violated: missing `docs/WORKSPACE_SDD.md`, missing `IMPACT_MAP.md` template, an injected
  "Graphify is required" claim, and an injected "load the full graph.json" instruction.
- **FR-015** — The new skill is registered in `profiles.json` under `core.skills`, and README count
  markers/badges are updated, so `check-consistency.sh` exits 0 (see D012 for why this overrides
  the "do not modify profiles.json" instruction).

## Non-functional requirements

- **NFR-001 (context economy)** — Onboarding a five-project workspace must be achievable from
  graph reports, manifests, READMEs and API descriptors alone. Reading implementation files is
  deferred to the point where an `IMPACT_MAP.md` names them.
- **NFR-002 (honesty)** — Every relationship is either evidenced or explicitly marked as inferred
  or unknown. There is no unmarked middle ground.
- **NFR-003 (graceful degradation)** — Missing Graphify, a missing manifest, or an unreadable
  project degrades a section to `Unknown - requires confirmation`; it never aborts the run.
- **NFR-004 (provider neutrality)** — The workflow is expressible as a prompt; nothing in it
  depends on a Claude-specific mechanism. The skill's contract is therefore
  `provider_specific: false`.
- **NFR-005 (skill form)** — `SKILL.md` stays within the repo's 400-char description and 600-line
  body caps (spec 022 FR-001).

## API / Interface changes

New user-facing command: `/sdd-workspace-onboarding`.

New artifact layer, written at the **workspace root** (not inside any project):

```
.sdd-workspace/
├── WORKSPACE_CONTEXT.md
├── PROJECTS.md
├── DEPENDENCY_GRAPH.md
├── INTEGRATION_CONTRACTS.md
├── SHARED_DECISIONS.md
├── guardrails/
│   └── WORKSPACE_GUARDRAILS.md
└── specs/
    ├── README.md
    └── features/
        └── <feature-slug>/
            ├── SPEC.md
            ├── PLAN.md
            ├── TASKS.md
            ├── DECISIONS.md
            ├── IMPACT_MAP.md
            ├── PROJECT_CHANGES.md
            └── VALIDATION.md
```

No change to any existing command's interface.

## Data model changes

None. `profiles.json` gains one entry in the existing `core.skills` array; its schema is unchanged.

## Edge cases

| # | Case | Handling |
|---|---|---|
| E1 | Workspace root is itself a git repo containing subprojects (monorepo) | Supported. Projects are detected by manifest, not by `.git` presence (D010). |
| E2 | A project has a `.graphify/graph.json` but no `GRAPH_REPORT.md` | Treated as "report missing". Propose `graphify update`; never read the JSON (D003). |
| E3 | A project has a stale report (older than its newest source) | Used for orientation, marked stale in `PROJECTS.md`, refresh proposed. |
| E4 | Two projects declare the same package name | Both recorded; the collision is a `Risk` row, not silently resolved. |
| E5 | A dependency edge is suggested by a name match only (e.g. an env var named `API_URL`) | `Inferred - requires confirmation` with the matched line as evidence. Never `Confirmed`. |
| E6 | The folder contains a vendored `node_modules`/`vendor` tree | Excluded from detection by default; exclusions are listed in `WORKSPACE_CONTEXT.md`. |
| E7 | Graphify is not installed at all | Whole run proceeds in fallback mode; `WORKSPACE_CONTEXT.md` records **Context completeness: partial**. |
| E8 | User declines to include a detected project | Recorded in `PROJECTS.md` as excluded with the reason; it is then out of bounds for every later feature. |
| E9 | `.sdd-workspace/` already exists | Update in place; never overwrite a human-edited `Owner notes` or `SHARED_DECISIONS.md` entry without showing the diff first. |
| E10 | A cross-project feature turns out to need a project absent from `IMPACT_MAP.md` | Stop condition. The map is amended and re-approved before any edit (D008). |

## Acceptance criteria

- **AC-001** — `docs/WORKSPACE_SDD.md` exists and contains the sections: why, core idea, folder
  structure, token-saving strategy, Graphify usage, cross-project feature workflow, guardrails.
- **AC-002** — `skills/sdd-workspace-onboarding/SKILL.md` exists and specifies the
  `/sdd-workspace-onboarding` flow with purpose, inputs, workflow, token rules, stop conditions and
  forbidden actions.
- **AC-003** — The documented workflow's first step detects candidate projects inside a workspace
  folder and confirms the list with the user before deeper reading.
- **AC-004** — The documented workflow consumes `.graphify/GRAPH_REPORT.md` per project when it
  exists.
- **AC-005** — When Graphify is unavailable, the documented workflow uses a bounded
  `Read`/`Grep`/`Glob` fallback and records the context as partial.
- **AC-006** — No shipped artifact reads or instructs reading `.graphify/graph.json` wholesale, and
  `check-consistency.sh` fails if one is introduced.
- **AC-007** — A `PROJECTS.md` template exists and the flow writes `.sdd-workspace/PROJECTS.md`.
- **AC-008** — A `DEPENDENCY_GRAPH.md` template exists and the flow writes
  `.sdd-workspace/DEPENDENCY_GRAPH.md`.
- **AC-009** — An `INTEGRATION_CONTRACTS.md` template exists and the flow writes
  `.sdd-workspace/INTEGRATION_CONTRACTS.md`.
- **AC-010** — A `WORKSPACE_CONTEXT.md` template exists and the flow writes
  `.sdd-workspace/WORKSPACE_CONTEXT.md`.
- **AC-011** — A `SHARED_DECISIONS.md` template exists, carrying D001–D010, and the flow writes
  `.sdd-workspace/SHARED_DECISIONS.md`.
- **AC-012** — A `WORKSPACE_GUARDRAILS.md` template exists and the flow writes
  `.sdd-workspace/guardrails/WORKSPACE_GUARDRAILS.md`.
- **AC-013** — Every document describing cross-project work states that `IMPACT_MAP.md` is required
  before implementation begins.
- **AC-014** — Every document describing cross-project work states that no project outside
  `IMPACT_MAP.md` may be modified, and names it as a stop condition.
- **AC-015** — `DEPENDENCY_GRAPH.md` requires per-relationship `Evidence` and `Confidence`, with
  `Confirmed` / `Inferred - requires confirmation` / `Unknown - requires confirmation` as the only
  values.
- **AC-016** — The skill's token rules mandate the order: workspace docs → per-project graph
  reports → manifests/README/API descriptors → bounded reading list → concrete implementation
  files.
- **AC-017** — Graphify remains optional and per-project: no shipped document claims it is
  required, and `check-consistency.sh` fails if one does.
- **AC-018** — `bash scripts/check-consistency.sh` exits 0, `python3 -m json.tool profiles.json`
  succeeds, and `bash scripts/check-consistency.test.sh` reports 0 failures.

## Test scenarios

| # | Scenario | Expected |
|---|---|---|
| TS-1 | Run `check-consistency.sh` on the unmodified tree | Exit 0 |
| TS-2 | Delete `docs/WORKSPACE_SDD.md`, re-run | Exit 1, `[workspace]` finding |
| TS-3 | Delete `docs/_templates/WORKSPACE_IMPACT_MAP.md`, re-run | Exit 1, `[workspace]` finding naming the template |
| TS-4 | Inject "Graphify is required" into a shipped doc, re-run | Exit 1, claim finding |
| TS-5 | Inject "load the full graph.json into context" into a shipped doc, re-run | Exit 1, claim finding |
| TS-6 | Remove `adapters/codex/prompts/sdd-workspace-onboarding.md` while `adapters/codex/` exists | Exit 1 |
| TS-7 | Existing negated prose in `docs/AGENTIC_ROUTING.md` ("`graph.json` should not be loaded wholesale") | Not reported — negated claims are safe documentation |

## Assumptions

- **A1** — The workspace root is a plain folder the user opens a session in; it is not required to
  be a git repository.
- **A2** — Child projects may or may not be SDD-onboarded; the flow works either way and reads
  `docs/ARCHITECTURE.md` opportunistically.
- **A3** — Graphify's report path is `.graphify/GRAPH_REPORT.md` (canonical since spec 010), with
  a legacy root `GRAPH_REPORT.md` fallback.
- **A4** — Registering the skill in `profiles.json` `core.skills` is the intended registration
  point: `core` is exempt from the `agentRouting` coverage rule, so no routing entry is needed.

## Open questions

- **OQ-1** *(non-blocking)* — **Deferred.** Should `.sdd-workspace/` eventually be installable via a
  `scripts/setup-workspace.sh`, mirroring `setup-graphify.sh`? The flow writes the files itself
  today. D014 raises the stakes: the installer is where this feature's one real defect lived, so a
  dedicated setup script would need its own install-time verification, not just CI.
- **OQ-2** *(non-blocking)* — **Deferred.** Should a dedicated `workspace-researcher` agent own this
  flow instead of routing it through `codebase-researcher` in workspace mode? D013 keeps it a future
  phase; no agent was created. Revisit once the flow has actually been run.
- **OQ-3** *(non-blocking)* — **Resolved: no.** `check-consistency.sh` does not validate a *user's*
  `.sdd-workspace/` tree. This repo ships the framework, not a workspace.
- **OQ-4** *(raised at close, non-blocking)* — **Deferred.** The flow has never been executed against
  a real workspace, so AC-016 (token minimisation) is an argued design property, not a measured one.
  The eval gate does not apply (`category: lifecycle`, not `mindset`), so nothing forces this. First
  real run should record what it actually cost.

## Contracted services

None. This feature ships no billable-service reviewer.
