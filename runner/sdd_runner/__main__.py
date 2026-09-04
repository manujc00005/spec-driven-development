"""CLI — spec 040 FR-001, FR-007, FR-013; reduced to an adapter by spec 042 T008.

Non-interactive by construction: no TTY required, stdin never read, nothing ever
prompted. A scheduler branches on the exit code alone.

`--notify` is executed WITHOUT a shell, with a fixed argument vector, and the
event is delivered as JSON on stdin. No agent-authored text ever reaches a shell
string (spec 040 NFR: Security).

**This module makes no protocol decision.** It parses argv into a `RunRequest`,
calls the public `run` interface once, renders the `RunOutcome`, and returns the exit code.
First-entry determination, resume authentication, the entry gate, the budget
formula and backend resolution used to live here; spec 042 moved them behind the
public interface, where a second caller can reach them without re-deriving them.
"""

import argparse
import json
import subprocess
import sys

from . import RunRequest, run


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


def render_plan(plan, out=None):
    """The dry-run projection. The core computes it; this decides how it looks."""
    write = (out or sys.stdout).write
    write("feature:         %s\n" % plan.feature_dir)
    write("backend:         %s (not resolved: a dry run dispatches nothing)\n" % plan.backend)
    write("unchecked tasks: %d\n" % plan.unchecked)
    write("max-iterations:  %d\n" % plan.max_iterations)
    write("max-delegations: %d\n" % plan.max_delegations)
    write("entry:           %s\n" % plan.entry)
    if plan.entry == "adopt":
        write("adoption baseline commit: %s\n" % plan.adoption_baseline)
        write("adoption diff base:       %s (against %s)\n"
              % (plan.adoption_diff_base, plan.default_branch))
        write("inherited tasks: %d (verification not observed by this run)\n"
              % len(plan.inherited))
        for task_id, verify in plan.inherited:
            write("  %s  inherited  verify: %s\n" % (task_id, verify[:70]))
    for task_id, title in plan.tasks:
        write("  %s  %s\n" % (task_id, title[:88]))
    write("dry run: nothing dispatched.\n")


def render(outcome):
    """Everything the operator sees, and which stream it goes on.

    Diagnostics and the terminal report are **independent**. A diagnostic says
    something went wrong alongside the run; `loop_completed` says whether there is
    a run to report. Coupling them cost a converged run its result line once
    already, and the coupling lived here.
    """
    # Always, whatever else is true of the outcome.
    for diagnostic in outcome.diagnostics:
        print(diagnostic.render(), file=sys.stderr)
    for line in outcome.gate.render():
        print(line, file=sys.stderr)
    if outcome.plan is not None:
        render_plan(outcome.plan)
        return
    if outcome.loop_completed:
        print("run result: %s (%s)" % (outcome.result, outcome.exit_name))
        print("reason:     %s" % outcome.reason)
        # Every blocking outcome carries a remediation, and the operator never saw
        # it: the CLI printed what was wrong and not what to do about it.
        if outcome.remediation:
            print("remediation: %s" % outcome.remediation)


def main(argv=None):
    args = build_parser().parse_args(argv)
    notify = _notifier(args.notify)
    outcome = run(RunRequest(
        repo=args.repo, feature=args.feature, backend=args.backend, model=args.model,
        max_iterations=args.max_iterations, max_delegations=args.max_delegations,
        baseline=args.baseline.split() if args.baseline else None,
        notify=notify, allow_unverified_backend=args.allow_unverified_backend,
        stub_script=args.stub_script, adopt=args.adopt, dry_run=args.dry_run,
    ))
    render(outcome)
    if notify and outcome.loop_completed and outcome.gate.passed \
            and not outcome.awaiting_human:
        notify({"event": "run-finished", "result": outcome.result,
                "code": outcome.exit_code, "reason": outcome.reason})
    return outcome.exit_code


if __name__ == "__main__":
    sys.exit(main())
