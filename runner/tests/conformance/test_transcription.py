"""The protocol transcription guard — spec 040 D008, replacing T017's original form.

T017 was specified as "identical fixture responses driven through the runner AND
through `sdd-orchestrate`". The spike found that unviable (D008): there is no
injection point for scripted responses into the skill's Agent-tool delegations,
`scripts/skill-eval.sh` is single-turn and cannot drive a delegating loop, and
spec 032's PLAN already rejected scripted reviewers as admissible evidence about
the loop's behaviour.

This is the replacement guard. It is weaker than a true two-executor comparison
and that is stated rather than hidden: R1 is PARTIALLY mitigated, not eliminated.
What it does prove:

  1. every rule in PROTOCOL_TRANSCRIPTION.md names a module that exists and a
     test that the suite actually collects - the table cannot rot into fiction;
  2. the runner's schema understanding is checked against REAL recorded phase-1
     artifacts, not only against fixtures the runner's author wrote;
  3. the one observed divergence is pinned, so it cannot be closed silently.
"""

import os
import re
import unittest

from sdd_runner import blocks, budget, closure, counters, escalation, gate, loop, state, tasks
from tests.support import REPO_ROOT

HERE = os.path.dirname(os.path.abspath(__file__))
TABLE = os.path.join(HERE, "PROTOCOL_TRANSCRIPTION.md")

REAL_ARTIFACTS = [
    "specs/features/032-autonomous-loop-residual-calibration/ORCHESTRATION.md",
    "specs/features/033-task-verification-criterion/ORCHESTRATION.md",
]

# Every module the table may name. A module absent from this map makes its rows
# UNCHECKED, not invalid - which is how `loop.Loop._lifecycle_step` survived in
# the table for a day after the method was deleted (D046). Add the module here
# when you add its first row.
MODULES = {"blocks": blocks, "budget": budget, "closure": closure, "counters": counters,
           "escalation": escalation, "gate": gate, "loop": loop, "state": state,
           "tasks": tasks}


def _table_rows():
    with open(TABLE, encoding="utf-8") as fh:
        text = fh.read()
    # Only the clause table. Everything from the divergence section onward is
    # prose plus its own table, and is not a clause->module->test mapping.
    text = text.split("## Resolved divergence")[0]
    rows = []
    for line in text.splitlines():
        if not line.startswith("| ") or line.startswith("|---") or "031 clause" in line:
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == 3:
            rows.append(cells)
    return rows


class TableIsHonest(unittest.TestCase):
    def test_the_table_is_not_empty(self):
        self.assertGreaterEqual(len(_table_rows()), 20)

    def test_every_named_module_attribute_exists(self):
        missing = []
        for _clause, module_ref, _test in _table_rows():
            # A cell may carry a parenthetical gloss - "`loop.Loop` (no git write
            # paths)". Drop it first, THEN strip the backticks, or the reference
            # keeps a trailing backtick and silently matches nothing.
            ref = module_ref.split("(")[0].strip().strip("`").strip()
            parts = ref.split(".")
            mod = MODULES.get(parts[0])
            if mod is None:
                continue
            target = mod
            for part in parts[1:]:
                if not hasattr(target, part):
                    missing.append(ref)
                    break
                target = getattr(target, part)
        self.assertEqual(missing, [], "table names attributes that do not exist: %s" % missing)

    def test_every_named_test_file_exists(self):
        root = os.path.abspath(os.path.join(HERE, ".."))
        for _clause, _module, test_ref in _table_rows():
            name = test_ref.strip("`").split(".")[0]
            if not name.startswith("test_"):
                continue
            found = any(name + ".py" in files
                        for _d, _s, files in os.walk(root))
            self.assertTrue(found, "table names a missing test file: %s" % name)


class AgainstRealArtifacts(unittest.TestCase):
    """The runner's model is checked against what real phase-1 runs recorded."""

    def _artifacts(self):
        for rel in REAL_ARTIFACTS:
            path = os.path.join(REPO_ROOT, rel)
            if os.path.isfile(path):
                with open(path, encoding="utf-8") as fh:
                    yield rel, fh.read()

    def test_recorded_finding_identities_match_the_runner_identity_format(self):
        seen = 0
        for rel, text in self._artifacts():
            body = state.Orchestration.loads(text).body("Findings")
            for line in body.splitlines():
                if not line.startswith("| ") or line.startswith("|---"):
                    continue
                identity = line.strip().strip("|").split("|")[0].strip()
                if identity.lower().startswith("reviewer"):
                    continue
                with self.subTest(artifact=rel, identity=identity):
                    self.assertRegex(identity, r"^[a-z-]+:[A-Za-z0-9-]+$")
                    seen += 1
        self.assertTrue(seen, "no recorded finding identity was available to check")

    def test_recorded_run_results_are_values_the_runner_understands(self):
        for rel, text in self._artifacts():
            with self.subTest(artifact=rel):
                self.assertIn(state.Orchestration.loads(text).run_result(), state.RUN_RESULTS)


class ObservedDivergence(unittest.TestCase):
    """The severity boundary settled by D011 (2026-08-31).

    The verdict block's `severity` is a CLOSED enum: Critical | High | Medium |
    Low. Report vocabulary (blocker/major/minor) is legitimate in human narrative
    and invalid inside the machine-parsed block. No aliases, no normalization.

    Do not "fix" any of these by relaxing the parser. Their whole purpose is that
    the boundary cannot move silently in either direction.
    """

    NON_CANONICAL = ("blocker", "major", "minor")

    @staticmethod
    def _block(severity):
        return ("```yaml\nverdict: REJECT\nfindings:\n  - id: CONF-001\n"
                "    severity: %s\n    evidence: a.py:1\n    summary: s\n"
                "    required_action: r\n```\n" % severity)

    def test_the_canonical_severities_are_accepted(self):
        for severity in blocks.SEVERITIES:
            with self.subTest(severity=severity):
                v = blocks.parse_reviewer(self._block(severity), "final-conformance", 1)
                self.assertFalse(v.synthetic, msg=v.errors)
                self.assertEqual(v.verdict, "REJECT")
                self.assertEqual(v.findings[0]["severity"], severity)

    def test_the_runner_rejects_a_non_canonical_severity_by_design(self):
        for severity in self.NON_CANONICAL:
            with self.subTest(severity=severity):
                v = blocks.parse_reviewer(self._block(severity), "final-conformance", 1)
                self.assertTrue(v.synthetic)
                self.assertEqual(v.verdict, "REJECT")
                self.assertTrue(any("severity" in e for e in v.errors))

    def test_no_alias_or_normalization_is_applied(self):
        """`blocker` must not become `Critical`, and `minor` must not become `Low`."""
        for severity in self.NON_CANONICAL:
            with self.subTest(severity=severity):
                v = blocks.parse_reviewer(self._block(severity), "final-conformance", 1)
                # The only finding present is the synthetic malformed one.
                self.assertEqual(v.findings[0]["id"], "ORCH-MALFORMED-final-conformance-1")
                self.assertNotIn(severity, [f.get("severity") for f in v.findings])

    def test_report_vocabulary_outside_the_block_is_ignored(self):
        """Narrative may say `blocker` freely; only the block is parsed."""
        prose = ("This is a blocker in my view, and there are two major issues plus one\n"
                 "minor nit. Severity language here is report vocabulary, not schema.\n\n")
        text = prose + self._block("Critical")
        v = blocks.parse_reviewer(text, "final-conformance", 1)
        self.assertFalse(v.synthetic, msg=v.errors)
        self.assertEqual(v.findings[0]["severity"], "Critical")
        self.assertIn("blocker", v.raw)          # the prose is retained verbatim

    def test_report_vocabulary_outside_an_approve_block_is_ignored(self):
        text = ("Nothing blocker-level remains; the earlier major finding is fixed.\n\n"
                "```yaml\nverdict: APPROVE\nfindings: []\n```\n")
        v = blocks.parse_reviewer(text, "domain", 1)
        self.assertEqual(v.verdict, "APPROVE")
        self.assertFalse(v.malformed, msg=v.errors)

    def test_the_canonical_vocabulary_is_unchanged(self):
        self.assertEqual(blocks.SEVERITIES, ("Critical", "High", "Medium", "Low"))

    def test_the_protocol_documents_the_closed_enum(self):
        """D011's fix is in the contracts a reviewer actually reads, not only here."""
        required = {
            "skills/sdd-orchestrate/SKILL.md": "closed enum",
            "agents/domain-reviewer.md": "closed",
            "agents/final-conformance-reviewer.md": "closed",
            "specs/features/031-autonomous-orchestration-loop/SPEC.md": "closed enum",
        }
        for rel, needle in required.items():
            path = os.path.join(REPO_ROOT, rel)
            if not os.path.isfile(path):
                self.skipTest("%s unavailable" % rel)
            with self.subTest(document=rel):
                with open(path, encoding="utf-8") as fh:
                    text = fh.read()
                self.assertIn(needle, text)
                self.assertIn("Critical | High | Medium | Low", text)

    def test_the_historical_artifact_was_not_retconned(self):
        """033 records a run that happened; it is narrative and stays as written."""
        path = os.path.join(REPO_ROOT, REAL_ARTIFACTS[1])
        if not os.path.isfile(path):
            self.skipTest("artifact unavailable")
        with open(path, encoding="utf-8") as fh:
            body = state.Orchestration.loads(fh.read()).body("Findings")
        found = [s for s in self.NON_CANONICAL if re.search(r"\|\s*%s\s*\|" % s, body)]
        self.assertTrue(found,
                        "the 033 registry rows were edited. D011 decided to leave them: "
                        "rewriting a run's record to match a later rule falsifies history.")


if __name__ == "__main__":
    unittest.main()
