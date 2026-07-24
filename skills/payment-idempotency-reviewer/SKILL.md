---
name: payment-idempotency-reviewer
description: Processor-agnostic review of money-movement flows for exactly-once effects — idempotency keys and dedup stores, retry storms, concurrent double-submission, DB constraints as the last line of defense, and outbox/event consistency. Extends backend-review and database-review.
triggers:
  - After `/backend-review` on any flow that moves money, credits balances, or grants paid entitlements
  - When retry logic, queues, webhooks, or scheduled jobs touch a payment or ledger table
  - When the user asks "can this double-charge?" or "is this safe to retry?"
  - Triggered by `/review-all` when the spec mentions payments, refunds, wallets, credits, or ledgers
---

## SDD Contract

```yaml
category: domain-reviewer
inputs: [diff, backend-review-findings, database-review-findings]
outputs: [idempotency-findings]
side_effects: none
writes_code: false
writes_specs: false
analysis_only: true
primary_agent: domain-reviewer
secondary_agents: [security-reviewer]
profile_scope: [payments-fintech]
provider_specific: false
```

# Payment Idempotency Reviewer

## Purpose

Answer one question with evidence: **if any step of this flow runs twice, does money move twice?**
Retries, double-clicks, webhook redeliveries, consumer rebalances and crash-recovery all replay
work; this skill traces each replay path to a dedup mechanism or flags the gap. It **extends**
`backend-review` (logic) and `database-review` (constraints) — run those first.

## Extends

- **Skills:** `backend-review`, `database-review`
- **Sibling:** `stripe-payments-reviewer` (Stripe-specific surface); `event-driven-reviewer` (broker delivery semantics)

## What this skill checks (beyond the generic reviews)

### Entry-point dedup

- Every money-moving entry point (HTTP endpoint, webhook, consumer, job) has an explicit
  idempotency identity: client-supplied key, event ID, or natural business key (`orderId` + operation).
- The dedup check-and-record is **atomic** — `SELECT`-then-`INSERT` without a unique constraint
  is a race, not a guard. The unique index on the idempotency key is the mechanism; application
  checks are just fast-paths.
- Replayed requests return the **original result** (stored response/state), not an error the
  client will retry forever.

### Concurrency

- Two identical requests in flight simultaneously: pessimistic lock, unique-constraint catch, or
  serializable transaction — one of them, deliberately, with the constraint-violation path handled.
- State transitions are guarded (`UPDATE ... WHERE status = 'PENDING'` with rows-affected check,
  or optimistic versioning) — not read-modify-write on stale state.

### Retries and failure windows

- Every retry wrapper around a money movement reuses the same idempotency identity.
- The crash window is examined: external call succeeded but local commit failed → on retry, is
  the external side consulted or re-executed? Flag "re-execute and hope".
- Timeouts are treated as **unknown outcome**, not failure — no automatic re-charge on timeout
  without a status check first.

### Storage as last line of defense

- Ledger/payment tables carry the unique constraints that make double-apply impossible even if
  every application guard fails (unique `(order_id, operation)`, unique `external_payment_id`).
- Dedup/processed-event tables have a retention story — unbounded growth eventually breaks the guard.
- Amounts immutable once recorded; corrections are compensating entries, not `UPDATE amount`.

### Event consistency (when events are emitted)

- DB state change and event emission are consistent: transactional outbox, or an explicit,
  documented acceptance of the gap. Publish-inside-transaction and publish-then-commit both flagged.
- Consumers of payment events apply the same entry-point dedup rules (event ID recorded atomically
  with the effect).

## Output format

```markdown
## Payment Idempotency Review

**Verdict:** PASS | PASS WITH NOTES | FAIL

### Replay matrix

| Entry point | Replay source | Dedup mechanism | Atomic? | Verdict |
|---|---|---|---|---|
| POST /orders | client retry / double-click | unique (customer_id, cart_hash) | yes (DB constraint) | OK |
| order-created consumer | redelivery / rebalance | none found | — | **GAP** |

### Findings

| # | Severity | File:Line | Finding | Action |
|---|---|---|---|---|

### Recommendations

- (Non-blocking hardening)
```

## What this skill does NOT do

- Does not review Stripe API specifics — signature checks, API versions (that's `stripe-payments-reviewer`).
- Does not review broker configuration/delivery semantics (that's `event-driven-reviewer`).
- Does not design the ledger schema from scratch — it reviews the one in the diff.
- Does not modify code.
