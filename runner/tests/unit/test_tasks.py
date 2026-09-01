"""031 FR-007 / spec 033: the task item is the detection unit."""

import unittest

from sdd_runner import tasks

TEXT = """# Tasks: x

## Phase 1: Preparation

- [x] T001 - Already done. Covers: AC-001. Verify: the suite passes.
- [ ] T002 - Pending work with a
  continuation line. Covers: AC-002, AC-003. Verify: run the command and see 0.
- [~] T003 - **[DEFERRED]** Not performed. Covers: AC-004. Verify: n/a.
"""


class Parsing(unittest.TestCase):
    def test_checked_deferred_and_pending_are_distinguished(self):
        parsed = {t.id: t for t in tasks.parse(TEXT)}
        self.assertTrue(parsed["T001"].checked)
        self.assertTrue(parsed["T003"].deferred)
        self.assertTrue(parsed["T002"].runnable)
        self.assertFalse(parsed["T001"].runnable)
        self.assertFalse(parsed["T003"].runnable)

    def test_continuation_lines_belong_to_the_task_item(self):
        t = {x.id: x for x in tasks.parse(TEXT)}["T002"]
        self.assertEqual(t.covers, ["AC-002", "AC-003"])
        self.assertEqual(t.verify, "run the command and see 0.")

    def test_unchecked_returns_only_runnable_tasks(self):
        self.assertEqual([t.id for t in tasks.unchecked(TEXT)], ["T002"])

    def test_next_id_continues_the_sequence(self):
        self.assertEqual(tasks.next_task_id(TEXT), "T004")

    def test_a_repair_task_is_recognized_by_its_finding_suffix(self):
        text = tasks.append_finding_task(TEXT, "T004", "Repair DOM-001 for T002", "DOM-001",
                                         ["AC-002"], "Persist first")
        by_id = {t.id: t for t in tasks.parse(text)}
        self.assertEqual(by_id["T004"].repairs, "DOM-001")
        self.assertEqual(by_id["T002"].repairs, "")

    def test_a_synthetic_finding_id_is_still_recognized(self):
        """ORCH-MALFORMED-domain-1 is a finding id too; a narrow pattern would miss it."""
        text = tasks.append_finding_task(TEXT, "T004", "Repair", "ORCH-MALFORMED-domain-1",
                                         ["AC-002"], "Return a conforming block")
        self.assertEqual({t.id: t for t in tasks.parse(text)}["T004"].repairs,
                         "ORCH-MALFORMED-domain-1")

    def test_repair_tasks_are_excluded_from_independently_runnable_work(self):
        text = tasks.append_finding_task(TEXT, "T004", "Repair DOM-001", "DOM-001",
                                         ["AC-002"], "Persist first")
        self.assertEqual([t.id for t in tasks.unchecked(text)], ["T002", "T004"])
        self.assertEqual([t.id for t in tasks.independently_runnable(text)], ["T002"],
                         "a repair is scheduled by its finding, never picked up twice")

    def test_task_for_finding_finds_the_existing_repair_task(self):
        text = tasks.append_finding_task(TEXT, "T004", "Repair DOM-001", "DOM-001",
                                         ["AC-002"], "Persist first")
        self.assertEqual(tasks.task_for_finding(text, "DOM-001").id, "T004")
        self.assertIsNone(tasks.task_for_finding(text, "DOM-999"))

    def test_check_task_marks_only_its_own_task(self):
        text = tasks.check_task(TEXT, "T002")
        by_id = {t.id: t for t in tasks.parse(text)}
        self.assertTrue(by_id["T002"].checked)
        self.assertFalse(by_id["T003"].checked)
        self.assertTrue(by_id["T003"].deferred, "a deferred task is left alone")

    def test_check_task_is_idempotent(self):
        once = tasks.check_task(TEXT, "T002")
        self.assertEqual(tasks.check_task(once, "T002"), once)

    def test_finding_task_carries_traceability_to_its_finding(self):
        out = tasks.append_finding_task(TEXT, "T004", "Fix the thing", "DOM-001",
                                        ["AC-002"], "Persist before proceeding")
        self.assertIn("- [ ] T004 - Fix the thing (from DOM-001). Covers: AC-002.", out)
        self.assertIn("Verify:", out)


if __name__ == "__main__":
    unittest.main()
