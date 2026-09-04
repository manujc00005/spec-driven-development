"""sdd_runner — the canonical, executable authority for the SDD autonomous protocol.

The protocol was defined by spec 031 (`autonomous-orchestration-loop`) and
corrected by spec 032. Spec 042 made **this package** its executable definition:
`policy` holds the vocabulary once, `protocol` exposes the interface, and every
other module is internal.

    from sdd_runner import run, RunRequest
    outcome = run(RunRequest(repo=".", feature="specs/features/042-...",
                             backend="stub", dry_run=True))

**Where this package and `skills/sdd-orchestrate/SKILL.md` disagree, the SKILL is
wrong** — the inverse of spec 040 D007, and deliberately so (spec 042 D004). That
deference was correct while the prose was the only complete definition and the
code transcribed part of it. It stopped being correct once the contract tests
started checking nine prose surfaces against this core: the core is now the only
definition that cannot drift, and deferring to prose would mean deferring to the
unverifiable half. The skill keeps its prose and loses final say; a normative
value changed there without changing it here turns the suite red.

Semantic changes still go through `/spec-update` against 031. This is a change of
*authority*, not a licence to edit the protocol from inside the runner.

Everything in `__all__` is public and stable. Everything else is an
implementation detail — import it and a later refactor may break you.
"""

__version__ = "0.1.0"

__all__ = [
    "run",
    "RunRequest",
    "RunOutcome",
    "GateResult",
    "RunPlan",
    "Refusal",
    "Diagnostic",
    "PROTOCOL_VERSION",
    "Backend",
    "Response",
    "BackendPrecondition",
]

# Resolved lazily (PEP 562) so that `import sdd_runner` does not drag the loop in
# behind it, and so the internal modules can keep using `from . import x` without
# a circular import through this file.
_LAZY = {
    "run": ("protocol", "run"),
    "RunRequest": ("protocol", "RunRequest"),
    "RunOutcome": ("protocol", "RunOutcome"),
    "GateResult": ("protocol", "GateResult"),
    "RunPlan": ("protocol", "RunPlan"),
    "Refusal": ("protocol", "Refusal"),
    "Diagnostic": ("protocol", "Diagnostic"),
    "PROTOCOL_VERSION": ("policy", "PROTOCOL_VERSION"),
    "Backend": ("backends", "Backend"),
    "Response": ("backends", "Response"),
    "BackendPrecondition": ("backends", "BackendPrecondition"),
}


def __getattr__(name):
    if name in _LAZY:
        import importlib
        module, attribute = _LAZY[name]
        return getattr(importlib.import_module("." + module, __name__), attribute)
    raise AttributeError("module %r has no attribute %r" % (__name__, name))


def __dir__():
    return sorted(list(globals()) + __all__)
