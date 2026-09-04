"""Every gate-refusal condition has a real `main` side — spec 042 CONF-006, D018.

CONF-003 added ten CLI scenarios so AC-008's *"each gate refusal"* became true
rather than narrower. They were captured after the refactor, so they proved the
refactor agreed with itself and nothing more: there was no "before" to compare
them against. CONF-006 captured one, from a temporary extraction of `main`, and
the comparison turned up a difference nobody had authorised — `main` lets a
`FileNotFoundError` from the baseline launcher escape the process, and this tree
answers it with a `BASELINE_UNAVAILABLE` refusal. That is now `DIFF-003` (D018).

Nine of the ten reproduce `main` byte-for-byte. This module is the guard on that
claim, and it is written to fail on each of the six ways it could stop being true:

  * a missing side, either one;
  * a provenance commit that changed without a regeneration updating everything
    that records it — the artifact headers, the index, and the digests;
  * one of the nine ceasing to be identical;
  * the tenth differing in any way other than the one D018 authorised;
  * a fourth authorised difference appearing;
  * `DIFF-003` disappearing from FR-009's block or from D018.

Everything is read structurally: the difference list from FR-009's fenced block by
identifier, the decision from its own `###` section, the transcripts by digest.
Never by searching prose — this feature has produced five false positives that way,
and the records quote their own superseded wording on purpose.
"""

import io
import json
import os
import unittest

from tests.contract import golden
from tests.support import REPO_ROOT

FEATURE = os.path.join(REPO_ROOT, "specs", "features", "042-canonical-autonomous-core")
EVIDENCE = os.path.join(FEATURE, "evidence")
INDEX = os.path.join(golden.GOLDEN_DIR, "index.json")
SUFFIX = ".main.txt"

# The identifiers FR-009 must carry, and what each one's `main` side looks like.
# `DIFF-001` is a line inside a transcript, not a scenario, so it has no pair here.
AUTHORISED = {
    "DIFF-002": ("audit-unavailable", "D015"),
    "DIFF-003": ("refusal-baseline-unavailable", "D018"),
}


def _load(path):
    with io.open(path, encoding="utf-8") as fh:
        return fh.read()


def _body(text):
    """The transcript inside a `main`-side artifact, without its `#` header."""
    lines = text.splitlines(True)
    i = 0
    while i < len(lines) and lines[i].startswith("#"):
        i += 1
    while i < len(lines) and not lines[i].strip():
        i += 1
    return "".join(lines[i:])


def _header_fields(text):
    """The `# key: value` provenance header, as a dict. Continuations are ignored."""
    fields = {}
    for line in text.splitlines():
        if not line.startswith("#"):
            break
        stripped = line[1:].strip()
        if ":" in stripped and not stripped.startswith(" "):
            key, _, value = stripped.partition(":")
            if " " not in key.strip():
                fields.setdefault(key.strip(), value.strip())
    return fields


def _sha256(text):
    import hashlib
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _spec_differences():
    """FR-009's fenced block, by identifier. The SPEC's list is the authority."""
    from sdd_runner import _miniyaml
    text = _load(os.path.join(FEATURE, "SPEC.md"))
    marker = "authorised-observable-differences:"
    start = text.index(marker)
    block = _miniyaml.parse(text[start:text.index("```", start)])
    return {entry["id"]: entry for entry in block[marker.rstrip(":")]}


def _decision_section(identifier):
    """One decision's own text, sliced between `###` headings — never a file-wide search."""
    text = _load(os.path.join(FEATURE, "DECISIONS.md"))
    head = "\n### %s - " % identifier
    if head not in text:
        return None
    start = text.index(head)
    nxt = text.find("\n### D", start + len(head))
    return text[start:nxt if nxt != -1 else len(text)]


class TheIndexIsTheProvenanceRecord(unittest.TestCase):
    """`index.json` says where the baselines came from; the artifacts must agree."""

    def setUp(self):
        self.document = json.loads(_load(INDEX))
        self.entries = {e["scenario"]: e for e in self.document["scenarios"]}

    def test_it_declares_the_capture_as_retrospective(self):
        self.assertTrue(self.document["retrospective"],
                        "a baseline reproduced after the fact is not a T001 oracle")
        self.assertEqual(self.document["finding"], "conformance:CONF-006")
        self.assertEqual(self.document["decision"], "D018")
        script = os.path.join(REPO_ROOT, self.document["captured_by"])
        self.assertTrue(os.path.exists(script),
                        "the index names a capture script that does not exist")

    def test_every_entry_records_what_a_baseline_needs_to_be_reproducible(self):
        for name, entry in sorted(self.entries.items()):
            with self.subTest(scenario=name):
                for field in ("condition", "command", "fixture", "main_commit",
                              "main_exit", "current_exit", "normalization", "relation",
                              "main_sha256", "current_sha256"):
                    self.assertTrue(str(entry.get(field, "")).strip(),
                                    "%s records no %s" % (name, field))

    def test_the_commit_cannot_change_without_regenerating_the_artifacts(self):
        """Two independent records of the provenance commit, compared.

        A partial regeneration — the index bumped, the artifacts left behind, or the
        reverse — is exactly how a baseline starts describing a `main` it was never
        captured from. Neither side can move alone.
        """
        declared = self.document["main_commit"]
        self.assertRegex(declared, r"^[0-9a-f]{40}$")
        for name, entry in sorted(self.entries.items()):
            with self.subTest(scenario=name):
                self.assertEqual(entry["main_commit"], declared,
                                 "the index disagrees with itself about the commit")
                header = _header_fields(_load(os.path.join(golden.GOLDEN_DIR, name + SUFFIX)))
                self.assertEqual(header.get("main-commit"), declared,
                                 "%s was captured from a different commit than the index "
                                 "declares: regenerate both" % name)
                self.assertEqual(header.get("scenario"), name)
                self.assertEqual(header.get("condition"), entry["condition"])

    def test_the_recorded_digests_match_what_is_on_disk(self):
        """An edited transcript with a stale digest is a rewritten baseline."""
        for name, entry in sorted(self.entries.items()):
            with self.subTest(scenario=name):
                main = _body(_load(os.path.join(golden.GOLDEN_DIR, name + SUFFIX)))
                now = _load(os.path.join(golden.GOLDEN_DIR, name + ".txt"))
                self.assertEqual(_sha256(main), entry["main_sha256"],
                                 "%s's `main` side was edited without regenerating" % name)
                self.assertEqual(_sha256(now), entry["current_sha256"],
                                 "%s's current side moved without regenerating" % name)


class BothSidesExistForEveryCondition(unittest.TestCase):
    """A difference with one side recorded cannot be checked against anything."""

    def setUp(self):
        self.entries = {e["scenario"]: e
                        for e in json.loads(_load(INDEX))["scenarios"]}

    def test_the_ten_gate_conditions_all_have_both_sides(self):
        from tests.contract import test_gate_refusal_coverage as coverage
        conditions = {e["condition"] for e in self.entries.values()}
        self.assertEqual(len(self.entries), 10, "the baseline set is not the ten CONF-003 added")
        self.assertEqual(len(conditions), 10, "two entries claim the same gate condition")
        emitted = set(coverage.emitted_conditions())
        self.assertTrue(conditions <= emitted,
                        "a baseline names a condition `gate.check` cannot emit: %s"
                        % sorted(conditions - emitted))
        for name in sorted(self.entries):
            with self.subTest(scenario=name):
                self.assertIn(name, golden.SCENARIOS)
                for side in (name + SUFFIX, name + ".txt"):
                    self.assertTrue(os.path.exists(os.path.join(golden.GOLDEN_DIR, side)),
                                    "%s is missing" % side)

    def test_the_baselines_cover_the_conditions_main_could_emit_and_no_others(self):
        """`baseline suite unavailable` is new; the other nine exist on both sides.

        Asserted against the count, because that asymmetry is the reason D018 exists:
        `main` emits fourteen terminal conditions and this tree emits fifteen.
        """
        from tests.contract import test_gate_refusal_coverage as coverage
        self.assertEqual(len(coverage.emitted_conditions()), 15)
        divergent = [e["condition"] for e in self.entries.values()
                     if e["relation"] != "identical"]
        self.assertEqual(divergent, ["baseline suite unavailable"])


class NineConditionsAreByteIdentical(unittest.TestCase):
    """The claim CONF-006 exists to make checkable."""

    def setUp(self):
        self.entries = {e["scenario"]: e
                        for e in json.loads(_load(INDEX))["scenarios"]}

    def test_every_condition_declared_identical_really_is(self):
        identical = [n for n, e in self.entries.items() if e["relation"] == "identical"]
        self.assertEqual(len(identical), 9,
                         "nine of the ten reproduce `main`; the count moved")
        for name in sorted(identical):
            with self.subTest(scenario=name):
                main = _body(_load(os.path.join(golden.GOLDEN_DIR, name + SUFFIX)))
                now = _load(os.path.join(golden.GOLDEN_DIR, name + ".txt"))
                self.assertEqual(main, now,
                                 "%s no longer reproduces `main` byte-for-byte. This is an "
                                 "unauthorised observable change, not a transcript to "
                                 "re-record." % name)
                self.assertEqual(e_exit(main), e_exit(now))

    def test_each_identical_side_actually_carries_a_refusal(self):
        """A comparison of two empty transcripts passes for the wrong reason."""
        for name, entry in sorted(self.entries.items()):
            if entry["relation"] != "identical":
                continue
            with self.subTest(scenario=name):
                main = _body(_load(os.path.join(golden.GOLDEN_DIR, name + SUFFIX)))
                self.assertEqual(e_exit(main), 10, "a gate refusal exits 10")
                self.assertIn("[GATE] refused: %s" % entry["condition"], main)
                self.assertNotIn("Traceback", main)


class TheTenthDiffersExactlyAsAuthorised(unittest.TestCase):
    """`DIFF-003`: the whole authorised departure, and nothing beside it."""

    NAME = "refusal-baseline-unavailable"

    def setUp(self):
        self.before = _body(_load(os.path.join(golden.GOLDEN_DIR, self.NAME + SUFFIX)))
        self.after = _load(os.path.join(golden.GOLDEN_DIR, self.NAME + ".txt"))

    def test_main_let_the_exception_escape(self):
        self.assertEqual(e_exit(self.before), 1)
        self.assertIn("Traceback (most recent call last):", self.before)
        self.assertIn("FileNotFoundError: [Errno 2] No such file or directory: "
                      "'definitely-not-a-real-binary-042'", self.before)
        self.assertNotIn("[GATE] refused", self.before)

    def test_this_tree_refuses_structurally_instead(self):
        from sdd_runner.policy import BASELINE_UNAVAILABLE, GATE_REFUSED
        self.assertEqual(e_exit(self.after), GATE_REFUSED)
        self.assertIn("[GATE] refused: %s" % BASELINE_UNAVAILABLE, self.after)
        self.assertIn("definitely-not-a-real-binary-042", self.after)
        self.assertIn("remediation:", self.after)

    def test_it_prints_no_traceback_and_reports_no_run(self):
        """D018's two negative clauses, instantiated (D014)."""
        self.assertNotIn("Traceback", self.after)
        self.assertNotIn("run result:", self.after)
        self.assertIn("Traceback", self.before)

    def test_the_difference_is_confined_to_stderr(self):
        """Both sides print nothing on stdout: only the refusal channel moved."""
        for label, text in (("main", self.before), ("now", self.after)):
            with self.subTest(side=label):
                stdout = text.split("--- stdout ---")[1].split("--- stderr ---")[0]
                self.assertEqual(stdout.strip(), "")


class TheAuthorisationIsOnTheRecord(unittest.TestCase):
    """`DIFF-003` must exist in FR-009's list and in a decision, or it is not authorised."""

    def test_fr009_enumerates_exactly_the_authorised_differences(self):
        declared = _spec_differences()
        self.assertEqual(sorted(declared), ["DIFF-001", "DIFF-002", "DIFF-003"],
                         "FR-009's list moved; a difference was added or dropped without "
                         "the guards that read it")

    def test_diff003_is_declared_against_its_decision(self):
        entry = _spec_differences().get("DIFF-003")
        self.assertIsNotNone(entry, "DIFF-003 left FR-009's block")
        self.assertEqual(entry["decision"], "D018")
        self.assertTrue(entry["surface"])
        self.assertTrue(entry["change"])

    def test_every_scenario_difference_names_a_decision_that_accepts_it(self):
        declared = _spec_differences()
        for identifier, (scenario, decision) in sorted(AUTHORISED.items()):
            with self.subTest(difference=identifier):
                self.assertEqual(declared[identifier]["decision"], decision)
                section = _decision_section(decision)
                self.assertIsNotNone(section, "%s is not a decision" % decision)
                self.assertIn("**Status:** Accepted", section,
                              "%s does not accept %s" % (decision, identifier))
                self.assertIn(identifier, section,
                              "%s never mentions the difference it authorises" % decision)
                self.assertIn(scenario, section,
                              "%s names no transcript pinning %s" % (decision, identifier))

    def test_no_retrospective_artifact_exists_for_an_unauthorised_difference(self):
        """A `main` side that differs and is not on the list is a finding, not evidence."""
        authorised = {scenario for scenario, _ in AUTHORISED.values()}
        for name in sorted(os.listdir(golden.GOLDEN_DIR)):
            if not name.endswith(SUFFIX):
                continue
            scenario = name[: -len(SUFFIX)]
            with self.subTest(scenario=scenario):
                self.assertIn(scenario, golden.SCENARIOS)
                main = _body(_load(os.path.join(golden.GOLDEN_DIR, name)))
                now = _load(os.path.join(golden.GOLDEN_DIR, scenario + ".txt"))
                if main != now:
                    self.assertIn(scenario, authorised,
                                  "%s differs from `main` and no entry in FR-009 authorises "
                                  "it" % scenario)


class TheGuardWouldActuallyFail(unittest.TestCase):
    """Each check above is compared against something that can move (D014)."""

    def test_a_baseline_edited_without_regenerating_is_caught(self):
        entry = json.loads(_load(INDEX))["scenarios"][0]
        main = _body(_load(os.path.join(golden.GOLDEN_DIR, entry["scenario"] + SUFFIX)))
        self.assertEqual(_sha256(main), entry["main_sha256"])
        self.assertNotEqual(_sha256(main + "\n"), entry["main_sha256"],
                            "the digest check cannot distinguish an edited transcript")

    def test_a_condition_that_stopped_matching_is_caught(self):
        name = "refusal-spec-missing"
        main = _body(_load(os.path.join(golden.GOLDEN_DIR, name + SUFFIX)))
        now = _load(os.path.join(golden.GOLDEN_DIR, name + ".txt"))
        self.assertEqual(main, now)
        self.assertNotEqual(main.replace("SPEC.md missing", "SPEC.md absent"), now,
                            "the comparison is vacuous")

    def test_a_fourth_difference_would_not_pass_the_list_check(self):
        declared = sorted(_spec_differences())
        self.assertEqual(declared, ["DIFF-001", "DIFF-002", "DIFF-003"])
        self.assertNotEqual(declared + ["DIFF-004"], declared)

    def test_the_decision_slice_reads_one_decision_and_not_the_file(self):
        """A file-wide search would find `DIFF-003` in D007's and D015's notes too."""
        section = _decision_section("D018")
        self.assertIn("DIFF-003", section)
        self.assertNotIn("### D017", section)
        self.assertNotIn("### D019", section)
        self.assertIsNone(_decision_section("D999"))


def e_exit(text):
    return int(text.split("\n", 1)[0].split("exit:")[1].strip())


if __name__ == "__main__":
    unittest.main()
