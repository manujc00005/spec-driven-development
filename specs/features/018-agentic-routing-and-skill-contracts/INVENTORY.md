# Phase 1 Inventory: Skill Classification & Agent Routing Matrix

Durable source for the Phase 2 agent contracts and skill-contract population (T004–T010).
Produced by the Phase 1 skill-inventory pass; persisted here per T001 (covers AC-007).

## Skill categories (61 skills, 5 clusters)

- **Core SDD Workflow** (22): sdd, sdd-medium, sdd-full, sdd-orchestrate, sdd-onboard,
  project-init, spec-create, spec-clarify, spec-plan, spec-analyze, spec-implement, spec-review,
  spec-close, spec-status, spec-update, spec-resume, sdd-guardrails, review-all, pr-description,
  handoff, decision-mapping, prototype.
- **Context / Research Capability** (3): graphify, graphify-context, context-manager.
- **Domain Reviewer Capability** (15): java-spring-reviewer, spring-boot-api-reviewer,
  spring-security-reviewer, java-performance-reviewer, observability-reviewer,
  event-driven-reviewer, microservices-patterns-reviewer, stripe-payments-reviewer,
  payment-idempotency-reviewer, prisma-migration-reviewer, nextjs-server-actions-reviewer,
  seo-review, aeo-review, geo-review, ai-visibility-review.
- **Quality / QA Capability** (12): qa-review, security-review, performance-review, api-review,
  backend-review, frontend-review, database-review, privacy-compliance-review, architect-review,
  refactor-review, test-engineer, debugger.
- **Mindset Manuals — Provider-Specific / Claude Adapter** (9): communicator, decomposer,
  honest-advisor, root-causer, scope-keeper, scout, stopper, threat-modeler, verifier.

No orphan skills. No broken profile references. All `plannedSkills` arrays empty (verified against
`profiles.json` during Phase 1).

## Skill → Agent matrix

`primary_agent` values use the six Phase 2 agents plus `orchestration-context` for
router/orchestrator skills (per D010). Mindset manuals list `secondary_agents: all` (consumed by
every agent, owned by none).

| Skill | primary_agent | secondary_agents | standalone? | Notes |
|---|---|---|---|---|
| sdd | orchestration-context | — | yes | Router to medium/full |
| sdd-medium | orchestration-context | — | yes | Explicit-force escape |
| sdd-full | orchestration-context | — | yes | Explicit-force escape |
| sdd-orchestrate | orchestration-context | — | yes | Dispatches deep-reasoner/fast-worker; not itself dispatched (D010) |
| sdd-onboard | codebase-researcher | solution-architect | yes | Overlaps project-init (fork: has code → onboard; empty → init) |
| project-init | solution-architect | — | yes | Greenfield interview |
| spec-create | solution-architect | — | yes | Includes auto-clarify |
| spec-clarify | solution-architect | — | yes | — |
| spec-plan | solution-architect | — | yes | — |
| spec-analyze | solution-architect | final-conformance-reviewer | yes | Overlaps sdd-guardrails |
| spec-implement | implementer | — | yes | Only code-writing lifecycle skill |
| spec-review | final-conformance-reviewer | solution-architect | yes | Conformance vs qa-review's functional axis |
| spec-close | final-conformance-reviewer | — | yes | — |
| spec-status | (any) | — | yes | — |
| spec-update | solution-architect | — | yes | — |
| spec-resume | (any) | — | yes | Pure alias of spec-status |
| sdd-guardrails | solution-architect | final-conformance-reviewer | yes | Global consistency gate |
| review-all | orchestration-context | — | yes | Dispatches domain/security/final agents |
| pr-description | final-conformance-reviewer | — | yes | — |
| handoff | (human, manual) | — | yes | `disable-model-invocation: true` |
| decision-mapping | solution-architect | — | yes | `disable-model-invocation: true`; overlaps prototype |
| prototype | codebase-researcher | solution-architect | yes | `disable-model-invocation: true`; LOGIC branch → researcher |
| graphify | codebase-researcher | — | yes | Already spawns its own subagents; don't double-nest |
| graphify-context | codebase-researcher | solution-architect | yes | Requires GRAPH_REPORT.md |
| context-manager | codebase-researcher | — | yes | No-graph fallback vs graphify-context |
| java-spring-reviewer | domain-reviewer | final-conformance-reviewer | yes | External subagent ref rerouted here (D006) |
| spring-boot-api-reviewer | domain-reviewer | final-conformance-reviewer | yes | External subagent ref rerouted here (D006) |
| spring-security-reviewer | security-reviewer | domain-reviewer | yes | Extends security-review |
| java-performance-reviewer | domain-reviewer | — | yes | Extends performance-review |
| observability-reviewer | domain-reviewer | — | yes | Extends backend-review |
| event-driven-reviewer | domain-reviewer | solution-architect | yes | External subagent ref rerouted here (D006) |
| microservices-patterns-reviewer | domain-reviewer | solution-architect | yes | Extends architect+api+db+security |
| stripe-payments-reviewer | domain-reviewer | security-reviewer | yes | Overlaps payment-idempotency-reviewer (layering, not duplication) |
| payment-idempotency-reviewer | domain-reviewer | security-reviewer | yes | Processor-agnostic |
| prisma-migration-reviewer | domain-reviewer | — | yes | Extends database-review |
| nextjs-server-actions-reviewer | security-reviewer | domain-reviewer | yes | Extends security+backend |
| seo-review / aeo-review / geo-review / ai-visibility-review | domain-reviewer | — | yes | Billable-gated (seo-geo-addon) |
| qa-review | final-conformance-reviewer | domain-reviewer | yes | Post-impl audit |
| security-review | security-reviewer | domain-reviewer | yes | Base for spring-security, nextjs-actions |
| performance-review | domain-reviewer | — | yes | Base for java-performance-reviewer |
| api-review | domain-reviewer | — | yes | Base for spring-boot-api-reviewer |
| backend-review | domain-reviewer | — | yes | Base for several extenders |
| frontend-review | domain-reviewer | — | yes | Base for nextjs/seo |
| database-review | domain-reviewer | — | yes | Base for prisma-migration-reviewer |
| privacy-compliance-review | security-reviewer | domain-reviewer | yes | Routes to external gdpr-spain (unchanged; not in D006 scope) |
| architect-review | solution-architect | domain-reviewer | yes | Analysis lens, not a responsibility owner |
| refactor-review | implementer | final-conformance-reviewer | yes | — |
| test-engineer | solution-architect | domain-reviewer, final-conformance-reviewer | yes | Strategy skill — NOT an agent (D004); consumed at multiple points per D005 |
| debugger | implementer | — | yes | Procedure, not a responsibility owner |
| communicator | (all agents) | — | yes | Mindset |
| decomposer | solution-architect | implementer | yes | Mindset |
| honest-advisor | (all agents) | — | yes | Mindset |
| root-causer | implementer | — | yes | Mindset |
| scope-keeper | implementer | — | yes | Mindset |
| scout | codebase-researcher | implementer | yes | Mindset |
| stopper | implementer | (all agents) | yes | Mindset |
| threat-modeler | security-reviewer | implementer | yes | Mindset |
| verifier | implementer | final-conformance-reviewer | yes | Mindset |

## Keep-as-skills rationale (do not convert to agents)

- **All 15 domain reviewers** — reusable, profile-selected checklists → consumed by `domain-reviewer`
  (security-flavored ones also by `security-reviewer`).
- **All 12 generic quality reviews** — composable review lenses, not owners of a deliverable.
- **All 9 mindset manuals** — behavioral injections with no artifact and no isolated
  responsibility; converting them would fragment behavior across process boundaries.
- **debugger** — a procedure any agent runs, not an owner of a deliverable.
- **test-engineer** — the skill stays; `solution-architect` (pre-impl strategy),
  `domain-reviewer` (domain expectations), and `final-conformance-reviewer` (coverage validation)
  consume it at different points. No dedicated agent (D004/D005).
- **architect-review** — an analysis lens consumed by `solution-architect`.
- **graphify** — already implements its own subagent fan-out; wrapping it in an agent would
  double-nest dispatch.
- **review-all, sdd-orchestrate** (and sdd/sdd-medium/sdd-full) — orchestration recipes the
  top-level context follows to dispatch agents; an orchestrator that is itself a dispatched
  subagent cannot cleanly spawn siblings (D010).
- **All spec-* lifecycle skills** — deterministic document operations consumed by
  `solution-architect` / `implementer` / `final-conformance-reviewer`.

## Architecture risks carried forward from Phase 1

| Risk | Severity | Status in Phase 2 |
|---|---|---|
| Reviewer skills route to subagents this repo doesn't ship (`java-spring`, `api-design`) | High | Addressed by D006 / FR-006 / T011 |
| No input/output contracts on any skill | High | Addressed by D011 / FR-004 / T002–T003, T010 |
| Only 2 agents, consumed by 1 skill | High | Addressed by FR-001–FR-002 / T004–T009 |
| `core` profile overloaded (41 skills: lifecycle + generic reviews + mindset + orchestrators) | Medium | Not addressed in Phase 2 — deliberately deferred, no file moves planned |
| No execution lifecycle / evidence of use | Medium | Partially addressed — final-conformance-reviewer produces a verdict (AC-014); no run-record store planned in this phase |
| Graphify not enforced as first research step | Medium | Addressed by D007 — owned by codebase-researcher, stays optional (not mandatory, per Non-goals) |
| context-manager vs graphify-context precedence unstated | Low | To be documented inside codebase-researcher's contract (T004) |
| `spec-resume` pure alias of `spec-status` | Low | Not addressed — harmless, deferred to a future major version |
