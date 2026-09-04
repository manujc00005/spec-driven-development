"""Two guards for rules that were correct but unguarded — spec 042 T030, T045.

Both come from the reviews, and both are the same class of gap: a rule the code
gets right, with no test that would notice if it stopped.
"""

import os
import tempfile
import unittest

from sdd_runner import RunRequest, run
from tests import support


class SiblingPrefixContainment(unittest.TestCase):
    """security:SEC-003 — the case that motivates `commonpath` had no test.

    `protocol.resolve_feature` compares resolved paths with
    `os.path.commonpath`, and both its docstring and the SPEC name
    `specs/features-old` as the reason: it is a *string prefix* of
    `specs/features`, so a `startswith` check would call it contained. The suite
    covered absolute-external paths, `..`, symlink escape and the features root —
    every case a prefix check also catches. Rewriting the check as `startswith`
    would have reintroduced spec 040 D042's exact bug with the suite green.
    """

    def test_a_sibling_whose_path_is_a_prefix_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, _feature = support.make_repo(tmp)
            sibling = os.path.join(repo, "specs", "features-old", "900-fixture")
            os.makedirs(sibling)
            for name, text in (("SPEC.md", support.SPEC), ("TASKS.md", support.TASKS)):
                with open(os.path.join(sibling, name), "w", encoding="utf-8") as fh:
                    fh.write(text)
            outcome = run(RunRequest(repo=repo, feature="specs/features-old/900-fixture",
                                     dry_run=True))
        self.assertEqual(outcome.exit_code, 10)
        self.assertTrue(outcome.diagnostics)
        self.assertIn("outside the spec trail", outcome.diagnostics[0].text)

    def test_the_guard_would_fail_under_a_startswith_rewrite(self):
        """States the mutation this test exists to catch, so the next reader can run it."""
        repo_root = "/repo/specs/features"
        candidate = "/repo/specs/features-old/900-fixture"
        self.assertTrue(candidate.startswith(repo_root),
                        "the sibling is a string prefix — that is the whole point")
        self.assertNotEqual(os.path.commonpath([repo_root, candidate]), repo_root,
                            "commonpath is what actually answers the question")


class ResumeIsAuthenticatedBeforeTheGate(unittest.TestCase):
    """domain:DOM-015 — the ordering FR-006 moved into the core had no oracle.

    Every scenario that exercises resume authentication uses a repository whose
    entry gate would pass, so swapping the two blocks in `protocol.run` changed
    nothing observable. This fixture is refused by *both*: the document is
    unresumable (exit 16) and the tree is dirty (exit 10). Only the recorded
    ordering yields 16.
    """

    def _repo(self, tmp):
        repo, feature = support.make_repo(tmp)
        with open(os.path.join(feature, "ORCHESTRATION.md"), "w", encoding="utf-8") as fh:
            fh.write("# Orchestration: foreign\n\nnot written by this runner\n")
        with open(os.path.join(repo, "stray.txt"), "w", encoding="utf-8") as fh:
            fh.write("an unattributed dirty path\n")
        return repo, feature

    def test_both_would_refuse_and_resume_answers_first(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, feature = self._repo(tmp)
            outcome = run(RunRequest(repo=repo, feature=feature, dry_run=True))
        self.assertEqual(outcome.exit_code, 16,
                         "the gate answered first: resume authentication was reordered")
        self.assertFalse(outcome.resumable)

    def test_the_gate_really_would_have_refused_this_tree_too(self):
        """Without this, the test above could pass for the wrong reason."""
        from sdd_runner import gate
        with tempfile.TemporaryDirectory() as tmp:
            repo, feature = self._repo(tmp)
            refusals = gate.check(repo, feature, first_entry=False)
        self.assertTrue(refusals, "the fixture must be gate-refusing as well")
        self.assertIn("dirty", " ".join(r.condition for r in refusals))


if __name__ == "__main__":
    unittest.main()
