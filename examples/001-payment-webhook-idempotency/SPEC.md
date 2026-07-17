# Feature Spec: Payment Webhook Idempotency

## Status

Done

> Closed 2026-07-14. Specification complete with all acceptance criteria verified in tests and design review. See REVIEW_REPORT.md.

## Problem

Payment providers (e.g., generic Payment Provider, Square, Stripe, PayPal) send webhook events to notify applications of transactions. These webhooks are **inherently unreliable**:

1. **Retry-on-failure:** If the webhook receiver doesn't respond with HTTP 2xx within a timeout, the provider retries (often 3–10 times over hours or days).
2. **Duplicate delivery:** Network timeouts create ambiguity: did the webhook arrive? Did it process? Retries can deliver the same event multiple times.
3. **Out-of-order delivery:** Multiple regional endpoints and async retry queues mean events may arrive out of sequence.
4. **At-least-once guarantee:** Providers guarantee *at least* one delivery, never *exactly* one.

Without idempotency, duplicate webhook delivery causes **duplicate business effects**:

- A `charge.succeeded` event processed twice charges the customer twice.
- A `customer.created` event processed twice creates two customer records.
- A `payment.completed` event processed twice sends two confirmation emails.

This is a critical bug: customers notice double charges immediately, support costs spike, and compliance issues arise (payment discrepancies, audit failures).

## Goal

Implement a **safe, idempotent webhook receiver** that:

1. Processes each webhook event exactly once, even if delivered multiple times.
2. Uses database constraints as the source of truth for idempotency, not code-based locking or caching.
3. Verifies webhook authenticity before processing.
4. Records event state clearly: received, processed, or failed.
5. Returns appropriate HTTP status codes to signal success to the provider (stop retries) or failure (continue retries).
6. Handles concurrent duplicate delivery safely.

## Non-goals

- **Real provider SDK integration.** This example uses a generic payment provider model. Adapting to Stripe/Square/PayPal is straightforward (replace signature verification and payload types).
- **Charge lookup, invoice creation, or payment processing.** The service layer is mocked; the focus is idempotency, not payment logic.
- **Reconciliation.** This handles inbound webhook events only. Reconciliation (daily sweep to catch missing events) is separate.
- **Multi-currency, tax, or accounting.** Out of scope.
- **Observability, alerting, or operational dashboards.** Out of scope (but noted as needed in production).
- **Event ordering.** The pattern is idempotent to *delivery* order, not to business logic order. Application logic must handle out-of-order events or enforce ordering separately.

## Functional requirements

**FR-001** — Store webhook events immutably in the database with a unique identifier from the payment provider.

**FR-002** — Detect and skip duplicate events: if the same provider event ID is received twice, process it only once.

**FR-003** — Use a database UNIQUE constraint on the provider event ID as the source of truth for idempotency, not in-memory locks or distributed locks.

**FR-004** — Verify the webhook's cryptographic signature before processing. Reject unsigned or incorrectly signed events before persistence.

**FR-005** — Process webhook events inside a database transaction. If processing fails, the transaction rolls back and the webhook status records the failure reason.

**FR-006** — Return appropriate HTTP status codes to signal outcome to the provider:
  - HTTP 200 (OK): Event processed successfully or already processed (duplicate).
  - HTTP 202 (Accepted): Event received but processing deferred or failed transiently (provider should retry).
  - HTTP 400 (Bad Request): Webhook body is malformed (provider should not retry).
  - HTTP 401 (Unauthorized): Signature verification failed (provider should not retry this event, but log it as a security incident).

**FR-007** — Record the webhook event status progression: `RECEIVED` → `PROCESSED` (or `RECEIVED` → `FAILED` if processing fails).

**FR-008** — Log the event payload and status in the database for auditing and investigation. Do not log secrets (provider secrets, API keys, tokens).

## Security requirements

**SR-001** — Signature verification is mandatory. Every webhook must be verified using the provider's shared secret before any processing occurs. Invalid signatures are rejected immediately (HTTP 401).

**SR-002** — The provider's shared secret is never logged or exposed in error messages. Signature mismatches are logged with event ID only, not secret or payload.

**SR-003** — Webhook event payloads are stored as-is (immutable) in the database for audit and replay purposes. Sensitive fields (customer PII if included) are noted in the schema.

**SR-004** — Access to the webhook endpoint is HTTP basic auth or OAuth2 token (out of scope for this example but noted as a requirement in production).

**SR-005** — The application does not trust HTTP headers for authentication. Only cryptographic signature verification is considered authoritative.

## Data integrity requirements

**DR-001** — The UNIQUE constraint on `provider_event_id` is the single source of truth for detecting duplicates. All duplicate detection must rely on this constraint, not application-layer caching or flags.

**DR-002** — If two threads attempt to process the same event concurrently (network retry while first request still processing), the database constraint ensures exactly one succeeds.

**DR-003** — If a webhook is marked as `FAILED`, it can be reprocessed manually. The status column allows application code to query failed events for retry.

**DR-004** — Webhook events are immutable once stored. The `received_at` and `processed_at` timestamps are set once and never changed.

**DR-005** — The `payload_hash` (SHA-256 of the raw payload) allows detecting if the same event was delivered with different payloads (edge case for audit).

## Edge cases

**EC-001** — Duplicate delivery while processing: first request is still processing when a retry arrives. The UNIQUE constraint ensures only one completes successfully.

**EC-002** — Signature verification failure: the provider sent the wrong signature (misconfiguration, secret rotation) or an attacker forged it. The event is rejected and logged as a security incident.

**EC-003** — Processing failure (e.g., charge lookup fails, invoice creation fails): the service returns HTTP 202, and the provider retries. When the underlying issue is fixed, the next retry succeeds.

**EC-004** — Out-of-order delivery: events arrive in a different order than they were sent (e.g., `charge.succeeded` before `charge.created`). Idempotency handles the duplicate-detection part; application logic must handle business logic order.

**EC-005** — Provider sends a webhook, never retries (we responded with 200 immediately): the event is stored and processed once.

**EC-006** — Provider crashes and resets its retry queue: the same event is delivered again hours or days later. The UNIQUE constraint detects it as a duplicate.

**EC-007** — Application crashes after inserting the webhook event but before sending a response: the provider retries. The second attempt hits the UNIQUE constraint and returns 200 safely.

## Acceptance criteria

**AC-001** — Webhook endpoint exists and accepts POST requests with a JSON payload and a cryptographic signature header.

**AC-002** — Invalid signatures are rejected before processing, returning HTTP 401. No changes to the database.

**AC-003** — Valid, new events are processed exactly once. A second delivery of the same event (by provider_event_id) is detected as a duplicate and returns HTTP 200 without re-processing.

**AC-004** — The UNIQUE constraint on `provider_event_id` enforces idempotency at the database level. Concurrent duplicate delivery results in exactly one successful process and one constraint violation (logged as duplicate).

**AC-005** — Webhook events are stored in the database with status RECEIVED, then PROCESSED or FAILED.

**AC-006** — Processing failures (e.g., charge not found, invoice creation fails) are recorded with a failure reason. The webhook endpoint returns HTTP 202 so the provider retries.

**AC-007** — The webhook event payload is stored immutably in the database for audit purposes.

**AC-008** — No secrets (provider API secrets, signing keys) are logged in error messages or stored in the webhook payload.

**AC-009** — The service layer is decoupled from signature verification and idempotency logic. The controller handles HTTP concerns; the service handles business logic; the repository handles data access.

**AC-010** — Tests verify: first event processed, duplicate ignored, invalid signature rejected, concurrent duplicates handled by constraint, processing failure recorded, status lifecycle is correct.

## Assumptions

- The payment provider's event ID (`provider_event_id`) is universally unique and never collides across time or across different event types. This is a safe assumption for all major payment providers.
- Webhook signature verification uses HMAC-SHA256 or similar (provider-specific). The example assumes a generic verifier; real integrations will use the provider's SDK.
- Events arrive in JSON format with a cryptographic signature in the HTTP headers.
- The application database is available and stable. Transient database outages will cause HTTP 500, and the provider will retry—this is acceptable.

## Dependencies

- Spring Framework (REST controller, transaction management)
- Spring Data JPA (repository pattern)
- JUnit 5 (testing)
- Mockito (mocking external dependencies)
- H2 or PostgreSQL (database)

## Risks

**R-001** — If the UNIQUE constraint is misconfigured or dropped, duplicate detection fails silently. Mitigation: constraint is verified in tests and enforced by the database.

**R-002** — If signature verification is bypassable (e.g., missing secret, hardcoded key), security is compromised. Mitigation: tests verify rejected unsigned events.

**R-003** — If processing fails but does not record the failure reason, human triage is impossible. Mitigation: the schema includes `failure_reason` and tests verify it's populated.

**R-004** — If two applications process the same webhook (multiple instances), they race for the UNIQUE constraint. Only one wins. Mitigation: This is expected and safe; the loser sees the constraint violation and returns 200.

**R-005** — Out-of-order events may violate business logic expectations (e.g., charge.succeeded before charge.created). Mitigation: The application logic must be idempotent to business order, not just delivery order. This example assumes a charge creation implies idempotent charge success handling.

## Expected test cases

- **Happy path:** New event, valid signature, processing succeeds.
- **Duplicate delivery:** Same event arrives twice. Second is not processed.
- **Invalid signature:** Event rejected before processing.
- **Concurrent duplicates:** Two requests with the same event_id arrive in parallel. Only one processes successfully.
- **Processing failure:** Charge lookup fails. Event status is FAILED, failure_reason is recorded, HTTP 202 is returned.
- **Malformed payload:** Missing required fields. HTTP 400.

---

This specification is complete and ready for implementation. See PLAN.md for architecture and DECISIONS.md for rationale.
