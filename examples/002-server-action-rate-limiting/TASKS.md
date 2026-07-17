# Tasks: server-action-rate-limiting

> Part of the worked example — produced with `/spec-plan`, executed with
> `/spec-implement`.

## Phase 1: Preparation

- [x] T001 - Test skeleton with injectable clock helper (no fake timers). Covers: AC-004 (infrastructure).

## Phase 2: Implementation

- [x] T002 - `SlidingWindowRateLimiter`: per-key timestamp window, prune-from-front, `remaining`/`retryAfterMs`, config validation. Covers: AC-001, AC-004.
- [x] T003 - Bounded key store: `maxKeys` + least-recently-seen eviction; `size()` for observability. Covers: AC-005.
- [x] T004 - `clientIpFrom(headers, trustedProxyCount)`: rightmost-minus-N parsing, whitespace tolerance, `UNKNOWN_CLIENT` shared bucket. Covers: AC-002.
- [x] T005 - `subscribeSchema` (trim/lowercase/max-length email, honeypot literal) + single `GENERIC_ERROR` constant. Covers: AC-003.
- [x] T006 - `subscribe` action: limit → validate → idempotent work; fail-closed limiter guard; constant response shape. Covers: AC-001, AC-003, AC-004.

## Phase 3: Tests

- [x] T007 - Limiter cases: limit, remaining, sliding re-open to the ms, boundary expiry, denied-consumes-nothing, retryAfter, key isolation, eviction, config errors. Covers: AC-001, AC-004, AC-005.
- [x] T008 - Client-IP cases: absent/empty header fallback, spoof-prefix attack, victim-poisoning attack, multi-proxy, clamping. Covers: AC-002.

## Phase 4: Review

- [x] T009 - `/security-review` on the example (see REVIEW_REPORT.md); fixes folded in. Covers: all ACs.
