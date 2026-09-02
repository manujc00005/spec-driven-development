"""Entry gate — spec 031 FR-002, spec 040 FR-002, spec 041 FR-010.

Refuses to start on any unmet precondition, naming the SPECIFIC condition and its
remediation, having changed nothing. Every refusal is a non-zero exit; none of
them is a warning.

Two first-entry modes (spec 041): a plain entry requires `Ready`; an *adopt*
entry (`--adopt`) requires `In Progress` and additionally a computable inherited
record — the baseline commit, the merge-base with the default branch as resolved
from git metadata, and the tasks already checked. In both modes any dirty path
refuses: on first entry no run exists yet to attribute anything to (041 D004).
"""

import os
import re
import subprocess
from dataclasses import dataclass, field

# First-entry statuses. `In Review` left both tuples with spec 041: its owning
# skills are /qa-review and /spec-close, never this loop.
READY_STATUSES = ("Ready",)
ADOPT_STATUSES = ("In Progress",)
REENTRY_STATUSES = ("Ready", "In Progress", "In Review")

# Stable condition names. The first three mirror skills/sdd-orchestrate/SKILL.md.
ADOPTION_NOT_NEEDED = "adoption not needed"
ALREADY_ENTERED = "already adopted or entered"
INHERITED_UNDETERMINED = "inherited diff undetermined"
# The fourth is the runner's alone, and deliberately so (spec 041 D011): the skill
# path is model-mediated and reads any SPEC dialect, so it never needs to say it
# could not read one. This parser does. Documented in runner/README.md and in the
# feature's SPEC so an operator who hits it on exit 10 finds it written down.
STATUS_UNREADABLE = "status unreadable"

# The lifecycle words this framework's own template uses. The gate does NOT try to
# parse an adopter's dialect — that surface is unbounded, and the skill path reads
# any of them because a model reads them. This list exists only to tell "a status
# the gate could not read" apart from "a status it read and rejected", so the
# refusal can say which (spec 041 T029, from the T014 replay).
KNOWN_STATUS_WORDS = ("Draft", "Ready", "In Progress", "In Review", "Done", "Archived")

# The names this runner's own bookkeeping owns inside the feature folder, so on
# re-entry they are in-flight work rather than an unaccounted-for change. Three of
# them the runner writes; `PR_DESCRIPTION.md` it does not — that belongs to the
# hand-off a follow-up owns (040 D034), and the name stays here only because
# `Loop._fingerprint` has excluded it since before spec 041 and dropping it would
# change fingerprints nobody asked to change. The cost is small and worth naming:
# on re-entry a dirty `PR_DESCRIPTION.md` is tolerated although no run produced it.
# `Loop._fingerprint` excludes
# the same NAMES for the same reason and imports this tuple so the two lists cannot
# drift apart. The names are shared, the matching rule is not: the fingerprint uses
# `endswith`, this gate compares exact repo-relative paths under the feature folder,
# which is the stricter of the two. Those paths are built with `os.path.relpath`
# while git porcelain always emits forward slashes, so the comparison assumes a
# POSIX checkout; the runner has never been exercised on Windows (040, experimental).
RUN_ARTIFACTS = ("ORCHESTRATION.md", "run.jsonl", "PR_DESCRIPTION.md", "TASKS.md")


@dataclass
class Refusal:
    condition: str
    detail: str
    remediation: str

    def render(self):
        return ("[GATE] refused: %s\n  detail: %s\n  remediation: %s"
                % (self.condition, self.detail, self.remediation))


@dataclass
class Inherited:
    """What an adopted run inherits (spec 041 gate condition 7)."""
    baseline: str
    diff_base: str
    default_branch: str
    checked: list = field(default_factory=list)   # [(task id, verify clause or "none")]


def _git(repo, *args):
    proc = subprocess.run(["git", "-C", repo] + list(args),
                          capture_output=True, text=True)
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def _status_line(spec_text):
    m = re.search(r"^##\s+Status\s*$", spec_text, re.MULTILINE)
    if not m:
        return None
    tail = spec_text[m.end():]
    for line in tail.splitlines():
        line = line.strip()
        if line and not line.startswith(">"):
            return line
    return None


def _looks_like_a_status(line):
    """True when the line plausibly states a lifecycle status.

    Deliberately generous: any known word appearing anywhere counts, so a decorated
    line (`**Done — 2026-08-22.**`) is read rather than refused as unreadable. What
    it catches is the line that carries no status at all — a code fence, a table
    border, a heading — where quoting it back at the maintainer explains nothing.
    """
    if not line:
        return False
    return any(word.lower() in line.lower() for word in KNOWN_STATUS_WORDS)


def _open_questions(spec_text):
    m = re.search(r"^##\s+Open questions\s*$", spec_text, re.MULTILINE)
    if not m:
        return 0
    tail = spec_text[m.end():]
    nxt = re.search(r"^##\s+", tail, re.MULTILINE)
    body = tail[: nxt.start()] if nxt else tail
    questions = []
    for line in body.splitlines():
        s = line.strip()
        if not s.startswith("- "):
            continue
        # A resolved question is struck through (~~OQ-n~~) or marked Resolved.
        if s.startswith("- ~~") or "**Resolved" in s or "Resolved " in s:
            continue
        questions.append(s[2:].strip())
    return questions


def _default_branch(repo):
    """The default branch from git metadata, or None. Never a guess (041 D003)."""
    code, default, _ = _git(repo, "symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD")
    if code == 0 and default:
        return default.split("/")[-1]
    return None


_TASK_ITEM = re.compile(r"^- \[(?P<mark>[ x])\] (?P<id>T\d{3})\b(?P<rest>.*?)(?=^- \[|\Z)",
                        re.MULTILINE | re.DOTALL)


def _checked_tasks(tasks_text):
    out = []
    for m in _TASK_ITEM.finditer(tasks_text):
        if m.group("mark") != "x":
            continue
        body = " ".join(m.group("rest").split())
        v = re.search(r"Verify:\s*(.+?)\s*$", body)
        out.append((m.group("id"), v.group(1) if v else "none"))
    return out


def inherited_record(repo, feature_dir):
    """Compute the inherited record, or return a Refusal (condition 7)."""
    code, baseline, _ = _git(repo, "rev-parse", "HEAD")
    if code != 0:
        return Refusal(INHERITED_UNDETERMINED, "HEAD cannot be resolved in %s" % repo,
                       "run inside a repository with at least one commit")
    default = _default_branch(repo)
    if default is None:
        return Refusal(INHERITED_UNDETERMINED,
                       "refs/remotes/origin/HEAD is not set, so the default branch is unknown",
                       "set it, e.g. `git remote set-head origin <branch>`, then re-run; the "
                       "gate never assumes a default-branch name")
    code, base, err = _git(repo, "merge-base", default, "HEAD")
    if code != 0 or not base:
        return Refusal(INHERITED_UNDETERMINED,
                       "no merge-base between %r and HEAD (%s)" % (default, err or "unrelated"),
                       "the feature branch must share history with %r" % default)
    tasks_path = os.path.join(feature_dir, "TASKS.md")
    checked = []
    if os.path.isfile(tasks_path):
        with open(tasks_path, encoding="utf-8") as fh:
            checked = _checked_tasks(fh.read())
    return Inherited(baseline=baseline, diff_base=base, default_branch=default, checked=checked)


def check(repo, feature_dir, baseline_cmd=None, first_entry=True, adopt=False,
          attributed=None):
    """Return a list of Refusals. Empty list == the gate passes.

    `attributed` lists the repo-relative paths the recorded run already claims;
    it is meaningful only on re-entry, where 031 condition 5 allows exactly those
    to be dirty. On first entry nothing is attributable and any dirty path refuses.
    """
    refusals = []

    spec_path = os.path.join(feature_dir, "SPEC.md")
    tasks_path = os.path.join(feature_dir, "TASKS.md")
    state_path = os.path.join(feature_dir, "ORCHESTRATION.md")

    if not os.path.isdir(feature_dir):
        return [Refusal("feature folder missing", feature_dir,
                        "pass an existing specs/features/<nnn>-<name> path")]
    if not os.path.isfile(spec_path):
        return [Refusal("SPEC.md missing", spec_path, "run /spec-create for this feature")]
    if not os.path.isfile(tasks_path):
        refusals.append(Refusal("TASKS.md missing", tasks_path,
                                "run /spec-plan to produce PLAN/TASKS/DECISIONS"))

    with open(spec_path, encoding="utf-8") as fh:
        spec_text = fh.read()

    status = _status_line(spec_text)
    status_readable = _looks_like_a_status(status)
    if adopt and os.path.exists(state_path):
        refusals.append(Refusal(
            ALREADY_ENTERED, "%s already exists" % state_path,
            "a run is resumed, never re-adopted: re-enter without --adopt"))
    if not status_readable:
        # Quoting back a code fence explains nothing. Say what happened instead, and
        # do not guess at the dialect: the gate reads this framework's own template
        # form, and says so (T029).
        refusals.append(Refusal(
            STATUS_UNREADABLE,
            ("SPEC.md has no `## Status` section" if status is None else
             "the first line under `## Status` is %r, which states no lifecycle status" % status),
            "the gate reads the framework's own form — `## Status`, then a line naming one of "
            "%s. A spec written in another dialect (a fenced block, a table) is not parsed here; "
            "the skill path reads it, this runner does not."
            % ", ".join(KNOWN_STATUS_WORDS)))
    elif first_entry and adopt:
        if status in READY_STATUSES:
            refusals.append(Refusal(
                ADOPTION_NOT_NEEDED, "SPEC.md Status is %r" % (status,),
                "run without --adopt; adoption is for a feature already In Progress"))
        elif status not in ADOPT_STATUSES:
            refusals.append(Refusal(
                "lifecycle status", "SPEC.md Status is %r" % (status,),
                "--adopt requires exactly In Progress; In Review belongs to /qa-review then "
                "/spec-close, Draft to /spec-plan, Done/Archived has nothing to run"))
    elif first_entry and status not in READY_STATUSES:
        refusals.append(Refusal(
            "lifecycle status", "SPEC.md Status is %r" % (status,),
            "promote the spec with /spec-plan; first entry requires Ready (an In Progress "
            "feature started by hand is adopted with --adopt)"))
    elif not first_entry and status not in REENTRY_STATUSES:
        refusals.append(Refusal(
            "lifecycle status", "SPEC.md Status is %r" % (status,),
            "re-entry requires one of %s" % ", ".join(REENTRY_STATUSES)))

    open_q = _open_questions(spec_text)
    if open_q:
        # Condition 2 forbids a question that BLOCKS an unchecked task. This gate
        # cannot judge that, so it refuses on any and says so, naming them, rather
        # than implying it weighed them (T030).
        shown = "; ".join(q[:80] for q in open_q[:3])
        refusals.append(Refusal(
            "open questions",
            "%d unresolved question(s) in SPEC.md, which this gate cannot judge as blocking or "
            "not: %s%s" % (len(open_q), shown, " …" if len(open_q) > 3 else ""),
            "condition 2 forbids a question that blocks an unchecked task, and the gate cannot "
            "tell which do. Resolve them, strike them through, or mark them Resolved so the "
            "answer is recorded rather than inferred; or run /spec-clarify"))

    code, branch, _ = _git(repo, "rev-parse", "--abbrev-ref", "HEAD")
    if code != 0:
        refusals.append(Refusal("not a git repository", repo, "run inside the repo checkout"))
    else:
        # Without adoption the pre-041 fallback to "main" stands; adoption never guesses.
        default_branch = _default_branch(repo) or "main"
        # A detached HEAD reports the literal string "HEAD" as its branch name, so it
        # never equalled the default branch and slipped through this condition. It is
        # not an isolated git location: it is no location at all, and adoption is the
        # worst place to allow it, because the maintainer's commit is both the baseline
        # and the attribution, and on a detached HEAD no branch references it.
        if branch == "HEAD":
            refusals.append(Refusal(
                "default branch", "HEAD is detached, so this run is on no branch at all",
                "check out a dedicated feature branch or worktree first, e.g. "
                "`git switch -c feature/<name>`; a commit made here would be referenced "
                "by nothing"))
        elif branch == default_branch:
            refusals.append(Refusal(
                "default branch", "HEAD is on %r" % branch,
                "check out a dedicated feature branch or worktree before running"
                + (" (`git switch -c feature/<name>` carries uncommitted work with it; "
                   "commit there before adopting)" if adopt else "")))

        # First entry: any dirty path refuses (041 D004), inside the feature folder or
        # out, because no run exists yet to attribute one to. Re-entry: 031 condition 5
        # — only the paths the recorded run already claims may be dirty, plus its own
        # state and evidence files, which the run is in the middle of writing.
        _, dirty, _ = _git(repo, "status", "--porcelain", "-uall")
        # Porcelain v1 is `XY<space>path`, but `_git` strips the whole output, so the
        # first line loses its leading status space and a fixed `[3:]` slice eats a
        # character of the path. Split on whitespace instead: it is correct with or
        # without that space.
        dirty_paths = [ln.split(None, 1)[-1].strip()
                       for ln in dirty.splitlines() if ln.strip()]
        if not first_entry:
            allowed = set(attributed or [])
            allowed.update(os.path.relpath(os.path.join(feature_dir, name), repo)
                           for name in RUN_ARTIFACTS)
            dirty_paths = [p for p in dirty_paths if p not in allowed]
        if dirty_paths:
            refusals.append(Refusal(
                "unattributed dirty tree", "%d dirty path(s): %s"
                % (len(dirty_paths), ", ".join(dirty_paths[:5])),
                ("commit the pre-adoption work on the feature branch (`git add -A && git commit`); "
                 "stash only what must be excluded from the feature") if adopt else
                ("commit, stash or discard the changes before starting an autonomous run"
                 if first_entry else
                 "on re-entry only the paths the recorded run claims may be dirty; inspect "
                 "`git status --short` and reconcile them by hand")))

        if adopt:
            record = inherited_record(repo, feature_dir)
            if isinstance(record, Refusal):
                refusals.append(record)

    if baseline_cmd:
        _, before, _ = _git(repo, "status", "--porcelain")
        proc = subprocess.run(baseline_cmd, shell=False, cwd=repo,
                              capture_output=True, text=True)
        _, after, _ = _git(repo, "status", "--porcelain")
        if proc.returncode != 0:
            refusals.append(Refusal(
                "red baseline suite", "%s exited %d" % (" ".join(baseline_cmd), proc.returncode),
                "get the baseline green before starting an autonomous run"))
        elif before != after:
            refusals.append(Refusal(
                "baseline suite mutates the tree",
                "git status changed while running %s" % " ".join(baseline_cmd),
                "make the baseline hermetic; a mutating baseline corrupts fingerprints"))

    return refusals
