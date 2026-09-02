# Calibration: autonomous-adopt-in-flight-feature

Evidence for AC-014 (both providers) and for every criterion observable in a run (T012). The subject
is the T001 fixture (`make_adopted_repo`) materialized at
`scratchpad/calib-041/adopted`, with a maintainer-committed `PLAN.md`, `DECISIONS.md`, hermetic
`verify.sh` and `.gitignore` on top. Adoption baseline `2ed6adc`, diff base `8069b19`, branch
`feat/adopted`, default branch `main` via `origin/HEAD`. Orchestrator: Claude Code (this session),
following `skills/sdd-orchestrate/SKILL.md` as edited by T002–T005.

## Provider runs (AC-014)

| Provider | Result | Evidence |
|---|---|---|
| Claude Code | see per-criterion rows below | this file, section *Claude Code run* |
| Codex | **pass** (2026-09-02, `codex-cli 0.152.1`) | this file, section *Codex run* |

## Claude Code run

### Refusal matrix (AC-002, AC-003, AC-004)

Each case is a copy of the calibration repo; the orchestrator evaluated the gate conditions with the
commands the skill names and the runner's gate was run on the same copy as a cross-check
(`PYTHONPATH=runner python3 -m sdd_runner --repo <copy> --feature specs/features/901-adopted --dry-run [--adopt]`).

| Case | Setup | Skill gate (orchestrator) | Runner gate | Criterion |
|---|---|---|---|---|
| A | `In Progress`, no `--adopt` | `Lifecycle status` — first entry, Status is In Progress; remediation names `--adopt` | exit 10 `lifecycle status` | AC-002 |
| B | `Ready`, `--adopt` | `Adoption not needed` — run without `--adopt` | exit 10 `adoption not needed` | AC-002 |
| C | `ORCHESTRATION.md` present, `--adopt` | `Already adopted or entered` — re-enter without `--adopt` | exit 10 `already adopted or entered` | AC-002 |
| D | one uncommitted path (`src/pricing.py`), `--adopt` | `Clean working tree` — 1 dirty path: ` M src/pricing.py`; remediation `git add -A && git commit` | exit 10 `unattributed dirty tree` | AC-003 |
| E | on `main` + untracked `wip.txt`, `--adopt` | `Isolated git location` then `Clean working tree`, in that order (plus `Adoption not needed`, because `main` carries the planned `Ready` spec) | exit 10: `adoption not needed`; `default branch`; `unattributed dirty tree` — same order | AC-004 |
| F | the real repo, `--adopt` | **GATE PASSES** | exit 0, prints entry `adopt`, baseline, diff base, 2 inherited rows | AC-001 |

No refusal created `ORCHESTRATION.md` (checked: absent in copies A, B, D, E after the gate).

### Happy path — adopted run with two inherited tasks and a seeded defect (AC-001, AC-005, AC-007, AC-008, AC-012)

Full state file: [evidence/ORCHESTRATION-adopted-run.md](evidence/ORCHESTRATION-adopted-run.md). Eight
delegations, budget 25.

| Criterion | Observed | Evidence |
|---|---|---|
| AC-001 | Gate passed on the real repo; `ORCHESTRATION.md` created with `Entry: adopt`, `Adoption baseline commit: 2ed6adc…`, `Adoption diff base: 8069b19… (against main)`, two `Inherited` rows (T001, T002) each `Verification observed by this run: no`; budget `max(25, 6 × 2) = 25` | evidence file, header and `## Inherited` |
| AC-005 | First two delegation-log entries are `domain-reviewer` A-001 on `8069b19..2ed6adc` (security not triggered: pure arithmetic). Verdict REJECT, `DOM-001 Critical` at `src/pricing.py:6-8` (the seeded `member` bypass). One task `T005 … (from DOM-001)` created; no spec task delegated until A-003 re-review returned APPROVE. Then T003 (A-004 worker, A-005 domain APPROVE) and T004 (A-006 worker, A-007 domain APPROVE) | evidence file, `## Attempts` A-001…A-007 and `## Findings` (DOM-001 `resolved`, resolving verdict `APPROVE A-003`) |
| AC-007 | After DONE: `--adopt` → *Already adopted or entered*; without `--adopt` → *Lifecycle status* (SPEC `Done`, state `DONE`, `resumable: no`). Runner cross-check re-run 2026-09-02 after T020/T024: `--adopt` → exit 10 `already adopted or entered` (unchanged); **without `--adopt` → exit 16**, not 10, because the runner now authenticates the document first and this one was written by the orchestrator, not by `sdd_runner`. The refusal is more precise than the original `lifecycle status`, and the row is corrected rather than left as recorded | this file and the runner stderr |
| AC-008 | `final-conformance-reviewer` A-008 report carries a section `Inherited tasks` labeling T001 and T002 **inherited, verification not observed**, and notes that T002's clause was true on the defective implementation; verdict APPROVE | evidence file, A-008 outcome |
| AC-012 | Every-exit assertion: HEAD `2ed6adc` before and after, `origin/feat/adopted` unchanged, no stash; SPEC status lines written only by `/spec-review` (Pass → In Review) and `/spec-close` (→ Done); closure delta = SPEC.md Status block + generated PR_DESCRIPTION.md + ORCHESTRATION.md, no unexpected path | evidence file, `## Closure delta` and last delegation-log row |
| Termination | `Run result: DONE`, frozen implementation fingerprint `18bf67a80fc8@2ed6adc` with domain and final-conformance APPROVE at that fingerprint; `PR_DESCRIPTION.md` generated ([evidence copy](evidence/PR_DESCRIPTION-adopted-run.md)) | evidence file, `## Run result` |

Commands the orchestrator ran to check worker claims (each recorded in the attempt's `Outcome`):
`python3 -c "from src.pricing import discount; …"` for T005 and T003 (`1500 → 1500`, `1500/member → 500`,
`100/member → 0`), `python3 -m unittest src.test_pricing` for T004 (`Ran 7 tests … OK`), and
`./verify.sh` after every task (`verify: green`, porcelain unchanged).

### All-checked adoption (AC-006)

Full state file: [evidence/ORCHESTRATION-allchecked-run.md](evidence/ORCHESTRATION-allchecked-run.md).
Copy of the fixture with T001–T004 implemented and committed by hand (`3b99a3a`), `In Progress`, no
state file, terminal-ready queue.

| Criterion | Observed | Evidence |
|---|---|---|
| AC-006 | Gate passed (0 unchecked tasks accepted as terminal-ready; budget `max(25, 0) = 25`). Delegations: A-001 `domain-reviewer` on the inherited diff → APPROVE; A-002 `final-conformance-reviewer` → APPROVE with four *inherited, verification not observed* labels. **No implementer/fast-worker delegation** (0 in `## Attempts`). `/spec-review` Pass → In Review, `/spec-close` → Done, `PR_DESCRIPTION.md` generated; `Run result: DONE` after 2 delegations | evidence file |

### Lessons recorded

- **Tick before fingerprinting.** In the first run the orchestrator computed A-003's reviewed
  fingerprint and ticked T005 afterwards, so the approval's fingerprint (`867e…`) differed from the
  tree's (`c9ea…`) by the checkbox alone. `src/` was identical and the next review refreshed the
  approval, but the protocol order is: verify the claim → tick the task → compute the fingerprint →
  review. From A-004 on the run did exactly that and every approval matched its tree.
- **Closure delta is per path, not the whole-tree fingerprint.** `SPEC.md` is inside the fingerprint
  rule, so the lifecycle status lines move the whole-tree hash; the termination section already says
  the closure delta is audited separately, and the run did so (hunks confined to the Status block,
  every other path untouched).
- **Two maintainer-side refusals were real, not synthetic.** The fixture's first PLAN suite mutated
  the tree (`src/__pycache__/`) and its `unittest discover` exited 5 with no tests (Python ≥ 3.12);
  both are condition-6 refusals the maintainer fixed (`.gitignore`, hermetic `verify.sh`) before
  adoption could start.
- **Vocabulary.** The 041 texts originally said `blocker` for the inherited-diff gating severity; the
  closed reviewer enum is `Critical | High | Medium | Low`. Corrected before the first delegation
  (SKILL, SPEC, PLAN, TASKS, DECISIONS, docs).

## Codex run (AC-014, T013) — PASS

Run 2026-09-02 against `codex-cli 0.152.1`, installed at `~/.local/bin/codex`. The CLI **is** on this
machine; the earlier "not available" blocker was wrong and is superseded by what follows. Invocation
follows this repo's own isolation convention (`scripts/skill-eval.sh`): `--ignore-user-config
--ephemeral`. Fixture: a fresh `make_adopted_repo` with `PLAN.md`, `DECISIONS.md`, `verify.sh` and
`.gitignore` committed; baseline `a6be6c6`, diff base `5547a96`, branch `feat/adopted`, clean tree.

### Run A — refusal without `--adopt`

```text
$ codex exec --ignore-user-config --ephemeral --sandbox read-only --cd <fixture> - < promptA.txt
AUTONOMOUS REFUSED
- condition: Lifecycle status
  observed: First entry has no ORCHESTRATION.md, but SPEC.md status is `In Progress`, not exactly `Ready`.
  remediation: /spec-plan specs/features/901-adopted
```

Codex inspected the real repository (`git status`, `git symbolic-ref`, and the four SDD documents)
before answering; it did not assume. Same condition Claude Code reported for case A, and the same
the runner exits 10 with.

### Run B — adopt gate, state initialization, inherited-diff verdict

```text
$ codex exec --ignore-user-config --ephemeral --sandbox workspace-write --cd <fixture> - < promptB.txt
verdict: REJECT
findings:
  - id: DOM-001
    severity: Critical
    evidence: src/pricing.py:6
    summary: The inherited implementation discounts non-members, violating AC-001 and checked task T002.
    required_action: Make discount subtract MEMBER_DISCOUNT only when member is true, without implementing unchecked T003 or T004.
```

What it produced, checked against git rather than taken on trust:

| Check | Result |
|---|---|
| Gate | passed with `--adopt`; Codex stated it would "only write state if every gate condition passes", and it wrote it |
| `ORCHESTRATION.md` header | `Entry: adopt`; `Adoption baseline commit: a6be6c69…` and `Adoption diff base: 5547a96b… (against main)`, both **byte-identical to `git rev-parse HEAD` and `git merge-base main HEAD`** |
| Budget | `max(25, 6 × 2 unchecked tasks at adoption)` = 25 |
| `Inherited` table | two rows, T001 and T002, each with its `Verify:` clause and `no` in the last column |
| Unfilled placeholders | zero |
| Verdict block | valid; `DOM-001`, severity `Critical`, evidence `src/pricing.py:6` — the same finding identity and severity Claude Code's `domain-reviewer` reported on the same seeded defect |
| Files touched | only `specs/features/901-adopted/ORCHESTRATION.md` |

**Stated caveat.** Condition 6 (green baseline suite) was not exercised: the prompt told Codex to
assume `./verify.sh` green rather than spend a run on it. Codex recorded that honestly in the state
file it wrote — "assumed green per caller instruction and not run" — instead of claiming the check.
The other five conditions plus condition 7 were evaluated against the real repository.

**What this closes and what it does not.** It closes AC-014's Codex row and T013. It is a smoke run
of the adoption entry, not a full autonomous run on Codex: no worker delegation, no repair, no
closure. The sequential-degradation claim in `adapters/codex/PARITY.md` is unchanged.

## Review findings and their repair (2026-09-02)

`/spec-review` returned **Partial** with five findings. Four became tasks T015–T018, traceable by
`(from CONF-041-0N)`; the fifth is answered by the transcript below.

| Finding | Severity | Repair | Evidence |
|---|---|---|---|
| CONF-041-01 | High | T015 — the CLI never passed `first_entry`, so narrowing first entry to `Ready` made every adopted run a one-shot: re-entry refused `lifecycle status`. `first_entry` is now derived from the presence of `ORCHESTRATION.md` | `runner/tests/integration/test_adopt_cli.py::ReEntryThroughTheCLI`, red before the fix (`AssertionError: 10 != 0`), green after |
| CONF-041-02 | Medium | T016 — AC-009's dry-run clause rested on a note the implementer wrote. Now a CLI test asserts the printed record | `test_dry_run_adopt_prints_the_inherited_record`; deleting the printing block makes it fail (mutation checked) |
| CONF-041-03 | Medium | T017 — the runner document recorded only `entry`, so it could not say what it inherited. It now persists `adoption baseline commit`, `adoption diff base` and an `Inherited` table; D006 clarified that "gate-level" bounds dispatch, not recording | `tests.unit.test_entry_default::AdoptionFactsArePersisted` |
| CONF-041-04 | Low | T018 — `loop.py`, `state.py`, `resume.py` added to PLAN's *Impacted areas* | PLAN.md *Impacted areas* |
| CONF-041-05 | Low | no task: the runner column was paraphrase. Transcript below | this section |

Suite after the repairs: **257 tests, OK** (239 on `main`); `check-consistency.sh` exit 0.

### Transcript — the adopt entry through the CLI

```text
$ python3 -m sdd_runner --repo <fixture> --feature specs/features/901-adopted --dry-run --adopt
feature:         <fixture>/specs/features/901-adopted
backend:         claude (not resolved: a dry run dispatches nothing)
unchecked tasks: 2
max-iterations:  3
max-delegations: 25
entry:           adopt
adoption baseline commit: a322f082f803c910b5098ba3d9ffb5b61a228323
adoption diff base:       80673331fa9fa22a3ed69a6305eb877d326ea601 (against main)
inherited tasks: 2 (verification not observed by this run)
  T001  inherited  verify: `python3 -c "import src.pricing"` exits 0.
  T002  inherited  verify: `discount(1500, member=True)` returns 500.
  T003  Clamp totals at zero. Covers: AC-002. Verify: `discount(100, member=True)` returns 0.
  T004  Add the unit tests. Covers: AC-001, AC-002. Verify: `python3 -m unittest src.test_pricin
dry run: nothing dispatched.

$ python3 -m sdd_runner --repo <fixture> --feature specs/features/901-adopted --dry-run   # no --adopt
[GATE] refused: lifecycle status
  detail: SPEC.md Status is 'In Progress'
  remediation: promote the spec with /spec-plan; first entry requires Ready (an In Progress feature started by hand is adopted with --adopt)
$ echo $?
10
```

## Review findings, round 2 (2026-09-02)

The second `/spec-review` was also **Partial**, and its first finding was another regression from
this feature's own runner work. Four tasks, T019–T022.

| Finding | Severity | Repair | Evidence |
|---|---|---|---|
| NEW-1 | Medium | T019 — the empty-tree rule was applied on re-entry too, so a live run could not resume over its own uncommitted `ORCHESTRATION.md`. The rule is now guarded by `first_entry`; re-entry tolerates the paths the run claims plus the artifacts it writes itself | `tests.unit.test_gate::ReEntryTreeRule` (4 cases), red before the guard; transcript below |
| NEW-1b | — | found while fixing it: `_git` strips the whole output, so `git status` loses the first line's leading status space and a fixed `[3:]` slice ate a character of the first path (`1 dirty path(s): rc/pricing.py`). Parsing now splits on whitespace | the refusal detail now reads `src/pricing.py` |
| NEW-2 | Low-Medium | T020 — a dry run returned before `Loop` existed, so it reported a pass for a document `resume.inspect` would refuse. The document is now authenticated where `first_entry` is derived, exiting 15 or 16 | `tests.integration.test_adopt_cli::StateIsAuthenticatedAtTheGate` (4 cases) |
| NEW-3, NEW-4, NEW-6 | Low | T021 — dead `self.inherited` removed; the `__main__` guard moved to the end of `test_entry_default.py`, which had been silently hiding the T017 class from a direct run; `_inherited_record` now raises instead of writing an adopted document with `n/a` fields | `grep` count 0; direct run reports 5 tests, was 2; new NEW-6 test |
| NEW-5 | Low | T022 — T017's `Verify:` clause annotated with `[VERIFY AMENDED]` | TASKS.md |

**T020 caught a fake fixture.** Adding state authentication turned T015's own re-entry tests red:
the skeleton document they wrote was not resumable, so what they proved was "the gate no longer
refuses", not "an adopted run resumes" — exactly the gap NEW-2 named. They now build a document
`resume.inspect` accepts.

**One list, not two.** `gate.RUN_ARTIFACTS` is now the single source for what the runner writes
itself, imported by `Loop._fingerprint`, which had its own copy. A disagreement between those two
lists is what makes a live run unresumable, so they can no longer drift.

Suite after round 2: **266 tests, OK**. `check-consistency.sh` exit 0; installers and manifests
still byte-identical to `main`.

### Transcript — re-entry over the run's own uncommitted state file (NEW-1, after the fix)

The `ORCHESTRATION.md` in the fixture is the document `resumable_state()` builds in
`runner/tests/integration/test_adopt_cli.py`: `writer: sdd_runner`, `entry: adopt`, a
consistent budget, this host and a dead pid. That matters for reading the exit code — a
skeleton document exits 16 here, because T020 authenticates it before the gate runs.

```text
$ git -C <fixture> status --porcelain
?? specs/features/901-adopted/ORCHESTRATION.md

$ python3 -m sdd_runner --repo <fixture> --feature specs/features/901-adopted --dry-run
feature:         <fixture>/specs/features/901-adopted
backend:         claude (not resolved: a dry run dispatches nothing)
unchecked tasks: 2
$ echo $?
0
```

Before T019 the same command refused: `[GATE] refused: unattributed dirty tree / detail: 1 dirty
path(s): specs/features/901-adopted/ORCHESTRATION.md`.

## Review findings, round 3 (2026-09-02)

Third `/spec-review`, third **Partial**, and the first finding was the same defect fixed one file
earlier in the same session. Four tasks, T023–T026.

| Finding | Severity | Repair | Evidence |
|---|---|---|---|
| R3-01 | Medium | T023 — the `__main__` guard in `test_adopt_cli.py` sat before the T020 class, so a direct run silently skipped the only four tests that evidence T020. This is NEW-4 reintroduced one file over, caused by appending a class after an existing guard | direct run now reports **13** tests, the same as discovery; it reported 5. All four test files I touched were checked for the same defect; no other has it |
| R3-02 | Medium | T024 — T020 put state authentication ahead of the gate, which made *already adopted or entered* unreachable for any document that was not a valid runner-written one, contradicting the SPEC edge case, `runner/README.md`, `docs/SDD-ORCHESTRATION.md` and two rows of this file. `--adopt` over an existing document is now answered by the gate first, because it is a statement about intent, not about that document; authentication keeps its precise refusals for a genuine re-entry | `tests.integration.test_adopt_cli::RefusalPrecedence` (4 cases: foreign and terminal documents with and without the flag, plus an unreadable one) |
| R3-03 | Medium | T025 — `attributed` is unwired and nothing records attributed paths, so a real-backend interrupted run cannot be resumed through the CLI. Recorded as **D010** with that limitation stated, named in `runner/README.md`, and the test that exercises it now says in its docstring that it pins a capability, not a behavior | D010; `runner/README.md` *Re-entry and the dirty tree* |
| R3-04 | Low | T026 — D004 said the feature-folder tolerance was removed in both modes; T019 restored a four-path tolerance on re-entry. Clarified in place | D004 `Clarified` note |
| R3-05 | Low | T026 — the "one list, so the gate and the fingerprint agree" comment claimed a parity that does not hold: the fingerprint matches by `endswith`, the gate by exact relative path. Reworded, and the POSIX separator assumption is now stated | `gate.py` `RUN_ARTIFACTS` comment |
| R3-06 | Low | T026 — the early `Orchestration.load` was unguarded, so an unreadable state file escaped as a traceback instead of an exit code | `test_an_unreadable_state_file_exits_with_a_code_not_a_traceback` |

**A row of this file was corrected, not defended.** The AC-007 runner cross-check recorded exit 10
for both halves. Re-run after T020/T024, the no-flag half exits **16**: the runner authenticates the
document first and the calibration file was written by the orchestrator, not by `sdd_runner`. The
refusal is more precise than the original; the row now says so.

Suite after round 3: **270 tests, OK**. `check-consistency.sh` exit 0; installers and manifests
byte-identical to `main`.

### The pattern these three rounds share

Every regression lived in the same place: a gate whose callers were not tested. The unit tests call
`gate.check` directly, so none of them could see that the CLI never passed `first_entry` (round 1),
that the tree rule was unguarded on re-entry (round 2), or that authentication had changed refusal
precedence (round 3). Each was found by review, not by a green suite of 250-plus tests. The CLI-level
test file exists now; it is the thing that was missing.

## Review findings, round 4 (2026-09-02)

Fourth `/spec-review`. **No fourth regression.** The reviewer traced twenty combinations of state
file, `--adopt` and `--dry-run` against the code and the four documents: every exit code claimed
reproduces, no combination is left unauthenticated in a way the loop can accept or crash on, and the
two predicates that decide precedence are the same expression on the same path. All twenty-two
runner test modules carry their `__main__` guard last, so the R3-01 failure mode is closed, not
merely fixed once.

One task, T027, for three documentation corrections:

| Finding | Repair |
|---|---|
| R4-01 | `RUN_ARTIFACTS` and `runner/README.md` both called the four names "the files the runner writes itself", contradicting the same README's *Finalization* section and the code: the runner never writes `PR_DESCRIPTION.md`. Both reworded. The tuple is unchanged on purpose — `Loop._fingerprint` has excluded that name since before spec 041, and dropping it would change fingerprints nobody asked to change. The residual cost is now stated where the rule lives: on re-entry a dirty `PR_DESCRIPTION.md` is tolerated although no run produced it |
| R4-02 | T023's `Verify:` said 9 tests; T024 added four to the same file later in the same round. Annotated `[OBSERVED]` with 13, and with the invariant that actually matters: direct run equals discovery, for all four modules |
| R4-03 | The round-2 transcript did not say what its `ORCHESTRATION.md` contained, and its `exit 0` is only correct because that document was a valid resumable one. The fixture is now named, with the note that a skeleton exits 16 there |

Suite: **270 tests, OK**. `check-consistency.sh` exit 0; installers and manifests byte-identical to
`main`. Twenty-five tasks closed; T013 and T014 remain, both maintainer-only.

## Escalation path observed (T028)

Round 3's review pointed out that nothing in this feature exercised the human-gated escalation path:
the calibration run converged with zero escalations, so "a human-only task surfaces as an escalation
and the run ends `PAUSED`, not as a loop failure" — the originating case's whole point — rested on
031's unchanged code. This run closes that. Full state file:
[evidence/ORCHESTRATION-escalation-run.md](evidence/ORCHESTRATION-escalation-run.md).

Fixture: an adopted feature with a **clean** inherited diff (no seeded defect, so the run reaches the
escalation) and two unchecked tasks — T003, whose `Verify:` is a shop owner comparing a printed sheet
by hand, and T004, unit tests. Three delegations, budget 25.

| Step | Observed |
|---|---|
| A-001 `domain-reviewer` on the inherited diff | APPROVE, findings `[]`. It also declined to raise missing type hints or a `Decimal` wrapper, calling them style rather than defects |
| A-002 `fast-worker` on T003 | `status: BLOCKED` with the question verbatim: the SPEC defines no printed sheet, no ten sample baskets and no sign-off mechanism. **It wrote nothing** — the post-delegation fingerprint is unchanged |
| Classification | **human-gated**: the question fails both "purely technical" and "inside the approved SPEC". Recorded as `ESC-001`, status `waiting`, question copied verbatim |
| A-003 `fast-worker` on T004 | Delegated because T004 is provably independent of T003, which owns no file. `DONE`; the orchestrator checked its `Verify:` clause itself — `Ran 7 tests, OK` — and ticked the task. The worker also reported the orchestrator's own untracked `ORCHESTRATION.md` as not its doing, which is the attribution discipline working |
| Termination | `Run result: PAUSED`, `Resumable: yes`, with the remediation naming what the maintainer must answer and the exact re-entry command (without `--adopt`, because a run is resumed, never re-adopted) |
| Every-exit assertion | HEAD `0f75ab4` = `origin/feat/adopted`, no commit, push, merge or stash by the loop; SPEC status untouched |

T003 stays unchecked and T004 is checked, which is the point: the run neither guessed at the human's
answer nor treated the block as a failure.

**This does not replace T014.** It observes the mechanism on a fixture; T014 observes it on the case
that started this feature, `proyecto-cumbre` 030, with its two real human-only tasks. That repository
is not on this machine — the only copy here is a directory of age-encrypted archives whose key this
session does not have — so T014 stays open and is the maintainer's.

## T014 — the originating case, replayed (2026-09-02)

The maintainer supplied the live path: `/Users/manu/Proyectos/lead-platform-workspace/proycto-cumbre`
(the directory name carries a typo on disk). The replay ran on a copy-on-write copy; the original was
never touched, and was confirmed still on `main` with its 21 dirty paths afterwards.

**The replay was performed and it failed. That is the result, not a pass.**

### Step 1 — the case exactly as it stands

`--adopt` on `main` with the tree dirty produced four refusals. Two are correct and were the point of
the design; two are defects:

| Refusal | Verdict |
|---|---|
| `default branch` — HEAD on `main` | correct, and listed **before** the tree refusal, so following them in order lands the commit on the branch |
| `unattributed dirty tree` — 34 paths | correct |
| `lifecycle status` — **"SPEC.md Status is '```'"** | **defect** |
| `open questions` — 2 unresolved | **defect** |

### Step 2 — after the documented remediation

Branching and committing cleared the first two exactly as `SKILL.md` promises. The other two remain,
so the gate still refuses and the run never starts.

### The two defects

**A. The status parser does not survive an adopter's SPEC dialect.** `gate._status_line` expects the
framework template's `## Status` followed by a bare word. This project writes it inside a fenced
block:

```
## Status

```
Estado: In Review
Blocked-by: —
Parent: —
```
```

The parser returns the opening fence, so the refusal reads `Status is '```'` — a message that tells
the maintainer nothing and a remediation that is wrong. Worse, this project uses **three** dialects
across its own specs (`Complete — 2026-08-20`, `**Complete — 2026-08-22.**`, and the fenced
`Estado:` form), none of which is the template's.

**B. The open-questions parser cannot tell a non-blocking question from a blocking one.** Both
questions it counted are explicitly labelled `(no bloqueante)` by the maintainer, and gate condition
2 only forbids an unresolved question **that blocks an unchecked task**. The parser counts any bullet
that is not struck through or marked Resolved, so it refuses on questions the spec deliberately
carries.

Both fail closed, which is the right direction of error, and both are **runner** defects: the skill
path is model-mediated, and a model reading `Estado: In Review` inside a fence understands it. The
runner transcribes the protocol and, here, transcribes it too literally.

### A third observation, not a defect

Feature 030 has moved to `In Review` since the question that started spec 041. D002 excludes that
status from adoption on purpose — QA and closure have owning skills. So even with both parsers fixed,
**this particular feature is now past the window adoption serves.** The originating case can no longer
be its own test.

### Status of T014

Performed, not passed. Its `Verify:` clause expects two human-gated escalations and `Run result:
PAUSED`; the run never reached the loop, so that outcome was not observed and cannot be until the two
defects are resolved. The escalation mechanism itself is observed on a fixture by T028.
