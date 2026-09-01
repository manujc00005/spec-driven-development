"""Claude Agent SDK backend — spec 040 FR-008.

The SDK is imported LAZILY and is an optional dependency (FR-014, D001): a
machine without it must keep using this framework exactly as before, and the
whole test suite must pass there. Importing this module is therefore safe; only
`preflight()` requires the package.

System prompts come from `agents/*.md` at run time and are never paraphrased
here (FR-009): those files stay the single source of truth for agent behaviour.
"""

import os

from . import Backend, BackendPrecondition, Response
from ..retry import TransportError

# Failures that mean "this code is wrong", never "the provider blipped".
PROGRAMMING_ERRORS = (TypeError, AttributeError, NameError, ImportError, KeyError, IndexError)

INSTALL_HINT = (
    "the Claude Agent SDK is not installed. Install the runner's optional "
    "dependency:  python3 -m pip install 'sdd-runner[claude]'  (from runner/), "
    "or  python3 -m pip install claude-agent-sdk"
)


class ClaudeBackend(Backend):
    name = "claude"

    # Declared rather than inherited (AUDIT-8): a delegated session gets the tools
    # the SDD roles actually need and nothing else. `acceptEdits` without a tool
    # list is an unattended session with whatever the host happens to expose.
    DEFAULT_TOOLS = ("Read", "Grep", "Glob", "Edit", "Write", "Bash")
    READ_ONLY_TOOLS = ("Read", "Grep", "Glob")

    def __init__(self, model=None, permission_mode="acceptEdits", cwd=None,
                 allowed_tools=None):
        self.model = model
        self.permission_mode = permission_mode
        self.allowed_tools = list(allowed_tools if allowed_tools is not None
                                  else self.DEFAULT_TOOLS)
        self.cwd = cwd
        self._sdk = None

    def preflight(self):
        try:
            import anyio  # noqa: F401  - used directly by _query, not only by the SDK
            import claude_agent_sdk  # noqa: F401
        except ImportError as exc:
            raise BackendPrecondition("%s (import failed: %s)" % (INSTALL_HINT, exc))
        self._sdk = claude_agent_sdk
        if not (os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("CLAUDE_CODE_OAUTH_TOKEN")):
            raise BackendPrecondition(
                "no provider credential in the environment: set ANTHROPIC_API_KEY or "
                "CLAUDE_CODE_OAUTH_TOKEN. Credentials are read from the environment only — "
                "never from a config file in the repo and never from a CLI argument.")

    def run(self, system_prompt, task_prompt, path_scope, timeout):
        if self._sdk is None:
            raise BackendPrecondition("preflight() was not called")
        try:
            text = self._query(system_prompt, task_prompt, timeout)
        except BackendPrecondition:
            raise
        except PROGRAMMING_ERRORS:
            # A TypeError here is a bug in this file, not a flaky network. Wrapping
            # it as TransportError would retry it three times and then report a
            # transport failure, hiding the defect behind the retry policy (PY-2).
            raise
        except Exception as exc:                      # transport-shaped failure
            raise TransportError("Agent SDK call failed: %s" % exc)
        return Response(text=text, backend=self.name,
                        meta={"model": self.model, "permission_mode": self.permission_mode})

    def _options(self, system_prompt):
        """The session's configuration, isolated so it is testable without anyio."""
        return self._sdk.ClaudeAgentOptions(
            system_prompt=system_prompt,
            permission_mode=self.permission_mode,
            cwd=self.cwd,
            model=self.model,
            allowed_tools=self.allowed_tools,
        )

    def _query(self, system_prompt, task_prompt, timeout):
        """Isolated so tests can substitute it without the SDK installed."""
        import anyio

        sdk = self._sdk
        options = self._options(system_prompt)

        async def _run():
            # The deadline must be INSIDE the event loop (AUDIT-8). The previous
            # form wrapped `anyio.run` in `move_on_after`, which is an async cancel
            # scope: outside a loop it cancels nothing, so the timeout never fired
            # and a hung session hung the whole runner.
            with anyio.fail_after(timeout):
                chunks = []
                async for message in sdk.query(prompt=task_prompt, options=options):
                    content = getattr(message, "content", None)
                    if content is None:
                        continue
                    for block in content:
                        text = getattr(block, "text", None)
                        if text:
                            chunks.append(text)
                return "\n".join(chunks)

        try:
            return anyio.run(_run)
        except TimeoutError:
            raise TransportError("Agent SDK call timed out after %ss" % timeout)
