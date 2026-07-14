# Pull Request: Payment Webhook Idempotency Handler

## Summary

Implement a safe, idempotent webhook receiver for payment provider events. This prevents duplicate processing of webhooks (which would double-charge customers) using a database UNIQUE constraint as the source of truth.

**The core guarantee:** Each webhook event is processed exactly once, even if delivered multiple times by the provider.

## Changes

### Database Schema
- **V1__create_webhook_events.sql:** Creates the `webhook_events` table with a UNIQUE constraint on `provider_event_id` as the idempotency key. Supports tracking event status (RECEIVED, PROCESSED, FAILED) and failure reasons.

### HTTP Endpoint
- **PaymentWebhookController.java:** Receives POST requests at `/webhooks/payment-provider` with a JSON payload and a cryptographic signature header.

### Business Logic
- **PaymentWebhookService.java:** Orchestrates idempotent processing:
  1. Verify the webhook signature (before persistence).
  2. Extract the provider event ID (idempotency key).
  3. Attempt to insert the event into the database.
  4. If UNIQUE constraint is violated (duplicate): return HTTP 200 (success, stop retries).
  5. If insert succeeds: process the event in a transaction.
  6. If processing fails: record the failure reason and return HTTP 202 (transient error, retry).

### Data Access
- **WebhookEventRepository.java:** Spring Data JPA repository for accessing webhook events. Provides methods to query by status, event type, and recent events for monitoring/retry workflows.

### Domain Model
- **WebhookEvent.java:** JPA entity representing a stored webhook event with lifecycle (RECEIVED → PROCESSED/FAILED).
- **PaymentEventPayload.java:** DTO for deserializing incoming webhook payloads (generic, applicable to any payment provider).

### Security
- **WebhookSignatureVerifier.java:** HMAC-SHA256 verification with constant-time comparison to prevent timing attacks. Signature verification happens before any processing.

### Tests
- **PaymentWebhookServiceTest.java:** Unit tests verifying idempotency guarantees:
  - First event processed ✓
  - Duplicate event skipped ✓
  - Invalid signature rejected ✓
  - Processing failure recorded ✓
  - Concurrent duplicates handled by constraint ✓

- **PaymentWebhookControllerTest.java:** Integration tests for HTTP contract:
  - Valid webhook returns 200 ✓
  - Invalid signature returns 401 ✓
  - Malformed payload returns 400 ✓
  - Duplicate returns 200 ✓
  - Processing failure returns 202 ✓

## Tests

All tests pass. Coverage includes:
- ✓ Idempotency: duplicate events are detected and skipped
- ✓ Security: invalid signatures are rejected before persistence
- ✓ Error handling: transient failures are distinguished from permanent failures
- ✓ HTTP contract: status codes are semantically correct
- ✓ Concurrent delivery: database constraint ensures exactly-once processing

Run with:
```bash
mvn test
```

## Security Notes

1. **Signature Verification:** All webhooks are verified before processing. Invalid signatures return HTTP 401 and are logged as security incidents.
2. **No Secrets in Logs:** The shared webhook secret is never logged or exposed in error messages.
3. **Immutable Audit Trail:** Webhook payloads are stored as-is in the database for forensic and compliance purposes.
4. **Idempotency:** Protects against double-charging customers (the most critical payment safety issue).

## Data Migration

The database migration is backward-compatible and additive:
- Creates a new `webhook_events` table.
- No existing tables are modified or dropped.
- Existing applications continue to run alongside the new webhook receiver.

To deploy:
```bash
mvn flyway:migrate
```

## Risks

**Low risk. No breaking changes.**

- The webhook receiver is new; no existing code depends on it.
- The UNIQUE constraint is enforced at the database level, preventing accidental duplicates.
- Idempotency is guaranteed by the database, not by application code.

**Known limitations (by design):**
- Events may arrive out of order. Application logic must handle out-of-order events or enforce ordering separately (not the webhook receiver's responsibility).
- Partial processing failures (e.g., invoice created, email failed) require reconciliation. The webhook is marked FAILED; a retry will re-attempt processing.

See REVIEW_REPORT.md for detailed risk analysis.

## Rollback Plan

If the webhook receiver needs to be rolled back:

1. **Pause incoming webhooks** at the payment provider (update webhook URL or disable).
2. **Revert the code changes** (remove the controller, service, verifier).
3. **Do NOT drop the database table.** Leave webhook_events as-is for audit purposes.
4. **Catch up on missed events** by querying the payment provider's API for events that arrived while the receiver was down, and reprocess them.

Alternatively, if a bug is found in the webhook receiver:

1. **Fix the bug** and redeploy.
2. **Query failed events:** `SELECT * FROM webhook_events WHERE status='FAILED'`.
3. **Retry failed events** via a manual admin API (not yet implemented).

## Future Work

- Implement a manual retry endpoint to reprocess failed events.
- Add metrics/observability (Prometheus, New Relic, DataDog).
- Implement reconciliation (daily sweep to catch events missed due to outages).
- Add support for provider-specific signature algorithms (Stripe, Square, PayPal each use different formats).
- Implement a webhook replay endpoint for testing.

## Checklist

- [x] Code follows repository conventions.
- [x] Tests pass and cover happy path + error cases.
- [x] No hardcoded secrets (example uses constant for clarity; production will use vault).
- [x] No breaking changes to existing APIs.
- [x] Database migration is additive and reversible.
- [x] Documentation is complete (SPEC.md, PLAN.md, DECISIONS.md, REVIEW_REPORT.md).
- [x] Signature verification is correct and happens before processing.
- [x] Idempotency is enforced by the database, not by application code.
- [x] Error handling distinguishes between transient (202) and permanent (400/401) failures.

---

**Type:** Feature (New webhook receiver for payment idempotency)  
**Impact:** Prevents duplicate charge processing (critical for payment safety)  
**Reviewers:** Backend team, Security team, Database team  
**Related:** Payment system, compliance (PCI, audit requirements)
