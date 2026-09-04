# Decisions: canonical-autonomous-core

## Decision log

### D001 - The package keeps the name `sdd_runner`; depth comes from `__all__`, not from a rename

**Date:** 2026-09-03

**Status:** Accepted

**Context:** The request offered `sdd_core` "or a better justified name". SPEC A-001 rejected
`sdd_core` — `docs/PROVIDER_ADAPTERS.md` already binds **"SDD Core"** to the provider-neutral
*workflow* layer and **"adapter"** to *provider packaging* — and recommended `runner/sdd_protocol/`
with `sdd_runner/` reduced to a CLI adapter. Planning then inventoried the cost: **21 test files
import `sdd_runner` submodules across 18 distinct import lines.**

**Decision:** The package stays `runner/sdd_runner/`. The canonical core is made deep *inside* it:
`__init__.__all__` becomes the public surface (≤ 12 names), `policy.py` holds the vocabulary,
`protocol.py` holds `run`/`RunRequest`/`RunOutcome`/`GateResult`/`RunPlan`, `seams.py` declares the
three seams, and every other module becomes internal. This supersedes SPEC A-001's recommended
spelling and resolves **OQ-2**: there is no second package, so no `python3 -m sdd_runner` shim is
needed.

**Reasoning:** A rename buys a better word and costs the reviewability of AC-005, whose whole
protection is that *"a reviewer must be able to see the assertion-level diff is import-only"*. Bury
that signal under 21 files of mechanical churn and the one criterion guarding the 276 tests stops
working in exactly the diff where it matters. Depth is a property of what an interface hides, not of
what a folder is called — a package exporting seven names and hiding 3 957 lines is deep whatever
its name. Spec 040 D002 already put the "this is the executor" meaning on the `runner/` **folder**;
the package name inside it was never load-bearing.

**Consequences:** Zero import churn; the diff a reviewer reads is the refactor. The word "runner"
stays slightly wrong for a package that is now the protocol authority — paid down by D004's
docstring and README corrections, which state the ownership in prose where the name cannot. A later
spec may rename it once the interface is stable and the churn is a one-line-per-file change.

---

### D002 - `PROTOCOL_TRANSCRIPTION.md` survives alongside the new contract tests

**Date:** 2026-09-03

**Status:** Accepted

**Context:** SPEC OQ-4. The 44-row table maps each clause of spec 031 to the module that encodes it
and the test that pins it. FR-012's contract tests check *values* across nine surfaces. The two
overlap, and merging them is attractive.

**Decision:** Both are kept. The table keeps clause→module→test traceability; the contract tests keep
value agreement across surfaces. T018 updates the table's module references to survive the move and
requires its guard to stay green.

**Reasoning:** They answer different questions. "Which clause of 031 does this code come from?" is
answerable only by the table — no value comparison carries provenance. "Do the skill and the core
state the same cap?" is answerable only by the contract tests — no table checks agreement. Deleting
the table to reduce file count would discard the only artifact that survives a clause being silently
dropped, which is the failure D046 already caught once.

**Consequences:** Two guards to maintain. The table's known weakness stays: a module absent from its
`MODULES` map makes its rows **unchecked** rather than failing, which is how a deleted method
survived in it for a day. T018 must not widen that hole while updating references; closing it is not
in this feature's scope and is recorded here so the next reader knows it was seen, not missed.

---

### D003 - `protocol_version` is a monotonic integer, stamped at 1 and not bumped by this feature

**Date:** 2026-09-03

**Status:** Accepted

**Context:** FR-009/FR-010 introduce a version into `ORCHESTRATION.md`. Two things had to be decided:
what it versions, and what this feature does to it.

**Decision:** It versions the **protocol contract**, not the package. It is a single monotonic
integer starting at `1`. Absent means `1`. Unknown or malformed refuses fail-closed, naming both the
version read and the version supported. **This feature stamps `1` and does not bump it**, because a
refactor that changes no rule changes no contract.

**Reasoning:** "Absent means 1" mirrors spec 041 D007 — *a state file with no `Entry` line is read as
`ready`* — so the repository has one compatibility idiom rather than two. Bumping on a refactor would
make the number track code churn instead of contract change, and the first real rule change would
then be indistinguishable from the noise. Fail-closed on unknown follows 031's standing rule that a
state file *"cannot authenticate re-entry and must fail the entry gate rather than being guessed back
into shape"*.

**Consequences:** A run started before this feature resumes unchanged. A future rule change must bump
the integer and decide a read policy for the older value — that decision belongs to the spec making
the change, and this one deliberately does not pre-empt it.

---

### D004 - The authority is inverted, and it is corrected where it is currently stated backwards

**Date:** 2026-09-03

**Status:** Accepted

**Context:** `runner/README.md` and `sdd_runner/__init__.py` both say: *"Where this runner and
`skills/sdd-orchestrate/SKILL.md` disagree, THIS RUNNER IS WRONG"* (spec 040 D007). This feature's
premise is the opposite. Leaving both statements standing would reproduce, inside the feature that
exists to end it, the contradiction it exists to end.

**Decision:** `runner/README.md`, `sdd_runner/__init__.py` and `skills/sdd-orchestrate/SKILL.md` are
corrected in the same change: the executable contract is the source of truth; the skill is its
human-readable projection. A contract test asserts no surviving text reasserts the old ownership.
Spec 040 D007 is **superseded**, and this decision says so explicitly rather than leaving a reader to
infer it from two documents that disagree.

**Reasoning:** D007 was correct when it was made — a prose protocol with a partial transcription
underneath it should defer to the prose. What changes the answer is FR-012: once nine surfaces are
mechanically checked against the core, the core is the only definition that *cannot* drift, and
deference to prose becomes deference to the unverifiable half.

**Consequences:** `/sdd-orchestrate` keeps its prose and loses final say. A maintainer editing the
skill's normative values without editing the core now gets a red suite instead of a silent
divergence — which is the point, and is also a workflow change worth stating out loud.

---

### D005 - Contract tests read an enumerated surface list; they never search the repository

**Date:** 2026-09-03

**Status:** Accepted

**Context:** Twelve unrelated review skills contain the string `Critical | High | Medium | Low` as
ordinary report vocabulary. A contract test that greps the repository for a protocol constant fails
on all twelve.

**Decision:** Every contract test reads the nine-surface list fixed in FR-012. Discovery by search is
forbidden. Adding a surface is an explicit edit to that list, and a test asserts the list is what the
guards consume.

**Reasoning:** A guard that cries wolf on twelve innocent files gets weakened or deleted — that is
the failure mode this feature exists to prevent, and it would be self-inflicted. The list is also the
honest artifact: it states exactly which documents carry protocol authority, which nothing in the
repository says today.

**Consequences:** A tenth surface added later without touching the list is unguarded. Accepted, and
mitigated by AC-001's "uncovered constant" test: a value in `policy` that no surface test consumes
fails the suite, so the gap surfaces from the core's side even when it is missed from the document's.

---

### D006 - "Installable" means locally packaged, not distributed to adopters

**Date:** 2026-09-03

**Status:** Accepted

**Context:** SPEC OQ-1, answered by the maintainer on 2026-09-03. The request asked for an
*installable* module; spec 040 **D001 (Accepted, on a `Done` spec)** decided the runner is maintainer
tooling — *"No installer change, no manifest change, no `profiles.json` change"* — with AC-014
requiring installers byte-identical to `main`.

**Decision:** The maintainer's answer stands as given: *"No se distribuye todavía. 'Instalable'
significa empaquetado y ejecutable localmente dentro del repositorio, no incluido en los instaladores
para adoptantes."* So the requirement is satisfied by local packaging — a clean `pyproject`, zero
non-stdlib runtime dependencies, no import reaching outside the package, `python3 -m sdd_runner`
working from a plain checkout. Spec 040 D001 is **upheld, not superseded**. Activation and downstream
distribution are a later feature's scope.

**Reasoning:** Entering the installers would drag `install.sh`, `install.ps1`, `profiles.json`, the
manifest and new coherence rules in `check-consistency.sh` into a refactor whose own acceptance
criterion is "no behaviour change", and would push a Python dependency onto every adopter to
validate a loop that has never run unattended — the same reasoning that produced 040 D001, unchanged
by anything this feature does.

**Consequences:** AC-009 is a byte-identity check, not a coherence-rule change. Adopter projects gain
nothing from this feature, by design. The packaging work done here is what makes the later
distribution spec cheap.

---

### D007 - Behaviour identity is proved by golden CLI transcripts captured before the first edit

**Date:** 2026-09-03

**Status:** Accepted

**Context:** AC-008 requires byte-identical external behaviour. The 276 tests assert the loop's
behaviour, not the CLI's *rendering*; FR-007 requires the dry-run output to stay byte-identical and
no current test asserts a byte of it.

**Decision:** T001 records exit code, stdout and stderr for ten scenarios — clean first entry,
~~each gate refusal~~, dry run, dry-run adopt, concurrent run, unresumable state, cap abort, budget
exhaustion, human escalation, core-complete — against the **pre-refactor** code. T019 replays them
after. ~~The only permitted difference is FR-009's `Protocol version` line.~~

**Two clauses of this Decision are struck, for different reasons.**

- ~~each gate refusal~~ — **struck 2026-09-04 (`conformance:CONF-003`, count corrected by
  `conformance:CONF-007`).** T001 did not record each gate refusal. It recorded **five** of the
  gate's fifteen terminal conditions, carried by **four** `refusal-*` scenarios, because
  `refusal-adopt-not-needed` reaches two. The clause was a description of the corpus that the corpus
  did not meet, and it stood unmarked while AC-008 quoted it. The repair was to **add the ten
  missing conditions**, never to narrow the criterion: `test_gate_refusal_coverage` derives the
  condition set from `gate.py`'s AST and fails if any lacks a transcript. Those ten are therefore
  post-refactor captures, which is why they were given `main` sides at CONF-006 — see the provenance
  note below.
- ~~The only permitted difference…~~ — struck for the reason given under **Superseded**.

**Superseded 2026-09-04 by D015 (spec 042 CONF-001), extended by D018 (CONF-006).** The struck
sentence was true when written and false from the moment D015 authorised a second difference. **The
list in force is FR-009's fenced `authorised-observable-differences` block, and this decision states
no count of its own** — it defers to that block, which at the time of writing carries `DIFF-001`
(D003), `DIFF-002` (D015) and `DIFF-003` (D018).

~~The replacement clause first read: "which enumerates **two**".~~ **Corrected 2026-09-04
(CONF-006).** Replacing one hard-coded count with another reproduced the defect at a smaller scale:
`DIFF-003` was already in the tree when that sentence was written, and this decision would have gone
stale the same way a third time. It now names no number.

Round 5 repaired FR-009, AC-008, D015's own Consequences and `test_golden_cli`'s docstring for
exactly this claim, and walked past this decision — which is `security:SEC-014`'s shape one document
over: an `Accepted` record stating a contract the tree no longer has. The original wording is struck
rather than deleted, per D013.

**On this decision's own subject — when the baselines were captured — see `conformance:CONF-006`
and the Consequences below.**

**Reasoning:** An oracle captured after the refactor proves the refactor agrees with itself. Ordering
this first is the whole value, which is why it is T001 and why no implementation task may precede it.

**Consequences:** If a scenario turns out not to be reproducible deterministically, that is a finding
about the CLI's testability, recorded as such — not a reason to drop the scenario or to weaken
AC-008.

**Provenance of the corpus — corrected 2026-09-04 (`conformance:CONF-006`).** The Decision above
describes T001 and nothing else, which was accurate when written and became misleading as the corpus
grew: read today it implies all 30 transcripts are pre-refactor oracles. They are not, and the
difference matters, because a transcript captured after the refactor proves only that the refactor
agrees with itself. The real split:

- **17 captured at T001**, against the pre-refactor code, before any implementation task ran. These
  are the oracles this decision is about, and they are the ones committed in `c36efd2`.
- **13 added afterwards**, against the refactored code: `internal-error` and `dry-run-contradiction`
  during the review rounds, `audit-unavailable` with D015, and the **ten** gate-refusal scenarios
  CONF-003 added so that AC-008's *"each gate refusal"* became true rather than narrowed.
- **11 have a retrospective `main` side**, reproduced from a temporary extraction of `main` rather
  than captured in order: `audit-unavailable.main.txt` (D015, `maintainer:MNT-010`) and the ten
  `refusal-*.main.txt` files (D018, `conformance:CONF-006`), all from `141638b`.

A retrospective baseline is weaker evidence than an ordered one — it is reproduced by a person who
already knows what the answer should be — and is recorded as retrospective for exactly that reason.
It is still strictly better than the prose string it replaces: nine of the ten reproduce `main`
byte-for-byte, and the tenth is `DIFF-003`. Every `main`-side artifact carries its provenance in its
own header, and `evidence/golden/index.json` records it structurally.

---

### D008 - Diagnostics keep their exact wording instead of being decomposed

**Date:** 2026-09-03

**Status:** Accepted

**Context:** `GateResult` carries `Refusal` values with `condition`, `detail` and `remediation` —
structured, as FR-005 requires. But four messages the core must emit are not gate refusals: the
feature-path containment failure, an unreadable state file, a concurrent run, and a backend
precondition. Each has a bespoke multi-line format that predates this feature and is pinned
byte-for-byte by T001's golden transcripts.

Decomposing them into `condition`/`observed`/`remediation` and re-rendering through
`Refusal.render()` would produce better-structured output and **different bytes**.

**Decision:** They become `Diagnostic(channel, text)` — structured enough to route (`GATE`,
`BACKEND`, `INTERNAL` decide the stream and the prefix), with the message text carried verbatim.
The docstring says so, and points here.

**Reasoning:** AC-008 is this feature's central promise: no observable change. Spending it on a
cosmetic improvement to four error messages would be the "ya que estoy" that turns a reviewable
refactor into a diff nobody can check. The structure that matters for control flow — which stream,
which exit code — is present; the structure that would only improve reading is deferred.

**Consequences:** A caller that wants `remediation` as a field gets it for gate refusals and not for
these four. That asymmetry is real and is the cost. It closes in whatever spec next changes the
CLI's output deliberately, where the transcripts get re-recorded on purpose rather than as a side
effect.

---

### D009 - Closing D046's hole was in scope; widening it was what T018 forbade

**Date:** 2026-09-03

**Status:** Accepted

**Context:** T018 was written as "update `PROTOCOL_TRANSCRIPTION.md` references **without widening**
the `MODULES` hole D002 names". Running it revealed the hole was live: `retry` had never been
registered, so the row for `retry.call_with_retry` was asserted about nothing. One of 36 rows was
decorative.

**Decision:** Register every module the table may name (`policy`, `protocol`, `resume`, `retry`
added) and add `test_no_row_is_silently_unchecked`, which fails when a row names an unregistered
module instead of skipping it.

**Reasoning:** This is the exact defect D046 recorded — `loop.Loop._lifecycle_step` survived in the
table for a day after the method was deleted, because its rows were unchecked rather than failing.
Leaving a known-live instance of a known defect untouched while editing the very file it lives in
would be the "found dead code" rule applied where it does not fit: A-010 protects code nobody is
touching, not a guard this task is required to modify. The task said do not *widen* the hole; a
one-line map addition that closes it is the smallest change that satisfies the task's own
verification criterion ("every row's module attribute resolves — checked by asserting zero rows are
skipped").

**Consequences:** The transcription guard now verifies 36 of 36 rows. A new row for an unregistered
module is a failure rather than a silent pass. No row's content changed, so the clause→module
provenance D002 preserved is untouched.

---

### D010 - Commits were made against the SPEC's Non-goals; recorded as a deviation, not authorised

**Date:** 2026-09-03

**Status:** Accepted (as a record of what happened, not as permission)

**Context:** `SPEC.md`'s Non-goals list, written by this feature, excludes *"`git commit`, `git
push`, `git merge`, real migrations, or any change to secrets."* The PLAN's Rollback strategy then
stated *"Every task is a separate commit on `feature/042-canonical-autonomous-core`"* and built its
cheapest rollback layer on `git revert`. The two documents contradicted each other from the moment
the PLAN was written.

The `/spec-analyze` pass that followed checked acceptance-criterion coverage, task `Covers:`/`Verify:`
clauses, FR traceability and open decisions. **It did not cross-check the PLAN against the SPEC's
Non-goals**, so the contradiction passed as Ready. Seven commits were then made on the feature
branch, acting on the PLAN.

The maintainer found it, together with two consequences of the same blind spot: `git add -A` tracked
`docs/AUTONOMOUS_SDD_FEATURE_PROMPT.md` **twice** (c36efd2 and again in d75ac69, after aafc74e had
removed it), so AC-013 was failing while being reported as met; and the report claimed T001–T022
closed when T021 and T022 were not.

**Decision:**

1. The **SPEC is not amended.** Redefining a Non-goal so the record matches what happened is the
   falsification this repository has a standing rule against, and the maintainer said so explicitly.
2. The **PLAN is corrected**: its Rollback section no longer mandates commits, and its verification
   checklist now records "the plan avoids behavior outside the spec" as **not met**.
3. The commits that exist are **recorded here as a deviation**. They are not reverted — undoing them
   needs history rewriting, which the maintainer forbade and the environment declines to run — and
   they are not retroactively blessed.
4. Whether this feature may commit at all is the maintainer's call, and until they make it the
   branch is treated as carrying an unauthorised history.

**Reasoning:** The Non-goal exists because an autonomous or semi-autonomous run must not decide on
its own to write history. That the writing was mundane — feature-branch commits, no push, no merge —
does not change who was entitled to decide it. The PLAN is the document that was wrong, so the PLAN
is the document that changes.

The deeper finding is about the gate, not the git: **`/spec-analyze` checked the plan's *coverage*
and never its *compliance*.** A PLAN can be fully traceable to every acceptance criterion and still
instruct work the SPEC forbids. Nothing in the analysis step looked at the Non-goals list at all.

**Consequences:**

- AC-013 is restored and verified by the check that actually answers the question:
  `git ls-files --error-unmatch` (exit 1), `git status --porcelain --untracked-files=all` (`??`),
  the recorded sha256, and an empty `git diff --name-status main...HEAD` for that path. The earlier
  verification used `git status` alone, which is silent about a staged or committed path — which is
  precisely how the same mistake was made twice and reported as fixed once.
- The branch carries seven commits plus the corrective one. The file is added in two of them and
  removed in two, netting to zero against `main`, so the PR diff is clean; the intermediate commits
  still contain it and only a history rewrite would change that.
- Every domain and security verdict obtained before the corrective commit is **stale**: the tree
  changed, so those approvals and rejections belong to a fingerprint that no longer exists.
- `/spec-analyze` needs a Non-goals compliance check. That is a framework change, outside this
  feature's scope, and belongs to whichever spec next touches the analysis step.

---

### D011 - A second deliberate change to observable output: the dry run answers what a real run answers

**Date:** 2026-09-03

**Status:** ~~Accepted~~ **SUPERSEDED / REJECTED 2026-09-03 by the maintainer.** Kept in full below,
unedited, because it is the record of an attempt — deleting it would hide that the widening
happened and that a decision was written to bless it.

> **Why it was rejected.** This decision resolved the contradiction in favour of the *repair* and
> declared FR-009's "only" wrong. The maintainer resolved it the other way, in favour of the
> feature's original objective: **preserve observable behaviour except `Protocol version`.** A
> refactor does not get to grow a second exception to the criterion that defines it, and a decision
> that makes an acceptance criterion false is not a resolution — it is the criterion losing.
>
> **What was done instead.** The dry-run check was moved back behind the dry-run branch, restoring
> `main`'s exit `0`; the `dry-run-contradiction` transcript was re-recorded at the baseline and kept,
> because it is now what would catch the same widening being reintroduced; the SPEC states the
> boundary explicitly (a dry run resolves no backend, so it validates no backend-exclusive option)
> instead of leaving it to be inferred from an edge-case bullet that read as an unqualified
> requirement; and tightening dry-run validation is recorded as an out-of-scope follow-up in
> Non-goals. AC-008 keeps exactly one exception.
>
> **What stays true from it.** The underlying observation was right: the SPEC's edge-case bullet did
> demand something the code did not do. The error was fixing it inside a feature whose acceptance
> criterion forbids the fix, and then amending the criterion to fit. The bullet is now qualified
> rather than the criterion weakened.

**Superseded status:** Rejected

**Context:** FR-009 states that the `Protocol version` header is *"the **only** intentional change to
observable output in this feature"*, and AC-008 requires the CLI's exit code and streams to be
byte-identical across the refactor. Repairing domain:DOM-013 broke both.

Before the repair, `protocol.run` returned the dry-run plan **before** resolving a backend, so
`--dry-run --backend claude --stub-script x` exited `0` and printed a plan. The same request without
`--dry-run` exited `14`. The SPEC's own edge-case list requires the core to reject a `RunRequest`
with contradictory fields and names this exact pair; FR-003 calls `RunRequest` "a validated value
type". So the pre-repair behaviour contradicted three statements in the SPEC, and the repair moved
the check ahead of the dry-run branch — changing an observable outcome from exit `0` to exit `14`.

The second reviewer found it: the change was made, it was correct, and **no decision recorded it**.
The Non-goals permit a rule change only *"where a contradiction between the three authorities is
demonstrated in writing and resolved by a recorded decision."* The demonstration existed in
`FINDINGS.md`; the decision did not.

**Decision:**

1. The change **stands**. A dry run that accepts what a real run refuses answers the same question
   two ways, and the SPEC says which answer is right.
2. FR-009's "only" is now **wrong as written**, and this decision says so rather than the SPEC being
   quietly edited: there are **two** intentional changes to observable output — the `Protocol
   version` line, and this exit code. Any later reader comparing FR-009 to the transcripts should
   land here.
3. It is guarded. A golden transcript (`dry-run-contradiction`) records exit `14` and its stderr, so
   the newly normative rule cannot regress silently — which is what "changed without a decision"
   also meant in practice: nothing was pinning it.

**Reasoning:** Reverting would restore a behaviour the SPEC's edge cases forbid, to protect a
sentence in FR-009 that was written before the contradiction was known. The honest order is to keep
the correct behaviour and correct the record — the same order D010 took with the commits, and the
opposite of amending the SPEC so the deviation disappears.

**Consequences:**

- The golden corpus is **19 scenarios**, not 17. The two added are this one and `internal-error`.
- AC-008 must be read with two declared exceptions, both listed in `test_golden_cli`'s
  `PERMITTED_DIFFERENCES` rationale and in this decision.
- Whoever next re-records the transcripts must show that each difference is declared here or in
  FR-009. A transcript re-recorded without a decision is how this would have gone unnoticed.

---

### D012 - Outcome disposition is stated, never inferred from diagnostics

**Date:** 2026-09-03

**Status:** Accepted

**Context:** The CLI needs one fact to decide whether to print `run result:` and whether to emit
`run-finished`: did the loop actually run and return a reportable result? Until now nobody stated
it. `RunOutcome.ran` computed it as *"a terminal result value **and** no diagnostics"* — a faithful
description of the pre-042 CLI, because before spec 042 a diagnostic only ever accompanied a
refusal.

T053 broke that premise on purpose. Repairing `security:SEC-008` gave a *successful* outcome a
diagnostic, so that a run whose `run.jsonl` became un-appendable would stop being silent about its
lost audit trail. The inference then read the new shape as "not a run": a converged feature, exit
`0`, `Run result: DONE`, printed nothing and notified nobody. The repair for a silent audit loss had
produced a silent success loss, and **411 passing tests did not see it** — several of them asserted
the inference itself, so the suite defended the defect.

**Decision:** `RunOutcome` gains `loop_completed: bool`, set to `True` **only** where `protocol.run`
holds a value returned by `Loop.run()`, and left `False` everywhere else — preflight refusals,
containment failures, `--dry-run`, and the internal-error path. `ran` is kept as the published
compatibility spelling and returns `loop_completed` and nothing else. **Neither consults
`diagnostics`**, and a contract test parses the property's AST to keep it that way.

The field is deliberately **not** `execution_started`. An exception can be raised after the loop
begins, and the baseline CLI printed no terminal result and sent no `run-finished` for it; "did it
start" is a different question from "is there a result to report", and only the second one has a
caller.

**Reasoning:** The defect was not that the inference was written wrongly — it was correct for every
shape that existed when it was written. It was that a *derived* fact silently changes meaning when a
new shape appears, and the deriving code has no way to notice. Two independent facts were being
carried on one field: *did the loop run* and *did anything go wrong*. Separating them removes the
class, not the instance. FR-004a states the rule so the next diagnostic added to a successful
outcome cannot reintroduce it.

**Consequences:**

- `RunOutcome`'s public shape grows one field; FR-004 is updated and FR-004a added.
- A converged run now reports itself and notifies even when something went wrong beside it, which is
  what a scheduler needs and what the baseline did.
- Exit 70 is unchanged: an internal error still prints only its diagnostic and sends no
  `run-finished`.
- A mutation falsifying the single `loop_completed=True` assignment is in the harness; four guards
  fire. A field nothing can falsify is decoration.

---

### D013 - The rejected `REVERTED` marker stays on the record

**Date:** 2026-09-03

**Status:** Accepted

**Context:** T043 implemented dry-run validation of backend-exclusive options; T049 undid it because
it widened observable behaviour. Closing T043 honestly took **three** attempts, and each one is a
different way of getting the record wrong:

1. It stayed `[x]` with its original `Verify:` clause — a criterion the tree now deliberately fails
   (`domain:DOM-020`).
2. It was annotated `REVERTED`, which reads honestly and **is not one of the three markers**
   `specs/_templates/TASKS.md` admits: `DEFERRED`, `SKIPPED`, `RESOLVED`. A fourth marker invented
   at the point of use is a vocabulary nobody else can read.
3. It became `DEFERRED -> DEBT-011` — and T055, the task that had performed step 2, kept a `Verify:`
   clause describing step 2's tree ("struck through and names T049"). The repair had inherited the
   defect it repaired (`maintainer:MNT-002`).

**Decision:** T043 is `DEFERRED (2026-09-03) -> DEBT-011`, T055's criterion states its real
objective, and **the history of steps 1 and 2 is kept** — in T043's annotation, in T055's clause, in
the findings registry and here. It is not edited out.

**Reasoning:** The whole point of the marker vocabulary is that a reader can tell "done" from "not
done, and here is where it lives now". Three markers exist so that distinction survives; a fourth
invented in the moment defeats it, and deleting the attempt would leave the next reader unable to
see why the wording is so careful. This repository already has a standing rule against rewriting a
run's record to match a later rule — the 033 registry rows were deliberately left as written for
exactly this reason. The same rule applies to a task's own history.

**Consequences:** `DEFERRED` is the only marker in use in this feature's TASKS. Anyone auditing
T043 sees that work was implemented, undone, and deferred, with the debt id that owns it. The cost
is a longer task entry, which is the correct price for a task that must not be read as executed.

---

### D014 - A negative assertion must instantiate the thing it denies

**Date:** 2026-09-03

**Status:** Accepted

**Context:** `AnInternalErrorStillReportsNothingTerminal` asserted that an internal error emits no
`run-finished`. It called `protocol.run()` directly, built a sink path in `setUp` that nothing ever
read, and never executed `__main__`. The notifier is constructed inside `__main__.main`; no
`__main__` ran, so no notifier existed, so nothing could have fired. The assertion was
`assertEqual([], [])` dressed as evidence (`maintainer:MNT-003`).

The same shape had already appeared three times in this feature — a guard that performed the
assignment it asserted (`domain:DOM-010`, twice), and one whose only assertion was
`assertTrue(<non-empty line>)` (`security:SEC-005` / `domain:DOM-018`).

**Decision:** Any test asserting that something does **not** happen must (a) run the component that
would make it happen, and (b) carry a companion test proving that component is reachable — here, a
converged run through the same code path delivering exactly one event to the same sink. A mutation
that removes the guard from the *consumer* is added alongside the one that protects the *producer*.

**Reasoning:** A positive assertion fails loudly when the code is wrong. A negative one fails
loudly only if the machinery is present; otherwise it passes for the wrong reason and keeps passing
forever. The producer-side mutation (`loop_completed=True` → `False`) could not see this: it
protects who sets the field, and the defect was in who reads it.

**Consequences:** Two mutations now cover the disposition contract from both ends, and the notify
condition has a structural guard over `__main__`'s AST. The rule generalises beyond this feature and
is the fourth instance of the same class — it belongs in the framework's review guidance, which is
out of scope here and recorded as an observation rather than a change.

---

### D015 - A run without a durable record is not a run: the audit failure is a security gate

**Date:** 2026-09-04

**Status:** Accepted. **Supersedes the behaviour asserted by D012's consequences, and by T051/T053/T057.**

**Context:** Three behaviours have existed on the path where `run.jsonl` cannot be written, and the
maintainer refused two of them.

1. **`main`** — reproduced from a temporary extraction, not assumed: exit **1**, empty stdout, a raw
   `IsADirectoryError` traceback. The first `log.emit` raises, the CLI's handler runs, and the
   handler's own `log.emit("internal-error", …)` raises again and escapes. `main` never reached exit
   70. `domain:DOM-023` says it did; that is corrected in `FINDINGS.md` without editing the finding.
2. **After T053/T057** — exit **0**, `run result: DONE`, one `run-finished`, and the lost transcript
   mentioned on stderr. A converged run reported as a success with no evidence for anything it did.
3. **This decision.**

Neither refused option is acceptable, and the reason is the same for both: **a scheduler must be
able to trust the exit code.** A traceback and exit 1 is not a code a scheduler can branch on. An
exit 0 that says DONE while the audit trail is gone is worse — it is a lie the scheduler will
believe. stderr is not a substitute for either.

**Decision — the policy.** A failure to persist `run.jsonl` is an audit failure, and an audit
failure is fatal:

- exit `INTERNAL_ERROR` (70);
- result `ABORTED`;
- `loop_completed=False`;
- `resumable=False` until a maintainer has looked — the tree may carry work no transcript accounts
  for;
- an explicit, redacted diagnostic, **no traceback**;
- no `run result: DONE`;
- no `run-finished`;
- and the loop **stops at the first failed write, before any further delegation**.

The last clause is the one that matters most. Stopping at the end would mean a run continued
delegating and editing the tree after its record had stopped — exactly the window a worker with
write access to the feature folder would want.

**Decision — the implementation.**

1. `RunLog.emit` keeps its promise: no raw `OSError` escapes the writer. That is what stops a failed
   write turning a coded exit into a traceback, and it is why `main` behaved as it did.
2. `Loop._emit` is the single wrapper. It calls the writer, inspects `write_failures`, and raises
   the typed `AuditUnavailable` on the first failure. **Every** loop event goes through it — forty
   call sites — and `test_audit_gate.OnlyOneRouteToTheLog` walks the module's AST and fails on a
   direct `self.log.emit` outside the wrapper. One bypass is all it takes for a run to continue past
   its own record.
3. `protocol.run` catches `AuditUnavailable` **before** the catch-all and builds the outcome without
   writing to the log that just failed — writing there is precisely what produced `main`'s
   traceback.
4. The post-loop `write_failures` reader remains, now as fail-closed defence rather than a
   diagnostic attached to a success: reaching it with a non-empty list means a write failed outside
   the wrapper, which is the same condition discovered late, and it returns the same exit 70.

**Reasoning:** The writer and the loop have different jobs, and conflating them produced both refused
behaviours. The writer's job is never to convert a lost line into a crash; the loop's job is to
decide that a run it cannot record is not a run it may report. Separating them lets each be right.

**Consequences:**

- ~~**FR-009 and AC-008 must authorise exactly two differences from `main`**~~: the `Protocol
  version` header, and this normalisation — a traceback with exit 1 becomes a stable diagnostic with
  exit 70. **Superseded 2026-09-04 by D018 (`conformance:CONF-006`).** The requirement stands with
  the count removed: FR-009 and AC-008 must authorise **every** difference from `main`, by
  identifier, in the block FR-009 carries. A third was already in the tree — `DIFF-003`, the
  `BASELINE_UNAVAILABLE` refusal — when this consequence was written, so the word "exactly" made
  this decision assert a closed set it did not own. No decision states the count now.

  **Correction, 2026-09-04.** This consequence was written as *"Both are named in the SPEC and in
  `test_golden_cli`"*, and only the second half was true: `test_golden_cli` declared both, and the
  SPEC named neither this decision nor the difference. FR-009 and AC-008 went on saying "only"
  while the tree shipped two, so the acceptance criterion gating this feature was false against
  it. Both reviewers found it in round 5 (`domain:DOM-023` re-reported, `security:SEC-013`) and it
  was repaired there: FR-009 enumerates them as `DIFF-001` and `DIFF-002` in a structured block,
  AC-008 refers to that list, and a contract test compares the two sides by identifier.

  A decision asserting an edit nobody made is worse than one asking for it — the assertion reads
  as done. The original sentence is kept above so the failure stays visible.
- A new golden scenario, `audit-unavailable`, pins it. It is labelled a **retrospective** baseline:
  it was not captured at T001 with the other seventeen, and its `main` behaviour was reproduced
  afterwards. Pretending otherwise would be the tidy history this feature has twice refused.
- D012 stays in full. Its mechanism (`loop_completed` stated, never inferred) is correct and
  unchanged; its consequence claiming the new reporting was "what the baseline did" is superseded
  here.
- Detecting a failed write is not the same as detecting tampering. A worker can still truncate
  `run.jsonl` silently — recorded as [[DEBT-012]], not closed here.

---

### D016 - One identity, one repair task: the strict rule stands, and the deviations stay on the record

**Date:** 2026-09-04

**Status:** Accepted

**Context:** `FINDINGS.md` states *"Identity maps to exactly one repair task. Re-reporting updates
the row; it never allocates a second task."* `skills/sdd-orchestrate/SKILL.md:288` states it
normatively as one of the nine protocol surfaces. `domain:DOM-025` and `security:SEC-011` found the
registry breaking it three ways: `security:SEC-006` had **two rows** for one identity; that row named
two tasks (`T047, T052`); and `security:SEC-004`'s row named one task while `TASKS.md` allocated a
second (`T051`, titled "second-round completion of security:SEC-004"). The registry showed one
violation and concealed the other.

SEC-011 supplied the argument that settles it: **the executable core already implements the strict
rule.** `loop._schedule_repairs` reuses the existing task and emits `repair-task-reused`. Adopting
the permissive reading would not be an edit to a registry — it would be a protocol change touching
the skill, the registry header and the loop.

**Decision:** The strict rule stands. The permissive reading is **not** adopted.

- `security:SEC-006`'s two rows are collapsed into one, preserving both rounds, both fingerprints
  and both required actions.
- Each of the two affected rows names its **canonical** task and records the other as a task created
  outside the rule: SEC-006 → `T047` canonical, `T052` a deviation; SEC-004 → `T031` canonical,
  `T051` a deviation.
- `T051` and `T052` are **not deleted and not hidden**. They exist, they did real work, and the
  record says both that they exist and that creating them broke the rule.

**Reasoning:** Deleting the `T047, T052` cell to make the rule look kept is the falsification D010
and D013 both refused, and it would erase two repairs the tree depends on. Rewriting history to
match a later rule is the failure this repository has a standing rule against. The honest form is a
canonical task plus a recorded deviation — the same shape as `DEFERRED -> DEBT-011`.

**Consequences:** The registry now has one row per identity, 42 of them. Two rows name two tasks
each, and both say why. A future re-report of either identity reuses its canonical task.

---

### D017 - The registry's `task_ref` is the authority; the title suffix is provenance

**Date:** 2026-09-04

**Status:** Accepted

**Context:** D016 restates a rule the code could not keep. `maintainer:MNT-004`: against this
feature's own `TASKS.md`, `tasks.task_for_finding` returned `None` for **every** identity, so
`_schedule_repairs` would have allocated a second task while its comment promised to reuse one. Two
independent causes, each invisible on its own — `_FROM_FINDING` matched `(from SEC-006)` while the
tasks say `(from security:SEC-006)`, and `Task.repairs` searched the *title*, which is a task item's
first line, so any wrapped title carried no marker at all.

**Decision:** Resolution is structured, not textual.

1. The Findings registry's repair-task column is the **authority** on a re-report. `task_for_finding`
   takes a `registry` mapping and, when it names a task, returns that task after validating it
   exists. ~~A registry pointing at a task that is gone returns `None` — the caller fails closed
   rather than allocating against a broken record.~~

   **Superseded 2026-09-04 by `maintainer:MNT-005`, repaired under T066.** Both halves of the struck
   sentence were false. A missing task now raises `BrokenRepairTaskReference`, and
   `Loop._schedule_repairs` catches it, emits `refused` and raises `UnresumableState` without writing
   anything. Returning `None` did **not** make the caller fail closed: `None` already means *"this
   identity has no task yet"*, and the caller acts on that by **allocating one** — so a broken
   reference produced a second task for an identity that already owned one, the exact outcome this
   decision exists to prevent. The original wording is struck rather than deleted so the mistake
   stays legible (D013's rule).
2. The `(from …)` suffix stays, as human provenance and a legacy fallback, parsed **anchored**: the
   marker matches an identity shape with an optional namespace, read from the whole task item rather
   than its first line.
3. Two identities may share one task when they are literally the same defect —
   `security:SEC-001` and `domain:DOM-003` are the worked example — so the parse returns a list.
4. A finding id appearing anywhere **outside** the marker creates no association. This feature has
   three such mentions, and a substring search treats all three as allocations.

**Reasoning:** A wider search was the obvious fix and the wrong one. Prose can be reworded, wrapped
or dropped without anyone noticing that a lookup stopped working — which is exactly what happened,
silently, while a comment promised the opposite. A structured field is the only thing that can be
authoritative, and the failure mode of the search — a mention read as an allocation — is the same
one this feature has now produced five times, three of them in its own verification tooling.

**Consequences:** `registry_task_refs` parses the registry's two structured columns and ignores every
narrative cell. `test_identity_task_refs` covers wrapped titles, optional namespaces, shared tasks,
incidental prose mentions and a registry pointing at a missing task. An AST guard asserts the loop
passes the registry rather than resolving from prose.

---

### D018 - Structured refusal when the baseline suite cannot launch

**Date:** 2026-09-04

**Status:** Accepted

**Context:** `main` runs the `--baseline` command from inside `gate.check` with no guard
(`gate.py:313`), and `__main__.py:163` calls the gate without wrapping it. A missing or
non-executable baseline binary raises `FileNotFoundError` (or `PermissionError`) and the exception
escapes the process: **traceback, exit 1**, no refusal, no remediation. Reproduced from a temporary
extraction of `main` at `141638b`, three runs out of three, and independently under the in-process
harness that produced the T001 oracle — where `main` raises rather than returning a code at all.

This feature already changed that path, in two steps and without anyone recording the change as
observable:

1. `security:SEC-006`'s repair wrapped the whole `gate.check` call in
   `except (OSError, UnicodeDecodeError)`. That stopped the traceback, but answered a
   `FileNotFoundError` from the baseline launcher with *"a file the entry gate reads could not be
   read… SPEC.md and TASKS.md must be readable UTF-8"* — a cause the core never observed.
2. `security:SEC-012` corrected the **classification**: the `OSError` is now caught at the launch
   site (`gate.py:280-295`) and becomes a `BASELINE_UNAVAILABLE` refusal. It repaired the wrong
   cause; it did not, and was not asked to, decide whether the departure from `main` was authorised.

Neither step registered a difference from `main`, and the ten gate-refusal transcripts CONF-003
added had no `main` side to be compared against. `CONF-006` gave them one, and the divergence became
visible: nine of the ten reproduce `main` byte-for-byte, and this one does not.

**Decision:** The departure is authorised as deliberate, with this semantics:

- `main`: uncaught `FileNotFoundError`, traceback, exit 1.
- spec 042: refusal `BASELINE_UNAVAILABLE`, exit **10** (`GATE_REFUSED`), a stable diagnostic naming
  the OS error and the observed argv quoted safely, and a remediation.
- The gate **stops before delegating or producing any later effect**.
- No traceback is printed, and the run is never classified as a loop execution.

It is registered as `DIFF-003` in FR-009's `authorised-observable-differences` block, which is the
list in force. AC-008 defers to that list by identifier; nothing here weakens it.

**Reasoning:** The runner's purpose is unattended operation, and an unavailable preflight dependency
is exactly the case a scheduler must be able to branch on. A traceback and exit 1 is not a code a
scheduler can act on — the same argument D015 made for the audit failure, on the other end of the
run. `PLAN.md` mandates the baseline command; a typo in it, an uninstalled tool or a lost `+x` bit
are the ordinary ways it goes missing, and every one of them is fixable by the operator the moment
the refusal says which argv failed and why.

**Alternatives considered, and why both are refused for an autonomous runner:**

1. **Restore `main`'s traceback and exit 1** — revert the guard so the corpus is identical in all
   ten conditions. Refused: it re-creates the one refusal path that returns an uninterpretable exit
   code, in the tool whose contract is that a scheduler can trust the exit code. It would also
   re-open `security:SEC-006`, whose repair exists to keep an `OSError` from escaping the gate, and
   the fix for SEC-006 that does not produce this difference does not exist — any capture of the
   exception is this difference.
2. **Defer it to a feature of its own** — keep the change out of 042 and land it later with its own
   criterion. Refused because the change is **already in the tree** and cannot be deferred without
   being reverted first, which is alternative 1 with an extra step. The honest options are to
   authorise it or to remove it; postponing it would mean shipping an unauthorised observable
   difference under a criterion that forbids one, which is the failure this feature exists to end.

**Consequences:**

- This is the **third** authorised observable difference. FR-009's block enumerates `DIFF-001`,
  `DIFF-002` and `DIFF-003`; every guard that counts them expects three.
- `baseline suite unavailable` is a **condition that does not exist in `main`**: the gate emits 14
  terminal conditions there and 15 here, and this is the one added. `test_gate_refusal_coverage`
  derives the set from `gate.py`'s AST, so the count is never asserted by hand.
- The gate returns immediately on this refusal — no delegation, no later effect, no `run result:`.
- The diagnostic and the remediation are stable text, pinned by the transcript pair.
- **Both sides are kept as evidence**: `evidence/golden/refusal-baseline-unavailable.main.txt` and
  `refusal-baseline-unavailable.txt`, plus the nine other conditions, each with a `main` side that
  is byte-identical to the current one. `test_main_baselines` fails if a side goes
  missing, if one of the nine stops matching, if this one differs in any way other than `DIFF-003`,
  if a fourth difference appears, or if `DIFF-003` leaves FR-009 or this decision.
- The `main` baselines are **retrospective**, captured at CONF-006 from an extraction of `141638b`,
  not at T001. `evidence/golden/index.json` records the provenance and the guard cross-checks it
  against the header each artifact carries, so the commit cannot change without a regeneration that
  updates both.
- No production behaviour changes here. The semantics being registered is the one already in the
  tree; this decision documents and pins it.
