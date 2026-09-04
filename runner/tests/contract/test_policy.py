"""One definition per protocol constant — spec 042 AC-001, FR-008.

`policy` is the vocabulary. The guard here is structural rather than
aspirational: it walks the package's ASTs and fails if any name `policy` defines
is *assigned* anywhere else. A re-export (`from .policy import X`) is an import,
not an assignment, so the modules keep their public spelling and still have one
definition between them.
"""

import ast
import io
import os
import unittest

from sdd_runner import policy

PACKAGE = os.path.dirname(os.path.abspath(policy.__file__))
# AC-001 says "anywhere under `runner/`" and FR-001 names the CLI, a backend **and
# a test fixture** as places a duplicate must not hide. The walk covered
# `runner/sdd_runner/` only, so a constant redefined in a fixture would not have
# failed it (spec 042 CONF-004). The property held — widening it found nothing —
# but a guard narrower than the criterion it enforces is a guard with a blind spot.
RUNNER_ROOT = os.path.dirname(PACKAGE)

# The only exclusions, and each is a source file that is *not* a place a protocol
# constant could be defined for the package to read:
#   * `policy.py` itself, which is where they are defined;
#   * `__pycache__`, which is generated.
# Nothing else is skipped — not the tests, not the fixtures, not the backends.
EXCLUDED_DIRS = {"__pycache__"}


def _module_files():
    for dirpath, dirs, files in os.walk(RUNNER_ROOT):
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
        for name in sorted(files):
            if name.endswith(".py"):
                yield os.path.join(dirpath, name)


def _module_level_assignments(path):
    """Upper-case names assigned at module level in `path`."""
    with io.open(path, encoding="utf-8") as fh:
        tree = ast.parse(fh.read())
    for node in tree.body:
        targets = []
        if isinstance(node, ast.Assign):
            targets = node.targets
        elif isinstance(node, ast.AnnAssign):
            targets = [node.target]
        for target in targets:
            if isinstance(target, ast.Name) and target.id.isupper():
                yield target.id


def _policy_names():
    return {n for n in dir(policy) if n.isupper() and not n.startswith("_")}


class SingleDefinition(unittest.TestCase):
    def test_no_policy_constant_is_assigned_outside_policy(self):
        names = _policy_names()
        offenders = []
        for path in _module_files():
            if os.path.basename(path) == "policy.py":
                continue
            for assigned in _module_level_assignments(path):
                if assigned in names:
                    offenders.append("%s assigns %s" %
                                     (os.path.relpath(path, RUNNER_ROOT), assigned))
        self.assertEqual(offenders, [], "protocol constants defined twice: %s" % offenders)

    def test_the_walk_covers_everything_the_criterion_names(self):
        """AC-001 says `runner/`, not `runner/sdd_runner/` (CONF-004)."""
        walked = list(_module_files())
        self.assertTrue(any(os.sep + "tests" + os.sep in f for f in walked),
                        "the walk no longer reaches the tests AC-001 names")
        self.assertTrue(any(os.sep + "backends" + os.sep in f for f in walked),
                        "the walk no longer reaches the backends")
        self.assertGreater(len(walked), 30)

    def test_only_policy_defines_the_canonical_constants(self):
        """Stated positively: exactly one file assigns each of them."""
        names = _policy_names()
        definers = {}
        for path in _module_files():
            for assigned in _module_level_assignments(path):
                if assigned in names:
                    definers.setdefault(assigned, []).append(os.path.basename(path))
        for name in sorted(names):
            with self.subTest(constant=name):
                self.assertEqual(definers.get(name, ["policy.py"]), ["policy.py"],
                                 "%s is defined outside policy.py" % name)

    def test_policy_is_not_empty_and_covers_the_inventoried_vocabulary(self):
        """A guard over an empty set passes for the wrong reason."""
        names = _policy_names()
        self.assertGreaterEqual(len(names), 39)
        for expected in ("OK", "NAMES", "SEVERITIES", "FINDING_KEYS", "FLOOR", "PER_TASK",
                         "HUMAN_GATED", "READY_STATUSES", "ADOPT_STATUSES", "REENTRY_STATUSES",
                         "KNOWN_STATUS_WORDS", "RUN_ARTIFACTS", "REVIEWERS", "READ_ONLY_AGENTS",
                         "CORE_COMPLETE", "AGENT_FILES", "SECURITY_TRIGGERS", "RUN_RESULTS",
                         "TERMINAL_RESULTS", "RECOVERABLE_RESULTS", "LIFECYCLE",
                         "INHERITED_COLUMNS", "ATTEMPT_COLUMNS", "FINDING_COLUMNS",
                         "FEATURES_ROOT", "PROTOCOL_VERSION"):
            with self.subTest(constant=expected):
                self.assertIn(expected, names)

    def test_policy_sits_at_the_bottom_of_the_import_graph(self):
        """It must be readable without dragging the loop in behind it."""
        with io.open(policy.__file__, encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                # `assertIsNone(node.module and node.level and node.module)` lived
                # here and was incoherent: for any level-0 import the expression is
                # `0`, so it would have failed with "policy must not import from the
                # package" against a perfectly ordinary `from x import y`. Latent
                # only because `policy` has no ImportFrom at all (domain:DOM-011).
                # The level check below is the guard that was meant.
                self.assertEqual(node.level, 0, "policy must not use a relative import")
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self.assertNotIn("sdd_runner", alias.name)


class ValuesAreUnchanged(unittest.TestCase):
    """The refactor moved these; it did not get to edit them (AC-008)."""

    def test_the_closed_vocabularies(self):
        self.assertEqual(policy.SEVERITIES, ("Critical", "High", "Medium", "Low"))
        self.assertEqual(policy.RUN_RESULTS, ("ACTIVE", "PAUSED", "DONE", "ABORTED"))
        self.assertEqual(policy.LIFECYCLE,
                         ("PLANNED", "DISPATCHED", "RESPONDED", "VERIFIED", "RECOVERED", "FAILED"))
        self.assertEqual(policy.REVIEWERS, ("domain", "security", "final-conformance"))
        self.assertEqual(policy.KNOWN_STATUS_WORDS,
                         ("Draft", "Ready", "In Progress", "In Review", "Done", "Archived"))
        self.assertEqual(len(policy.HUMAN_GATED), 6)
        self.assertEqual(len(policy.SECURITY_TRIGGERS), 10)

    def test_the_budget_formula_constants(self):
        self.assertEqual((policy.FLOOR, policy.PER_TASK), (25, 6))

    def test_the_exit_codes(self):
        self.assertEqual(
            [policy.OK, policy.GATE_REFUSED, policy.HUMAN_ESCALATION, policy.CAP_ABORT,
             policy.BUDGET_EXHAUSTED, policy.BACKEND_PRECONDITION, policy.CONCURRENT_RUN,
             policy.STATE_UNRESUMABLE, policy.NOT_CONVERGED, policy.CLOSURE_NOT_PROVEN,
             policy.INTERNAL_ERROR],
            [0, 10, 11, 12, 13, 14, 15, 16, 17, 18, 70])
        self.assertEqual(len(policy.NAMES), 11)


if __name__ == "__main__":
    unittest.main()
