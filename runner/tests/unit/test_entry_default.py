"""Spec 041 D007: a state document without an `entry` field is a `ready` entry."""

import unittest

from sdd_runner import resume, state


def _doc(entry=None):
    caps = {"max_iterations": 3, "max_delegations": 25, "pid": 4242, "host": "h"}
    if entry is not None:
        caps["entry"] = entry
    doc = state.new_document("specs/features/900-fixture", "runner", "2026-09-02T00:00:00Z", caps)
    return doc


class EntryField(unittest.TestCase):
    def _inspect(self, doc):
        # ACTIVE on this host with a dead pid: an interrupted run, resumable.
        return resume.inspect(doc, "ORCHESTRATION.md", 3, "h", pid_alive=lambda pid: False)

    def test_a_new_document_records_the_entry(self):
        for entry in ("ready", "adopt"):
            with self.subTest(entry=entry):
                fields = state.parse_fields(_doc(entry).body("State"))
                self.assertEqual(fields["entry"], entry)
                self.assertEqual(self._inspect(_doc(entry)).entry, entry)

    def test_a_document_without_the_field_authenticates_as_ready(self):
        doc = _doc()
        fields = state.parse_fields(doc.body("State"))
        del fields["entry"]
        doc.set_body("State", state.render_fields(fields))
        self.assertNotIn("entry", state.parse_fields(doc.body("State")))
        self.assertEqual(self._inspect(doc).entry, "ready")



class AdoptionFactsArePersisted(unittest.TestCase):
    """Spec 041 T017 / CONF-041-03: a runner-written adopted document must be able
    to say what it inherited, not only that it was an adopt entry."""

    def _adopted_doc(self, tmp):
        from sdd_runner import gate
        from tests.support import make_adopted_repo
        repo, feature_dir, info = make_adopted_repo(tmp)
        record = gate.inherited_record(repo, feature_dir)
        self.assertIsInstance(record, gate.Inherited)
        doc = state.new_document(feature_dir, "runner", "2026-09-02T00:00:00Z",
                                 {"max_iterations": 3, "max_delegations": 25,
                                  "pid": 1, "host": "h", "entry": "adopt",
                                  "inherited": record})
        return doc, info

    def test_an_adopted_document_records_baseline_diff_base_and_inherited_rows(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            doc, info = self._adopted_doc(tmp)
            fields = state.parse_fields(doc.body("State"))
            self.assertEqual(fields["entry"], "adopt")
            self.assertEqual(fields["adoption baseline commit"], info["baseline"])
            self.assertEqual(fields["adoption diff base"],
                             "%s (against %s)" % (info["diff_base"], info["default_branch"]))
            headers, rows = state.parse_table(doc.body("Inherited"))
            self.assertEqual(headers, state.INHERITED_COLUMNS)
            self.assertEqual([r["Task"] for r in rows], ["T001", "T002"])
            for row in rows:
                self.assertEqual(row["Checked before adoption"], "yes")
                self.assertEqual(row["Verification observed by this run"], "no")
                self.assertTrue(row["Verify clause"].strip())

    def test_a_ready_document_records_no_adoption_facts(self):
        doc = _doc("ready")
        fields = state.parse_fields(doc.body("State"))
        self.assertEqual(fields["adoption baseline commit"], "n/a")
        self.assertEqual(fields["adoption diff base"], "n/a")
        headers, rows = state.parse_table(doc.body("Inherited"))
        self.assertEqual(headers, state.INHERITED_COLUMNS)
        self.assertEqual(rows, [])

    def test_an_uncomputable_record_stops_the_run_instead_of_degrading_it(self):
        """NEW-6: never write `entry: adopt` with `n/a` adoption fields."""
        import subprocess
        import tempfile
        from sdd_runner import resume as resume_mod
        from sdd_runner.loop import Loop
        from tests.support import make_adopted_repo
        with tempfile.TemporaryDirectory() as tmp:
            repo, feature_dir, _ = make_adopted_repo(tmp)
            subprocess.run(["git", "-C", repo, "remote", "remove", "origin"],
                           check=True, capture_output=True)
            loop = Loop(repo, feature_dir, backend=None, log=None, adopt=True)
            with self.assertRaises(resume_mod.UnresumableState) as caught:
                loop._inherited_record()
            self.assertIn("no longer computable", caught.exception.reason)


if __name__ == "__main__":
    unittest.main()
