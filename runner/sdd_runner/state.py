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

from .log import redact, secret_values
from .policy import (ATTEMPT_COLUMNS, FINDING_COLUMNS, INHERITED_COLUMNS,  # noqa: F401
                     LIFECYCLE, PROTOCOL_VERSION, RUN_RESULTS)

_HEADING = re.compile(r"^##[ \t]+(?P<title>.+?)[ \t]*$", re.MULTILINE)


class UnknownProtocolVersion(ValueError):
    """The `Protocol version` field is present but unreadable — spec 042 FR-010."""

    def __init__(self, raw):
        self.raw = raw
        super().__init__("unreadable protocol version %r" % (raw,))


class Section:
    __slots__ = ("title", "body")

    def __init__(self, title, body):
        self.title = title
        self.body = body          # everything after the heading line, verbatim

    def render(self):
        return "## %s\n%s" % (self.title, self.body)


class Orchestration:
    """A parsed ORCHESTRATION.md that can be re-rendered without drift."""

    def __init__(self, preamble="", sections=None, path=None, environ=None):
        self.preamble = preamble
        self.sections = sections or []
        self.path = path
        # Secrets are stripped at the WRITER, the same placement and the same
        # reason as in log.py: no call site can forget it. This file carries
        # agent-authored text verbatim - an escalation question, a finding's
        # required action - and a credential an agent echoes must not survive
        # into it (AC-012, D025).
        self.environ = environ

    # -- parsing ----------------------------------------------------------
    @classmethod
    def loads(cls, text, path=None, environ=None):
        matches = list(_HEADING.finditer(text))
        if not matches:
            return cls(preamble=text, sections=[], path=path, environ=environ)
        preamble = text[: matches[0].start()]
        sections = []
        for i, m in enumerate(matches):
            start = m.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            body = text[start:end]
            if body.startswith("\n"):
                body = body[1:]
            sections.append(Section(m.group("title"), body))
        return cls(preamble=preamble, sections=sections, path=path, environ=environ)

    @classmethod
    def load(cls, path, environ=None):
        with open(path, "r", encoding="utf-8") as fh:
            return cls.loads(fh.read(), path=path, environ=environ)

    # -- rendering --------------------------------------------------------
    def dumps(self):
        """The document as held in memory. Round-trip fidelity lives here."""
        return self.preamble + "".join(s.render() for s in self.sections)

    def redacted(self):
        """What actually reaches disk: `dumps()` with known secret values stripped."""
        return redact(self.dumps(), secret_values(self.environ))

    def create_exclusive(self, path):
        """Publish this document at `path` only if nothing is there yet.

        Two properties at once, and both are needed:

        * **atomic create-if-absent.** `os.link` fails with `FileExistsError` when
          the target exists and never replaces it, so two contenders cannot both
          succeed. `os.replace` would be wrong here: it overwrites.
        * **never partially visible.** The content is written and fsynced to a
          temporary name first, so the moment `path` exists it is already a
          complete document. Claiming with an empty `O_EXCL` file and filling it
          in afterwards leaves a window in which a contender loads a truncated
          document and blames the state instead of the other runner.

        Nothing is cleaned up here: a stale owner's document is *resumed* by
        `resume.inspect`, never deleted, so there is no reclaim race to lose.
        """
        directory = os.path.dirname(os.path.abspath(path)) or "."
        fd, tmp = tempfile.mkstemp(dir=directory, prefix=".orchestration-new-", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                fh.write(self.redacted())
                fh.flush()
                os.fsync(fh.fileno())
            os.link(tmp, path)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)
        self.path = path
        return path

    def save(self, path=None):
        """Atomic write — 031 requires the state file to be written atomically."""
        target = path or self.path
        if not target:
            raise ValueError("no path to save to")
        directory = os.path.dirname(os.path.abspath(target)) or "."
        fd, tmp = tempfile.mkstemp(dir=directory, prefix=".orchestration-", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                fh.write(self.redacted())
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
    def protocol_version(self):
        """The protocol contract version this document was written under.

        **Absent means 1** (spec 042 D003). That mirrors spec 041 D007 — a state
        file with no `Entry` line is read as `ready` — so the repository has one
        compatibility idiom rather than two, and every run started before the
        field existed stays resumable.

        **Present but unreadable fails closed**, including an empty value: a
        truncated write is how the value is lost in practice, and guessing there
        would be guessing about the very field that fixes what every other field
        means. Absent and empty are different things and are treated differently
        (spec 042 SPEC edge cases; domain:DOM-004 caught them being conflated).

        The field is looked for **anywhere in the document**, case-insensitively,
        with backticks stripped. Two writers state it in two dialects: this core
        writes it inside `## State`, lower-case and unquoted; the skill's scaffold
        states it in the header block, capitalised and backtick-quoted. A reader
        that understood only its own spelling read the other writer's document as
        *absent* and resumed it as version 1 — so the fail-closed gate could never
        fire on the writer most likely to trip it (security:SEC-001 /
        domain:DOM-003). Reading both is what spec 040 D034 §3 means by shared
        readability.
        """
        stated = []
        for line in self.dumps().splitlines():
            line = line.strip()
            if not line.startswith("- ") or ":" not in line:
                continue
            key, value = line[2:].split(":", 1)
            if key.strip().lower() == "protocol version":
                stated.append(value.strip().strip("`").strip())
        if not stated:
            return 1                       # absent
        # A document that states two DIFFERENT versions is self-contradictory, and
        # picking one silently is guessing at the field whose whole job is to say
        # what every other field means. The first draft took the first statement,
        # which would have become a fail-open the moment the version was bumped
        # (security:SEC-007). Repeating the same value is not a contradiction.
        if len(set(stated)) > 1:
            raise UnknownProtocolVersion(", ".join(stated))
        raw = stated[0]
        if not raw.isdigit() or int(raw) < 1:
            raise UnknownProtocolVersion(raw)
        return int(raw)

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
    inherited = caps.get("inherited")          # gate.Inherited, or None for a ready entry
    doc.set_body("State", render_fields({
        "writer": "sdd_runner",
        # spec 042 FR-009. Additive: a reader that predates the field ignores an
        # unknown State line, and a document without it reads as version 1.
        "protocol version": str(PROTOCOL_VERSION),
        "entry": str(caps.get("entry", "ready")),
        "adoption baseline commit": inherited.baseline if inherited else "n/a",
        "adoption diff base": ("%s (against %s)" % (inherited.diff_base,
                                                    inherited.default_branch)
                               if inherited else "n/a"),
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
    # An adopted run inherits checked tasks it never watched happen. Recording them
    # is the whole point: without these rows the document cannot say what it took on
    # trust (spec 041 FR-005/FR-010).
    doc.set_body("Inherited", render_table(INHERITED_COLUMNS, [
        {"Task": task_id, "Checked before adoption": "yes",
         "Verify clause": verify.replace("|", "\\|"),
         "Verification observed by this run": "no"}
        for task_id, verify in (inherited.checked if inherited else [])
    ]))
    doc.set_body("Findings", render_table(FINDING_COLUMNS, []))
    doc.set_body("Delegation log", "\n")
    doc.set_body("Escalations", "\n_None._\n\n")
    doc.set_body("Cap changes", "\n_None._\n\n")
    doc.set_body("Closure delta", "\n_Not frozen._\n\n")
    doc.set_body("Run result", "\nACTIVE\n\nresumable: yes\n\n")
    return doc
