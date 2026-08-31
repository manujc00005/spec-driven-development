"""FR-008/FR-016/FR-017: preconditions fail at startup, and Codex stays shut."""

import unittest

from sdd_runner import exits
from sdd_runner.backends import BackendPrecondition, resolve
from sdd_runner.backends.codex import FLAGS_VERIFIED, CodexBackend
from sdd_runner.backends.stub import StubBackend


class CodexGate(unittest.TestCase):
    def test_flags_are_still_unverified(self):
        """If this ever flips, DEBT-001/DEBT-002 must have closed with a real run."""
        self.assertFalse(FLAGS_VERIFIED)

    def test_refuses_by_default_before_touching_the_machine(self):
        with self.assertRaises(BackendPrecondition) as ctx:
            resolve("codex", model="some-model")
        message = str(ctx.exception)
        self.assertIn("gated", message)
        self.assertIn("DEBT-001", message)
        self.assertIn("DEBT-002", message)
        self.assertIn("Codex parity is not claimed", message)

    def test_the_gate_precedes_the_cli_check_so_an_installed_cli_cannot_unlock_it(self):
        backend = CodexBackend(model="m", executable="definitely-not-on-path")
        with self.assertRaises(BackendPrecondition) as ctx:
            backend.preflight()
        self.assertIn("gated", str(ctx.exception))

    def test_opt_in_still_requires_a_real_cli(self):
        backend = CodexBackend(model="m", executable="definitely-not-on-path",
                               allow_unverified=True)
        with self.assertRaises(BackendPrecondition) as ctx:
            backend.preflight()
        self.assertIn("not on PATH", str(ctx.exception))

    def test_argv_carries_the_isolation_flags_and_the_model_pin(self):
        argv = CodexBackend(model="pinned-model").argv("prompt")
        self.assertEqual(argv[:2], ["codex", "exec"])
        self.assertIn("--ignore-user-config", argv)
        self.assertIn("--ephemeral", argv)
        self.assertIn("--model", argv)
        self.assertIn("pinned-model", argv)

    def test_evidence_status_is_not_observed_until_a_real_run(self):
        self.assertEqual(CodexBackend(model="m").evidence_status(), "not observed")


class ClaudeBackendPreconditions(unittest.TestCase):
    def test_missing_sdk_names_the_install_hint(self):
        try:
            import claude_agent_sdk  # noqa: F401
        except ImportError:
            with self.assertRaises(BackendPrecondition) as ctx:
                resolve("claude")
            self.assertIn("pip install", str(ctx.exception))
        else:
            self.skipTest("the Agent SDK is installed on this machine")


class StubBackendContract(unittest.TestCase):
    def test_counts_invocations(self):
        stub = StubBackend(script=["one", "two"])
        stub.preflight()
        stub.run("sys", "a", [], 1)
        stub.run("sys", "b", [], 1)
        self.assertEqual(stub.invocations, 2)

    def test_exhausted_script_fails_loudly(self):
        stub = StubBackend(script=["one"])
        stub.run("sys", "a", [], 1)
        with self.assertRaises(BackendPrecondition):
            stub.run("sys", "b", [], 1)


class UnknownBackend(unittest.TestCase):
    def test_named_refusal(self):
        with self.assertRaises(BackendPrecondition):
            resolve("gpt-whatever")


class ExitCodes(unittest.TestCase):
    def test_codes_are_distinct(self):
        codes = [exits.OK, exits.GATE_REFUSED, exits.HUMAN_ESCALATION, exits.CAP_ABORT,
                 exits.BUDGET_EXHAUSTED, exits.BACKEND_PRECONDITION, exits.CONCURRENT_RUN,
                 exits.INTERNAL_ERROR]
        self.assertEqual(len(codes), len(set(codes)))
        self.assertEqual(exits.OK, 0)
        self.assertTrue(all(c != 0 for c in codes[1:]))


if __name__ == "__main__":
    unittest.main()
