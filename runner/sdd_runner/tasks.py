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
# The allocation marker, ANCHORED. It matches `(from <identity>)` where the
# identity is a finding id with an optional reviewer namespace, and nothing else.
# The unanchored `\(from ([^)]+)\)` it replaces matched any parenthetical starting
# with "from", and — worse — was only ever applied to a task's FIRST line, so a
# title wrapped across two lines carried no marker at all. Against this feature's
# own TASKS.md that combination made `task_for_finding` return `None` for every
# identity, while `_schedule_repairs` promised in a comment to reuse the task it
# could no longer find (spec 042 `maintainer:MNT-004`).
# `SEC-006`, `security:SEC-006`, and the synthetic form the protocol mints for a
# reviewer that returns two malformed blocks: `ORCH-MALFORMED-final-conformance-2`.
# The suite's own `test_a_synthetic_finding_id_is_still_recognized` caught a first
# draft of this pattern that omitted the synthetic shape — narrowing the parse is
# right, narrowing it past a real id is not.
_IDENTITY = r"(?:[a-z][a-z-]*:)?[A-Z]{3,}(?:-[A-Z]+)*(?:-[a-z][a-z-]*)*-\d+"
_FROM_FINDING = re.compile(r"\(from\s+(?P<ids>%s(?:\s*(?:,|and)\s*%s)*)\s*[^)]*\)"
                           % (_IDENTITY, _IDENTITY))
_BARE_IDENTITY = re.compile(_IDENTITY)

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
        """The first identity this task repairs, or "" — legacy single-value form."""
        found = self.repairs_all
        return found[0] if found else ""

    @property
    def repairs_all(self):
        """Every identity this task is allocated to, in order.

        Read from the WHOLE task item, not its first line: a title wrapped across
        lines used to lose its marker entirely. Two identities may share one task
        when they are literally the same defect — `security:SEC-001` and
        `domain:DOM-003` are the worked example — so this returns a list.

        Only the `(from …)` marker counts. A finding id mentioned anywhere else in
        the task's prose is provenance, not an allocation, and creates no
        association: this feature has three such mentions (*"the second half of
        domain:DOM-020"*, *"raised adjacent to security:SEC-002"*, a parenthetical
        naming why a clause changed) and a substring search treats all three as
        allocations.
        """
        # The logical header only: everything before `Covers:`. Searching the whole
        # item turned a `(from SEC-006)` written inside a `Verify:` clause or in
        # narrative prose into an allocation (`maintainer:MNT-007`) — the same
        # mention-read-as-use failure this parse was tightened to end.
        header = " ".join((self.raw or self.title).split())
        cut = header.find("Covers:")
        if cut != -1:
            header = header[:cut]
        m = _FROM_FINDING.search(header)
        if not m:
            return []
        return [i.group(0) for i in _BARE_IDENTITY.finditer(m.group("ids"))]


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


class BrokenRepairTaskReference(RuntimeError):
    """The Findings registry and `TASKS.md` disagree — spec 042 `maintainer:MNT-005`.

    Raised, never returned as `None`, because `None` already means *"this identity
    has no task yet"* and the caller acts on that by **allocating one**. A registry
    naming a task that does not exist would therefore have produced a second task
    for an identity that already owned one — the exact outcome the registry rule
    exists to prevent, reached through the code written to enforce it.

    Also raised when the registry itself is malformed: one identity in two rows, or
    a Repair-task column naming more than one canonical task. Both were silently
    resolved by taking the first — `setdefault` for the row, `[0]` for the cell —
    which is `domain:DOM-025`'s defect reintroduced inside its own detector
    (`maintainer:MNT-006`).
    """


def _same_identity(a, b):
    """`SEC-006` and `security:SEC-006` are the same identity; namespace is optional."""
    return a.split(":")[-1] == b.split(":")[-1]


def task_for_finding(text, finding_id, registry=None):
    """The repair task allocated to this identity, or None.

    `registry` — a mapping of identity to task id, read from the Findings registry
    — is the **authority** when it is supplied: the registry is the structured
    record of which task owns which identity, and a title suffix is prose that can
    be reworded, wrapped or dropped. When the registry names a task, this returns
    that task and validates it exists; a registry naming a task that is **not** in
    `TASKS.md` raises `BrokenRepairTaskReference` rather than returning `None`, so
    the caller refuses instead of allocating a second task against a broken record.

    `None` was the first answer here and it was unsafe: it already means *"this
    identity has no task yet"*, and `_schedule_repairs` acts on that by creating
    one (`maintainer:MNT-005`). Only a value the caller cannot mistake for absence
    works.

    Without a registry — or when the registry does not know this identity — the
    `(from …)` marker is the fallback, which is what the loop had before and what
    silently stopped working (`maintainer:MNT-004`).
    """
    parsed = parse(text)
    if registry:
        for identity, task_id in registry.items():
            if _same_identity(identity, finding_id):
                for task in parsed:
                    if task.id == task_id:
                        return task
                raise BrokenRepairTaskReference(
                    "the registry allocates %s to %s, which is not in TASKS.md"
                    % (identity, task_id))
    for task in parsed:
        if any(_same_identity(r, finding_id) for r in task.repairs_all):
            return task
    return None


def registry_task_refs(findings_text):
    """Parse a Findings registry into {identity: task id}.

    Deliberately narrow: it reads the table's identity column and its repair-task
    column and nothing else, so a finding id appearing in a *narrative* cell — a
    fingerprint that says "the tree the MNT-001 repair produced", a required
    action that names a sibling — creates no association. That distinction is the
    whole reason the registry, and not a search, is the authority.

    **It fails closed rather than choosing.** One identity in two rows, or a
    Repair-task cell naming more than one task, raises. The first version used
    `setdefault` and `task_ids[0]`, so both shapes resolved silently to whichever
    came first — which is `domain:DOM-025`'s defect (a duplicate row hidden by a
    dict) reproduced inside the function written to detect it
    (`maintainer:MNT-006`). A deviation belongs in the Required-action prose and in
    D016, not in the structured column.
    """
    refs = {}
    for line in findings_text.splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 4:
            continue
        identity = cells[0].strip("*` ")
        if not re.fullmatch(r"[a-z][a-z-]*:[A-Z]{3,}(?:-[A-Z]+)*(?:-[a-z][a-z-]*)*-\d+",
                            identity):
            continue
        if identity in refs:
            raise BrokenRepairTaskReference(
                "%s appears in more than one registry row; one identity, one row"
                % identity)
        task_ids = re.findall(r"\bT\d{3}\b", cells[3])
        if len(task_ids) > 1:
            raise BrokenRepairTaskReference(
                "%s names %d tasks in its Repair task column (%s); the column holds "
                "the canonical task only, and a deviation belongs in Required action"
                % (identity, len(task_ids), ", ".join(task_ids)))
        if task_ids:
            refs[identity] = task_ids[0]
    return refs


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
