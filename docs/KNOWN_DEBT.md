# Known debt

Debt that was **accepted deliberately** at close time, not discovered later. One entry per item,
each naming what is unverified, what it would cost if the assumption is wrong, and what would
close it.

A spec may close with an unmet acceptance criterion only if the criterion is downgraded in its
`SPEC.md` (with a decision recording why) **and** the item lands here. Silently closing over an
unmet criterion is the failure this file exists to prevent.

This register is not a backlog. Ideas, nice-to-haves and refactors do not belong here — only
claims the repo currently makes that nobody has checked.

| ID | Item | Origin | Status |
|---|---|---|---|
| DEBT-001 | Codex isolation flags in `skill-eval.sh` are enforced but unverified | spec 028 | Open |
| DEBT-002 | Codex adapter advertised as prompt-based/unverified | spec 019 | Open |
| DEBT-003 | `skill-eval.test.sh` copies the whole repo 33 times per run | spec 028 | Open |
| DEBT-004 | The five `python-sql-data` reviewers ship uncalibrated against a real diff | spec 029 | Open |
| DEBT-005 | Hardcoded skill counts in `adapters/` and `docs/` are unguarded | spec 029 | Open |

---

## DEBT-001 — Codex isolation flags are enforced but unverified

**Origin:** spec 028 (`eval-runner-isolation`), FR-011/AC-011 downgraded by D011 on 2026-08-07.

**The unverified claim.** `scripts/skill-eval.sh` refuses a `codex exec` runner that lacks
`--ignore-user-config` or `--ephemeral`, and requires `--model` as its pin flag. That flag set
comes from a reviewed external implementation. **Nobody has run it against a real Codex CLI.** The
CLI is not installed on the maintainer's machine, and `iso-codex-happy` in the test suite is green
against a *planted* `codex` binary — it validates the harness's own logic and says nothing about
what the real CLI accepts.

**Cost if wrong.** The gate fails closed, so the failure mode is a hard block, not a silent leak:
the first operator with Codex installed cannot run the harness with a correct runner. Mitigated,
not removed, by AC-012 — the refusal message says the flag set is unverified, points here, and
names `--allow-unisolated`, so the operator can proceed with a downgraded artifact and report the
real flags.

**This file is a live dependency of that message.** `skill-eval.sh` sends blocked operators here
by path, and a self-test case asserts the file exists and documents the unverified provider. If
this register is renamed or moved, fix the message and that assertion in the same change.

**What closes it.** Install the Codex CLI, run one real `codex exec`, confirm the flag spellings
(including `--model` versus `-m`), record it in spec 028's `DECISIONS.md` as D008, and correct the
provider table row if they differ. This was task T013.

Then flip the row's fourth field from `unverified` to `verified` in `PROVIDER_TABLE`
([skill-eval.sh](../scripts/skill-eval.sh)). That field is what drives the caveat in the refusal
message, so the hedge disappears on its own — and the test
`claude refusal does not carry the unverified caveat` proves the field is actually load-bearing
rather than decorative.

**Related:** [[DEBT-002]] — same root cause, different surface. Both close the day someone
installs the CLI.

---

## DEBT-002 — Codex adapter advertised as prompt-based/unverified

**Origin:** spec 019 (`provider-aware-codex-adapter`), OQ-1 deferred at close.

**The unverified claim.** The exact Codex custom-prompt directory and config schema on the current
Codex release. The adapter is labeled prompt-based/unverified precisely because of this, so the
repo is not currently overclaiming — but the label has to stay until someone checks.

**Cost if wrong.** `adapters/codex/` ships prompts to a location the CLI may not read. A user
following `adapters/codex/README.md` gets an adapter that appears installed and does nothing.

**What closes it.** Verify against an installed Codex CLI before advertising the adapter as
verified.

**Recorded here** because it is the same missing prerequisite as DEBT-001 and was, until now,
visible only inside spec 019's open questions — where nothing joined it to the identical gap in
spec 028.

---

## DEBT-003 — The skill-eval self-test copies the whole repo 33 times per run

**Origin:** spec 028, `/qa-review` finding on 2026-08-07. Not a correctness issue.

**The problem.** `fresh_copy` does a full `cp -r` of the 9.1 MB repository per case, across 33
call sites — roughly 300 MB of I/O and 39 seconds per run, most of it system time.

**Cost.** The suite is local-only by design (`CONTRIBUTING.md`: deliberately off the CI path), so
its runtime is paid by whoever is iterating — the person most likely to start skipping it.

**What closes it.** The gate cases are pure refusals that abort before output-path resolution and
never write into the tree; they can share one copy. Only the mutating cases need isolation:
`missing-scenario`, the two `out-inside-skills` variants, and `unresolvable-out`.

## DEBT-004 — The five python-sql-data reviewers ship uncalibrated

**Origin:** spec 029, T026, deferred at close on 2026-08-23.

`python-reviewer`, `python-testing-reviewer`, `sql-query-reviewer`,
`database-performance-reviewer` and `data-pipeline-reviewer` were written from domain knowledge and
never run against a real Python + SQL diff. Every acceptance criterion spec 029 defined is met and
verified — the profile installs, the contracts are well-formed, the routing is correct — but **none
of them asks whether the checklists actually catch anything**. Structural conformance is not the
same as usefulness, and the spec closed on the former.

**Why it was not closed with the spec:** calibration needs a real diff from live work. Inventing one
would produce exactly the self-designed fixture that spec 031's T023 was written to distrust: the
same agent authoring the diff, the checklist and the verdict.

**How to retire it:** run all five skills against a genuine Python + SQL change and adjust the
checklists from what they caught and what they missed. The maintainer works in Python and SQL daily,
so the input exists — it just has to be a real one.

**Risk while open:** the reviewers may be verbose where it does not matter and silent where it does.
They are advisory, so the failure mode is wasted attention, not a broken build.

## DEBT-005 — Hardcoded skill counts in adapters/ and docs/ are unguarded

**Origin:** spec 029, T027, skipped at close on 2026-08-23.

`scripts/check-consistency.sh` guards the count markers in `README.md`, but equivalent hardcoded
counts in `adapters/` and `docs/` have no guard. They drift silently every time a skill is added —
and spec 029 added five.

**Why it was skipped rather than done:** T027's own text says *"Framework-wide change, deliberately
out of scope here"*. It is a change to the consistency checker, not to the profile spec 029 shipped.

**How to retire it:** extend the existing count-marker mechanism to those files, following the
pattern already proven in `README.md`. Small and mechanical once someone decides to own it.

**Risk while open:** documentation can state a count that no longer matches disk. Same class of
defect as spec 034's manifest, one layer up: a record asserting a state nothing verifies.
