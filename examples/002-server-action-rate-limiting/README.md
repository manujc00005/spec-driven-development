# Worked Example: Server Action Rate Limiting (Next.js / TypeScript)

An end-to-end pass of the SDD workflow over a TypeScript feature: protecting a
public Next.js server action with **input validation** (zod), a
**sliding-window rate limiter**, and an **enumeration-resistant response
contract**. The TypeScript counterpart to the
[payment webhook example](../001-payment-webhook-idempotency/) — same workflow,
different stack (`next-prisma-web` profile territory).

> **Educational example.** It shows the workflow and the pattern faithfully —
> it is **not** a complete production system. Read
> [What this example is NOT](#what-this-example-is-not) before copying code.

## What it demonstrates

1. **The SDD artifact trail** — [SPEC](SPEC.md) → [PLAN](PLAN.md) →
   [TASKS](TASKS.md) → [DECISIONS](DECISIONS.md) →
   [REVIEW_REPORT](REVIEW_REPORT.md) → [IMPLEMENTATION_SUMMARY](IMPLEMENTATION_SUMMARY.md),
   exactly as `/spec-create` → `/spec-plan` → `/spec-implement` →
   `/security-review` → `/spec-close` produce them.
2. **Cheapest-check-first ordering** — rate limit before validation before
   work, so attacker requests spend the least of your CPU
   ([subscribe.ts](src/app/actions/subscribe.ts)).
3. **The x-forwarded-for trust boundary** — why the client-controlled part of
   the header must never become a rate-limit key, with named spoofing and
   limit-poisoning attack tests ([client-ip.ts](src/lib/client-ip.ts),
   [client-ip.test.ts](src/test/client-ip.test.ts)).
4. **Sliding-window mechanics you can pin in a test** — re-opens exactly when
   the oldest hit expires, denied retries consume nothing, bounded key store
   with LRU eviction ([rate-limiter.ts](src/lib/rate-limiter.ts), 9 test
   cases with an injected clock — no fake timers).
5. **Enumeration resistance as a spec requirement** — one generic error for
   every rejection path, constant response shape, idempotent persistence
   (DECISIONS [D005](DECISIONS.md)).
6. **Explicit failure policy** — fail-closed on limiter errors for an
   unauthenticated mutation, with the reasoning recorded
   (DECISIONS [D003](DECISIONS.md)).

## Layout

```
SPEC.md · PLAN.md · TASKS.md · DECISIONS.md      # the workflow artifacts
REVIEW_REPORT.md                                 # /security-review output
IMPLEMENTATION_SUMMARY.md                        # /spec-close output
src/
  app/actions/subscribe.ts                       # the server action
  lib/rate-limiter.ts                            # sliding window + LRU bound
  lib/client-ip.ts                               # trust-boundary helper
  lib/validation.ts                              # zod schema + honeypot
  test/rate-limiter.test.ts                      # 9 cases, injected clock
  test/client-ip.test.ts                         # 8 cases, incl. attack tests
```

Source files are **educational fragments** (same convention as example 001):
there is no `package.json`/`tsconfig` and the tests are written for vitest but
meant to be read here, not executed here.

## What this example is NOT

- **A distributed rate limiter.** The store is an in-process Map: it resets on
  deploy and counts per instance (effective limit = limit × instances behind a
  load balancer). The class interface is the documented seam for
  Redis/Upstash. See DECISIONS [D002](DECISIONS.md).
- **A production signup system.** Persistence is an illustrative idempotent
  stub; there is no email verification, no double-opt-in, no observability.
- **A CAPTCHA replacement.** Rate limiting dampens abuse; it does not
  authenticate humanity.
- **Copy-paste security.** `trustedProxyCount` must match YOUR proxy chain —
  the default (1) is right for Vercel-like setups and wrong for others.

## Where SDD earned its keep

- The **enumeration requirement (FR-005)** existed in the SPEC before any code
  — it shaped the error handling instead of being retrofitted.
- The **fail-open/fail-closed choice** would normally be an accident of
  whoever wrote the try/catch; here it is DECISIONS D003 with the trade-off
  recorded.
- The **security review found real issues** (see
  [REVIEW_REPORT](REVIEW_REPORT.md)) — including one the original code got
  wrong — and the trail shows the fix, not just the polished result.
