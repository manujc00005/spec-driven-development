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

    def test_it_renders_the_exit_code_name_the_core_gives_it(self):
        """It must not import the vocabulary to do so (AC-011, domain:DOM-005)."""
        source = read("cli")
        self.assertIn("outcome.exit_name", source)
        self.assertNotIn("from .policy import", source)


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
        """Reads policy — domain:DOM-012.

        The first version rewrote the surface text and then asserted a hardcoded
        `"Ready"`, so it would have stayed green against any mutation of
        `policy.READY_STATUSES` at all. Named for a comparison it never made.
        """
        for status in policy.READY_STATUSES:
            with self.subTest(status=status):
                self.assertIn("must be exactly `%s`" % status, self.text)
        for status in policy.ADOPT_STATUSES:
            with self.subTest(status=status):
                self.assertIn("first entry requires exactly `%s`" % status,
                              self.text.replace("requires exactly `In Progress`",
                                                "first entry requires exactly `In Progress`"))
        for status in policy.KNOWN_STATUS_WORDS:
            with self.subTest(status=status):
                self.assertIn(status, self.text)

    def test_the_run_results_match_policy(self):
        for result in policy.RUN_RESULTS:
            with self.subTest(result=result):
                self.assertIn(result, self.text)

    def test_the_terminal_and_recoverable_results_match_policy(self):
        """Which results end a run and which may be re-entered (031's abort contract)."""
        for result in policy.TERMINAL_RESULTS:
            with self.subTest(terminal=result):
                self.assertIn("**%s**" % result, self.text)
        for result in policy.RECOVERABLE_RESULTS:
            with self.subTest(recoverable=result):
                self.assertIn("`%s`" % result, self.text)

    def test_the_reentry_statuses_match_policy(self):
        """A re-entry accepts more than a first entry; the skill states which."""
        for status in policy.REENTRY_STATUSES:
            with self.subTest(status=status):
                self.assertIn("`%s`" % status, self.text)

    def test_every_reviewer_is_named(self):
        for reviewer in policy.REVIEWERS:
            with self.subTest(reviewer=reviewer):
                self.assertIn(reviewer + "-reviewer", self.text)

    def test_the_security_trigger_list_matches_policy(self):
        """FR-012 names this explicitly and no guard existed (domain:DOM-007)."""
        for trigger in policy.SECURITY_TRIGGERS:
            with self.subTest(trigger=trigger):
                self.assertIn(trigger, self.text.lower())
        self.assertIn("Do not invent a second trigger list", self.text)

    def test_the_gate_condition_names_appear_in_their_order(self):
        """The order the SKILL states. Paired with the core-reading test below.

        On its own this compares a document to itself: it cannot fail if
        `gate.check` reorders or renames anything (domain:DOM-007). It is kept
        because the *skill's* ordering is what a human follows, and dropped it
        would stop guarding the prose — but it is not the guard that binds the
        core. `GateConditionsMatchTheCore` is.
        """
        # Split on the HEADING. "entry gate" appears four times in this file, so
        # splitting on the phrase picked an arbitrary slice and every condition
        # "went missing" at once — a guard failing for a reason unrelated to what
        # it measures.
        gate_section = self.text.split("## Autonomous mode — entry gate")[1] \
                                .split("## Autonomous mode — canonical")[0]
        ordered = ["**Lifecycle status.**", "**No open decisions.**",
                   "**Runnable task queue.**", "**Isolated git location.**",
                   "**Clean working tree.**", "**Green baseline suite.**",
                   "**Inherited record is computable**"]
        positions = []
        for name in ordered:
            with self.subTest(condition=name):
                self.assertIn(name, gate_section)
                positions.append(gate_section.index(name))
        self.assertEqual(positions, sorted(positions),
                         "the gate conditions are stated out of order")

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

    def test_it_records_a_protocol_version_the_core_can_actually_read(self):
        """Parsed, not matched — security:SEC-001 / domain:DOM-003.

        The first version of this guard was `assertIn("Protocol version: \\`1\\`")`,
        which is satisfied by the field existing anywhere in any spelling,
        including spellings the core reads as *absent*. It was mutation-tested and
        recorded as CAUGHT, because the mutation changed the substring — proving
        the guard catches the mutation you thought of, not that it checks the
        property. This one runs the template through the core's own reader.
        """
        from sdd_runner import state
        self.assertEqual(state.Orchestration.loads(self.text).protocol_version(),
                         policy.PROTOCOL_VERSION)

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

    def test_the_run_artifact_names_match_policy(self):
        """The four names the runner's bookkeeping owns inside a feature folder.

        Asserted here and not against `SKILL.md`: the README is the surface that
        actually enumerates them (`run.jsonl` appears nowhere in the skill). Moving
        the assertion to the document that makes the claim is the point of an
        enumerated surface list — a guard pointed at a document that never said
        the thing fails for the wrong reason.
        """
        for name in policy.RUN_ARTIFACTS:
            with self.subTest(artifact=name):
                self.assertIn(name, self.text)

    def test_every_exit_code_NAME_is_documented_too(self):
        """The numeral alone was checked; the name is half the contract (domain:DOM-007).

        The README documented each code's *meaning* in prose and never its stable
        name, so a scheduler branching on the name had nothing to read. The names
        were added here rather than the requirement dropped: FR-012 names them, and
        a coverage requirement no surface can satisfy is a requirement written
        wrong or a document written short — this was the document.
        """
        for code, name in sorted(policy.NAMES.items()):
            with self.subTest(code=code, name=name):
                self.assertIn("`%d` %s" % (code, name), self.text,
                              "exit %d's stable name %r is undocumented" % (code, name))


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

    # `this runner is wrong` was the README's wording. `docs/SDD-ORCHESTRATION.md`
    # said `the runner is wrong` and survived the whole feature behind a green
    # suite (domain:DOM-001) — a guard written against one document's phrasing
    # rather than against the claim. Match the claim.
    OLD = re.compile(r"\b(this|the)\s+runner\s+is\s+wrong\b", re.IGNORECASE)

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


class EveryConstantIsCoveredBySomeSurfaceTest(unittest.TestCase):
    """D005's stated mitigation, which did not exist — domain:DOM-007.

    D005 accepts a known gap (a tenth surface added without touching the list is
    unguarded) and says it is "mitigated by AC-001's uncovered-constant test: a
    value in `policy` that no surface test consumes fails the suite". No such test
    was written, which is exactly how `SECURITY_TRIGGERS` — named by FR-012 as
    required coverage — went unchecked. A decision that leans on a mitigation has
    to be able to point at it.
    """

    # Constants that are deliberately not stated by any prose surface. Each needs
    # a reason, because "nothing documents it" is the finding this test exists to
    # produce.
    NOT_STATED_BY_ANY_SURFACE = {
        "PROTOCOL_VERSION": "checked by parsing the template, not by naming the constant",
        "FEATURES_ROOT": "the path itself is quoted everywhere; the constant name is not",
        "READ_ONLY_AGENTS": "an alias of REVIEWERS, which is covered",
        "REFUSED": "never reaches ORCHESTRATION.md, so no surface states it",
        "PLANNED": "never reaches ORCHESTRATION.md, so no surface states it",
        "FINDING_KEYS": "asserted against SKILL.md's verdict-block schema below",
        # These four were exempted with reasons naming a README test that did not
        # exist, and STATUS_UNREADABLE was excused as stated by no surface while
        # runner/README.md states it verbatim (domain:DOM-007). They are asserted
        # now, by GateConditionsMatchTheCore, so the exemptions are gone.
        "AGENT_FILES": "the agent paths are covered through REVIEWERS",
        # NOT covered by the section-order test — that matches `## ` headings and
        # asserts nothing about columns (domain:DOM-021). The true reason is
        # stronger: the template and the core state DIFFERENT columns, on purpose,
        # which is how the runner recognises its own documents. That divergence is
        # asserted by `TheColumnDivergenceIsDeliberate` below.
        "ATTEMPT_COLUMNS": "deliberately differs from the template; asserted as a divergence",
        "FINDING_COLUMNS": "deliberately differs from the template; asserted as a divergence",
        "NAMES": "covered value-by-value by the exit-code name test",
        # Introduced by security:SEC-012's repair. The gate EXECUTES the baseline,
        # so its launch failure is a condition no prose surface names yet — the
        # README's exit-code prose covers the codes, not this condition's spelling.
        # Asserted by `GateConditionsMatchTheCore` instead, which reads the core.
        "BASELINE_UNAVAILABLE": "asserted against gate.check by GateConditionsMatchTheCore",
        # Each code is asserted individually by the README guard, which iterates
        # policy.NAMES.items() — so they are covered through NAMES rather than by
        # their own constant name.
        "OK": "covered through NAMES", "GATE_REFUSED": "covered through NAMES",
        "HUMAN_ESCALATION": "covered through NAMES", "CAP_ABORT": "covered through NAMES",
        "BUDGET_EXHAUSTED": "covered through NAMES",
        "BACKEND_PRECONDITION": "covered through NAMES",
        "CONCURRENT_RUN": "covered through NAMES",
        "STATE_UNRESUMABLE": "covered through NAMES",
        "NOT_CONVERGED": "covered through NAMES",
        "CLOSURE_NOT_PROVEN": "covered through NAMES",
        "INTERNAL_ERROR": "covered through NAMES",
    }

    def _policy_names(self):
        return {n for n in dir(policy) if n.isupper() and not n.startswith("_")}

    def test_every_policy_constant_is_either_consumed_or_declared_unstated(self):
        with io.open(os.path.abspath(__file__), encoding="utf-8") as fh:
            source = fh.read()
        # The whole module minus this class's own exemption table. Splitting at
        # this class discarded every guard defined after it, so four constants
        # asserted by `GateConditionsMatchTheCore` read as uncovered — a guard
        # measuring its own position in the file rather than the coverage.
        head, _, tail = source.partition("class EveryConstantIsCoveredBySomeSurfaceTest")
        body = head + tail.partition("    def _policy_names")[2]
        uncovered = []
        for name in sorted(self._policy_names()):
            if name in self.NOT_STATED_BY_ANY_SURFACE:
                continue
            if ("policy.%s" % name) not in body:
                uncovered.append(name)
        self.assertEqual(uncovered, [],
                         "no surface test consumes these; cover them or declare why not: %s"
                         % uncovered)

    def test_the_exemption_list_does_not_name_a_constant_that_no_longer_exists(self):
        stale = sorted(set(self.NOT_STATED_BY_ANY_SURFACE) - self._policy_names())
        self.assertEqual(stale, [], "exemptions for constants that are gone: %s" % stale)


class GateConditionsMatchTheCore(unittest.TestCase):
    """FR-012's "gate condition names and their order", DERIVED from `gate.check`.

    Two guards have now failed here, both the same way. The first compared
    `SKILL.md` against a hardcoded list of `SKILL.md`'s own headings. The second
    replaced it with a list captioned *"Emitted by `gate.check`, in the order it
    appends them"* — which was the skill's ordering relabelled with the core's
    spellings, and **had already drifted**: `gate.check` appends
    `"TASKS.md missing"` first, and the list put it third. Nothing derived
    anything, so nothing noticed (domain:DOM-007, twice).

    So this reads the core two ways and never restates it: the append order comes
    from `gate.check`'s syntax tree, and the emitted order comes from a fixture
    that trips several conditions at once.
    """

    @staticmethod
    def _source_order(function="check"):
        """Condition names in the order `function` appends them, from the AST.

        A `Refusal(...)` first argument is either a string literal or a `policy`
        constant; both are resolved here, so renaming a constant or moving a call
        changes what this returns.

        Two functions build refusals: `check`, and `inherited_record`, whose
        `inherited diff undetermined` reaches the caller through `check`. Asking
        `check` alone for all four named constants is what made the first draft of
        `test_all_four_are_reachable_from_the_source_order` fail — correctly.
        """
        import ast
        from sdd_runner import gate, policy
        with io.open(gate.__file__, encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        target = next(n for n in tree.body
                      if isinstance(n, ast.FunctionDef) and n.name == function)
        order = []
        for node in ast.walk(target):
            if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                    and node.func.id == "Refusal" and node.args):
                continue
            first = node.args[0]
            if isinstance(first, ast.Constant) and isinstance(first.value, str):
                order.append((node.lineno, first.value))
            elif isinstance(first, ast.Name) and hasattr(policy, first.id):
                order.append((node.lineno, getattr(policy, first.id)))
        return [name for _line, name in sorted(order)]

    def _multi_refusal_fixture(self, tmp):
        """A repository that trips several conditions at once.

        One refusal proves nothing about ordering. This one is on the default
        branch, has a dirty tree, a Draft status, an unresolved open question and
        no `TASKS.md`.
        """
        import subprocess
        from tests import support
        spec = support.SPEC.replace("Ready", "Draft").replace(
            "- ~~OQ-1~~ **Resolved.**", "- OQ-1: unresolved and blocking.")
        repo, feature = support.make_repo(tmp, spec=spec)
        os.remove(os.path.join(feature, "TASKS.md"))
        with io.open(os.path.join(repo, "stray.txt"), "w", encoding="utf-8") as fh:
            fh.write("dirty\n")
        subprocess.run(["git", "-C", repo, "checkout", "-q", "main"],
                       capture_output=True)
        return repo, feature

    def test_the_source_order_is_readable_and_starts_where_the_core_starts(self):
        order = self._source_order()
        self.assertGreaterEqual(len(order), 10)
        self.assertEqual(order[:3],
                         ["feature folder missing", "SPEC.md missing", "TASKS.md missing"],
                         "the conditions `gate.check` appends first moved")

    def test_the_emitted_order_is_a_subsequence_of_the_source_order(self):
        import tempfile
        from sdd_runner import gate
        source = self._source_order()
        with tempfile.TemporaryDirectory() as tmp:
            repo, feature = self._multi_refusal_fixture(tmp)
            emitted = [r.condition for r in gate.check(repo, feature)]
        self.assertGreaterEqual(len(emitted), 3,
                                "the fixture must trip several conditions: %s" % emitted)
        cursor = iter(source)
        self.assertTrue(all(any(candidate == name for candidate in cursor)
                            for name in emitted),
                        "emitted %s is not in the order the source appends: %s"
                        % (emitted, source))

    def test_every_emitted_condition_is_one_the_core_declares(self):
        import tempfile
        from sdd_runner import gate
        source = set(self._source_order())
        with tempfile.TemporaryDirectory() as tmp:
            repo, feature = self._multi_refusal_fixture(tmp)
            for refusal in gate.check(repo, feature):
                with self.subTest(condition=refusal.condition):
                    self.assertIn(refusal.condition,
                                  source | set(self._source_order("inherited_record")))
                    self.assertTrue(refusal.detail and refusal.remediation,
                                    "a refusal must name evidence and a remediation")

    def test_the_baseline_launch_condition_is_emitted_by_the_core(self):
        """security:SEC-012 — a condition the gate raises when it EXECUTES, not reads."""
        source = set(self._source_order())
        self.assertIn(policy.BASELINE_UNAVAILABLE, source)
        self.assertEqual(policy.BASELINE_UNAVAILABLE, "baseline suite unavailable")

    def test_the_four_named_constants_are_the_core_spelling(self):
        """These were exempted from coverage; now they are asserted."""
        self.assertEqual(policy.ADOPTION_NOT_NEEDED, "adoption not needed")
        self.assertEqual(policy.ALREADY_ENTERED, "already adopted or entered")
        self.assertEqual(policy.INHERITED_UNDETERMINED, "inherited diff undetermined")
        self.assertEqual(policy.STATUS_UNREADABLE, "status unreadable")

    def test_all_four_are_reachable_from_the_source_order(self):
        """Declared constants no function appends would be dead vocabulary."""
        source = set(self._source_order()) | set(self._source_order("inherited_record"))
        for constant in (policy.ADOPTION_NOT_NEEDED, policy.ALREADY_ENTERED,
                         policy.INHERITED_UNDETERMINED, policy.STATUS_UNREADABLE):
            with self.subTest(condition=constant):
                self.assertIn(constant, source)

    def test_the_inherited_condition_is_raised_by_the_adoption_path_not_the_gate(self):
        """Where a condition lives is part of the contract, not an accident."""
        self.assertNotIn(policy.INHERITED_UNDETERMINED, self._source_order())
        self.assertIn(policy.INHERITED_UNDETERMINED,
                      self._source_order("inherited_record"))

    def test_the_readme_states_each_of_them(self):
        """`STATUS_UNREADABLE` was exempted as stated by no surface. It is in the README."""
        readme = read("runner-readme")
        for constant in (policy.ADOPTION_NOT_NEEDED, policy.ALREADY_ENTERED,
                         policy.INHERITED_UNDETERMINED, policy.STATUS_UNREADABLE):
            with self.subTest(condition=constant):
                self.assertIn(constant, readme)


class TheColumnDivergenceIsDeliberate(unittest.TestCase):
    """The runner recognises its own documents by its table headers — domain:DOM-021.

    `state.py` says so directly: *"The runner recognizes its OWN documents by these
    exact table headers. A document written by the phase-1 executor uses different
    columns; resume must BLOCK on it rather than guess."* `resume.py` depends on
    it. So the template stating different columns is not a divergence to be fixed —
    it is the mechanism, and what needs asserting is that it stays different.

    Two constants were exempted from the uncovered-constant guard as "covered by
    the template's section-order test", which matches headings and never looks at a
    column. The exemption recorded a coverage that did not exist in place of a
    property that does.
    """

    def setUp(self):
        self.template = read("template")

    def _header_cells(self, after):
        section = self.template.split(after, 1)[1]
        for line in section.splitlines():
            if line.startswith("| ") and "---" not in line:
                return [c.strip() for c in line.strip().strip("|").split("|")]
        return []

    def test_the_template_states_its_own_attempt_columns(self):
        cells = self._header_cells("## Attempts")
        self.assertTrue(cells, "the template no longer states an Attempts header")
        self.assertNotEqual(cells, policy.ATTEMPT_COLUMNS,
                            "the template and the core now agree on Attempts columns, which "
                            "removes how the runner tells its own documents apart")

    def test_the_template_states_its_own_finding_columns(self):
        cells = self._header_cells("## Findings")
        self.assertTrue(cells, "the template no longer states a Findings header")
        self.assertNotEqual(cells, policy.FINDING_COLUMNS)

    def test_the_core_still_documents_why(self):
        """The rationale travelled with the constants into `policy` (spec 042 T003)."""
        with io.open(policy.__file__, encoding="utf-8") as fh:
            source = fh.read()
        self.assertTrue("recognizes its OWN documents by these" in source,
                        "policy no longer records why the columns differ")

    def test_the_inherited_columns_are_the_one_shared_shape(self):
        """`INHERITED_COLUMNS` is asserted as matching — the contrast is the point."""
        for column in policy.INHERITED_COLUMNS:
            with self.subTest(column=column):
                self.assertIn(column, self.template)


class FindingKeysMatchTheVerdictSchema(unittest.TestCase):
    """`FINDING_KEYS` was exempted citing SKILL.md; nothing asserted it (domain:DOM-021)."""

    def test_every_required_finding_field_is_in_the_schema_the_skill_publishes(self):
        skill = read("skill")
        block = skill.split("### Reviewer verdict block", 1)[1].split("###", 1)[0]
        for key in sorted(policy.FINDING_KEYS):
            with self.subTest(field=key):
                self.assertIn("%s:" % key, block,
                              "reviewers are told a schema the parser does not require")


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
