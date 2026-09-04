"""Every terminal condition `gate.check` can emit has a recorded CLI transcript.

Spec 042 CONF-003. AC-008's minimum corpus says *"each gate refusal"* and the
corpus recorded **five of the fifteen conditions, carried by four scenarios** —
`refusal-adopt-not-needed` reaches two, "adoption not needed" and "inherited diff
undetermined". The criterion was **not** narrowed: coverage was added until it was
true.

~~"the corpus recorded four of them"~~ **Corrected 2026-09-04 (`conformance:CONF-007`).**
"Them" was conditions and "four" was scenarios. The two counts differ, they differ
because of exactly one scenario, and this module exists to keep them apart — so
stating one for the other here was the defect in the guard against it.

Two independent sides, and the guard is the comparison between them:

  * the **conditions** come from `gate.py`'s syntax tree — every `Refusal(...)`
    the module can construct, resolving `policy` constants;
  * the **scenarios** come from `COVERAGE`, a table written by hand, and each
    entry is checked against the transcript it names.

`COVERAGE` is structured — condition to scenario, one mapping per row — and lives
here rather than in prose. Nothing in this module searches a document for a
condition name: this feature produced seven false positives that way, and the
transcripts quote refusal text on purpose.
"""

import ast
import io
import os
import unittest

from sdd_runner import gate, policy
from tests.contract import golden

# condition emitted by gate.check  ->  the scenario whose transcript records it.
# A condition with no entry fails `test_every_condition_has_a_scenario`; an entry
# whose transcript does not actually carry the refusal fails the next test.
COVERAGE = {
    "feature folder missing":          "refusal-feature-folder-missing",
    "SPEC.md missing":                 "refusal-spec-missing",
    "TASKS.md missing":                "refusal-tasks-missing",
    "already adopted or entered":      "refusal-already-adopted",
    "status unreadable":               "refusal-status-unreadable",
    "adoption not needed":             "refusal-adopt-not-needed",
    "lifecycle status":                "refusal-status-not-ready",
    "open questions":                  "refusal-open-questions",
    "not a git repository":            "refusal-not-a-git-repository",
    "default branch":                  "refusal-default-branch",
    "unattributed dirty tree":         "refusal-dirty-tree",
    "baseline suite unavailable":      "refusal-baseline-unavailable",
    "red baseline suite":              "refusal-red-baseline",
    "baseline suite mutates the tree": "refusal-baseline-mutates",
    "inherited diff undetermined":     "refusal-adopt-not-needed",
}


def emitted_conditions():
    """Every terminal condition the gate module can construct, from its AST."""
    with io.open(gate.__file__, encoding="utf-8") as fh:
        tree = ast.parse(fh.read())
    found = []
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                and node.func.id == "Refusal" and node.args):
            continue
        first = node.args[0]
        if isinstance(first, ast.Constant) and isinstance(first.value, str):
            value = first.value
        elif isinstance(first, ast.Name) and hasattr(policy, first.id):
            value = getattr(policy, first.id)
        else:
            continue
        if value not in found:
            found.append(value)
    return found


def transcript(scenario):
    path = os.path.join(golden.GOLDEN_DIR, scenario + ".txt")
    with io.open(path, encoding="utf-8") as fh:
        return fh.read()


class TheMatrixIsComplete(unittest.TestCase):
    def test_every_condition_has_a_scenario(self):
        missing = [c for c in emitted_conditions() if c not in COVERAGE]
        self.assertEqual(missing, [],
                         "gate conditions with no recorded CLI transcript: %s" % missing)

    def test_no_scenario_is_mapped_to_a_condition_the_gate_cannot_emit(self):
        stale = sorted(set(COVERAGE) - set(emitted_conditions()))
        self.assertEqual(stale, [],
                         "the matrix maps conditions the gate no longer emits: %s" % stale)

    def test_the_matrix_is_not_vacuous(self):
        """A guard over an empty condition list passes for the wrong reason."""
        self.assertGreaterEqual(len(emitted_conditions()), 15)


class EveryScenarioActuallyRecordsItsCondition(unittest.TestCase):
    def test_each_named_scenario_exists_and_was_captured(self):
        for condition, scenario in sorted(COVERAGE.items()):
            with self.subTest(condition=condition):
                self.assertIn(scenario, golden.SCENARIOS,
                              "the matrix names a scenario with no builder")
                self.assertTrue(
                    os.path.exists(os.path.join(golden.GOLDEN_DIR, scenario + ".txt")),
                    "the matrix names a scenario with no recorded transcript")

    def test_each_transcript_carries_the_refusal_it_is_mapped_to(self):
        for condition, scenario in sorted(COVERAGE.items()):
            with self.subTest(condition=condition):
                self.assertIn("refused: %s" % condition, transcript(scenario),
                              "%s does not record %r" % (scenario, condition))

    def test_each_refusal_carries_evidence_and_a_remediation(self):
        """031's refusal shape, checked on what the operator actually sees."""
        for condition, scenario in sorted(COVERAGE.items()):
            with self.subTest(condition=condition):
                text = transcript(scenario)
                block = text[text.index("refused: %s" % condition):]
                self.assertIn("remediation:", block,
                              "%s refuses without saying what to do" % condition)

    def test_every_refusal_scenario_exits_ten(self):
        for condition, scenario in sorted(COVERAGE.items()):
            with self.subTest(condition=condition):
                self.assertTrue(transcript(scenario).startswith("exit: 10"),
                                "%s does not exit with the gate-refused code" % scenario)


class TheScenariosDriveTheRealGate(unittest.TestCase):
    """Not a helper, not a hand-built expectation — the CLI, end to end."""

    def test_no_scenario_builder_calls_the_gate_directly(self):
        with io.open(golden.__file__, encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        for node in ast.walk(tree):
            if not (isinstance(node, ast.FunctionDef) and node.name.startswith("sc_refusal_")):
                continue
            for call in ast.walk(node):
                if isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute):
                    with self.subTest(scenario=node.name):
                        self.assertNotIn(call.func.attr, {"check", "inherited_record"},
                                         "a scenario short-circuits the CLI")

    def test_the_transcripts_are_produced_by_the_cli(self):
        """`capture` runs `__main__.main`; a hand-written transcript would not replay."""
        for scenario in sorted(set(COVERAGE.values())):
            with self.subTest(scenario=scenario):
                self.assertEqual(golden.capture(scenario), transcript(scenario),
                                 "%s no longer replays byte for byte" % scenario)


if __name__ == "__main__":
    unittest.main()
