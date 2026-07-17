# Feature Spec: server-action-rate-limiting

> Part of the worked example — this is the SPEC a real project would write for
> this feature, produced with `/spec-create`.

## Status

Done

## Problem

The public newsletter-subscribe server action is reachable without
authentication. Nothing stops a bot from submitting thousands of addresses
(spam, list poisoning, downstream email costs) or from using response
differences to probe which emails are already subscribed.

## Goal

Rate-limit the action per client, validate all input before it reaches
persistence, and make every rejection indistinguishable from the outside.

## Non-goals

- Distributed rate limiting (single-instance dampening is the scope; the store
  interface is the documented swap point for Redis/Upstash).
- CAPTCHA or proof-of-work challenges.
- Auth-gated mutations (different threat model: the key would be the user id,
  not the IP).

## Users / Actors

- Legitimate visitor subscribing once (must never notice the limiter).
- Bot submitting in bulk (must be dampened cheaply).
- Attacker probing for enumeration or limiter thresholds (must learn nothing).

## Current behavior

The action validates nothing and accepts unlimited submissions.

## Desired behavior

Requests are keyed by client IP (proxy-appended entry only), limited to 5 per
10 minutes via a sliding window, validated with zod, and answered with a
constant-shape response carrying one generic error string.

## Functional requirements

- FR-001: Sliding-window limiter, 5 hits / 10 min per key, in-memory with a
  bounded key store (LRU eviction) so key rotation cannot grow memory
  unboundedly.
- FR-002: Client key = the x-forwarded-for entry appended by the trusted proxy
  (configurable trusted-proxy count); absent/empty header → shared "unknown"
  bucket, never a bypass.
- FR-003: Rate limit runs BEFORE validation (cheapest check first); zod
  validation runs before any work; the honeypot field rejects with the same
  generic error as every other failure.
- FR-004: Limiter failure fails CLOSED for this unauthenticated mutation.
- FR-005: Response shape is constant — `{ ok }` or `{ ok, error }` with one
  generic message; no field-level errors, no retry-after leak, idempotent
  persistence so duplicates are indistinguishable from first-time success.
- FR-006: Denied requests consume no slot (no perpetual lockout for retries).

## Non-functional requirements

- Performance: O(hits-in-window) per check; eviction O(keys) only at capacity.
- Security: see FR-002..005 — the trust boundary and information-leak
  requirements ARE the feature.
- Observability: limiter exposes `size()`; production would add a denied-count
  metric (out of scope here).
- Maintainability: store swappable behind `SlidingWindowRateLimiter`'s
  interface without touching the action.

## API / Interface changes

New server action `subscribe(formData)` → `{ ok: boolean; error?: string }`.

## Data model changes

None in the example (persistence is an illustrative idempotent upsert stub).

## Edge cases

- Hit exactly `windowMs` old → expired (boundary is exclusive).
- Attacker prepends fake IPs in x-forwarded-for → only the proxy-appended
  entry is read; victim-IP poisoning is ignored the same way.
- More trusted proxies configured than header entries → clamp, never crash.
- Store at `maxKeys` → least-recently-seen key evicted; evicted keys get a
  fresh window (bounded memory is bought with forgiveness, documented).
- `headers()` throwing → fail closed (generic error).

## Acceptance criteria

- AC-001: 6th request within 10 minutes from one IP is denied; a different IP
  is unaffected.
- AC-002: Spoofed x-forwarded-for prefixes change nothing (test-covered).
- AC-003: Honeypot, invalid email, and rate-limit rejections return the
  identical error string.
- AC-004: Denied retries do not extend the lockout; the window re-opens exactly
  when the oldest counted hit expires (test-covered to the millisecond).
- AC-005: Store never exceeds `maxKeys`.

## Test scenarios

- Unit: 9 limiter cases (limits, sliding boundary, retry-after, isolation,
  eviction, config validation) + 8 client-IP cases (spoofing, poisoning,
  proxy-count clamping, empty-header fallback).
- Integration/E2E/manual: out of scope for the example — listed in
  IMPLEMENTATION_SUMMARY as what a real project would add.

## Assumptions

- Exactly one trusted proxy in front of the app (Vercel-like default),
  configurable via `trustedProxyCount`.
- Subscribe is a rare human action: 5/10min hurts no legitimate user.

## Open questions

- None.
