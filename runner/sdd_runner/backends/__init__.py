"""Backend interface and registry — spec 040 FR-008.

One operation: run a session given a system prompt, a task prompt, a path scope
and a timeout; return raw text plus transport metadata. Three implementations:

  stub    always present, scripted, deterministic (FR-016)
  claude  Claude Agent SDK, imported lazily
  codex   `codex exec` subprocess, GATED SHUT by default (FR-017)

A backend whose preconditions are unmet fails at STARTUP with a named cause,
never mid-run.
"""

from dataclasses import dataclass, field


class BackendPrecondition(RuntimeError):
    """Named, actionable reason a backend cannot be used. Raised before any dispatch."""


@dataclass
class Response:
    text: str
    backend: str
    meta: dict = field(default_factory=dict)


class Backend:
    """Interface. Implementations must not mutate anything outside `path_scope`."""

    name = "abstract"

    def preflight(self):
        """Raise BackendPrecondition if this backend cannot run. Called once, at startup."""
        raise NotImplementedError

    def run(self, system_prompt, task_prompt, path_scope, timeout):
        raise NotImplementedError


def resolve(name, allow_unverified=False, **kwargs):
    """Return a preflighted backend, or raise BackendPrecondition."""
    if name == "stub":
        from .stub import StubBackend
        backend = StubBackend(**kwargs)
    elif name == "claude":
        from .claude import ClaudeBackend
        backend = ClaudeBackend(**kwargs)
    elif name == "codex":
        from .codex import CodexBackend
        backend = CodexBackend(allow_unverified=allow_unverified, **kwargs)
    else:
        raise BackendPrecondition(
            "unknown backend %r; choose one of stub, claude, codex" % (name,))
    backend.preflight()
    return backend
