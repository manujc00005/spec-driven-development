"""The strict YAML subset — spec 040 D010.

This module's entire job is rejecting things, and it had no tests of its own:
it was exercised only through `blocks`, which sees the accepted shapes. What
matters here is the other side — that "unrecognized" and "rejected" really are
the same thing, because that equality is what makes the fail-closed parser
fail-closed rather than merely strict-looking.
"""

import unittest

from sdd_runner._miniyaml import MiniYamlError, parse


class AcceptedGrammar(unittest.TestCase):
    def test_scalar_mapping(self):
        self.assertEqual(parse("verdict: APPROVE"), {"verdict": "APPROVE"})

    def test_inline_comment_is_stripped(self):
        """The canonical block in SKILL.md carries one, so this is required."""
        self.assertEqual(parse("verdict: APPROVE # APPROVE | REJECT"), {"verdict": "APPROVE"})

    def test_empty_list_literal(self):
        self.assertEqual(parse("findings: []"), {"findings": []})

    def test_block_sequence_of_mappings(self):
        doc = parse("findings:\n  - id: SEC-001\n    severity: High")
        self.assertEqual(doc, {"findings": [{"id": "SEC-001", "severity": "High"}]})

    def test_block_sequence_of_scalars(self):
        self.assertEqual(parse("decisions:\n  - a question"),
                         {"decisions": ["a question"]})

    def test_quoted_scalar_keeps_its_hash(self):
        self.assertEqual(parse('summary: "a # b"'), {"summary": "a # b"})


class RejectedOutright(unittest.TestCase):
    """Every one of these is a YAML feature a full parser would accept."""

    CASES = {
        "anchor": "verdict: &a APPROVE",
        "alias": "verdict: *a",
        "tag": "verdict: !!str APPROVE",
        "flow mapping": "verdict: {a: b}",
        "literal block scalar": "summary: |\n  text",
        "folded block scalar": "summary: >\n  text",
        "document start": "---\nverdict: APPROVE",
        "document end": "verdict: APPROVE\n...",
        "tab indentation": "findings:\n\t- id: X",
        "duplicate key": "verdict: APPROVE\nverdict: REJECT",
        "duplicate key in an item": "findings:\n  - id: A\n    id: B",
        "top-level indentation": "  verdict: APPROVE",
        "not a mapping": "just a line",
        "empty document": "",
        "comment only": "# nothing here",
        "nested structure in an item": "findings:\n  - id: A\n    nested:\n      - x",
        "unterminated quote": 'summary: "open',
        "inconsistent sequence indent": "findings:\n  - id: A\n   - id: B",
        "empty block sequence": "findings:\n",
    }

    def test_each_case_raises_rather_than_guessing(self):
        for label, text in self.CASES.items():
            with self.subTest(case=label):
                with self.assertRaises(MiniYamlError):
                    parse(text)

    def test_the_error_is_the_only_failure_mode(self):
        """No case may raise something a caller would not catch as MiniYamlError."""
        for label, text in self.CASES.items():
            with self.subTest(case=label):
                try:
                    parse(text)
                except MiniYamlError:
                    pass
                except Exception as exc:            # noqa: BLE001 - that is the assertion
                    self.fail("%s raised %s, not MiniYamlError" % (label, type(exc).__name__))
                else:
                    self.fail("%s was accepted" % label)


if __name__ == "__main__":
    unittest.main()
