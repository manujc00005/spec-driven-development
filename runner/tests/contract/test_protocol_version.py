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

from sdd_runner import exits, policy, resume, state
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

    def test_an_empty_value_is_absence_not_corruption(self):
        """`- protocol version:` with nothing after it is a missing field, not a bad one."""
        self.assertEqual(self._doc("").protocol_version(), 1)


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
