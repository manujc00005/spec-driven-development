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

import json
import os

from . import Backend, BackendPrecondition, Response


def load_script(path):
    """Read a stub script from disk. Fails closed on anything but the two shapes.

    Accepted: a JSON list of response strings, consumed in order, or a JSON object
    mapping an agent name to its own list. Nothing else — a malformed script must
    stop the run before it dispatches, not halfway through it.
    """
    if not os.path.isfile(path):
        raise BackendPrecondition("stub script not found: %s" % path)
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except (ValueError, OSError) as exc:
        raise BackendPrecondition("stub script %s is not readable JSON: %s" % (path, exc))

    def _strings(values, where):
        if not isinstance(values, list) or not values:
            raise BackendPrecondition(
                "stub script %s: %s must be a non-empty list of responses" % (path, where))
        for item in values:
            if not isinstance(item, str):
                raise BackendPrecondition(
                    "stub script %s: %s contains a %s, expected a response string"
                    % (path, where, type(item).__name__))
        return list(values)

    if isinstance(data, list):
        return _strings(data, "the script")
    if isinstance(data, dict):
        if not data:
            raise BackendPrecondition("stub script %s is an empty object" % path)
        return {str(k): _strings(v, "key %r" % k) for k, v in data.items()}
    raise BackendPrecondition(
        "stub script %s must be a JSON list or object, got %s" % (path, type(data).__name__))


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
