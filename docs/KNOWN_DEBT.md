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
| DEBT-010 | The adopted loop has never reached a human-gated `PAUSED` outside a fixture | spec 041 | Open (non-blocking) |
| DEBT-011 | A dry run does not validate backend-exclusive options | spec 042 | Open |
| DEBT-012 | `run.jsonl` detects write failures but is not tamper-evident | spec 042 | Open |
| DEBT-013 | Five record-hygiene defects in spec 042, deliberately not repaired (one since closed) | spec 042 | Open (non-blocking), 4 of 5 |

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

> **2026-09-04 — narrowed further by spec 044, still not closed.** The plugin path is verified: `codex plugin
> marketplace add <checkout>` and `codex plugin add sdd@spec-driven-development` exit 0 on `codex-cli 0.152.1`,
> and a `codex exec` session built its skills context with the plugin's skills in it. What stays open is
> exactly this entry's claim — whether the CLI reads and acts on the **prompts** under `~/.codex/prompts` —
> plus one new observation: a Codex session executing a plugin skill has not been seen (usage limit, 044 D012).
>
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
`In Review` and `Implemented`; ~~**it may not reach `Done`**~~.
**Superseded 2026-09-02 (spec 040's record, corrected while spec 041 was editing this file):**
spec 040 closed `Done` on 2026-09-01 as EXPERIMENTAL, with T018 and T022 moved out of scope by
its D034, so that clause read as a live gate the repo contradicts. The debt itself is unchanged
and still open.

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

**Blocking status.** Spec 041's D011 first made this a gate on that feature's `Done`. D012 lifted
it on 2026-09-02: the mechanism is proven end to end by T028's fixture run, what is missing is
observation on a real feature; the escalation and `PAUSED` code belongs to spec 031 and was not
touched; and the runner is experimental and `stub`-only, so the failure mode is a visible,
recoverable abort rather than a silent wrong answer. The entry stays open with its closing condition
unchanged — it is carried, not dismissed.

**Related:** [[DEBT-009]] — both are about the loop never having met reality; that one is the runner
against a provider, this one is the protocol against a real feature's human tasks.


---

## DEBT-011 — A dry run does not validate backend-exclusive options

**Origin:** spec 042 (`canonical-autonomous-core`), T043 deferred on 2026-09-03; D011 **Superseded**.

**The gap.** `--dry-run` returns its plan before a backend is resolved, so options that only mean
something to a particular backend are not checked. The live case:

```
python3 -m sdd_runner --feature <path> --dry-run --backend claude --stub-script s.json  -> exit 0
python3 -m sdd_runner --feature <path>            --backend claude --stub-script s.json  -> exit 14
```

The same contradictory request is accepted by one invocation and refused by the other. Spec 042's
SPEC states the boundary explicitly — a dry run dispatches nothing, so it has no backend to
contradict — but "explicable" is not the same as "intended", and a caller reasonably expects a dry
run to answer as the real run would.

**Cost if wrong.** Small and non-silent. The operator learns of the contradiction one invocation
later, from a refusal that names the flags. Nothing is dispatched, no provider is reached, and no
state is written in the meantime, so the wrong answer costs a re-run rather than damage.

**Why it was not fixed in spec 042.** It **was** fixed, and then reverted. The fix moved the check
ahead of the dry-run branch and turned an exit `0` into an exit `14` — an observable change that
FR-009 did not authorise. At that point its structured list contained only `DIFF-001`; later review
added other, unrelated entries, but the dry-run change remains outside the list. The maintainer
rejected it as a usability improvement outside this refactor's scope. The attempt is recorded in
spec 042's D011, marked Superseded/Rejected and kept in full so the reasoning survives.

**What closes it.** A feature that owns the change deliberately: move the validation ahead of the
dry-run branch (or into `RunRequest`), re-record the `dry-run-contradiction` golden transcript at
exit `14`, and state the output change in its own acceptance criterion. It is a small change; what
it needs is the authority to alter observable behaviour, which spec 042 did not have.

**Related:** spec 042 D011 (Superseded), `domain:DOM-013`, `domain:DOM-017`, `domain:DOM-020`.


---

## DEBT-012 — `run.jsonl` detects write failures but is not tamper-evident

**Origin:** spec 042 (`canonical-autonomous-core`), raised by `security-reviewer` in round 4 as an
unresolved risk rather than a finding, and accepted here as debt.

**What spec 042 closed.** A *failed* write is now detected and is fatal: `Loop._emit` raises
`AuditUnavailable` on the first failure, the run stops before any further delegation, and the
invocation reports exit 70 / `ABORTED` / `resumable: no` (D015). A worker can no longer make the
transcript stop and let the run report success.

**What remains open.** A worker with write access to the feature folder — which every implementer
delegation has, by design — can still **truncate or rewrite** `run.jsonl`. Nothing detects that:
`open(path, "a")` succeeds afterwards, subsequent appends land normally, and the file reads as a
shorter but well-formed transcript. `state.py`'s claim that a run's decisions are reconstructible
from the durable record holds against accident and **not** against the party the record exists to
document.

**Cost if wrong.** Bounded but real. `ORCHESTRATION.md` is written separately and atomically and
carries the attempt table, the findings registry and the run result, so a tampered `run.jsonl`
does not by itself let a worker hide that a delegation happened. What it can hide is the
*event-level* detail a post-hoc audit would use to reconstruct a disputed run: dispatch payload
references, verdict parsing, counter transitions. This matters when the loop is trusted to run
unattended against a real provider, which it has never yet done ([[DEBT-009]]).

**Why not in spec 042.** The feature's acceptance criterion is that observable behaviour does not
change outside the differences FR-009's structured list authorises. Making the transcript
tamper-evident means
choosing a mechanism — a monotonic sequence number, a hash chain over records, or an append-only
sink outside the repository — and **verifying the chain before every append**, which changes the
write path's cost and failure modes on every event. That is a feature, with its own threat model and
its own acceptance criteria, not a repair.

**What closes it.** Either: (a) a per-record sequence number plus a hash chain (each record carries
the digest of its predecessor), verified on open and before each append, with a documented response
to a broken chain — most likely the same `AuditUnavailable` gate D015 established; or (b) an
append-only sink outside the worker's reach, with the same verification. Either way the closing
feature must state what a broken chain *does*, because a detector with no policy is the defect
D015 was written to remove.

**Related:** spec 042 D015 (the audit gate), `security:SEC-004`, `security:SEC-008`,
`maintainer:MNT-001`, [[DEBT-009]].


---

## DEBT-013 — Five record-hygiene defects in spec 042, deliberately not repaired

**Origin:** spec 042 round-5 reviews, listed by both reviewers as **non-blocking observations**. The
maintainer authorised a bounded repair pass covering only the five blocking findings and instructed
explicitly that observations be recorded rather than fixed, so that a pass meant to close
contradictions did not turn into another round of improvements.

None of these violates an acceptance criterion, a normative rule or a security property. They are
recorded because a defect nobody wrote down is a defect nobody can choose about.

| # | Where | What |
|---|---|---|
| 1 | `DECISIONS.md`, D016 Consequences | Says *"one row per identity, 42 of them"*. **The registry has grown by roughly half again since**, and the correction previously recorded here ("There are 54") had itself gone stale before anyone read it — twice. No figure is stated here now: `FINDINGS.md` is the count, and `registry_task_refs` derives it. True when written; a dated record rather than a live claim, but a reader may take it as a count to check. |
| 2 | `FINDINGS.md`, `maintainer:MNT-005`…`MNT-010` | **RESOLVED 2026-09-04 (`conformance:CONF-007`).** Was: status `open` while their repair tasks are `[x]` and the repairs are in the tree, where the other rows use `repaired, awaiting re-review` for that state — two vocabularies in one column. All six now read `repaired, awaiting final conformance`, which is the same vocabulary and the more precise state: their re-review is T025, not a reviewer round. The row is kept marked rather than deleted (D013). |
| 3 | `runner/tests/contract/test_identity_task_refs.py` | `if __name__ == "__main__": unittest.main()` sits above the last class, so running the file **directly** silently skips `TheCallerRefusesRatherThanAllocating` — the behavioural guard MNT-005 demanded. Under `unittest discover`, which is how the suite runs, everything is collected, so nothing is currently unverified. |
| 4 | `loop.py` → `protocol.py` | The `UnresumableState` raised by `_schedule_repairs` is not caught by `Loop.run`'s per-task handlers, so it reaches the catch-all and surfaces as exit **70 / INTERNAL_ERROR** rather than exit **16 / STATE_UNRESUMABLE**, and its remediation is dropped. Still a coded, fail-closed refusal with no bypass — T066's criterion is met — but the classification is inconsistent with the same exception raised elsewhere in the loop. |
| 5 | `evidence/mutation_harness.py` | A comment block describing one mutation now sits above a different one, after a row was inserted between them. Cosmetic. |

**Cost if wrong.** Items 1 and 5 mislead a reader and cost nothing else; item 2 did the same and is
closed. Item 3 is a negative-space trap of the D014 family: the day someone runs that file directly
to check MNT-005, they get a pass that proves nothing. Item 4 costs an operator the remediation text
and gives a scheduler the wrong code on one refusal path.

**What closes it.** Items 1 and 5 are edits; item 2 was one and is done. Item 3 is moving four lines
to the end of the file. Item 4 needs a decision first — whether `_schedule_repairs`'s refusal should
classify as `STATE_UNRESUMABLE`, which is a behaviour change and therefore not spec 042's to make.

**Status:** four of the five open. The heading keeps the figure five because that is how many were
recorded; the table says which are live.

**Related:** spec 042 D013 (keep the history), D014 (a negative assertion must instantiate what it
denies), D016, `maintainer:MNT-005`.
