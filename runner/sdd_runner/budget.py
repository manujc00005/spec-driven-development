"""Delegation budget — spec 031 FR-009, spec 040 FR-004.

The delegation budget is the SOLE global monotonic backstop against an unbounded
run. It counts every delegated worker, reviewer, deep-reasoner call and
structured-output retry, re-approvals included. Deterministic local commands and
same-context owning-skill calls are logged but do not consume it.

The default is task-relative and computed ONCE at first entry:

    max_delegations = max(25, 6 * unchecked_tasks_at_first_entry)

Spend is checked BEFORE dispatch. `charge()` raises rather than allowing an
over-budget call to be made and noticed afterwards.
"""

FLOOR = 25
PER_TASK = 6


class BudgetExhausted(RuntimeError):
    def __init__(self, used, cap):
        super().__init__(
            "delegation budget exhausted: %d of %d used; refusing to dispatch" % (used, cap)
        )
        self.used = used
        self.cap = cap


def default_cap(unchecked_tasks: int) -> int:
    return max(FLOOR, PER_TASK * max(0, int(unchecked_tasks)))


class Budget:
    def __init__(self, cap: int, used: int = 0):
        self.cap = int(cap)
        self.used = int(used)

    def can_dispatch(self, n: int = 1) -> bool:
        """031: prove `used + 1 <= cap` BEFORE allocating the attempt."""
        return self.used + n <= self.cap

    def charge(self, n: int = 1, reason: str = "") -> int:
        if not self.can_dispatch(n):
            raise BudgetExhausted(self.used, self.cap)
        self.used += n
        return self.used

    def raise_cap(self, new_cap: int, reason: str) -> dict:
        """Re-entry may only INCREASE an effective cap; never reduce, never reset.

        031 FR-009: on authenticated re-entry an explicit override may only
        increase an effective cap; it may never reduce a cap below its stored
        value or reset any counter.
        """
        new_cap = int(new_cap)
        if new_cap < self.cap:
            raise ValueError(
                "cap may not be reduced: stored %d, requested %d" % (self.cap, new_cap)
            )
        old, self.cap = self.cap, new_cap
        return {"old": old, "new": new_cap, "reason": reason}

    @property
    def remaining(self) -> int:
        return max(0, self.cap - self.used)
