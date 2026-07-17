# Decisions: Payment Webhook Idempotency

## D001 — Idempotency key is the provider's event ID, not a hash of the payload

**Status:** Active

**Context:** We need to detect duplicate webhook deliveries. Candidates for the idempotency key:
- Provider's event ID (e.g., `evt_abc123`)
- Hash of the payload
- Hash of the payload + timestamp
- Request signature

**Decision:** Use the provider's event ID as the idempotency key.

**Reasoning:**
- The provider assigns a unique ID to each event and guarantees it never repeats. This is the strongest guarantee.
- Payload hashes introduce edge cases: two events with identical payloads (unlikely but theoretically possible) would collide.
- Request signatures are cryptographic credentials, not business identifiers.
- The provider controls the event ID; we use it as-is without transformation.

**Consequences:** We must extract the event ID from the webhook payload reliably. Real provider SDKs abstract this; our example documents the pattern.

---

## D002 — Duplicate detection uses a database UNIQUE constraint, not in-memory locks or distributed locks

**Status:** Active

**Context:** We need to detect and skip duplicate events. Options:
- In-memory lock (e.g., `ConcurrentHashMap` + `synchronized`)
- Distributed lock (e.g., Redis, Zookeeper)
- Database UNIQUE constraint

**Decision:** Use a database UNIQUE constraint on `provider_event_id` in the webhook_events table.

**Reasoning:**
- **Atomic:** The UNIQUE constraint is evaluated at INSERT time, atomically. No race window between "check if exists" and "insert."
- **Crash-safe:** If the application crashes after inserting but before responding, the constraint persists. A retry from the provider will detect the duplicate.
- **In-memory locks are not crash-safe:** If the process dies, the lock is lost. A retry will process the event again.
- **Distributed locks add operational complexity:** Another service to deploy and monitor. Failure modes include lock loss (timeout), network partitions, lock corruption.
- **The database is already required:** We're inserting the event regardless. Adding a constraint is free compared to external locking.

**Consequences:**
- UNIQUE constraint violations are the *expected normal path* for retries (not errors to fear).
- If two requests arrive concurrently with the same event ID, one succeeds and one fails the constraint. We catch the failure and return HTTP 200 for both.
- The application does not need to code its own "check if exists" logic; the database enforces it.

---

## D003 — Duplicates return HTTP 200, not HTTP 409 or error

**Status:** Active

**Context:** When a duplicate event is detected (UNIQUE constraint violation), what should we return?
- HTTP 200 (success)
- HTTP 409 (conflict)
- HTTP 202 (accepted)
- HTTP 500 (error)

**Decision:** Return HTTP 200 (success) for duplicates.

**Reasoning:**
- **Provider expectation:** The provider retries until it gets a 2xx response. Returning 200 tells the provider "I got it" and stops retries. This is the fastest, cleanest outcome.
- **Not an error:** A duplicate is not an application error. It's the normal, expected result of a retry. Treating it as an error (409, 500) causes unnecessary noise.
- **Semantics of 200:** "The request succeeded." A duplicate event is idempotent to delivery, so it *did* succeed (as a no-op).
- **Provider behavior:** If we return 409 or 5xx, the provider retries again, creating more noise. Eventually it gives up and logs the event as "undelivered." We don't want that.

**Consequences:**
- The application does not treat duplicate constraint violations as errors or exceptions. They are handled as normal control flow (not an exception path).
- Logging must distinguish between "first process" and "duplicate detected" (same 200 response, but different meanings).

---

## D004 — Signature verification happens before persistence, not after

**Status:** Active

**Context:** At what point do we verify the webhook's cryptographic signature?
- Before persisting anything
- After inserting the event (but before processing)
- During processing

**Decision:** Verify the signature *before* persisting anything.

**Reasoning:**
- **Security first:** An invalid signature is a security incident (forged webhook, misconfigured secret, attack). It should not touch the database.
- **No noise:** Invalid events (wrong signature, no signature) are not stored, so they don't clutter audit logs or occupy disk.
- **Fast rejection:** Signature verification is fast (HMAC-SHA256 microseconds). No point paying the cost of a database write if we're going to reject it anyway.
- **Clear audit trail:** Only trusted events (valid signature) appear in the webhook_events table.

**Consequences:**
- Signature verification is separate from idempotency detection. Failed signatures do not trigger the UNIQUE constraint.
- The controller handles signature verification, not the repository or service.

---

## D005 — Failed events are recorded with a reason, not discarded or retried internally

**Status:** Active

**Context:** When processing a webhook fails (e.g., charge lookup fails), should we:
- Discard the event and log an error
- Retry internally (with backoff, retry count, DLQ)
- Record the failure and let the provider retry

**Decision:** Record the failure and let the provider retry via HTTP 202 (Accepted).

**Reasoning:**
- **No internal retry loop:** Designing a robust retry mechanism (backoff, circuit breaker, DLQ) is complex and adds operational overhead.
- **Provider handles retries:** The payment provider already retries failed webhooks on its side. Leveraging that is simpler than duplicating retry logic.
- **Transient vs. permanent:** We don't know if a failure is transient (database temporarily unavailable) or permanent (charge ID not found). Returning 202 tells the provider to retry. If it's permanent, the human investigates the failed event.
- **Auditability:** Recording the failure reason allows humans to triage failed events and understand what went wrong.
- **Eventual consistency:** If a charge lookup fails because the charge is not yet synced to the local database, a retry an hour later will succeed.

**Consequences:**
- The service layer catches exceptions during processing, records the failure reason, and returns HTTP 202 (not throwing an exception).
- Failed events are queryable by status in the database, enabling manual retry or investigation.

---

## D006 — No real payment provider SDK dependency

**Status:** Active

**Context:** Should we include Stripe SDK, Square SDK, or PayPal SDK as a real dependency?

**Decision:** No. Use a generic "Payment Provider" concept. Demonstrate the pattern with mock implementations.

**Reasoning:**
- **Idempotency is provider-agnostic:** The pattern works for Stripe, Square, PayPal, custom providers, and any webhook system. Using one real provider would distract from the universality.
- **Educational focus:** The example teaches the pattern, not Stripe integration. Adding a real SDK would muddy the learning with provider-specific details.
- **Adaptability:** A developer reading this can easily replace `PaymentEventPayload` with Stripe's types and `WebhookSignatureVerifier` with Stripe's verification logic. The core pattern is unchanged.
- **Dependency management:** Real SDKs change frequently. This example should not rot because Stripe updated their API.

**Consequences:**
- The example includes a `PaymentEventPayload` interface/class that is generic. Real integrations will extend or replace this with provider types.
- Signature verification is demonstrated generically (HMAC-SHA256), not with a specific provider's algorithm.

---

## D007 — Events are stored immutably; status and failure reasons are appended, not updated in-place

**Status:** Active

**Context:** The webhook_events table stores the event payload. Should we:
- Allow updates to the payload or signature fields (treat them as mutable)
- Keep them immutable and append status changes

**Decision:** Store payload and signature immutably. Only update status and timestamp fields when processing completes or fails.

**Reasoning:**
- **Auditability:** The stored payload is the source of truth for what the provider sent. It should never change.
- **Forensics:** If we need to replay an event or investigate a failure, we need the exact payload that was received.
- **Compliance:** Payment systems are audited. Immutable event records are a regulatory expectation.

**Consequences:**
- The INSERT statement creates the record with payload, signature, and status='RECEIVED'.
- The UPDATE statement only touches status, processed_at, processed_by, failure_reason (never the payload).

---

## D008 — No internal state machines for event processing; status is source of truth

**Status:** Active

**Context:** As the webhook is processed, it transitions through states (RECEIVED → PROCESSING → PROCESSED). Should we:
- Use an in-memory state machine (e.g., enum with state transitions)
- Use the database status column as the state machine

**Decision:** The database status column is the state machine. No in-memory state transitions.

**Reasoning:**
- **Durability:** If the process crashes mid-transition, the state is lost if it's only in memory. The database persists it.
- **Observability:** Querying the database shows the current state of all events. In-memory state is opaque.
- **Simplicity:** No need to code state transition rules in memory. The database is the single source of truth.

**Consequences:**
- Status is immediately set to RECEIVED when inserted.
- Status is updated to PROCESSED or FAILED when processing completes.
- The application queries the database to determine event state, not in-memory flags.

---

## D009 — No payload decompression, decryption, or transformation; store raw

**Status:** Active

**Context:** Should we deserialize, validate, and transform the webhook payload before storing?

**Decision:** Store the raw, untransformed webhook payload as received.

**Reasoning:**
- **Immutability:** The stored payload is exactly what the provider sent. No chance of corruption or loss in transformation.
- **Auditability:** If there's a dispute, we have the exact bytes the provider claimed to send (signed with their secret).
- **Future-proofing:** If the provider adds new fields to the payload, we don't lose them by deserializing to a strict schema.

**Consequences:**
- The payload is stored as TEXT (or BLOB). No validation or schema enforcement at the database level.
- The service layer deserializes the payload when processing (and validates it). If validation fails, we record the failure and retry.

---

## D010 — Webhook endpoint is stateless; concurrency is handled by the database

**Status:** Active

**Context:** The webhook controller receives multiple requests. Should it:
- Coordinate them with locks (async RequestsHandling)
- Make each request independent (stateless)

**Decision:** The controller is stateless. Each request independently attempts to insert the event. The database's UNIQUE constraint coordinates them.

**Reasoning:**
- **Simplicity:** No locks, no state, no coordination logic in the controller.
- **Scalability:** Multiple processes on different machines can all handle webhook requests independently. The database (shared) enforces uniqueness.
- **Consistency:** The database constraint is the single source of truth, not any in-process coordination.

**Consequences:**
- Request processing is truly concurrent and scalable.
- UNIQUE constraint violations are expected and handled as normal control flow (not exceptions).
- Load balancers can distribute webhook requests across any number of instances.

---

## D011 — No event ordering guarantee; application logic must be idempotent to out-of-order events

**Status:** Active

**Context:** Webhooks may arrive out of order (e.g., charge.succeeded before charge.created). Should the webhook receiver:
- Queue and order events before processing
- Process them in any order

**Decision:** Process them in any order. The application logic must handle out-of-order events.

**Reasoning:**
- **Scope:** Idempotency (duplicate detection) is a different concern from ordering. Adding ordering to the webhook receiver adds complexity beyond the scope of this example.
- **Application responsibility:** The application domain model (e.g., charge state machine) should handle out-of-order events or enforce ordering rules.
- **Realism:** Real providers sometimes deliver out-of-order. Applications need to be robust to this regardless of the webhook receiver.

**Consequences:**
- The webhook receiver processes events immediately upon receipt, without queuing or sorting.
- The business logic layer (e.g., `PaymentProvider` service) must be idempotent to business order, not just delivery order.

---

All decisions are Active. See SPEC.md for context and PLAN.md for implementation strategy.
