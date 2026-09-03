"""The three seams this architecture leaves open — spec 042 FR-015, AC-010.

A seam is declared here **only** when a real second implementation exists or a
named feature will supply one. This module holds no abstraction invented in
advance of a caller: the SPEC forbids hypothetical seams, and a registry of
aspirations is exactly that.

Each entry names what fills it, who owns filling it, and what this feature
deliberately did not do.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Seam:
    name: str
    interface: str
    filled_by_today: str
    owner: str
    not_done_here: str


CALLER = Seam(
    name="caller",
    interface="protocol.run(RunRequest) -> RunOutcome",
    filled_by_today="sdd_runner.__main__ — argv in, exit code out",
    owner="the autonomous-entry feature",
    not_done_here=("Nothing turns a free-form request into a RunRequest. There is no entry "
                   "point that decides which feature to run, and none is added here."),
)

BACKEND = Seam(
    name="backend",
    interface="backends.Backend.run(system_prompt, task_prompt, path_scope, timeout)",
    filled_by_today="stub — scripted and deterministic (spec 040 FR-016)",
    owner="the real-providers feature",
    not_done_here=("`claude` stays optional and lazily imported; `codex` stays gated behind "
                   "--allow-unverified-backend and DEBT-001/DEBT-002. Neither becomes usable "
                   "by anything spec 042 did."),
)

FINALIZER = Seam(
    name="finalizer",
    interface="everything after loop.CORE_COMPLETE",
    filled_by_today="nothing — the run stops at the freeze and hands off",
    owner="the Finalizer feature (spec 040 D034 §1, §6)",
    not_done_here=("No lifecycle skill is dispatched, no closure delta is computed, no "
                   "PR_DESCRIPTION.md is written. `closure.classify`, `closure.observe` and "
                   "`closure.unexpected` exist, are tested, and have no callers; they are the "
                   "Finalizer's pre-written half and spec 042 left them untouched (A-010)."),
)

SEAMS = (CALLER, BACKEND, FINALIZER)
