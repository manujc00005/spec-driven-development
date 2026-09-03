"""The CLI's observable behaviour did not change — spec 042 AC-008, D007.

Seventeen scenarios were recorded from the **pre-refactor** code before the first
implementation task ran (T001), covering every refusal path, both dry-run forms
and all five terminal states. This replays them.

The only difference this feature is allowed to introduce is FR-009's
`Protocol version` line in `ORCHESTRATION.md` — which none of these transcripts
prints, so in practice every byte must match. That is stated as an explicit
allowance rather than left implicit: an exception nobody wrote down is an
exception nobody can review.

An oracle recorded *after* a refactor proves the refactor agrees with itself. The
ordering is the whole value, which is why T001 came first.
"""

import io
import os
import unittest

from tests.contract import golden

# The one difference FR-009 permits. Nothing else may differ, and this list being
# empty in practice is the point: it is here so a future intentional change has a
# place to be declared instead of being smuggled into a re-record.
PERMITTED_DIFFERENCES = ("- protocol version:",)


class GoldenTranscripts(unittest.TestCase):
    def test_every_recorded_scenario_still_exists_as_a_builder(self):
        recorded = {n[:-4] for n in os.listdir(golden.GOLDEN_DIR) if n.endswith(".txt")}
        self.assertEqual(recorded, set(golden.SCENARIOS),
                         "a scenario was recorded or deleted without updating the other side")

    def test_all_seventeen_scenarios_were_recorded(self):
        self.assertEqual(len(golden.SCENARIOS), 17)

    def test_the_transcripts_replay_byte_for_byte(self):
        for name in sorted(golden.SCENARIOS):
            with self.subTest(scenario=name):
                path = os.path.join(golden.GOLDEN_DIR, name + ".txt")
                with io.open(path, encoding="utf-8") as fh:
                    expected = fh.read()
                actual = golden.capture(name)
                if actual != expected:
                    self._explain(name, expected, actual)

    def _explain(self, name, expected, actual):
        exp = expected.splitlines()
        act = actual.splitlines()
        for i in range(max(len(exp), len(act))):
            a = exp[i] if i < len(exp) else "<missing>"
            b = act[i] if i < len(act) else "<missing>"
            if a != b and not any(p in a or p in b for p in PERMITTED_DIFFERENCES):
                self.fail("scenario %r changed at line %d\n  recorded: %r\n  now:      %r\n"
                          "Re-record only when the change is intended AND declared."
                          % (name, i + 1, a, b))


class TheOracleIsNotVacuous(unittest.TestCase):
    """A comparison against nothing passes for the wrong reason."""

    def test_every_transcript_records_an_exit_code_and_both_streams(self):
        for name in sorted(golden.SCENARIOS):
            path = os.path.join(golden.GOLDEN_DIR, name + ".txt")
            with io.open(path, encoding="utf-8") as fh:
                text = fh.read()
            with self.subTest(scenario=name):
                self.assertTrue(text.startswith("exit: "))
                self.assertIn("--- stdout ---", text)
                self.assertIn("--- stderr ---", text)

    def test_the_scenarios_cover_the_terminal_states_ac008_names(self):
        for required in ("dry-run", "dry-run-adopt", "core-complete", "budget-exhausted",
                         "cap-abort", "human-escalation", "concurrent-run",
                         "unresumable-state", "reentry-after-done", "backend-precondition"):
            with self.subTest(scenario=required):
                self.assertIn(required, golden.SCENARIOS)

    def test_the_refusal_scenarios_cover_distinct_gate_conditions(self):
        refusals = [n for n in golden.SCENARIOS if n.startswith("refusal-")]
        self.assertGreaterEqual(len(refusals), 5)

    def test_a_changed_transcript_would_actually_fail(self):
        """The comparison is real: a mutated expectation is caught."""
        name = "dry-run"
        path = os.path.join(golden.GOLDEN_DIR, name + ".txt")
        with io.open(path, encoding="utf-8") as fh:
            expected = fh.read()
        mutated = expected.replace("max-delegations: 25", "max-delegations: 26")
        self.assertNotEqual(mutated, expected, "the mutation anchor is gone")
        with self.assertRaises(AssertionError):
            self._compare(name, mutated)

    def _compare(self, name, expected):
        actual = golden.capture(name)
        exp, act = expected.splitlines(), actual.splitlines()
        for i in range(max(len(exp), len(act))):
            a = exp[i] if i < len(exp) else "<missing>"
            b = act[i] if i < len(act) else "<missing>"
            if a != b and not any(p in a or p in b for p in PERMITTED_DIFFERENCES):
                raise AssertionError("%s line %d: %r != %r" % (name, i + 1, a, b))


if __name__ == "__main__":
    unittest.main()
