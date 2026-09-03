"""Exit codes — spec 040 FR-013.

Distinct codes so a scheduler can branch on the code alone, without parsing
output.

The values themselves moved to `policy` with spec 042 (AC-001: one definition
per constant). This module stays as the spelling every caller and test already
uses; it defines nothing.
"""

from .policy import (BACKEND_PRECONDITION, BUDGET_EXHAUSTED, CAP_ABORT,  # noqa: F401
                     CLOSURE_NOT_PROVEN, CONCURRENT_RUN, GATE_REFUSED,
                     HUMAN_ESCALATION, INTERNAL_ERROR, NAMES, NOT_CONVERGED, OK,
                     STATE_UNRESUMABLE)
