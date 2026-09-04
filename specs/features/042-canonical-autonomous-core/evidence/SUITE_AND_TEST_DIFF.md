# Suite count and test-diff evidence — T050 / AC-005

<!-- Every figure below was produced by the command shown above it, against the tree as it stands.
     Regenerate with the same commands; `test_ac005_evidence.py` fails if this file goes empty,
     loses a section, or states a count the tree has moved past. -->

> **Superseded counts, kept visible.** This file has recorded `Ran 362 tests`, then `Ran 395`, then
> `Ran 441`, then `Ran 474`. Each was true when written and stale when read — `domain:DOM-019`,
> raised three times. The third occurrence was worse than a stale figure: the file was **emptied**
> by a truncate-before-read bug in the command meant to update its count
> (`open(p,"w").write(open(p).read()...)` truncates before the read runs), and no test in the suite
> read the artifact, so 448 passing tests could not see that AC-005's evidence had ceased to exist.
> The guard added with this repair is the answer to that, not the corrected number.
>
> **The guard makes this file a fixpoint, on purpose.** `test_ac005_evidence` derives the count from
> the tree and compares it with the figure recorded here, so **adding or removing any test fails the
> suite until this artifact is regenerated**. That is the discipline DOM-019 asked for three times:
> evidence for an acceptance criterion has to be re-run, not remembered.
>
> **The derivation command was wrong, and is corrected here (`conformance:CONF-006`).** It read
> `sum(1 for _ in unittest.TestLoader().discover(...))`, which counts the suite's **direct
> children** — 42 — not its tests. The figure beside it was never what that command produced; it
> came from the guard, which flattens recursively. A number attributed to a command that cannot
> produce it is DOM-019's defect in its purest form: unreproducible evidence that looks reproducible.
> The command below now flattens the same way `discovered_test_count()` does, and both agree.

## Count

```
$ PYTHONPATH=runner python3 -m unittest discover -s runner/tests -t runner
Ran 494 tests
OK
```

Independently derived, counted the way the suite runs it, so the figure and the tree cannot drift
apart:

```
$ PYTHONPATH=runner python3 -c "import unittest; \
    s = unittest.TestLoader().discover('runner/tests', top_level_dir='runner'); \
    c = lambda n: sum(c(x) for x in n) if hasattr(n, '__iter__') else 1; print(c(s))"
494
```

Baseline on `main` was **276**. AC-005's floor is "at least 276, all passing"; the suite is above it
because this feature adds contract tests, not because anything was relaxed. Run on a machine with
neither the Claude Agent SDK nor a usable Codex CLI installed.

## No assertion was weakened

```
$ git diff main -- runner/tests | grep -E "^-" | grep -vE "^---" | grep -E "assert|self\.fail"
(no output)
```

**Not one deleted or altered assertion line** across the whole test tree. This is the evidence
AC-005 names: a reviewer can see the assertion-level diff is import-only.

## What changed in the test tree, counted correctly

`git diff --name-only` **cannot see a file that is not yet tracked**, and this feature added 8 of
them — so an earlier version of this section reached its conclusion with a command blind to the
thing it claimed. The honest measure is the union:

```
$ { git diff --name-only main...HEAD -- runner/tests; \
    git ls-files --others --exclude-standard -- runner/tests; } | sort -u
```

| | Count | Files |
|---|---|---|
| **Tracked, modified** | 12 | `conformance/PROTOCOL_TRANSCRIPTION.md`, `conformance/test_transcription.py`, `contract/__init__.py`, `contract/capture_golden.py`, `contract/golden.py`, `contract/test_golden_cli.py`, `contract/test_interface.py`, `contract/test_packaging.py`, `contract/test_policy.py`, `contract/test_protocol_version.py`, `contract/test_public_lifecycle.py`, `contract/test_surfaces.py` |
| **New, untracked** | 8 | `contract/test_ac005_evidence.py`, `contract/test_audit_gate.py`, `contract/test_containment_and_ordering.py`, `contract/test_gate_refusal_coverage.py`, `contract/test_identity_task_refs.py`, `contract/test_main_baselines.py`, `contract/test_outcome_and_logging.py`, `integration/test_transcript_loss_reporting.py` |

Of the pre-existing test modules outside `contract/`, 3 were touched (`conformance/PROTOCOL_TRANSCRIPTION.md`, `conformance/test_transcription.py`, `integration/test_transcript_loss_reporting.py`), and additively: T018
registered more modules with the transcription guard and added
`test_no_row_is_silently_unchecked`. Every other pre-existing test file is byte-identical to `main`.

Every figure in this section is regenerated from the two commands above, so the counts, the file
lists and the prose cannot drift apart. They did once: the untracked row said `6` while naming five
files and the prose still said "five", because a regeneration updated the number and not the list —
the continuation of `domain:DOM-019` repaired under T050. `test_ac005_evidence` now compares them
structurally.

That is the evidence for D001: keeping the package name cost one slightly-wrong word and bought a
diff in which every changed line is the refactor itself.
