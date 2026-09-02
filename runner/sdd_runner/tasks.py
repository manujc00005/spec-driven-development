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

# A repair task carries the finding it repairs in its title: `(from DOM-001)`.
# 031 FR-007 requires that traceability; the loop also uses it to tell a repair
# task (owned by the Findings registry) from an independently runnable one, so
# the same repair is never scheduled by two mechanisms.
_FROM_FINDING = re.compile(r"\(from ([^)]+)\)")

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

    @property
    def repairs(self):
        """The finding id this task repairs, or "" for an ordinary task."""
        m = _FROM_FINDING.search(self.title)
        return m.group(1) if m else ""


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


def independently_runnable(text):
    """Unchecked tasks the loop may pick up on its own.

    Repair tasks are excluded: they are scheduled by the Findings registry as
    part of their task's convergence cycle. Treating them as ordinary pending
    work would delegate the same repair twice.
    """
    return [t for t in parse(text) if t.runnable and not t.repairs]


def next_task_id(text):
    ids = [int(t.id[1:]) for t in parse(text) if t.id[1:].isdigit()]
    return "T%03d" % ((max(ids) + 1) if ids else 1)


def check_task(text, task_id):
    """Mark one task item `[x]`. Returns the text unchanged if it is already checked."""
    out = []
    for line in text.splitlines(True):
        m = _BULLET.match(line.rstrip("\n"))
        if m and m.group("rest").strip().startswith(task_id + " "):
            line = line.replace("- [ ]", "- [x]", 1)
        out.append(line)
    return "".join(out)


def uncheck_task(text, task_id):
    """Return a task item to `[ ]`. Used when a re-review stales an approval and
    the task goes back to REVIEW - leaving it checked would make a later resume
    skip work that is no longer done."""
    out = []
    for line in text.splitlines(True):
        m = _BULLET.match(line.rstrip("\n"))
        if m and m.group("rest").strip().startswith(task_id + " "):
            line = line.replace("- [x]", "- [ ]", 1)
        out.append(line)
    return "".join(out)


def task_for_finding(text, finding_id):
    """The existing repair task for this finding, or None. Never allocate a second."""
    for task in parse(text):
        if task.repairs == finding_id:
            return task
    return None


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
