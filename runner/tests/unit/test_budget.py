"""FR-004: the budget is a hard ceiling checked BEFORE dispatch."""

import unittest

from sdd_runner.budget import Budget, BudgetExhausted, default_cap


class DefaultCap(unittest.TestCase):
    def test_task_relative_with_a_floor_of_25(self):
        self.assertEqual(default_cap(0), 25)
        self.assertEqual(default_cap(4), 25)
        self.assertEqual(default_cap(5), 30)
        self.assertEqual(default_cap(24), 144)


class Spending(unittest.TestCase):
    def test_refuses_the_n_plus_first_charge(self):
        b = Budget(3)
        for _ in range(3):
            b.charge()
        self.assertFalse(b.can_dispatch())
        with self.assertRaises(BudgetExhausted):
            b.charge()
        self.assertEqual(b.used, 3)

    def test_monotonic_and_never_reset(self):
        b = Budget(10, used=4)
        b.raise_cap(20, "explicit override on re-entry")
        self.assertEqual(b.used, 4)
        self.assertEqual(b.cap, 20)

    def test_cap_may_only_increase(self):
        b = Budget(10)
        with self.assertRaises(ValueError):
            b.raise_cap(9, "attempted reduction")


if __name__ == "__main__":
    unittest.main()
