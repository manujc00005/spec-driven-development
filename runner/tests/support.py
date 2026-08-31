"""Shared test helpers. Stdlib only — the suite must run with nothing installed."""

import os
import subprocess
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURES = os.path.join(HERE, "fixtures", "responses")
REPO_ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))


def fixture(name):
    with open(os.path.join(FIXTURES, name), encoding="utf-8") as fh:
        return fh.read()


SPEC = """# Feature Spec: fixture

## Status

Ready

## Open questions

- ~~OQ-1~~ **Resolved.**

## Acceptance criteria

- AC-001: the thing works.
"""

TASKS = """# Tasks: fixture

## Phase 2: Implementation

- [ ] T001 - Do the first thing. Covers: AC-001. Verify: the suite passes.
- [ ] T002 - Do the second thing. Covers: AC-001. Verify: the suite passes.
"""


def make_repo(tmpdir, tasks=TASKS, spec=SPEC, feature="specs/features/900-fixture"):
    """A real git repo on a non-default branch with a clean tree and a Ready spec."""
    repo = os.path.join(tmpdir, "repo")
    feature_dir = os.path.join(repo, feature)
    os.makedirs(feature_dir)
    os.makedirs(os.path.join(repo, "agents"), exist_ok=True)
    for agent in ("implementer", "domain-reviewer", "security-reviewer",
                  "final-conformance-reviewer", "deep-reasoner"):
        with open(os.path.join(repo, "agents", agent + ".md"), "w", encoding="utf-8") as fh:
            fh.write("# %s\nSystem prompt for %s.\n" % (agent, agent))
    with open(os.path.join(feature_dir, "SPEC.md"), "w", encoding="utf-8") as fh:
        fh.write(spec)
    with open(os.path.join(feature_dir, "TASKS.md"), "w", encoding="utf-8") as fh:
        fh.write(tasks)

    def git(*args):
        subprocess.run(["git", "-C", repo] + list(args), check=True,
                       capture_output=True, text=True)

    git("init", "-q")
    git("config", "user.email", "fixture@example.invalid")
    git("config", "user.name", "Fixture")
    git("add", "-A")
    git("commit", "-qm", "fixture baseline")
    git("checkout", "-q", "-b", "feat/fixture")
    return repo, feature_dir


# Finalization (031 FR-013) costs four delegations beyond the task cycle:
# final-conformance-reviewer, then the three owning lifecycle skills.
FINALIZATION_CALLS = 4


def approve_block():
    return "Looks right.\n\n```yaml\nverdict: APPROVE\nfindings: []\n```\n"


def finalization_flat():
    """Responses a flat-list stub needs appended for a run that should reach DONE."""
    return [approve_block()] * FINALIZATION_CALLS


def finalization_keys(each=1):
    """The same, for an agent-keyed stub script."""
    return {
        "final-conformance-reviewer": [approve_block()] * each,
        "lifecycle:spec-review": [approve_block()] * each,
        "lifecycle:spec-close": [approve_block()] * each,
        "lifecycle:pr-description": [approve_block()] * each,
    }
