# Decisions: Workspace SDD — Graphify-aware multi-project onboarding

D001–D010 are the **workspace doctrine**: they ship verbatim as the baseline of
`docs/_templates/workspace/SHARED_DECISIONS.md`, so every workspace a user onboards starts from
them. D011–D013 are decisions about *this feature's* delivery and stay here.

## Decision log

### D001 — Workspace SDD works above project-level SDD, not instead of it

**Date:** 2026-08-05 · **Status:** Accepted

**Context:** A workspace layer could either absorb per-project specs into one central tree, or sit
above them and only describe the edges.

**Decision:** `.sdd-workspace/` records **project-level** structure — which projects exist, what
they own, how they connect, what contracts bind them. Work confined to one project keeps using that
project's own `specs/features/**`. Only genuinely cross-project features get a workspace spec.

**Reasoning:** Centralising every spec would make the workspace a bottleneck and couple release
cadences that are deliberately independent. The edges are the part no single project can own.

**Consequences:** Two spec homes exist. The rule for choosing is mechanical: more than one project
in the impact set → workspace spec; otherwise → project spec.

---

### D002 — Graphify runs per project; there is no merged workspace graph

**Date:** 2026-08-05 · **Status:** Accepted

**Context:** Graphify could be pointed at the workspace root to produce one graph spanning every
project.

**Decision:** Each project keeps its own `.graphify/` and its own `GRAPH_REPORT.md`. Workspace SDD
consumes those reports; it never merges them.

**Reasoning:** A super-graph over six repositories is larger than any single report and cannot be
consumed within a bounded context — it would recreate the exact cost the layer exists to avoid.
Per-project reports also stay individually refreshable, which a merged graph would not.

**Consequences:** Cross-project edges are **not** derived by Graphify. They are derived from
manifests, API descriptors and configuration, and recorded by hand in `DEPENDENCY_GRAPH.md` with
evidence. That is the division of labour the core sentence names.

---

### D003 — `.graphify/graph.json` is never loaded wholesale

**Date:** 2026-08-05 · **Status:** Accepted

**Context:** `graph.json` is the complete machine-readable graph. It is tempting as a single source
of everything, and ruinous as a context payload.

**Decision:** No skill, prompt, template or agent instruction may read `.graphify/graph.json` in
full. Bounded access only: `GRAPH_REPORT.md`, or Graphify's scoped read-only queries
(`review-context`, `affected-flows`, `tree`, `path`).

**Reasoning:** Loading the raw graph defeats the token-saving purpose Graphify exists for. This
restates, at workspace scope, a rule `docs/AGENTIC_ROUTING.md` already applies to the six lifecycle
agents.

**Consequences:** Enforced, not merely asserted: `scripts/check-consistency.sh` fails on any shipped
document that instructs loading it. A project with `graph.json` but no report counts as
*report missing* (SPEC E2) — the JSON is not a fallback.

---

### D004 — Every cross-project dependency carries evidence or an explicit confidence marker

**Date:** 2026-08-05 · **Status:** Accepted

**Context:** Cross-project edges are usually *inferred* — a matching env var, a similar route name,
a package version. Inference presented as fact is how a map becomes actively misleading.

**Decision:** Every relationship in `DEPENDENCY_GRAPH.md` carries an `Evidence` line (file, line or
manifest reference) and a `Confidence` value from a closed vocabulary: `Confirmed`,
`Inferred - requires confirmation`, `Unknown - requires confirmation`. Nothing is written without
one.

**Reasoning:** The whole value of the layer is that a later session trusts it instead of re-reading
the code. Trust requires that the map distinguish what was observed from what was guessed.

**Consequences:** Onboarding output is honest but incomplete on first pass, and says so. Promoting
an edge to `Confirmed` is a deliberate human act, not a side effect of a later run.

---

### D005 — Every cross-project feature starts with `IMPACT_MAP.md`

**Date:** 2026-08-05 · **Status:** Accepted

**Context:** Without a declared blast radius, "make the widget send consent" has no documented
reason not to touch five repositories.

**Decision:** A cross-project feature produces `IMPACT_MAP.md` — affected projects, **unaffected**
projects, contracts touched, risks, implementation order, validation plan, bounded reading list —
and it is approved before any implementation begins.

**Reasoning:** Naming what is *out* of scope is what converts a plan into a boundary. An
affected-only list bounds nothing.

**Consequences:** Cross-project work gains one approval gate. Discovering mid-implementation that
another project is needed is a stop condition (D008), not an improvisation.

---

### D006 — Missing Graphify never blocks onboarding

**Date:** 2026-08-05 · **Status:** Accepted

**Context:** Graphify is an external, optional tool. The framework's standing posture (spec 010,
`README.md`, `docs/AGENTIC_ROUTING.md`) is graceful degradation.

**Decision:** When a project has no `GRAPH_REPORT.md`, the flow falls back to bounded
`Read`/`Grep`/`Glob` over manifests, README and API descriptors, and records
**Context completeness: partial** in `WORKSPACE_CONTEXT.md`. It may *propose*
`scripts/setup-graphify.sh`; it never installs or runs anything unprompted.

**Reasoning:** A workspace map produced from manifests is worth far more than no map. Making the
optional tool a precondition would contradict the framework's own design principle.

**Consequences:** Two quality tiers of workspace context exist, and the artifacts say which tier
they are. `check-consistency.sh` fails on any shipped document claiming Graphify is required.

---

### D007 — Source code remains the source of truth; Graphify is an accelerator

**Date:** 2026-08-05 · **Status:** Accepted

**Context:** A generated map is a snapshot. Snapshots go stale, silently.

**Decision:** `GRAPH_REPORT.md` and `.sdd-workspace/` narrow *where to look*. Neither is
authoritative about what the code does. Where they disagree with the code, the code wins and the
artifact is corrected.

**Reasoning:** Same rule `skills/graphify-context/SKILL.md` already states per project; the
workspace layer inherits it rather than inventing a competing one.

**Consequences:** Staleness is recorded per project in `PROJECTS.md`. A stale report is still used
for orientation, with the staleness flagged.

---

### D008 — No project may be modified unless it is listed in `IMPACT_MAP.md`

**Date:** 2026-08-05 · **Status:** Accepted

**Context:** D005 requires the map. Without an enforcement rule, the map is documentation rather
than a boundary.

**Decision:** An agent may edit only projects named as affected in the approved `IMPACT_MAP.md`.
Needing a project outside it is a **stop condition**: halt, amend the map, get re-approval, resume.

**Reasoning:** This is the workspace-scope analogue of the `implementer` agent's per-task file
boundary — the mechanism that already keeps single-project work honest.

**Consequences:** Stated in the skill's forbidden actions, the Codex prompt, the workspace
guardrails template and `docs/WORKSPACE_SDD.md`, so no reading path misses it.

---

### D009 — Integration contracts are updated before dependent implementation

**Date:** 2026-08-05 · **Status:** Accepted

**Context:** When a producer and a consumer change together, whichever ships first defines the
contract by accident.

**Decision:** A change to a cross-project contract (REST shape, event schema, webhook payload,
shared package API, env var) is written into `INTEGRATION_CONTRACTS.md` **before** any dependent
project implements against it. Silent contract changes are forbidden.

**Reasoning:** The contract file is the only shared artifact both sides read. If it lags the code,
consumers integrate against an undocumented moving target.

**Consequences:** `IMPACT_MAP.md`'s implementation order must place the contract update first.
`VALIDATION.md` carries a contract-validation section for exactly this.

---

### D010 — Workspace SDD supports both multi-repo folders and monorepos

**Date:** 2026-08-05 · **Status:** Accepted

**Context:** "Workspace" could be defined as several sibling git repositories, or as one repository
with several packages. Picking one would exclude half the real cases.

**Decision:** Projects are detected by **manifest and structure markers**, not by `.git` presence.
A folder of independent clones and a monorepo with `packages/*` are both valid workspaces.

**Reasoning:** The relationships the layer records — contracts, ownership, blast radius — are
identical in both shapes. Only the VCS boundary differs, and that is not what the layer maps.

**Consequences:** Detection cannot rely on `.git`. `PROJECTS.md` records a `Path` relative to the
workspace root, which works for both shapes.

---

## Feature-delivery decisions

### D011 — This spec is numbered 025, not 024 as requested

**Date:** 2026-08-05 · **Status:** Accepted

**Context:** The brief asked for `specs/features/024-workspace-sdd-graphify-onboarding/`. `024` was
already occupied by `specs/features/024-delivery-operations-profile/` (in flight, uncommitted at
the time of writing).

**Decision:** Claim `025`. Confirmed with the maintainer before any file was written.

**Reasoning:** Two folders sharing a number breaks the unique-prefix assumption `/spec-status` and
every cross-reference rely on.

**Consequences:** All references in this feature use `025`. The brief's `024` paths are superseded.

---

### D012 — `profiles.json` is modified, against the brief's instruction

**Date:** 2026-08-05 · **Status:** Accepted

**Context:** The brief said "no modifiques profiles.json". It also set AC-018, "validaciones pasan",
and asked for a new skill. `scripts/check-consistency.sh` raises `orphan-skill` and exits 1 for any
`skills/*/SKILL.md` not declared shipped or planned by some profile, and `plannedSkills` is not an
escape hatch — a planned item that exists on disk is itself a failure (`planned-drift`). The two
instructions cannot both hold.

**Decision:** Append the single string `"sdd-workspace-onboarding"` to `profiles.json`'s
`core.skills` array. No other key, profile, or structure is touched. Confirmed with the maintainer,
who chose registration over a failing CI.

**Reasoning:** The instruction's evident intent is "do not restructure the manifest", not "ship a
skill the manifest cannot see". Registration is the mechanical companion to creating a skill in
this repo — the same one-line change every previous skill required.

**Consequences:** `skills-total` moves 65→66 and `core-skills` 41→42; `check-consistency.sh --fix`
updates the README markers and badge. `core` is exempt from the `agentRouting` coverage rule
(spec 018 D014), so no routing entry is needed.

---

### D013 — No `workspace-researcher` agent in this phase

**Date:** 2026-08-05 · **Status:** Accepted

**Context:** The flow has a distinct accountability shape (read many projects, write one map) that
could justify a seventh lifecycle agent.

**Decision:** No agent is created. `codebase-researcher` gains a documented **workspace mode** in
`docs/AGENTIC_ROUTING.md`: workspace docs first, then per-project Graphify reports, then bounded
files. A dedicated agent is named as a possible future phase (SPEC OQ-2).

**Reasoning:** Agents encode accountability boundaries. Drawing one before the flow has been used
even once would freeze a guess into `profiles.json` and `agents/`. `codebase-researcher` already
owns bounded, graph-first research; a workspace is a wider input to the same job.

**Consequences:** No change to `agents/**` or to any profile's `agents` array in this feature.
