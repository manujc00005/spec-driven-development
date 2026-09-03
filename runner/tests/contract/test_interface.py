"""The public interface stays small and stays opaque — spec 042 AC-002, AC-003, AC-010, AC-011.

"Small public surface" and "no internals leak" are properties that decay
silently: one convenient re-export, one dataclass field holding a live object,
and the module is split rather than deep. These are the guards that make the
decay loud.
"""

import ast
import dataclasses
import io
import os
import unittest

import sdd_runner
from sdd_runner import protocol, seams
from sdd_runner.backends import Backend
from sdd_runner.counters import CounterState
from sdd_runner.loop import Loop
from sdd_runner.state import Orchestration

CLI = os.path.join(os.path.dirname(os.path.abspath(sdd_runner.__file__)), "__main__.py")

INTERNAL_TYPES = (Loop, Orchestration, Backend, CounterState, io.IOBase)


class PublicSurface(unittest.TestCase):
    def test_the_surface_is_at_most_twelve_names(self):
        self.assertLessEqual(len(sdd_runner.__all__), 12, sdd_runner.__all__)

    def test_every_declared_name_actually_resolves(self):
        for name in sdd_runner.__all__:
            with self.subTest(name=name):
                self.assertIsNotNone(getattr(sdd_runner, name))

    def test_internals_are_not_reachable_from_the_package_root(self):
        for name in ("Loop", "Orchestration", "CounterState", "Budget", "gate", "loop"):
            with self.subTest(name=name):
                self.assertNotIn(name, sdd_runner.__all__)

    def test_importing_the_package_does_not_drag_the_loop_in(self):
        """PEP 562 laziness is the reason the internal `from . import x` calls stay safe."""
        with io.open(sdd_runner.__file__, encoding="utf-8") as fh:
            source = fh.read()
        tree = ast.parse(source)
        for node in tree.body:
            self.assertNotIsInstance(node, (ast.Import, ast.ImportFrom),
                                     "__init__ must not import at module level")


class TheCliMakesNoProtocolDecision(unittest.TestCase):
    """T008: argv in, exit code out. Everything between belongs to the core."""

    def _cli_tree(self):
        with io.open(CLI, encoding="utf-8") as fh:
            return ast.parse(fh.read())

    def test_it_imports_only_the_public_interface_and_rendering_vocabulary(self):
        allowed = set(sdd_runner.__all__) | {"protocol", "HUMAN_ESCALATION", "NAMES"}
        for node in ast.walk(self._cli_tree()):
            if isinstance(node, ast.ImportFrom) and node.level:
                for alias in node.names:
                    with self.subTest(name=alias.name):
                        self.assertIn(alias.name, allowed,
                                      "the CLI reached past the public interface")

    def test_the_containment_rule_no_longer_lives_in_the_cli(self):
        with io.open(CLI, encoding="utf-8") as fh:
            source = fh.read()
        for leaked in ("realpath", "commonpath", "default_cap", "gate.check",
                       "resume.inspect", "Loop("):
            with self.subTest(rule=leaked):
                self.assertNotIn(leaked, source)


class NothingInternalEscapes(unittest.TestCase):
    def _walk(self, value, path, seen):
        if id(value) in seen:
            return
        seen.add(id(value))
        for internal in INTERNAL_TYPES:
            self.assertNotIsInstance(value, internal,
                                     "%s leaks a %s" % (path, internal.__name__))
        if dataclasses.is_dataclass(value) and not isinstance(value, type):
            for f in dataclasses.fields(value):
                self._walk(getattr(value, f.name), "%s.%s" % (path, f.name), seen)
        elif isinstance(value, (list, tuple, set)):
            for i, item in enumerate(value):
                self._walk(item, "%s[%d]" % (path, i), seen)
        elif isinstance(value, dict):
            for k, item in value.items():
                self._walk(item, "%s[%r]" % (path, k), seen)

    def test_a_refused_outcome_carries_no_internal_object(self):
        outcome = protocol.run(protocol.RunRequest(repo=".", feature="nowhere"))
        self._walk(outcome, "outcome", set())

    def test_the_outcome_and_gate_types_are_frozen_value_types(self):
        for cls in (protocol.RunOutcome, protocol.GateResult, protocol.RunPlan,
                    protocol.RunRequest, protocol.Diagnostic):
            with self.subTest(cls=cls.__name__):
                self.assertTrue(dataclasses.is_dataclass(cls))
                self.assertTrue(cls.__dataclass_params__.frozen,
                                "%s must be frozen: a mutable outcome is shared state"
                                % cls.__name__)

    def test_a_gate_result_is_fail_closed_by_construction(self):
        """There is no way to spell "passed" other than having no refusals."""
        self.assertTrue(protocol.GateResult().passed)
        self.assertFalse(protocol.GateResult((protocol.Refusal("c", "d", "r"),)).passed)
        self.assertNotIn("passed", [f.name for f in dataclasses.fields(protocol.GateResult)])


class SeamsAreDeclaredAndEmpty(unittest.TestCase):
    def test_exactly_three_seams_each_naming_its_owner(self):
        self.assertEqual([s.name for s in seams.SEAMS], ["caller", "backend", "finalizer"])
        for seam in seams.SEAMS:
            with self.subTest(seam=seam.name):
                self.assertTrue(seam.owner and seam.filled_by_today and seam.not_done_here)

    def test_no_autonomous_entry_point_exists(self):
        """The caller seam is open: nothing turns a request into a RunRequest."""
        self.assertNotIn("autonomous", dir(protocol))
        self.assertFalse(hasattr(protocol, "run_from_description"))

    def test_no_lifecycle_skill_is_dispatchable(self):
        """The loop can only delegate to the five agents it knows; none is a lifecycle skill."""
        from sdd_runner import policy
        self.assertEqual(set(policy.AGENT_FILES),
                         {"worker", "domain", "security", "final-conformance", "deep-reasoner"})
        for target in policy.AGENT_FILES.values():
            with self.subTest(target=target):
                self.assertTrue(target.startswith("agents/"))

    def test_no_lifecycle_skill_name_is_used_as_a_value_in_the_loop(self):
        """Prose explaining that the loop does NOT dispatch them is not a violation.

        The first version of this test grepped the file and failed on the
        docstring that says the runner leaves those skills alone — the exact
        over-reach D005 forbids, produced by this feature's own guard on its
        first run. So it reads the AST and skips docstrings: what matters is
        whether a skill name is ever a live value, not whether it is mentioned.
        """
        from sdd_runner import loop
        with io.open(loop.__file__, encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        docstrings = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef,
                                 ast.AsyncFunctionDef)):
                first = node.body[0] if node.body else None
                if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) \
                        and isinstance(first.value.value, str):
                    docstrings.add(id(first.value))
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str) \
                    and id(node) not in docstrings:
                for skill in ("/spec-review", "/spec-close", "/pr-description"):
                    with self.subTest(skill=skill, line=node.lineno):
                        self.assertNotIn(skill, node.value,
                                         "the Finalizer seam is not open: %s" % skill)

    def test_the_finalizers_pre_written_half_is_still_uncalled(self):
        """A-010: found dead code is reported, not removed — and not quietly wired up."""
        from sdd_runner import closure
        package = os.path.dirname(os.path.abspath(closure.__file__))
        callers = []
        for name in sorted(os.listdir(package)):
            if not name.endswith(".py") or name == "closure.py":
                continue
            with io.open(os.path.join(package, name), encoding="utf-8") as fh:
                source = fh.read()
            for symbol in ("classify(", "observe(", "unexpected("):
                if "closure_mod." + symbol in source or "closure." + symbol in source:
                    callers.append("%s -> %s" % (name, symbol))
        self.assertEqual(callers, [], "closure's Finalizer half gained a caller: %s" % callers)


if __name__ == "__main__":
    unittest.main()
