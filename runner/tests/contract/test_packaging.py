"""Locally packaged, not distributed — spec 042 AC-009, FR-017, D006.

"Installable" was answered by the maintainer as *packaged and locally runnable*,
not *shipped to adopters*. That makes this a two-sided guard: the package must
stand on its own (no import outside itself or the stdlib, a declared package
list, `python3 -m sdd_runner` working from a checkout), and it must stay
**invisible** to the installers — spec 040 D001 is upheld, not superseded.
"""

import ast
import io
import os
import subprocess
import sys
import sysconfig
import unittest

import sdd_runner
from tests.support import REPO_ROOT

PACKAGE = os.path.dirname(os.path.abspath(sdd_runner.__file__))
RUNNER_ROOT = os.path.dirname(PACKAGE)

# The only third-party names the package may mention at all, and only lazily,
# inside the optional Claude backend (spec 040 FR-014, D001).
OPTIONAL = {"claude_agent_sdk", "anyio"}


def _top_level_imports(path):
    with io.open(path, encoding="utf-8") as fh:
        tree = ast.parse(fh.read())
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name.split(".")[0], node
        elif isinstance(node, ast.ImportFrom):
            if node.level:                       # relative: inside the package
                continue
            if node.module:
                yield node.module.split(".")[0], node


class StandsOnItsOwn(unittest.TestCase):
    def test_every_import_is_stdlib_or_the_package_itself(self):
        stdlib = set(sys.stdlib_module_names)
        offenders = []
        for dirpath, _dirs, files in os.walk(PACKAGE):
            for name in sorted(files):
                if not name.endswith(".py"):
                    continue
                path = os.path.join(dirpath, name)
                for module, node in _top_level_imports(path):
                    if module in stdlib or module == "sdd_runner":
                        continue
                    if module in OPTIONAL:
                        # Allowed, but it must not be reachable at import time.
                        self.assertGreater(node.col_offset, 0,
                                           "%s imports %s at module level" % (name, module))
                        continue
                    offenders.append("%s imports %s" % (name, module))
        self.assertEqual(offenders, [], "non-stdlib runtime dependency: %s" % offenders)

    def test_the_runtime_dependency_list_is_empty(self):
        with io.open(os.path.join(RUNNER_ROOT, "pyproject.toml"), encoding="utf-8") as fh:
            text = fh.read()
        self.assertIn("dependencies = []", text)
        self.assertIn('packages = ["sdd_runner", "sdd_runner.backends"]', text)

    def test_the_module_runs_from_a_plain_checkout(self):
        """No SDK, no Codex CLI, no install step — just PYTHONPATH."""
        proc = subprocess.run([sys.executable, "-m", "sdd_runner", "--help"],
                              capture_output=True, text=True, timeout=60,
                              env=dict(os.environ, PYTHONPATH=RUNNER_ROOT))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("--feature", proc.stdout)
        self.assertIn("--dry-run", proc.stdout)

    def test_nothing_here_needs_the_optional_extras(self):
        for name in OPTIONAL:
            with self.subTest(module=name):
                self.assertNotIn(name, sys.modules,
                                 "%s was imported merely by loading the package" % name)


class InvisibleToTheInstallers(unittest.TestCase):
    """FR-017 / spec 040 D001 and AC-014: containment stays checkable, not intended."""

    INSTALLERS = ["install.sh", "install.ps1", "profiles.json",
                  "scripts/check-consistency.sh"]

    def test_no_installer_mentions_the_runner(self):
        for rel in self.INSTALLERS:
            path = os.path.join(REPO_ROOT, rel)
            if not os.path.isfile(path):
                self.skipTest("%s unavailable" % rel)
            with io.open(path, encoding="utf-8") as fh:
                text = fh.read()
            with self.subTest(installer=rel):
                for needle in ("sdd_runner", "runner/"):
                    self.assertNotIn(needle, text,
                                     "%s references the runner; D001 says it must not" % rel)

    def test_the_package_is_not_listed_as_a_shipped_artifact(self):
        path = os.path.join(REPO_ROOT, "profiles.json")
        if not os.path.isfile(path):
            self.skipTest("profiles.json unavailable")
        with io.open(path, encoding="utf-8") as fh:
            self.assertNotIn("runner", fh.read())


if __name__ == "__main__":
    unittest.main()
