# Microservices Patterns

> Copy this template into your project as `docs/MICROSERVICES_PATTERNS.md` and fill it in.
> Claude Code reads this to understand service boundaries, communication patterns, and
> resilience/contract-testing setup. Essential for `/microservices-patterns-reviewer` and
> `/spec-implement` when a change spans more than one service.

## Service boundary map

| Service | Bounded context / responsibility | Owns data store | Team/owner |
|---|---|---|---|
| `order-service` | Order lifecycle | `orders_db` | Commerce team |
| `billing-service` | Payment capture, invoicing | `billing_db` | Payments team |

## Communication matrix

| From | To | Type | Protocol | Reason |
|---|---|---|---|---|
| `order-service` | `billing-service` | Async (event) | Kafka `orders.created` | Decouple failure domains, billing can lag |
| `order-service` | `inventory-service` | Sync (REST) | HTTP | Caller needs immediate stock confirmation |

## Data ownership

| Service | Database | Shared with | Exception documented? |
|---|---|---|---|
| `order-service` | `orders_db` (PostgreSQL) | None | — |
| (legacy example) `reporting-service` | `orders_db` (read-only) | `order-service` | Yes — see DECISIONS.md D0xx, migration planned |

## Distributed transaction / saga strategy

| Flow | Pattern | Choreography or orchestration | Coordinator (if orchestrated) |
|---|---|---|---|
| Order fulfillment | Saga | Orchestration | `order-saga-service` |
| Inventory reservation | Saga | Choreography | — (services react to events directly) |

> Implementation correctness of each saga's compensating actions (idempotency, persisted state,
> compensation-failure handling) is reviewed by `event-driven-reviewer`, not here — this table
> only records the architectural choice.

## Resilience policy

| Caller → Callee | Timeout | Retry (max, backoff) | Circuit breaker | Bulkhead | Fallback |
|---|---|---|---|---|---|
| `order-service` → `inventory-service` | 2s | 3, exponential | Resilience4j, 50% failure rate opens | Dedicated thread pool (20) | Return cached availability, flag stale |

## Deployment coupling

| Property | Value |
|---|---|
| Can services deploy independently? | Yes / No (explain any coordinated-release exceptions) |
| Shared libraries | (name, versioning policy) |
| Migration backward-compatibility policy | N-1 service version must still work against current schema |

## API ownership

| API / contract | Owning service | Consumers | Deprecation policy |
|---|---|---|---|
| `POST /v1/orders` | `order-service` | `web-app`, `mobile-app` | 2 versions supported in parallel, 90-day sunset notice |
| `orders.created` event schema | `order-service` | `billing-service`, `shipping-service` | Schema registry compatibility mode: BACKWARD |

## Contract testing setup

| Property | Value |
|---|---|
| Tool | Pact / WireMock / Spring Cloud Contract / none |
| Contract broker | (URL, or "n/a") |
| Provider verification in CI | Yes / No — which pipeline stage |
| Consumer contract coverage | Which consumer/provider pairs have contracts today |

> OpenAPI schema compatibility and REST DTO breaking-change classification are reviewed by
> `api-review`, not duplicated here — this section only tracks the consumer-driven contract
> testing layer (Pact/WireMock) and whether provider verification actually runs in CI.

## What NOT to assume

- "It works when I run both services locally" is not evidence of deployment independence.
- A shared database "just for now" tends to become permanent — document the exception and the
  migration plan, don't leave it implicit.
- A circuit breaker dependency in `pom.xml`/`package.json` is not the same as one actually wired
  around the call site with real thresholds.
