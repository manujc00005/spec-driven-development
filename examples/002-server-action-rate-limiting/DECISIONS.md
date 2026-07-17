# Decisions: server-action-rate-limiting

> Part of the worked example — the decision log a real project would keep.

## Decision log

### D001 - Sliding window over fixed window and token bucket

**Date:** 2026-07-17

**Status:** Accepted

**Context:** Fixed windows allow a 2× burst straddling the boundary; token
bucket smooths but its state is harder to assert in tests.

**Decision:** Sliding window over a per-key timestamp log.

**Reasoning:** No boundary burst, and "the window re-opens exactly when the
oldest hit expires" is a property a test can pin to the millisecond — the
teaching goal of this example.

**Consequences:** Memory is O(limit) per key instead of O(1) — bounded and
acceptable at limit=5.

### D002 - In-memory store, interface as the swap point

**Date:** 2026-07-17

**Status:** Accepted

**Context:** A per-process Map resets on deploy and is per-instance behind a
load balancer (effective limit = limit × instances).

**Decision:** Ship in-memory with the limitation documented in three places
(code header, README, this log); the class interface is the seam where
Redis/Upstash slots in.

**Reasoning:** The example teaches the algorithm and the trust boundary; a
Redis dependency would bury both under infrastructure. Honesty over illusion:
in-memory is *dampening*, not a hard guarantee.

**Consequences:** Copy-pasters get single-instance protection until they swap
the store — stated, not hidden.

### D003 - Fail closed on limiter errors

**Date:** 2026-07-17

**Status:** Accepted

**Context:** If `headers()` or the limiter throws, the action must choose:
serve without protection (open) or reject (closed).

**Decision:** Fail closed for this unauthenticated public mutation.

**Reasoning:** The worst case of closed is a lost signup during an incident;
the worst case of open is unlimited spam exactly when the protection broke.
For read-only or authenticated paths the trade-off can invert — the decision
must be explicit either way.

**Consequences:** Limiter bugs surface as user-visible rejections (loud, not
silent).

### D004 - Key by proxy-appended x-forwarded-for entry only

**Date:** 2026-07-17

**Status:** Accepted

**Context:** x-forwarded-for is client-writable except for the entries your
own proxies append; trusting it blindly enables both limit bypass (rotate
fake IPs) and limit poisoning (spend a victim's budget).

**Decision:** Read the Nth-from-right entry with N = `trustedProxyCount`
(explicit parameter, default 1); missing/empty header → shared strict bucket.

**Reasoning:** The rightmost-minus-N rule is the only header interpretation
that survives an adversarial client behind a known proxy chain.

**Consequences:** Misconfigured `trustedProxyCount` shifts the key — the
parameter is documented as deployment-critical.

### D005 - One generic error for every rejection

**Date:** 2026-07-17

**Status:** Accepted

**Context:** Field-level errors are friendlier UX; this endpoint is also a
probe target (which check failed? is that email registered?).

**Decision:** Constant response shape, single generic message, idempotent
persistence so duplicate subscriptions look identical to first-time success.

**Reasoning:** Enumeration resistance outranks form UX on an
unauthenticated endpoint; a real product can re-add client-side (pre-submit)
validation hints without changing the server contract.

**Consequences:** Legitimate typo-makers get less guidance — accepted and
recorded as the UX cost of the security posture.
