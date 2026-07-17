import { describe, it, expect } from "vitest";
import { clientIpFrom, UNKNOWN_CLIENT } from "../lib/client-ip";

function headersWith(xff?: string): Headers {
  const h = new Headers();
  if (xff !== undefined) h.set("x-forwarded-for", xff);
  return h;
}

describe("clientIpFrom — the trust boundary", () => {
  it("returns the shared 'unknown' bucket when the header is absent", () => {
    expect(clientIpFrom(headersWith())).toBe(UNKNOWN_CLIENT);
  });

  it("single entry behind one trusted proxy → that entry", () => {
    expect(clientIpFrom(headersWith("203.0.113.7"))).toBe("203.0.113.7");
  });

  it("SPOOF ATTEMPT: attacker prepends fake IPs — only the proxy-appended entry is used", () => {
    // The attacker sent "x-forwarded-for: 10.0.0.1, 172.16.0.1" with the
    // request; the trusted proxy appended the real address last.
    const spoofed = headersWith("10.0.0.1, 172.16.0.1, 203.0.113.7");
    expect(clientIpFrom(spoofed, 1)).toBe("203.0.113.7");
  });

  it("SPOOF ATTEMPT: victim's IP injected for limit-poisoning is ignored the same way", () => {
    const poisoned = headersWith("198.51.100.99, 203.0.113.7");
    expect(clientIpFrom(poisoned, 1)).not.toBe("198.51.100.99");
  });

  it("two trusted proxies → second entry from the right", () => {
    const h = headersWith("203.0.113.7, 10.1.1.1, 10.2.2.2");
    expect(clientIpFrom(h, 2)).toBe("10.1.1.1");
  });

  it("whitespace and empty segments are tolerated", () => {
    expect(clientIpFrom(headersWith("  203.0.113.7  ,, "))).toBe("203.0.113.7");
  });

  it("empty header value falls back to the shared bucket, never bypasses", () => {
    expect(clientIpFrom(headersWith(""))).toBe(UNKNOWN_CLIENT);
  });

  it("REGRESSION SEC-001: fewer entries than trusted proxies → shared bucket, never an attacker-writable entry", () => {
    // Original code clamped to entries[0] here — the leftmost, client-written
    // entry. With trustedProxyCount=3 and a single spoofed entry, the attacker
    // would have chosen their own rate-limit key.
    expect(clientIpFrom(headersWith("6.6.6.6"), 3)).toBe(UNKNOWN_CLIENT);
  });
});
