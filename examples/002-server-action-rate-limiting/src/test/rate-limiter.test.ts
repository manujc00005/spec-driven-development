import { describe, it, expect } from "vitest";
import { SlidingWindowRateLimiter } from "../lib/rate-limiter";

/** Controllable clock: tests move time explicitly, no fake timers needed. */
function clockAt(start = 0) {
  let now = start;
  return {
    now: () => now,
    advance: (ms: number) => {
      now += ms;
    },
  };
}

describe("SlidingWindowRateLimiter", () => {
  it("allows up to the limit within one window", () => {
    const clock = clockAt();
    const limiter = new SlidingWindowRateLimiter({ limit: 3, windowMs: 1000, now: clock.now });

    expect(limiter.check("a").allowed).toBe(true);
    expect(limiter.check("a").allowed).toBe(true);
    expect(limiter.check("a").allowed).toBe(true);
    expect(limiter.check("a").allowed).toBe(false);
  });

  it("reports remaining slots as they are consumed", () => {
    const clock = clockAt();
    const limiter = new SlidingWindowRateLimiter({ limit: 3, windowMs: 1000, now: clock.now });

    expect(limiter.check("a").remaining).toBe(2);
    expect(limiter.check("a").remaining).toBe(1);
    expect(limiter.check("a").remaining).toBe(0);
    expect(limiter.check("a").remaining).toBe(0); // denied
  });

  it("slides: a hit re-opens exactly when the oldest hit leaves the window", () => {
    const clock = clockAt();
    const limiter = new SlidingWindowRateLimiter({ limit: 2, windowMs: 1000, now: clock.now });

    limiter.check("a"); // t=0
    clock.advance(600);
    limiter.check("a"); // t=600
    clock.advance(300); // t=900 — both hits still inside
    expect(limiter.check("a").allowed).toBe(false);

    clock.advance(101); // t=1001 — the t=0 hit just left the window
    expect(limiter.check("a").allowed).toBe(true);
  });

  it("boundary: a hit exactly windowMs old no longer counts", () => {
    const clock = clockAt();
    const limiter = new SlidingWindowRateLimiter({ limit: 1, windowMs: 1000, now: clock.now });

    limiter.check("a"); // t=0
    clock.advance(1000); // t=1000: hit timestamp 0 <= windowStart 0 → expired
    expect(limiter.check("a").allowed).toBe(true);
  });

  it("denied calls do not consume slots (no perpetual lockout on retries)", () => {
    const clock = clockAt();
    const limiter = new SlidingWindowRateLimiter({ limit: 1, windowMs: 1000, now: clock.now });

    limiter.check("a"); // consumes the only slot at t=0
    clock.advance(500);
    limiter.check("a"); // denied — must NOT extend the lockout
    clock.advance(501); // t=1001: original hit expired
    expect(limiter.check("a").allowed).toBe(true);
  });

  it("retryAfterMs counts down to the oldest hit's expiry", () => {
    const clock = clockAt();
    const limiter = new SlidingWindowRateLimiter({ limit: 1, windowMs: 1000, now: clock.now });

    limiter.check("a"); // t=0
    clock.advance(400);
    expect(limiter.check("a").retryAfterMs).toBe(600);
  });

  it("keys are isolated: one client's burst never affects another", () => {
    const clock = clockAt();
    const limiter = new SlidingWindowRateLimiter({ limit: 1, windowMs: 1000, now: clock.now });

    expect(limiter.check("a").allowed).toBe(true);
    expect(limiter.check("a").allowed).toBe(false);
    expect(limiter.check("b").allowed).toBe(true);
  });

  it("evicts the least-recently-seen key at maxKeys (bounded memory)", () => {
    const clock = clockAt();
    const limiter = new SlidingWindowRateLimiter({ limit: 1, windowMs: 1000, maxKeys: 2, now: clock.now });

    limiter.check("old"); // t=0
    clock.advance(10);
    limiter.check("mid"); // t=10
    clock.advance(10);
    limiter.check("new"); // t=20 → store full, "old" evicted
    expect(limiter.size()).toBe(2);

    // "old" was evicted, so it gets a fresh window — by design: bounded memory
    // is bought with forgiveness for evicted keys, not with unbounded growth.
    expect(limiter.check("old").allowed).toBe(true);
  });

  it("rejects nonsensical configuration", () => {
    expect(() => new SlidingWindowRateLimiter({ limit: 0, windowMs: 1000 })).toThrow();
    expect(() => new SlidingWindowRateLimiter({ limit: 1, windowMs: 0 })).toThrow();
  });
});
