"""FR-005: ORCHESTRATION.md round-trips byte-identically, including real artifacts."""

import os
import tempfile
import unittest

from sdd_runner import closure, state
from tests.support import REPO_ROOT

REAL_ARTIFACTS = [
    "specs/features/032-autonomous-loop-residual-calibration/ORCHESTRATION.md",
    "specs/features/033-task-verification-criterion/ORCHESTRATION.md",
]


class RoundTrip(unittest.TestCase):
    def test_real_phase_one_artifacts_round_trip_byte_identically(self):
        checked = 0
        for rel in REAL_ARTIFACTS:
            path = os.path.join(REPO_ROOT, rel)
            if not os.path.isfile(path):
                continue
            with self.subTest(artifact=rel):
                with open(path, encoding="utf-8") as fh:
                    raw = fh.read()
                self.assertEqual(state.Orchestration.loads(raw).dumps(), raw)
                checked += 1
        self.assertTrue(checked, "no real phase-1 artifact was available to check")

    def test_unknown_sections_are_carried_through_verbatim(self):
        raw = "# T\n\n## Weird Section\n\nfree text\n\n## State\n\n- phase: X\n"
        doc = state.Orchestration.loads(raw)
        doc.set_body("State", "\n- phase: Y\n")
        self.assertIn("## Weird Section\n\nfree text\n\n", doc.dumps())

    def test_append_line_is_append_only(self):
        doc = state.new_document("f", "runner", 0, {"max_iterations": 3, "max_delegations": 25})
        doc.append_line("Delegation log", "- A-001 worker: dispatched")
        doc.append_line("Delegation log", "- A-002 domain: dispatched")
        body = doc.body("Delegation log")
        self.assertLess(body.index("A-001"), body.index("A-002"))


class ClosureHashingIsTotal(unittest.TestCase):
    """PY-1: `_hash_file` must classify every path, never raise out of an audit.

    The closure delta is the last gate before DONE. A file the process cannot
    read must produce a value that differs from any real hash - so it registers
    as a change - not an exception that aborts the audit.
    """

    def test_an_unreadable_file_is_marked_rather_than_raising(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "locked.txt")
            with open(path, "w", encoding="utf-8") as fh:
                fh.write("secret-ish")
            os.chmod(path, 0o000)
            try:
                if os.access(path, os.R_OK):
                    self.skipTest("running as a user that ignores file modes")
                value = closure._hash_file(path)
            finally:
                os.chmod(path, 0o600)   # inside the tmpdir, or cleanup cannot remove it
        self.assertEqual(value, closure.UNREADABLE)

    def test_a_missing_file_and_an_unreadable_one_are_distinguishable(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(closure._hash_file(os.path.join(tmp, "gone")), closure.DELETED)


class RedactionAtTheWriter(unittest.TestCase):
    """AC-012: the state file must not carry a credential an agent echoed.

    `dumps()` is the in-memory document and stays verbatim, so round-trip
    fidelity is untouched; `redacted()` is what reaches disk.
    """

    SENTINEL = "sk-ant-sentinel-state-0002"

    def _doc(self):
        doc = state.new_document("f", "runner", 0,
                                 {"max_iterations": 3, "max_delegations": 25})
        doc.environ = {"ANTHROPIC_API_KEY": self.SENTINEL}
        doc.set_body("Escalations",
                     "\n- **waiting** (money) on T001: bill it with %s?\n\n" % self.SENTINEL)
        return doc

    def test_save_strips_the_secret(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "ORCHESTRATION.md")
            self._doc().save(path)
            with open(path, encoding="utf-8") as fh:
                body = fh.read()
        self.assertNotIn(self.SENTINEL, body)
        self.assertIn("[REDACTED]", body)
        self.assertIn("bill it with", body, "the surrounding text must survive")

    def test_dumps_is_left_verbatim_so_round_trip_fidelity_is_unaffected(self):
        self.assertIn(self.SENTINEL, self._doc().dumps())

    def test_a_document_with_no_known_secrets_is_written_unchanged(self):
        doc = state.new_document("f", "runner", 0,
                                 {"max_iterations": 3, "max_delegations": 25})
        doc.environ = {"PATH": "/usr/bin"}
        self.assertEqual(doc.redacted(), doc.dumps())


class AtomicSave(unittest.TestCase):
    def test_save_is_atomic_and_leaves_no_temp_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "ORCHESTRATION.md")
            doc = state.new_document("f", "runner", 0,
                                     {"max_iterations": 3, "max_delegations": 25})
            doc.save(path)
            self.assertTrue(os.path.isfile(path))
            leftovers = [n for n in os.listdir(tmp) if n.startswith(".orchestration-")]
            self.assertEqual(leftovers, [])

    def test_run_result_and_resumability_are_readable_back(self):
        doc = state.new_document("f", "runner", 0, {"max_iterations": 3, "max_delegations": 25})
        self.assertEqual(doc.run_result(), "ACTIVE")
        self.assertTrue(doc.is_active())
        doc.set_body("Run result", "\nPAUSED\n\nresumable: yes\n\n")
        self.assertEqual(doc.run_result(), "PAUSED")
        self.assertFalse(doc.is_active())
        self.assertTrue(doc.resumable())


if __name__ == "__main__":
    unittest.main()
