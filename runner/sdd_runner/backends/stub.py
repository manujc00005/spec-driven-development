"""Deterministic scripted backend — spec 040 FR-016.

This is a FIRST-CLASS implementation, not test scaffolding. Every loop guarantee
— caps, budget, resume, fail-closed parsing — is provable through it without a
single provider call, which is what makes the suite deterministic and free.

Note the boundary this backend does NOT cross, recorded honestly: spec 032's
PLAN rejects scripted reviewers as evidence about the LOOP's real behaviour,
because a mock cannot produce the malformed-block and format-retry paths a real
provider produces spontaneously. The stub proves what the RUNNER does with a
given response. It does not prove what a provider will send.
"""

from . import Backend, BackendPrecondition, Response


class StubBackend(Backend):
    name = "stub"

    def __init__(self, script=None, strict=True):
        # script: list of responses, or dict keyed by agent name -> list
        self.script = script if script is not None else []
        self.strict = strict
        self.calls = []          # every (agent, prompt) it was asked for
        self._cursor = 0

    def preflight(self):
        if self.strict and not self.script:
            raise BackendPrecondition(
                "stub backend has no scripted responses; supply `script=` before running")

    def run(self, system_prompt, task_prompt, path_scope, timeout):
        agent = (system_prompt or "").strip().splitlines()[0][:80] if system_prompt else ""
        self.calls.append({"agent": agent, "prompt": task_prompt, "scope": list(path_scope or [])})
        if isinstance(self.script, dict):
            queue = self.script.get(agent)
            if queue is None:
                for key, value in self.script.items():
                    if key and key in (system_prompt or ""):
                        queue = value
                        break
            if not queue:
                raise BackendPrecondition("stub has no scripted response for agent %r" % agent)
            text = queue.pop(0)
        else:
            if self._cursor >= len(self.script):
                raise BackendPrecondition(
                    "stub script exhausted after %d responses" % len(self.script))
            text = self.script[self._cursor]
            self._cursor += 1
        return Response(text=text, backend=self.name, meta={"call": len(self.calls)})

    @property
    def invocations(self):
        """How many times a provider call WOULD have been made. Asserted by AC-006."""
        return len(self.calls)
