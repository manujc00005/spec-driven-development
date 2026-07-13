# Feature Spec: Phase 3 — Messaging / event-driven / microservices patterns

## Status

Done

## Problem

The SDD framework has no review intelligence for event-driven systems or distributed
microservices patterns. Phase 2 shipped Java/Spring-specific reviewers (`java-spring-reviewer`,
`spring-boot-api-reviewer`, `spring-security-reviewer`, `java-performance-reviewer`), but none of
them cover Kafka/RabbitMQ/ActiveMQ producers/consumers, delivery-semantics guarantees, the outbox
pattern, saga/compensation flows, or cross-service architectural concerns (service boundaries,
sync vs async communication, distributed transactions, resilience patterns, contract
compatibility). `profiles.json` already declares a `messaging-event-driven` profile, but every
skill under it is a `plannedSkills` placeholder — nothing is shipped.

## Goal

Ship exactly 2 review skills, 2 context templates, and updated `profiles.json` entries that make
the `messaging-event-driven` profile a real, activatable **optional profile** — conceptually
layered on top of `java-spring-backend` (its skills assume a Java/Spring service underneath) but
installed via an explicit, manual profile combination, not automatically bundled — without
duplicating what `backend-review`, `api-review`, `database-review`, `security-review`,
`architect-review`, or `test-engineer` already cover. Keep `README.md` (and `docs/INSTALL.md` if
it goes stale) in sync with the new skill/template/profile counts.

## Non-goals

- Standalone `kafka-reviewer`, `rabbitmq-reviewer`, `outbox-pattern-reviewer`,
  `saga-orchestration-reviewer` skills — consolidated into `event-driven-reviewer` instead
  (see DECISIONS D001).
- Standalone `contract-testing-reviewer` skill — folded into `microservices-patterns-reviewer`
  as a section (see DECISIONS D002).
- `observability-reviewer` skill — stays in `plannedSkills`, deferred (correlation IDs / trace
  propagation are reviewed as checks inside `event-driven-reviewer`, but a dedicated
  observability-stack reviewer is out of scope here).
- `payments-fintech` profile (`stripe-payments-reviewer`, `payment-idempotency-reviewer`) —
  separate profile, separate future phase. Not touched.
- New hooks (`messaging-review-reminder`, `openapi-contract-reminder` stay in `plannedHooks`).
  No hook files are created or modified in this phase.
- Kubernetes/deployment reviewer — still a future phase.
- Changing the default profile (`java-spring-backend` stays default) or primary build tool
  (Maven stays primary).
- Enabling `blockchain-crypto` (`disabled: true` untouched).
- Modifying `C:\ProgramData\ClaudeConfig`.
- Installing dependencies, running builds/tests, or committing.
- Phase 4 (not started).

## Functional requirements

### Skills

- FR-001: `skills/event-driven-reviewer/SKILL.md` — reviews Kafka/RabbitMQ/ActiveMQ
  producer/consumer code for: delivery semantics (at-least-once vs exactly-once expectations vs
  what the code actually guarantees), idempotent consumer design, retry/backoff configuration,
  DLQ wiring and poison-message handling, ordering guarantees (partitioning/single-active-consumer),
  schema evolution (Avro/Protobuf/JSON Schema compatibility), correlation ID propagation and
  distributed trace context, the transactional outbox pattern, and saga/compensation flows.
  **Extends** `backend-review` + the `java-spring` agent for Spring Kafka/AMQP idioms; **extends**
  `database-review` for the outbox table's transactional-write guarantees.
- FR-002: `skills/microservices-patterns-reviewer/SKILL.md` — reviews cross-service architectural
  decisions: service boundaries and bounded contexts, sync vs async communication choice,
  shared-database anti-pattern vs database-per-service, distributed transactions (2PC vs saga),
  choreography vs orchestration, timeouts/retries/circuit-breaker/bulkhead resilience patterns,
  deployment coupling, and API ownership. Includes a **Contract compatibility** section covering
  Pact/WireMock consumer-driven contract testing and provider/consumer verification workflow — this
  section explicitly defers pure OpenAPI/DTO/breaking-change mechanics to `api-review` rather than
  re-implementing them (see DECISIONS D002). **Extends** `architect-review` + `api-review` +
  `database-review` (shared-DB vs DB-per-service) + `security-review` (service-to-service auth
  boundaries).

### Templates

- FR-003: `docs/_templates/MESSAGING.md` — broker topology (Kafka topics/partitions or
  RabbitMQ/ActiveMQ exchanges/queues), naming conventions, consumer-group strategy, schema
  registry, DLQ policy, retry/backoff configuration, and a delivery-semantics decision record
  placeholder.
- FR-004: `docs/_templates/MICROSERVICES_PATTERNS.md` — service boundary map, sync/async
  communication matrix, saga/orchestration notes placeholder, resilience policy
  (timeouts/retries/circuit-breaker/bulkhead configuration), and contract-testing setup
  (Pact broker / WireMock) placeholder.

### profiles.json

- FR-005: Update the `messaging-event-driven` profile — move `event-driven-reviewer` and
  `microservices-patterns-reviewer` from `plannedSkills` to `skills`; remove `kafka-reviewer`,
  `rabbitmq-reviewer`, `outbox-pattern-reviewer`, `saga-orchestration-reviewer` from
  `plannedSkills` (superseded, see D001); move `MESSAGING.md` and `MICROSERVICES_PATTERNS.md`
  from `plannedTemplates` to `templates`. `hooks`/`plannedHooks` stay unchanged — no hook ships
  this phase.
- FR-006: Update the `java-spring-backend` profile — remove `contract-testing-reviewer` from
  `plannedSkills` (superseded, see D002) and correct the profile `note` field. Leave
  `observability-reviewer` in `plannedSkills` (deferred, out of scope).

### Documentation sync

- FR-007: Update `README.md` so it stays accurate once FR-001–FR-006 ship: skill count
  (40 → 42), the `skills/` **and** `docs/_templates/` entries in the repository-structure tree
  (the tree currently lists template files by name, e.g. `TESTING.md`/`SECURITY.md`/
  `DEPLOYMENT.md` — `MESSAGING.md` and `MICROSERVICES_PATTERNS.md` must be added the same way),
  the "Status of this repository" checklist (including its `docs/_templates/` file-name list),
  the "Roadmap" completed/planned lists, and the "Profiles" table/section — without changing what
  it already correctly says about `blockchain-crypto` staying disabled, `java-spring-backend`
  staying the default profile, or Graphify's status (none of those change in this phase).
- FR-008: Update `docs/INSTALL.md` **only** where it goes factually stale because of this phase —
  specifically, its "What you'll see for planned items" example currently says
  `messaging-event-driven` "mostly consists of Phase 3 candidates that don't exist in the repo
  yet"; after FR-001–FR-005 ship, 2 skills and 2 templates under that profile do exist, and only
  the hook (`messaging-review-reminder`) remains planned. If no other part of `docs/INSTALL.md` is
  actually inaccurate, this is the only edit made there.

## Acceptance criteria

- AC-001: Both new skills have an explicit "Extends" section naming the base skills and
  supporting reviewers they build on, and do not re-implement checks those already perform.
- AC-002: `event-driven-reviewer` explicitly covers every bullet requested: Kafka, RabbitMQ,
  ActiveMQ, producers/consumers, delivery semantics, at-least-once vs exactly-once, idempotent
  consumers, retry/backoff, DLQ, poison messages, ordering, schema evolution, correlation IDs,
  trace propagation, outbox, saga/compensation.
- AC-003: `microservices-patterns-reviewer` explicitly covers every bullet requested: service
  boundaries, bounded contexts, sync vs async communication, shared-database risk,
  database-per-service, distributed transactions, saga vs orchestration, timeouts, retries,
  circuit breaker, bulkhead, deployment coupling, API ownership, contract compatibility
  (Pact, WireMock, OpenAPI compatibility, provider/consumer contracts, backward compatibility,
  breaking changes).
- AC-004: No `kafka-reviewer`, `rabbitmq-reviewer`, `outbox-pattern-reviewer`,
  `saga-orchestration-reviewer`, or `contract-testing-reviewer` skill directory is created.
- AC-005: `profiles.json` — `messaging-event-driven` lists exactly 2 shipped skills and 2 shipped
  templates, 0 shipped hooks; `java-spring-backend.plannedSkills` no longer lists
  `contract-testing-reviewer`; `blockchain-crypto.disabled` stays `true`;
  `defaults.profile` stays `java-spring-backend`; `defaults.buildTool` stays `maven`.
- AC-006: Templates are documentation/context only — no executable logic — following the same
  placeholder structure as `TESTING.md`/`SECURITY.md`/`DEPLOYMENT.md` from Phase 2.
- AC-007: No hook file (`.sh` or `.ps1`) is created or modified by this feature.
- AC-008: No secrets, PII, or hardcoded local paths in any new/modified file.
- AC-009: `C:\ProgramData\ClaudeConfig` is untouched; nothing is committed.
- AC-010: `README.md`'s skill count, repository-structure tree, "Status of this repository"
  checklist, and "Roadmap" section all reflect the 2 new skills and 2 new templates shipped by
  this phase. `blockchain-crypto` is still described as disabled by default, `java-spring-backend`
  is still described as the default profile, and the Graphify integration status line is
  unchanged.
- AC-011: `README.md` and `docs/INSTALL.md` describe `messaging-event-driven` accurately per the
  installer's actual behavior (verified against `install.sh`/`install.ps1`): it is an **optional**
  profile that must be explicitly requested; passing a `--profile`/`-Profile` flag does **not**
  also install the default profile unless it is explicitly included in the same flag (e.g.
  `--profile java-spring-backend,messaging-event-driven`). No wording implies automatic bundling.
