"""Escalation classifier — spec 031 FR-005, spec 040 FR-006.

Auto-resolvable ONLY when every statement is true: purely technical; reversible;
inside the approved SPEC; and not in a human-gated domain.

Any one human-gated trigger wins. An unclassifiable question is human-gated:
the classifier never guesses in the permissive direction.
"""

import re
from dataclasses import dataclass
from .policy import HUMAN_GATED  # noqa: F401 - re-exported (spec 042 AC-001)

_COMPILED = [(name, re.compile(pattern, re.IGNORECASE)) for name, pattern in HUMAN_GATED]


@dataclass
class Classification:
    gated: bool                 # True => human-gated, the run pauses
    trigger: str                # which rule fired, or "auto-resolvable"
    question: str               # verbatim
    reason: str

    @property
    def auto_resolvable(self) -> bool:
        return not self.gated


def classify(question: str) -> Classification:
    """Classify one exact question from a worker BLOCKED block, independently."""
    text = (question or "").strip()
    if not text:
        return Classification(
            gated=True,
            trigger="unclassifiable",
            question=question or "",
            reason="empty question: cannot prove it is technical, reversible and in-scope",
        )
    for name, pattern in _COMPILED:
        match = pattern.search(text)
        if match:
            return Classification(
                gated=True,
                trigger=name,
                question=text,
                reason="matched human-gated domain %r on %r" % (name, match.group(0)),
            )
    return Classification(
        gated=False,
        trigger="auto-resolvable",
        question=text,
        reason="no human-gated domain matched; route to deep-reasoner and record in DECISIONS.md",
    )


def classify_all(questions):
    """Each question is classified independently; any gated one gates the whole block."""
    return [classify(q) for q in (questions or [])]
