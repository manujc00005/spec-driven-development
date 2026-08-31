"""TASKS.md parsing — spec 031 FR-007, and the Verify clause of spec 033.

The detection unit is the TASK ITEM: the bullet beginning `- [ ]` or `- [x]`
together with its continuation lines, up to the next bullet. Within it, the
`Covers:` clause and the `Verify:` clause are the task's traceability and its
stop condition.

The runner never EXECUTES a Verify clause (031 FR-010). It evaluates a claimed
completion against it.
"""

import re
from dataclasses import dataclass, field

_BULLET = re.compile(r"^- \[(?P<mark>[ x~])\]\s*(?P<rest>.*)$")
_ID = re.compile(r"^(?P<id>T\d{3})\b\s*-?\s*(?P<title>.*)$")


@dataclass
class Task:
    id: str
    title: str
    checked: bool
    deferred: bool
    covers: list = field(default_factory=list)
    verify: str = ""
    phase: str = ""
    raw: str = ""

    @property
    def runnable(self):
        return not self.checked and not self.deferred


def _clause(text, label):
    m = re.search(r"%s:\s*(?P<v>.*)" % label, text, re.DOTALL)
    if not m:
        return ""
    value = m.group("v")
    # A clause ends where the next known clause begins.
    for other in ("Covers:", "Verify:"):
        if other.lower() != label.lower() + ":":
            idx = value.find(other)
            if idx != -1:
                value = value[:idx]
    return " ".join(value.split())


def parse(text):
    tasks = []
    phase = ""
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("## "):
            phase = line[3:].strip()
            i += 1
            continue
        m = _BULLET.match(line)
        if not m:
            i += 1
            continue
        block = [m.group("rest")]
        j = i + 1
        while j < len(lines) and not _BULLET.match(lines[j]) and not lines[j].startswith("## "):
            block.append(lines[j])
            j += 1
        raw = "\n".join(block)
        idm = _ID.match(m.group("rest").strip())
        if idm:
            covers = re.findall(r"AC-\d{3}", _clause(raw, "Covers"))
            tasks.append(Task(
                id=idm.group("id"),
                title=idm.group("title").strip(),
                checked=m.group("mark") == "x",
                deferred=m.group("mark") == "~",
                covers=covers,
                verify=_clause(raw, "Verify"),
                phase=phase,
                raw=raw,
            ))
        i = j
    return tasks


def unchecked(text):
    return [t for t in parse(text) if t.runnable]


def next_task_id(text):
    ids = [int(t.id[1:]) for t in parse(text) if t.id[1:].isdigit()]
    return "T%03d" % ((max(ids) + 1) if ids else 1)


def append_finding_task(text, task_id, title, finding_id, covers, required_action):
    """Create exactly one unchecked task for a NEW finding identity (031 FR-007).

    Title suffix `(from <finding-id>)` keeps requirement<->task<->test traceability.
    """
    line = ("- [ ] %s - %s (from %s). Covers: %s. Verify: the originating reviewer returns APPROVE "
            "on the re-review, and its required action is satisfied: %s"
            % (task_id, title, finding_id, ", ".join(covers) if covers else "AC-000",
               required_action))
    body = text.rstrip("\n")
    return body + "\n" + line + "\n"
