# Security Review: server-action-rate-limiting

> Part of the worked example — `/security-review` output over this folder's
> code, kept verbatim so the trail shows a real finding and its fix, not just
> the polished end state.

## Verdict

**Pass** (after fixing SEC-001)

## Confirmed findings

### SEC-001 — Proxy-count clamp handed the rate-limit key to the attacker

- **Severity:** High (for the pattern being taught; Medium in the concrete
  5-req/10-min context)
- **Location:** `src/lib/client-ip.ts`, original clamp
  `entries[Math.max(0, index)]`
- **Risk:** With `trustedProxyCount` greater than the number of header entries
  (misconfiguration, or an internal request that skipped part of the chain),
  the index went negative and the clamp selected `entries[0]` — the leftmost,
  **client-written** entry. An attacker sending a single spoofed entry would
  choose their own rate-limit key, re-enabling both bypass (rotate keys) and
  poisoning (spend a victim's budget) — exactly the attacks the helper exists
  to stop.
- **Evidence:** the original test asserted the clamp
  (`clientIpFrom(headersWith("203.0.113.7"), 3)` → `"203.0.113.7"`), proving
  the behavior was designed-in, not incidental.
- **Fix applied:** when `entries.length < trustedProxyCount`, return
  `UNKNOWN_CLIENT` (strict shared bucket). Regression test renamed and
  inverted: `REGRESSION SEC-001` now asserts the shared-bucket fallback.

## Accepted risks (documented, not fixed)

- **Shared "unknown" bucket griefing** — clients whose requests carry no
  x-forwarded-for share one 5/10min budget; a flood of header-less requests
  starves legitimate header-less users. Accepted: in the target deployment the
  trusted proxy always appends the header, so the bucket only sees anomalous
  traffic — and the failure mode (a lost signup) is the fail-closed posture
  already chosen in DECISIONS D003.
- **Per-instance limits** (in-memory store) — effective limit multiplies by
  instance count. Accepted and triple-documented (code header, README,
  DECISIONS D002); the store interface is the swap point.

## Checks that passed

- Validation precedes all work; nothing downstream reads raw input.
- Rejections are shape- and message-constant across honeypot, validation, and
  limiter paths (enumeration resistance, FR-005).
- Denied requests consume no slot — no self-inflicted permanent lockout.
- Key store is bounded (`maxKeys` + LRU eviction) — the limiter cannot be
  turned into the memory-DoS vector.
- Fail-closed on limiter exceptions for this unauthenticated mutation.
- No secrets, no logging of user input, idempotent persistence stub.

## Notes for real deployments

- Set `trustedProxyCount` from your actual topology; both directions of error
  are harmful (too low → attacker-writable key; too high → shared bucket).
- Add a denied-requests metric before tuning limits.
