"""Golden CLI transcripts — spec 042 T001/T019, decided by D007.

AC-008 requires the CLI's observable behaviour to be byte-identical across the
refactor. The 276 tests assert the LOOP's behaviour; none of them asserts a byte
of what the CLI prints, and FR-007 requires the dry-run rendering to survive
unchanged. So an oracle is recorded here (D007).

NOT ALL OF IT IS A PRE-REFACTOR ORACLE, and the difference is the whole point of
D007: a transcript captured after the refactor proves only that the refactor
agrees with itself. Seventeen scenarios were captured at T001 against the
pre-refactor code, before the first implementation task touched anything. The
other thirteen were added later, against the refactored code — `internal-error`
and `dry-run-contradiction` during the review rounds, `audit-unavailable` with
D015, and the ten `refusal-*` gate conditions with CONF-003, which added coverage
rather than narrowing AC-008's "each gate refusal".

What gives those thirteen a real "before" side is a separate artifact: eleven
`<scenario>.main.txt` files, reproduced from a temporary extraction of `main` at
`141638b` and labelled retrospective. Nine of the ten gate conditions reproduce
byte-for-byte; `refusal-baseline-unavailable` is `DIFF-003` (D018) and
`audit-unavailable` is `DIFF-002` (D015). `test_main_baselines` is the guard, and
D007 carries the full provenance split (`conformance:CONF-006`).

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


def sc_dry_run_contradiction(tmp):
    """A dry run does not validate backend-exclusive options, because it resolves
    no backend — and this transcript pins that it still does not.

    It briefly did: repairing domain:DOM-013 moved the check ahead of the dry-run
    branch and turned this exit `0` into an exit `14`. That widened observable
    behaviour, which is the one thing this feature promised not to do, so it was
    reverted and spec 042's D011 is Superseded. The scenario stays: what it now guards is the
    baseline, and it is the transcript that would catch the same widening being
    reintroduced.

    The same request WITHOUT `--dry-run` is refused — see `stub-script-wrong-backend`.
    The pair is the point: validation applies where dispatch happens.
    """
    repo, feature = support.make_repo(tmp)
    return repo, ["--repo", repo, "--feature", feature, "--dry-run",
                  "--backend", "claude", "--stub-script", _script(tmp, [])]


def sc_internal_error(tmp):
    """The catch-all path, which no transcript covered — security:SEC-004 / DOM-006.

    `Loop.run` is patched to raise, which is the only deterministic way to reach
    the handler from the CLI. The patch is undone before the scenario returns, so
    it cannot leak into another capture.
    """
    from sdd_runner import loop as loop_mod
    repo, feature = support.make_repo(tmp)
    # A valid script: the backend must resolve, or the run refuses before the
    # handler under test is ever reached.
    argv = ["--repo", repo, "--feature", feature, "--backend", "stub",
            "--stub-script", _script(tmp, [support.fixture("worker_done.md")]),
            "--baseline", "true"]

    original = loop_mod.Loop.run

    def boom(self):
        raise RuntimeError("deliberate failure for the internal-error transcript")

    loop_mod.Loop.run = boom
    try:
        code, out, err = run_cli(argv, repo, tmp)
    finally:
        loop_mod.Loop.run = original
    return (repo, argv), (code, out, err)


def sc_audit_unavailable(tmp):
    """A converged run whose transcript cannot be written — spec 042 D015.

    **Retrospective baseline, and labelled as one.** This scenario was not
    captured before the refactor with the other seventeen; it was found in round 4
    and its `main` behaviour was reproduced afterwards from a temporary extraction
    of `main`: exit **1**, empty stdout, a raw `IsADirectoryError` traceback on
    stderr, because the first `log.emit` raised and the handler's second `emit`
    raised again. Pretending it was recorded at T001 would be the kind of tidy
    history this feature has twice refused to write.

    What it pins now is the *authorised* replacement (AC-008's second permitted
    difference): a stable diagnostic and exit 70 instead of a traceback and exit 1.
    """
    repo, feature = support.make_repo(tmp)
    script = _script(tmp, ([support.fixture("worker_done.md"), support.approve_block()] * 2)
                     + support.finalization_flat())
    os.mkdir(os.path.join(feature, "run.jsonl"))
    return repo, ["--repo", repo, "--feature", feature, "--backend", "stub",
                  "--stub-script", script, "--baseline", "true"]


# --- one scenario per gate.check terminal condition (spec 042 CONF-003) -------
# Every one drives the real CLI through the real gate. None calls `gate.check`
# directly and none constructs an expected refusal by hand: a transcript that
# does not exercise the path proves nothing about the path.

def sc_refusal_feature_folder_missing(tmp):
    repo, _feature = support.make_repo(tmp)
    return repo, ["--repo", repo, "--feature", "specs/features/999-does-not-exist",
                  "--dry-run"]


def sc_refusal_spec_missing(tmp):
    repo, feature = support.make_repo(tmp)
    os.remove(os.path.join(feature, "SPEC.md"))
    _git(repo, "add", "-A"); _git(repo, "commit", "-qm", "drop SPEC.md")
    return repo, ["--repo", repo, "--feature", feature, "--dry-run"]


def sc_refusal_tasks_missing(tmp):
    repo, feature = support.make_repo(tmp)
    os.remove(os.path.join(feature, "TASKS.md"))
    _git(repo, "add", "-A"); _git(repo, "commit", "-qm", "drop TASKS.md")
    return repo, ["--repo", repo, "--feature", feature, "--dry-run"]


def sc_refusal_status_unreadable(tmp):
    """A `## Status` section whose line states no lifecycle status at all.

    This condition is the runner's alone (spec 041 D011): the skill path is
    model-mediated and reads any dialect, so it never needs to say it could not
    read one. This parser does.
    """
    spec = support.SPEC.replace("## Status\n\nReady", "## Status\n\n| state | who |")
    repo, feature = support.make_repo(tmp, spec=spec)
    return repo, ["--repo", repo, "--feature", feature, "--dry-run"]


def sc_refusal_open_questions(tmp):
    spec = support.SPEC.replace("- ~~OQ-1~~ **Resolved.**",
                                "- OQ-1: which currency does the total use?")
    repo, feature = support.make_repo(tmp, spec=spec)
    return repo, ["--repo", repo, "--feature", feature, "--dry-run"]


def sc_refusal_not_a_git_repository(tmp):
    """A spec trail with no repository around it."""
    repo = os.path.join(tmp, "bare")
    feature = os.path.join(repo, "specs", "features", "900-fixture")
    os.makedirs(feature)
    for name, text in (("SPEC.md", support.SPEC), ("TASKS.md", support.TASKS)):
        with open(os.path.join(feature, name), "w", encoding="utf-8") as fh:
            fh.write(text)
    return repo, ["--repo", repo, "--feature", feature, "--dry-run"]


def sc_refusal_already_adopted(tmp):
    """`--adopt` over a feature that already has a state document."""
    repo, feature, _info = support.make_adopted_repo(tmp)
    with open(os.path.join(feature, "ORCHESTRATION.md"), "w", encoding="utf-8") as fh:
        fh.write("# Orchestration: prior run\n\n## State\n\n- writer: sdd_runner\n\n")
    return repo, ["--repo", repo, "--feature", feature, "--dry-run", "--adopt"]


def sc_refusal_baseline_unavailable(tmp):
    repo, feature = support.make_repo(tmp)
    return repo, ["--repo", repo, "--feature", feature, "--dry-run",
                  "--baseline", "definitely-not-a-real-binary-042"]


def sc_refusal_red_baseline(tmp):
    repo, feature = support.make_repo(tmp)
    return repo, ["--repo", repo, "--feature", feature, "--dry-run", "--baseline", "false"]


def sc_refusal_baseline_mutates_the_tree(tmp):
    """A baseline that passes and leaves the tree dirty is refused just the same."""
    repo, feature = support.make_repo(tmp)
    script = os.path.join(tmp, "mutate.py")
    with open(script, "w", encoding="utf-8") as fh:
        fh.write("import pathlib; pathlib.Path('mutated-by-the-baseline.txt').write_text('x')\n")
    return repo, ["--repo", repo, "--feature", feature, "--dry-run",
                  "--baseline", "%s %s" % (sys.executable, script)]


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
    "dry-run-contradiction": sc_dry_run_contradiction,
    "internal-error": sc_internal_error,
    "audit-unavailable": sc_audit_unavailable,
    "refusal-feature-folder-missing": sc_refusal_feature_folder_missing,
    "refusal-spec-missing": sc_refusal_spec_missing,
    "refusal-tasks-missing": sc_refusal_tasks_missing,
    "refusal-status-unreadable": sc_refusal_status_unreadable,
    "refusal-open-questions": sc_refusal_open_questions,
    "refusal-not-a-git-repository": sc_refusal_not_a_git_repository,
    "refusal-already-adopted": sc_refusal_already_adopted,
    "refusal-baseline-unavailable": sc_refusal_baseline_unavailable,
    "refusal-red-baseline": sc_refusal_red_baseline,
    "refusal-baseline-mutates": sc_refusal_baseline_mutates_the_tree,
}

# Scenarios whose builder runs the CLI itself, because reaching the path needs a
# patch that must not outlive the capture.
SELF_RUNNING = {"internal-error"}


def capture(name):
    build = SCENARIOS[name]
    with tempfile.TemporaryDirectory() as tmp:
        if name in SELF_RUNNING:
            _repo_argv, (code, out, err) = build(tmp)
            return render(code, out, err)
        repo, argv = build(tmp)
        code, out, err = run_cli(argv, repo, tmp)
        return render(code, out, err)
