"""Bounded retry policy — spec 040 FR-010.

Transport and transient provider failures are retried under a bounded policy:
finite attempts, exponential backoff, per-attempt timeout. EVERY retry consumes
the delegation budget (031 FR-009 counts structured-output retries). Exhausted
retries fail the delegation CLOSED — never silently.
"""

from dataclasses import dataclass


class TransportError(RuntimeError):
    """A transient provider/transport failure. Retryable."""


class DelegationFailedClosed(RuntimeError):
    """Retries exhausted. The caller must treat this as a failed delegation."""


@dataclass
class RetryPolicy:
    attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 30.0
    timeout: float = 900.0

    def delay_for(self, attempt: int) -> float:
        return min(self.max_delay, self.base_delay * (2 ** max(0, attempt - 1)))


def call_with_retry(fn, policy, budget, sleep, on_attempt=None, reason=""):
    """Invoke `fn`, charging the budget for every attempt including retries.

    The budget is charged BEFORE each attempt; if it cannot be charged the call
    is never made.
    """
    last = None
    for attempt in range(1, policy.attempts + 1):
        budget.charge(1, reason="%s (attempt %d)" % (reason, attempt))
        if on_attempt:
            on_attempt(attempt)
        try:
            return fn(policy.timeout)
        except TransportError as exc:
            last = exc
            if attempt < policy.attempts:
                sleep(policy.delay_for(attempt))
    raise DelegationFailedClosed(
        "delegation failed closed after %d attempts: %s" % (policy.attempts, last)
    )
