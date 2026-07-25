# Examples

Worked, end-to-end examples of the SDD workflow — each one carries a real engineering problem through `/spec-create` → `/spec-plan` → `/spec-analyze` → `/spec-implement` → `/spec-review` → the relevant specialized reviews → `/spec-close` → `/pr-description`, with all the artifacts the workflow produced.

| Example | Stack | Demonstrates |
|---|---|---|
| [`001-payment-webhook-idempotency/`](001-payment-webhook-idempotency/) | Java / Spring Boot | Constraint-based idempotency (UNIQUE constraint, not locks), HMAC signature verification before processing, retry-aware HTTP status codes (200/202/400/401), full SPEC/PLAN/TASKS/DECISIONS, 14 test cases, database migration, and review artifacts |
| [`002-server-action-rate-limiting/`](002-server-action-rate-limiting/) | TypeScript / Next.js | Sliding-window rate limiting with a bounded key store, the x-forwarded-for trust boundary (spoofing/poisoning attack tests), zod validation with honeypot, enumeration-resistant constant responses, fail-closed policy, 17 test cases, and a security review that caught a real finding (SEC-001) with its fix in the trail |

These examples are educational: they show the workflow and the pattern faithfully, but they are not complete production systems.

The artifacts here (`SPEC.md`, `PLAN.md`, `TASKS.md`, `DECISIONS.md`, review reports, …) are **provider-neutral SDD Core** — the same regardless of which AI agent drives the workflow. The slash-command names shown above (`/spec-create`, `/spec-plan`, …) are the **Claude Code adapter's** surface; the Codex adapter runs the identical lifecycle through prompts. See [Provider adapters](../adapters/README.md).
