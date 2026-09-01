"""`--feature` containment — spec 040 AC-016, AUDIT-5.

The four path cases, each proving that a refusal writes **nothing** — at the
requested location or at the location the path actually resolves to. That second
half is the one a string-prefix check cannot give you: `repo/specs/features/x`
can be a symlink whose target is anywhere, and a prefix comparison sees only the
name.
"""

import os
import subprocess
import sys
import tempfile
import unittest

from sdd_runner import exits
from tests.support import SPEC, TASKS, make_repo

RUNNER_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ARTIFACTS = ("ORCHESTRATION.md", "run.jsonl")


class FeatureContainment(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo, self.feature_dir = make_repo(self.tmp.name)
        # The external target is a COMPLETE, otherwise-valid feature folder. If it
        # were empty the gate would refuse it for a missing SPEC.md and the test
        # would pass without the containment check existing at all.
        self.outside = os.path.join(self.tmp.name, "outside")
        os.makedirs(self.outside, exist_ok=True)
        for name, body in (("SPEC.md", SPEC), ("TASKS.md", TASKS)):
            with open(os.path.join(self.outside, name), "w", encoding="utf-8") as fh:
                fh.write(body)

    def run_cli(self, feature):
        env = dict(os.environ, PYTHONPATH=RUNNER_ROOT)
        with open(os.devnull, "rb") as devnull:
            return subprocess.run(
                [sys.executable, "-m", "sdd_runner", "--repo", self.repo,
                 "--feature", feature, "--dry-run"],
                stdin=devnull, capture_output=True, text=True, env=env, timeout=60)

    def assert_no_artifacts(self, *directories):
        for directory in directories:
            for name in ARTIFACTS:
                path = os.path.join(directory, name)
                self.assertFalse(os.path.exists(path),
                                 "a refusal left %s behind" % path)

    def assert_refused(self, proc):
        """Refused for CONTAINMENT, not for some other missing precondition."""
        self.assertEqual(proc.returncode, exits.GATE_REFUSED, proc.stderr)
        self.assertIn("remediation", proc.stderr.lower())
        self.assertIn("specs/features", proc.stderr,
                      "the refusal must name containment, not a different condition")
        self.assertNotIn("SPEC.md missing", proc.stderr,
                         "refused for the wrong reason: the target is a valid feature folder")

    # -- the four cases --------------------------------------------------
    def test_an_absolute_external_path_is_refused(self):
        self.assert_refused(self.run_cli(self.outside))
        self.assert_no_artifacts(self.outside)

    def test_a_dotdot_escape_is_refused(self):
        self.assert_refused(self.run_cli("../outside"))
        self.assert_no_artifacts(self.outside)

    def test_a_symlink_escape_is_refused_and_writes_at_neither_location(self):
        """The requested path is inside; what it resolves to is not."""
        link = os.path.join(self.repo, "specs", "features", "999-escape")
        os.symlink(self.outside, link)
        proc = self.run_cli("specs/features/999-escape")
        self.assert_refused(proc)
        self.assert_no_artifacts(self.outside, os.path.dirname(link))

    def test_a_path_inside_the_repo_but_outside_specs_features_is_refused(self):
        elsewhere = os.path.join(self.repo, "elsewhere")
        os.makedirs(elsewhere, exist_ok=True)
        for name, body in (("SPEC.md", SPEC), ("TASKS.md", TASKS)):
            with open(os.path.join(elsewhere, name), "w", encoding="utf-8") as fh:
                fh.write(body)
        proc = self.run_cli("elsewhere")
        self.assert_refused(proc)
        self.assert_no_artifacts(elsewhere)

    # -- and the legitimate one still works ------------------------------
    def test_the_real_feature_folder_is_accepted(self):
        proc = self.run_cli("specs/features/900-fixture")
        self.assertEqual(proc.returncode, exits.OK, proc.stderr)

    def test_a_symlink_that_stays_inside_specs_features_is_accepted(self):
        """Containment is about where it lands, not about being a symlink."""
        link = os.path.join(self.repo, "specs", "features", "901-alias")
        os.symlink(self.feature_dir, link)
        # The link is itself a repository change; commit it, or the run is refused
        # for an unattributed dirty tree and this proves nothing about containment.
        subprocess.run(["git", "-C", self.repo, "add", "-A"], capture_output=True, check=True)
        subprocess.run(["git", "-C", self.repo, "commit", "-qm", "alias"],
                       capture_output=True, check=True)
        proc = self.run_cli("specs/features/901-alias")
        self.assertEqual(proc.returncode, exits.OK, proc.stderr)

    def test_the_features_root_itself_is_refused(self):
        self.assert_refused(self.run_cli("specs/features"))


if __name__ == "__main__":
    unittest.main()
