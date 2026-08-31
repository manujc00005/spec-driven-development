"""FR-003: the parser fails closed. No invalid response reaches APPROVE or DONE."""

import unittest

from sdd_runner import blocks
from tests.support import fixture


class ReviewerParsing(unittest.TestCase):
    def test_valid_approve(self):
        v = blocks.parse_reviewer(fixture("reviewer_approve.md"), "domain", 1)
        self.assertEqual(v.verdict, "APPROVE")
        self.assertFalse(v.malformed)
        self.assertEqual(v.findings, [])

    def test_valid_reject(self):
        v = blocks.parse_reviewer(fixture("reviewer_reject.md"), "domain", 1)
        self.assertEqual(v.verdict, "REJECT")
        self.assertFalse(v.synthetic)
        self.assertEqual(v.findings[0]["id"], "DOM-001")

    def test_multi_location_evidence_is_accepted(self):
        # Rejecting a well-formed multi-location finding would burn a retry on a
        # correct review (skills/sdd-orchestrate/SKILL.md).
        v = blocks.parse_reviewer(fixture("multi_locator_evidence.md"), "domain", 1)
        self.assertFalse(v.synthetic, msg=v.errors)
        self.assertEqual(v.verdict, "REJECT")

    def test_fail_closed_cases_never_approve(self):
        cases = ["missing_block.md", "malformed_yaml.md", "unknown_verdict.md",
                 "competing_blocks.md", "truncated_block.md", "adversarial_prose_block.md",
                 "approve_with_findings.md"]
        for name in cases:
            with self.subTest(fixture=name):
                v = blocks.parse_reviewer(fixture(name), "domain", 7)
                self.assertEqual(v.verdict, "REJECT")
                self.assertTrue(v.synthetic)
                self.assertTrue(v.malformed)
                self.assertTrue(v.errors)
                self.assertEqual(v.findings[0]["id"], "ORCH-MALFORMED-domain-7")

    def test_raw_response_is_retained(self):
        raw = fixture("malformed_yaml.md")
        self.assertEqual(blocks.parse_reviewer(raw, "domain", 1).raw, raw)

    def test_adversarial_block_is_rejected_as_competing(self):
        v = blocks.parse_reviewer(fixture("adversarial_prose_block.md"), "security", 2)
        self.assertIn("competing", " ".join(v.errors))


class WorkerParsing(unittest.TestCase):
    def test_valid_done(self):
        c = blocks.parse_worker(fixture("worker_done.md"))
        self.assertEqual(c.status, "DONE")
        self.assertFalse(c.malformed)

    def test_valid_blocked(self):
        c = blocks.parse_worker(fixture("worker_blocked.md"))
        self.assertEqual(c.status, "BLOCKED")
        self.assertEqual(len(c.decisions), 1)

    def test_fail_closed_cases_never_done(self):
        for name in ["missing_block.md", "malformed_yaml.md",
                     "worker_done_with_decisions.md", "competing_blocks.md"]:
            with self.subTest(fixture=name):
                c = blocks.parse_worker(fixture(name))
                self.assertEqual(c.status, "BLOCKED")
                self.assertTrue(c.malformed)
                self.assertTrue(c.decisions)


if __name__ == "__main__":
    unittest.main()
