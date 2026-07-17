/**
 * Client-IP extraction — the trust boundary most rate limiters get wrong.
 *
 * `x-forwarded-for` is CLIENT-CONTROLLED unless a proxy you operate overwrites
 * it. Trusting it blindly hands attackers two attacks at once:
 *   1. Bypass: rotate the header value → every request gets a fresh limit.
 *   2. Poisoning: send a victim's IP → exhaust the victim's limit for them.
 *
 * The safe rule: only read the entry appended by YOUR proxy. Behind one
 * trusted proxy (Vercel, a single nginx), that is the LAST entry — everything
 * to its left arrived in the request and is attacker-writable.
 */

/** Fallback key when no address is available; groups such requests together
 * under one (strict) shared bucket rather than letting them bypass limits. */
export const UNKNOWN_CLIENT = "unknown";

export function clientIpFrom(headers: Headers, trustedProxyCount = 1): string {
  const xff = headers.get("x-forwarded-for");
  if (!xff) return UNKNOWN_CLIENT;

  const entries = xff
    .split(",")
    .map((part) => part.trim())
    .filter(Boolean);
  if (entries.length === 0) return UNKNOWN_CLIENT;

  // With N trusted proxies, the client IP is the Nth entry from the right.
  // Entries further left are unverified claims, never used as keys.
  const index = entries.length - trustedProxyCount;
  if (index < 0) {
    // Fewer entries than trusted proxies: the request did not traverse the
    // full trusted chain, so every entry present is an unverified claim.
    // Clamping to entries[0] here would hand the key to the attacker
    // (REVIEW_REPORT SEC-001) — fall back to the strict shared bucket instead.
    return UNKNOWN_CLIENT;
  }
  return entries[index] ?? UNKNOWN_CLIENT;
}
