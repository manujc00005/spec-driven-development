"""Verdict and completion block parsing — spec 031 FR-003/FR-004, spec 040 FR-003.

Control flow keys ONLY on the fenced block. Prose above it is retained for the
human and never interpreted (precedent: commit 36c3b04, where control flow keyed
on rendered message text and broke).

Fail-closed is the whole point of this module:

  * a reviewer response that cannot be parsed becomes a synthetic REJECT
  * a worker response that cannot be parsed becomes BLOCKED

There is no code path from an invalid response to APPROVE.
"""

import re
from dataclasses import dataclass, field

from ._miniyaml import MiniYamlError, parse
from .policy import FINDING_KEYS, SEVERITIES  # noqa: F401 - re-exported (spec 042 AC-001)

_FENCE = re.compile(r"^[ \t]*```[ \t]*(?P<lang>[A-Za-z0-9_-]*)[ \t]*$")

# `path:line`, `path:line,line`, `path:line-line`. A path plus at least one line.
# One finding may legitimately span several locations (SKILL.md "Malformed or
# missing blocks"): rejecting a well-formed multi-location finding would burn a
# retry on a correct review.
_LOCATOR = re.compile(r"^(?P<path>[^\s:][^:]*):(?P<lines>\d+([,-]\d+)*)$")


@dataclass
class ReviewerVerdict:
    verdict: str                     # APPROVE | REJECT
    findings: list = field(default_factory=list)
    malformed: bool = False
    synthetic: bool = False
    errors: list = field(default_factory=list)
    raw: str = ""

    @property
    def approved(self) -> bool:
        return self.verdict == "APPROVE"


@dataclass
class WorkerCompletion:
    status: str                      # DONE | BLOCKED
    decisions: list = field(default_factory=list)
    malformed: bool = False
    errors: list = field(default_factory=list)
    raw: str = ""

    @property
    def done(self) -> bool:
        return self.status == "DONE"


def _candidate_blocks(text: str, key: str):
    """Return every fenced block whose body declares `key` at column 0.

    Returns (blocks, trailing_after_last) where trailing_after_last is the text
    following the final candidate's closing fence.
    """
    lines = text.splitlines()
    blocks = []
    i = 0
    end_line = None
    while i < len(lines):
        m = _FENCE.match(lines[i])
        if not m:
            i += 1
            continue
        start = i + 1
        j = start
        while j < len(lines) and not _FENCE.match(lines[j]):
            j += 1
        if j >= len(lines):
            break  # unterminated fence: not a candidate, and nothing after it is
        body = "\n".join(lines[start:j])
        if re.search(r"^%s[ \t]*:" % re.escape(key), body, re.MULTILINE):
            blocks.append((body, m.group("lang")))
            end_line = j
        i = j + 1
    trailing = ""
    if end_line is not None:
        trailing = "\n".join(lines[end_line + 1 :]).strip()
    return blocks, trailing


def _extract(text: str, key: str):
    """Locate the single terminal candidate block, or explain why there isn't one."""
    blocks, trailing = _candidate_blocks(text or "", key)
    if not blocks:
        return None, ["no fenced block declaring %r was found" % key]
    if len(blocks) > 1:
        return None, [
            "found %d competing blocks declaring %r; the report must end with exactly one"
            % (len(blocks), key)
        ]
    body, lang = blocks[0]
    errors = []
    if lang != "yaml":
        errors.append("block is fenced as %r, expected 'yaml'" % (lang or ""))
    if trailing:
        errors.append("the block must be the last element of the report; %d characters follow it"
                      % len(trailing))
    if errors:
        return None, errors
    return body, []


def _validate_locator(value) -> list:
    values = value if isinstance(value, list) else [value]
    errors = []
    for item in values:
        if not isinstance(item, str) or not _LOCATOR.match(item.strip()):
            errors.append("evidence %r is not a path:line locator" % (item,))
    return errors


def parse_reviewer(text: str, reviewer: str = "reviewer", iteration: int = 0) -> ReviewerVerdict:
    """Parse a reviewer report. Never returns APPROVE for an invalid response."""
    body, errors = _extract(text, "verdict")
    if body is None:
        return _synthetic(reviewer, iteration, errors, text)

    try:
        doc = parse(body)
    except MiniYamlError as exc:
        return _synthetic(reviewer, iteration, ["block is not valid YAML subset: %s" % exc], text)

    errs = []
    extra = set(doc) - {"verdict", "findings"}
    if extra:
        errs.append("unexpected keys: %s" % ", ".join(sorted(extra)))
    if "verdict" not in doc:
        errs.append("missing key 'verdict'")
    if "findings" not in doc:
        errs.append("missing key 'findings'")

    verdict = doc.get("verdict")
    if verdict not in ("APPROVE", "REJECT"):
        errs.append("verdict %r is not APPROVE or REJECT" % (verdict,))

    findings = doc.get("findings", [])
    if not isinstance(findings, list):
        errs.append("findings must be a list")
        findings = []

    if verdict == "APPROVE" and findings:
        # "An approval carrying findings is malformed" - SKILL.md.
        errs.append("APPROVE must carry an empty findings list")
    if verdict == "REJECT" and not findings:
        errs.append("REJECT must carry at least one finding")

    normalized = []
    for idx, item in enumerate(findings, 1):
        if not isinstance(item, dict):
            errs.append("finding %d is not a mapping" % idx)
            continue
        missing = FINDING_KEYS - set(item)
        unexpected = set(item) - FINDING_KEYS
        if missing:
            errs.append("finding %d missing: %s" % (idx, ", ".join(sorted(missing))))
        if unexpected:
            errs.append("finding %d unexpected: %s" % (idx, ", ".join(sorted(unexpected))))
        if item.get("severity") not in SEVERITIES:
            errs.append("finding %d severity %r is not one of %s"
                        % (idx, item.get("severity"), "/".join(SEVERITIES)))
        if not str(item.get("id", "")).strip():
            errs.append("finding %d has an empty id" % idx)
        if "evidence" in item:
            errs.extend("finding %d: %s" % (idx, e) for e in _validate_locator(item["evidence"]))
        if not missing and not unexpected:
            normalized.append(item)

    if errs:
        return _synthetic(reviewer, iteration, errs, text)

    return ReviewerVerdict(verdict=verdict, findings=normalized, raw=text or "")


def _synthetic(reviewer: str, iteration: int, errors: list, raw: str) -> ReviewerVerdict:
    """The fail-closed reviewer result of SKILL.md "Malformed or missing blocks".

    A synthetic REJECT closes no finding, so it always increments that reviewer's
    no-progress counter and cannot bypass the convergence caps.
    """
    return ReviewerVerdict(
        verdict="REJECT",
        findings=[{
            "id": "ORCH-MALFORMED-%s-%s" % (reviewer, iteration),
            "severity": "High",
            "evidence": "agent-output:verdict-block",
            "summary": "Reviewer returned an invalid autonomous verdict",
            "required_action": "Return a block conforming to the canonical sdd-orchestrate schema",
        }],
        malformed=True,
        synthetic=True,
        errors=errors,
        raw=raw or "",
    )


def parse_worker(text: str) -> WorkerCompletion:
    """Parse a worker report. Never returns DONE for an invalid response."""
    body, errors = _extract(text, "status")
    if body is None:
        return _blocked(errors, text)

    try:
        doc = parse(body)
    except MiniYamlError as exc:
        return _blocked(["block is not valid YAML subset: %s" % exc], text)

    errs = []
    extra = set(doc) - {"status", "decisions"}
    if extra:
        errs.append("unexpected keys: %s" % ", ".join(sorted(extra)))
    if "status" not in doc:
        errs.append("missing key 'status'")
    if "decisions" not in doc:
        errs.append("missing key 'decisions'")

    status = doc.get("status")
    if status not in ("DONE", "BLOCKED"):
        errs.append("status %r is not DONE or BLOCKED" % (status,))

    decisions = doc.get("decisions", [])
    if not isinstance(decisions, list):
        errs.append("decisions must be a list")
        decisions = []
    if status == "DONE" and decisions:
        errs.append("DONE must carry an empty decisions list")
    if status == "BLOCKED" and not decisions:
        errs.append("BLOCKED must carry a non-empty decisions list")
    for idx, item in enumerate(decisions, 1):
        if not isinstance(item, str) or not item.strip():
            errs.append("decision %d is not a non-empty string" % idx)

    if errs:
        return _blocked(errs, text)

    return WorkerCompletion(status=status, decisions=decisions, raw=text or "")


def _blocked(errors: list, raw: str) -> WorkerCompletion:
    """Two invalid completion blocks become BLOCKED with the exact validation errors."""
    return WorkerCompletion(
        status="BLOCKED",
        decisions=["Worker returned an invalid completion block: %s" % "; ".join(errors)],
        malformed=True,
        errors=errors,
        raw=raw or "",
    )
