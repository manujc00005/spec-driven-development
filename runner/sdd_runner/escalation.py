"""Escalation classifier — spec 031 FR-005, spec 040 FR-006.

Auto-resolvable ONLY when every statement is true: purely technical; reversible;
inside the approved SPEC; and not in a human-gated domain.

Any one human-gated trigger wins. An unclassifiable question is human-gated:
the classifier never guesses in the permissive direction.
"""

import re
from dataclasses import dataclass

HUMAN_GATED = [
    ("product-ux",
     r"\b(ux|user experience|product decision|wording|copy|which flow|what should the user)\b"),
    ("money",
     r"\b(pricing|price|billing|invoice|refund|payment|charge the customer|financial liability"
     r"|money|currency|tarifa|facturaci[oó]n)\b"),
    ("personal-data",
     r"\b(personal data|pii|gdpr|rgpd|lopdgdd|aepd|consent|retention|erasure|right to be forgotten"
     r"|datos personales)\b"),
    ("public-contract",
     r"\b(public api|published schema|external contract|breaking change|api version"
     r"|backward.?incompatib)\w*\b"),
    ("destructive",
     r"\b(delete|drop table|truncate|purge|apply the migration|production data|irreversible"
     r"|destructive)\b"),
    ("spec-contradiction",
     r"\b(contradicts the spec|conflicts with the spec|spec says otherwise|not in the spec"
     r"|outside the spec|spec-update)\b"),
]

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
