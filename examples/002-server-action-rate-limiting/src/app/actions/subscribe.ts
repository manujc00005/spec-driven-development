"use server";

import { headers } from "next/headers";
import { subscribeSchema, GENERIC_ERROR } from "../../lib/validation";
import { SlidingWindowRateLimiter } from "../../lib/rate-limiter";
import { clientIpFrom } from "../../lib/client-ip";

/**
 * Newsletter-subscribe server action: the reference pattern for any public
 * mutation reachable without auth.
 *
 * Order of checks (each one is cheaper than the next stage it protects):
 *   1. Rate limit BY CLIENT KEY — before validation, because validation is
 *      CPU the attacker spends for free if it runs first.
 *   2. Validate with zod — nothing downstream sees raw input.
 *   3. Do the work.
 *
 * Response shape is CONSTANT: { ok } | { ok, error } with one generic error
 * string. No timing/shape difference reveals which check rejected the request
 * or whether an email was already subscribed (enumeration).
 */

// Module-scope: one limiter per server process, shared across requests.
// 5 attempts / 10 minutes per client — subscribe is a rare human action.
const limiter = new SlidingWindowRateLimiter({
  limit: 5,
  windowMs: 10 * 60 * 1000,
});

export interface SubscribeResult {
  ok: boolean;
  error?: string;
}

export async function subscribe(formData: FormData): Promise<SubscribeResult> {
  // -- 1. Rate limit ---------------------------------------------------------
  let decision;
  try {
    const ip = clientIpFrom(await headers());
    decision = limiter.check(ip);
  } catch {
    // Fail CLOSED: if the limiter breaks, an unauthenticated public mutation
    // must reject, not open the floodgates (DECISIONS.md D003). For a
    // read-only or authenticated path, fail-open can be the right call —
    // the point is that the choice is explicit, not accidental.
    return { ok: false, error: GENERIC_ERROR };
  }
  if (!decision.allowed) {
    // Same generic error as validation: the limiter's existence and threshold
    // are not advertised to the caller.
    return { ok: false, error: GENERIC_ERROR };
  }

  // -- 2. Validate -----------------------------------------------------------
  const parsed = subscribeSchema.safeParse({
    email: formData.get("email"),
    website: formData.get("website") ?? "",
  });
  if (!parsed.success) {
    return { ok: false, error: GENERIC_ERROR };
  }

  // -- 3. Work ---------------------------------------------------------------
  // Illustrative stand-in for the real persistence call (e.g. Prisma upsert).
  // Idempotent by design: subscribing twice is a no-op, not an error — which
  // is also what makes the constant response shape possible.
  await persistSubscription(parsed.data.email);

  return { ok: true };
}

async function persistSubscription(_email: string): Promise<void> {
  // prisma.subscriber.upsert({ where: { email }, create: { email }, update: {} })
}
