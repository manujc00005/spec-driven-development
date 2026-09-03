"""The public interface — spec 042 FR-002…FR-007, AC-002, AC-003.

One function, five value types:

    run(RunRequest) -> RunOutcome

Everything the protocol decides happens behind that call: request validation and
feature-path containment, first-entry versus re-entry, resume authentication and
its ordering against the entry gate, the gate itself, budget computation, backend
resolution, the loop, freeze, and the terminal result.

Before spec 042 four of those decisions lived in `__main__.py` — an
argument-parsing module was deciding, among other things, what counts as a first
entry and how large the delegation budget is. A second caller had to re-derive
them or diverge. They live here now, and `__main__` renders.

**Nothing internal escapes.** `RunOutcome` and `GateResult` carry strings,
integers, booleans and frozen value types. No `Loop`, no `Orchestration`, no
`Backend`, no `CounterState`, no open file handle — asserted by
`tests/contract/test_interface.py`, because "small public surface" is a property
that decays silently.
"""

import os
import socket
import time
from dataclasses import dataclass, field, replace

from . import exits, gate as gate_mod, resume as resume_mod, state as state_mod
from . import tasks as tasks_mod
from .backends import BackendPrecondition, resolve
from .budget import default_cap
from .gate import Refusal
from .log import RunLog
from .loop import Loop
from .policy import FEATURES_ROOT, PROTOCOL_VERSION

# Terminal results a run can report, beyond the loop's own DONE/PAUSED/ABORTED.
REFUSED = "REFUSED"      # the gate said no; nothing was dispatched
PLANNED = "PLANNED"      # --dry-run: the plan was computed, nothing dispatched


@dataclass(frozen=True)
class Diagnostic:
    """A message that must reach the operator, with the stream it belongs on.

    The *structured* gate refusals live in `GateResult`. A `Diagnostic` is
    everything else the core needs to say — a backend precondition, an
    unreadable state file, a containment failure — whose exact wording is pinned
    by the golden transcripts of AC-008.

    Their text is not decomposed into condition/observed/remediation the way a
    `Refusal` is. Doing that would change the bytes the CLI prints, which is
    precisely what this feature promised not to do; it is recorded as D008 and
    belongs to whatever spec next changes the CLI's output on purpose.
    """
    channel: str                  # GATE | BACKEND | INTERNAL
    text: str

    def render(self):
        return "[%s] %s" % (self.channel, self.text)


@dataclass(frozen=True)
class GateResult:
    """Fail-closed by construction: no refusals is the only way to pass."""
    refusals: tuple = ()

    @property
    def passed(self):
        return not self.refusals

    def render(self):
        return tuple(r.render() for r in self.refusals)


@dataclass(frozen=True)
class RunPlan:
    """What a dry run computes. Data only — `__main__` decides how it looks."""
    feature_dir: str
    backend: str
    unchecked: int
    max_iterations: int
    max_delegations: int
    entry: str
    tasks: tuple = ()                     # ((task id, title), ...)
    adoption_baseline: str = ""
    adoption_diff_base: str = ""
    default_branch: str = ""
    inherited: tuple = ()                 # ((task id, verify clause), ...)


@dataclass(frozen=True)
class RunOutcome:
    exit_code: int
    result: str
    reason: str = ""
    remediation: str = ""
    resumable: bool = True
    escalations: tuple = ()
    gate: GateResult = field(default_factory=GateResult)
    plan: RunPlan = None
    diagnostics: tuple = ()
    protocol_version: int = PROTOCOL_VERSION


@dataclass(frozen=True)
class RunRequest:
    """Every input the protocol accepts, validated by the core rather than the caller."""
    repo: str = "."
    feature: str = ""
    backend: str = "claude"
    model: str = None
    max_iterations: int = 3
    max_delegations: int = None
    baseline: tuple = None                # argv of the PLAN-mandated verification
    notify: object = None                 # callable taking one JSON-able event
    allow_unverified_backend: bool = False
    stub_script: str = None
    adopt: bool = False
    dry_run: bool = False


def _refuse(exit_code, *diagnostics, result=REFUSED, gate=None):
    return RunOutcome(exit_code, result, gate=gate or GateResult(),
                      diagnostics=tuple(diagnostics))


def resolve_feature(repo, requested):
    """Resolve `--feature` and prove it lands inside `specs/features/`.

    Returns (feature_dir, Diagnostic|None). The check runs BEFORE any write — the
    core puts `ORCHESTRATION.md` and `run.jsonl` in this directory, claims it with
    an exclusive create, and fingerprints the repository around it.

    Every path is resolved through symlinks first (spec 040 AUDIT-5, AC-016). A
    prefix comparison on the requested path sees only the name: `specs/features/x`
    can be a symlink to anywhere, and `commonpath` on the unresolved path would
    call it contained. `os.path.commonpath` on the RESOLVED paths is what actually
    answers the question, and it is path-aware — `/repo/specs/features-old` is not
    inside `/repo/specs/features`, which a string prefix would get wrong.
    """
    features_root = os.path.realpath(os.path.join(repo, FEATURES_ROOT))
    if not os.path.isdir(features_root):
        return None, Diagnostic("GATE", (
            "refused: %s does not exist in this repository\n"
            "  remediation: run from a repository with an SDD spec trail, "
            "or pass --repo" % FEATURES_ROOT))

    candidate = requested if os.path.isabs(requested) else os.path.join(repo, requested)
    resolved = os.path.realpath(candidate)

    def refuse(detail):
        return Diagnostic("GATE", (
            "refused: --feature must resolve to a directory inside %s\n"
            "  requested: %s\n"
            "  resolves to: %s\n"
            "  detail: %s\n"
            "  remediation: pass a feature folder under %s, or set --repo to the "
            "repository that contains it" % (FEATURES_ROOT, requested, resolved,
                                             detail, FEATURES_ROOT)))

    if resolved == features_root:
        return None, refuse("that is the features root itself, not a feature")
    try:
        contained = os.path.commonpath([features_root, resolved]) == features_root
    except ValueError:                      # different drives on Windows
        contained = False
    if not contained:
        return None, refuse("it lands outside the spec trail")
    return resolved, None


def _authenticate_reentry(state_path, request, hostname):
    """Existence is not authentication (031).

    A dry run returns before `Loop` exists, so without this the core would report
    a pass for a document that could never be resumed (spec 041 T020 /
    CONF-041-02). Only for a genuine RE-ENTRY: `--adopt` over an existing document
    is a statement about intent, not about that document — "a run is resumed,
    never re-adopted" holds whether the file is valid, stale or foreign, so the
    gate's `already adopted or entered` owns it and authenticating first would
    bury that answer under a different condition (spec 041 T024 / R3-02).
    """
    try:
        doc = state_mod.Orchestration.load(state_path)
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        # A state file that cannot even be read is still a refusal with a code,
        # never a traceback: a scheduler branches on the exit code alone (T026).
        return _refuse(exits.STATE_UNRESUMABLE, Diagnostic("GATE", (
            "refused: %s cannot be read: %s\n  remediation: inspect the file, or "
            "archive it and start a fresh run" % (state_path, exc))))
    try:
        resume_mod.inspect(doc, state_path, request.max_iterations, hostname)
    except resume_mod.ConcurrentRun as exc:
        return _refuse(exits.CONCURRENT_RUN, Diagnostic("GATE", "refused: %s" % exc))
    except resume_mod.UnresumableState as exc:
        return _refuse(exits.STATE_UNRESUMABLE, Diagnostic("GATE", (
            "refused: %s\n  remediation: %s" % (exc.reason, exc.remediation))))
    return None


def _plan(repo, feature_dir, request, pending, cap):
    inherited = ()
    baseline = diff_base = branch = ""
    if request.adopt:
        record = gate_mod.inherited_record(repo, feature_dir)
        baseline, diff_base, branch = record.baseline, record.diff_base, record.default_branch
        inherited = tuple(record.checked)
    return RunPlan(
        feature_dir=feature_dir, backend=request.backend, unchecked=len(pending),
        max_iterations=request.max_iterations, max_delegations=cap,
        entry="adopt" if request.adopt else "ready",
        tasks=tuple((t.id, t.title) for t in pending),
        adoption_baseline=baseline, adoption_diff_base=diff_base,
        default_branch=branch, inherited=inherited)


def _backend(request, repo):
    if request.stub_script and request.backend != "stub":
        raise BackendPrecondition(
            "--stub-script applies to --backend stub, not %r" % (request.backend,))
    if request.backend == "stub":
        from .backends.stub import load_script
        kwargs = ({"script": load_script(request.stub_script)} if request.stub_script
                  else {"strict": False})
    else:
        kwargs = {"model": request.model, "cwd": repo}
    return resolve(request.backend, allow_unverified=request.allow_unverified_backend,
                   **kwargs)


def run(request):
    """Execute the protocol. The only entry point; everything else is internal."""
    repo = os.path.realpath(request.repo)
    feature_dir, refusal = resolve_feature(repo, request.feature)
    if refusal is not None:
        return _refuse(exits.GATE_REFUSED, refusal)

    hostname = socket.gethostname()

    # `gate.check` has always distinguished first entry from re-entry, and the CLI
    # never told it which this was — harmless while `In Progress` was a first-entry
    # status, fatal once spec 041 narrowed first entry to `Ready`: every adopted run
    # became a one-shot. The state file is what makes a run re-entrant, so it is what
    # answers the question (spec 041 T015 / CONF-041-01).
    state_path = os.path.join(feature_dir, "ORCHESTRATION.md")
    first_entry = not os.path.exists(state_path)
    if not first_entry and not request.adopt:
        blocked = _authenticate_reentry(state_path, request, hostname)
        if blocked is not None:
            return blocked

    refusals = gate_mod.check(repo, feature_dir, baseline_cmd=request.baseline,
                              first_entry=first_entry, adopt=request.adopt)
    if refusals:
        return RunOutcome(exits.GATE_REFUSED, REFUSED, gate=GateResult(tuple(refusals)))

    with open(os.path.join(feature_dir, "TASKS.md"), encoding="utf-8") as fh:
        tasks_text = fh.read()
    pending = tasks_mod.independently_runnable(tasks_text)
    cap = request.max_delegations or default_cap(len(pending))

    # A dry run dispatches nothing, so it must not require a dispatchable backend
    # (spec 040 FR-001). Resolving one first made the flag unusable on exactly the
    # machine AC-010 says must work: no Agent SDK, no Codex CLI.
    if request.dry_run:
        return RunOutcome(exits.OK, PLANNED,
                          plan=_plan(repo, feature_dir, request, pending, cap))

    try:
        backend = _backend(request, repo)
    except BackendPrecondition as exc:
        return _refuse(exits.BACKEND_PRECONDITION, Diagnostic("BACKEND", str(exc)))

    log = RunLog(os.path.join(feature_dir, "run.jsonl"), clock=time.time)
    loop = Loop(repo, feature_dir, backend, log,
                max_iterations=request.max_iterations,
                max_delegations=request.max_delegations,
                notify=request.notify, baseline_cmd=request.baseline,
                adopt=request.adopt)
    try:
        outcome = loop.run()
    except Exception as exc:                            # never a silent crash
        log.emit("internal-error", detail=str(exc))
        return _refuse(exits.INTERNAL_ERROR, Diagnostic("INTERNAL", str(exc)),
                       result="ABORTED")

    return RunOutcome(outcome.code, outcome.result, reason=outcome.reason,
                      remediation=outcome.remediation, resumable=outcome.resumable,
                      escalations=tuple(outcome.escalations))
