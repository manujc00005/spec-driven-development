"""FR-010: bounded retries, charged to the budget, failing closed when exhausted."""

import unittest

from sdd_runner.budget import Budget, BudgetExhausted
from sdd_runner.retry import (DelegationFailedClosed, RetryPolicy, TransportError,
                              call_with_retry)


class Backoff(unittest.TestCase):
    def test_delay_grows_exponentially_and_is_capped(self):
        p = RetryPolicy(attempts=5, base_delay=1.0, max_delay=4.0)
        self.assertEqual([p.delay_for(n) for n in range(1, 5)], [1.0, 2.0, 4.0, 4.0])


class Charging(unittest.TestCase):
    def test_every_attempt_including_retries_consumes_budget(self):
        budget = Budget(10)
        slept = []
        calls = []

        def flaky(timeout):
            calls.append(timeout)
            if len(calls) < 3:
                raise TransportError("transient")
            return "ok"

        result = call_with_retry(flaky, RetryPolicy(attempts=3), budget, slept.append)
        self.assertEqual(result, "ok")
        self.assertEqual(len(calls), 3)
        self.assertEqual(budget.used, 3, "N attempts must decrement the budget by N")
        self.assertEqual(len(slept), 2)

    def test_exhausted_retries_fail_closed(self):
        budget = Budget(10)

        def always_fails(timeout):
            raise TransportError("down")

        with self.assertRaises(DelegationFailedClosed):
            call_with_retry(always_fails, RetryPolicy(attempts=3), budget, lambda s: None)
        self.assertEqual(budget.used, 3)

    def test_the_call_is_never_made_when_the_budget_cannot_be_charged(self):
        budget = Budget(1)
        budget.charge()
        made = []
        with self.assertRaises(BudgetExhausted):
            call_with_retry(lambda t: made.append(1), RetryPolicy(), budget, lambda s: None)
        self.assertEqual(made, [], "the provider must never be called over budget")

    def test_a_non_transport_error_is_not_retried(self):
        budget = Budget(10)
        calls = []

        def boom(timeout):
            calls.append(1)
            raise ValueError("a real bug, not a transport blip")

        with self.assertRaises(ValueError):
            call_with_retry(boom, RetryPolicy(attempts=3), budget, lambda s: None)
        self.assertEqual(len(calls), 1)


if __name__ == "__main__":
    unittest.main()
