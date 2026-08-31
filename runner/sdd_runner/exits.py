"""Exit codes — spec 040 FR-013.

Distinct codes so a scheduler can branch on the code alone, without parsing
output.
"""

OK = 0
GATE_REFUSED = 10
HUMAN_ESCALATION = 11
CAP_ABORT = 12
BUDGET_EXHAUSTED = 13
BACKEND_PRECONDITION = 14
CONCURRENT_RUN = 15
STATE_UNRESUMABLE = 16
NOT_CONVERGED = 17
INTERNAL_ERROR = 70

NAMES = {
    OK: "ok",
    GATE_REFUSED: "gate-refused",
    HUMAN_ESCALATION: "human-escalation",
    CAP_ABORT: "cap-abort",
    BUDGET_EXHAUSTED: "budget-exhausted",
    BACKEND_PRECONDITION: "backend-precondition",
    CONCURRENT_RUN: "concurrent-run",
    STATE_UNRESUMABLE: "state-unresumable",
    NOT_CONVERGED: "not-converged",
    INTERNAL_ERROR: "internal-error",
}
