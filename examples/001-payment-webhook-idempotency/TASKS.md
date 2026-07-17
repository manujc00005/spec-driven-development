# Tasks: Payment Webhook Idempotency

Status legend: `[x]` done

## Task list

- [x] **T001** — Create database schema (`V1__create_webhook_events.sql`). Covers: AC-005, AC-007, DR-001, DR-004.

- [x] **T002** — Create domain model (`WebhookEvent.java`, `PaymentEventPayload.java`). Covers: AC-001, AC-005.

- [x] **T003** — Create repository (`WebhookEventRepository.java`) with UNIQUE constraint handling. Covers: AC-003, AC-004, DR-001, DR-002.

- [x] **T004** — Create signature verifier (`WebhookSignatureVerifier.java`). Covers: AC-002, SR-001, SR-002.

- [x] **T005** — Create service with idempotent processing logic (`PaymentWebhookService.java`). Covers: AC-001, AC-003, AC-004, AC-006, AC-009, FR-001…FR-007.

- [x] **T006** — Create HTTP controller (`PaymentWebhookController.java`). Covers: AC-001, AC-009, FR-001, FR-006.

- [x] **T007** — Write tests for duplicate delivery, idempotency guarantee (`PaymentWebhookServiceTest.java`). Covers: AC-003, AC-004, AC-010, EC-001.

- [x] **T008** — Write tests for invalid signatures, malformed payloads (`PaymentWebhookControllerTest.java`). Covers: AC-002, AC-010, SR-001.

- [x] **T009** — Create DECISIONS.md explaining all technical choices. Covers: Design rationale.

All tasks are complete. Implementation is ready for review.

## Verification

| Task | File | Status |
|------|------|--------|
| T001 | `src/main/resources/db/migration/V1__create_webhook_events.sql` | Complete |
| T002 | `src/main/java/com/example/payments/WebhookEvent.java` | Complete |
| T002 | `src/main/java/com/example/payments/PaymentEventPayload.java` | Complete |
| T003 | `src/main/java/com/example/payments/WebhookEventRepository.java` | Complete |
| T004 | `src/main/java/com/example/payments/WebhookSignatureVerifier.java` | Complete |
| T005 | `src/main/java/com/example/payments/PaymentWebhookService.java` | Complete |
| T006 | `src/main/java/com/example/payments/PaymentWebhookController.java` | Complete |
| T007 | `src/test/java/com/example/payments/PaymentWebhookServiceTest.java` | Complete |
| T008 | `src/test/java/com/example/payments/PaymentWebhookControllerTest.java` | Complete |
| T009 | `DECISIONS.md` | Complete |

---

All tasks complete. Ready for `/security-review`, `/database-review`, and `/code-review`.
