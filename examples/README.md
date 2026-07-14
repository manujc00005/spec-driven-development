# Examples

Worked, end-to-end examples of the SDD workflow — each one carries a real engineering problem through `/spec-create` → `/spec-plan` → `/spec-analyze` → `/spec-implement` → `/spec-review` → the relevant specialized reviews → `/spec-close` → `/pr-description`, with all the artifacts the workflow produced.

| Example | Stack | Demonstrates |
|---|---|---|
| [`002-payment-webhook-idempotency/`](002-payment-webhook-idempotency/) | Java / Spring Boot | Constraint-based idempotency (UNIQUE constraint, not locks), HMAC signature verification before processing, retry-aware HTTP status codes (200/202/400/401), full SPEC/PLAN/TASKS/DECISIONS, 14 test cases, database migration, and review artifacts |

These examples are educational: they show the workflow and the pattern faithfully, but they are not complete production systems.
