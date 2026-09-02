"""FR-002 / AC-003: each precondition refuses by name, and changes nothing."""

import os
import re
import subprocess
import tempfile
import unittest

from sdd_runner import gate
from tests.support import ADOPT_SPEC, SPEC, TASKS, make_adopted_repo, make_repo


def git_status(repo):
    return subprocess.run(["git", "-C", repo, "status", "--porcelain"],
                          capture_output=True, text=True).stdout


class GatePasses(unittest.TestCase):
    def test_a_clean_ready_feature_on_a_branch_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, feature_dir = make_repo(tmp)
            self.assertEqual(gate.check(repo, feature_dir), [])


class EachPreconditionRefusesByName(unittest.TestCase):
    def _conditions(self, repo, feature_dir, **kw):
        before = git_status(repo)
        refusals = gate.check(repo, feature_dir, **kw)
        # Every refusal must leave the tree byte-identical.
        self.assertEqual(git_status(repo), before)
        for r in refusals:
            self.assertTrue(r.remediation, "refusal %r has no remediation" % r.condition)
        return [r.condition for r in refusals]

    def test_lifecycle_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, feature_dir = make_repo(tmp, spec=SPEC.replace("Ready", "Draft"))
            self.assertIn("lifecycle status", self._conditions(repo, feature_dir))

    def test_open_questions(self):
        spec = SPEC.replace("- ~~OQ-1~~ **Resolved.**",
                            "- ~~OQ-1~~ **Resolved.**\n- OQ-2: something genuinely unresolved.")
        with tempfile.TemporaryDirectory() as tmp:
            repo, feature_dir = make_repo(tmp, spec=spec)
            self.assertIn("open questions", self._conditions(repo, feature_dir))

    def test_missing_tasks_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, feature_dir = make_repo(tmp)
            os.remove(os.path.join(feature_dir, "TASKS.md"))
            self.assertIn("TASKS.md missing", self._conditions(repo, feature_dir))

    def test_default_branch(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, feature_dir = make_repo(tmp)
            subprocess.run(["git", "-C", repo, "checkout", "-q", "master"],
                           capture_output=True, text=True)
            subprocess.run(["git", "-C", repo, "branch", "-M", "main"],
                           capture_output=True, text=True)
            self.assertIn("default branch", self._conditions(repo, feature_dir))

    def test_a_detached_head_is_not_an_isolated_git_location(self):
        """QA round: `git rev-parse --abbrev-ref HEAD` says "HEAD" when detached, which
        equals no branch name, so the default-branch comparison never fired and the gate
        passed. Adoption is the worst place for that: the maintainer's commit is the
        baseline and the attribution, and on a detached HEAD no branch references it."""
        for adopt in (False, True):
            with self.subTest(adopt=adopt):
                with tempfile.TemporaryDirectory() as tmp:
                    repo, feature_dir, _ = make_adopted_repo(tmp)
                    subprocess.run(["git", "-C", repo, "checkout", "-q", "--detach", "HEAD"],
                                   check=True, capture_output=True)
                    found = {r.condition: r for r in gate.check(repo, feature_dir, adopt=adopt)}
                    self.assertIn("default branch", found)
                    self.assertIn("detached", found["default branch"].detail)
                    self.assertIn("branch", found["default branch"].remediation)

    def test_unattributed_dirty_tree(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, feature_dir = make_repo(tmp)
            with open(os.path.join(repo, "agents", "implementer.md"), "a",
                      encoding="utf-8") as fh:
                fh.write("\nedited outside the feature folder\n")
            self.assertIn("unattributed dirty tree", self._conditions(repo, feature_dir))

    def test_a_dirty_path_inside_the_feature_folder_refuses_too(self):
        """Rewritten for spec 041 D004: on first entry no run exists to attribute a
        path to, so the inside-the-feature-folder tolerance is gone in both modes."""
        with tempfile.TemporaryDirectory() as tmp:
            repo, feature_dir = make_repo(tmp)
            with open(os.path.join(feature_dir, "notes.md"), "w", encoding="utf-8") as fh:
                fh.write("scratch inside the feature folder\n")
            self.assertIn("unattributed dirty tree", self._conditions(repo, feature_dir))
        with tempfile.TemporaryDirectory() as tmp:
            repo, feature_dir, _ = make_adopted_repo(tmp)
            with open(os.path.join(feature_dir, "notes.md"), "w", encoding="utf-8") as fh:
                fh.write("scratch inside the feature folder\n")
            self.assertIn("unattributed dirty tree",
                          self._conditions(repo, feature_dir, adopt=True))

    def test_red_baseline_suite(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, feature_dir = make_repo(tmp)
            conditions = self._conditions(repo, feature_dir,
                                          baseline_cmd=["false"])
            self.assertIn("red baseline suite", conditions)

    def test_baseline_that_mutates_the_tree(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, feature_dir = make_repo(tmp)
            script = os.path.join(tmp, "mutate.sh")
            with open(script, "w", encoding="utf-8") as fh:
                fh.write("#!/bin/sh\necho mutated >> agents/implementer.md\n")
            os.chmod(script, 0o755)
            before = git_status(repo)
            refusals = gate.check(repo, feature_dir, baseline_cmd=[script])
            self.assertIn("baseline suite mutates the tree",
                          [r.condition for r in refusals])
            self.assertNotEqual(git_status(repo), before)   # the baseline did it, not the gate


def _set_status(repo, feature_dir, status):
    """Rewrite the fixture's status and commit it, so only the status differs."""
    path = os.path.join(feature_dir, "SPEC.md")
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    text = re.sub(r"## Status\n\n[^\n]+\n", "## Status\n\n%s\n" % status, text)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    if git_status(repo).strip():            # "In Progress" is already the fixture's status
        subprocess.run(["git", "-C", repo, "commit", "-qam", "status %s" % status],
                       check=True, capture_output=True)


class AdoptionGate(unittest.TestCase):
    """Spec 041 FR-010 / AC-009: the status x adopt matrix and condition 7."""

    def _conditions(self, repo, feature_dir, **kw):
        before = git_status(repo)
        refusals = gate.check(repo, feature_dir, **kw)
        self.assertEqual(git_status(repo), before)
        return [r.condition for r in refusals]

    def test_status_matrix(self):
        # (status, adopt) -> the condition that must appear, or None for a pass.
        expected = {
            ("Ready", False): None,
            ("In Progress", False): "lifecycle status",
            ("In Review", False): "lifecycle status",
            ("Draft", False): "lifecycle status",
            ("Done", False): "lifecycle status",
            ("Ready", True): gate.ADOPTION_NOT_NEEDED,
            ("In Progress", True): None,
            ("In Review", True): "lifecycle status",
            ("Draft", True): "lifecycle status",
            ("Done", True): "lifecycle status",
        }
        for (status, adopt), condition in expected.items():
            with self.subTest(status=status, adopt=adopt):
                with tempfile.TemporaryDirectory() as tmp:
                    repo, feature_dir, _ = make_adopted_repo(tmp)
                    _set_status(repo, feature_dir, status)
                    conditions = self._conditions(repo, feature_dir, adopt=adopt)
                    if condition is None:
                        self.assertEqual(conditions, [])
                    else:
                        self.assertIn(condition, conditions)
                        self.assertNotIn(gate.INHERITED_UNDETERMINED, conditions)

    def test_in_review_is_not_a_first_entry_status_anymore(self):
        self.assertNotIn("In Review", gate.READY_STATUSES)
        self.assertNotIn("In Review", gate.ADOPT_STATUSES)
        self.assertIn("In Review", gate.REENTRY_STATUSES)

    def test_a_ready_spec_refuses_adoption_by_name_with_its_remediation(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, feature_dir = make_repo(tmp)          # Ready, no origin/HEAD
            refusals = gate.check(repo, feature_dir, adopt=True)
            by_name = {r.condition: r for r in refusals}
            self.assertIn(gate.ADOPTION_NOT_NEEDED, by_name)
            self.assertIn("without --adopt", by_name[gate.ADOPTION_NOT_NEEDED].remediation)

    def test_an_existing_state_file_refuses_adoption(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, feature_dir, _ = make_adopted_repo(tmp)
            with open(os.path.join(feature_dir, "ORCHESTRATION.md"), "w", encoding="utf-8") as fh:
                fh.write("# Orchestration: adopted\n")
            subprocess.run(["git", "-C", repo, "add", "-A"], check=True, capture_output=True)
            subprocess.run(["git", "-C", repo, "commit", "-qm", "state"], check=True,
                           capture_output=True)
            conditions = self._conditions(repo, feature_dir, adopt=True)
            self.assertIn(gate.ALREADY_ENTERED, conditions)

    def test_missing_origin_head_refuses_adoption_as_undetermined(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, feature_dir, _ = make_adopted_repo(tmp)
            subprocess.run(["git", "-C", repo, "remote", "remove", "origin"], check=True,
                           capture_output=True)
            refusals = gate.check(repo, feature_dir, adopt=True)
            by_name = {r.condition: r for r in refusals}
            self.assertIn(gate.INHERITED_UNDETERMINED, by_name)
            self.assertIn("set-head", by_name[gate.INHERITED_UNDETERMINED].remediation)
            # Without adoption the same repo is not asked for an inherited record.
            self.assertNotIn(gate.INHERITED_UNDETERMINED,
                             [r.condition for r in gate.check(repo, feature_dir)])

    def test_default_branch_and_dirty_tree_are_reported_branch_first(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, feature_dir, info = make_adopted_repo(tmp)
            subprocess.run(["git", "-C", repo, "checkout", "-q", info["default_branch"]],
                           check=True, capture_output=True)
            with open(os.path.join(repo, "agents", "implementer.md"), "a",
                      encoding="utf-8") as fh:
                fh.write("\nuncommitted work\n")
            conditions = self._conditions(repo, feature_dir, adopt=True)
            self.assertIn("default branch", conditions)
            self.assertIn("unattributed dirty tree", conditions)
            self.assertLess(conditions.index("default branch"),
                            conditions.index("unattributed dirty tree"))

    def test_inherited_record_shape(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, feature_dir, info = make_adopted_repo(tmp)
            record = gate.inherited_record(repo, feature_dir)
            self.assertIsInstance(record, gate.Inherited)
            self.assertEqual(record.baseline, info["baseline"])
            self.assertEqual(record.diff_base, info["diff_base"])
            self.assertEqual(record.default_branch, info["default_branch"])
            self.assertEqual([t for t, _ in record.checked], ["T001", "T002"])
            for _, verify in record.checked:
                self.assertNotEqual(verify, "none")


class ReEntryTreeRule(unittest.TestCase):
    """Spec 041 T019 / NEW-1: first entry is strict, re-entry is attributable.

    D004 removed the feature-folder tolerance because on FIRST entry there is no run
    to attribute a path to. On re-entry there is: 031 condition 5 says only paths
    attributable to the recorded run may be dirty. Applying the first-entry rule to
    both made a live run unable to resume over its own state file.
    """

    def _conditions(self, repo, feature_dir, **kw):
        return [r.condition for r in gate.check(repo, feature_dir, **kw)]

    def _state_file(self, feature_dir):
        with open(os.path.join(feature_dir, "ORCHESTRATION.md"), "w", encoding="utf-8") as fh:
            fh.write("# Orchestration\n")

    def test_re_entry_tolerates_the_runs_own_uncommitted_state_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, feature_dir, _ = make_adopted_repo(tmp)
            self._state_file(feature_dir)
            self.assertEqual(
                self._conditions(repo, feature_dir, first_entry=False), [])

    def test_re_entry_tolerates_paths_the_run_recorded_as_attributed(self):
        """Pins a capability the CLI does not yet use: nothing in the runner records
        attributed paths, so `attributed` is always empty in production (D010/T025).
        The parameter exists so the gate can express 031 condition 5 correctly the day
        a caller has that list; this test keeps it honest in the meantime."""
        with tempfile.TemporaryDirectory() as tmp:
            repo, feature_dir, _ = make_adopted_repo(tmp)
            self._state_file(feature_dir)
            with open(os.path.join(repo, "src", "pricing.py"), "a", encoding="utf-8") as fh:
                fh.write("\n# work in flight\n")
            self.assertEqual(
                self._conditions(repo, feature_dir, first_entry=False,
                                 attributed=["src/pricing.py"]), [])

    def test_re_entry_still_refuses_a_path_the_run_cannot_account_for(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, feature_dir, _ = make_adopted_repo(tmp)
            self._state_file(feature_dir)
            with open(os.path.join(repo, "agents", "implementer.md"), "a",
                      encoding="utf-8") as fh:
                fh.write("\nnobody claimed this\n")
            conditions = self._conditions(repo, feature_dir, first_entry=False,
                                          attributed=["src/pricing.py"])
            self.assertIn("unattributed dirty tree", conditions)

    def test_first_entry_is_unchanged_and_strict_in_both_modes(self):
        for adopt in (False, True):
            with self.subTest(adopt=adopt):
                with tempfile.TemporaryDirectory() as tmp:
                    repo, feature_dir, _ = make_adopted_repo(tmp)
                    # A dirty path inside the feature folder, the old tolerance.
                    with open(os.path.join(feature_dir, "scratch.md"), "w",
                              encoding="utf-8") as fh:
                        fh.write("x\n")
                    self.assertIn("unattributed dirty tree",
                                  self._conditions(repo, feature_dir, adopt=adopt))


class HonestRefusals(unittest.TestCase):
    """Spec 041 T029/T030, from the T014 replay against a real adopter project.

    Its specs write the status inside a fenced block and carry questions marked
    non-blocking. Both refusals were right to fire and wrong about why.
    """

    FENCED = SPEC.replace("## Status\n\nReady\n",
                          "## Status\n\n```\nEstado: In Review\nBlocked-by: —\n```\n")

    def _refusals(self, repo, feature_dir, **kw):
        return {r.condition: r for r in gate.check(repo, feature_dir, **kw)}

    def test_a_fenced_status_refuses_as_unreadable_not_as_a_quoted_fence(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, feature_dir = make_repo(tmp, spec=self.FENCED)
            found = self._refusals(repo, feature_dir)
            self.assertIn(gate.STATUS_UNREADABLE, found)
            self.assertNotIn("lifecycle status", found,
                             "an unreadable status must not also be reported as the wrong status")
            r = found[gate.STATUS_UNREADABLE]
            self.assertIn("states no lifecycle status", r.detail)
            for word in ("Draft", "Ready", "In Progress"):
                self.assertIn(word, r.remediation)
            self.assertIn("the skill path reads it", r.remediation)

    def test_a_missing_status_section_says_so(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, feature_dir = make_repo(tmp, spec="# Feature Spec: x\n\n## Problem\n\nNone.\n")
            r = self._refusals(repo, feature_dir)[gate.STATUS_UNREADABLE]
            self.assertIn("no `## Status` section", r.detail)

    def test_a_decorated_status_is_still_read_not_refused_as_unreadable(self):
        """Generous on purpose: `**Done — 2026-08-22.**` is a status, not a fence."""
        with tempfile.TemporaryDirectory() as tmp:
            repo, feature_dir = make_repo(
                tmp, spec=SPEC.replace("## Status\n\nReady\n",
                                       "## Status\n\n**Done — 2026-08-22.**\n"))
            found = self._refusals(repo, feature_dir)
            self.assertNotIn(gate.STATUS_UNREADABLE, found)
            self.assertIn("lifecycle status", found)

    def test_a_normal_status_is_unaffected(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, feature_dir = make_repo(tmp)
            self.assertEqual(gate.check(repo, feature_dir), [])

    def test_the_open_questions_refusal_names_them_and_admits_it_cannot_judge(self):
        spec = SPEC.replace(
            "- ~~OQ-1~~ **Resolved.**",
            "- ~~OQ-1~~ **Resolved.**\n"
            "- **Q1 (non-blocking)**: whether the slug stays in the URL.\n"
            "- **Q2 (non-blocking)**: whether the insurance defect stays as debt.")
        with tempfile.TemporaryDirectory() as tmp:
            repo, feature_dir = make_repo(tmp, spec=spec)
            r = self._refusals(repo, feature_dir)["open questions"]
            self.assertIn("2 unresolved", r.detail)
            self.assertIn("cannot judge as blocking or not", r.detail)
            self.assertIn("Q1", r.detail)
            self.assertIn("Q2", r.detail)
            self.assertIn("blocks an unchecked task", r.remediation)


class RefusalRendering(unittest.TestCase):
    def test_refusal_names_condition_detail_and_remediation(self):
        r = gate.Refusal("open questions", "2 unresolved", "answer them")
        rendered = r.render()
        for part in ("open questions", "2 unresolved", "answer them"):
            self.assertIn(part, rendered)


if __name__ == "__main__":
    unittest.main()
