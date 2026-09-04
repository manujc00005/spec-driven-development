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

# Environment variables whose VALUES must never appear in an artifact. The value
# is redacted wherever it occurs, not just when logged under its own name.
#
# Deliberately broad (SEC-003): the original list required the NAME to contain
# API_KEY/TOKEN/SECRET/PASSWORD/CREDENTIAL/AUTH/SESSION_KEY, which misses
# OPENAI_KEY, DB_PASS, GH_PAT, PRIVATE_KEY and anything else people actually
# name their credentials. A false positive costs one over-redacted string in a
# maintainer's log; a false negative costs a credential in clear. Err the cheap
# way. `SAFE_NAMES` keeps the everyday variables whose names collide out of it.
SECRET_ENV_HINTS = (
    "KEY", "TOKEN", "SECRET", "PASS", "PWD", "CREDENTIAL", "AUTH", "PAT",
    "PRIVATE", "SIGNATURE", "SIGNING",
)

# Ordinary variables whose names collide with a hint but never hold a secret.
SAFE_NAMES = frozenset({"PWD", "OLDPWD", "KEYMAP", "PASSWD", "AUTHOR", "PATH"})

_MIN_SECRET_LEN = 8
REDACTED = "[REDACTED]"


def secret_values(environ=None):
    env = environ if environ is not None else os.environ
    values = []
    for name, value in env.items():
        if not value or len(value) < _MIN_SECRET_LEN:
            continue
        upper = name.upper()
        if upper in SAFE_NAMES:
            continue
        if any(hint in upper for hint in SECRET_ENV_HINTS):
            values.append(value)
    # Longest first so a longer secret containing a shorter one redacts fully.
    return sorted(set(values), key=len, reverse=True)


def redact(obj, secrets=None):
    """Recursively replace any known secret value with [REDACTED]."""
    secrets = secret_values() if secrets is None else secrets
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


class AuditUnavailable(RuntimeError):
    """The durable transcript could not be written — spec 042 D015.

    Raised by the loop's `_emit` wrapper, never by `RunLog` itself: the writer
    keeps its "never raises into the loop" promise so a lost line cannot turn a
    coded exit into a traceback, and the *loop* decides that a run without a
    durable record is not a run. The two responsibilities are separate on purpose.
    """

    def __init__(self, event, failures):
        self.event = event
        self.failures = list(failures)
        super().__init__("audit transcript unavailable while recording %r: %s"
                         % (event, self.failures[-1] if self.failures else "unknown"))


class RunLog:
    """Append-only JSONL writer. Never raises into the loop on a write failure.

    That sentence was a promise with no implementation: the write had no handler,
    so a full disk or a read-only feature directory raised straight into the
    caller. Four `log.emit` calls sit *inside* exception handlers, where a raise
    converts a correctly classified exit 15 or 16 into an unhandled exception —
    an exit 70 `resumable: no` reported for a concurrent run that was perfectly
    resumable (security:SEC-004). The promise is now kept here, once, instead of
    at whichever call site happened to remember.
    """

    def __init__(self, path, clock, environ=None):
        self.path = path
        self._clock = clock
        self._secrets = secret_values(environ)
        self.events = []
        self.write_failures = []       # lines the transcript lost, for the record

    def emit(self, event, **fields):
        record = {"ts": self._clock(), "event": event}
        record.update(fields)
        record = redact(record, self._secrets)
        self.events.append(record)
        line = json.dumps(record, ensure_ascii=False, sort_keys=True)
        try:
            with open(self.path, "a", encoding="utf-8") as fh:
                fh.write(line + "\n")
        except OSError as exc:
            # The writer RECORDS the failure; the loop decides what it means. That
            # split is deliberate (D015): swallowing here is what stops a lost line
            # turning a coded exit into a traceback, and `Loop._emit` is what turns
            # it into a fatal audit failure. An earlier comment here said losing a
            # line never changes what the run reports — true of the writer, and
            # false of the system, once D015 made an unrecordable run a refusal
            # (`maintainer:MNT-009`).
            self.write_failures.append("%s: %s" % (type(exc).__name__, exc))
        return record
