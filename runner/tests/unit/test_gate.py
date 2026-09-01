"""FR-002 / AC-003: each precondition refuses by name, and changes nothing."""

import os
import subprocess
import tempfile
import unittest

from sdd_runner import gate
from tests.support import SPEC, TASKS, make_repo


def git_status(repo):
    return subprocess.run(["git", "-C", repo, "status", "--porcelain"],
                          capture_output=True, text=True).stdout


class GatePasses(unittest.TestCase):
    def test_a_clean_ready_feature_on_a_branch_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, feature_dir = make_repo(tmp)
            self.assertEqual(gate.check(repo, feature_dir), [])


class EachPreconditionRefusesByName(unittest.TestCase):
    def _conditions(self, repo, feature_dir, **kw):
        before = git_status(repo)
        refusals = gate.check(repo, feature_dir, **kw)
        # Every refusal must leave the tree byte-identical.
        self.assertEqual(git_status(repo), before)
        for r in refusals:
            self.assertTrue(r.remediation, "refusal %r has no remediation" % r.condition)
        return [r.condition for r in refusals]

    def test_lifecycle_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, feature_dir = make_repo(tmp, spec=SPEC.replace("Ready", "Draft"))
            self.assertIn("lifecycle status", self._conditions(repo, feature_dir))

    def test_open_questions(self):
        spec = SPEC.replace("- ~~OQ-1~~ **Resolved.**",
                            "- ~~OQ-1~~ **Resolved.**\n- OQ-2: something genuinely unresolved.")
        with tempfile.TemporaryDirectory() as tmp:
            repo, feature_dir = make_repo(tmp, spec=spec)
            self.assertIn("open questions", self._conditions(repo, feature_dir))

    def test_missing_tasks_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, feature_dir = make_repo(tmp)
            os.remove(os.path.join(feature_dir, "TASKS.md"))
            self.assertIn("TASKS.md missing", self._conditions(repo, feature_dir))

    def test_default_branch(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, feature_dir = make_repo(tmp)
            subprocess.run(["git", "-C", repo, "checkout", "-q", "master"],
                           capture_output=True, text=True)
            subprocess.run(["git", "-C", repo, "branch", "-M", "main"],
                           capture_output=True, text=True)
            self.assertIn("default branch", self._conditions(repo, feature_dir))

    def test_unattributed_dirty_tree(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, feature_dir = make_repo(tmp)
            with open(os.path.join(repo, "agents", "implementer.md"), "a",
                      encoding="utf-8") as fh:
                fh.write("\nedited outside the feature folder\n")
            self.assertIn("unattributed dirty tree", self._conditions(repo, feature_dir))

    def test_red_baseline_suite(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, feature_dir = make_repo(tmp)
            conditions = self._conditions(repo, feature_dir,
                                          baseline_cmd=["false"])
            self.assertIn("red baseline suite", conditions)

    def test_baseline_that_mutates_the_tree(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, feature_dir = make_repo(tmp)
            script = os.path.join(tmp, "mutate.sh")
            with open(script, "w", encoding="utf-8") as fh:
                fh.write("#!/bin/sh\necho mutated >> agents/implementer.md\n")
            os.chmod(script, 0o755)
            before = git_status(repo)
            refusals = gate.check(repo, feature_dir, baseline_cmd=[script])
            self.assertIn("baseline suite mutates the tree",
                          [r.condition for r in refusals])
            self.assertNotEqual(git_status(repo), before)   # the baseline did it, not the gate


class RefusalRendering(unittest.TestCase):
    def test_refusal_names_condition_detail_and_remediation(self):
        r = gate.Refusal("open questions", "2 unresolved", "answer them")
        rendered = r.render()
        for part in ("open questions", "2 unresolved", "answer them"):
            self.assertIn(part, rendered)


if __name__ == "__main__":
    unittest.main()
