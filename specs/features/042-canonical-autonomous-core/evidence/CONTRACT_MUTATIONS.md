# Contract-guard mutation evidence — T015 / AC-006

Each protocol surface was mutated in one normative value, the contract suite was run, and the
mutation was reverted and verified byte-identical. A row reading **CAUGHT** means the guard failed
as it should; **MISSED** would mean the guard is decorative.

Reproduce with the script recorded in this feature's scratch notes; it reverts every file it
touches and asserts the revert before moving on.

| Surface | File | Verdict | Guards that fired |
|---|---|---|---|
| cli | `runner/sdd_runner/__main__.py` | **CAUGHT** | 1 guard(s): test_every_flag_is_still_offered |
| skill | `skills/sdd-orchestrate/SKILL.md` | **CAUGHT** | 1 guard(s): test_the_severity_enum_is_the_closed_one |
| template | `skills/sdd-orchestrate/templates/ORCHESTRATION.md` | **CAUGHT** | 1 guard(s): test_it_records_the_protocol_version |
| runner-readme | `runner/README.md` | **CAUGHT** | 1 guard(s): test_the_budget_formula_matches_policy |
| orchestration-doc | `docs/SDD-ORCHESTRATION.md` | **CAUGHT** | 1 guard(s): test_the_budget_formula_matches_policy |
| domain-reviewer | `agents/domain-reviewer.md` | **CAUGHT** | 1 guard(s): test_the_severity_enum_is_closed_in_both |
| final-conformance-reviewer | `agents/final-conformance-reviewer.md` | **CAUGHT** | 1 guard(s): test_the_severity_enum_is_closed_in_both |
| codex-parity | `adapters/codex/PARITY.md` | **CAUGHT** | 1 guard(s): test_it_claims_the_same_adoption_entry |
| counter-eval | `evals/scenarios/orchestrate-per-finding-counter.md` | **CAUGHT** | 1 guard(s): test_the_default_budget_it_assumes_matches_policy |
| core (policy.FLOOR) | `runner/sdd_runner/policy.py` | **CAUGHT** | 5 guard(s): test_the_default_budget_it_assumes_matches_policy; test_the_budget_formula_matches_policy; test_the_budget_formula_matches_policy |

**Suite state after every revert: GREEN.**

The last row mutates the **core** rather than a document: changing `policy.FLOOR` from 25 to 30
breaks the surfaces that state the budget formula. That direction matters as much as the other —
it proves the guards compare the two sides rather than each checking itself.

## What the first run found

The first pass reported **two MISSED** and left the suite red. All three problems were in the
harness or the guards, not in the code under test, and each is worth keeping:

1. **`skill` MISSED — a mention is not a declaration.** The guard asserted the enum string appeared
   somewhere in `SKILL.md`. It appears twice: in the closed-enum declaration *and* in the verdict
   block example. Mutating the declaration left the example, and the guard stayed green. Fixed by
   pinning the declaration (`closed enum: \`…\``), not the vocabulary.

2. **`orchestration-doc` MISSED — `re.search` reads one occurrence.** `docs/SDD-ORCHESTRATION.md`
   states the budget formula twice. Mutating one left the other, and the guard read the survivor.
   Fixed with `findall` over every occurrence, plus an assertion that at least one exists so a
   deleted formula cannot pass as "all zero of them agree".

3. **The suite was red after every file had been reverted.** `FLOOR = 25` and `FLOOR = 30` are the
   same number of bytes, so the revert produced a file with the same size and, within one
   filesystem timestamp tick, the same mtime — and CPython's `.pyc` validity check is
   mtime-plus-size. The stale bytecode was used. The harness now clears `__pycache__` before each
   run. Any future mutation harness in this repository has the same trap waiting for it.

None of these was found by reading the guards. All three were found by running them against a
change they were supposed to catch, which is the argument for AC-006 requiring demonstrated
failure rather than existence.
