"""FR-004: counter arithmetic against a table derived line by line from 031 FR-009.

Every expected value below cites the clause it comes from. The clauses are quoted
from skills/sdd-orchestrate/SKILL.md "Autonomous mode - convergence caps", which
is 031 FR-009 as corrected by 032 (D017/D008).
"""

import unittest

from sdd_runner.counters import CounterState


def finding(fid, severity="High"):
    return {"id": fid, "severity": severity, "evidence": "a.py:1",
            "summary": "s", "required_action": "r"}


class NoProgressStreak(unittest.TestCase):
    """"Increment on a REJECT - synthetic ones included - that resolves none of
    that reviewer's open findings.\""""

    def test_repeated_identical_reject_increments_every_round(self):
        c = CounterState(3)
        for expected in (1, 2, 3):
            summary = c.record_reject("domain", [finding("DOM-001")], 1)
            self.assertEqual(summary["no_progress_streak"], expected)

    def test_approve_resets_to_zero(self):
        """"Reset to zero on an APPROVE.\""""
        c = CounterState(3)
        c.record_reject("domain", [finding("DOM-001")], 1)
        c.record_reject("domain", [finding("DOM-001")], 2)
        self.assertEqual(c.reviewer("domain").no_progress_streak, 2)
        self.assertEqual(c.record_approve("domain", "fp")["no_progress_streak"], 0)

    def test_reject_resolving_a_prior_finding_resets_even_while_raising_new_ones(self):
        """"and equally on a REJECT that resolves at least one previously open
        finding of that reviewer, even when it raises new ones.\""""
        c = CounterState(3)
        c.record_reject("domain", [finding("DOM-001")], 1)
        c.record_reject("domain", [finding("DOM-001")], 2)
        summary = c.record_reject("domain", [finding("DOM-002")], 3)
        self.assertEqual(summary["no_progress_streak"], 0)
        self.assertEqual(summary["resolved"], ["domain:DOM-001"])

    def test_streaks_are_per_reviewer(self):
        c = CounterState(3)
        c.record_reject("domain", [finding("DOM-001")], 1)
        c.record_reject("domain", [finding("DOM-001")], 2)
        c.record_reject("security", [finding("SEC-001")], 2)
        self.assertEqual(c.reviewer("domain").no_progress_streak, 2)
        self.assertEqual(c.reviewer("security").no_progress_streak, 1)


class TotalInvocations(unittest.TestCase):
    """"Total invocations (audit only, never gates).\""""

    def test_approvals_count_for_audit_but_never_gate(self):
        c = CounterState(3)
        for _ in range(10):
            c.record_approve("domain", "fp", clean_reapproval=True)
        self.assertEqual(c.reviewer("domain").total_invocations, 10)
        self.assertEqual(c.reviewer("domain").clean_reapprovals, 10)
        self.assertIsNone(c.breached())
        self.assertFalse(c.would_exceed("domain"))


class PerFindingTotal(unittest.TestCase):
    """"Count a REJECT carrying the same <reviewer>:<finding-id> ONLY when a repair
    attempt for that finding has already completed with a worker DONE.\""""

    def test_bare_re_reports_do_not_increment(self):
        """"A finding re-reported while it still sits unworked in the queue does
        not increment anything.\""""
        c = CounterState(3)
        for i in range(5):
            c.record_reject("domain", [finding("DOM-001")], i)
        self.assertEqual(c.findings["domain:DOM-001"].reject_total, 0)

    def test_a_failed_repair_increments(self):
        c = CounterState(3)
        c.record_reject("domain", [finding("DOM-001")], 1)
        c.record_repair_done("domain:DOM-001")
        c.record_reject("domain", [finding("DOM-001")], 2)
        self.assertEqual(c.findings["domain:DOM-001"].reject_total, 1)

    def test_blocked_repair_is_not_a_failed_repair(self):
        """"A BLOCKED attempt is not a failed repair: nothing was changed.\""""
        c = CounterState(3)
        c.record_reject("domain", [finding("DOM-001")], 1)
        # No record_repair_done() call: the worker came back BLOCKED.
        c.record_reject("domain", [finding("DOM-001")], 2)
        self.assertEqual(c.findings["domain:DOM-001"].reject_total, 0)

    def test_flip_flop_is_caught_though_the_streak_keeps_resetting(self):
        """"this is what catches a flip-flop, which a streak reset by intervening
        approvals would miss.\""""
        c = CounterState(3)
        for round_ in range(1, 4):
            c.record_reject("domain", [finding("DOM-001")], round_)
            c.record_repair_done("domain:DOM-001")
            c.record_approve("domain", "fp%d" % round_)   # streak resets every round
        c.record_reject("domain", [finding("DOM-001")], 4)
        self.assertEqual(c.reviewer("domain").no_progress_streak, 1)
        self.assertEqual(c.findings["domain:DOM-001"].reject_total, 3)
        self.assertEqual(c.breached(), ("finding", "domain:DOM-001"))

    def test_monotonic_once_counting_starts(self):
        c = CounterState(5)
        c.record_reject("domain", [finding("DOM-001")], 1)
        c.record_repair_done("domain:DOM-001")
        c.record_reject("domain", [finding("DOM-001")], 2)
        c.record_approve("domain", "fp")
        self.assertEqual(c.findings["domain:DOM-001"].reject_total, 1)


class CapBreach(unittest.TestCase):
    def test_reviewer_cap_breaches_at_max_iterations(self):
        c = CounterState(3)
        for i in range(3):
            c.record_reject("domain", [finding("DOM-001")], i)
        self.assertEqual(c.breached(), ("reviewer", "domain"))

    def test_pre_check_refuses_an_over_cap_call(self):
        """"an over-cap call is never made or counted.\""""
        c = CounterState(2)
        c.record_reject("domain", [finding("DOM-001")], 1)
        self.assertFalse(c.would_exceed("domain"))
        c.record_reject("domain", [finding("DOM-001")], 2)
        self.assertTrue(c.would_exceed("domain"))


if __name__ == "__main__":
    unittest.main()
