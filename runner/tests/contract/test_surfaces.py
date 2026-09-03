"""The nine protocol surfaces agree with the core — spec 042 FR-012, AC-006, AC-012.

A **protocol surface** is a document that states a normative value of the
autonomous protocol. There are nine and they are listed here, once, in `SURFACES`.

**These tests read that list. They never search the repository** (FR-012a, D005).
The reason is concrete, not theoretical: twelve unrelated review skills contain
the string `Critical | High | Medium | Low` as ordinary report vocabulary, and a
guard that greps for it fails on all twelve, gets called noisy, and gets deleted.
This feature produced that exact false positive twice from its own tooling — once
in the T002 constant scan, once in the first draft of `test_interface` — so the
rule is enforced rather than trusted: `test_over_reach` proves the guards consume
the list.

Every assertion below quotes a value the surface really states. A surface that
does not mention a rule is not asserted about it; inventing coverage would make
the suite green for the wrong reason.
"""

import io
import os
import re
import unittest

from sdd_runner import policy
from tests.support import REPO_ROOT

# The enumerated protocol surfaces. Adding one is an edit here, on purpose.
SURFACES = {
    "cli": "runner/sdd_runner/__main__.py",
    "skill": "skills/sdd-orchestrate/SKILL.md",
    "template": "skills/sdd-orchestrate/templates/ORCHESTRATION.md",
    "runner-readme": "runner/README.md",
    "orchestration-doc": "docs/SDD-ORCHESTRATION.md",
    "domain-reviewer": "agents/domain-reviewer.md",
    "final-conformance-reviewer": "agents/final-conformance-reviewer.md",
    "codex-parity": "adapters/codex/PARITY.md",
    "counter-eval": "evals/scenarios/orchestrate-per-finding-counter.md",
}

# Documents that use protocol WORDS as ordinary vocabulary and are NOT surfaces.
# Listed so the over-reach guard can prove the difference is enforced.
NOT_SURFACES = [
    "skills/security-review/SKILL.md", "skills/qa-review/SKILL.md",
    "skills/api-review/SKILL.md", "skills/database-review/SKILL.md",
    "skills/frontend-review/SKILL.md", "skills/performance-review/SKILL.md",
    "skills/privacy-compliance-review/SKILL.md", "skills/review-all/SKILL.md",
    "skills/seo-review/SKILL.md", "skills/aeo-review/SKILL.md",
    "skills/geo-review/SKILL.md", "skills/ai-visibility-review/SKILL.md",
]


def assert_every_formula(case, text, times):
    """Every stated `max(FLOOR, PER_TASK x ...)` must match policy — not just the first.

    `re.search` reads one occurrence. `docs/SDD-ORCHESTRATION.md` states the formula
    twice, so a half-edited document passed this guard when it was mutation-tested
    (T015). `findall` is the fix, and the count assertion keeps a deleted formula
    from passing as "all zero of them agree".
    """
    stated = re.findall(r"max\((\d+), (\d+) %s" % re.escape(times), text)
    case.assertTrue(stated, "the budget formula is no longer stated here")
    for floor, per_task in stated:
        with case.subTest(formula="max(%s, %s ...)" % (floor, per_task)):
            case.assertEqual((int(floor), int(per_task)), (policy.FLOOR, policy.PER_TASK))


def read(key):
    path = os.path.join(REPO_ROOT, SURFACES[key])
    with io.open(path, encoding="utf-8") as fh:
        return fh.read()


class TheListIsHonest(unittest.TestCase):
    def test_every_named_surface_exists(self):
        for key, rel in SURFACES.items():
            with self.subTest(surface=key):
                self.assertTrue(os.path.isfile(os.path.join(REPO_ROOT, rel)), rel)

    def test_there_are_nine(self):
        self.assertEqual(len(SURFACES), 9)


class Cli(unittest.TestCase):
    """The flag set and the exit-code vocabulary the CLI renders."""

    def test_every_flag_is_still_offered(self):
        source = read("cli")
        for flag in ("--feature", "--repo", "--backend", "--model", "--max-iterations",
                     "--max-delegations", "--baseline", "--notify",
                     "--allow-unverified-backend", "--stub-script", "--adopt", "--dry-run"):
            with self.subTest(flag=flag):
                self.assertIn('"%s"' % flag, source)

    def test_the_backend_choices_match_the_backends_that_exist(self):
        self.assertIn('choices=("stub", "claude", "codex")', read("cli"))

    def test_it_renders_exit_code_names_from_the_core(self):
        self.assertIn("NAMES", read("cli"))


class Skill(unittest.TestCase):
    """`skills/sdd-orchestrate/SKILL.md` — the protocol's prose projection."""

    def setUp(self):
        self.text = read("skill")

    def test_the_severity_enum_is_the_closed_one(self):
        # Pin the DECLARATION, not merely a mention: the enum also appears in the
        # verdict-block example, so `assertIn(enum)` stayed green against a mutated
        # declaration when this guard was mutation-tested (T015).
        self.assertIn("closed enum: `%s`" % " | ".join(policy.SEVERITIES), self.text)

    def test_the_budget_formula_matches_policy(self):
        assert_every_formula(self, self.text, "×")

    def test_the_first_entry_statuses_match_policy(self):
        self.assertIn("`SPEC.md` is `Ready`", self.text.replace("must be exactly `Ready`",
                                                               "`SPEC.md` is `Ready`"))
        self.assertIn(policy.ADOPT_STATUSES[0], self.text)

    def test_the_run_results_match_policy(self):
        for result in policy.RUN_RESULTS:
            with self.subTest(result=result):
                self.assertIn(result, self.text)

    def test_every_reviewer_is_named(self):
        for reviewer in policy.REVIEWERS:
            with self.subTest(reviewer=reviewer):
                self.assertIn(reviewer + "-reviewer", self.text)

    def test_the_six_human_gated_domains_are_all_described(self):
        self.assertEqual(len(policy.HUMAN_GATED), 6)
        for keyword in ("product or UX", "money movement", "personal-data",
                        "public API", "destructive", "contradicts the SPEC"):
            with self.subTest(domain=keyword):
                self.assertIn(keyword, self.text)


class Template(unittest.TestCase):
    """The `ORCHESTRATION.md` scaffold — section order and header fields."""

    def setUp(self):
        self.text = read("template")

    def test_it_records_the_protocol_version(self):
        self.assertIn("Protocol version: `%d`" % policy.PROTOCOL_VERSION, self.text)

    def test_the_attempt_lifecycle_matches_policy(self):
        self.assertIn(" | ".join(policy.LIFECYCLE), self.text)

    def test_the_run_results_match_policy(self):
        self.assertIn(" | ".join(policy.RUN_RESULTS), self.text)

    def test_the_section_order_is_the_one_state_writes(self):
        headings = re.findall(r"^## (.+)$", self.text, re.M)
        for section in ("State", "Attempts", "Inherited", "Findings", "Delegation log",
                        "Escalations", "Cap changes", "Closure delta", "Run result"):
            with self.subTest(section=section):
                self.assertIn(section, headings)

    def test_the_inherited_columns_match_policy(self):
        for column in policy.INHERITED_COLUMNS:
            with self.subTest(column=column):
                self.assertIn(column, self.text)


class RunnerReadme(unittest.TestCase):
    def setUp(self):
        self.text = read("runner-readme")

    def test_every_exit_code_is_documented_with_its_value(self):
        for code, name in sorted(policy.NAMES.items()):
            with self.subTest(code=code, name=name):
                self.assertRegex(self.text, r"`%d`" % code,
                                 "exit %d (%s) is undocumented" % (code, name))

    def test_the_budget_formula_matches_policy(self):
        assert_every_formula(self, self.text, "x")

    def test_the_terminal_phase_matches_policy(self):
        self.assertIn(policy.CORE_COMPLETE, self.text)


class OrchestrationDoc(unittest.TestCase):
    def setUp(self):
        self.text = read("orchestration-doc")

    def test_the_budget_formula_matches_policy(self):
        assert_every_formula(self, self.text, "×")

    def test_the_terminal_phase_matches_policy(self):
        self.assertIn(policy.CORE_COMPLETE, self.text)

    def test_the_documented_invocation_still_works(self):
        self.assertIn("--autonomous specs/features/<nnn>-<name>", self.text)
        self.assertIn("--max-delegations", self.text)


class ReviewerAgents(unittest.TestCase):
    """Both reviewer contracts must carry the closed enum — this is D011's fix."""

    def test_the_severity_enum_is_closed_in_both(self):
        for key in ("domain-reviewer", "final-conformance-reviewer"):
            with self.subTest(agent=key):
                text = read(key)
                self.assertIn(" | ".join(policy.SEVERITIES), text)
                self.assertIn("closed", text)


class CodexParity(unittest.TestCase):
    """Codex is a protocol surface: it states the durable record's shape (A-011)."""

    def setUp(self):
        self.text = read("codex-parity")

    def test_it_names_the_same_durable_record(self):
        self.assertIn("ORCHESTRATION.md", self.text)
        self.assertIn("Inherited", self.text)

    def test_it_claims_the_same_adoption_entry(self):
        self.assertIn(policy.ADOPT_STATUSES[0], self.text)
        self.assertIn("adoption header fields", self.text)


class CounterEval(unittest.TestCase):
    """The eval scenario hard-codes the caps it reasons about."""

    def setUp(self):
        self.text = read("counter-eval")

    def test_the_default_budget_it_assumes_matches_policy(self):
        stated = re.search(r"`max-delegations` is (\d+)", self.text)
        self.assertIsNotNone(stated)
        self.assertEqual(int(stated.group(1)), policy.FLOOR)

    def test_it_reasons_about_the_two_gating_counters_policy_defines(self):
        self.assertIn("no-progress streak", self.text)
        self.assertIn("per-finding REJECT total", self.text)


class AuthorityIsInverted(unittest.TestCase):
    """AC-012 / D004: the old ownership must not survive anywhere."""

    OLD = re.compile(r"this runner is wrong|THIS RUNNER IS WRONG", re.IGNORECASE)

    def test_no_surface_still_says_the_runner_defers_to_the_skill(self):
        for key, rel in SURFACES.items():
            with self.subTest(surface=key):
                self.assertIsNone(self.OLD.search(read(key)),
                                  "%s still states the pre-042 authority" % rel)

    def test_the_package_docstring_states_the_new_authority(self):
        import sdd_runner
        self.assertIn("the SKILL is\nwrong", sdd_runner.__doc__)

    def test_the_skill_says_the_executable_contract_is_the_source_of_truth(self):
        text = read("skill")
        self.assertIn("The executable contract is the source of truth", text)
        self.assertIn("this prose is wrong", text)


class OverReach(unittest.TestCase):
    """FR-012a: the guards read the list; they do not search the repository."""

    def test_the_twelve_report_vocabulary_files_are_not_surfaces(self):
        surfaces = set(SURFACES.values())
        for rel in NOT_SURFACES:
            with self.subTest(document=rel):
                self.assertNotIn(rel, surfaces)

    def test_they_really_do_contain_the_protocol_words(self):
        """If they did not, this guard would be protecting against nothing."""
        found = 0
        for rel in NOT_SURFACES:
            path = os.path.join(REPO_ROOT, rel)
            if not os.path.isfile(path):
                continue
            with io.open(path, encoding="utf-8") as fh:
                if " | ".join(policy.SEVERITIES) in fh.read():
                    found += 1
        self.assertGreaterEqual(found, 8,
                                "the over-reach scenario no longer exists; re-derive the list")

    def test_no_surface_test_walks_the_repository(self):
        """A guard that discovers surfaces by search is the failure mode, not the guard.

        Checked over the AST, not the source text: the first version compared
        strings and failed on its own list of forbidden names. That is the third
        time in this feature that a text search mistook a mention for a use, and
        it is why FR-012a exists.
        """
        import ast
        with io.open(os.path.abspath(__file__), encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        forbidden = {"walk", "glob", "iglob", "rglob", "listdir", "scandir"}
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                base = node.func.value
                if isinstance(base, ast.Name) and base.id == "ast":
                    continue          # `ast.walk` walks a syntax tree, not a filesystem
                with self.subTest(call=node.func.attr, line=node.lineno):
                    self.assertNotIn(node.func.attr, forbidden,
                                     "line %d discovers files instead of reading SURFACES"
                                     % node.lineno)


if __name__ == "__main__":
    unittest.main()
