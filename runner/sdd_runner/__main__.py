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
import subprocess
import sys
import time

from . import exits, gate
from .backends import BackendPrecondition, resolve
from .log import RunLog
from .loop import Loop


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
    p.add_argument("--dry-run", action="store_true",
                   help="run the entry gate, print the plan and the budget, dispatch nothing")
    return p


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
    repo = os.path.abspath(args.repo)
    feature_dir = args.feature if os.path.isabs(args.feature) else os.path.join(repo, args.feature)

    refusals = gate.check(repo, feature_dir,
                          baseline_cmd=args.baseline.split() if args.baseline else None)
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
                baseline_cmd=args.baseline.split() if args.baseline else None)
    try:
        outcome = loop.run()
    except Exception as exc:                            # never a silent crash
        log.emit("internal-error", detail=str(exc))
        print("[INTERNAL] %s" % exc, file=sys.stderr)
        return exits.INTERNAL_ERROR

    print("run result: %s (%s)" % (outcome.result, exits.NAMES.get(outcome.code, outcome.code)))
    print("reason:     %s" % outcome.reason)
    if notify and outcome.code != exits.HUMAN_ESCALATION:
        notify({"event": "run-finished", "result": outcome.result,
                "code": outcome.code, "reason": outcome.reason})
    return outcome.code


if __name__ == "__main__":
    sys.exit(main())
