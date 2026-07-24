---
name: event-driven-reviewer
description: Review Kafka/RabbitMQ/ActiveMQ producer and consumer code for delivery-semantics correctness, idempotent consumers, retry/backoff, DLQ and poison-message handling, ordering guarantees, schema evolution, correlation ID/trace propagation, the transactional outbox pattern, and saga/compensation flows. Extends backend-review and database-review, and is consumed by the domain-reviewer agent for Spring Kafka/AMQP idioms.
triggers:
  - After `/backend-review` when Kafka, RabbitMQ, or ActiveMQ producer/consumer code changes
  - When the user asks to "review my Kafka consumer", "check message idempotency", "review the outbox implementation", or "review the saga/compensation flow"
  - Triggered automatically by `/review-all` when broker client dependencies or `@KafkaListener`/`@RabbitListener`/`@JmsListener` annotations are detected
---

## SDD Contract

```yaml
category: domain-reviewer
inputs: [diff, backend-review-findings, database-review-findings]
outputs: [messaging-findings]
side_effects: none
writes_code: false
writes_specs: false
analysis_only: true
primary_agent: domain-reviewer
secondary_agents: [solution-architect]
profile_scope: [messaging-event-driven]
provider_specific: false
```

# Event-Driven Reviewer

## Purpose

Catch messaging- and event-driven-specific correctness issues that generic `backend-review`
misses: wrong delivery-semantics assumptions, non-idempotent consumers, missing retry/DLQ
handling, silent reordering, schema-evolution breaks, lost trace context, and outbox/saga
implementations that don't actually guarantee what they claim to. This skill **extends**
`backend-review` — run that first for general service/data-access quality, then this for
messaging depth. It also **extends `database-review`** specifically for the outbox table's
transactional-write guarantees (the write itself is a normal DB write; this skill only adds the
messaging-specific correctness questions on top).

This skill deliberately covers **Kafka, RabbitMQ, and ActiveMQ under one lens**, not as three
separate reviewers: the broker changes the API surface, not the review question. See
`DECISIONS.md` D001 in `specs/features/003-phase3-event-driven-microservices/` for why.

## Extends

- **Skill:** `backend-review` (general service/data-access quality — run first)
- **Skill:** `database-review` (outbox table's transactional-write guarantees only)
- **Agent:** `domain-reviewer` (Spring Kafka / Spring AMQP / JMS idioms, `@KafkaListener`,
  `@RabbitListener`, `@JmsListener`, `KafkaTemplate`, `RabbitTemplate`)

## What this skill checks

### Broker-specific idioms (Kafka / RabbitMQ / ActiveMQ)

- **Kafka:** producer `acks` config (`acks=all` for durability vs `acks=1`/`0`), `enable.idempotence`
  for idempotent producers, consumer `enable.auto.commit` vs manual offset commit, `max.poll.records`
  and processing time vs `max.poll.interval.ms` (silent rebalance/duplicate delivery risk),
  `@KafkaListener` concurrency vs partition count.
- **RabbitMQ:** publisher confirms (`ConfirmCallback`) and mandatory/returned-message handling,
  consumer `ackMode` (`AUTO`/`MANUAL`/`NONE`), manual ack placed *after* successful processing (not
  before), prefetch count (`basicQos`) tuned for throughput vs fairness, durable queues/exchanges
  for anything that must survive a broker restart.
- **ActiveMQ:** session `acknowledgeMode` (`AUTO_ACKNOWLEDGE` vs `CLIENT_ACKNOWLEDGE` vs
  `SESSION_TRANSACTED`), redelivery policy (`maximumRedeliveries`, backoff multiplier), consumer
  prefetch (`ActiveMQPrefetchPolicy`), persistent vs non-persistent delivery mode.
- Producer/consumer code that hardcodes broker-specific behavior without a documented reason
  (e.g. relying on Kafka partition-key ordering when the topic is actually consumed by a
  concurrent, non-keyed consumer group).

### Delivery semantics: at-least-once vs exactly-once

- What the code's comments/naming/tests *claim* ("exactly-once processing") vs what the actual
  configuration *guarantees* (most broker+consumer combinations here are at-least-once by
  default; true exactly-once requires transactional producers + idempotent consumers, or
  Kafka transactions end-to-end).
- Silent assumption of exactly-once delivery with no idempotency safeguard downstream — this is
  the most common and most dangerous gap.
- Whether "effectively exactly-once" (at-least-once delivery + idempotent consumer) is being used
  correctly instead of chasing unnecessary broker-level exactly-once guarantees.

### Idempotent consumers

- A deduplication mechanism exists for redelivered messages: dedup table/key (message ID,
  business key, or hash), unique constraint on the write, or upsert semantics.
- The idempotency key is derived from message content/business identity, not from
  broker-assigned metadata that changes on redelivery (e.g. a fresh Kafka offset after a
  rebalance).
- Side effects performed before the idempotency check (e.g. an outbound HTTP call or a second
  publish) that would duplicate on redelivery even if the DB write itself is deduplicated.
- Idempotency window/retention: does the dedup record expire before a plausible redelivery could
  still arrive (e.g. after a long consumer outage)?

### Retry/backoff and DLQ / poison messages

- Retry is bounded (max attempts) and uses backoff (fixed, exponential, or exponential+jitter) —
  not a tight retry loop that can overwhelm the broker or a downstream dependency.
- Retryable errors (transient: network, timeout, downstream 5xx) are distinguished from
  non-retryable errors (poison message: malformed payload, schema violation, business-rule
  violation that will never succeed on retry).
- A DLQ (or dead-letter exchange/queue) is actually wired for the topic/queue in question — not
  just declared in config with nothing consuming or alerting on it.
- Poison messages don't block the partition/queue (e.g. a single malformed Kafka message stalling
  an entire partition because the consumer keeps crashing and re-polling the same offset).
- DLQ messages retain enough context (original headers, correlation ID, failure reason, attempt
  count) to be replayed or triaged without re-deriving the failure from scratch.

### Ordering guarantees

- Where ordering matters (state transitions, financial events), messages for the same logical
  entity are routed to preserve order: Kafka partitioning key = the entity's identity, RabbitMQ
  single active consumer / single queue per ordered stream, ActiveMQ exclusive consumer.
- Consumer-side concurrency doesn't silently break producer-side ordering guarantees (e.g. a
  Kafka topic partitioned by order ID, but the consumer's concurrency setting processes multiple
  partitions' messages in a shared thread pool without partition-affinity).
- Reordering caused by differential retry delay (message B succeeds while message A for the same
  entity is still retrying) is either prevented or explicitly tolerated with a documented reason.

### Schema evolution

- Schema changes (Avro/Protobuf/JSON Schema) are backward- and/or forward-compatible per the
  registry's configured compatibility mode — not just "it happens to still deserialize today."
- New fields are optional / have defaults; required-field additions or type changes are treated as
  breaking (matches the same breaking-change discipline `api-review` applies to REST DTOs).
- Consumers tolerate unknown fields (forward compatibility) rather than failing hard on an
  unrecognized property.
- A schema registry (or equivalent versioning discipline) is actually enforced in CI/deploy, not
  just aspirational.

### Correlation IDs and trace propagation

- A correlation/trace ID is generated or extracted at the point a message enters the system and
  propagated through message headers (not just logged locally and dropped).
- Downstream consumers/producers propagate the same correlation ID onward instead of minting a
  new one, so a single business transaction is traceable end-to-end across services and brokers.
- Correlation IDs survive retries and DLQ routing (the ID on a replayed DLQ message still matches
  the original).
- This skill checks that propagation *code* exists and is wired correctly; it does not evaluate
  the observability/tracing *infrastructure* itself (collectors, dashboards, sampling) — that is
  `observability-reviewer`'s scope (currently `plannedSkills`, not yet shipped).

### Transactional outbox pattern

- The business-data write and the outbox-row insert happen in the **same local database
  transaction** — the entire point of the pattern; if they're in separate transactions, the
  pattern isn't actually implemented, just resembled.
- A relay/poller (or CDC mechanism, e.g. Debezium) actually publishes outbox rows to the broker
  and marks them processed/deletes them — an outbox table that nothing drains is a silent data
  leak, not a working outbox.
- The relay is itself at-least-once and idempotent-safe on the publish side (a crash between
  publish and mark-processed must not lose the row or duplicate indefinitely without downstream
  dedup).
- Outbox row cleanup/retention policy exists (unbounded growth of a "processed" outbox table).
- The DB-write half of this (schema, indexing, transaction demarcation) is `database-review`'s
  concern; this skill only checks the messaging-specific guarantee the pattern exists to provide.

### Saga / compensation flows

- Each forward step that can fail *after* a prior step succeeded has a corresponding compensating
  action defined (not just a happy-path chain with no rollback story).
- Compensating actions are idempotent and safe to run more than once (a saga coordinator retry
  must not double-refund, double-cancel, etc.).
- Saga state (which steps completed, which compensations are pending) is persisted somewhere
  durable, not held only in memory (a crashed orchestrator must be able to resume or safely
  abandon a saga).
- Partial-failure and compensation-failure ("what if the compensation itself fails?") are
  explicitly handled — at minimum surfaced for manual intervention, not silently swallowed.
- This skill reviews the **implementation correctness** of a saga/compensation flow already in
  code. The architectural decision of *whether* to use a saga vs. a distributed transaction, and
  *choreography vs. orchestration*, is `microservices-patterns-reviewer`'s scope — the two skills
  are complementary, not overlapping.

## Output format

```markdown
## Event-Driven Review

**Verdict:** PASS | PASS WITH NOTES | FAIL

### Delivery semantics summary

- Broker(s) involved:
- Claimed semantics: at-least-once / exactly-once / effectively-exactly-once
- Actual guarantee based on config: (assessment)
- Idempotency safeguard present: yes / no / partial

### Findings

| # | Category | Severity | File:Line | Finding | Action |
|---|---|---|---|---|---|
| 1 | Idempotency | High | `OrderConsumer.java:52` | No dedup key on redelivery | Add dedup table keyed by message business ID |

### Outbox / saga summary (if applicable)

- Outbox write + business write in same transaction: yes / no / n/a
- Saga compensations defined for every forward step: yes / no / n/a

### Required actions before merge

- [ ] (Blockers)
```

## What this skill does NOT do

- Does not re-check general service/data-access quality (that's `backend-review`).
- Does not review the outbox table's schema/indexing/migration itself (that's `database-review`).
- Does not decide saga vs. 2PC vs. choreography vs. orchestration at the architecture level
  (that's `microservices-patterns-reviewer`).
- Does not review REST/OpenAPI contract compatibility (that's `api-review`, or
  `microservices-patterns-reviewer`'s Contract compatibility section for cross-service
  consumer-driven contracts).
- Does not review the observability/tracing stack itself, only whether propagation code exists
  (a dedicated `observability-reviewer` is `plannedSkills`, not yet shipped).
- Does not review payment-specific idempotency keys (that's a future `payments-fintech` profile
  concern — this skill's "idempotent consumers" section is scoped to message redelivery, not
  payment-API idempotency).
- Does not modify code.
