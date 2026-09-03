"""Golden CLI transcripts — spec 042 T001/T019, decided by D007.

AC-008 requires the CLI's observable behaviour to be byte-identical across the
refactor. The 276 tests assert the LOOP's behaviour; none of them asserts a byte
of what the CLI prints, and FR-007 requires the dry-run rendering to survive
unchanged. So the oracle is recorded here, from the PRE-refactor code, before the
first implementation task touches anything (D007).

A transcript is `exit code + stdout + stderr`, normalized: temp paths, shas,
timestamps, pids and hostnames differ per run and are replaced by placeholders.
Everything else must match byte for byte. The normalization is deliberately
narrow — it hides what cannot be stable and nothing else, because a normalizer
that scrubs too much turns a regression test into a formality.
"""

import io
import os
import re
import socket
import subprocess
import sys
import tempfile
from contextlib import redirect_stderr, redirect_stdout

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from tests import support  # noqa: E402

GOLDEN_DIR = os.path.join(
    support.REPO_ROOT, "specs", "features", "042-canonical-autonomous-core",
    "evidence", "golden")

_SHA = re.compile(r"\b[0-9a-f]{40}\b")
# Also covers the 16-hex approval fingerprints the loop prints in its DONE reason.
_SHORT_SHA = re.compile(r"\b[0-9a-f]{7,64}\b")
_TS = re.compile(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:?\d{2})?")


def normalize(text, repo=None, tmpdir=None):
    """Replace what cannot be stable between two runs, and nothing else."""
    if repo:
        text = text.replace(os.path.realpath(repo), "<REPO>").replace(repo, "<REPO>")
    if tmpdir:
        text = text.replace(os.path.realpath(tmpdir), "<TMP>").replace(tmpdir, "<TMP>")
    text = _SHA.sub("<SHA>", text)
    text = _SHORT_SHA.sub("<SHA>", text)
    text = _TS.sub("<TS>", text)
    text = text.replace(socket.gethostname(), "<HOST>")
    text = re.sub(r"\bpid[= ]\d+", "pid=<PID>", text)
    text = re.sub(r"\bprocess \d+", "process <PID>", text)
    return text


def run_cli(argv, repo, tmpdir):
    """Call the CLI in-process and capture (exit code, stdout, stderr)."""
    from sdd_runner.__main__ import main
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        try:
            code = main(argv)
        except SystemExit as exc:                 # argparse errors exit rather than return
            code = exc.code if isinstance(exc.code, int) else 2
    return (code,
            normalize(out.getvalue(), repo, tmpdir),
            normalize(err.getvalue(), repo, tmpdir))


def render(code, stdout, stderr):
    return ("exit: %s\n--- stdout ---\n%s--- stderr ---\n%s" % (code, stdout, stderr))


def _git(repo, *args):
    return subprocess.run(["git", "-C", repo] + list(args), check=True,
                          capture_output=True, text=True).stdout.strip()


# --- scenario builders -------------------------------------------------------
# Each returns (repo, argv). The tmpdir is supplied by the caller so the
# normalizer can scrub it.

def sc_dry_run(tmp):
    repo, feature = support.make_repo(tmp)
    return repo, ["--repo", repo, "--feature", feature, "--dry-run"]


def sc_dry_run_adopt(tmp):
    repo, feature, _info = support.make_adopted_repo(tmp)
    return repo, ["--repo", repo, "--feature", feature, "--dry-run", "--adopt"]


def sc_refusal_default_branch(tmp):
    repo, feature = support.make_repo(tmp)
    _git(repo, "checkout", "-q", "master" if _has(repo, "master") else "-")
    return repo, ["--repo", repo, "--feature", feature, "--dry-run"]


def _has(repo, branch):
    try:
        _git(repo, "rev-parse", "--verify", branch)
        return True
    except subprocess.CalledProcessError:
        return False


def sc_refusal_dirty_tree(tmp):
    repo, feature = support.make_repo(tmp)
    with open(os.path.join(repo, "stray.txt"), "w", encoding="utf-8") as fh:
        fh.write("uncommitted\n")
    return repo, ["--repo", repo, "--feature", feature, "--dry-run"]


def sc_refusal_status_not_ready(tmp):
    repo, feature = support.make_repo(tmp, spec=support.SPEC.replace("Ready", "Draft"))
    return repo, ["--repo", repo, "--feature", feature, "--dry-run"]


def sc_refusal_outside_spec_trail(tmp):
    repo, _feature = support.make_repo(tmp)
    return repo, ["--repo", repo, "--feature", "specs", "--dry-run"]


def sc_refusal_features_root(tmp):
    repo, _feature = support.make_repo(tmp)
    return repo, ["--repo", repo, "--feature", "specs/features", "--dry-run"]


def sc_refusal_adopt_not_needed(tmp):
    repo, feature = support.make_repo(tmp)          # status is Ready
    return repo, ["--repo", repo, "--feature", feature, "--dry-run", "--adopt"]


def sc_backend_precondition(tmp):
    repo, feature = support.make_repo(tmp)
    return repo, ["--repo", repo, "--feature", feature,
                  "--backend", "stub", "--stub-script", "/nonexistent.json"]


def sc_stub_script_wrong_backend(tmp):
    repo, feature = support.make_repo(tmp)
    return repo, ["--repo", repo, "--feature", feature,
                  "--backend", "codex", "--stub-script", "/x.json"]


def sc_unresumable_state(tmp):
    repo, feature = support.make_repo(tmp)
    with open(os.path.join(feature, "ORCHESTRATION.md"), "w", encoding="utf-8") as fh:
        fh.write("# Orchestration: garbage\n\nnot a valid state document\n")
    return repo, ["--repo", repo, "--feature", feature, "--dry-run"]


# --- loop-driven scenarios (scripted stub, deterministic) --------------------

def _script(tmp, payload, name="script.json"):
    import json
    path = os.path.join(tmp, name)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh)
    return path


def sc_core_complete(tmp):
    """A converging two-task run: implemented, approved, finalized."""
    repo, feature = support.make_repo(tmp)
    script = _script(tmp, ([support.fixture("worker_done.md"), support.approve_block()] * 2)
                     + support.finalization_flat())
    return repo, ["--repo", repo, "--feature", feature, "--backend", "stub",
                  "--stub-script", script, "--baseline", "true"]


def sc_budget_exhausted(tmp):
    """The same run with the budget clamped below what one task costs."""
    repo, feature = support.make_repo(tmp)
    script = _script(tmp, ([support.fixture("worker_done.md"), support.approve_block()] * 2)
                     + support.finalization_flat())
    return repo, ["--repo", repo, "--feature", feature, "--backend", "stub",
                  "--stub-script", script, "--baseline", "true",
                  "--max-delegations", "1"]


def _converged_state(tmp):
    """Run to DONE once, and hand back the repo, argv and the state file it left."""
    repo, feature = support.make_repo(tmp)
    script = _script(tmp, ([support.fixture("worker_done.md"), support.approve_block()] * 2)
                     + support.finalization_flat())
    argv = ["--repo", repo, "--feature", feature, "--backend", "stub",
            "--stub-script", script, "--baseline", "true"]
    run_cli(argv, repo, tmp)
    return repo, argv, os.path.join(feature, "ORCHESTRATION.md")


def sc_reentry_after_done(tmp):
    """A finished run is not resumable: there is nothing left to do."""
    repo, argv, _state = _converged_state(tmp)
    return repo, argv


def sc_concurrent_run(tmp):
    """An ACTIVE state file owned by a LIVE pid on this host refuses a second runner.

    The pid recorded is this very process, so `_pid_alive` is true by
    construction and the scenario is deterministic rather than racy.
    """
    repo, argv, state_path = _converged_state(tmp)
    with open(state_path, encoding="utf-8") as fh:
        text = fh.read()
    # The result lives in the `## Run result` section body; the owner fields are
    # lowercase `State` lines. Both spellings come from `state.Orchestration`.
    text = text.replace("## Run result\n\nDONE\n", "## Run result\n\nACTIVE\n", 1)
    text = re.sub(r"^- runner host: .*$", "- runner host: %s" % socket.gethostname(),
                  text, count=1, flags=re.M)
    text = re.sub(r"^- runner pid: .*$", "- runner pid: %d" % os.getpid(),
                  text, count=1, flags=re.M)
    with open(state_path, "w", encoding="utf-8") as fh:
        fh.write(text)
    return repo, argv


def sc_human_escalation(tmp):
    """A worker BLOCKED on a human-gated question pauses the run."""
    repo, feature = support.make_repo(tmp)
    script = _script(tmp, [support.fixture("worker_blocked_human.md")])
    return repo, ["--repo", repo, "--feature", feature, "--backend", "stub",
                  "--stub-script", script, "--baseline", "true"]


def sc_cap_abort(tmp):
    """A reviewer that keeps rejecting without resolving anything hits the streak cap."""
    repo, feature = support.make_repo(tmp)
    script = _script(tmp, [support.fixture("worker_done.md"),
                           support.fixture("reviewer_reject.md")] * 8)
    return repo, ["--repo", repo, "--feature", feature, "--backend", "stub",
                  "--stub-script", script, "--baseline", "true",
                  "--max-iterations", "1", "--max-delegations", "40"]


SCENARIOS = {
    "dry-run": sc_dry_run,
    "dry-run-adopt": sc_dry_run_adopt,
    "refusal-default-branch": sc_refusal_default_branch,
    "refusal-dirty-tree": sc_refusal_dirty_tree,
    "refusal-status-not-ready": sc_refusal_status_not_ready,
    "refusal-outside-spec-trail": sc_refusal_outside_spec_trail,
    "refusal-features-root": sc_refusal_features_root,
    "refusal-adopt-not-needed": sc_refusal_adopt_not_needed,
    "backend-precondition": sc_backend_precondition,
    "stub-script-wrong-backend": sc_stub_script_wrong_backend,
    "unresumable-state": sc_unresumable_state,
    "core-complete": sc_core_complete,
    "budget-exhausted": sc_budget_exhausted,
    "reentry-after-done": sc_reentry_after_done,
    "concurrent-run": sc_concurrent_run,
    "human-escalation": sc_human_escalation,
    "cap-abort": sc_cap_abort,
}


def capture(name):
    build = SCENARIOS[name]
    with tempfile.TemporaryDirectory() as tmp:
        repo, argv = build(tmp)
        code, out, err = run_cli(argv, repo, tmp)
        return render(code, out, err)
