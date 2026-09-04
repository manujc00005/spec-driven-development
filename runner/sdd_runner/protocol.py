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
import traceback
from dataclasses import dataclass, field, replace

from . import exits, gate as gate_mod, resume as resume_mod, state as state_mod
from . import tasks as tasks_mod
from .backends import BackendPrecondition, resolve
from .budget import default_cap
from .gate import Refusal
from . import log as log_mod
from .log import AuditUnavailable, RunLog, redact
from .loop import Loop
from .policy import FEATURES_ROOT, NAMES, PLANNED, PROTOCOL_VERSION, REFUSED  # noqa: F401



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
    loop_completed: bool = False
    """Did `Loop.run()` return normally, with a reportable terminal result?

    **Stated by the core, never inferred.** It is `True` only where `run()` has a
    value returned by `Loop.run()` in hand, and `False` everywhere else: preflight
    refusals, containment failures, `--dry-run`, and the internal-error path — an
    exception can be raised *after* the loop started, and the baseline CLI printed
    no terminal result and sent no `run-finished` for it, so "started" is the wrong
    question and is deliberately not the one asked here.

    It replaces an inference. `ran` used to mean "terminal result **and** no
    diagnostics", which held only while diagnostics accompanied refusals alone. The
    moment a *successful* outcome carried one — a converged run whose `run.jsonl`
    lost events — a `DONE`/exit-0 run stopped printing its result and stopped
    emitting `run-finished`, leaving a scheduler waiting on an event that never
    came. The repair for a silent audit loss had introduced a silent success loss.
    A caller needs one fact, so the core states that fact.
    """

    @property
    def exit_name(self):
        """The stable name of this exit code.

        On the outcome rather than left to the caller: the code-to-name map is
        protocol vocabulary, and a CLI that imports it from `policy` reaches past
        the public interface — which is what AC-011 forbids and what
        `test_interface` was quietly whitelisting (domain:DOM-005).
        """
        return NAMES.get(self.exit_code, self.exit_code)

    @property
    def awaiting_human(self):
        """True when the run stopped for a maintainer answer.

        The loop has already notified in that case, so a caller must not notify
        again. Exposed as protocol semantics instead of making the caller compare
        against an exit-code constant it should not be importing.
        """
        return self.exit_code == exits.HUMAN_ESCALATION

    @property
    def ran(self):
        """Compatibility spelling of `loop_completed`. Consults nothing else.

        Kept because it is in the published surface. It returns `loop_completed`
        and **must not** grow a second condition: every defect this property has
        had came from it deciding the answer instead of reporting it.
        """
        return self.loop_completed


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


def _refuse(exit_code, *diagnostics, resumable, result=REFUSED, gate=None):
    """Build a refusal.

    `resumable` is **keyword-only and required**: there is no safe default, so the
    interpreter enforces that rather than a docstring asking nicely. It had a
    default of `True`, and every pre-loop refusal silently took it — including
    `UnresumableState`, the one exception whose entire meaning is `resumable: no`,
    while the identical exception raised inside `Loop.run` reported `False` at the
    same exit code (security:SEC-002).

    The first repair passed it explicitly at the three sites that were wrong and
    left the default armed; the guard written to protect that was a tautology
    (security:SEC-005 / domain:DOM-018). A required parameter needs no guard.
    """
    return RunOutcome(exit_code, result, gate=gate or GateResult(),
                      diagnostics=tuple(diagnostics), resumable=resumable)


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
            "archive it and start a fresh run" % (state_path, exc))), resumable=False)
    try:
        resume_mod.inspect(doc, state_path, request.max_iterations, hostname)
    except resume_mod.ConcurrentRun as exc:
        # A live owner is a reason to come back later, not corrupt provenance.
        return _refuse(exits.CONCURRENT_RUN, Diagnostic("GATE", "refused: %s" % exc),
                       resumable=True)
    except resume_mod.UnresumableState as exc:
        return _refuse(exits.STATE_UNRESUMABLE, Diagnostic("GATE", (
            "refused: %s\n  remediation: %s" % (exc.reason, exc.remediation))),
                       resumable=False)
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
    # Backend-exclusive options are validated where the backend is resolved, which
    # a dry run never reaches. That is deliberate, not an oversight: a dry run
    # dispatches nothing, so it has no backend to contradict (SPEC "Desired
    # behavior"; spec 042 D011, Superseded). Validating them in a dry run too is
    # recorded as an out-of-scope follow-up.
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
        return _refuse(exits.GATE_REFUSED, refusal, resumable=True)

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

    try:
        refusals = gate_mod.check(repo, feature_dir, baseline_cmd=request.baseline,
                                  first_entry=first_entry, adopt=request.adopt)
    except (OSError, UnicodeDecodeError) as exc:
        # The gate reads `SPEC.md` on every entry and `TASKS.md` again under
        # `--adopt`, both before the handler added for security:SEC-006 — so
        # widening only that handler left the two reads that run *first* able to
        # escape as a traceback and exit 1. Wrapping the call covers every read
        # beneath it, present and future, which a per-read handler would not
        # (security:SEC-006, re-reported).
        return _refuse(exits.GATE_REFUSED, Diagnostic("GATE", (
            "refused: a file the entry gate reads could not be read: %s\n"
            "  remediation: inspect the feature folder; SPEC.md and TASKS.md must be "
            "readable UTF-8" % exc)), resumable=True)
    if refusals:
        return RunOutcome(exits.GATE_REFUSED, REFUSED, gate=GateResult(tuple(refusals)))

    try:
        with open(os.path.join(feature_dir, "TASKS.md"), encoding="utf-8") as fh:
            tasks_text = fh.read()
    except (OSError, UnicodeDecodeError) as exc:
        # This read sits between the gate and the loop, and used to be outside
        # every handler: an unreadable TASKS.md escaped as a traceback and process
        # exit 1, in a module whose own rule is that a scheduler branches on the
        # exit code alone (domain:DOM-016).
        #
        # `UnicodeDecodeError` is not an `OSError`, so the first repair still let a
        # non-UTF-8 TASKS.md escape (security:SEC-006) — reachable without an
        # attacker, because `Loop._set_task_checkbox` rewrites the file
        # non-atomically and an interrupted write can truncate it mid-codepoint.
        # The sibling handler eleven lines above catches the same set.
        return _refuse(exits.GATE_REFUSED, Diagnostic("GATE", (
            "refused: TASKS.md could not be read: %s\n  remediation: restore the task "
            "queue, or run /spec-plan <feature-path>" % exc)), resumable=True)
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
        return _refuse(exits.BACKEND_PRECONDITION, Diagnostic("BACKEND", str(exc)),
                       resumable=True)

    log = RunLog(os.path.join(feature_dir, "run.jsonl"), clock=time.time)
    loop = Loop(repo, feature_dir, backend, log,
                max_iterations=request.max_iterations,
                max_delegations=request.max_delegations,
                notify=request.notify, baseline_cmd=request.baseline,
                adopt=request.adopt)
    try:
        outcome = loop.run()
    except AuditUnavailable as exc:
        # Caught BEFORE the catch-all, and answered without touching the log that
        # just failed — writing there is what made this a traceback and exit 1 on
        # `main`: the first `emit` raised, and the second, inside the handler,
        # raised again.
        #
        # A run whose durable record is gone is not a converged run, whatever the
        # loop was about to report. A scheduler must be able to trust the exit
        # code, and stderr is not enough (spec 042 D015). So: INTERNAL_ERROR,
        # ABORTED, and not resumable until a maintainer has looked — the tree may
        # carry work no transcript accounts for.
        return _refuse(
            exits.INTERNAL_ERROR,
            Diagnostic("INTERNAL", redact(
                "audit transcript unavailable while recording %r: %s. The run stopped "
                "at that event, before any further delegation. Nothing after it was "
                "recorded, so this run is not convergent and is not resumable until "
                "the feature folder is inspected."
                % (exc.event, exc.failures[-1] if exc.failures else "unknown"),
                log_mod.secret_values())),
            result="ABORTED", resumable=False)
    except Exception as exc:                            # never a silent crash
        # `str(exc)` alone is empty for `raise ValueError()`, so the operator got
        # `[INTERNAL] ` and the log got `detail: ""` — no type, nowhere (DOM-016).
        # `run.jsonl` is additive-only by the SPEC, so the type and traceback cost
        # no existing byte.
        detail = "%s: %s" % (type(exc).__name__, exc) if str(exc) else type(exc).__name__
        try:
            log.emit("internal-error", detail=detail,
                     exception_type=type(exc).__name__, traceback=traceback.format_exc())
        except Exception:                               # noqa: BLE001 - see below
            # Redundant defence, and deliberately kept. `RunLog.emit` now implements
            # its own promise at the writer (T051), so this cannot fire for the
            # OSError it was written against — but this is the last-resort handler
            # of the whole process, and the one place where "something unforeseen
            # raised" must still become exit 70 rather than a traceback. The earlier
            # comment here said emit does not implement its promise; that stopped
            # being true and is corrected (domain:DOM-022).
            pass
        # The log redacts against the environment's secret values before writing;
        # stderr had no such filter, so a credential inside an exception message
        # was scrubbed in run.jsonl and printed in clear one line later.
        return _refuse(exits.INTERNAL_ERROR,
                       Diagnostic("INTERNAL", redact(detail, log_mod.secret_values())),
                       result="ABORTED", resumable=False)

    # Fail-closed defence, not a footnote on a success. `Loop._emit` raises on the
    # FIRST failed write, so reaching here with a non-empty list means a write failed
    # outside the wrapper — a bypass, or a path that does not go through it. Either
    # way the run cannot be reported as converged: it is the same condition as
    # `AuditUnavailable`, discovered late (spec 042 D015).
    #
    # This block used to attach a diagnostic to an otherwise successful outcome,
    # which is precisely the shape the maintainer refused: exit 0 and `run-finished`
    # for a run with no audit trail.
    if log.write_failures:
        return _refuse(
            exits.INTERNAL_ERROR,
            Diagnostic("INTERNAL", redact(
                "audit transcript incomplete: %d event(s) were lost and the loop did "
                "not stop at the first one. Treated as an audit failure, not as a "
                "successful run. First failure: %s"
                % (len(log.write_failures), log.write_failures[0]),
                log_mod.secret_values())),
            result="ABORTED", resumable=False)
    # The only place in the module that holds a value returned by `Loop.run()`,
    # and therefore the only place entitled to say so.
    return RunOutcome(outcome.code, outcome.result, reason=outcome.reason,
                      remediation=outcome.remediation, resumable=outcome.resumable,
                      escalations=tuple(outcome.escalations), loop_completed=True)
