"""CLI — spec 040 FR-001, FR-007, FR-013.

Non-interactive by construction: no TTY required, stdin never read, nothing ever
prompted. A scheduler branches on the exit code alone.

`--notify` is executed WITHOUT a shell, with a fixed argument vector, and the
event is delivered as JSON on stdin. No agent-authored text ever reaches a shell
string (spec 040 NFR: Security).
"""

import argparse
import json
import os
import socket
import subprocess
import sys
import time

from . import exits, gate, resume, state as state_mod
from .backends import BackendPrecondition, resolve
from .log import RunLog
from .loop import Loop
from .policy import FEATURES_ROOT  # noqa: F401


def build_parser():
    p = argparse.ArgumentParser(
        prog="python3 -m sdd_runner",
        description="Phase-2 executor for the SDD autonomous loop (spec 040).")
    p.add_argument("--feature", required=True, help="specs/features/<nnn>-<name>")
    p.add_argument("--repo", default=".", help="repository root (default: cwd)")
    p.add_argument("--backend", default="claude", choices=("stub", "claude", "codex"))
    p.add_argument("--model", default=None, help="model pin, required by the codex backend")
    p.add_argument("--max-iterations", type=int, default=3)
    p.add_argument("--max-delegations", type=int, default=None)
    p.add_argument("--baseline", default=None,
                   help="PLAN-mandated verification command. Checked at the entry gate and "
                        "again at finalization; without it, 031's second DONE condition is "
                        "recorded as unobserved rather than assumed")
    p.add_argument("--notify", default=None,
                   help="command executed (without a shell) on escalation, abort and completion")
    p.add_argument("--allow-unverified-backend", action="store_true",
                   help="permit a backend whose provider flags have never been verified")
    p.add_argument("--stub-script", default=None,
                   help="JSON file of scripted responses for --backend stub: a list, or an "
                        "object keyed by agent name. The only way to exercise a full run "
                        "end to end without a provider.")
    p.add_argument("--adopt", action="store_true",
                   help="first entry on a feature already In Progress (spec 041): requires a "
                        "fully clean tree and a computable inherited record; the gate mirrors "
                        "the skill, and --dry-run prints what would be inherited")
    p.add_argument("--dry-run", action="store_true",
                   help="run the entry gate, print the plan and the budget, dispatch nothing")
    return p



def _resolve_feature(repo, requested):
    """Resolve `--feature` and prove it lands inside `specs/features/`.

    Returns (feature_dir, refusal_message). The check runs BEFORE any write —
    the runner puts `ORCHESTRATION.md` and `run.jsonl` in this directory, claims
    it with an exclusive create, and fingerprints the repository around it.

    Every path is resolved through symlinks first (AUDIT-5, AC-016). A prefix
    comparison on the requested path sees only the name: `specs/features/x` can
    be a symlink to anywhere, and `commonpath` on the unresolved path would call
    it contained. `os.path.commonpath` on the RESOLVED paths is what actually
    answers the question, and it is path-aware — `/repo/specs/features-old` is
    not inside `/repo/specs/features`, which a string prefix would get wrong.
    """
    features_root = os.path.realpath(os.path.join(repo, FEATURES_ROOT))
    if not os.path.isdir(features_root):
        return None, ("[GATE] refused: %s does not exist in this repository\n"
                      "  remediation: run from a repository with an SDD spec trail, "
                      "or pass --repo" % FEATURES_ROOT)

    candidate = requested if os.path.isabs(requested) else os.path.join(repo, requested)
    resolved = os.path.realpath(candidate)

    def refuse(detail):
        return ("[GATE] refused: --feature must resolve to a directory inside %s\n"
                "  requested: %s\n"
                "  resolves to: %s\n"
                "  detail: %s\n"
                "  remediation: pass a feature folder under %s, or set --repo to the "
                "repository that contains it" % (FEATURES_ROOT, requested, resolved,
                                                 detail, FEATURES_ROOT))

    if resolved == features_root:
        return None, refuse("that is the features root itself, not a feature")
    try:
        contained = os.path.commonpath([features_root, resolved]) == features_root
    except ValueError:                      # different drives on Windows
        contained = False
    if not contained:
        return None, refuse("it lands outside the spec trail")
    return resolved, None


def _notifier(command):
    if not command:
        return None

    argv = command.split() if isinstance(command, str) else list(command)

    def send(event):
        payload = json.dumps(event, ensure_ascii=False, sort_keys=True)
        try:
            subprocess.run(argv, input=payload, text=True, shell=False, timeout=30)
        except Exception as exc:                       # a broken sink never kills the run
            print("[notify] sink failed: %s" % exc, file=sys.stderr)

    return send


def main(argv=None):
    args = build_parser().parse_args(argv)
    repo = os.path.realpath(args.repo)
    feature_dir, refusal = _resolve_feature(repo, args.feature)
    if refusal:
        print(refusal, file=sys.stderr)
        return exits.GATE_REFUSED

    # `gate.check` has always distinguished first entry from re-entry, and the CLI
    # never told it which this was — harmless while `In Progress` was a first-entry
    # status, fatal once spec 041 narrowed first entry to `Ready`: every adopted run
    # became a one-shot. The state file is what makes a run re-entrant, so it is what
    # answers the question (spec 041 T015 / CONF-041-01).
    state_path = os.path.join(feature_dir, "ORCHESTRATION.md")
    first_entry = not os.path.exists(state_path)
    if not first_entry and not args.adopt:
        # Existence is not authentication. 031: "a missing/malformed/mismatched state
        # file cannot authenticate re-entry and must fail the entry gate rather than
        # being guessed back into shape." `Loop` enforces that, but a dry run returns
        # before `Loop` exists, so it used to report a pass for a document that could
        # never be resumed (spec 041 T020 / CONF-041-02).
        #
        # Only for a genuine RE-ENTRY. `--adopt` over an existing document is a
        # statement about intent, not about that document: the answer is "a run is
        # resumed, never re-adopted" whether the file is valid, stale or foreign, so
        # the gate's `already adopted or entered` owns it and authenticating first
        # would bury that answer under a different condition (T024 / R3-02).
        try:
            doc = state_mod.Orchestration.load(state_path)
        except (OSError, UnicodeDecodeError, ValueError) as exc:
            # A state file that cannot even be read is still a refusal with a code,
            # never a traceback: a scheduler branches on the exit code alone (T026).
            print("[GATE] refused: %s cannot be read: %s\n  remediation: inspect the file, or "
                  "archive it and start a fresh run" % (state_path, exc), file=sys.stderr)
            return exits.STATE_UNRESUMABLE
        try:
            resume.inspect(doc, state_path, args.max_iterations, socket.gethostname())
        except resume.ConcurrentRun as exc:
            print("[GATE] refused: %s" % exc, file=sys.stderr)
            return exits.CONCURRENT_RUN
        except resume.UnresumableState as exc:
            print("[GATE] refused: %s\n  remediation: %s" % (exc.reason, exc.remediation),
                  file=sys.stderr)
            return exits.STATE_UNRESUMABLE

    refusals = gate.check(repo, feature_dir,
                          baseline_cmd=args.baseline.split() if args.baseline else None,
                          first_entry=first_entry, adopt=args.adopt)
    if refusals:
        for r in refusals:
            print(r.render(), file=sys.stderr)
        return exits.GATE_REFUSED

    from . import tasks as tasks_mod
    from .budget import default_cap

    with open(os.path.join(feature_dir, "TASKS.md"), encoding="utf-8") as fh:
        tasks_text = fh.read()
    pending = tasks_mod.independently_runnable(tasks_text)
    cap = args.max_delegations or default_cap(len(pending))

    # A dry run dispatches nothing, so it must not require a dispatchable backend
    # (FR-001). Resolving one first made the flag unusable on exactly the machine
    # AC-010 says must work: no Agent SDK, no Codex CLI.
    if args.dry_run:
        print("feature:         %s" % feature_dir)
        print("backend:         %s (not resolved: a dry run dispatches nothing)"
              % args.backend)
        print("unchecked tasks: %d" % len(pending))
        print("max-iterations:  %d" % args.max_iterations)
        print("max-delegations: %d" % cap)
        print("entry:           %s" % ("adopt" if args.adopt else "ready"))
        if args.adopt:
            record = gate.inherited_record(repo, feature_dir)
            print("adoption baseline commit: %s" % record.baseline)
            print("adoption diff base:       %s (against %s)"
                  % (record.diff_base, record.default_branch))
            print("inherited tasks: %d (verification not observed by this run)"
                  % len(record.checked))
            for task_id, verify in record.checked:
                print("  %s  inherited  verify: %s" % (task_id, verify[:70]))
        for t in pending:
            print("  %s  %s" % (t.id, t.title[:88]))
        print("dry run: nothing dispatched.")
        return exits.OK

    if args.stub_script and args.backend != "stub":
        print("[BACKEND] --stub-script applies to --backend stub, not %r" % args.backend,
              file=sys.stderr)
        return exits.BACKEND_PRECONDITION

    try:
        if args.backend == "stub":
            from .backends.stub import load_script
            kwargs = ({"script": load_script(args.stub_script)} if args.stub_script
                      else {"strict": False})
        else:
            kwargs = {"model": args.model, "cwd": repo}
        backend = resolve(args.backend, allow_unverified=args.allow_unverified_backend,
                          **kwargs)
    except BackendPrecondition as exc:
        print("[BACKEND] %s" % exc, file=sys.stderr)
        return exits.BACKEND_PRECONDITION

    log = RunLog(os.path.join(feature_dir, "run.jsonl"), clock=time.time)
    notify = _notifier(args.notify)
    loop = Loop(repo, feature_dir, backend, log,
                max_iterations=args.max_iterations, max_delegations=args.max_delegations,
                notify=notify,
                baseline_cmd=args.baseline.split() if args.baseline else None,
                adopt=args.adopt)
    try:
        outcome = loop.run()
    except Exception as exc:                            # never a silent crash
        log.emit("internal-error", detail=str(exc))
        print("[INTERNAL] %s" % exc, file=sys.stderr)
        return exits.INTERNAL_ERROR

    print("run result: %s (%s)" % (outcome.result, exits.NAMES.get(outcome.code, outcome.code)))
    print("reason:     %s" % outcome.reason)
    # Every blocking outcome carries a remediation, and the operator never saw
    # it: the CLI printed what was wrong and not what to do about it.
    if outcome.remediation:
        print("remediation: %s" % outcome.remediation)
    if notify and outcome.code != exits.HUMAN_ESCALATION:
        notify({"event": "run-finished", "result": outcome.result,
                "code": outcome.code, "reason": outcome.reason})
    return outcome.code


if __name__ == "__main__":
    sys.exit(main())
