"""One identity, one repair task — resolved from the record, not from prose.

Spec 042 `maintainer:MNT-004` / D016 / D017. `_schedule_repairs` promised in a
comment to reuse an existing repair task and could not find one: against this
feature's own `TASKS.md`, `task_for_finding` returned `None` for **every**
identity. Two independent causes, both invisible:

  * `_FROM_FINDING` was `\\(from ([^)]+)\\)` and the loop compared its capture to a
    bare `SEC-006`, while the tasks say `(from security:SEC-006)`;
  * `Task.repairs` searched the **title**, which is the task item's first line, so
    a title wrapped across lines carried no marker at all.

The fix is not a wider search. The registry's `task_ref` column is a structured
field and is the authority; the title suffix is human provenance and a legacy
fallback, parsed anchored.
"""

import io
import os
import unittest

from sdd_runner import tasks
from tests.support import REPO_ROOT

FEATURE = os.path.join(REPO_ROOT, "specs", "features", "042-canonical-autonomous-core")


def read(name):
    with io.open(os.path.join(FEATURE, name), encoding="utf-8") as fh:
        return fh.read()


class TheRegistryIsTheAuthority(unittest.TestCase):
    def setUp(self):
        self.tasks_text = read("TASKS.md")
        self.refs = tasks.registry_task_refs(read("FINDINGS.md"))

    def test_it_reads_every_identity_in_the_registry(self):
        self.assertGreaterEqual(len(self.refs), 30)
        for identity in ("security:SEC-001", "domain:DOM-001", "maintainer:MNT-001"):
            with self.subTest(identity=identity):
                self.assertIn(identity, self.refs)

    def test_every_identity_resolves_to_a_task_that_exists(self):
        unresolved = []
        for identity in self.refs:
            if tasks.task_for_finding(self.tasks_text, identity, registry=self.refs) is None:
                unresolved.append(identity)
        self.assertEqual(unresolved, [],
                         "the registry names tasks that are not in TASKS.md: %s" % unresolved)

    def test_a_registry_pointing_at_a_missing_task_raises(self):
        """`None` was the wrong signal — the caller reads it as "allocate one".

        The first version asserted `None` and called that fail-closed. It is not:
        `_schedule_repairs` treats `None` as *"this identity has no task yet"* and
        creates one, so a broken reference produced a **second** task for an
        identity that already owned one — the outcome the rule exists to prevent
        (`maintainer:MNT-005`). A typed exception is unambiguous; `None` is not.
        """
        with self.assertRaises(tasks.BrokenRepairTaskReference):
            tasks.task_for_finding(self.tasks_text, "security:SEC-001",
                                   registry={"security:SEC-001": "T999"})

    def test_two_identities_may_share_one_task_when_the_defect_is_the_same(self):
        first = tasks.task_for_finding(self.tasks_text, "security:SEC-001", registry=self.refs)
        second = tasks.task_for_finding(self.tasks_text, "domain:DOM-003", registry=self.refs)
        self.assertIsNotNone(first)
        self.assertEqual(first.id, second.id,
                         "SEC-001 and DOM-003 are the same defect and share T028")

    def test_one_identity_in_two_rows_raises(self):
        """`setdefault` kept the first and said nothing — DOM-025's defect, in its detector."""
        duplicated = ("| domain:DOM-098 | 1 | Low | T042 | open | R1 | first row |\n"
                      "| domain:DOM-098 | 2 | Low | T043 | open | R2 | second row |\n")
        with self.assertRaises(tasks.BrokenRepairTaskReference) as caught:
            tasks.registry_task_refs(duplicated)
        self.assertIn("DOM-098", str(caught.exception))

    def test_a_cell_naming_two_tasks_raises(self):
        """Taking `[0]` silently chose an owner. The column holds the canonical task."""
        with self.assertRaises(tasks.BrokenRepairTaskReference) as caught:
            tasks.registry_task_refs(
                "| domain:DOM-097 | 1 | Low | T031, T051 | open | R1 | two tasks |\n")
        self.assertIn("T051", str(caught.exception))

    def test_the_real_registry_holds_one_canonical_task_per_identity(self):
        """The deviations live in Required action and D016, not in the column."""
        self.assertEqual(self.refs["security:SEC-004"], "T031")
        self.assertEqual(self.refs["security:SEC-006"], "T047")
        registry = read("FINDINGS.md")
        for deviation in ("T051", "T052"):
            with self.subTest(task=deviation):
                self.assertIn(deviation, registry,
                              "a deviation was hidden rather than recorded")

    def test_a_narrative_mention_creates_no_association(self):
        """The registry reads two columns, not the whole row."""
        refs = tasks.registry_task_refs(
            "| domain:DOM-099 | 1 | Low | T042 | open | the tree the MNT-001 repair "
            "produced | see security:SEC-006 and T047 for context |\n")
        self.assertEqual(refs, {"domain:DOM-099": "T042"})


class TheTitleSuffixIsProvenanceAndAFallback(unittest.TestCase):
    def test_it_survives_a_title_wrapped_across_lines(self):
        text = ("## Phase 1\n\n"
                "- [ ] T010 - Do the thing that needs a very long description indeed\n"
                "  and therefore wraps (from security:SEC-042). Covers: AC-001.\n"
                "  Verify: the suite passes.\n")
        found = tasks.task_for_finding(text, "SEC-042")
        self.assertIsNotNone(found, "a wrapped title lost its allocation marker")
        self.assertEqual(found.id, "T010")

    def test_the_namespace_is_optional_on_both_sides(self):
        text = ("## Phase 1\n\n"
                "- [ ] T011 - A repair (from security:SEC-043). Covers: AC-001. "
                "Verify: the suite passes.\n")
        for spelling in ("SEC-043", "security:SEC-043"):
            with self.subTest(spelling=spelling):
                self.assertIsNotNone(tasks.task_for_finding(text, spelling))

    def test_two_identities_in_one_marker_are_both_allocated(self):
        text = ("## Phase 1\n\n"
                "- [ ] T012 - A shared repair (from security:SEC-044 and domain:DOM-044). "
                "Covers: AC-001. Verify: the suite passes.\n")
        for spelling in ("SEC-044", "DOM-044"):
            with self.subTest(spelling=spelling):
                found = tasks.task_for_finding(text, spelling)
                self.assertIsNotNone(found)
                self.assertEqual(found.id, "T012")

    def test_a_marker_inside_a_verify_clause_is_not_an_allocation(self):
        """The fallback reads the logical header only (`maintainer:MNT-007`)."""
        text = ("## Phase 1\n\n"
                "- [ ] T015 - An ordinary task. Covers: AC-001. Verify: the repair task\n"
                "  (from SEC-006) is reused rather than duplicated.\n")
        self.assertIsNone(tasks.task_for_finding(text, "SEC-006"))
        self.assertEqual(tasks.parse(text)[0].repairs_all, [])

    def test_an_incidental_prose_mention_is_not_an_allocation(self):
        text = ("## Phase 1\n\n"
                "- [ ] T013 - Something else entirely. Covers: AC-001. Verify: the suite\n"
                "  passes. This is the second half of domain:DOM-020, raised adjacent to\n"
                "  security:SEC-002, and mentions maintainer:MNT-001 in passing.\n")
        for spelling in ("DOM-020", "SEC-002", "MNT-001"):
            with self.subTest(spelling=spelling):
                self.assertIsNone(tasks.task_for_finding(text, spelling),
                                  "a mention became an allocation")

    def test_a_parenthetical_that_is_not_an_allocation_marker_is_ignored(self):
        text = ("## Phase 1\n\n"
                "- [ ] T014 - A task (from the maintainer's own reading). Covers: AC-001. "
                "Verify: the suite passes.\n")
        self.assertEqual(tasks.parse(text)[0].repairs_all, [])


class TheLoopWouldReuseRatherThanAllocate(unittest.TestCase):
    """The behaviour the broken lookup made unreachable."""

    def test_the_loop_passes_the_registry_to_the_resolver(self):
        import ast
        from sdd_runner import loop as loop_mod
        with io.open(loop_mod.__file__, encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        calls = [n for n in ast.walk(tree)
                 if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                 and n.func.attr == "task_for_finding"]
        self.assertTrue(calls, "the lookup moved; re-derive this guard")
        for call in calls:
            with self.subTest(line=call.lineno):
                self.assertIn("registry", {kw.arg for kw in call.keywords},
                              "the loop resolves from prose instead of the record")


if __name__ == "__main__":
    unittest.main()


class TheCallerRefusesRatherThanAllocating(unittest.TestCase):
    """`maintainer:MNT-005` — the behaviour, driven through `_schedule_repairs`.

    The resolver's return value was tested and the caller's reaction was not, so a
    broken reference resolved "correctly" to `None` and the loop then did the one
    thing the rule forbids.
    """

    def _loop(self, tmp):
        from sdd_runner import loop as loop_mod
        from sdd_runner.log import RunLog
        from tests import support
        repo, feature = support.make_repo(tmp)
        log = RunLog(os.path.join(feature, "run.jsonl"), clock=lambda: 0)
        loop = loop_mod.Loop(repo, feature, backend=None, log=log)
        loop.doc = None
        return loop, feature

    def test_a_broken_reference_creates_no_task_and_refuses(self):
        import tempfile
        from sdd_runner import loop as loop_mod
        from sdd_runner.counters import CounterState, FindingRow
        from sdd_runner.resume import UnresumableState
        from sdd_runner.tasks import Task

        with tempfile.TemporaryDirectory() as tmp:
            loop, feature = self._loop(tmp)
            tasks_path = os.path.join(feature, "TASKS.md")
            with io.open(tasks_path, encoding="utf-8") as fh:
                before = fh.read()

            loop.counters = CounterState(max_iterations=3)
            row = FindingRow(identity="domain:DOM-777", reviewer="domain",
                             finding_id="DOM-777", severity="High",
                             required_action="x", task_ref="T999")   # a task that is gone
            loop.counters.findings["domain:DOM-777"] = row

            task = Task(id="T001", title="anything", checked=False, deferred=False)
            with self.assertRaises(UnresumableState) as caught:
                loop._schedule_repairs(task, "domain", [{"id": "DOM-777",
                                                         "required_action": "x"}])

            with io.open(tasks_path, encoding="utf-8") as fh:
                after = fh.read()

        self.assertEqual(after, before, "TASKS.md was modified by a refused run")
        self.assertIn("disagree", caught.exception.reason)
        self.assertTrue(caught.exception.remediation)
        events = [e.get("event") for e in loop.log.events]
        self.assertNotIn("repair-task-created", events,
                         "a second task was allocated against a broken reference")
        self.assertIn("refused", events)
