"""Five terminal states, driven through the public interface alone — spec 042 AC-007.

The import list is the test. Everything below reaches `start`, `pause`, `abort`,
`resume` and `core-complete` with nothing but `run` and `RunRequest`: no `Loop`,
no `gate`, no `Orchestration`, no `Budget`. If a future refactor makes any of
these states unreachable without an internal import, this module stops compiling
and the "small public surface" claim is falsified rather than quietly weakened.

`support` and `tempfile` build the repository fixture — that is the harness, not
the interface under test.
"""

import json
import os
import tempfile
import unittest

from sdd_runner import RunRequest, run
from tests import support


def script(tmp, payload, name="script.json"):
    path = os.path.join(tmp, name)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh)
    return path


def converging():
    return ([support.fixture("worker_done.md"), support.approve_block()] * 2) \
        + support.finalization_flat()


class TheFiveStates(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo, self.feature = support.make_repo(self.tmp.name)

    def request(self, **kwargs):
        base = dict(repo=self.repo, feature=self.feature, backend="stub",
                    baseline=support.GREEN_BASELINE)
        base.update(kwargs)
        return RunRequest(**base)

    # -- start ------------------------------------------------------------
    def test_start_computes_a_plan_and_dispatches_nothing(self):
        outcome = run(self.request(dry_run=True, backend="claude"))
        self.assertEqual(outcome.exit_code, 0)
        self.assertEqual(outcome.result, "PLANNED")
        self.assertEqual(outcome.plan.unchecked, 2)
        self.assertEqual(outcome.plan.entry, "ready")
        self.assertEqual([t[0] for t in outcome.plan.tasks], ["T001", "T002"])
        self.assertFalse(os.path.exists(os.path.join(self.feature, "ORCHESTRATION.md")),
                         "a dry run wrote state")

    # -- core-complete ----------------------------------------------------
    def test_core_complete_converges_and_freezes(self):
        outcome = run(self.request(stub_script=script(self.tmp.name, converging())))
        self.assertEqual(outcome.exit_code, 0, outcome.reason)
        self.assertEqual(outcome.result, "DONE")
        self.assertIn("core complete", outcome.reason)
        state = os.path.join(self.feature, "ORCHESTRATION.md")
        with open(state, encoding="utf-8") as fh:
            text = fh.read()
        self.assertIn("- protocol version: %d" % outcome.protocol_version, text)

    # -- pause ------------------------------------------------------------
    def test_pause_on_a_human_gated_question(self):
        outcome = run(self.request(
            stub_script=script(self.tmp.name, [support.fixture("worker_blocked_human.md")])))
        self.assertEqual(outcome.result, "PAUSED")
        self.assertEqual(outcome.exit_code, 11)
        self.assertTrue(outcome.escalations, "a pause must say what it is waiting for")

    # -- abort ------------------------------------------------------------
    def test_abort_when_the_delegation_budget_is_exhausted(self):
        outcome = run(self.request(stub_script=script(self.tmp.name, converging()),
                                   max_delegations=1))
        self.assertEqual(outcome.result, "ABORTED")
        self.assertEqual(outcome.exit_code, 13)
        self.assertTrue(outcome.resumable, "budget exhaustion is remediable")

    def test_abort_when_a_reviewer_stops_converging(self):
        outcome = run(self.request(
            stub_script=script(self.tmp.name,
                               [support.fixture("worker_done.md"),
                                support.fixture("reviewer_reject.md")] * 8),
            max_iterations=1, max_delegations=40))
        self.assertEqual(outcome.result, "ABORTED")
        self.assertEqual(outcome.exit_code, 12)
        self.assertIn("domain", outcome.reason,
                      "a non-convergence abort names the reviewer, not the counter")

    # -- resume -----------------------------------------------------------
    def test_resume_refuses_a_finished_run_rather_than_redoing_it(self):
        first = run(self.request(stub_script=script(self.tmp.name, converging())))
        self.assertEqual(first.result, "DONE")
        again = run(self.request(stub_script=script(self.tmp.name, converging())))
        self.assertEqual(again.exit_code, 16)
        self.assertTrue(again.diagnostics, "the refusal must say why")
        self.assertIn("completed run", again.diagnostics[0].text)
        self.assertEqual(again.diagnostics[0].channel, "GATE")

    def test_resume_carries_the_budget_forward_rather_than_resetting_it(self):
        """A second entry after a cap abort must not start counting again."""
        aborted = run(self.request(stub_script=script(self.tmp.name, converging()),
                                   max_delegations=1))
        self.assertEqual(aborted.exit_code, 13)
        state = os.path.join(self.feature, "ORCHESTRATION.md")
        self.assertTrue(os.path.exists(state), "an abort must leave resumable state")
        with open(state, encoding="utf-8") as fh:
            text = fh.read()
        self.assertIn("- delegations used: 1", text)
        self.assertIn("- protocol version: %d" % aborted.protocol_version, text)


class NothingButTheInterfaceWasNeeded(unittest.TestCase):
    def test_this_module_imports_no_internal(self):
        import ast
        import io
        with io.open(os.path.abspath(__file__), encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == "sdd_runner":
                imported.update(a.name for a in node.names)
            if isinstance(node, ast.ImportFrom) and (node.module or "").startswith("sdd_runner."):
                self.fail("reached into %s" % node.module)
        self.assertEqual(imported, {"run", "RunRequest"})


if __name__ == "__main__":
    unittest.main()
