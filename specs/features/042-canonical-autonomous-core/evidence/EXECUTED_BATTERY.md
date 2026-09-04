# Executed battery — T076 / `conformance:CONF-005`, final re-run for `conformance:CONF-009…012`

<!-- Every line below was produced by running the command shown, on the tree named
     in the fingerprint. Nothing here is read off another artifact. -->

**Fingerprint this ran against**

| | |
|---|---|
| HEAD | `8242fcd` on `feature/042-canonical-autonomous-core` |
| Paths in scope | 97 (`main...HEAD`, tracked working-tree changes, and untracked, **excluding this file**) |
| Tree digest | `e19066bd78aded16361a86c21e7cdccfa7ac8ca210237a75ee556442f742cada` |
| Date | 2026-09-04 |

**Why this file exists.** The first T025 pass had no shell. It verified AC-004, AC-005, AC-006,
AC-008, AC-009 and two of AC-013's four checks by **reading artifacts and guard code**, and said so.
That is a documentary pass, not an executed one, and `conformance:CONF-005` was raised so nobody
later mistakes the one for the other.

**A defect in the first attempt at this file, recorded rather than hidden.** Its runner ended every
command with `| tail -3`, so the exit code persisted was `tail`'s and not the command's — and a
suite with **two failures** was written down as `exit: 0`. The failures were real (two volatile
totals that CONF-003's new scenarios had moved) and were repaired.

**This final re-run.** The runner writes each command's output to its own file and reads `$?`
immediately, with no pipeline between the command and its status. The fingerprint now also includes
tracked changes present only in the working tree. The preceding command omitted four such paths —
`docs/KNOWN_DEBT.md`, `docs/SDD-ORCHESTRATION.md`, `runner/sdd_runner/log.py`, and
`runner/sdd_runner/tasks.py` — so its 93-path digest did not authenticate the full tree even though
the tests ran against those bytes (`conformance:CONF-009`). This run covers all 97 reviewable paths.

**The digest excludes this file, and must.** A digest over a set that contains the artifact carrying
it cannot be recomputed: writing the number changes the number. The previous version of this file
recorded a digest taken before it was written and did not say so, which is a figure no reader can
reproduce. Recompute with:

```
$ ART=specs/features/042-canonical-autonomous-core/evidence/EXECUTED_BATTERY.md
$ { git diff --name-only main...HEAD; git diff --name-only HEAD; \
    git ls-files --others --exclude-standard; } | sort -u \
    | grep -v "^$ART$" | while read -r p; do [ -f "$p" ] && shasum -a 256 "$p"; done \
    | sort | shasum -a 256
```

## Results

### focused: public interface + lifecycle + refs + ac005

```
$ PYTHONPATH=runner python3 -m unittest tests.contract.test_interface \
    tests.contract.test_public_lifecycle tests.contract.test_ac005_evidence \
    tests.contract.test_identity_task_refs
Ran 52 tests in 4.331s
OK
```

exit: **0**

### full suite

```
$ PYTHONPATH=runner python3 -m unittest discover -s runner/tests -t runner
Ran 494 tests in 130.197s
OK
```

exit: **0**

### golden replay (capture_golden)

```
$ PYTHONPATH=runner python3 runner/tests/contract/capture_golden.py
  stable    refusal-tasks-missing
  stable    stub-script-wrong-backend
  stable    unresumable-state
30 scenario(s); 30 stable, 0 changed
```

exit: **0**

### main baselines re-capture --check

```
$ python3 specs/features/042-canonical-autonomous-core/evidence/capture_main_baselines.py --check
checked 10 baselines against 141638b: stable
```

exit: **0**

### mutation harness

```
$ python3 specs/features/042-canonical-autonomous-core/evidence/mutation_harness.py
spec (DIFF-003 authorised)   CAUGHT
core (policy.BASELINE_UNAVAILABLE) CAUGHT
suite after all reverts: GREEN
verdicts: 18 CAUGHT
```

exit: **0**

### compileall -W error::SyntaxWarning

```
$ python3 -W error::SyntaxWarning -m compileall -q -f runner/sdd_runner runner/tests \
(no output)
```

exit: **0**

### check-consistency

```
$ bash scripts/check-consistency.sh
Consistency check passed: profiles.json, disk artifacts, settings wiring, and README counts are aligned.
```

exit: **0**

### installers byte-identical to main

```
$ git diff --stat main...HEAD -- install.sh install.ps1 profiles.json
(no output)
```

exit: **0**

### git diff --check

```
$ git diff --check
(no output)
```

exit: **0**

### AC-013a: prompt file untracked

```
$ git ls-files --error-unmatch docs/AUTONOMOUS_SDD_FEATURE_PROMPT.md
error: pathspec 'docs/AUTONOMOUS_SDD_FEATURE_PROMPT.md' did not match any file(s) known to git
Did you forget to 'git add'?
```

exit: **1**

**Exit 1 is the required result.** `--error-unmatch` fails precisely because the file is not tracked, which is what AC-013 demands.

### AC-013b: prompt file shows ??

```
$ git status --porcelain --untracked-files=all -- docs/AUTONOMOUS_SDD_FEATURE_PROMPT.md
?? docs/AUTONOMOUS_SDD_FEATURE_PROMPT.md
```

exit: **0**

### AC-013c: prompt sha256 matches baseline

```
$ shasum -a 256 docs/AUTONOMOUS_SDD_FEATURE_PROMPT.md > $t && diff $t \
(no output)
```

exit: **0**

### AC-013d: prompt absent from main...HEAD

```
$ git diff --name-status main...HEAD -- docs/AUTONOMOUS_SDD_FEATURE_PROMPT.md
(no output)
```

exit: **0**

### state round-trip

```
$ PYTHONPATH=runner python3 -m unittest tests.unit.test_state
Ran 10 tests in 0.004s
OK
```

exit: **0**

### findings/task_ref validation

```
$ python3 - <<'PY'  # registry_task_refs against TASKS.md
identities=66 canonical_tasks=54 broken=0
tasks=83 checked=80 unchecked=['T025', 'T026', 'T027']
conformance:CONF-009 -> ['T080']
conformance:CONF-010 -> ['T081']
conformance:CONF-011 -> ['T082']
conformance:CONF-012 -> ['T083']
```

exit: **0**

### 15/15 gate condition matrix

```
$ python3 - <<'PY'  # gate.py AST vs COVERAGE
emitted=15 covered=15 uncovered=[]
```

exit: **0**
