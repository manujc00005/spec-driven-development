"""Codex backend — spec 040 FR-017, D004. IMPLEMENTED BUT GATED.

Read this before changing anything here.

The implementation is real: it is a genuine second implementation of the Backend
interface, so the abstraction carries two loads rather than one plus a comment.
It is also SHUT by default and must stay shut until someone runs it against a
real Codex CLI.

Why: `DEBT-001` records that the isolation flag set enforced by
`scripts/skill-eval.sh` (`--ignore-user-config`, `--ephemeral`, `--model`) comes
from a reviewed external implementation that NOBODY HAS RUN. `DEBT-002` records
that the Codex adapter's prompt directory and config schema are likewise
unverified. The Codex CLI is not installed on the maintainer's machine.

Rules that must not be softened without closing those debts:

  1. No CLI installed  -> explicit, safe startup failure.
  2. Flags unverified  -> gated; requires --allow-unverified-backend.
  3. The suite proves Codex is never used accidentally.
  4. A real execution is reported as `observed`; anything else `not observed`.
  5. No documentation says "Codex supported" or "Codex parity".

Approved wording, per the maintainer:
  "Codex backend implementation is present but gated."
  "Codex execution requires local CLI verification."
  "Codex parity is not claimed."
"""

import shutil
import subprocess

from . import Backend, BackendPrecondition, Response
from ..retry import TransportError

# The flag set scripts/skill-eval.sh enforces. UNVERIFIED against a real CLI.
ISOLATION_FLAGS = ("--ignore-user-config", "--ephemeral")
PIN_FLAG = "--model"

FLAGS_VERIFIED = False          # flip only with a recorded real `codex exec` run

GATE_MESSAGE = (
    "Codex backend implementation is present but gated. Codex execution requires local CLI "
    "verification.\n"
    "  Reason: the isolation flag set (%s, %s) is enforced but has never been exercised against a "
    "real Codex CLI.\n"
    "  See docs/KNOWN_DEBT.md DEBT-001 (isolation flags enforced but unverified) and DEBT-002 "
    "(adapter advertised as prompt-based/unverified).\n"
    "  To proceed anyway on a machine that has the CLI, pass --allow-unverified-backend. The run "
    "is then stamped unverified and its result must be reported as observed only if a real "
    "`codex exec` actually executed.\n"
    "  Codex parity is not claimed."
) % (ISOLATION_FLAGS[0], ISOLATION_FLAGS[1])


class CodexBackend(Backend):
    name = "codex"

    def __init__(self, model=None, executable="codex", allow_unverified=False, cwd=None):
        self.model = model
        self.executable = executable
        self.allow_unverified = bool(allow_unverified)
        self.cwd = cwd
        self.executed = False       # True only after a real subprocess actually ran

    def preflight(self):
        # Rule 2 first: the gate is about the flag set, not about the machine, so
        # it refuses identically whether or not a CLI happens to be present. This
        # ordering is what stops an installed CLI from silently unlocking Codex.
        if not FLAGS_VERIFIED and not self.allow_unverified:
            raise BackendPrecondition(GATE_MESSAGE)
        # Rule 1.
        if shutil.which(self.executable) is None:
            raise BackendPrecondition(
                "the Codex CLI (%r) is not on PATH. Codex execution requires local CLI "
                "verification; install the CLI or choose --backend claude." % self.executable)
        if not self.model:
            raise BackendPrecondition(
                "Codex requires an explicit %s pin; an unpinned run records a claim about a "
                "model that may not have been used." % PIN_FLAG)

    def argv(self, task_prompt):
        """The exact command line. Exposed so tests can assert the flags without running it.

        KNOWN EXPOSURE (SEC-004, spec 040 D028): the prompt travels as a command-line
        argument, so it is readable by any process on the host via `ps` or `/proc`.
        The prompt carries the agent contract, repository content and reviewer-authored
        required actions. Passing it on stdin instead is the fix, and whether this CLI
        accepts stdin is precisely what DEBT-001 says nobody has checked - so the fix
        lands with that verification, not before it.
        """
        return [self.executable, "exec", *ISOLATION_FLAGS, PIN_FLAG, str(self.model), task_prompt]

    def run(self, system_prompt, task_prompt, path_scope, timeout):
        prompt = "%s\n\n---\n\n%s" % (system_prompt or "", task_prompt or "")
        argv = self.argv(prompt)
        try:
            proc = subprocess.run(argv, capture_output=True, text=True,
                                  timeout=timeout, cwd=self.cwd)
        except FileNotFoundError as exc:
            raise BackendPrecondition("Codex CLI disappeared between preflight and run: %s" % exc)
        except subprocess.TimeoutExpired as exc:
            raise TransportError("codex exec timed out after %ss" % timeout)
        if proc.returncode != 0:
            raise TransportError("codex exec exited %d: %s" % (proc.returncode, proc.stderr[-400:]))
        self.executed = True
        return Response(text=proc.stdout, backend=self.name,
                        meta={"model": self.model, "flags_verified": FLAGS_VERIFIED,
                              "isolation": list(ISOLATION_FLAGS)})

    def evidence_status(self):
        """Rule 4: `observed` only when a real `codex exec` actually executed."""
        return "observed" if self.executed else "not observed"
