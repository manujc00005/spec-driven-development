"""Capture `main`'s side of the ten gate-refusal conditions — spec 042 CONF-006, D018.

The ten `refusal-*` scenarios were added by CONF-003 to make AC-008's *"each gate
refusal"* true rather than narrower. They were captured **after** the refactor, so
until this script ran they had no "before" side and the claim that behaviour was
preserved could not be checked against anything (`maintainer:MNT-010`'s defect,
one corpus over).

Method, and why each part of it:

  * `main` is read through `git archive main | tar -x` into a temporary directory.
    No checkout, no reset, no stash: the working tree is never touched, so the
    capture cannot be contaminated by the branch it is meant to be compared with.
  * The scenario builders and the normalizer come from **this branch's**
    `tests/contract/golden.py`, copied into the extraction. They define what a
    scenario *is*; taking them from `main` would compare two different fixtures.
    The fixtures themselves are built by `runner/tests/support.py`, which is
    byte-identical between `main` and this branch — asserted below, because if it
    ever stops being true the comparison stops meaning anything.
  * The CLI is invoked as a real child process, so the exit code and both streams
    are the process's own. That is the only way to record `main`'s behaviour on
    `refusal-baseline-unavailable`, where the exception escapes the interpreter
    and there is no return value to capture.

Normalization is deliberately narrow: `golden.normalize` and nothing else, plus
the traceback file frames, which encode this machine's paths and the extraction
directory. Every artifact declares in its own header what was applied to it.

Usage:  python3 capture_main_baselines.py [--commit main] [--check]

`--check` re-captures and compares against what is on disk without writing, which
is how a maintainer verifies the baselines still hold after changing `main`.
"""

import argparse
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
GOLDEN = os.path.join(HERE, "golden")
RUNNER = os.path.join(REPO, "runner")
SUFFIX = ".main.txt"

# Condition per scenario. The names are `gate.check`'s own; `test_gate_refusal_coverage`
# derives the full set from the module's AST, so this table is never the authority
# for which conditions exist — only for which of them this artifact set covers.
TEN = [
    ("refusal-feature-folder-missing",    "feature folder missing"),
    ("refusal-spec-missing",              "SPEC.md missing"),
    ("refusal-tasks-missing",             "TASKS.md missing"),
    ("refusal-status-unreadable",         "status unreadable"),
    ("refusal-open-questions",            "open questions"),
    ("refusal-not-a-git-repository",      "not a git repository"),
    ("refusal-already-adopted",           "already adopted or entered"),
    ("refusal-baseline-unavailable",      "baseline suite unavailable"),
    ("refusal-red-baseline",              "red baseline suite"),
    ("refusal-baseline-mutates",          "baseline suite mutates the tree"),
]

# The one authorised departure, and the decision that authorised it. Anything else
# that diverges is a finding, not a re-record.
DIVERGENT = {"refusal-baseline-unavailable": "DIFF-003"}

_FRAME = re.compile(r'^\s*File "[^"]*", line \d+, in .*\n', re.M)


def _git(*args, cwd=REPO):
    return subprocess.run(["git"] + list(args), cwd=cwd, check=True,
                          capture_output=True, text=True).stdout.strip()


def _extract(commit, dest):
    """Read `commit` into `dest` without touching the working tree."""
    archive = subprocess.run(["git", "archive", commit], cwd=REPO, check=True,
                             capture_output=True)
    subprocess.run(["tar", "-x", "-C", dest], input=archive.stdout, check=True)


def _drop_frames(text):
    """Remove traceback file frames: they encode this machine's paths.

    The exception lines, the source lines and the caret markers are kept verbatim —
    they are what the artifact is for. This follows `audit-unavailable.main.txt`,
    which set the convention.
    """
    return _FRAME.sub("", text)


def _header(scenario, condition, commit, command, framed):
    lines = [
        "# RETROSPECTIVE baseline - `main`'s real output on this path.",
        "# NOT captured at T001: reproduced afterwards from a temporary extraction of",
        "# `main`, for spec 042 conformance:CONF-006 / D018. D007 carries the full",
        "# provenance split of the corpus.",
        "# scenario: %s" % scenario,
        "# condition: %s" % condition,
        "# main-commit: %s" % commit,
        "# command: %s" % command,
        "# fixture: golden.SCENARIOS[%r], built by runner/tests/support.py, which is" % scenario,
        "#   byte-identical between `main` and this branch.",
        "# normalization: golden.normalize only - <REPO>, <TMP>, <SHA>, <TS>, <HOST>,",
        "#   <PID>. No semantic difference is normalized.",
    ]
    if framed:
        lines.append("#   Traceback `File \"...\", line N, in f` frames dropped: they encode this")
        lines.append("#   machine's paths and the extraction directory. Exception lines, source")
        lines.append("#   lines and caret markers are verbatim.")
    if scenario in DIVERGENT:
        lines.append("# relation: DIVERGES from the current side, authorised as %s (D018)."
                     % DIVERGENT[scenario])
    else:
        lines.append("# relation: byte-identical to the current side.")
    return "\n".join(lines) + "\n\n"


def body_of(text):
    """The transcript, with the `#` provenance header stripped."""
    lines = text.splitlines(True)
    i = 0
    while i < len(lines) and lines[i].startswith("#"):
        i += 1
    while i < len(lines) and not lines[i].strip():
        i += 1
    return "".join(lines[i:])


def sha256(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def capture(commit, workdir):
    """Run the ten scenarios through `commit`'s real CLI. Returns [(name, ...)]."""
    extraction = os.path.join(workdir, "main")
    os.makedirs(extraction)
    _extract(commit, extraction)

    mine = os.path.join(RUNNER, "tests", "support.py")
    theirs = os.path.join(extraction, "runner", "tests", "support.py")
    with io.open(mine, encoding="utf-8") as a, io.open(theirs, encoding="utf-8") as b:
        if a.read() != b.read():
            raise SystemExit(
                "runner/tests/support.py differs between %s and this branch: the two "
                "sides would no longer be running the same fixture, and comparing them "
                "would prove nothing. Re-establish the fixture first." % commit)

    # The scenario builders are this branch's: they define what each scenario is.
    contract = os.path.join(extraction, "runner", "tests", "contract")
    os.makedirs(contract, exist_ok=True)
    io.open(os.path.join(contract, "__init__.py"), "w").close()
    shutil.copy(os.path.join(RUNNER, "tests", "contract", "golden.py"), contract)

    root = os.path.join(extraction, "runner")
    sys.path.insert(0, root)
    for name in ("tests", "tests.support", "tests.contract", "tests.contract.golden"):
        sys.modules.pop(name, None)
    from tests.contract import golden

    env = dict(os.environ, PYTHONPATH=root, PYTHONDONTWRITEBYTECODE="1")
    results = []
    for name, condition in TEN:
        with tempfile.TemporaryDirectory() as tmp:
            repo, argv = golden.SCENARIOS[name](tmp)
            proc = subprocess.run([sys.executable, "-m", "sdd_runner"] + argv,
                                  capture_output=True, text=True, env=env, cwd=tmp)
            out = golden.normalize(proc.stdout, repo, tmp)
            err = golden.normalize(proc.stderr, repo, tmp)
            command = " ".join(["python3", "-m", "sdd_runner"] +
                               [golden.normalize(a, repo, tmp) for a in argv])
        framed = "Traceback" in err
        if framed:
            err = _drop_frames(err)
        results.append((name, condition, command, proc.returncode, out, err, framed))
    sys.path.remove(root)
    return results


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--commit", default="main")
    ap.add_argument("--check", action="store_true",
                    help="compare against what is on disk instead of writing")
    args = ap.parse_args(argv)

    commit = _git("rev-parse", args.commit)
    with tempfile.TemporaryDirectory() as workdir:
        results = capture(commit, workdir)

    index, drift = [], []
    for name, condition, command, code, out, err, framed in results:
        text = (_header(name, condition, commit, command, framed) +
                "exit: %s\n--- stdout ---\n%s--- stderr ---\n%s" % (code, out, err))
        path = os.path.join(GOLDEN, name + SUFFIX)
        current = os.path.join(GOLDEN, name + ".txt")
        with io.open(current, encoding="utf-8") as fh:
            now = fh.read()
        if args.check:
            if not os.path.exists(path):
                drift.append("%s: no recorded baseline" % name)
            else:
                with io.open(path, encoding="utf-8") as fh:
                    if body_of(fh.read()) != body_of(text):
                        drift.append("%s: recorded baseline differs from a fresh capture" % name)
        else:
            with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(text)
        index.append({
            "scenario": name,
            "condition": condition,
            "command": command,
            "fixture": "golden.SCENARIOS[%r] via runner/tests/support.py" % name,
            "main_commit": commit,
            "main_exit": code,
            "current_exit": int(now.split("\n", 1)[0].split("exit:")[1].strip()),
            "normalization": ("golden.normalize; traceback file frames dropped"
                              if framed else "golden.normalize"),
            "relation": DIVERGENT.get(name, "identical"),
            "main_sha256": sha256(body_of(text)),
            "current_sha256": sha256(now),
        })

    document = {
        "artifact": "main-side baselines for the ten gate-refusal conditions",
        "spec": "042-canonical-autonomous-core",
        "finding": "conformance:CONF-006",
        "decision": "D018",
        "main_commit": commit,
        "retrospective": True,
        "captured_by": os.path.relpath(os.path.abspath(__file__), REPO),
        "authorised_difference": "DIFF-003",
        "scenarios": index,
    }
    if args.check:
        for line in drift:
            print("DRIFT %s" % line)
        print("checked %d baselines against %s: %s"
              % (len(index), commit[:7], "DRIFT" if drift else "stable"))
        return 1 if drift else 0

    with io.open(os.path.join(GOLDEN, "index.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(document, fh, indent=2, sort_keys=True)
        fh.write("\n")
    for entry in index:
        print("%-38s main=%-3s now=%-3s %s"
              % (entry["scenario"], entry["main_exit"], entry["current_exit"], entry["relation"]))
    print("wrote %d baselines and index.json from %s" % (len(index), commit[:7]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
