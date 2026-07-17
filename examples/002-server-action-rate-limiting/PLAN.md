# Implementation Plan: server-action-rate-limiting

> Part of the worked example — produced with `/spec-plan`.

## Summary

Three small modules behind one action: a clock-injectable sliding-window
limiter with bounded key storage, a trust-boundary-aware client-IP helper, and
a zod schema with a honeypot — composed in `subscribe.ts` in
cheapest-check-first order with a constant response shape.

## Related spec

`SPEC.md` (this folder).

## Impacted areas

- `src/lib/rate-limiter.ts` — new
- `src/lib/client-ip.ts` — new
- `src/lib/validation.ts` — new
- `src/app/actions/subscribe.ts` — new
- `src/test/rate-limiter.test.ts`, `src/test/client-ip.test.ts` — new

## Proposed approach

1. Limiter first, TDD with an injected clock (no fake timers): timestamps
   array per key, prune-from-front on each check, LRU eviction at `maxKeys`.
2. Client-IP helper as a pure function over `Headers`: rightmost-minus-N
   parsing, shared "unknown" bucket fallback.
3. Schema with normalization (trim/lowercase) and the honeypot literal.
4. Action composes them: limit → validate → idempotent work; single generic
   error constant shared by every rejection path; fail-closed try/catch around
   the limiter.

## Alternatives considered

- **Fixed window** — rejected: burst at the boundary allows 2× the limit in
  seconds; sliding window costs a few timestamps per key.
- **Token bucket** — fine algorithm, but sliding window is easier to reason
  about in tests ("exactly when does it re-open?") — teaching value decided.
- **Middleware-level limiting** — rejected for the example: the action is the
  unit under spec; middleware placement is a deployment concern noted in the
  README.

## Dependencies

`zod` and Next.js `headers()` — both standard in the target stack. Tests
written for vitest.

## Risks

- In-memory store limits are per-instance — mitigated by documenting loudly
  (README, DECISIONS D002, code comment) rather than pretending otherwise.
- IP keying is only as good as the proxy config — `trustedProxyCount` is
  explicit instead of guessed.

## Test strategy

Unit tests only, by design (see SPEC test scenarios): limiter boundary
behavior to the millisecond via injected clock; client-IP spoofing/poisoning
cases as named attack tests.

## Rollback strategy

Feature-flag or remove the limiter call in the action; modules are additive.

## PLAN verification checklist

- [x] The plan covers all acceptance criteria.
- [x] The plan avoids behavior outside the spec.
- [x] Risks are documented.
- [x] Test strategy is documented.
- [x] Rollback strategy is documented.
- [x] SPEC.md status updated.
