/**
 * Sliding-window rate limiter, in-memory.
 *
 * SCOPE (read this before copying): the store is a per-process Map. It resets
 * on every deploy/restart and is NOT shared across instances — behind a
 * load balancer each instance enforces its own window, so the effective limit
 * is limit × instances. That is acceptable for abuse *dampening* on a single
 * instance and for teaching the algorithm; for a hard guarantee swap the store
 * for Redis/Upstash behind this same interface (DECISIONS.md D002).
 */

export interface RateLimitResult {
  allowed: boolean;
  /** Requests remaining in the current window (0 when denied). */
  remaining: number;
  /** Milliseconds until the oldest counted request leaves the window. */
  retryAfterMs: number;
}

interface WindowState {
  /** Timestamps (ms) of requests still inside the window, oldest first. */
  hits: number[];
  /** Last touch, for LRU eviction. */
  lastSeen: number;
}

export interface RateLimiterOptions {
  /** Max requests allowed per window. */
  limit: number;
  /** Window length in milliseconds. */
  windowMs: number;
  /**
   * Max tracked keys. Without a bound, an attacker rotating keys (e.g.
   * spoofed IPs) grows the Map without limit — the limiter itself becomes
   * the DoS vector. Oldest-seen keys are evicted first.
   */
  maxKeys?: number;
  /** Clock injection for tests. */
  now?: () => number;
}

export class SlidingWindowRateLimiter {
  private readonly store = new Map<string, WindowState>();
  private readonly limit: number;
  private readonly windowMs: number;
  private readonly maxKeys: number;
  private readonly now: () => number;

  constructor(options: RateLimiterOptions) {
    if (options.limit < 1) throw new Error("limit must be >= 1");
    if (options.windowMs < 1) throw new Error("windowMs must be >= 1");
    this.limit = options.limit;
    this.windowMs = options.windowMs;
    this.maxKeys = options.maxKeys ?? 10_000;
    this.now = options.now ?? Date.now;
  }

  /**
   * Records a hit for `key` and reports whether it is allowed.
   * One call = one consumed slot when allowed; denied calls consume nothing,
   * so a client that keeps retrying while blocked is not punished forever.
   */
  check(key: string): RateLimitResult {
    const now = this.now();
    const windowStart = now - this.windowMs;

    let state = this.store.get(key);
    if (!state) {
      this.evictIfFull();
      state = { hits: [], lastSeen: now };
      this.store.set(key, state);
    }
    state.lastSeen = now;

    // Drop hits that slid out of the window. Hits are appended in time order,
    // so a single scan from the front suffices.
    let firstInside = 0;
    while (firstInside < state.hits.length && state.hits[firstInside] <= windowStart) {
      firstInside++;
    }
    if (firstInside > 0) state.hits = state.hits.slice(firstInside);

    if (state.hits.length >= this.limit) {
      const oldest = state.hits[0];
      return {
        allowed: false,
        remaining: 0,
        retryAfterMs: Math.max(0, oldest + this.windowMs - now),
      };
    }

    state.hits.push(now);
    return {
      allowed: true,
      remaining: this.limit - state.hits.length,
      retryAfterMs: 0,
    };
  }

  /** Tracked key count — exposed for tests and observability. */
  size(): number {
    return this.store.size;
  }

  private evictIfFull(): void {
    if (this.store.size < this.maxKeys) return;
    // Evict the least-recently-seen key. O(n) scan is fine at this scale;
    // a real distributed store makes this Redis's problem, not ours.
    let oldestKey: string | undefined;
    let oldestSeen = Infinity;
    for (const [key, state] of this.store) {
      if (state.lastSeen < oldestSeen) {
        oldestSeen = state.lastSeen;
        oldestKey = key;
      }
    }
    if (oldestKey !== undefined) this.store.delete(oldestKey);
  }
}
