"""FR-006: any human-gated trigger wins; an unclassifiable question is human-gated."""

import unittest

from sdd_runner.escalation import classify, classify_all

GATED = {
    "product-ux": "Which flow should the user see after the timeout?",
    "money": "What price do we bill for the overage tier?",
    "personal-data": "How long do we retain the personal data of deleted accounts?",
    "public-contract": "Should we make a breaking change to the public API response?",
    "destructive": "Can I apply the migration to production data?",
    "spec-contradiction": "This contradicts the spec: the SPEC says 3, the task says 5.",
}


class HumanGated(unittest.TestCase):
    def test_each_category_gates(self):
        for expected, question in GATED.items():
            with self.subTest(category=expected):
                c = classify(question)
                self.assertTrue(c.gated)
                self.assertEqual(c.trigger, expected)

    def test_unclassifiable_is_gated(self):
        for question in ("", "   ", None):
            with self.subTest(question=question):
                self.assertTrue(classify(question).gated)

    def test_any_gated_question_gates_the_block(self):
        results = classify_all(["Should backoff be 2x or 3x?", GATED["money"]])
        self.assertTrue(any(r.gated for r in results))
        self.assertFalse(results[0].gated)


class AutoResolvable(unittest.TestCase):
    def test_purely_technical_question(self):
        c = classify("Should the retry backoff be exponential or linear?")
        self.assertTrue(c.auto_resolvable)
        self.assertEqual(c.trigger, "auto-resolvable")

    def test_verbatim_question_is_preserved(self):
        q = "Should the retry backoff be 2x or 3x?"
        self.assertEqual(classify(q).question, q)


if __name__ == "__main__":
    unittest.main()
