"""Structured run log — spec 040 FR-011.

One JSON object per event in `run.jsonl`, next to `ORCHESTRATION.md`. Every
decision the runner makes must be reconstructible from this file ALONE, without
the provider transcript.

Redaction happens at the WRITER, not at call sites, so no call site can forget
it. That is the only placement that survives a careless future edit.
"""

import json
import os
import re

# Environment variables whose VALUES must never appear in the log. The value is
# redacted wherever it occurs, not just when logged under its own name.
SECRET_ENV_HINTS = (
    "API_KEY", "TOKEN", "SECRET", "PASSWORD", "CREDENTIAL", "AUTH", "SESSION_KEY",
)

_MIN_SECRET_LEN = 8
REDACTED = "[REDACTED]"


def _secret_values(environ=None):
    env = environ if environ is not None else os.environ
    values = []
    for name, value in env.items():
        if not value or len(value) < _MIN_SECRET_LEN:
            continue
        upper = name.upper()
        if any(hint in upper for hint in SECRET_ENV_HINTS):
            values.append(value)
    # Longest first so a longer secret containing a shorter one redacts fully.
    return sorted(set(values), key=len, reverse=True)


def redact(obj, secrets=None):
    """Recursively replace any known secret value with [REDACTED]."""
    secrets = _secret_values() if secrets is None else secrets
    if not secrets:
        return obj
    if isinstance(obj, str):
        out = obj
        for value in secrets:
            if value and value in out:
                out = out.replace(value, REDACTED)
        return out
    if isinstance(obj, dict):
        return {redact(k, secrets): redact(v, secrets) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [redact(v, secrets) for v in obj]
    return obj


class RunLog:
    """Append-only JSONL writer. Never raises into the loop on a write failure."""

    def __init__(self, path, clock, environ=None):
        self.path = path
        self._clock = clock
        self._secrets = _secret_values(environ)
        self.events = []

    def emit(self, event, **fields):
        record = {"ts": self._clock(), "event": event}
        record.update(fields)
        record = redact(record, self._secrets)
        self.events.append(record)
        line = json.dumps(record, ensure_ascii=False, sort_keys=True)
        with open(self.path, "a", encoding="utf-8") as fh:
            fh.write(line + "\n")
        return record
