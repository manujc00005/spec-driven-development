"""`protocol_version` compatibility — spec 042 FR-009, FR-010, AC-004, D003.

The field is additive and the compatibility rule is deliberately the one the
repository already uses: **absent means 1**, mirroring spec 041 D007's "a state
file with no `Entry` line is read as `ready`". Anything the core cannot read is
fail-closed, never guessed — 031's standing rule about state files.
"""

import os
import re
import socket
import tempfile
import unittest

from sdd_runner import exits, policy, resume, state  # noqa: F401
from tests.contract import golden
from tests.support import REPO_ROOT

REAL_ARTIFACTS = [
    "specs/features/032-autonomous-loop-residual-calibration/ORCHESTRATION.md",
    "specs/features/033-task-verification-criterion/ORCHESTRATION.md",
]


class TheFieldIsWrittenAndKept(unittest.TestCase):
    def test_a_new_document_records_the_version(self):
        doc = state.new_document("specs/features/900-fixture", "runner", "now",
                                 {"max_iterations": 3, "max_delegations": 25})
        self.assertIn("- protocol version: %d" % policy.PROTOCOL_VERSION, doc.dumps())
        self.assertEqual(doc.protocol_version(), policy.PROTOCOL_VERSION)

    def test_a_real_run_keeps_it_across_every_save(self):
        """`Loop._state_fields` replaces the whole State body; an unrestated field is lost."""
        with tempfile.TemporaryDirectory() as tmp:
            _repo, _argv, state_path = golden._converged_state(tmp)
            with open(state_path, encoding="utf-8") as fh:
                text = fh.read()
        self.assertIn("- protocol version: 1", text)
        self.assertEqual(state.Orchestration.loads(text).protocol_version(), 1)

    def test_this_feature_stamps_one_and_does_not_bump(self):
        """D003: a refactor changes no rule, so it changes no contract version."""
        self.assertEqual(policy.PROTOCOL_VERSION, 1)


class AbsentMeansOne(unittest.TestCase):
    def test_a_document_without_the_field_reads_as_version_one(self):
        doc = state.Orchestration.loads("# x\n\n## State\n\n- writer: sdd_runner\n\n")
        self.assertEqual(doc.protocol_version(), 1)

    def test_the_real_phase_one_artifacts_read_as_version_one(self):
        """They predate the field. They must stay readable (AC-004)."""
        seen = 0
        for rel in REAL_ARTIFACTS:
            path = os.path.join(REPO_ROOT, rel)
            if not os.path.isfile(path):
                continue
            with open(path, encoding="utf-8") as fh:
                text = fh.read()
            with self.subTest(artifact=rel):
                self.assertNotIn("protocol version", text.lower())
                self.assertEqual(state.Orchestration.loads(text).protocol_version(), 1)
                seen += 1
        self.assertTrue(seen, "no real artifact was available to check")


class UnreadableFailsClosed(unittest.TestCase):
    """Never guessed back into shape."""

    @staticmethod
    def _doc(value):
        return state.Orchestration.loads(
            "# x\n\n## State\n\n- writer: sdd_runner\n- protocol version: %s\n\n" % value)

    def test_a_non_integer_raises_rather_than_defaulting(self):
        for value in ("abc", "1.0", "-1", "0", "v1"):
            with self.subTest(value=value):
                with self.assertRaises(state.UnknownProtocolVersion):
                    self._doc(value).protocol_version()

    def test_a_present_but_empty_value_fails_closed(self):
        """Absent and empty are different things — spec 042 SPEC edge cases.

        This test asserted the opposite until domain:DOM-004 pointed out that the
        SPEC lists `empty` among the malformed values (`abc`, empty, negative)
        that must take the fail-closed path, and that the test was pinning the
        contradiction rather than the rule. A truncated write is exactly how the
        value is lost in practice, so it is the shape least safe to guess at.
        """
        with self.assertRaises(state.UnknownProtocolVersion):
            self._doc("").protocol_version()

    def test_a_line_that_is_absent_entirely_still_reads_as_one(self):
        doc = state.Orchestration.loads("# x\n\n## State\n\n- writer: sdd_runner\n\n")
        self.assertEqual(doc.protocol_version(), 1)


class BothWritersDialectsAreRead(unittest.TestCase):
    """security:SEC-001 / domain:DOM-003 — the gate was defeated by spelling.

    This core writes `- protocol version: 1` inside `## State`. The skill's
    canonical scaffold states `- Protocol version: \\`1\\`` in the header block,
    capitalised and backticked. A reader that understood only its own dialect read
    the other writer's document as *absent* and resumed it as version 1 — so
    FR-010's fail-closed refusal could never fire on the writer most likely to
    declare a version this core cannot implement.
    """

    TEMPLATE = os.path.join(REPO_ROOT, "skills", "sdd-orchestrate", "templates",
                            "ORCHESTRATION.md")

    def test_the_canonical_scaffold_is_read_at_the_version_it_states(self):
        with open(self.TEMPLATE, encoding="utf-8") as fh:
            text = fh.read()
        self.assertEqual(state.Orchestration.loads(text).protocol_version(),
                         policy.PROTOCOL_VERSION,
                         "the template states a version this core cannot read")

    def test_the_scaffolds_dialect_is_read_at_a_version_it_does_not_implement(self):
        """The case that matters: a template-shaped document declaring v99."""
        with open(self.TEMPLATE, encoding="utf-8") as fh:
            text = fh.read()
        bumped = text.replace("- Protocol version: `1`", "- Protocol version: `99`")
        self.assertNotEqual(bumped, text, "the template anchor moved")
        self.assertEqual(state.Orchestration.loads(bumped).protocol_version(), 99)

    def test_both_spellings_of_the_field_are_understood(self):
        for line in ("- protocol version: 7", "- Protocol version: `7`",
                     "- PROTOCOL VERSION: 7", "- Protocol Version:  `7` "):
            with self.subTest(spelling=line):
                doc = state.Orchestration.loads("# x\n\n%s\n\n## State\n\n- writer: x\n" % line)
                self.assertEqual(doc.protocol_version(), 7)


class TheVersionIsCarriedNotRestamped(unittest.TestCase):
    """domain:DOM-010 — a resumed run keeps the version it was written under."""

    def test_the_loop_persists_the_documents_version_not_the_cores(self):
        """Forces the two apart — domain:DOM-010.

        The first version of this test performed the assignment under test itself
        and then asserted the result was 1, which also passes with the production
        line deleted, because `Loop.__init__` seeds the field with
        `PROTOCOL_VERSION == 1`. `loop.py`'s own comment says why: "Today the two
        are always equal" — which is exactly the reason the test has to make them
        unequal. Here the core claims version 2 and the document says 1; the
        persisted State must still say 1.
        """
        import json as _json
        import tempfile as _tempfile
        from unittest import mock
        from sdd_runner import RunRequest, run
        from tests import support
        with _tempfile.TemporaryDirectory() as tmp:
            repo, feature = support.make_repo(tmp)
            script = os.path.join(tmp, "s.json")
            with open(script, "w", encoding="utf-8") as fh:
                _json.dump(([support.fixture("worker_done.md"), support.approve_block()] * 2)
                           + support.finalization_flat(), fh)
            # A run that leaves RESUMABLE state: a converged one records DONE and
            # re-entry rightly refuses, so it cannot exercise the carry at all.
            run(RunRequest(repo=repo, feature=feature, backend="stub",
                           stub_script=script, baseline=support.GREEN_BASELINE,
                           max_delegations=1))
            path = os.path.join(feature, "ORCHESTRATION.md")
            with open(path, encoding="utf-8") as fh:
                self.assertIn("- protocol version: 1", fh.read())

            # Now the core moves on and the document does not. The test must NOT
            # perform the carry itself — the previous two versions did, one level
            # apart, and both passed with the production line deleted
            # (domain:DOM-010, re-reported). `_load_or_create_state` is what sets
            # it in a real run, so that is what runs here.
            with mock.patch.object(policy, "PROTOCOL_VERSION", 2), \
                    mock.patch("sdd_runner.loop.PROTOCOL_VERSION", 2), \
                    mock.patch("sdd_runner.state.PROTOCOL_VERSION", 2):
                self.assertEqual(
                    state.parse_fields(state.Orchestration.load(path).body("State"))
                    ["protocol version"], "1")
                from sdd_runner.loop import Loop
                loop = Loop(repo, feature, backend=None, log=None)
                with open(os.path.join(feature, "TASKS.md"), encoding="utf-8") as fh:
                    unchecked = fh.read().count("- [ ] T")
                # The test does NOT set `loop.protocol_version`. That is the whole
                # point: `_load_or_create_state` must set it, and deleting that
                # must turn this red.
                loop.doc, _resumed = loop._load_or_create_state(unchecked)
                loop.budget = type("B", (), {"cap": 25, "used": 0})()
                self.assertEqual(loop._state_fields("END")["protocol version"], "1",
                                 "a resumed v1 run was restamped as the core's version")

    def test_state_fields_restates_the_carried_value(self):
        import inspect as _inspect
        from sdd_runner import loop as loop_mod
        source = _inspect.getsource(loop_mod.Loop._state_fields)
        self.assertIn("self.protocol_version", source)
        self.assertNotIn('"protocol version": str(PROTOCOL_VERSION)', source)


class TwoStatementsAreAContradiction(unittest.TestCase):
    """security:SEC-009 — the conflict branch existed and nothing exercised it.

    Every `assertRaises(UnknownProtocolVersion)` in this module fed the reader a
    document stating the version **once**, so deleting the conflict branch left
    the suite green while T048 was checked off against a clause naming it.
    """

    @staticmethod
    def _doc(*statements):
        lines = "\n".join("- protocol version: %s" % s for s in statements)
        return state.Orchestration.loads(
            "# x\n\n## State\n\n- writer: sdd_runner\n%s\n\n" % lines)

    def test_two_different_versions_fail_closed_naming_both(self):
        with self.assertRaises(state.UnknownProtocolVersion) as caught:
            self._doc("1", "2").protocol_version()
        self.assertIn("1", str(caught.exception))
        self.assertIn("2", str(caught.exception))

    def test_the_same_version_stated_twice_is_not_a_contradiction(self):
        """The other half of T048's clause, and the one that would over-refuse."""
        self.assertEqual(self._doc("1", "1").protocol_version(), 1)
        self.assertEqual(self._doc("2", "2", "2").protocol_version(), 2)

    def test_the_two_dialects_stating_the_same_value_agree(self):
        """A document carrying both spellings is not self-contradictory."""
        doc = state.Orchestration.loads(
            "# x\n\n- Protocol version: `3`\n\n## State\n\n"
            "- writer: sdd_runner\n- protocol version: 3\n\n")
        self.assertEqual(doc.protocol_version(), 3)

    def test_the_two_dialects_disagreeing_fail_closed(self):
        doc = state.Orchestration.loads(
            "# x\n\n- Protocol version: `9`\n\n## State\n\n"
            "- writer: sdd_runner\n- protocol version: 1\n\n")
        with self.assertRaises(state.UnknownProtocolVersion):
            doc.protocol_version()


class ResumeRefusesWhatItCannotImplement(unittest.TestCase):
    def _inspect(self, text):
        doc = state.Orchestration.loads(text)
        return resume.inspect(doc, "/tmp/ORCHESTRATION.md", 3, socket.gethostname())

    def _live_active(self, version_line):
        return ("# x\n\n## State\n\n- writer: sdd_runner\n%s"
                "- entry: ready\n- phase: IMPLEMENT\n- max-delegations: 25\n"
                "- delegations used: 0\n- runner host: %s\n- runner pid: 1\n\n"
                "## Run result\n\nACTIVE\n\nresumable: yes\n\n"
                % (version_line, socket.gethostname()))

    def test_a_newer_version_is_unresumable_and_names_both_numbers(self):
        with self.assertRaises(resume.UnresumableState) as caught:
            self._inspect(self._live_active("- protocol version: 99\n"))
        self.assertIn("99", caught.exception.reason)
        self.assertIn(str(policy.PROTOCOL_VERSION), caught.exception.reason)
        self.assertTrue(caught.exception.remediation)

    def test_an_unreadable_version_is_unresumable_and_quotes_what_it_read(self):
        with self.assertRaises(resume.UnresumableState) as caught:
            self._inspect(self._live_active("- protocol version: abc\n"))
        self.assertIn("abc", caught.exception.reason)
        self.assertIn(str(policy.PROTOCOL_VERSION), caught.exception.remediation)

    def test_the_refusal_is_checked_before_the_document_is_believed(self):
        """A version the core cannot implement must not be authenticated by its fields."""
        text = self._live_active("- protocol version: 99\n").replace(
            "## Run result\n\nACTIVE", "## Run result\n\nDONE")
        with self.assertRaises(resume.UnresumableState) as caught:
            self._inspect(text)
        self.assertIn("protocol version 99", caught.exception.reason)


class ThroughTheCli(unittest.TestCase):
    def test_a_newer_version_exits_state_unresumable_without_a_traceback(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, feature = __import__("tests.support", fromlist=["x"]).make_repo(tmp)
            path = os.path.join(feature, "ORCHESTRATION.md")
            doc = state.new_document(feature, "runner", "now",
                                     {"max_iterations": 3, "max_delegations": 25})
            doc.save(path)
            with open(path, encoding="utf-8") as fh:
                text = fh.read()
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(re.sub(r"- protocol version: 1", "- protocol version: 99", text))
            code, _out, err = golden.run_cli(
                ["--repo", repo, "--feature", feature, "--dry-run"], repo, tmp)
        self.assertEqual(code, exits.STATE_UNRESUMABLE)
        self.assertIn("protocol version 99", err)
        self.assertNotIn("Traceback", err)


if __name__ == "__main__":
    unittest.main()
