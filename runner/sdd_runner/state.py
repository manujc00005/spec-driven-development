"""ORCHESTRATION.md I/O — spec 031 FR-008/FR-011, spec 040 FR-005.

`ORCHESTRATION.md` is authoritative over conversation memory and is shared with
the phase-1 executor: a run started by this runner must be resumable by an
interactive `sdd-orchestrate` session and vice versa. That makes byte-fidelity a
correctness property, not a nicety, so this module is deliberately conservative:

  * it NEVER reformats a section it did not change;
  * it round-trips an unmodified document byte-identically;
  * sections it does not understand are carried through verbatim.

The schema (State, Attempts, Findings, Delegation log, Escalations, Cap changes,
Closure delta, Run result) belongs to spec 031. This module does not add or
rename sections.
"""

import os
import re
import tempfile

_HEADING = re.compile(r"^##[ \t]+(?P<title>.+?)[ \t]*$", re.MULTILINE)

RUN_RESULTS = ("ACTIVE", "PAUSED", "DONE", "ABORTED")


class Section:
    __slots__ = ("title", "body")

    def __init__(self, title, body):
        self.title = title
        self.body = body          # everything after the heading line, verbatim

    def render(self):
        return "## %s\n%s" % (self.title, self.body)


class Orchestration:
    """A parsed ORCHESTRATION.md that can be re-rendered without drift."""

    def __init__(self, preamble="", sections=None, path=None):
        self.preamble = preamble
        self.sections = sections or []
        self.path = path

    # -- parsing ----------------------------------------------------------
    @classmethod
    def loads(cls, text, path=None):
        matches = list(_HEADING.finditer(text))
        if not matches:
            return cls(preamble=text, sections=[], path=path)
        preamble = text[: matches[0].start()]
        sections = []
        for i, m in enumerate(matches):
            start = m.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            body = text[start:end]
            if body.startswith("\n"):
                body = body[1:]
            sections.append(Section(m.group("title"), body))
        return cls(preamble=preamble, sections=sections, path=path)

    @classmethod
    def load(cls, path):
        with open(path, "r", encoding="utf-8") as fh:
            return cls.loads(fh.read(), path=path)

    # -- rendering --------------------------------------------------------
    def dumps(self):
        return self.preamble + "".join(s.render() for s in self.sections)

    def save(self, path=None):
        """Atomic write — 031 requires the state file to be written atomically."""
        target = path or self.path
        if not target:
            raise ValueError("no path to save to")
        directory = os.path.dirname(os.path.abspath(target)) or "."
        fd, tmp = tempfile.mkstemp(dir=directory, prefix=".orchestration-", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                fh.write(self.dumps())
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp, target)
        except BaseException:
            if os.path.exists(tmp):
                os.unlink(tmp)
            raise
        self.path = target
        return target

    # -- section access ---------------------------------------------------
    def get(self, title):
        for s in self.sections:
            if s.title.lower() == title.lower():
                return s
        return None

    def body(self, title, default=""):
        s = self.get(title)
        return s.body if s else default

    def set_body(self, title, body):
        s = self.get(title)
        if s is None:
            s = Section(title, body)
            self.sections.append(s)
        else:
            s.body = body
        return s

    def append_line(self, title, line):
        """Append one line to an append-only section (Attempts, Delegation log, Cap changes)."""
        s = self.get(title)
        if s is None:
            s = Section(title, "\n" + line + "\n\n")
            self.sections.append(s)
            return s
        body = s.body.rstrip("\n")
        s.body = body + "\n" + line + "\n\n"
        return s

    # -- the few fields the driver must read back -------------------------
    def run_result(self):
        body = self.body("Run result")
        for token in RUN_RESULTS:
            if re.search(r"\b%s\b" % token, body):
                return token
        return None

    def resumable(self):
        return bool(re.search(r"resumable:\s*yes", self.body("Run result"), re.IGNORECASE))

    def is_active(self):
        return self.run_result() == "ACTIVE"



# The runner recognizes its OWN documents by these exact table headers. A
# document written by the phase-1 executor uses different columns; resume must
# BLOCK on it rather than guess (spec 040 T013, "no inventes estado").
ATTEMPT_COLUMNS = ["Attempt", "Task", "Agent", "Objective", "Lifecycle",
                   "Allowed paths", "Pre", "Post", "Outcome", "Timestamp"]
FINDING_COLUMNS = ["Reviewer:finding", "Task", "Severity", "Required action", "Status",
                   "REJECTs", "Repair done", "First seen", "Last seen",
                   "Resolving verdict/fingerprint"]

LIFECYCLE = ("PLANNED", "DISPATCHED", "RESPONDED", "VERIFIED", "RECOVERED", "FAILED")


def parse_fields(body):
    """Parse a `- key: value` block into an ordered dict. Unknown lines are ignored."""
    fields = {}
    for line in body.splitlines():
        line = line.strip()
        if not line.startswith("- "):
            continue
        if ":" not in line:
            continue
        key, value = line[2:].split(":", 1)
        fields[key.strip()] = value.strip()
    return fields


def render_fields(fields):
    return "\n" + "".join("- %s: %s\n" % (k, v) for k, v in fields.items()) + "\n"


def parse_table(body):
    """Parse a markdown table into (headers, [dict, ...]).

    Returns ([], []) when the section holds no table at all. Raises ValueError on
    a table whose rows do not match its header - that is corruption, not absence.
    """
    lines = [l.strip() for l in body.splitlines() if l.strip().startswith("|")]
    if not lines:
        return [], []
    headers = [c.strip() for c in lines[0].strip("|").split("|")]
    rows = []
    for line in lines[1:]:
        cells = [c.strip() for c in line.strip("|").split("|")]
        if all(set(c) <= set("- ") for c in cells):
            continue                      # the |---|---| separator
        if len(cells) != len(headers):
            raise ValueError("table row has %d cells, header has %d: %r"
                             % (len(cells), len(headers), line))
        rows.append(dict(zip(headers, cells)))
    return headers, rows


def render_table(headers, rows):
    out = ["| " + " | ".join(headers) + " |",
           "|" + "|".join("---" for _ in headers) + "|"]
    for row in rows:
        out.append("| " + " | ".join(str(row.get(h, "")) for h in headers) + " |")
    return "\n" + "\n".join(out) + "\n\n"

def new_document(feature_path, mode, started_at, caps):
    """Create the initial state file. 031: create it only AFTER the entry gate passes."""
    doc = Orchestration(
        preamble="# Orchestration: %s\n\n"
                 "> Written by `sdd_runner` (spec 040), in the schema spec 031 defines.\n"
                 "> Mode: %s. Started: %s.\n\n" % (feature_path, mode, started_at),
        sections=[],
    )
    doc.set_body("State", render_fields({
        "writer": "sdd_runner",
        "phase": "INIT",
        "current task": "none",
        "current attempt": "none",
        "iteration": "0",
        "max-iterations": str(caps.get("max_iterations")),
        "max-delegations": str(caps.get("max_delegations")),
        "delegations used": "0",
        "completed tasks": "",
        "counters": "",
        "approvals": "",
        "runner pid": str(caps.get("pid", "")),
        "runner host": str(caps.get("host", "")),
    }))
    doc.set_body("Attempts", render_table(ATTEMPT_COLUMNS, []))
    doc.set_body("Findings", render_table(FINDING_COLUMNS, []))
    doc.set_body("Delegation log", "\n")
    doc.set_body("Escalations", "\n_None._\n\n")
    doc.set_body("Cap changes", "\n_None._\n\n")
    doc.set_body("Closure delta", "\n_Not frozen._\n\n")
    doc.set_body("Run result", "\nACTIVE\n\nresumable: yes\n\n")
    return doc
