"""Spec 041 T001: the adoption fixture has the shape the adoption gate expects.

Every later 041 test — gate matrix, dry-run, calibration — builds on this repo,
so its shape is pinned here rather than assumed there.
"""

import os
import re
import subprocess
import tempfile
import unittest

from tests.support import make_adopted_repo


def git(repo, *args):
    return subprocess.run(["git", "-C", repo] + list(args), check=True,
                          capture_output=True, text=True).stdout.strip()


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


class AdoptedFixtureShape(unittest.TestCase):
    def test_adopt_fixture_shape(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, feature_dir, info = make_adopted_repo(tmp)

            # On a non-default branch, clean, with the default branch resolvable
            # through origin/HEAD (D003: the gate never assumes "main").
            self.assertEqual(git(repo, "rev-parse", "--abbrev-ref", "HEAD"), info["branch"])
            self.assertEqual(git(repo, "status", "--porcelain"), "")
            self.assertEqual(git(repo, "symbolic-ref", "--short", "refs/remotes/origin/HEAD"),
                             "origin/" + info["default_branch"])

            # The inherited record the gate will compute (spec 041 condition 7).
            self.assertEqual(git(repo, "rev-parse", "HEAD"), info["baseline"])
            self.assertEqual(git(repo, "merge-base", info["default_branch"], "HEAD"),
                             info["diff_base"])
            self.assertNotEqual(info["baseline"], info["diff_base"])
            self.assertEqual(git(repo, "log", "--oneline", "%s..HEAD" % info["diff_base"]).count("\n"),
                             0, "exactly one commit sits on the feature branch")

            # In Progress, two checked tasks (each with a Verify: clause), two unchecked.
            spec = read(os.path.join(feature_dir, "SPEC.md"))
            self.assertRegex(spec, r"## Status\n\nIn Progress\n")
            tasks = read(os.path.join(feature_dir, "TASKS.md"))
            checked = re.findall(r"^- \[x\] (T\d{3}).*?Verify: \S", tasks, re.M)
            self.assertEqual(checked, ["T001", "T002"])
            self.assertEqual(re.findall(r"^- \[ \] (T\d{3})", tasks, re.M), ["T003", "T004"])

            # The inherited diff carries the implementation and the seeded defect.
            changed = git(repo, "diff", "--name-only", "%s..HEAD" % info["diff_base"]).splitlines()
            self.assertIn("src/pricing.py", changed)
            self.assertIn("SEEDED DEFECT", read(os.path.join(repo, "src", "pricing.py")))


if __name__ == "__main__":
    unittest.main()
