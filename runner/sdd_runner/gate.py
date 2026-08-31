"""Entry gate — spec 031 FR-002, spec 040 FR-002.

Refuses to start on any unmet precondition, naming the SPECIFIC condition and its
remediation, having changed nothing. Every refusal is a non-zero exit; none of
them is a warning.
"""

import os
import re
import subprocess
from dataclasses import dataclass

READY_STATUSES = ("Ready", "In Progress", "In Review")


@dataclass
class Refusal:
    condition: str
    detail: str
    remediation: str

    def render(self):
        return ("[GATE] refused: %s\n  detail: %s\n  remediation: %s"
                % (self.condition, self.detail, self.remediation))


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


def _open_questions(spec_text):
    m = re.search(r"^##\s+Open questions\s*$", spec_text, re.MULTILINE)
    if not m:
        return 0
    tail = spec_text[m.end():]
    nxt = re.search(r"^##\s+", tail, re.MULTILINE)
    body = tail[: nxt.start()] if nxt else tail
    count = 0
    for line in body.splitlines():
        s = line.strip()
        if not s.startswith("- "):
            continue
        # A resolved question is struck through (~~OQ-n~~) or marked Resolved.
        if s.startswith("- ~~") or "**Resolved" in s or "Resolved " in s:
            continue
        count += 1
    return count


def check(repo, feature_dir, baseline_cmd=None, first_entry=True):
    """Return a list of Refusals. Empty list == the gate passes."""
    refusals = []

    spec_path = os.path.join(feature_dir, "SPEC.md")
    tasks_path = os.path.join(feature_dir, "TASKS.md")

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
    if first_entry and status not in READY_STATUSES:
        refusals.append(Refusal(
            "lifecycle status", "SPEC.md Status is %r" % (status,),
            "promote the spec with /spec-plan; first entry requires one of %s"
            % ", ".join(READY_STATUSES)))

    open_q = _open_questions(spec_text)
    if open_q:
        refusals.append(Refusal(
            "open questions", "%d unresolved question(s) in SPEC.md" % open_q,
            "answer them and record the resolution, or run /spec-clarify"))

    code, branch, _ = _git(repo, "rev-parse", "--abbrev-ref", "HEAD")
    if code != 0:
        refusals.append(Refusal("not a git repository", repo, "run inside the repo checkout"))
    else:
        code, default, _ = _git(repo, "symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD")
        default_branch = default.split("/")[-1] if code == 0 and default else "main"
        if branch == default_branch:
            refusals.append(Refusal(
                "default branch", "HEAD is on %r" % branch,
                "check out a dedicated feature branch or worktree before running"))

        _, dirty, _ = _git(repo, "status", "--porcelain", "-uall")
        unattributed = [ln for ln in dirty.splitlines()
                        if ln.strip() and os.path.relpath(feature_dir, repo) not in ln]
        if unattributed:
            refusals.append(Refusal(
                "unattributed dirty tree", "%d path(s) modified outside the feature folder"
                % len(unattributed),
                "commit, stash or attribute the changes before starting an autonomous run"))

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
