# Messaging

> Copy this template into your project as `docs/MESSAGING.md` and fill it in.
> Claude Code reads this to understand broker topology, delivery-semantics expectations,
> and DLQ/retry policy. Essential for `/event-driven-reviewer` and `/spec-implement` when
> changes touch producers, consumers, the outbox pattern, or saga/compensation flows.

## Brokers in use

| Broker | Purpose | Version |
|---|---|---|
| Kafka | (e.g. domain events, event sourcing) | |
| RabbitMQ | (e.g. task queues, RPC-style async) | |
| ActiveMQ | (e.g. legacy JMS integration) | |

## Topic / queue inventory

| Name | Broker | Producer(s) | Consumer(s) | Delivery semantics | Ordering required |
|---|---|---|---|---|---|
| `orders.created` | Kafka | `order-service` | `billing-service`, `shipping-service` | At-least-once | Yes (per order ID) |

## Naming conventions

| Convention | Pattern | Example |
|---|---|---|
| Kafka topic | `<domain>.<event>` | `orders.created` |
| RabbitMQ exchange | `<domain>.exchange` | `orders.exchange` |
| RabbitMQ queue | `<domain>.<consumer>.queue` | `orders.billing.queue` |
| ActiveMQ destination | `<domain>.<queue-or-topic>` | `orders.legacy` |
| Consumer group (Kafka) | `<service-name>` | `billing-service` |

## Partitioning / consumer-group strategy

| Topic | Partition key | Partition count | Consumer group(s) | Concurrency |
|---|---|---|---|---|
| `orders.created` | Order ID | 12 | `billing-service` | 12 (1:1 with partitions) |

## Schema registry and evolution

| Property | Value |
|---|---|
| Format | Avro / Protobuf / JSON Schema |
| Registry | Confluent Schema Registry / Apicurio / none |
| Compatibility mode | BACKWARD / FORWARD / FULL |
| Breaking-change process | (e.g. new topic version, consumer migration window) |

## Delivery semantics decision record

| Topic/queue | Claimed semantics | Actual guarantee | Idempotency safeguard |
|---|---|---|---|
| `orders.created` | Exactly-once (business intent) | At-least-once (Kafka default) + idempotent consumer | Dedup on order ID in `billing-service` |

## Retry / backoff policy

| Topic/queue | Max attempts | Backoff strategy | Retryable errors | Non-retryable (→ DLQ immediately) |
|---|---|---|---|---|
| `orders.created` | 5 | Exponential + jitter, 1s→30s | Network, timeout, downstream 5xx | Schema violation, malformed payload |

## DLQ policy

| Topic/queue | DLQ destination | Alerting | Replay process |
|---|---|---|---|
| `orders.created` | `orders.created.DLQ` | PagerDuty on depth > 0 | Manual review + republish tool |

## Outbox pattern (if used)

| Property | Value |
|---|---|
| Outbox table | `outbox_events` |
| Relay mechanism | Poller / Debezium CDC |
| Cleanup/retention | Delete after N days processed |

## Saga / compensation (if used)

| Saga | Steps | Pattern | Orchestrator/coordinator | Compensation for each step |
|---|---|---|---|---|
| Order fulfillment | Reserve stock → Charge payment → Ship | Orchestration | `order-saga-service` | Release stock, refund payment |

## Correlation ID / trace propagation

| Property | Value |
|---|---|
| Header name | `X-Correlation-Id` / `traceparent` (W3C Trace Context) |
| Generated at | API gateway / first producer |
| Propagated through | Message headers, preserved across retries and DLQ |

## What NOT to assume

- Broker default configuration is rarely "exactly-once" — verify per topic/queue, don't assume.
- A DLQ declared in config is not the same as a DLQ that's monitored and replayable.
- Partition/queue count changes can silently break ordering assumptions — review before scaling.
