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


class ClaudeBackendErrorClassification(unittest.TestCase):
    """PY-2: a bug in this file must not be laundered into a transport blip.

    `run()` used to wrap every exception as `TransportError`, so a `TypeError`
    would be retried three times under the backoff policy and then reported as a
    provider failure — the real defect invisible behind the retry. That fix was
    claimed last turn and never tested; this is the evidence.
    """

    def _backend(self, raiser):
        from sdd_runner.backends.claude import ClaudeBackend
        backend = ClaudeBackend(model="m")
        backend._sdk = object()          # preflight already passed, by construction
        backend._query = lambda *a, **k: raiser()
        return backend

    def test_a_programming_error_propagates_unchanged(self):
        for error in (TypeError, AttributeError, NameError, KeyError, IndexError):
            with self.subTest(error=error.__name__):
                backend = self._backend(lambda e=error: (_ for _ in ()).throw(e("boom")))
                with self.assertRaises(error):
                    backend.run("sys", "task", [], 1)

    def test_an_unexpected_runtime_error_is_still_treated_as_transport(self):
        from sdd_runner.retry import TransportError

        backend = self._backend(lambda: (_ for _ in ()).throw(ConnectionResetError("dropped")))
        with self.assertRaises(TransportError):
            backend.run("sys", "task", [], 1)

    def test_a_precondition_is_never_reclassified(self):
        backend = self._backend(
            lambda: (_ for _ in ()).throw(BackendPrecondition("no credential")))
        with self.assertRaises(BackendPrecondition):
            backend.run("sys", "task", [], 1)

    def test_run_without_preflight_refuses(self):
        from sdd_runner.backends.claude import ClaudeBackend

        with self.assertRaises(BackendPrecondition):
            ClaudeBackend(model="m").run("sys", "task", [], 1)


class ClaudeSessionBoundary(unittest.TestCase):
    """AUDIT-8: the session's tools are declared, and its deadline is real."""

    def test_the_tool_list_is_declared_not_inherited(self):
        from sdd_runner.backends.claude import ClaudeBackend

        backend = ClaudeBackend(model="m")
        self.assertEqual(backend.allowed_tools, list(ClaudeBackend.DEFAULT_TOOLS))
        self.assertNotIn("WebFetch", backend.allowed_tools)
        self.assertNotIn("Agent", backend.allowed_tools)

    def test_a_read_only_role_can_be_given_a_read_only_session(self):
        from sdd_runner.backends.claude import ClaudeBackend

        backend = ClaudeBackend(model="m", allowed_tools=ClaudeBackend.READ_ONLY_TOOLS)
        for writing in ("Edit", "Write", "Bash"):
            self.assertNotIn(writing, backend.allowed_tools)

    def test_the_options_carry_the_tool_list(self):
        """The list must reach ClaudeAgentOptions, not just sit on the object."""
        import types

        from sdd_runner.backends.claude import ClaudeBackend

        captured = {}
        backend = ClaudeBackend(model="m")
        backend._sdk = types.SimpleNamespace(ClaudeAgentOptions=lambda **kw: captured.update(kw))
        backend._options("system prompt")

        self.assertEqual(captured["allowed_tools"], list(ClaudeBackend.DEFAULT_TOOLS))
        self.assertEqual(captured["permission_mode"], "acceptEdits")
        self.assertEqual(captured["model"], "m")

    def test_a_read_only_session_reaches_the_options_too(self):
        import types

        from sdd_runner.backends.claude import ClaudeBackend

        captured = {}
        backend = ClaudeBackend(model="m", allowed_tools=ClaudeBackend.READ_ONLY_TOOLS)
        backend._sdk = types.SimpleNamespace(ClaudeAgentOptions=lambda **kw: captured.update(kw))
        backend._options("system prompt")
        self.assertNotIn("Write", captured["allowed_tools"])

    def test_the_deadline_is_inside_the_event_loop(self):
        """A cancel scope outside a loop cancels nothing; this one must fire."""
        import inspect

        from sdd_runner.backends import claude

        source = inspect.getsource(claude.ClaudeBackend._query)
        self.assertIn("fail_after", source)
        self.assertNotIn("anyio.move_on_after", source,
                         "move_on_after around a synchronous anyio.run never fires")
        # The deadline must be established inside the coroutine, not around it.
        self.assertLess(source.index("async def _run"), source.index("fail_after"))


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


class DryRunNeedsNoBackend(unittest.TestCase):
    """FR-001: --dry-run "performs the entry gate, parses TASKS.md, prints the plan
    and the computed budget, and dispatches nothing".

    It resolved the backend first, so on a machine with no Agent SDK — the very
    machine AC-010 says must work — the flag exited 14 without ever reaching the
    plan it exists to print.
    """

    def test_dry_run_reaches_the_plan_without_a_usable_backend(self):
        import tempfile
        from sdd_runner.__main__ import main
        from tests.support import make_repo

        with tempfile.TemporaryDirectory() as tmp:
            repo, _feature_dir = make_repo(tmp)
            code = main(["--repo", repo, "--feature", "specs/features/900-fixture",
                         "--backend", "claude", "--dry-run"])
        self.assertEqual(code, exits.OK)

    def test_a_real_run_still_refuses_an_unusable_backend(self):
        import tempfile
        from sdd_runner.__main__ import main
        from tests.support import make_repo

        try:
            import claude_agent_sdk  # noqa: F401
        except ImportError:
            pass
        else:
            self.skipTest("the Agent SDK is installed on this machine")

        with tempfile.TemporaryDirectory() as tmp:
            repo, _feature_dir = make_repo(tmp)
            code = main(["--repo", repo, "--feature", "specs/features/900-fixture",
                         "--backend", "claude"])
        self.assertEqual(code, exits.BACKEND_PRECONDITION)


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
