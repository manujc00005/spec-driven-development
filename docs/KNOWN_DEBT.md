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
| DEBT-006 | Four `plannedHooks` remain planned and unowned | spec 017 | Open |
| DEBT-007 | `install.ps1` has never been run on real Windows outside CI | spec 016 | Open |
| DEBT-008 | The scope-keeper hook has never been observed firing in a live session | spec 036 | Open |
| DEBT-009 | The runner has never executed against a real provider, or from `cron` | spec 040 | Open |
| DEBT-010 | The adopted loop has never reached a human-gated `PAUSED` outside a fixture | spec 041 | Open |

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

> **2026-09-02 — the premise is dead; two of the three closing steps are done.** The Codex CLI **is**
> installed on the maintainer's machine (`codex-cli 0.152.1`, `~/.local/bin/codex`), so every
> sentence above claiming it is not is superseded. Real `codex exec` runs were made during spec 041's
> T013 and are recorded in
> [041/CALIBRATION.md](../specs/features/041-autonomous-adopt-in-flight-feature/CALIBRATION.md).
> Against `codex exec --help` on that version, all three required flags exist with the spellings
> `PROVIDER_TABLE` uses: `--ignore-user-config`, `--ephemeral`, and `--model` (with `-m` as its short
> alias, so the long form the table pins is correct). **Nothing in the table needs correcting.**
> What is still owed before flipping the row's fourth field to `verified` belongs to spec 028, not to
> 041: a recorded run of `scripts/skill-eval.sh` itself with that runner, and the D008 entry in spec
> 028's `DECISIONS.md`. Flipping the field from another feature's session would be the silent
> cross-spec edit this register exists to prevent.

Then flip the row's fourth field from `unverified` to `verified` in `PROVIDER_TABLE`
([skill-eval.sh](../scripts/skill-eval.sh)). That field is what drives the caveat in the refusal
message, so the hedge disappears on its own — and the test
`claude refusal does not carry the unverified caveat` proves the field is actually load-bearing
rather than decorative.

**Also load-bearing for spec 040.** The runner's `codex` backend is implemented but refuses to
run without `--allow-unverified-backend`, and its refusal message names this entry by ID. Spec 040
D004 accepted that gate rather than shipping a prose-only Codex path — which is how DEBT-002 came
to exist — so this debt now blocks two features, not one. The runner's test
`test_the_flags_are_still_unverified` fails if `FLAGS_VERIFIED` is flipped without a recorded real
run.

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

> **2026-09-02 — partially advanced, not closed.** The CLI is installed (see [[DEBT-001]]), and
> `$CODEX_HOME/prompts` — the directory `adapters/codex/install-codex.sh` targets — exists at
> `~/.codex/prompts` and already holds eight SDD prompt files, so the *write* half of the assumption
> is real on this version. Three caveats keep this open. First, whether the CLI actually **reads**
> that directory could not be shown here: custom prompts surface as slash commands in the interactive
> TUI, and `codex exec` offers no way to demonstrate it non-interactively. Second, the installed
> copies have drifted from source — `sdd-spec-implement.md`, `sdd-spec-plan.md`, `sdd-spec-analyze.md`
> and `README.md` differ, and `sdd-workspace-onboarding.md` was never installed — so an operator
> reading `adapters/codex/README.md` today gets a partial adapter. Third, `config.example.toml` is
> still unverified against this version's real key names. Closing this needs an interactive Codex
> session that invokes one installed prompt by name, plus a re-run of the installer.

**What closes it.** Verify against an installed Codex CLI before advertising the adapter as
verified.

**Also load-bearing for spec 040**, alongside [[DEBT-001]]: the runner's Codex backend cites both
IDs in the message it refuses with, and spec 040's SPEC forbids claiming multi-backend parity
anywhere until a real `codex exec` run records the accepted flag spellings.

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

## DEBT-006 — Four plannedHooks remain planned and unowned

**Origin:** spec 017, T16, skipped at close on 2026-08-23.

`openapi-contract-reminder`, `messaging-review-reminder`, `stripe-review-reminder` and
`prisma-migration-guard` are declared under `plannedHooks` in `profiles.json` and have never been
implemented. Spec 017 promoted every `plannedSkills` entry to a shipped skill; the hooks were left
behind and the task carrying them was labelled `(Future)` by its own author.

**Why it was skipped rather than done:** a future item held as an open task is what kept spec 017
from closing for thirteen months, even though everything it actually shipped was finished. Scope for
a later spec, not debt for that one.

**How to retire it:** decide per hook whether it is still wanted. Three of the four are *reminders*,
the same shape as `graphify-scan-reminder` and `scope-keeper-reminder` — reinforcement, never
enforcement — so the pattern is proven and the cost is low. `prisma-migration-guard` is different:
a guard implies blocking, which needs its own decision about what it refuses and why.

**Risk while open:** `profiles.json` advertises intent the framework does not deliver. Low, because
planned items are installed by nothing and the distinction is documented — but it is the same
"record asserting more than the mechanism provides" shape that specs 034 and 036 were about.

## DEBT-007 — install.ps1 has never been run on real Windows outside CI

**Origin:** spec 016, T07, deferred at close on 2026-08-23. Also inherited from spec 015's
`update.ps1` backlog.

`install.ps1` and `update.ps1` carry code parity with their bash counterparts, and spec 034 D005 put
a behavioural PowerShell suite on the `windows-latest` runner, so their **logic** is now exercised on
real Windows every PR. What has never been checked is a human running them **as an adopter would**:
`C:\ProgramData` defaults, drive letters, an interactive PowerShell profile, an existing central dir
with real content.

**Why it never blocked a spec:** spec 016's AC-04 requires code parity and defers runtime
verification by its own wording. The deferral was correct; what was wrong was leaving it as an open
task with no owner and no id for thirteen months.

**Why it shrank:** before spec 034 this needed a full manual pass. Now CI covers the logic, so what
remains is a much narrower environment check — and CI would already have caught a logic regression.

**How to retire it:** one adopter-style install on a Windows machine, recorded in spec 016's TASKS.md.

**Risk while open:** a Windows-only path issue could survive CI. Bounded — the suites do install,
remove, refresh and read manifests on Windows, so a broad breakage would surface.

## DEBT-008 — The scope-keeper hook has never been observed firing in a live session

**Origin:** spec 036, T010, deferred at close on 2026-08-23.

`scope-keeper-reminder` is asserted by 19 automated tests across both languages, driven with crafted
`PreToolUse` payloads. Nobody has yet watched it fire in a real session: reminder before the first
edit, silence before the second.

**Why it could not be closed with the spec:** the session that wrote the hook started before the hook
was wired, so it could not observe itself. That is a genuine limitation, not an excuse — but it is
also why this is a one-time observation rather than ongoing work.

**How to retire it:** open any new session, make an edit, confirm the `[scope-keeper]` message
appears; make a second edit, confirm silence. Tick T010 in spec 036 with what was seen.

**Risk while open:** the wiring could be wrong in a way the tests cannot see — they invoke the hook
directly rather than through the harness. The hook itself is proven; the delivery path is not.

---

## DEBT-009 — The runner has never executed against a real provider, or from cron

**Origin:** spec 040 (`agent-sdk-runner`), AC-001 and AC-002 downgraded by D030 on 2026-08-31.
Tasks T018 and T022 are recorded `NOT OBSERVED`.

**The unverified claim.** `runner/` is presented as a phase-2 executor that runs the SDD autonomous
loop unattended — from CI, from `cron`, overnight. **Every line of that has been demonstrated
against a deterministic stub backend and nothing else.** Four things nobody has seen work:

1. an `agents/*.md` prompt reaching a real provider through the Claude Agent SDK;
2. an owning lifecycle skill (`/spec-review`, `/spec-close`, `/pr-description`) actually executing
   when the runner delegates it;
3. `PR_DESCRIPTION.md` appearing on disk;
4. a real `codex exec` invocation — which is [[DEBT-001]] and [[DEBT-002]] seen from this feature.

The cause is environmental, not deferred effort: `import claude_agent_sdk` raises
`ModuleNotFoundError` and `which codex` finds nothing on the maintainer's machine, both verified
2026-08-31.

**Narrowed 2026-08-31 (spec 040 D031).** The CLI is now observed converging end to end — a real
subprocess, stdin closed, two tasks, exit 0, artifacts present, no runner-created commit — against
a **scripted** stub backend. What that removes from this debt is the question "does the command-line
entry point work at all". What it leaves untouched is every one of the four items above.

**Narrowed 2026-08-31 (spec 040 D031).** The CLI is now observed converging end to end — a real
subprocess, stdin closed, two tasks, exit 0, artifacts present, no runner-created commit — against a
**scripted** stub backend. That removes the question "does the command-line entry point work at
all". It leaves every one of the four items above untouched.

**Cost if wrong.** The failure mode is a first real run that does not work, not a silent
corruption: the entry gate refuses before touching anything, and every ambiguous path in the runner
fails closed. What is genuinely unknown is the *shape* of the integration — whether an
`agents/*.md` file is a usable system prompt for an SDK session, whether a delegated session can
run a Claude Code skill at all, and whether the lifecycle steps return the canonical verdict block
the runner requires. If the answer to the second is no, the finalization design needs rethinking,
not patching. Spec 040's PLAN carries this as R10 and its Assumptions already state that a
prompt-shape mismatch is a finding, **not** a licence to fork the agent files.

**What this debt is not.** It is not "the runner is untested". 176 tests cover the fail-closed
parser, the counter arithmetic, the hard budget, idempotent re-entry, the repair cycle and the
freeze/closure audit, and each control was verified by reverting it and watching the suite go red.
The gap is the seam between that machinery and a real provider.

**What closes it.** Install `claude-agent-sdk`, run spec 040's T018 (the two E2E scenarios, one
from a non-interactive shell and one from `cron`) and T022 (one overnight run on a real `Ready`
spec, with its `ORCHESTRATION.md` and `run.jsonl` read start to finish by hand). Then restore the
two downgraded clauses in spec 040's `SPEC.md` and close this entry. Until then the spec may reach
`In Review` and `Implemented`; **it may not reach `Done`**.

**Related:** [[DEBT-001]] and [[DEBT-002]] — the Codex half of the same gap, and both are now
load-bearing for spec 040 as well.

---

## DEBT-010 — The adopted loop has never reached a human-gated `PAUSED` outside a fixture

**Origin:** spec 041 (`autonomous-adopt-in-flight-feature`), T014's residual, recorded by D011 on
2026-09-02.

**The unverified claim.** That a real feature's human-only task — a visual check, a real-world run —
surfaces as a human-gated escalation and pauses the adopted run with the answers needed, rather than
failing it. Spec 041's T028 observes exactly that on a **fixture**: a worker returned `BLOCKED` with
its question verbatim, the classifier called it human-gated, the independent task continued, and the
run ended `PAUSED` with its remediation. What has never been seen is the same on a real repository
with a real feature's tasks.

**Why T014 did not close it.** T014 was written to see this on `proyecto-cumbre` feature 030 — the
case that motivated the whole feature. The replay ran, found two real defects (fixed as T029/T030),
and then could go no further: 030 had moved to `In Review`, which D002 excludes from adoption on
purpose. The originating case is permanently past the window adoption serves, so that task's
criterion is dead rather than pending, and the residual moved here.

**Cost if wrong.** Contained. The escalation classifier and the PAUSED path are spec 031 code that
this feature did not touch, and the fixture run exercises them end to end; what is unverified is only
their behavior against the untidier shape of a real feature's task list. The failure mode would be a
run that aborts where it should pause, which is visible and recoverable, not a silent wrong answer.

**What closes it.** Adopt any real in-flight feature that has at least one human-only task, and
record the run's `ORCHESTRATION.md` showing a `human-gated` escalation in `waiting` and `Run result:
PAUSED`. The next feature the maintainer starts by hand is the natural candidate — adoption pays
there, not on a feature already past `In Review`.

**Related:** [[DEBT-009]] — both are about the loop never having met reality; that one is the runner
against a provider, this one is the protocol against a real feature's human tasks.
