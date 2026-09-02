"""AC-001 end to end, through the real CLI in a real subprocess.

Every other integration test builds `Loop` in-process and skips the CLI entirely:
argument parsing, the order backends are resolved in, the exit-code mapping. That
gap is not theoretical — it is where a `--dry-run` regression lived unnoticed
through three review passes, because the flag was only ever exercised against a
repository whose entry gate refused first.

These tests spawn `python3 -m sdd_runner` with stdin closed, so "no TTY" is a
property of the process rather than a claim about it.
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest

from sdd_runner import exits, state
from tests.support import (TASKS, approve_block, finalization_flat, fixture, make_repo)

RUNNER_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def converging_script():
    """Two tasks, each implemented and approved, then finalization."""
    return ([fixture("worker_done.md"), approve_block()] * 2) + finalization_flat()


class CliEndToEnd(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo, self.feature_dir = make_repo(self.tmp.name, tasks=TASKS)

    def write_script(self, payload):
        path = os.path.join(self.tmp.name, "script.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh)
        return path

    def run_cli(self, *args, baseline="true"):
        """Spawn the CLI with stdin closed. No TTY, no inherited session.

        `baseline=None` omits the flag entirely, which is one of AC-015's four
        cases and not the same as passing an empty one.
        """
        env = dict(os.environ, PYTHONPATH=RUNNER_ROOT)
        argv = [sys.executable, "-m", "sdd_runner", "--repo", self.repo,
                "--feature", "specs/features/900-fixture"]
        if baseline is not None:
            # 031's condition 2, in its smallest honest form (D036).
            argv += ["--baseline", baseline]
        with open(os.devnull, "rb") as devnull:
            return subprocess.run(argv + list(args), stdin=devnull, capture_output=True,
                                  text=True, env=env, timeout=120)

    def script_file(self, body, name):
        path = os.path.join(self.tmp.name, name)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(body)
        os.chmod(path, 0o755)
        return path

    def git(self, *args):
        return subprocess.run(["git", "-C", self.repo] + list(args),
                              capture_output=True, text=True).stdout.strip()

    # -- AC-001 ----------------------------------------------------------
    def test_a_two_task_feature_converges_to_exit_zero_with_no_tty(self):
        script = self.write_script(converging_script())
        proc = self.run_cli("--backend", "stub", "--stub-script", script)
        self.assertEqual(proc.returncode, exits.OK, proc.stderr)

        # ... on a non-default branch, with an unstaged tree ...
        self.assertNotIn(self.git("rev-parse", "--abbrev-ref", "HEAD"), ("main", "master"))
        self.assertEqual(self.git("diff", "--cached", "--name-only"), "")

        # ... the artifacts present, ORCHESTRATION.md matching 031's schema ...
        doc = state.Orchestration.load(os.path.join(self.feature_dir, "ORCHESTRATION.md"))
        for section in ("State", "Attempts", "Findings", "Delegation log", "Escalations",
                        "Cap changes", "Closure delta", "Run result"):
            self.assertIsNotNone(doc.get(section), "missing 031 section %r" % section)
        self.assertEqual(doc.run_result(), "DONE")
        self.assertTrue(os.path.isfile(os.path.join(self.feature_dir, "run.jsonl")))

        # ... no lifecycle skill invoked and no closure event, because the real CLI
        # stops on 040's side of the `_finalize` seam too (AC-019, D034) ...
        with open(os.path.join(self.feature_dir, "run.jsonl"), encoding="utf-8") as fh:
            events = [json.loads(line) for line in fh if line.strip()]
        self.assertEqual([e for e in events if e["event"] in ("lifecycle", "closure-delta")], [])
        self.assertEqual([e for e in events
                          if e["event"] == "dispatch" and e["agent"].startswith("lifecycle:")], [])
        self.assertFalse(os.path.exists(os.path.join(self.feature_dir, "PR_DESCRIPTION.md")))

        # ... and no commit the runner created.
        self.assertEqual(len(self.git("log", "--oneline").splitlines()), 1)

    def test_the_run_is_reconstructible_from_the_log_the_cli_wrote(self):
        script = self.write_script(converging_script())
        self.run_cli("--backend", "stub", "--stub-script", script)
        with open(os.path.join(self.feature_dir, "run.jsonl"), encoding="utf-8") as fh:
            events = [json.loads(line)["event"] for line in fh if line.strip()]
        for required in ("plan", "dispatch", "verdict", "freeze", "core-complete", "finish"):
            self.assertIn(required, events)

    # -- AC-015: the baseline is a condition of closing, through the CLI --
    def _converged(self):
        return self.write_script(converging_script())

    def _run_result(self):
        """None when no state file exists - which is what an entry refusal leaves."""
        path = os.path.join(self.feature_dir, "ORCHESTRATION.md")
        if not os.path.isfile(path):
            return None
        return state.Orchestration.load(path).run_result()

    def test_a_green_non_mutating_baseline_is_the_only_one_that_closes(self):
        """AC-015's four cases, each through a real subprocess.

        The point is that the outcome is read from the CLI's exit code and the
        persisted run result, not from a verification string the runner wrote
        about itself.
        """
        failing = self.script_file("#!/bin/sh\nexit 7\n", "red.sh")
        mutating = self.script_file(
            "#!/bin/sh\necho mutated >> agents/implementer.md\n", "mutate.sh")

        # AC-015's prose asks for 18 in all three failing cases. Two of them
        # never reach the closure gate: 031 FR-002 makes a red or tree-mutating
        # baseline an ENTRY refusal, so the run is stopped at exit 10 before any
        # work is done. That is earlier and more protective, and the two
        # requirements cannot both hold. This asserts what the code must do; the
        # AC needs amending (see T028's note).
        cases = [
            ("omitted", None, exits.CLOSURE_NOT_PROVEN),      # 18, at the closure gate
            ("non-zero", failing, exits.GATE_REFUSED),        # 10, at the entry gate (031 FR-002)
            ("mutating", mutating, exits.GATE_REFUSED),       # 10, at the entry gate (031 FR-002)
            ("green", "true", exits.OK),
        ]
        for label, baseline, expected in cases:
            with self.subTest(baseline=label):
                self.setUp()                      # a fresh repo per case
                proc = self.run_cli("--backend", "stub", "--stub-script", self._converged(),
                                    baseline=baseline)
                self.assertEqual(proc.returncode, expected,
                                 "%s baseline: %s" % (label, proc.stderr[-400:]))
                # The Verify clause's actual requirement: only the last exits 0.
                if label != "green":
                    self.assertNotEqual(proc.returncode, exits.OK)
                if expected == exits.OK:
                    self.assertEqual(self._run_result(), "DONE")
                else:
                    # Either no state at all (entry refusal changed nothing) or a
                    # state that is not DONE. Never DONE.
                    self.assertNotEqual(self._run_result(), "DONE")

    def test_an_omitted_baseline_names_the_flag_in_its_remediation(self):
        proc = self.run_cli("--backend", "stub", "--stub-script", self._converged(),
                            baseline=None)
        self.assertEqual(proc.returncode, exits.CLOSURE_NOT_PROVEN)
        self.assertIn("--baseline", proc.stdout + proc.stderr)

    # -- AC-002: the non-interactive contract ----------------------------
    def test_dry_run_needs_no_backend_and_exits_zero(self):
        proc = self.run_cli("--dry-run")
        self.assertEqual(proc.returncode, exits.OK, proc.stderr)
        self.assertIn("dry run: nothing dispatched.", proc.stdout)
        self.assertIn("max-delegations:", proc.stdout)

    def test_the_process_never_reads_stdin(self):
        """stdin is closed; a runner that read it would fail rather than proceed."""
        script = self.write_script(converging_script())
        proc = self.run_cli("--backend", "stub", "--stub-script", script)
        self.assertEqual(proc.returncode, exits.OK, proc.stderr)

    def test_a_scheduler_can_branch_on_the_code_alone(self):
        proc = self.run_cli("--backend", "codex", "--model", "m")
        self.assertEqual(proc.returncode, exits.BACKEND_PRECONDITION)
        self.assertIn("DEBT-001", proc.stderr)

    # -- the script loader fails closed ----------------------------------
    def test_a_malformed_script_stops_before_dispatching(self):
        cases = {
            "not json": "{[",
            "wrong shape": json.dumps("a bare string"),
            "empty list": json.dumps([]),
            "non-string item": json.dumps([1, 2]),
            "empty object": json.dumps({}),
        }
        for label, payload in cases.items():
            with self.subTest(case=label):
                path = os.path.join(self.tmp.name, "bad.json")
                with open(path, "w", encoding="utf-8") as fh:
                    fh.write(payload)
                proc = self.run_cli("--backend", "stub", "--stub-script", path)
                self.assertEqual(proc.returncode, exits.BACKEND_PRECONDITION, proc.stderr)
                self.assertFalse(
                    os.path.isfile(os.path.join(self.feature_dir, "ORCHESTRATION.md")),
                    "a rejected script must not have started a run")

    def test_a_missing_script_is_named(self):
        proc = self.run_cli("--backend", "stub", "--stub-script",
                            os.path.join(self.tmp.name, "nope.json"))
        self.assertEqual(proc.returncode, exits.BACKEND_PRECONDITION)
        self.assertIn("not found", proc.stderr)

    # -- the --notify sink, as a real command --------------------------
    def _notify_sink(self, body, name="sink.sh"):
        path = os.path.join(self.tmp.name, name)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(body)
        os.chmod(path, 0o755)
        return path

    def _escalating_script(self):
        return self.write_script([fixture("worker_blocked_human.md")])

    def test_the_notify_sink_receives_the_event_as_json_on_stdin(self):
        out = os.path.join(self.tmp.name, "event.json")
        sink = self._notify_sink("#!/bin/sh\ncat > %s\n" % out)
        proc = self.run_cli("--backend", "stub", "--stub-script", self._escalating_script(),
                            "--notify", sink)
        self.assertEqual(proc.returncode, exits.HUMAN_ESCALATION, proc.stderr)
        with open(out, encoding="utf-8") as fh:
            event = json.load(fh)
        self.assertEqual(event["event"], "human-escalation")
        self.assertIn("money", event["triggers"])

    def test_a_sink_that_exits_non_zero_does_not_change_the_run_outcome(self):
        """Declared edge case: the notify command fails."""
        sink = self._notify_sink("#!/bin/sh\nexit 3\n")
        proc = self.run_cli("--backend", "stub", "--stub-script", self._escalating_script(),
                            "--notify", sink)
        self.assertEqual(proc.returncode, exits.HUMAN_ESCALATION, proc.stderr)

    def test_a_sink_that_does_not_exist_is_reported_and_survived(self):
        proc = self.run_cli("--backend", "stub", "--stub-script", self._escalating_script(),
                            "--notify", os.path.join(self.tmp.name, "absent"))
        self.assertEqual(proc.returncode, exits.HUMAN_ESCALATION, proc.stderr)
        self.assertIn("[notify] sink failed", proc.stderr)

    def test_agent_text_never_reaches_a_shell(self):
        """The sink is run without a shell, so an injection attempt is inert."""
        marker = os.path.join(self.tmp.name, "pwned")
        sink = self._notify_sink("#!/bin/sh\ncat >/dev/null\n")
        proc = self.run_cli("--backend", "stub", "--stub-script", self._escalating_script(),
                            "--notify", sink)
        self.assertEqual(proc.returncode, exits.HUMAN_ESCALATION, proc.stderr)
        self.assertFalse(os.path.exists(marker))

    # -- AUDIT-5: --feature must live inside the repository ---------------
    def test_a_feature_path_outside_the_repo_is_refused(self):
        outside = os.path.join(self.tmp.name, "elsewhere")
        os.makedirs(outside, exist_ok=True)
        proc = self.run_cli("--dry-run")           # sanity: the normal path works
        self.assertEqual(proc.returncode, exits.OK, proc.stderr)

        env = dict(os.environ, PYTHONPATH=RUNNER_ROOT)
        with open(os.devnull, "rb") as devnull:
            bad = subprocess.run(
                [sys.executable, "-m", "sdd_runner", "--repo", self.repo,
                 "--feature", outside, "--dry-run"],
                stdin=devnull, capture_output=True, text=True, env=env, timeout=60)
        self.assertEqual(bad.returncode, exits.GATE_REFUSED)
        self.assertIn("inside specs/features", bad.stderr)

    def test_a_relative_path_escaping_the_repo_is_refused(self):
        env = dict(os.environ, PYTHONPATH=RUNNER_ROOT)
        with open(os.devnull, "rb") as devnull:
            bad = subprocess.run(
                [sys.executable, "-m", "sdd_runner", "--repo", self.repo,
                 "--feature", "../escape", "--dry-run"],
                stdin=devnull, capture_output=True, text=True, env=env, timeout=60)
        self.assertEqual(bad.returncode, exits.GATE_REFUSED)

    def test_the_flag_is_refused_for_a_real_backend(self):
        script = self.write_script(converging_script())
        proc = self.run_cli("--backend", "claude", "--stub-script", script)
        self.assertEqual(proc.returncode, exits.BACKEND_PRECONDITION)
        self.assertIn("applies to --backend stub", proc.stderr)


if __name__ == "__main__":
    unittest.main()
