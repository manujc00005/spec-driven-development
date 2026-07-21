---
name: stripe-payments-reviewer
description: Review Stripe integration code — webhook signature verification, idempotency keys, amount/currency handling in minor units, API version pinning, test/live key hygiene, and dispute/refund flows. Extends security-review and backend-review.
triggers:
  - After `/security-review` on any diff touching Stripe SDK calls, webhook handlers, or checkout/billing flows
  - When `stripe` appears in changed dependencies, env contracts, or API routes
  - When the user asks to "review payments", "check the webhook", or "audit billing"
  - Triggered by `/review-all` when the spec mentions payments, checkout, subscriptions, or refunds
---

# Stripe Payments Reviewer

## Purpose

Catch the Stripe-specific mistakes that generic `security-review` and `backend-review` miss —
the ones that produce double charges, unverified webhooks, or drifted amounts. This skill
**extends** both: run them first; this pass assumes generic auth/injection/logic issues are
already covered and goes deep on the payment surface only.

## Extends

- **Skills:** `security-review`, `backend-review`
- **Sibling:** `payment-idempotency-reviewer` (run it when money-movement flows change beyond Stripe calls)

## What this skill checks (beyond the generic reviews)

### Webhooks

- Signature verified with the SDK helper (`constructEvent` / `Webhook.constructEvent`) using the
  **raw** request body — a parsed/re-serialized body breaks verification silently.
- Webhook secret comes from the environment contract, never inline; a distinct secret per endpoint.
- Handler is idempotent: the same `event.id` delivered twice must not double-apply (Stripe retries).
- Handler returns 2xx fast and defers slow work — Stripe times out at ~10s and retries, causing duplicates.
- Unhandled event types are acknowledged (2xx + log), not errored — otherwise the endpoint gets disabled.
- Event data is treated as untrusted input: look up the object fresh from Stripe or your DB for
  authorization decisions; never trust `metadata` for access control.

### Idempotency and retries

- Mutating Stripe calls (`paymentIntents.create`, `charges`, `refunds`, `subscriptions`) pass an
  **idempotency key** derived from your domain (order ID), not a random UUID per attempt.
- Client-side retry loops around Stripe calls reuse the same key.

### Amounts and currency

- Amounts sent to Stripe are **integer minor units** (cents); flag any `float`/`double`/decimal
  multiplication at the call site (`amount * 100` on a float is a bug factory).
- Zero-decimal currencies (JPY, KRW) handled — no blanket `* 100`.
- The currency sent matches the currency stored; no hardcoded `"eur"`/`"usd"` where the order carries one.
- Displayed amount and charged amount derive from the same source of truth.

### Keys, config, and API version

- Secret keys only server-side; publishable keys only client-side; no key material in logs or error messages.
- Test vs live separation via environment contract — no conditionals on key prefixes in code.
- API version pinned (SDK config or dashboard note in the spec); an unpinned version makes
  webhook payload shapes drift under you.

### Lifecycle correctness

- The state machine handles: `payment_intent.succeeded`, `payment_intent.payment_failed`, and
  asynchronous methods that succeed **later** — success is not assumed at redirect time.
- Refunds update local state via webhook, not optimistically.
- Disputes (`charge.dispute.created`) at least log/alert — silence loses the dispute by default.
- Checkout Session/PaymentIntent reuse: abandoned sessions expire, retried orders do not stack
  multiple open intents for the same cart.

## Output format

```markdown
## Stripe Payments Review

**Verdict:** PASS | PASS WITH NOTES | FAIL

### Findings

| # | Category | Severity | File:Line | Finding | Action |
|---|---|---|---|---|---|
| 1 | Webhook | Critical | `route.ts:18` | Signature check uses parsed JSON body | Verify against raw body |

### Money-path trace

- (One paragraph: where the amount originates, every transformation until the Stripe call, and where truth is stored)

### Recommendations

- (Non-blocking hardening)
```

## What this skill does NOT do

- Does not review generic auth/injection/logging (that's `security-review`).
- Does not design pricing, tax, or invoicing strategy.
- Does not cover non-Stripe processors — the idempotency sibling skill is processor-agnostic.
- Does not modify code.
