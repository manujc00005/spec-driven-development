# Worked Example: Payment Webhook Idempotency

A professional, end-to-end worked example of the SDD framework applied to payment safety.

## What this example demonstrates

This example walks through the design and implementation of a **safe, idempotent webhook receiver** for payment provider events. It demonstrates:

- **Idempotency by design:** Database UNIQUE constraints as the source of truth, not code-based locking
- **Payment-safe architecture:** Handling retries, duplicates, and network failures without double-charging
- **Security-first design:** Signature verification before processing, immutable event records
- **SDD workflow discipline:** Full lifecycle from SPEC → PLAN → TASKS → implementation → security review
- **Data integrity:** Transaction isolation, deterministic event keys, proper error recording
- **Professional documentation:** How to write specs, plans, tasks, and decisions for a critical system

## Why webhook idempotency matters

Payment providers (Stripe, Square, PayPal, etc.) send webhook events to notify you of transactions. These webhooks are **unreliable by design**:

- **Retries:** If your service doesn't respond with HTTP 200 in time, the provider retries (often 5–10 times).
- **Duplicate delivery:** Network flakes, server crashes, and timeout ambiguity mean the same event can be delivered multiple times.
- **Out-of-order delivery:** Retries and multiple regional endpoints mean events can arrive out of sequence.
- **At-least-once delivery guarantee:** Providers guarantee *at least* one delivery, not *exactly* one.

**Without idempotency**, you get:

```
Event: charge.succeeded (charge_id=ch_12345, amount=$100)
↓
webhook received (first time)
→ process event
→ create invoice
→ emit email
→ return 200
↓
webhook received again (retry, same event)
→ process event (AGAIN)
→ create invoice (AGAIN) — now customer is invoiced twice
→ emit email (AGAIN)
→ return 200
```

**With idempotency**, you get:

```
Event: charge.succeeded (charge_id=ch_12345, amount=$100)
↓
webhook received (first time)
→ check if event ch_12345 already processed
→ not processed → process, store event, return 200
↓
webhook received again (retry, same event)
→ check if event ch_12345 already processed
→ YES, already processed → return 200 (safe no-op)
```

## How the SDD workflow is used

This example follows the SDD framework exactly as documented:

1. **SPEC.md** — defines the problem, requirements, edge cases, acceptance criteria
2. **PLAN.md** — describes the architecture: DB schema, transaction strategy, idempotency key choice, signature verification
3. **TASKS.md** — breaks implementation into small, sequential tasks (schema → model → repository → service → controller → tests)
4. **DECISIONS.md** — records the *why* behind each choice (why UNIQUE constraint vs. locks, why duplicates return 200, etc.)
5. **Java code** — realistic, compilable implementation following the PLAN
6. **Tests** — verifying the core idempotency guarantees
7. **REVIEW_REPORT.md** — what a security and database review would report
8. **PR_DESCRIPTION.md** — how to present this for code review

The workflow demonstrates:
- How to specify a safety-critical system clearly
- How to design for constraint-based correctness (DB UNIQUE constraint as source of truth)
- How to verify implementation against the spec
- How reviews catch idempotency gaps
- How to document decisions for future maintainers

## File walkthrough

### Documentation files

- **SPEC.md** — The feature specification. Defines the idempotency problem, security requirements, edge cases, and acceptance criteria.
- **PLAN.md** — The implementation plan. Describes database schema, transaction strategy, how the UNIQUE constraint enforces idempotency, signature verification flow, and testing strategy.
- **TASKS.md** — Actionable tasks, each covering one concern (schema, domain model, repository, service, controller, tests).
- **DECISIONS.md** — Technical decisions and their rationale. Why DB constraint > in-memory lock, why duplicates return 200, why we store failure reasons, etc.
- **REVIEW_REPORT.md** — What `/security-review` and `/database-review` would find in this implementation.
- **PR_DESCRIPTION.md** — The pull request description. How you'd present this to your team.

### Code files

- **PaymentWebhookController.java** — HTTP endpoint. Receives raw payload and signature, delegates to service.
- **PaymentWebhookService.java** — Business logic. Verifies signature, extracts event ID, persists, processes idempotently.
- **WebhookEvent.java** — Domain model. Represents a stored webhook event with its status lifecycle.
- **WebhookEventRepository.java** — Data access. Handles UNIQUE constraint violations gracefully.
- **PaymentEventPayload.java** — Payload DTO. Deserialized from provider's webhook body.
- **WebhookSignatureVerifier.java** — Security utility. Implements HMAC verification.
- **V1__create_webhook_events.sql** — Database schema. Defines webhook_events table with unique constraint.

### Test files

- **PaymentWebhookServiceTest.java** — Tests idempotency: first event processed, duplicates safely ignored.
- **PaymentWebhookControllerTest.java** — Tests HTTP contract: invalid signatures rejected, valid events processed.

## Key design decisions

### 1. Idempotency key = provider event ID

The payment provider assigns a unique ID to each event (e.g., `ch_12345` or `evt_xyz`). We use this as the idempotency key, not a hash of the payload or a request signature.

**Why:** The provider guarantees ID uniqueness; we don't have to generate or hash anything. Simple, reliable, provider-aligned.

### 2. Database UNIQUE constraint is the source of truth

We insert the webhook event with a UNIQUE constraint on `provider_event_id`. If a duplicate arrives, the INSERT fails with a constraint violation. We catch this and return success.

**Why:** The database is the only system that can guarantee atomicity across retries. An in-memory lock would be lost on a crash. A distributed lock adds complexity and failure modes. The UNIQUE constraint is built-in, atomic, and free.

### 3. Duplicates return HTTP 200

When a duplicate event is detected, we return HTTP 200 (success) immediately, without processing it again.

**Why:** The provider retries until it gets a 2xx response. Returning 200 tells the provider "I got it" and stops retries. Returning an error would cause more retries, which is noise and confuses the provider.

### 4. Signature verification happens before persistence

We verify the provider's signature *before* we write anything to the database.

**Why:** A forged event (with an invalid signature) is a security incident. We should reject it before it touches any state. Signature verification is fast; no point writing garbage to the database.

### 5. Failed events are recorded, not discarded

If processing fails (e.g., charge lookup fails, invoice creation fails), we record the failure reason in the database and return HTTP 202 (Accepted) to stop retries.

**Why:** Retrying a transient failure (DB unavailable) is good. Retrying a permanent failure (charge ID not found) is not. We record the failure so humans can investigate.

### 6. No real payment provider SDK

This example uses a generic "Payment Provider" concept, not Stripe or PayPal SDK imports.

**Why:** The idempotency pattern is the same across all providers. A real SDK would distract from the core idea. You can adapt this to Stripe by replacing `PaymentEventPayload` with Stripe's types and `WebhookSignatureVerifier` with Stripe's verification logic.

## How to read this example

1. **Start with SPEC.md** — understand the problem and requirements
2. **Read PLAN.md** — understand the architecture and why
3. **Skim DECISIONS.md** — see the rationale for each choice
4. **Read PaymentWebhookService.java** — understand the core idempotent flow
5. **Read the tests** — see the guarantees being verified
6. **Read REVIEW_REPORT.md** — see what a real review would catch
7. **Read PR_DESCRIPTION.md** — see how you'd present this to your team

## Interview talking points

This example gives you several strong talking points:

### "I designed an idempotent webhook receiver"

- **Problem:** Payment webhooks are inherently unreliable; duplicates cause double-charging without idempotency.
- **Solution:** Database UNIQUE constraint on the provider event ID. First event processed, duplicates return 200.
- **Trade-off:** Constraint violations are the normal, expected path for retries—not errors to avoid.
- **Why it matters:** Payment safety is not negotiable. Idempotency is table-stakes for financial systems.

### "I chose database constraints over in-memory locks"

- **Why:** In-memory locks are lost on crash. Distributed locks add complexity. DB constraints are atomic, simple, and free.
- **Trade-off:** Slightly slower than a lock (one extra INSERT conflict), but atomicity is worth it.
- **Evidence:** The test `testDuplicateEventIsNotProcessedTwice()` demonstrates the guarantee holds under concurrent delivery.

### "I separated signature verification from processing"

- **Why:** Invalid signatures are security incidents, not transient failures. Reject before persistence.
- **Evidence:** The test `testInvalidSignatureRejected()` shows rejection without writing.

### "I recorded failures, not discarded them"

- **Why:** Transient failures (DB unavailable) should retry. Permanent failures (charge not found) should not. Recording lets humans triage.
- **Evidence:** The schema includes a `failure_reason` column and `status` enum.

### "I followed SDD discipline to specify a safety-critical system"

- **Problem:** Payment systems are easy to get wrong. Informal specs breed bugs.
- **Solution:** Formal SPEC, PLAN, TASKS, DECISIONS. Each layer checked by a different reviewer (security, database, code).
- **Trade-off:** Takes more time upfront. Catches more bugs before code review.
- **Evidence:** SPEC.md, PLAN.md, REVIEW_REPORT.md show the discipline.

## What NOT to discuss

This is an *educational* example, not a complete production system. Don't claim:

- "Production-ready payment system" — it's not. It shows the webhook receiver pattern only.
- "Real integration with Stripe/Square" — it doesn't. It's generic.
- "Full reconciliation logic" — missing. Out of scope.
- "Multi-currency support" — missing. Out of scope.
- "Observability stack" — missing. Out of scope.

**Do say:**
- "This shows how to design an idempotent webhook receiver safely, using SDD discipline."
- "The pattern applies to any payment provider or async event system."
- "In a real system, you'd add provider-specific signature verification, reconciliation, and monitoring."

## Questions you might get

**Q: Why not use a distributed lock?**
A: Distributed locks add a dependency and failure mode. If the lock service is down, you lose idempotency. The DB constraint doesn't have this problem.

**Q: What if the database is down?**
A: The INSERT fails, and we return 500 to the provider, which retries. When the database comes back, the retry succeeds. The constraint is not lost.

**Q: What about events that arrive out of order?**
A: Idempotency doesn't enforce ordering. If `charge.succeeded` arrives after `charge.failed`, we process both. The application logic must handle out-of-order events (usually by state machines). This example assumes in-order (or handles out-of-order explicitly in the service layer).

**Q: Can I use this for non-payment events?**
A: Absolutely. The pattern works for any webhook or async event system: Kafka topics, SNS/SQS, webhooks from marketing tools, etc.

## Next steps

To use this example:

1. Read SPEC.md to understand the problem
2. Read PLAN.md to understand the design
3. Copy the code and adapt it to your provider (Stripe, Square, etc.)
4. Use REVIEW_REPORT.md as a checklist for your implementation
5. Follow TASKS.md to structure your work

This example is intentionally self-contained. You don't need to run it; read it, understand it, and apply the pattern to your own systems.

---

**Created as a worked example of the SDD framework. Not an executable product.**
