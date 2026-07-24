---
name: microservices-patterns-reviewer
description: Review cross-service architectural decisions in a microservices system — service boundaries, sync vs async communication, data ownership, distributed transactions, resilience patterns, deployment coupling, API ownership, and cross-service contract compatibility. Extends architect-review, api-review, database-review, and security-review.
triggers:
  - After `/architect-review` on a change spanning multiple services
  - When the user asks to "review our service boundaries", "check for a shared database", "review the circuit breaker config", or "check contract compatibility between services"
  - Triggered automatically by `/review-all` when the project has more than one deployable service, or a `pact`/`wiremock`/`spring-cloud-contract` dependency is detected
---

## SDD Contract

```yaml
category: domain-reviewer
inputs: [diff, architect-review-findings, api-review-findings, database-review-findings, security-review-findings]
outputs: [cross-service-findings]
side_effects: none
writes_code: false
writes_specs: false
analysis_only: true
primary_agent: domain-reviewer
secondary_agents: [solution-architect]
profile_scope: [messaging-event-driven]
provider_specific: false
```

# Microservices Patterns Reviewer

## Purpose

Catch cross-service architectural risks that a single-service review can't see: services that
have quietly become tightly coupled, a "distributed monolith" sharing one database, sync calls
where async would decouple failure domains, resilience patterns declared but not actually wired,
and contracts between services that drift without either side noticing. This skill **extends**
`architect-review` for the general architectural-analysis discipline (root causes, trade-offs,
file:line evidence), and adds microservices-specific pattern checks on top.

## Extends

- **Skill:** `architect-review` (general architectural analysis, root-cause discipline — run first
  for non-microservices-specific design questions)
- **Skill:** `api-review` (REST conventions, OpenAPI/DTO design, breaking-change detection — this
  skill's Contract compatibility section defers to it rather than re-checking the same ground)
- **Skill:** `database-review` (schema/migration/index correctness — this skill only adds the
  shared-database-vs-database-per-service *ownership* question, not schema quality itself)
- **Skill:** `security-review` (this skill only adds the service-to-service auth-boundary
  question — token/secret handling itself is `security-review`'s scope)

## What this skill checks

### Service boundaries and bounded contexts

- A service's responsibility maps to a coherent business capability / bounded context, not an
  arbitrary technical slice (e.g. a "utils-service" or "shared-service" with no clear ownership).
- Two services that always deploy together and always change together for the same reason are
  probably one bounded context split in two, not two real boundaries.
- Domain terms are not silently reused with different meanings across service boundaries (a
  classic bounded-context violation — e.g. "Order" meaning different things in two services
  without an explicit translation/anti-corruption layer).

### Sync vs async communication

- Synchronous (REST/gRPC) calls are used where the caller genuinely needs an immediate response
  or blocks on the result; asynchronous (event/message) communication is used where it doesn't —
  not the reverse (e.g. a chain of 4 synchronous calls where an event would decouple the services'
  failure domains and let them scale/deploy independently).
- Synchronous call chains don't create a hidden distributed monolith (service A must call B must
  call C synchronously to complete A's own request) without a documented reason.
- Where async is used, the caller doesn't secretly assume synchronous-like ordering/latency.

### Data ownership: shared database vs. database-per-service

- Each service owns its own data store; no other service reads or writes another service's
  tables/schema directly (the "shared database" anti-pattern — the single biggest source of
  hidden coupling in a microservices system).
- If a shared database genuinely exists (e.g. a legacy migration in progress), it's an explicit,
  documented, temporary exception — not silently normalized as the standard.
- Cross-service data needs are met via API calls or published events/read-models, not direct
  cross-schema joins or a shared connection string.
- (Schema quality, indexing, and migration correctness *within* a service's own database is
  `database-review`'s scope, not re-checked here.)

### Distributed transactions: 2PC vs. saga

- No use of two-phase commit (2PC) across independently-deployable services (it doesn't scale,
  and most modern brokers/datastores here don't support it cleanly) unless there's an explicit,
  justified exception.
- Where cross-service consistency is required, a saga (choreography or orchestration) is the
  chosen pattern, and the *architectural choice* is deliberate and documented — not accidental.
- (Whether a saga's compensating actions are correctly implemented — idempotent, persisted state,
  compensation-failure handling — is `event-driven-reviewer`'s scope; this skill only reviews
  *which pattern was chosen and why*, not the implementation correctness of a saga already coded.)

### Choreography vs. orchestration

- The choice between choreography (services react to each other's events, no central coordinator)
  and orchestration (a central saga orchestrator drives the flow) is explicit and matches the
  flow's complexity — choreography for simple, few-step flows; orchestration once a flow has
  several steps/branches/compensations that are hard to reason about as scattered event handlers.
- A choreography-based flow doesn't have an *implicit* orchestrator hiding in one service that
  everyone treats as the source of truth (the worst-of-both-worlds outcome).
- An orchestrator doesn't become a synchronous single point of failure for the whole flow.

### Resilience patterns: timeouts, retries, circuit breaker, bulkhead

- Every outbound synchronous call (REST/gRPC/DB) has an explicit timeout — no unbounded waits
  that can exhaust caller threads/connections during a downstream outage.
- Retries on outbound calls are bounded and backed off (not amplifying load on an already-struggling
  downstream service — "retry storms").
- A circuit breaker (Resilience4j, Spring Cloud Circuit Breaker, Hystrix-successor) wraps calls to
  unreliable/critical downstreams, with sane thresholds — not just declared as a dependency with
  no actual wiring around the call site.
- Bulkheads (separate thread/connection pools per downstream) isolate one failing dependency from
  starving resources needed for unrelated calls.
- Fallback behavior on circuit-open/timeout is defined and appropriate (fail fast with a clear
  error vs. degrade gracefully with cached/default data) — not silently swallowed into a generic
  500.

### Deployment coupling

- Services can be deployed independently — a change to one service doesn't require a
  simultaneous, coordinated deploy of another (a strong signal of a hidden shared boundary or
  a breaking, non-backward-compatible contract change).
- Shared libraries between services are versioned independently and don't force a lockstep
  release train across every consuming service for an unrelated change.
- Database migrations are backward-compatible with the previous service version, so a rolling
  deploy doesn't require all instances to update atomically.

### API ownership

- Each API/contract (REST, event schema, gRPC proto) has one clear owning service/team — not
  jointly "owned" by whoever last touched it, which is how contracts silently drift.
- Changes to an API are made by (or reviewed with) its owning service, not unilaterally by a
  consumer working around a gap.
- Deprecation of an API/event follows a documented process (version overlap period, consumer
  migration tracking) rather than being pulled the moment the owning team no longer needs it.

### Contract compatibility

Cross-service contract verification — **not** general OpenAPI/DTO review, which is `api-review`'s
job (see Extends above). This section only covers the parts `api-review` doesn't:

- **Consumer-driven contract testing** (Pact): consumer expectations are captured as contracts,
  published to a broker, and verified against the actual provider in CI — not just asserted in
  the consumer's own unit tests with a hand-rolled stub that can drift from the real provider.
- **Provider verification**: the provider runs contract-verification tests against every
  published consumer contract before a deploy, and a broken contract fails the build — it isn't
  discovered in production.
- **WireMock stubs**: stubs used in a consumer's tests are kept in sync with the real provider
  (ideally generated from or validated against the same OpenAPI spec / Pact contract), not
  hand-maintained fixtures that silently diverge from actual provider behavior over time.
- **OpenAPI-based compatibility and breaking changes**: this skill flags that a check is missing
  or a contract test is failing; the actual breaking-vs-non-breaking classification of a REST
  DTO/schema change is `api-review`'s checklist — **do not duplicate it here**, cross-reference it.
- A contract-testing setup exists at all for services with more than one consumer, proportional
  to the actual blast radius of an undetected break (a two-service internal integration may not
  need a full Pact broker; a widely-consumed public-facing service contract should have one).

## Output format

```markdown
## Microservices Patterns Review

**Verdict:** PASS | PASS WITH NOTES | FAIL

### Architecture summary

- Services involved:
- Communication pattern(s): sync / async / mixed
- Data ownership: database-per-service / shared database (exception documented: yes/no)
- Cross-service consistency pattern: saga (choreography/orchestration) / 2PC / n/a

### Findings

| # | Category | Severity | File:Line / Service | Finding | Action |
|---|---|---|---|---|---|
| 1 | Resilience | High | `payment-service` → `OrderClient.java:28` | No timeout on outbound call | Add explicit timeout + circuit breaker |

### Contract compatibility summary

- Contract testing tool in use: Pact / WireMock / Spring Cloud Contract / none
- Provider verification wired in CI: yes / no
- Breaking REST/DTO changes: see `api-review` output (not duplicated here)

### Required actions before merge

- [ ] (Blockers)
```

## What this skill does NOT do

- Does not perform general architectural analysis unrelated to service boundaries (that's
  `architect-review`).
- Does not re-check OpenAPI/DTO design, versioning, or breaking-change classification for a
  single REST contract (that's `api-review` — this skill's Contract compatibility section only
  adds the cross-service, consumer-driven-contract-testing layer on top).
- Does not review a saga/compensation flow's implementation correctness, retry/backoff, DLQ,
  idempotency, or broker-specific idioms (that's `event-driven-reviewer`).
- Does not review schema/migration/index quality within one service's own database (that's
  `database-review` — this skill only flags a shared-database *ownership* violation).
- Does not review token/secret handling itself (that's `security-review` — this skill only flags
  a missing or unclear service-to-service auth boundary).
- Does not create a standalone `contract-testing-reviewer` skill — see
  `specs/features/003-phase3-event-driven-microservices/DECISIONS.md` D002.
- Does not review payment-specific workflows (a future `payments-fintech` profile concern).
- Does not modify code.
