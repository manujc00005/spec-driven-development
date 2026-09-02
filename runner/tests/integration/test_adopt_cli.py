"""Spec 041 T015/T016: the CLI's adopt entry and its re-entry.

Both cases the unit tests cannot reach, because they live in argument handling
and in what `--dry-run` prints, not in `gate.check`.
"""

import os
import socket
import subprocess
import sys
import tempfile
import unittest

from sdd_runner import exits
from tests.support import make_adopted_repo

RUNNER_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
FEATURE = "specs/features/901-adopted"


def run_cli(repo, *args):
    env = dict(os.environ, PYTHONPATH=RUNNER_ROOT)
    with open(os.devnull, "rb") as devnull:
        return subprocess.run(
            [sys.executable, "-m", "sdd_runner", "--repo", repo,
             "--feature", FEATURE, "--dry-run"] + list(args),
            stdin=devnull, capture_output=True, text=True, env=env, timeout=60)


def commit(repo, message):
    subprocess.run(["git", "-C", repo, "add", "-A"], check=True, capture_output=True)
    subprocess.run(["git", "-C", repo, "commit", "-qm", message], check=True,
                   capture_output=True)


def resumable_state(pid=999999, entry="adopt", result="ACTIVE", resumable="yes"):
    """A state document `resume.inspect` actually accepts.

    T015's first fixture was a skeleton: it passed the gate but `resume.inspect`
    would have refused it, so the test proved "the gate no longer refuses" rather
    than "an adopted run resumes" (T020 / CONF-041-02). Default pid is a dead one,
    which is how an interrupted run looks.
    """
    return ("# Orchestration: adopted\n\n## State\n\n"
            "- writer: sdd_runner\n- entry: %s\n- iteration: 0\n"
            "- max-delegations: 25\n- delegations used: 0\n"
            "- counters: \n- approvals: \n- completed tasks: \n"
            "- runner pid: %d\n- runner host: %s\n\n"
            "## Run result\n\n%s\n\nresumable: %s\n"
            % (entry, pid, socket.gethostname(), result, resumable))


class DryRunPrintsTheInheritedRecord(unittest.TestCase):
    """T016 / AC-009: the record is what makes an adopt dry run worth running."""

    def test_dry_run_adopt_prints_the_inherited_record(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, _feature_dir, info = make_adopted_repo(tmp)
            proc = run_cli(repo, "--adopt")
            self.assertEqual(proc.returncode, exits.OK, proc.stderr)
            self.assertIn("entry:           adopt", proc.stdout)
            self.assertIn("adoption baseline commit: %s" % info["baseline"], proc.stdout)
            self.assertIn("adoption diff base:       %s (against %s)"
                          % (info["diff_base"], info["default_branch"]), proc.stdout)
            self.assertIn("inherited tasks: 2", proc.stdout)
            for task_id in ("T001", "T002"):
                self.assertIn("%s  inherited  verify:" % task_id, proc.stdout)
            # The budget is computed from what is still UNCHECKED at adoption.
            self.assertIn("max-delegations: 25", proc.stdout)

    def test_a_plain_dry_run_prints_no_inherited_record(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, feature_dir, _ = make_adopted_repo(tmp)
            _set_status(repo, feature_dir, "Ready")
            proc = run_cli(repo)
            self.assertEqual(proc.returncode, exits.OK, proc.stderr)
            self.assertIn("entry:           ready", proc.stdout)
            self.assertNotIn("inherited", proc.stdout)


def _set_status(repo, feature_dir, status):
    import re
    path = os.path.join(feature_dir, "SPEC.md")
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    text = re.sub(r"## Status\n\n[^\n]+\n", "## Status\n\n%s\n" % status, text)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    commit(repo, "status %s" % status)


class ReEntryThroughTheCLI(unittest.TestCase):
    """T015 / AC-007: an adopted run must be resumable.

    `gate.check` has always taken `first_entry`, and the CLI has never passed it.
    That was harmless while `In Progress` was a first-entry status; spec 041
    narrowed first entry to `Ready`, which made every adopted run a one-shot.
    """

    def _adopted_repo_with_state(self, tmp):
        repo, feature_dir, info = make_adopted_repo(tmp)
        with open(os.path.join(feature_dir, "ORCHESTRATION.md"), "w", encoding="utf-8") as fh:
            fh.write(resumable_state())
        commit(repo, "runner state")
        return repo, feature_dir, info

    def test_an_adopted_run_can_be_re_entered_without_the_flag(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, _, _ = self._adopted_repo_with_state(tmp)
            proc = run_cli(repo)
            self.assertEqual(proc.returncode, exits.OK, proc.stderr)
            self.assertNotIn("lifecycle status", proc.stderr)

    def test_re_entering_with_the_adopt_flag_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, _, _ = self._adopted_repo_with_state(tmp)
            proc = run_cli(repo, "--adopt")
            self.assertEqual(proc.returncode, exits.GATE_REFUSED)
            self.assertIn("already adopted or entered", proc.stderr)
            self.assertIn("without --adopt", proc.stderr)

    def test_a_closed_feature_is_still_refused_on_re_entry(self):
        """Re-entry is not a way past the lifecycle: Done is not a re-entry status."""
        with tempfile.TemporaryDirectory() as tmp:
            repo, feature_dir, _ = self._adopted_repo_with_state(tmp)
            _set_status(repo, feature_dir, "Done")
            proc = run_cli(repo)
            self.assertEqual(proc.returncode, exits.GATE_REFUSED)
            self.assertIn("lifecycle status", proc.stderr)



class StateIsAuthenticatedAtTheGate(unittest.TestCase):
    """T020 / CONF-041-02: existence is not authentication.

    A dry run returns before `Loop` is built, so without this the CLI reported a
    pass for a document `resume.inspect` would refuse.
    """

    def _repo_with_state(self, tmp, body):
        repo, feature_dir, _ = make_adopted_repo(tmp)
        with open(os.path.join(feature_dir, "ORCHESTRATION.md"), "w", encoding="utf-8") as fh:
            fh.write(body)
        return repo

    def test_a_document_missing_its_budget_is_refused_by_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            # Everything valid except the budget, so `inspect` reaches the cap check.
            repo = self._repo_with_state(
                tmp, "# Orchestration\n\n## State\n\n- writer: sdd_runner\n- entry: adopt\n"
                     "- iteration: 0\n- counters: \n- approvals: \n- completed tasks: \n"
                     "- runner pid: 999999\n- runner host: %s\n\n"
                     "## Run result\n\nACTIVE\n\nresumable: yes\n" % socket.gethostname())
            proc = run_cli(repo)
            self.assertEqual(proc.returncode, exits.STATE_UNRESUMABLE, proc.stderr)
            self.assertIn("max-delegations", proc.stderr)
            self.assertIn("remediation", proc.stderr)

    def test_a_document_written_by_another_executor_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = self._repo_with_state(tmp, "# Orchestration\n\n## State\n\n"
                                              "- writer: sdd-orchestrate\n\n"
                                              "## Run result\n\nACTIVE\n\nresumable: yes\n")
            proc = run_cli(repo)
            self.assertEqual(proc.returncode, exits.STATE_UNRESUMABLE, proc.stderr)
            self.assertIn("sdd-orchestrate", proc.stderr)

    def test_a_live_run_on_this_host_is_refused_as_concurrent(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = self._repo_with_state(tmp, resumable_state(pid=os.getpid()))
            proc = run_cli(repo)
            self.assertEqual(proc.returncode, exits.CONCURRENT_RUN, proc.stderr)
            self.assertIn("already owns", proc.stderr)

    def test_a_valid_document_still_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = self._repo_with_state(tmp, resumable_state())
            proc = run_cli(repo)
            self.assertEqual(proc.returncode, exits.OK, proc.stderr)


class RefusalPrecedence(unittest.TestCase):
    """T024 / R3-02: `--adopt` over an existing document answers about intent.

    T020 put state authentication ahead of the gate, which made `already adopted or
    entered` unreachable for any document that was not a valid runner-written one —
    a contract four documents describe and two CALIBRATION rows had already recorded.
    """

    FOREIGN = ("# Orchestration\n\n## State\n\n- writer: sdd-orchestrate\n\n"
               "## Run result\n\nACTIVE\n\nresumable: yes\n")
    TERMINAL = ("# Orchestration\n\n## State\n\n- writer: sdd_runner\n\n"
                "## Run result\n\nDONE\n\nresumable: no\n")

    def _repo(self, tmp, body):
        repo, feature_dir, _ = make_adopted_repo(tmp)
        with open(os.path.join(feature_dir, "ORCHESTRATION.md"), "w", encoding="utf-8") as fh:
            fh.write(body)
        return repo

    def test_adopt_over_a_foreign_document_is_already_adopted_or_entered(self):
        with tempfile.TemporaryDirectory() as tmp:
            proc = run_cli(self._repo(tmp, self.FOREIGN), "--adopt")
            self.assertEqual(proc.returncode, exits.GATE_REFUSED, proc.stderr)
            self.assertIn("already adopted or entered", proc.stderr)
            self.assertIn("without --adopt", proc.stderr)

    def test_adopt_over_a_terminal_document_is_already_adopted_or_entered(self):
        with tempfile.TemporaryDirectory() as tmp:
            proc = run_cli(self._repo(tmp, self.TERMINAL), "--adopt")
            self.assertEqual(proc.returncode, exits.GATE_REFUSED, proc.stderr)
            self.assertIn("already adopted or entered", proc.stderr)

    def test_re_entry_without_the_flag_still_authenticates_the_document(self):
        """The precise refusal survives where it belongs: a real re-entry."""
        for body, needle in ((self.FOREIGN, "sdd-orchestrate"),
                             (self.TERMINAL, "completed run")):
            with self.subTest(needle=needle):
                with tempfile.TemporaryDirectory() as tmp:
                    proc = run_cli(self._repo(tmp, body))
                    self.assertEqual(proc.returncode, exits.STATE_UNRESUMABLE, proc.stderr)
                    self.assertIn(needle, proc.stderr)

    def test_an_unreadable_state_file_exits_with_a_code_not_a_traceback(self):
        """T026 / R3-06: a scheduler branches on the exit code alone."""
        with tempfile.TemporaryDirectory() as tmp:
            repo, feature_dir, _ = make_adopted_repo(tmp)
            with open(os.path.join(feature_dir, "ORCHESTRATION.md"), "wb") as fh:
                fh.write(b"\xff\xfe not valid utf-8 \x00\x9c")
            proc = run_cli(repo)
            self.assertEqual(proc.returncode, exits.STATE_UNRESUMABLE, proc.stderr)
            self.assertIn("cannot be read", proc.stderr)
            self.assertNotIn("Traceback", proc.stderr)


if __name__ == "__main__":
    unittest.main()
