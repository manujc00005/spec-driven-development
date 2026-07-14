# Implementation Plan: Payment Webhook Idempotency

## Architecture

The webhook receiver consists of four layers:

```
HTTP Request
    ↓
[PaymentWebhookController]          ← HTTP concerns (status codes, headers)
    ↓ (delegates)
[PaymentWebhookService]             ← Business logic (idempotency, processing)
    ↓ (delegates)
[WebhookSignatureVerifier]          ← Security (signature verification)
[WebhookEventRepository]            ← Data access (UNIQUE constraint, status)
    ↓
[Database: webhook_events table]    ← Source of truth (UNIQUE constraint)
```

**Responsibilities:**

- **Controller:** Parse HTTP request, delegate to service, return status code based on result.
- **Service:** Verify signature, extract provider event ID, attempt idempotent insert-and-process, handle constraint violations, record status.
- **SignatureVerifier:** HMAC verification using provider's shared secret.
- **Repository:** JPA access to webhook_events table, handle UNIQUE constraint violations, query by status.
- **Database:** webhook_events table with UNIQUE constraint on provider_event_id, status enum, payload storage, audit timestamps.

## Database Design

### webhook_events table

```sql
CREATE TABLE webhook_events (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    provider_event_id VARCHAR(255) NOT NULL UNIQUE,  -- Source of truth for idempotency
    event_type VARCHAR(100) NOT NULL,                 -- e.g., "charge.succeeded"
    status VARCHAR(50) NOT NULL DEFAULT 'RECEIVED',   -- RECEIVED, PROCESSED, FAILED
    payload TEXT NOT NULL,                            -- Immutable raw JSON
    payload_hash VARCHAR(64),                         -- SHA-256 of raw payload
    signature_header VARCHAR(500),                    -- Signature from webhook header
    failure_reason TEXT,                              -- Populated if status=FAILED
    received_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP,
    created_by VARCHAR(100),                          -- "webhook-receiver" for audit
    updated_by VARCHAR(100),
    
    INDEX idx_status (status),
    INDEX idx_received_at (received_at),
    CONSTRAINT fk_webhook_not_modified CHECK (processed_at >= received_at)
);
```

**Key design decisions:**

- **provider_event_id UNIQUE:** The database enforces single-process guarantee atomically.
- **status enum:** RECEIVED → PROCESSED or RECEIVED → FAILED. No back-transitions.
- **payload as TEXT:** Stored immutably for audit and replay. Real implementations may compress or archive old payloads.
- **failure_reason:** Explains why processing failed (e.g., "charge_id not found", "database unavailable").
- **Indexes on (status, received_at):** Allows querying failed or recent events for manual retry or monitoring.

## Transaction Strategy

**Two-phase idempotent processing:**

```
1. INSERT webhook_events (provider_event_id, event_type, payload, status='RECEIVED')
   ↓
   If UNIQUE constraint violation:
     → Duplicate detected
     → Log it
     → Return HTTP 200 (success to provider)
   ↓
2. Process the event inside a transaction:
   BEGIN TRANSACTION
     extract charge_id from payload
     lookup charge in payment system
     create invoice
     emit email
     UPDATE webhook_events SET status='PROCESSED', processed_at=NOW()
   COMMIT
   ↓
   If exception during processing:
     ROLLBACK
     UPDATE webhook_events SET status='FAILED', failure_reason=error_message
     Return HTTP 202 (transient failure, retry)
```

**Why this works:**

- **Insert is atomic:** The UNIQUE constraint is checked before returning. Either the insert succeeds (first occurrence) or fails (duplicate). No race condition.
- **Processing is in a transaction:** If processing fails partway (e.g., email service down), we rollback and record the failure. On retry, the insert succeeds (constraint still allows re-insert if status was FAILED, or we query status first).
- **Idempotency is guaranteed by the UNIQUE constraint, not by application logic:** We don't have to code a "check if exists" before processing. The database does it.

**Edge case: application crash mid-processing**

```
Thread 1: INSERT succeeds (status=RECEIVED)
Thread 1: BEGIN processing
Thread 1: Create invoice (success)
Thread 1: Emit email (fails, app crashes)
Thread 1: Never sends HTTP response
         ↓
Provider: Timeout waiting for response
Provider: Retries webhook
         ↓
Thread 2: Attempt INSERT with same provider_event_id
         ↓
Thread 2: UNIQUE constraint violation (already in DB)
Thread 2: Status is still RECEIVED (previous txn never completed)
Thread 2: Log as duplicate, return 200
```

This is **safe for idempotency** but **unsafe for business logic** (email was sent, invoice was created, but we're not retrying). This is acceptable because:

1. The webhook receiver recovered (new request).
2. The idempotency guarantee (exactly one process) is held.
3. Reconciliation (daily check for orphaned invoices) will catch the partial failure.

## Idempotency Strategy

**Idempotency key:** The provider's unique event ID (e.g., `evt_12345`, `ch_67890`).

**Why this key, not others:**

- **Not request signature:** Signatures can be identical for different requests. The provider controls the key; we use it.
- **Not payload hash:** Two different events could have the same payload (unlikely but possible in theory). The provider's ID is unique by design.
- **Not timestamp:** Multiple events can occur at the same timestamp.

**Detection method:** UNIQUE constraint on provider_event_id.

**Why constraint, not code:**

- **Atomic:** Constraint violation is detected at insert time, before any processing. No race window.
- **Crash-safe:** If the application crashes, the constraint is still in the database. Retries still detect the duplicate.
- **No additional dependency:** In-memory locks are lost on crash. Distributed locks (Redis, Zookeeper) add operational complexity. The database is already required for processing.

## Signature Verification Strategy

**Flow:**

```
Receive HTTP request
  ↓
Extract signature from header
Extract shared secret from configuration
Compute HMAC-SHA256(shared_secret, raw_payload)
Compare computed HMAC with received signature
  ↓
  If mismatch:
    Log security incident
    Return HTTP 401
    Persist nothing
  ↓
  If match:
    Proceed to idempotency check
```

**Why before persistence:**

- **Security first:** Invalid signatures are not trusted and should not touch the database.
- **Audit:** Signature verification failures are flagged as potential attacks and logged separately from idempotency.

**Secrets management (not implemented here):**

In production, the shared secret is:
- Fetched from a secrets vault (AWS Secrets Manager, HashiCorp Vault), not hardcoded.
- Cached in memory with a short TTL (e.g., 1 hour).
- Rotated periodically; the verifier supports multiple valid secrets (old and new) during rotation.

For this example, the secret is a constant for simplicity.

## Error Handling

| Scenario | Detection | Action | HTTP Status | Retry? |
|----------|-----------|--------|-------------|--------|
| Valid event, first time | INSERT success | Process | 200 (after process) | No |
| Valid event, duplicate | INSERT constraint violation | Log, skip process | 200 | No |
| Invalid signature | HMAC mismatch | Reject, log security | 401 | No |
| Malformed JSON | JSON parse error | Reject | 400 | No |
| Processing exception (transient) | catch Exception in service | Record failure, rollback | 202 | Yes |
| Processing exception (permanent) | Application determines | Record failure, log | 202 or 400 | Yes / No |
| Database unavailable | Connection error | Return 500 | 500 | Yes |

## Retry Behavior (Provider's Side)

We don't implement retries ourselves. The *provider* retries based on our HTTP response:

- **2xx (200, 202):** Success or accepted. Provider logs and moves on (no more retries).
- **4xx (400, 401):** Client error. Provider logs and (usually) does not retry.
- **5xx (500, 502, 503):** Server error. Provider retries with exponential backoff.

**Our design returns:**

- **200:** Event processed successfully OR already processed (duplicate). Either way, we're done.
- **202:** Event received but processing deferred/failed transiently. Provider should retry.
- **401:** Signature verification failed. Provider should not retry this event (log it as a breach attempt).
- **400:** Payload malformed. Provider should not retry.
- **500:** Database or critical error. Provider retries.

## Testing Strategy

### Unit Tests (PaymentWebhookServiceTest)

1. **Idempotency:** First event processed, duplicate ignored.
2. **Invalid signature:** Rejected before processing.
3. **Concurrent duplicates:** Database constraint handles race.
4. **Processing failure:** Exception caught, status recorded, HTTP 202 returned.
5. **Status lifecycle:** RECEIVED → PROCESSED or FAILED.

### Integration Tests (PaymentWebhookControllerTest)

1. **HTTP contract:** POST /webhooks/payment-provider with valid payload returns 200.
2. **Invalid signature header:** Returns 401.
3. **Malformed JSON:** Returns 400.
4. **Concurrent requests:** Only one processes; others return 200 (duplicate).

### Mocks

- **PaymentProvider interface:** Abstraction for looking up charge, creating invoice. Mocked in tests to succeed or fail on demand.
- **WebhookSignatureVerifier:** Can be mocked or use real HMAC in tests (it's fast).
- **Database:** H2 in-memory for tests, or PostgreSQL for integration.

## Rollback Strategy

**If deployment fails:**

1. **RECEIVED events not processed:** They are safe to leave in the database. Redeploy with a fix; retries will pick them up.
2. **PROCESSED events:** Already committed. No rollback needed (idempotency holds).
3. **FAILED events:** Can be reprocessed manually once the underlying issue is fixed.

**If the schema needs to change:**

1. Add new columns/indexes with `ALTER TABLE` (non-blocking for PostgreSQL with proper planning).
2. Backfill data if needed.
3. Deploy code that understands both old and new schema.
4. Once traffic is routed to the new code, remove dead code for old schema.

**If idempotency logic is broken:**

The UNIQUE constraint is the fallback. Even if code is broken, the database ensures duplicates are not processed twice (they'll hit the constraint).

## Deployment Plan

1. **Schema migration:** Deploy V1__create_webhook_events.sql (creates the table with UNIQUE constraint).
2. **Code deployment:** Deploy the controller, service, repository, verifier.
3. **Test:** Send test webhook from provider (with correct signature).
4. **Monitor:** Watch webhook logs, event status, failure rates.
5. **Cutover:** Provider switches to sending webhooks to the new endpoint (or update webhook URL in provider config).

---

This plan is detailed enough for implementation. See TASKS.md for step-by-step work items.
