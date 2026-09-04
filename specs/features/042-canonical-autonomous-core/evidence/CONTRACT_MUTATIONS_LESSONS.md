# Mutation-testing lessons — spec 042

`CONTRACT_MUTATIONS.md` next to this file is **generated**: the harness rewrites it on every run, so
nothing narrative may live there. This file is written by hand and holds what the runs taught, which
is worth more than the table.

## First pass — 8 of 10 caught, suite left red

> The table beside this file is regenerated on every run and its totals move; the
> figures quoted below are the ones each pass reported at the time, and are history
> rather than a current claim. `CONTRACT_MUTATIONS.md` is the live count.

Three problems, all in the harness or the guards rather than the code under test:

1. **`skill` MISSED — a mention is not a declaration.** The guard asserted the severity enum appeared
   *somewhere* in `SKILL.md`. It appears twice: in the closed-enum declaration and in the verdict
   block example. Mutating the declaration left the example, and the guard stayed green. Fixed by
   pinning the declaration (`closed enum: \`…\``), not the vocabulary.

2. **`orchestration-doc` MISSED — `re.search` reads one occurrence.** `docs/SDD-ORCHESTRATION.md`
   states the budget formula twice; mutating one left the other for the guard to read. Fixed with
   `findall` over every occurrence, plus an assertion that at least one exists so a deleted formula
   cannot pass as "all zero of them agree".

3. **The suite was red after every file had been reverted.** `FLOOR = 25` and `FLOOR = 30` are the
   same number of bytes, so the revert produced a file with the same size and, within one filesystem
   timestamp tick, the same mtime — and CPython's `.pyc` validity check is mtime-plus-size. The stale
   bytecode was used. The harness now clears `__pycache__` before each run.

None of these was found by reading the guards. All three came from running them against a change
they were supposed to catch, which is the argument for AC-006 requiring demonstrated failure rather
than existence.

# Second mutation pass — after the reviews

Three mutations were added because the reviews proved their absence had hidden real defects. The
lesson from the first pass — *a mutation test proves a guard catches the mutation you thought of* —
turned out to be the finding, not the footnote:

| Added mutation | The defect it would have caught | Found instead by |
|---|---|---|
| `policy.READY_STATUSES` → `("Approved",)` | `test_the_first_entry_statuses_match_policy` rewrote the surface text and asserted a hardcoded `"Ready"`, never reading policy at all | domain:DOM-012 |
| `docs/SDD-ORCHESTRATION.md` authority sentence restored | The AC-012 guard matched only `this runner is wrong`; the document said `the runner is wrong` and survived the whole feature | domain:DOM-001 |
| Template version → `notanumber` | The template guard was a whole-file substring match, so it could not tell a readable field from an unreadable one | security:SEC-001 / domain:DOM-003 |

**16 of 16 caught. Suite green after all reverts** — the harness runs the suite once, at the end.
The earlier wording named a per-revert check nobody performs (`maintainer:MNT-008`, re-reported as
`security:SEC-016` / `domain:DOM-029`).

The first pass reported 10 of 10 and was recorded as complete. It was complete *against the
mutations that were written*, and the three that mattered most were not among them — each because
the guard was written first and the mutation chosen to match it, rather than the other way round.
The reviews found all three from the other direction: by reading what the guard actually asserts.


## Third pass — after round 4

Sixteen mutations, sixteen caught, suite green after all reverts. Three were added by this round,
and each exists because something got through without it:

| Mutation | What it protects |
|---|---|
| `core (audit failure raises)` | Deleting the `AuditUnavailable` raise makes a run whose transcript is gone keep going and report normally — the outcome D015 refused. |
| `cli (notify reads loop_completed)` | The producer-side mutation protects who *sets* the disposition; this protects who *reads* it. `maintainer:MNT-003` lived in the gap. |
| `core (policy.READY_STATUSES)` | Added in the second pass, after `domain:DOM-012` showed a guard that never read `policy` at all. |

The closing paragraph of the generated file is now **derived from the table** rather than written by
hand. It said *"the last row mutates the core… `policy.FLOOR`"*, which was true when written and
false four rows later, and the file is regenerated on every run so every run restored the falsehood
(`domain:DOM-024` / `security:SEC-010`). Its first derived version was also wrong — it classified
`runner/README.md` as core because the path starts with `runner/` — which is the same failure in a
smaller form, and is why the classifier now asks whether the file is executable rather than where it
lives.

The harness itself moved out of a scratch directory and into this folder for the same reason: an
artifact stamped GENERATED whose generator nobody can read has provenance that cannot be re-checked.


## Fourth pass — CONF-006

Eighteen mutations, eighteen caught, suite green after all reverts. Two were added, both because
`conformance:CONF-006` recorded a new authorised difference and the guard over it had never been
falsified:

| Mutation | What it protects |
|---|---|
| `spec (DIFF-003 authorised)` | `test_main_baselines` claims it fails when `DIFF-003` leaves FR-009's block. Nothing had checked that claim — and an unchecked guard over an authorised difference is exactly how `DIFF-003` reached the tree unnoticed in the first place. |
| `core (policy.BASELINE_UNAVAILABLE)` | Renaming the condition must break the recorded refusal. Without it the transcript pair could have been pinning a string nobody emits. |

Running them meant widening the harness's suite: every module it ran was blind to both, so both would
have read CAUGHT-by-accident or, worse, MISSED for the wrong reason. `test_main_baselines` and
`test_gate_refusal_coverage` are now in it.

**Per-pass totals are dated records.** Each section above states the figure for its own pass and
nothing more; the live table is `CONTRACT_MUTATIONS.md`, regenerated by the harness, and the harness
exits non-zero on any row that is not CAUGHT.
