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

    def test_finding_task_carries_traceability_to_its_finding(self):
        out = tasks.append_finding_task(TEXT, "T004", "Fix the thing", "DOM-001",
                                        ["AC-002"], "Persist before proceeding")
        self.assertIn("- [ ] T004 - Fix the thing (from DOM-001). Covers: AC-002.", out)
        self.assertIn("Verify:", out)


if __name__ == "__main__":
    unittest.main()
