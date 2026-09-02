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


ADOPT_SPEC = """# Feature Spec: adopted fixture

## Status

In Progress

## Open questions

- ~~OQ-1~~ **Resolved.**

## Acceptance criteria

- AC-001: members get the discount and non-members do not.
- AC-002: totals never go negative.
"""

ADOPT_TASKS_BEFORE = """# Tasks: adopted fixture

## Phase 2: Implementation

- [ ] T001 - Add the pricing module. Covers: AC-001. Verify: `python3 -c "import src.pricing"` exits 0.
- [ ] T002 - Apply the member discount. Covers: AC-001. Verify: `discount(1500, member=True)` returns 500.
- [ ] T003 - Clamp totals at zero. Covers: AC-002. Verify: `discount(100, member=True)` returns 0.
- [ ] T004 - Add the unit tests. Covers: AC-001, AC-002. Verify: `python3 -m unittest src.test_pricing` exits 0.
"""

ADOPT_TASKS_AFTER = ADOPT_TASKS_BEFORE.replace(
    "- [ ] T001", "- [x] T001").replace("- [ ] T002", "- [x] T002")

# The seeded defect (spec 041 T001): the discount is applied whether or not the
# buyer is a member, so AC-001 is violated by the inherited diff. A domain
# reviewer reading this file should REJECT it; that is what the adoption
# calibration run (T012) relies on.
ADOPT_PRICING = '''"""Pricing for the adopted fixture."""

MEMBER_DISCOUNT = 1000


def discount(total, member=False):
    # SEEDED DEFECT: `member` is ignored.
    return total - MEMBER_DISCOUNT
'''


def make_adopted_repo(tmpdir, feature="specs/features/901-adopted"):
    """A repo in the shape spec 041's adoption gate expects to inherit.

    `main` is the default branch and is resolvable through `origin/HEAD`; the
    feature branch carries one commit with T001/T002 checked, their diff, and
    one seeded reviewable defect; T003/T004 are unchecked; the tree is clean.
    Returns (repo, feature_dir, info) where info holds the shas the gate will
    compute: `baseline` (feature HEAD) and `diff_base` (merge-base with main).
    """
    repo = os.path.join(tmpdir, "adopted")
    feature_dir = os.path.join(repo, feature)
    os.makedirs(feature_dir)
    os.makedirs(os.path.join(repo, "agents"), exist_ok=True)
    for agent in ("implementer", "domain-reviewer", "security-reviewer",
                  "final-conformance-reviewer", "deep-reasoner"):
        with open(os.path.join(repo, "agents", agent + ".md"), "w", encoding="utf-8") as fh:
            fh.write("# %s\nSystem prompt for %s.\n" % (agent, agent))

    def write(rel, text):
        path = os.path.join(repo, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)

    def git(*args):
        return subprocess.run(["git", "-C", repo] + list(args), check=True,
                              capture_output=True, text=True).stdout.strip()

    # Default branch: planned, nothing implemented.
    write(os.path.join(feature, "SPEC.md"), ADOPT_SPEC.replace("In Progress", "Ready"))
    write(os.path.join(feature, "TASKS.md"), ADOPT_TASKS_BEFORE)
    git("init", "-q", "-b", "main")
    git("config", "user.email", "fixture@example.invalid")
    git("config", "user.name", "Fixture")
    git("add", "-A")
    git("commit", "-qm", "plan the adopted fixture")
    diff_base = git("rev-parse", "HEAD")

    # Feature branch: the maintainer implemented T001/T002 by hand and committed.
    git("checkout", "-q", "-b", "feat/adopted")
    write("src/__init__.py", "")
    write("src/pricing.py", ADOPT_PRICING)
    write(os.path.join(feature, "SPEC.md"), ADOPT_SPEC)
    write(os.path.join(feature, "TASKS.md"), ADOPT_TASKS_AFTER)
    git("add", "-A")
    git("commit", "-qm", "implement T001 and T002 by hand")
    baseline = git("rev-parse", "HEAD")

    # `origin/HEAD` is how the gate resolves the default branch (spec 041 D003).
    origin = os.path.join(tmpdir, "origin.git")
    subprocess.run(["git", "init", "-q", "--bare", "-b", "main", origin],
                   check=True, capture_output=True, text=True)
    git("remote", "add", "origin", origin)
    git("push", "-q", "origin", "main", "feat/adopted")
    git("remote", "set-head", "origin", "main")

    return repo, feature_dir, {"baseline": baseline, "diff_base": diff_base,
                               "branch": "feat/adopted", "default_branch": "main"}


# Finalization on 040's side of the `_finalize` seam costs exactly ONE delegation
# beyond the task cycle: final-conformance-reviewer. The three owning lifecycle
# skills used to be dispatched here too; D034 put them outside this spec, so a
# harness that still scripted them was paying for calls the runner never makes.
FINALIZATION_CALLS = 1


def approve_block():
    return "Looks right.\n\n```yaml\nverdict: APPROVE\nfindings: []\n```\n"


# 031's condition 2 in its smallest honest form: a command that passes and
# changes nothing. A harness that means to reach DONE must declare one (D035).
GREEN_BASELINE = ["true"]


def finalization_flat():
    """Responses a flat-list stub needs appended for a run that should reach DONE."""
    return [approve_block()] * FINALIZATION_CALLS


def finalization_keys(each=1):
    """The same, for an agent-keyed stub script."""
    return {"final-conformance-reviewer": [approve_block()] * each}
