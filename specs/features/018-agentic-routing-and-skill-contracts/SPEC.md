# Feature Spec: Agentic Routing and Skill Contracts (Phase 2)

## Status

Done

## Problem

The framework has 61 healthy, well-scoped skills, but there is no clear **agent layer**
that consumes them. Skills are invoked ad-hoc — by the human or by slash commands — so it
is impossible to say *who* is accountable for research, architecture, implementation,
security, domain review, and final conformance. The only two agents that exist
(`deep-reasoner`, `fast-worker`) are consumed by a single skill (`sdd-orchestrate`); the
other 60 skills have no agent owner.

A second, concrete defect compounds this: three reviewer skills
(`java-spring-reviewer`, `spring-boot-api-reviewer`, `event-driven-reviewer`) declare that
they "route to the `java-spring` / `api-design` subagent" — but those subagents are **not
shipped by this repo**. They are ambient, environment-provided agents. This is an
uncontrolled coupling: the framework's behavior depends on artifacts it does not own.

## Goal

Create a minimal, professional agentic layer that:

- keeps skills as reusable capabilities (no skill becomes an agent),
- defines exactly **6 agents** with clear, non-overlapping responsibilities,
- adds lightweight **input/output contracts** to skills,
- routes all domain/stack reviewers through a single `domain-reviewer` agent,
- removes the framework's dependence on uncontrolled external subagents,
- preserves Claude Code compatibility,
- prepares the framework for future providers (e.g. Codex) **without coupling to them**.

## Non-goals

- Not one agent per technology.
- Not replacing skills with agents.
- Not deleting or moving any existing skill.
- Not breaking Claude Code.
- Not building complex swarms or advanced parallelism.
- Not competing on agent count.
- Not installing or wiring external providers.
- Not touching downstream/consumer projects.
- Not making Graphify mandatory.
- Not changing hook behavior.
- Not creating a dedicated `test-engineer` agent in this phase.

## Users / Actors

- **Solo maintainer** of the SDD framework (primary).
- **Downstream project developers** who install a profile and rely on stable agent routing.
- **Claude Code runtime** dispatching agents and loading skills.
- **Future providers** (Codex and others) that may map onto the same agent contracts.

## Current state

- 61 skills on disk; every skill is declared in exactly one profile.
- No orphan skills; no broken profile references; all `plannedSkills` arrays empty.
- 2 agents on disk: `deep-reasoner` (opus, read-only), `fast-worker` (sonnet, implements) —
  consumed only by `sdd-orchestrate`, copied per-file by the installer (not junction-linked).
- 7 profiles (`core`, `java-spring-backend`, `messaging-event-driven`, `payments-fintech`,
  `next-prisma-web`, `seo-geo-addon`, `blockchain-crypto` [disabled]).
- `profiles.json` already has an `agents` / `plannedAgents` slot per profile (added in 0.4.0).
- `check-consistency` (spec 007 / 012) validates skill ↔ profile references but has no
  notion of agents or skill contracts.

## Phase 1 findings

- The disorder is **missing agent-routing**, not cleanup — the skill/profile layer is healthy.
- Skills fall into 5 clusters: core-lifecycle (22), context/research (3), domain reviewers (15),
  generic quality reviews (12), mindset manuals (9).
- 6 skills *look* like candidate agents (`sdd-orchestrate`, `review-all`, `graphify`,
  `architect-review`, `test-engineer`, `debugger`) but should stay skills — they are
  orchestration recipes, fan-out capabilities, analysis lenses, or procedures, not accountable actors.
- Highest-severity risk: reviewer skills route to `java-spring` / `api-design` subagents this
  repo does not ship.
- Mindset manuals are always-on behavioral injections; they belong to every agent, not to one.

## User stories

- **US-1** — As the maintainer, I want each skill to have a documented primary agent consumer,
  so I know who is accountable for running it.
- **US-2** — As the maintainer, I want domain/stack reviewers routed through one `domain-reviewer`
  agent, so the framework no longer depends on uncontrolled external subagents.
- **US-3** — As the maintainer, I want six agents with explicit allowed/forbidden actions,
  so no agent can commit, push, edit secrets, or bypass the spec workflow.
- **US-4** — As a downstream developer, I want `profiles.json` to express agent routing without
  breaking my existing skill installs, so upgrades are non-breaking.
- **US-5** — As the maintainer, I want `check-consistency` to validate agent and contract
  references, so drift is caught in CI, not in production.
- **US-6** — As a future-provider integrator, I want agent contracts described independently of
  Claude Code specifics, so the same responsibilities can map onto another provider later.
- **US-7** — As a new contributor, I want documentation that explains the difference between a
  skill and an agent, so I stop conflating the two.

## Functional requirements

- **FR-001:** Define exactly six agent contracts: `codebase-researcher`, `solution-architect`,
  `implementer`, `security-reviewer`, `domain-reviewer`, `final-conformance-reviewer`.
- **FR-002:** Each agent contract declares: responsibility, inputs, outputs, skills consumed,
  allowed actions, forbidden actions, and when-to-run.
- **FR-003:** No agent contract permits `git commit`, `git push`, `git add .`, editing secrets,
  or bypassing SPEC/PLAN/TASKS.
- **FR-004:** Add a lightweight, machine-readable skill contract to every SKILL.md (frontmatter
  or a standard section — whichever matches repo style), exposing at minimum: `category`,
  `inputs`, `outputs`, `side_effects`, `writes_code`, `writes_specs`, `analysis_only`,
  `primary_agent`, `secondary_agents`, `profile_scope`, `provider_specific`.
- **FR-005:** `domain-reviewer` becomes the documented owner of all stack/domain reviewer skills
  (Java/Spring, payments, event-driven/microservices, Next.js/Prisma, SEO/GEO/AEO/AI-visibility,
  and the generic api/backend/frontend/database/performance bases when used for domain review).
- **FR-006:** Remove or reroute the `java-spring` / `api-design` external-subagent references in
  `java-spring-reviewer`, `spring-boot-api-reviewer`, and `event-driven-reviewer` so they route
  to `domain-reviewer`.
- **FR-007:** Every skill's `primary_agent` maps to one of the six agents (or to the
  orchestration context for router/orchestrator skills — see FR-013).
- **FR-008:** `profiles.json` expresses per-profile agent routing (which agents a profile
  activates, and which reviewer skills `domain-reviewer` loads for that profile) without breaking
  existing `skills` installs.
- **FR-009:** `check-consistency` validates: (a) every skill's `primary_agent` resolves to a real
  agent or the orchestration context; (b) every profile-referenced agent exists on disk or in
  `plannedAgents`; (c) every reviewer routed to `domain-reviewer` exists.
- **FR-010:** `codebase-researcher` owns Graphify-based research; Graphify remains optional and
  degrades gracefully when absent.
- **FR-011:** Preserve Claude Code compatibility — agent files remain standard Claude agent
  Markdown with `name`/`description`/`model`/`tools` frontmatter; installer copy semantics unchanged.
- **FR-012:** Introduce no project-specific or private content; agents and contracts are generic.
- **FR-013:** `sdd-orchestrate`, `review-all`, `sdd`, `sdd-medium`, `sdd-full` remain
  orchestration skills/context, not dispatched agents; their `primary_agent` is the orchestration
  context, not one of the six.
- **FR-014:** Testing ownership is split per the Test strategy section — no dedicated test agent.
- **FR-015:** Ship documentation explaining skills vs agents and the routing model.

## Non-functional requirements

- **Performance:** No advanced parallelism required; `codebase-researcher` must avoid broad file
  reads (bounded context).
- **Security:** Forbidden-action lists are part of every agent contract; `security-reviewer` is a
  dedicated isolated reviewer.
- **Observability:** Consistency validation runs in CI (extends existing `check-consistency`).
- **Maintainability:** Contracts are lightweight; no over-engineering; must match current repo
  conventions (frontmatter/section style already used by skills).
- **Compatibility:** Non-breaking for downstream installs; provider-agnostic contract language.

## Agent model

Exactly six agents. All reviewers are analysis-only. None may commit, push, or edit secrets.

### 1. codebase-researcher
- **Responsibility:** Understand the affected code area; use Graphify when available; produce
  bounded context; avoid broad file reading; never modify application code.
- **Inputs:** Feature description, repo, optional `GRAPH_REPORT.md`.
- **Outputs:** Bounded reading list, impact summary, staleness flags.
- **Skills consumed:** `graphify`, `graphify-context`, `context-manager`, `scout`,
  `prototype` (LOGIC branch), `sdd-onboard` (read path).
- **Allowed:** Read, Grep, Glob, run Graphify.
- **Forbidden:** Modify application code; make architectural or implementation decisions.
- **When to run:** First, before planning or review on medium/large features.

### 2. solution-architect
- **Responsibility:** Review SPEC/PLAN; surface architectural decisions; block ambiguous
  implementation; **own test strategy before implementation**; update or propose DECISIONS.
- **Inputs:** Feature intent, research output.
- **Outputs:** SPEC/PLAN/TASKS/DECISIONS updates, blocking questions, pre-implementation test strategy.
- **Skills consumed:** `spec-create`, `spec-clarify`, `spec-plan`, `spec-update`, `spec-analyze`,
  `sdd-guardrails`, `architect-review`, `decision-mapping`, `decomposer`, `honest-advisor`,
  `test-engineer` (strategy use).
- **Allowed:** Write SPEC docs; propose decisions.
- **Forbidden:** Implement code; make silent decisions (must record in DECISIONS).
- **When to run:** After research, before implementation.

### 3. implementer
- **Responsibility:** Execute approved TASKS only; modify code within explicit boundaries; stop
  on missing decisions; add tests only when a task requires it; never commit or push.
- **Inputs:** Approved TASKS + DECISIONS + allowed-file boundaries.
- **Outputs:** Code diff + verification evidence.
- **Skills consumed:** `spec-implement`, `refactor-review`, `scope-keeper`, `scout`, `stopper`,
  `verifier`, `root-causer`, `debugger`.
- **Allowed:** Edit/Write within listed files; run verifications.
- **Forbidden:** Change unlisted files; make architectural decisions; commit/push; claim done unverified.
- **When to run:** After the plan is approved, task by task.

### 4. security-reviewer
- **Responsibility:** Review secrets, auth, payments, permissions, and sensitive data; produce
  severity-based findings; never modify code.
- **Inputs:** Diff, spec.
- **Outputs:** Security findings ranked by severity.
- **Skills consumed:** `security-review`, `spring-security-reviewer`,
  `nextjs-server-actions-reviewer`, `privacy-compliance-review`, `threat-modeler`, and the
  payment reviewers when money is involved.
- **Allowed:** Read-only analysis.
- **Forbidden:** Modify code.
- **When to run:** On any auth / user-data / payment / upload / secrets feature.

### 5. domain-reviewer
- **Responsibility:** Load profile-specific reviewer skills; review Java/Spring, payments,
  event-driven/microservices, Next.js, Prisma, SEO/GEO, etc.; **replace the external
  `java-spring` / `api-design` subagent coupling**; produce domain findings; own domain-specific
  test expectations; never modify code.
- **Inputs:** Diff, active profile.
- **Outputs:** Domain findings + domain-specific test expectations.
- **Skills consumed:** `java-spring-reviewer`, `spring-boot-api-reviewer`,
  `java-performance-reviewer`, `observability-reviewer`, `event-driven-reviewer`,
  `microservices-patterns-reviewer`, `stripe-payments-reviewer`, `payment-idempotency-reviewer`,
  `prisma-migration-reviewer`, `seo-review`, `aeo-review`, `geo-review`, `ai-visibility-review`,
  and generic bases (`api-review`, `backend-review`, `frontend-review`, `database-review`,
  `performance-review`) when used for domain review.
- **Allowed:** Read-only analysis; select reviewers by active profile.
- **Forbidden:** Modify code.
- **When to run:** Per active profile, after generic review.

### 6. final-conformance-reviewer
- **Responsibility:** Verify SPEC → PLAN → TASKS → DIFF → TESTS → REVIEW; validate evidence;
  **own final coverage/evidence validation**; produce a final conformance verdict; never modify code.
- **Inputs:** All spec docs + diff + test/coverage results.
- **Outputs:** Traceability verdict + PR description.
- **Skills consumed:** `spec-review`, `spec-analyze`, `spec-close`, `sdd-guardrails`,
  `qa-review`, `pr-description`.
- **Allowed:** Read-only analysis; produce verdict and PR text.
- **Forbidden:** Modify code; close on unresolved contradictions.
- **When to run:** Last, before PR.

**Unchanged:** `deep-reasoner` and `fast-worker` remain as-is (D009). `sdd-orchestrate` remains
the orchestration context that *dispatches* these agents; it is not one of them (D010).

## Skill contract model

Each SKILL.md exposes lightweight metadata — frontmatter keys or a standard `## Contract`
section, whichever matches the current per-skill style. Minimum fields:

| Field | Type | Meaning |
|---|---|---|
| `category` | enum | lifecycle / context-research / domain-reviewer / quality-review / mindset / orchestration |
| `inputs` | list | what the skill needs to run |
| `outputs` | list | what it produces |
| `side_effects` | enum | none / writes-specs / writes-code / writes-scratch |
| `writes_code` | bool | modifies application code |
| `writes_specs` | bool | modifies SPEC/PLAN/TASKS/DECISIONS |
| `analysis_only` | bool | produces findings only |
| `primary_agent` | string | the one accountable agent (or `orchestration-context`) |
| `secondary_agents` | list | agents that may also load it |
| `profile_scope` | list | profiles that ship it (or `all`) |
| `provider_specific` | bool | tied to a specific provider (Claude Code, etc.) |

Do not over-engineer. Fields must be derivable from the Phase 1 matrix and the agent model above.

## Profile routing model

- `profiles.json` keeps `skills` / `plannedSkills` exactly as today (non-breaking).
- Per-profile `agents` / `plannedAgents` slots (already present since 0.4.0) list which agents the
  profile activates. `core` activates all six; overlay profiles add domain reviewers to
  `domain-reviewer`'s scope.
- A per-profile routing map declares which reviewer skills `domain-reviewer` loads for that
  profile (e.g. `java-spring-backend` → `java-spring-reviewer`, `spring-boot-api-reviewer`,
  `java-performance-reviewer`, `observability-reviewer`). The exact JSON shape is a PLAN decision;
  it must be additive and ignored by older installers.
- `check-consistency` validates the routing map against skills on disk and agents on disk.

## Acceptance criteria

- **AC-001:** Six agent contracts are documented.
- **AC-002:** New agents are added under `agents/` only when implementation begins.
- **AC-003:** Each new agent has clear inputs, outputs, allowed actions, and forbidden actions.
- **AC-004:** Existing skills remain skills (none deleted, none converted to agents).
- **AC-005:** `domain-reviewer` is the documented owner of stack/domain reviewer skills.
- **AC-006:** Java/Spring/API reviewer references to external subagents are removed or rerouted to `domain-reviewer`.
- **AC-007:** Every skill has a documented primary agent consumer.
- **AC-008:** `profiles.json` can express agent routing without breaking existing skills.
- **AC-009:** `check-consistency` validates skill/profile/agent references.
- **AC-010:** Graphify remains optional and is owned by `codebase-researcher` for research.
- **AC-011:** Claude Code compatibility is preserved.
- **AC-012:** No project-specific private content is introduced.
- **AC-013:** No new agent can commit, push, edit secrets, or bypass specs.
- **AC-014:** `final-conformance-reviewer` can produce a traceability verdict.
- **AC-015:** Documentation explains the difference between skills and agents.

## Risks

- **R-1 (High):** Rerouting reviewer skills could change review behavior for downstream users who
  relied on the external subagents. *Mitigation:* keep reviewer skill bodies intact; change only
  the routing target; document in CHANGELOG.
- **R-2 (Medium):** Adding contract frontmatter to 61 skills risks breaking skill parsing if the
  schema is wrong. *Mitigation:* validate with `check-consistency` in CI before merge; roll out
  in a single mechanical pass with a schema test.
- **R-3 (Medium):** `profiles.json` routing changes could break older installers. *Mitigation:*
  additive-only fields; installer treats unknown keys as ignorable; version bump documented.
- **R-4 (Low):** Six agents may still overlap at the edges (e.g. security vs domain on payments).
  *Mitigation:* explicit forbidden/when-to-run boundaries; payments reviewed by `security-reviewer`
  for money-safety and `domain-reviewer` for processor idioms.
- **R-5 (Low):** Provider-agnostic language may drift toward Claude-specific coupling.
  *Mitigation:* `provider_specific` flag on skills; agent contracts describe responsibilities, not
  provider mechanics.

## Test strategy

No dedicated test-engineer agent. Testing ownership is split:

- **Pre-implementation test strategy → `solution-architect`** (via `test-engineer` skill).
- **Domain-specific test expectations → `domain-reviewer`.**
- **Final coverage / evidence validation → `final-conformance-reviewer`** (via `qa-review`).
- **`implementer` adds tests only when a task in TASKS.md explicitly requires it.**

Concrete gates for this spec:
- **Schema/unit:** `check-consistency` validates every skill contract parses and every
  `primary_agent` / profile agent / routed reviewer resolves.
- **Integration:** installer dry-run per profile confirms agents copy correctly and skills still link.
- **Regression:** existing `check-consistency` skill↔profile checks still pass unchanged.
- **Manual:** dispatch each of the six agents against a sample feature and confirm boundaries hold
  (no code edits from reviewers; implementer stops on missing decision).

## Rollback strategy

- All changes are additive documentation + JSON fields + one consistency check. Revert by:
  1. removing the six `agents/*.md` files,
  2. reverting the `agents`/routing additions in `profiles.json`,
  3. reverting the contract blocks in SKILL.md files,
  4. reverting the `check-consistency` extension.
- `deep-reasoner` / `fast-worker` and all skill bodies are untouched, so rollback cannot regress
  the existing orchestration path.
- No database, no runtime state, no downstream migration — rollback is a `git revert` of the
  feature branch.

## Assumptions

- The `agents` / `plannedAgents` slots in `profiles.json` (0.4.0) are the intended home for agent
  routing.
- Claude agent Markdown (`name`/`description`/`model`/`tools`) is the target agent file format.
- `check-consistency` (specs 007/012) is extensible to cover agents and contracts.

## Open questions

- ~~Exact skill-contract carrier: frontmatter keys vs a `## Contract` section.~~ **Resolved — D011:**
  a fenced YAML block under a standard `## SDD Contract` section inside each SKILL.md.
- ~~Exact JSON shape of the per-profile routing map.~~ **Resolved — D012:** an additive
  `agentRouting` map per profile in `profiles.json`, mapping agent names to consumed skills.

## Contracted services

Read `specs/SERVICES.md`. If absent: Contracted services not declared → all billable add-ons
treated as NOT contracted (conservative default). This spec is framework-internal and introduces
no billable service; the SEO/GEO/AEO/AI-visibility reviewers it routes remain gated on their
existing service contracts.
