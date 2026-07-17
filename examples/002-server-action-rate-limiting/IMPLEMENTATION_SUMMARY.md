# Implementation Summary: server-action-rate-limiting

> Part of the worked example — `/spec-close` output.

## What was built

A public Next.js server action protected in cheapest-check-first order:
sliding-window rate limit (5/10min per client key) → zod validation with a
honeypot → idempotent persistence. Client keys come only from the
proxy-appended x-forwarded-for entry; every rejection returns one constant
generic response.

## Acceptance criteria coverage

- AC-001 (limit + key isolation): Covered — limiter tests.
- AC-002 (spoof/poisoning resistance): Covered — named attack tests + SEC-001
  regression.
- AC-003 (constant rejection): Covered — single `GENERIC_ERROR` across paths.
- AC-004 (sliding semantics, no retry punishment): Covered — millisecond-pinned
  boundary tests via injected clock.
- AC-005 (bounded store): Covered — eviction test + `size()`.

## Review outcome

`/security-review` found one real High finding (SEC-001: the proxy-count clamp
selected an attacker-writable header entry) — fixed, with an inverted
regression test. Two risks accepted and documented (shared unknown-bucket
griefing; per-instance limits). See REVIEW_REPORT.md.

## What a real project would add next

- Swap the in-memory store for Redis/Upstash behind the existing interface
  (D002) when running more than one instance.
- Denied-requests metric + alerting before tuning thresholds.
- Integration test through the framework's action invocation path.
- Email verification / double-opt-in on the persistence side.

## What this is NOT

A production signup system or a distributed limiter — see README.md
disclaimers. The pattern and the artifact trail are the deliverable.
