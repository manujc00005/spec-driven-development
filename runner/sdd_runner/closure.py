"""Freeze and closure delta — spec 031 FR-013, spec 040 T014.

Three words with exact meanings, because the whole feature turns on them.

**Freeze.** The moment the run records the implementation fingerprint that every
required reviewer has approved, together with a per-path content map of the tree
at that instant. Nothing may be delegated to a lifecycle skill before this, and
the frozen fingerprint is what every later comparison is made against.

**Closure allowlist.** The narrow set of paths that MAY change after the freeze
without invalidating it: the status/evidence writes the owning lifecycle skills
make, plus the generated `ORCHESTRATION.md`, `CALIBRATION.md`, `PR_DESCRIPTION.md`
and `run.jsonl`. `SPEC.md` is allowed only for a change confined to its `## Status`
section; `TASKS.md` only for checkbox bookkeeping. Everything else - production,
tests, PLAN content, DECISIONS content, a non-lifecycle SPEC change - is
unexpected.

**Closure delta.** The observed difference between the frozen map and the tree at
the end, each path classified allowed or unexpected. An allowed delta is audited
and does not stale the frozen approval. A single unexpected path invalidates
final conformance and returns the run to REVIEW.

The asymmetry is deliberate: this module decides that something IS allowed only
when it can say which rule allows it. Anything it cannot classify is unexpected.

**What spec 040 actually drives (D034, T032).** Only the freeze half:
`tree_map`, `render` and `parse`. The loop records the frozen fingerprint, the
verification outcome and the frozen tree map, and stops — the closure delta is
computed over what the owning lifecycle skills change after the freeze, and this
runner does not dispatch them. `observe`, `unexpected` and `classify` are kept
here, tested here, and called by nobody in production: they are the seam the
follow-up `Finalizer` spec begins at (AUDIT-9), and the frozen map above is what
it will compare against. Deleting them would only mean writing them again.
"""

import hashlib
import os
import re
import subprocess

from . import state as state_mod

# Generated artifacts, allowed to change after the freeze - but ONLY inside the
# feature folder. Matching the basename alone would allow any `src/run.jsonl` or
# `lib/PR_DESCRIPTION.md` anywhere in the repo, and this is the last gate before
# DONE (SEC-001).
GENERATED = ("ORCHESTRATION.md", "run.jsonl", "PR_DESCRIPTION.md", "CALIBRATION.md")

ALLOWED = "allowed"
UNEXPECTED = "unexpected"

CLOSURE_COLUMNS = ["Path", "Frozen", "Observed", "Classification", "Rule"]

DELETED = "<deleted>"
# A path the process cannot read is NOT the same as an absent one, and it must
# not raise out of the audit: it registers as a change and gets classified like
# any other (PY-1).
UNREADABLE = "<unreadable>"

# 031's second DONE condition: a green, non-mutating verification suite. These
# are the four outcomes, and only PASS satisfies it (AUDIT-1, spec 040 D036).
VERIFY_PASS = "PASS"
VERIFY_NOT_DECLARED = "NOT DECLARED - condition 2 of 031's termination contract is unobserved"
VERIFY_FAILED = "FAILED"
VERIFY_MUTATED = "MUTATED THE TREE"


class CorruptClosureRecord(ValueError):
    """The persisted closure record cannot be read. Never guess past this."""


def _hash_file(path):
    try:
        with open(path, "rb") as fh:
            return hashlib.sha256(fh.read()).hexdigest()[:16]
    except (FileNotFoundError, IsADirectoryError):
        return DELETED
    except OSError:
        return UNREADABLE


def tree_map(repo):
    """{path: short content hash} for every path git reports as changed.

    Built from `git status --porcelain`, so it covers modified tracked files and
    untracked ones alike, and a path that stops being reported is itself a delta.
    """
    proc = subprocess.run(
        ["git", "-C", repo, "status", "--porcelain=v1", "-uall"],
        capture_output=True, text=True)
    out = {}
    for line in proc.stdout.splitlines():
        path = line[3:].strip().strip('"')
        if not path or path.endswith("/"):
            continue
        out[path] = _hash_file(os.path.join(repo, path))
    return out


def _section_changed_only(repo, path, section):
    """True when the diff for `path` touches only lines inside `## <section>`.

    Conservative by construction: an unreadable diff, a new file, or any hunk
    that starts outside the section returns False.
    """
    proc = subprocess.run(["git", "-C", repo, "diff", "-U0", "HEAD", "--", path],
                          capture_output=True, text=True)
    if proc.returncode != 0 or not proc.stdout.strip():
        return False

    full = os.path.join(repo, path)
    try:
        with open(full, encoding="utf-8") as fh:
            lines = fh.read().splitlines()
    except OSError:
        return False

    bounds = None
    for i, line in enumerate(lines):
        if re.match(r"^##\s+%s\s*$" % re.escape(section), line):
            end = len(lines)
            for j in range(i + 1, len(lines)):
                if lines[j].startswith("## "):
                    end = j
                    break
            bounds = (i + 1, end + 1)          # 1-based, inclusive-ish
            break
    if bounds is None:
        return False

    for hunk in re.finditer(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@", proc.stdout,
                            re.MULTILINE):
        start = int(hunk.group(1))
        count = int(hunk.group(2) or 1)
        if count == 0:                          # pure deletion: cannot localize safely
            return False
        if start < bounds[0] or start + count - 1 > bounds[1]:
            return False
    return True


def _checkbox_only(repo, path):
    """True when the diff for `path` changes nothing but `- [ ]` / `- [x]` markers."""
    proc = subprocess.run(["git", "-C", repo, "diff", "-U0", "HEAD", "--", path],
                          capture_output=True, text=True)
    if proc.returncode != 0 or not proc.stdout.strip():
        return False
    removed, added = [], []
    for line in proc.stdout.splitlines():
        if line.startswith("+++") or line.startswith("---"):
            continue
        if line.startswith("+"):
            added.append(line[1:])
        elif line.startswith("-"):
            removed.append(line[1:])
    if len(added) != len(removed):
        return False
    for before, after in zip(removed, added):
        if before.replace("- [ ]", "- [x]", 1) != after:
            return False
    return True


def classify(repo, feature_dir, path):
    """Return (classification, rule) for one changed path."""
    name = os.path.basename(path)
    in_feature = os.path.abspath(os.path.join(repo, path)).startswith(
        os.path.abspath(feature_dir) + os.sep)

    if name in GENERATED:
        if in_feature:
            return ALLOWED, "generated artifact in the feature folder"
        return UNEXPECTED, ("a file named like a generated artifact, but outside the feature "
                            "folder")

    if in_feature and name == "SPEC.md":
        if _section_changed_only(repo, path, "Status"):
            return ALLOWED, "SPEC.md Status section only"
        return UNEXPECTED, "SPEC.md changed outside its Status section"

    if in_feature and name == "TASKS.md":
        if _checkbox_only(repo, path):
            return ALLOWED, "TASKS.md checkbox bookkeeping only"
        return UNEXPECTED, "TASKS.md content changed beyond checkbox bookkeeping"

    return UNEXPECTED, "not on the closure allowlist"


def observe(repo, feature_dir, frozen):
    """Compare the tree against the frozen map. Returns a list of delta rows."""
    current = tree_map(repo)
    rows = []
    for path in sorted(set(frozen) | set(current)):
        before = frozen.get(path, "<absent>")
        after = current.get(path, "<absent>")
        if before == after:
            continue
        classification, rule = classify(repo, feature_dir, path)
        rows.append({"Path": path, "Frozen": before, "Observed": after,
                     "Classification": classification, "Rule": rule})
    return rows


def unexpected(rows):
    return [r for r in rows if r["Classification"] == UNEXPECTED]


# -- persistence ------------------------------------------------------------
def render(frozen_fingerprint, frozen, delta_rows, phase, verification):
    """The `## Closure delta` section body. Human-readable first, parseable second."""
    head = ("\n- frozen fingerprint: %s\n- phase: %s\n- verification: %s\n- frozen paths: %d\n\n"
            % (frozen_fingerprint or "none", phase, verification, len(frozen)))
    frozen_table = state_mod.render_table(
        ["Path", "Frozen hash"],
        [{"Path": p, "Frozen hash": h} for p, h in sorted(frozen.items())]).rstrip("\n")
    delta_table = state_mod.render_table(CLOSURE_COLUMNS, delta_rows).rstrip("\n")
    return head + "### Frozen tree\n" + frozen_table + "\n\n### Observed delta\n" + delta_table \
        + "\n\n"


def parse(body):
    """Read back a persisted closure record. Raise CorruptClosureRecord on anything odd."""
    fields = state_mod.parse_fields(body)
    if "frozen fingerprint" not in fields or "phase" not in fields:
        raise CorruptClosureRecord(
            "the Closure delta section has no frozen fingerprint or phase")

    parts = body.split("### Frozen tree")
    if len(parts) != 2:
        raise CorruptClosureRecord("the Closure delta section has no Frozen tree table")
    rest = parts[1].split("### Observed delta")
    if len(rest) != 2:
        raise CorruptClosureRecord("the Closure delta section has no Observed delta table")

    try:
        frozen_headers, frozen_rows = state_mod.parse_table(rest[0])
        delta_headers, delta_rows = state_mod.parse_table(rest[1])
    except ValueError as exc:
        raise CorruptClosureRecord("a Closure delta table is malformed: %s" % exc)

    if frozen_rows and frozen_headers != ["Path", "Frozen hash"]:
        raise CorruptClosureRecord(
            "the Frozen tree table uses columns this runner does not write: %s" % frozen_headers)
    if delta_rows and delta_headers != CLOSURE_COLUMNS:
        raise CorruptClosureRecord(
            "the Observed delta table uses columns this runner does not write: %s" % delta_headers)

    declared = fields.get("frozen paths", "").strip()
    if declared.isdigit() and int(declared) != len(frozen_rows):
        raise CorruptClosureRecord(
            "the Closure delta section declares %s frozen paths but lists %d"
            % (declared, len(frozen_rows)))

    return {
        "frozen_fingerprint": fields["frozen fingerprint"],
        "phase": fields["phase"],
        "verification": fields.get("verification", ""),
        "frozen": {r["Path"]: r["Frozen hash"] for r in frozen_rows},
        "delta": delta_rows,
    }
