"""Prove each contract guard actually fails. Mutate, run, revert, record.

Spec 042, evidence for AC-006. This lives **inside the feature's evidence** and
not in a scratch directory: `CONTRACT_MUTATIONS.md` is stamped GENERATED, and an
artifact whose generator nobody can read is an artifact whose provenance cannot be
re-checked (domain:DOM-024 / security:SEC-010).

Run from the repository root:

    python3 specs/features/042-canonical-autonomous-core/evidence/mutation_harness.py
"""
import io, os, shutil, subprocess, sys

# Four levels up from evidence/: .../specs/features/<feature>/evidence/harness.py
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "..", "..", "..", ".."))
MUTATIONS = [
    ("cli", "runner/sdd_runner/__main__.py", '"--dry-run"', '"--dry-runX"'),
    ("skill", "skills/sdd-orchestrate/SKILL.md",
     "**`severity` is a closed enum: `Critical | High | Medium | Low`.**",
     "**`severity` is a closed enum: `Blocker | Major | Minor`.**"),
    ("template", "skills/sdd-orchestrate/templates/ORCHESTRATION.md",
     "- Protocol version: `1`", "- Protocol version: `2`"),
    ("runner-readme", "runner/README.md", "`max(25, 6 x unchecked tasks)`",
     "`max(30, 6 x unchecked tasks)`"),
    ("orchestration-doc", "docs/SDD-ORCHESTRATION.md", "max(25, 6 × unchecked tasks)",
     "max(99, 6 × unchecked tasks)"),
    ("domain-reviewer", "agents/domain-reviewer.md", "Critical | High | Medium | Low",
     "Blocker | Major | Minor | Nit"),
    ("final-conformance-reviewer", "agents/final-conformance-reviewer.md",
     "Critical | High | Medium | Low", "Blocker | Major | Minor | Nit"),
    ("codex-parity", "adapters/codex/PARITY.md", "adoption header fields",
     "adoption metadata"),
    ("counter-eval", "evals/scenarios/orchestrate-per-finding-counter.md",
     "`max-delegations` is 25", "`max-delegations` is 26"),
    ("core (policy.FLOOR)", "runner/sdd_runner/policy.py", "FLOOR = 25", "FLOOR = 30"),
    # Added after the reviews: the two mutations the first pass never tried, and
    # whose absence is why DOM-001 and DOM-012 survived behind a green suite.
    ("core (policy.READY_STATUSES)", "runner/sdd_runner/policy.py",
     'READY_STATUSES = ("Ready",)', 'READY_STATUSES = ("Approved",)'),
    ("orchestration-doc (authority)", "docs/SDD-ORCHESTRATION.md",
     "semantics, **the skill is wrong**", "semantics, **the runner is wrong**"),
    ("template (version readability)", "skills/sdd-orchestrate/templates/ORCHESTRATION.md",
     "- Protocol version: `1`", "- Protocol version: `notanumber`"),
    # T057: the disposition must be STATED. Falsifying the one assignment that
    # states it has to turn the suite red, or the field is decoration and the
    # inference it replaced could come back unnoticed.
    ("core (loop_completed stated)", "runner/sdd_runner/protocol.py",
     "escalations=tuple(outcome.escalations), loop_completed=True)",
     "escalations=tuple(outcome.escalations), loop_completed=False)"),
    # MNT-003: the producer mutation above protects who SETS the field. This one
    # protects who READS it — dropping it from the CLI's notify condition would
    # make an internal error emit `run-finished`, which the producer mutation
    # cannot see.
    # D015: the audit gate. Falsifying the raise means a run whose transcript is
    # gone keeps going and reports normally — the outcome the maintainer refused.
    ("core (audit failure raises)", "runner/sdd_runner/loop.py",
     "            raise AuditUnavailable(event, self.log.write_failures)",
     "            pass  # MUTATION"),
    ("cli (notify reads loop_completed)", "runner/sdd_runner/__main__.py",
     "    if notify and outcome.loop_completed and outcome.gate.passed \\\n"
     "            and not outcome.awaiting_human:",
     "    if notify and outcome.gate.passed \\\n"
     "            and not outcome.awaiting_human:"),
    # CONF-006 / D018. The guard over the `main` baselines claims it fails when
    # `DIFF-003` leaves FR-009's block. Nobody had checked that claim, and an
    # unchecked guard over an authorised difference is how the difference got into
    # the tree unnoticed in the first place.
    ("spec (DIFF-003 authorised)",
     "specs/features/042-canonical-autonomous-core/SPEC.md",
     "    - id: DIFF-003", "    - id: DIFF-00X"),
    # And the behaviour the transcript pair pins: rename the condition and the
    # recorded refusal stops matching, on both the current side and the nine
    # byte-identical baselines' sibling check.
    ("core (policy.BASELINE_UNAVAILABLE)", "runner/sdd_runner/policy.py",
     'BASELINE_UNAVAILABLE = "baseline suite unavailable"',
     'BASELINE_UNAVAILABLE = "baseline suite missing"'),
]

def clear_bytecode():
    """`FLOOR = 25` and `FLOOR = 30` are the same length, so a same-second revert
    left a stale .pyc that Python's mtime+size check accepted. Found the hard way."""
    for dirpath, dirs, _f in os.walk(os.path.join(ROOT, "runner")):
        for d in list(dirs):
            if d == "__pycache__":
                shutil.rmtree(os.path.join(dirpath, d), ignore_errors=True)


def run_suite():
    clear_bytecode()
    env = dict(os.environ, PYTHONPATH=os.path.join(ROOT, "runner"))
    proc = subprocess.run([sys.executable, "-m", "unittest", "tests.contract.test_surfaces", "tests.contract.test_protocol_version",
                           "tests.contract.test_outcome_and_logging",
                           "tests.integration.test_transcript_loss_reporting",
                           "tests.contract.test_audit_gate",
                           "tests.contract.test_identity_task_refs",
                           # CONF-006: the two mutations above are invisible to
                           # every module before this line.
                           "tests.contract.test_main_baselines",
                           "tests.contract.test_gate_refusal_coverage"],
                          cwd=ROOT, env=env, capture_output=True, text=True, timeout=180)
    return proc.returncode, proc.stderr

def _core_row_summary(rows):
    """Derived from the table, so it cannot age into a lie."""
    # Executable, not "under runner/": `runner/README.md` is a prose surface that
    # happens to live beside the package, and counting it as core made the derived
    # sentence false in a new way — the failure this derivation exists to end.
    def _executable(rel):
        return rel.endswith(".py")

    core = [n for n, rel, _v, _d in rows if _executable(rel)]
    docs = [n for n, rel, _v, _d in rows if not _executable(rel)]
    return ("**%d of the %d mutations target the core or the CLI** (%s); the remaining %d target a "
            "prose surface." % (len(core), len(rows), ", ".join("`%s`" % c for c in core),
                                len(docs)))


rows = []
for name, rel, old, new in MUTATIONS:
    path = os.path.join(ROOT, rel)
    original = io.open(path, encoding="utf-8").read()
    hits = original.count(old)
    if hits != 1:
        # Not "skip and carry on": a mutation that did not happen is not evidence,
        # and recording it as SKIPPED beside fifteen CAUGHT rows is how this file
        # came to claim 16 of 16 while one anchor had silently rotted
        # (`maintainer:MNT-008`). Exactly one match, or the run fails.
        rows.append((name, rel, "**ANCHOR ROTTED**",
                     "expected exactly 1 occurrence, found %d: %r" % (hits, old)))
        continue
    io.open(path, "w", encoding="utf-8").write(original.replace(old, new, 1))
    code, err = run_suite()
    io.open(path, "w", encoding="utf-8").write(original)
    assert io.open(path, encoding="utf-8").read() == original, "revert failed for " + rel
    failed = [l for l in err.splitlines() if l.startswith("FAIL:")]
    rows.append((name, rel, "CAUGHT" if code != 0 else "MISSED",
                 "%d guard(s): %s" % (len(failed),
                                      "; ".join(f.split("(")[0].replace("FAIL: ","").strip()
                                                for f in failed[:3]) or "-")))
    print("%-28s %s" % (name, rows[-1][2]), flush=True)

code, _ = run_suite()
suite_green = code == 0
not_caught = [r for r in rows if r[2] != "CAUGHT"]
print("\nsuite after all reverts:", "GREEN" if suite_green else "RED")
print("verdicts:", ", ".join("%d %s" % (sum(1 for r in rows if r[2] == v), v)
                             for v in sorted({r[2] for r in rows})))
io.open(os.path.join(ROOT, "specs/features/042-canonical-autonomous-core/evidence/CONTRACT_MUTATIONS.md"),
        "w", encoding="utf-8").write(
"""# Contract-guard mutation evidence — T015 / AC-006

<!-- GENERATED by evidence/mutation_harness.py. Rewritten on every run; narrative
     added here is destroyed, and any claim written here by hand will age silently.
     The lessons live in CONTRACT_MUTATIONS_LESSONS.md, written by hand. -->

Each protocol surface was mutated in one normative value, the contract suite was run, and the
mutation was reverted and verified byte-identical. A row reading **CAUGHT** means the guard failed
as it should; **MISSED** would mean the guard is decorative.

Reproduce with `python3 specs/features/042-canonical-autonomous-core/evidence/mutation_harness.py`
from the repository root. It reverts every file it touches and asserts the revert before moving on.

| Surface | File | Verdict | Guards that fired |
|---|---|---|---|
""" + "\n".join("| %s | `%s` | **%s** | %s |" % r for r in rows) + """

**Suite state after all reverts: %s.** (The suite runs once, at the end — an earlier version of
this line said "after every revert", which it never did.)

%s

Mutating the **core** rather than a document matters as much as the other direction: it proves the
guards compare the two sides rather than each checking itself. The `core (policy.FLOOR)` row is the
worked example — changing 25 to 30 breaks every surface that states the budget formula.

*An earlier version of this paragraph said "the last row" and named `policy.FLOOR`. Rows were added
after it was written, so the claim aged into a falsehood that every regeneration restored
(domain:DOM-024 / security:SEC-010). It is derived from the table now.*
""" % ("GREEN" if code == 0 else "RED", _core_row_summary(rows)))

if not_caught:
    print("\nFAILED: %d mutation(s) did not produce a caught failure:" % len(not_caught))
    for name, _rel, verdict, detail in not_caught:
        print("  %-34s %-18s %s" % (name, verdict, detail))
if not suite_green:
    print("\nFAILED: the suite is red after the reverts.")
sys.exit(1 if (not_caught or not suite_green) else 0)
