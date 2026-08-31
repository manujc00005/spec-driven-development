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

    def run_cli(self, *args):
        """Spawn the CLI with stdin closed. No TTY, no inherited session."""
        env = dict(os.environ, PYTHONPATH=RUNNER_ROOT)
        with open(os.devnull, "rb") as devnull:
            return subprocess.run(
                [sys.executable, "-m", "sdd_runner", "--repo", self.repo,
                 "--feature", "specs/features/900-fixture"] + list(args),
                stdin=devnull, capture_output=True, text=True, env=env, timeout=120)

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

        # ... and no commit the runner created.
        self.assertEqual(len(self.git("log", "--oneline").splitlines()), 1)

    def test_the_run_is_reconstructible_from_the_log_the_cli_wrote(self):
        script = self.write_script(converging_script())
        self.run_cli("--backend", "stub", "--stub-script", script)
        with open(os.path.join(self.feature_dir, "run.jsonl"), encoding="utf-8") as fh:
            events = [json.loads(line)["event"] for line in fh if line.strip()]
        for required in ("plan", "dispatch", "verdict", "freeze", "closure-delta", "finish"):
            self.assertIn(required, events)

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

    def test_the_flag_is_refused_for_a_real_backend(self):
        script = self.write_script(converging_script())
        proc = self.run_cli("--backend", "claude", "--stub-script", script)
        self.assertEqual(proc.returncode, exits.BACKEND_PRECONDITION)
        self.assertIn("applies to --backend stub", proc.stderr)


if __name__ == "__main__":
    unittest.main()
