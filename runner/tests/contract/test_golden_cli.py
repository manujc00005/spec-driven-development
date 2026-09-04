"""The CLI's observable behaviour changed only in the ways FR-009 enumerates — AC-008, D007.

Seventeen scenarios were recorded from the **pre-refactor** code before the first
implementation task ran (T001), covering both dry-run forms, all five terminal
states, and **five of the gate's fifteen terminal conditions**, carried by four
`refusal-*` scenarios — `refusal-adopt-not-needed` reaches two. This replays them,
and the other thirteen scenarios added since.

~~"covering every refusal path"~~ **Corrected 2026-09-04 (`conformance:CONF-007`).**
That was the claim, and the corpus never met it: the remaining ten conditions had
no transcript until CONF-003 added one each. The criterion was not narrowed —
`test_gate_refusal_coverage` derives the conditions from `gate.py`'s AST and fails
if any lacks a scenario. Scenarios and conditions are not the same count, and this
docstring conflated them.

The differences this feature is allowed are enumerated in FR-009 with stable
identifiers, and reproduced by the constants below — **the SPEC's list is the
authority and the only place the count lives**:

  * `DIFF-001` — the additive `Protocol version` line in `ORCHESTRATION.md`, which
    none of these transcripts prints, so it never varies a byte here;
  * `DIFF-002` — the `audit-unavailable` path, where `main`'s raw traceback and
    exit 1 become exit 70 with a stable redacted diagnostic (D015);
  * `DIFF-003` — the `refusal-baseline-unavailable` path, where `main` lets a
    `FileNotFoundError` escape the process and this tree refuses `BASELINE_UNAVAILABLE`
    at exit 10 (D018).

Each is stated rather than left implicit: an exception nobody wrote down is an
exception nobody can review. This docstring has now been wrong twice about how many
there are — it said one while two shipped (`maintainer:MNT-009`, re-reported as
`security:SEC-015` / `domain:DOM-028`), then two while three shipped
(`conformance:CONF-006`). Both times the tree was ahead of the record.

An oracle recorded *after* a refactor proves the refactor agrees with itself. The
ordering is the whole value, which is why T001 came first — and why the thirteen
later scenarios have `main` sides recorded beside them instead
(`test_main_baselines`, D007's provenance note).
"""

import io
import os
import unittest

from tests.contract import golden
from tests.support import REPO_ROOT


def _read(path):
    with io.open(path, encoding="utf-8") as fh:
        return fh.read()


def _body(text):
    """A `main`-side artifact without its `#` provenance header."""
    lines = text.splitlines(True)
    i = 0
    while i < len(lines) and lines[i].startswith("#"):
        i += 1
    while i < len(lines) and not lines[i].strip():
        i += 1
    return "".join(lines[i:])

# Line-level differences permitted inside a transcript. Exactly one, and it stays
# one: FR-009's `Protocol version` header.
#
# A second line-level difference was briefly added and reverted — repairing
# domain:DOM-013 made a dry run refuse a backend-exclusive option, turning an
# exit 0 into an exit 14, and D011 was written to bless it. The maintainer refused
# that one; the follow-up is DEBT-011 and D011 is Superseded.
#
# The feature's other authorised differences are not lines inside a transcript but
# whole scenarios — see `AUTHORISED_SCENARIO_DIFFERENCES` below. An earlier version
# of this comment said the feature's promise was "no observable change" full stop,
# which stopped being true when D015 was recorded (`maintainer:MNT-009`); a later
# one said "two in total", which stopped being true when D018 recorded the third.
# Neither number is stated here any more: FR-009's list is the authority.
PERMITTED_DIFFERENCES = ("- protocol version:",)

# The authorised differences that are whole scenarios rather than a line that may
# vary inside one. Each maps to a one-line summary of what `main` did, and each has
# its `main` side on disk as `<scenario>.main.txt`.
#
# Both are **retrospective** baselines: reproduced from a temporary extraction of
# `main`, not captured at T001 with the other seventeen. `audit-unavailable` was
# reproduced after round 4 (D015, `maintainer:MNT-010`); `refusal-baseline-unavailable`
# at CONF-006, together with the nine gate conditions that turned out to reproduce
# `main` byte-for-byte (D018). `test_main_baselines` is the guard over that set.
AUTHORISED_SCENARIO_DIFFERENCES = {
    "audit-unavailable": "main: exit 1, empty stdout, IsADirectoryError traceback",
    "refusal-baseline-unavailable": "main: exit 1, empty stdout, FileNotFoundError traceback",
}

# Which enumerated difference each side of the contract implements, and — for the
# scenario-shaped ones — which scenario pins it. The SPEC's FR-009 carries the list;
# this maps its identifiers onto what this module pins. `DIFF-001` names no scenario
# because it is a line that may vary inside any of them.
DIFFERENCE_IDS = {
    "DIFF-001": ("PERMITTED_DIFFERENCES", None),
    "DIFF-002": ("AUTHORISED_SCENARIO_DIFFERENCES", "audit-unavailable"),
    "DIFF-003": ("AUTHORISED_SCENARIO_DIFFERENCES", "refusal-baseline-unavailable"),
}


class GoldenTranscripts(unittest.TestCase):
    # Transcripts of `main`'s side of an authorised difference. They are not
    # scenarios — nothing replays them, because the code that produced them is not
    # in this tree — so they are named `<scenario>.main.txt` and excluded here by
    # that suffix rather than by accident (`maintainer:MNT-010`).
    RETROSPECTIVE_SUFFIX = ".main.txt"

    def test_every_recorded_scenario_still_exists_as_a_builder(self):
        recorded = {n[:-4] for n in os.listdir(golden.GOLDEN_DIR)
                    if n.endswith(".txt") and not n.endswith(self.RETROSPECTIVE_SUFFIX)}
        self.assertEqual(recorded, set(golden.SCENARIOS),
                         "a scenario was recorded or deleted without updating the other side")

    def test_every_retrospective_artifact_belongs_to_a_scenario(self):
        """A `main` side must belong to a scenario, and be identical or authorised.

        This required every `main` transcript to name an authorised *difference*,
        which was true while `audit-unavailable` was the only one. CONF-006 recorded
        ten more, nine of which reproduce `main` byte-for-byte — evidence that
        nothing changed, which is the opposite of a difference and was rejected by
        the old shape of this check. What must never exist is a `main` side that
        *differs* and is authorised by nothing; that is asserted here and again, in
        full, by `test_main_baselines`.
        """
        for name in os.listdir(golden.GOLDEN_DIR):
            if not name.endswith(self.RETROSPECTIVE_SUFFIX):
                continue
            with self.subTest(artifact=name):
                scenario = name[: -len(self.RETROSPECTIVE_SUFFIX)]
                self.assertIn(scenario, golden.SCENARIOS)
                before = _body(_read(os.path.join(golden.GOLDEN_DIR, name)))
                after = _read(os.path.join(golden.GOLDEN_DIR, scenario + ".txt"))
                if before != after:
                    self.assertIn(scenario, AUTHORISED_SCENARIO_DIFFERENCES,
                                  "a `main` transcript differs and no entry in FR-009 "
                                  "authorises it")

    def test_every_scenario_the_criteria_name_is_recorded(self):
        """AC-008's named minimum corpus, checked by name — never by total.

        This asserted a raw count (`== 20`) and went red the moment CONF-003 added
        the ten missing gate-refusal scenarios. A total is a volatile figure: it
        changes whenever coverage grows, which is the one direction nobody should
        have to repair a test to allow. What the criterion actually names is a
        **set of paths**, so that is what is asserted; the totals are derived by
        `test_the_recorded_corpus_and_the_builders_agree` and by
        `test_gate_refusal_coverage`, which compares against `gate.py`'s AST.

        `internal-error` reaches the catch-all (security:SEC-004, domain:DOM-006 —
        the whole `Diagnostic("INTERNAL", ...)` path was unobserved output).
        `dry-run-contradiction` records the BASELINE: a dry run resolves no backend
        and so validates no backend-exclusive option; it was briefly re-recorded at
        exit 14 and reverted, and is kept because it catches that widening coming
        back. `audit-unavailable` is `DIFF-002`; its `main` side is recorded beside
        it, as are the `main` sides of the ten gate conditions CONF-003 added — it
        was the only one until CONF-006 captured those (D018, `test_main_baselines`).
        """
        recorded = {n[:-4] for n in os.listdir(golden.GOLDEN_DIR)
                    if n.endswith(".txt") and not n.endswith(self.RETROSPECTIVE_SUFFIX)}
        self.assertEqual(recorded, set(golden.SCENARIOS))
        self.assertGreaterEqual(len(golden.SCENARIOS), 20,
                                "the corpus shrank below what earlier rounds recorded")

    def test_the_second_authorised_difference_records_both_sides(self):
        """`maintainer:MNT-010` — a difference needs both sides on the record.

        The `audit-unavailable` transcript pins the NEW behaviour. On its own it
        says nothing about what `main` did, so the claim that a difference was
        authorised could not be checked against anything but a prose string. The
        `main` side is recorded beside it, normalized the same way and labelled a
        retrospective reproduction.
        """
        old = os.path.join(golden.GOLDEN_DIR, "audit-unavailable.main.txt")
        new = os.path.join(golden.GOLDEN_DIR, "audit-unavailable.txt")
        self.assertTrue(os.path.exists(old), "main's side of the difference is unrecorded")
        with io.open(old, encoding="utf-8") as fh:
            before = fh.read()
        with io.open(new, encoding="utf-8") as fh:
            after = fh.read()

        with self.subTest("it is labelled retrospective, not captured at T001"):
            self.assertIn("RETROSPECTIVE", before)
        with self.subTest("main: exit 1 and a traceback"):
            self.assertIn("exit: 1", before)
            self.assertIn("Traceback", before)
        with self.subTest("now: exit 70 and a stable diagnostic, no traceback"):
            self.assertIn("exit: 70", after)
            self.assertIn("audit transcript unavailable", after)
            self.assertNotIn("Traceback", after)
        with self.subTest("neither side reports a terminal result"):
            for side, text in (("main", before), ("now", after)):
                self.assertNotIn("run result:", text.split("--- stdout ---")[1]
                                 .split("--- stderr ---")[0])

    def test_the_scenario_differences_are_declared_and_bounded(self):
        """Every authorised difference is named, and each names a real scenario.

        The set is compared against `DIFFERENCE_IDS`, which is compared in turn
        against FR-009's block by `TheSpecAndTheseConstantsAgree` — so this cannot
        drift without the SPEC drifting with it. It used to assert the literal
        `["audit-unavailable"]`, which is how it went red when D018 was recorded
        rather than reporting anything useful.
        """
        self.assertEqual(len(PERMITTED_DIFFERENCES), 1)
        named = {scenario for _, scenario in DIFFERENCE_IDS.values() if scenario}
        self.assertEqual(sorted(AUTHORISED_SCENARIO_DIFFERENCES), sorted(named),
                         "a scenario difference is pinned here or listed there, not both")
        for name in sorted(AUTHORISED_SCENARIO_DIFFERENCES):
            with self.subTest(scenario=name):
                self.assertIn(name, golden.SCENARIOS)
                self.assertTrue(
                    os.path.exists(os.path.join(golden.GOLDEN_DIR,
                                                name + self.RETROSPECTIVE_SUFFIX)),
                    "an authorised difference with no `main` side on the record")

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


class TheSpecAndTheseConstantsAgree(unittest.TestCase):
    """FR-009's list is the record; this module is one reader of it.

    Read **structurally, by identifier**, from the fenced block FR-009 carries —
    never by searching the SPEC's prose. This feature has produced five false
    positives from substring searches, and a guard over free text would be the
    sixth: the SPEC quotes its own superseded wording on purpose, so any search
    for "only difference" finds the sentence that was corrected.
    """

    @staticmethod
    def _declared():
        from sdd_runner import _miniyaml
        path = os.path.join(REPO_ROOT, "specs", "features",
                            "042-canonical-autonomous-core", "SPEC.md")
        with io.open(path, encoding="utf-8") as fh:
            text = fh.read()
        marker = "authorised-observable-differences:"
        start = text.index(marker)
        end = text.index("```", start)
        block = _miniyaml.parse(text[start:end])
        return {entry["id"]: entry for entry in block[marker.rstrip(":")]}

    def test_the_spec_declares_exactly_the_differences_this_module_pins(self):
        declared = self._declared()
        self.assertEqual(sorted(declared), sorted(DIFFERENCE_IDS),
                         "FR-009's list and this module's constants disagree")

    def test_each_declared_difference_names_the_decision_that_authorised_it(self):
        for identifier, entry in sorted(self._declared().items()):
            with self.subTest(difference=identifier):
                self.assertRegex(str(entry.get("decision", "")), r"^D\d{3}$",
                                 "an authorised difference names no decision")
                self.assertTrue(entry.get("surface"))
                self.assertTrue(entry.get("change"))

    def test_the_counts_on_both_sides_line_up(self):
        self.assertEqual(len(PERMITTED_DIFFERENCES), 1)
        self.assertEqual(len(AUTHORISED_SCENARIO_DIFFERENCES), 2)
        self.assertEqual(sorted(self._declared()),
                         ["DIFF-001", "DIFF-002", "DIFF-003"],
                         "a difference was added to or dropped from FR-009 without "
                         "updating the constants that pin it")


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
                         "unresumable-state", "reentry-after-done", "backend-precondition",
                         "internal-error", "dry-run-contradiction", "audit-unavailable"):
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
