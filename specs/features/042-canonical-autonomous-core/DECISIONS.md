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

**Decision:** T001 records exit code, stdout and stderr for ten scenarios — clean first entry, each
gate refusal, dry run, dry-run adopt, concurrent run, unresumable state, cap abort, budget
exhaustion, human escalation, core-complete — against the **pre-refactor** code. T019 replays them
after. The only permitted difference is FR-009's `Protocol version` line.

**Reasoning:** An oracle captured after the refactor proves the refactor agrees with itself. Ordering
this first is the whole value, which is why it is T001 and why no implementation task may precede it.

**Consequences:** If a scenario turns out not to be reproducible deterministically, that is a finding
about the CLI's testability, recorded as such — not a reason to drop the scenario or to weaken
AC-008.

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
