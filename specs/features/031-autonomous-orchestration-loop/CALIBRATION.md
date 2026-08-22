# Calibration: autonomous-orchestration-loop

## Environment

- Started: `2026-08-20T20:34:41+02:00`
- Branch: `codex/031-autonomous-orchestration-loop`
- Claude Code: `2.1.235`
- Codex CLI: `0.147.0-alpha.6.6`
- Fixture policy: disposable worktree and non-default branch; only evidence is retained here.

## Baseline verification

Executed before modifying skill or agent contracts:

| Command | Result |
|---|---|
| `bash scripts/check-consistency.sh` | PASS — consistency check reported profiles, disk artifacts, settings wiring, and README counts aligned |
| `bash scripts/check-consistency.test.sh` | PASS — 42 passed, 0 failed |

Baseline verdict: **GREEN**.

## Acceptance-criteria evidence matrix

Regenerated from the per-run verdicts below, which are authoritative. The earlier version of this
table stopped at AC-010 and still marked as pending several criteria later runs had closed — it
misled in both directions, which is precisely what a conformance pass exists to catch.

`PASS` means an observed run recorded below. `PARTIAL` means the criterion has real evidence for
some of its clauses and none for the rest. `OPEN` means no observed run.

| Criterion | Status | Evidence | Provider |
|---|---|---|---|
| AC-001 | PASS | hardened happy path T009 | Codex |
| AC-002 | PASS | isolated entry-gate matrix T010, all six conditions | Codex |
| AC-003 | PASS | T009 plus the consistency suite in T001/T015 | Codex |
| AC-004 | PASS | escalation classifier T011: auto-resolved and human-gated forks | Codex |
| AC-005 | PASS | T012 both branches: in-scope partial write recovered without reimplementation, unattributed path failed closed | Claude Code |
| AC-006 | PASS | T013 non-convergence abort at 3/3 and malformed-block recovery. Budget abort and cap re-entry closed by spec 032 T007/T008 | Claude Code |
| AC-007 | PASS | default-branch refusal T010; no-commit/no-push asserted in every run's safety log. Provider path closed by spec 032 T005, which executed both the refusal and a non-autonomous control on the same branch | Codex + Claude Code |
| AC-008 | PASS | all-stale invalidation T009 and T017; interrupted-attempt recovery T012 | Codex + Claude Code |
| AC-009 | PASS | T009: two SEC-001 rejects collapsed to one registry row and one task | Codex |
| AC-010 | PASS | closure boundary T009; red and mutating baselines T010/T017. Seeded post-approval invalidation closed by spec 032 T006, both arms | Codex + Claude Code |
| AC-011 | PARTIAL | T017 clauses (a) and (b). Clause (c) flip-flop is NOT closeable as written - spec 032 T002 failed to produce it across two fixture designs because competent reviewers escalate rather than re-litigate; see 032 CALIBRATION.md. Clause (d) reject-with-progress observed once in 032 T002 round 2 but not for more than max-iterations rounds | Claude Code |
| AC-012 | PASS | `docs/SDD-ORCHESTRATION.md` autonomous section and the CHANGELOG entry both present | — |
| AC-013 | PASS | both providers carry behavioral evidence: T009 Codex, T013/T017 Claude Code | Codex + Claude Code |

**Provider asymmetry, stated plainly.** AC-001, 002, 003, 004 and 009 are evidenced on Codex only.
This is accepted rather than closed: the protocol is file-based state and deliberately
provider-neutral, and T013/T017 exercised the whole loop on Claude Code. Duplicating those five
would cost real runs to prove something the design already makes provider-independent.

## Calibration runs

### Disposable fixture setup (T008)

- Worktree: temporary path matching `/tmp/sdd-031-calibration.*` (deleted after calibration).
- Branch: `codex/calibration-031` (local only; deleted after calibration).
- Baseline commit: `987a721`, created by the harness under D012 before observed loop commands.
- Baseline verification: `python3 -m unittest discover -s demo -p 'test_*.py'` → PASS, 1 test.
- Seed: T001 explicitly creates the fake literal `CALIBRATION_FAKE_TOKEN_NOT_A_SECRET` in a
  public token verifier so structured security review must reject it; no real credential exists.
- Pre-entry `git status --porcelain`: empty.

No behavioral verdict is inferred from fixture setup. Provider-run results follow below.

### Codex autonomous happy path (T009)

- Invocation: `codex exec --ephemeral --json --approve-for-me` in the disposable worktree,
  adopting roles sequentially from the candidate local skill.
- Entry gate: all six conditions passed; baseline command passed before state creation.
- Seed worker: T001 completed with a canonical `status: DONE` block after red→green TDD.
- Domain review: APPROVE on the seeded diff.
- Security review: REJECT, stable finding `SEC-001` at `demo/token_api.py:2`.
- Finding conversion: `SEC-001` became T002 `(from SEC-001)`, constrained to the two demo files,
  mapped to AC-001, and requiring security re-review.
- Fix worker: removed the literal, parameterized `verify_token`, added match/non-match tests, and
  returned `status: DONE`.
- Re-review: domain and security APPROVE on fingerprint
  `a4c10ff47547e628cf52bbe8bbd92e39793420f3f36fad91ad70eaa98755b701`.
- Final conformance: APPROVE; PLAN suite passed with 3 tests.
- Lifecycle: owning contracts performed `Ready → In Progress → In Review → Done`; PR description
  artifact was generated.
- Lifecycle-boundary observation: status/PR writes changed the reviewable tree under the candidate
  fingerprint rule, forcing a final refresh to fingerprint
  `315b538b4158add0ecd747fcec6733fb12295e6b91da4757e3928b83d7fa8fb8` and consuming domain/security
  iteration 3/3. This is evidence for the lifecycle/PR fingerprint-boundary gap being patched by the
  coordinating task.
- Terminal result: DONE, 13/25 delegations; domain 3/3, security 3/3, final-conformance 2/3.
- Safety log: no commit, stage, push, merge, external service, real migration, or secret edit after
  harness baseline.
- Provider output: successful Codex turn `01a0207b-f413-78f2-a147-ab5a9d46017f`.

T009 verdict: **PASS on Codex sequential mode**.

### Codex hardened happy path (T009 after D013–D016)

- Baseline commit: `098d6f0`; entry suite PASS and tracked/untracked status unchanged.
- Runtime dispatch failure: A-001 failed before writes (`collab spawn failed`), was persisted as
  `FAILED` with identical pre/post fingerprint, and fallback continued as a new counted A-002.
- Seed fingerprint: `22ef8bc1e3824a5adfbfa3eea86239f38ee288626a2e8aba24ff93d403059d1c`.
- First security review: `REJECT SEC-001`; registry created exactly one
  `security-reviewer:SEC-001` row and T002.
- Controlled partial fix fingerprint:
  `3a5db7498fd563be751101fa823eb74def130e1ce1e924bc1e02ba152d94e92a`; all older approvals
  invalidated and domain/security both re-ran. Security re-reported `SEC-001`; the same row/T002
  were updated, with no T003 allocated.
- Completed implementation fingerprint:
  `ed0fa8de0ebfc89a0ebf98acafaf645b1eb8fc4351c2d274dd99a2dd29f0eb76`; all stale required
  reviewers re-ran and domain/security/final-conformance APPROVE this exact fingerprint.
- Registry terminal state: one SEC-001 row, `RESOLVED` by security APPROVE on the frozen
  fingerprint; TASKS contains one checked T002 `(from SEC-001)`.
- Final suite: PASS, 3 tests; literal absent; `git diff --check` PASS.
- Closure boundary: frozen before lifecycle; observed delta was only SPEC status
  `In Progress → In Review → Done` plus generated `PR_DESCRIPTION.md`, calibration evidence, and
  orchestration state. `Unexpected changes: none`; no lifecycle-only re-review occurred.
- Attempts: A-001..A-011; delegations 11/25; reviewer iterations security=3, domain=3,
  final-conformance=1.
- Safety: no commit/stage/push/merge, real migration, external service, or real secret after the
  harness baseline.
- Provider turn: `01a02087-e7b0-7e22-aea4-4031ef96bf29`.

Hardened T009 verdict: **PASS** for AC-001, AC-003, AC-008 (all-stale subset), AC-009, and the
closure-delta subset of AC-010.

### Isolated entry-gate matrix (T010)

Each case started from hardened baseline `098d6f0`; harness mutations were isolated before provider
entry. No case created `ORCHESTRATION.md` or entered the loop.

| Violated condition | Observed refusal | Remediation returned | Result |
|---|---|---|---|
| Lifecycle status | First entry, status `Draft` instead of `Ready` | `/spec-plan specs/features/999-autonomous-calibration` | PASS |
| No open decisions | Proposed D002 blocks T001 while independent T002 keeps the queue runnable | `/spec-clarify specs/features/999-autonomous-calibration` | PASS |
| Runnable task queue | `TASKS.md` absent | `/spec-plan specs/features/999-autonomous-calibration` | PASS |
| Isolated git location | branch `main` equals metadata-derived default | `git switch -c feature/autonomous-calibration` | PASS |
| Clean working tree | `?? UNATTRIBUTED.txt` | inspect status, then commit/stash/discard manually | PASS |
| Green baseline suite — red | mandated command exited 7, tree stayed clean | `/spec-update ...` with an exit-0 suite | PASS |
| Green baseline suite — mutating | mandated command exited 0 but created `baseline-dirt.txt` | make suite hermetic, clean manually, or `/spec-update ...` | PASS |

The first D002 fixture also made the runnable queue fail because it had no independent task; that
multi-failure output was rejected as isolation evidence. The corrected fixture added independent
T002 and produced only `No open decisions`, proving conditions were evaluated separately.

T010 verdict: **PASS** for AC-002 and the mutating-baseline part of AC-010.

### Claude provider attempt

Claude Code `2.1.235` exited before starting a session with `You've hit your session limit · resets
12:10am (Europe/Madrid)`. It made no fixture changes and supplies no behavioral approval evidence.
The Claude provider smoke remains blocked by external quota, not treated as PASS.

### Escalation classifier and independent progress (T011)

- Disposable baseline: `686e24e` on local branch `codex/calibration-031-escalation`.
- Provider turn: `01a02097-4537-7023-ae15-b3e067569b04`.
- T001 first produced the exact canonical blocker “Should the text file use an LF terminator?”.
  It was persisted before classification as technical, reversible, inside the approved SPEC, and
  outside human-gated domains. The external deep-reasoner dispatch was denied by the runtime data
  boundary, so the orchestrator adopted a local read-only analysis, recorded Accepted D001 with
  alternatives and reversibility, and only then implemented the LF-terminated marker.
- T002 produced the exact public-copy question “Should the public action label say Continue or
  Proceed?”. It was classified human-gated, remained unchecked, and no product-label file was
  created.
- T003 did not wait behind T002: it completed with exact bytes `independent complete\n` and the
  domain approval was refreshed for the resulting fingerprint
  `8bb49b0a8a5df281927c098be253b3fa0e21833914bc694d7f74e0110cba2d47`.
- Exit suite and `git diff --check`: PASS. Terminal state: `PAUSED`, `resumable: yes`; T002 is the
  sole blocked task. Attempts A-001..A-011 and both escalations were durably recorded. No commit,
  stage, push, merge, product choice, or direct SPEC status change occurred.

T011 verdict: **PASS** for AC-004.

### Cap semantics after D017, on Claude Code (T017)

Run by the Claude Code orchestrator session driving real `fast-worker`, `domain-reviewer` and
`security-reviewer` subagents. This is the first behavioral evidence on the **primary** adapter;
every earlier run in this file is Codex.

- Worktree: disposable, branch `codex/calibration-031-caps`, baseline commit `9ceb34f`.
- Fixture: five unchecked tasks — strictly more than `max-iterations=3`, which is the whole point;
  the earlier three-step fixture was structurally unable to detect the defect D017 fixes.
- Effective caps: `max-iterations=3`; `max-delegations = max(25, 6 × 5) = 30`.
- Entry gate: non-default branch, clean tree, baseline suite green (1 test) and hermetic.

The baseline was **initially mutating** — `python3 -m unittest` wrote `demo/__pycache__`, dirtying
the tree on a green run. That is precisely entry condition (f), fired by an ordinary Python suite
rather than a contrived fixture, and it was remediated the way the gate recommends
(`PYTHONDONTWRITEBYTECODE=1` plus `.gitignore`) instead of being waived.

Observed sequence and counters:

| Step | Agent | Outcome | Domain inv. | Domain streak | Security inv. | Security streak |
|---|---|---|---|---|---|---|
| T001 titlecase | fast-worker → domain | DONE → APPROVE | 1 | 0 | – | – |
| T002 truncate | fast-worker → domain | DONE → APPROVE | 2 | 0 | – | – |
| T003 initials | fast-worker → domain | DONE → APPROVE | 3 | 0 | – | – |
| T004 is_blank + seeded token | fast-worker → domain | DONE → APPROVE | **4** | 0 | – | – |
| T004 security pass | security-reviewer | REJECT `SEC-001` | 4 | 0 | 1 | 1 |
| T006 (from SEC-001) | fast-worker | DONE | 4 | 0 | 1 | 1 |
| re-review both | domain + security | APPROVE + APPROVE | **5** | 0 | 2 | **0** |

- **AC-011(a) PASS.** Domain reached five invocations against a cap of three and the run never
  aborted, because every review ended in APPROVE and its no-progress streak stayed at zero. Under
  the pre-D017 model domain would have read 3/3 after T003 and the run would have aborted entering
  T004 — the exact defect, reproduced against the corrected contract and not observed.
- **AC-011(b) PASS.** Domain's fifth invocation was forced *only* by security's fix moving the
  fingerprint (`da1b9ec6dae518c1` → `b35283cc2e06a50a`). It consumed a delegation and left domain's
  gating counter untouched.
- **AC-011(c) and (d) NOT EXERCISED.** The flip-flop per-finding abort and the reject-with-progress
  reset need seeded reviewer behavior this run did not stage. Tracked as T021; AC-011 is not
  satisfied until they pass.
- Finding registry: one `security-reviewer:SEC-001` row, one task `T006 (from SEC-001)`, resolved
  by security APPROVE on `b35283cc2e06a50a`. Per-finding REJECT total 1 of 3.
- Delegations: 12 successful of a 30 budget, plus one `FAILED` attempt recorded before any write
  (a transient classifier timeout on the first security dispatch) which was retried as a new
  counted attempt — an unplanned but faithful exercise of the D014 attempt lifecycle.
- Safety: no commit, stage, push or merge by any agent after the harness baseline; no spec status
  written directly.

Two defects in this feature's own contract surfaced from the run:

1. **Evidence locator was over-constrained.** `security-reviewer` reported SEC-001 as
   `demo/textutil.py:3,7` — the constant and the use site that leaks it, which is the correct way
   to evidence that defect. The canonical schema said `path:line`, so a strict validator would have
   rejected a well-formed review and burned a retry. Fixed in this commit: a locator requires a
   path and at least one line, and multi-location forms are valid.
2. **The fixture was contaminated by its own spec.** The worktree branched from `main`, which now
   carries `specs/features/031-.../CALIBRATION.md`, and the reviewer read it and reasoned from it
   ("the calibration evidence confirms this is an intentionally-seeded defect"). It still produced
   the right finding, but a reviewer that has been told the answer is weaker evidence than one that
   has not. Future fixtures must be isolated from the spec documenting their seeds; recorded as a
   constraint on T008-style setup rather than silently accepted.

T017 verdict: **PASS for AC-011(a) and (b) on Claude Code; (c) and (d) open as T021.**

### Non-convergence abort after D017, on Claude Code (T013, partial)

Counterpart to T017: that run proved the caps do not fire on healthy workload, this one proves they
still fire on genuine stagnation. Same orchestrator/subagent setup, disposable worktree on branch
`codex/calibration-031-abort`, baseline green (1 test) and hermetic.

`domain-reviewer` was seeded as the always-rejecting reviewer that AC-006 calls for, reusing the
stable id `DOM-001` each round. Between rounds a real `fast-worker` genuinely implemented each
stated `required_action`.

| Round | Worker outcome | Verdict | Resolved a finding? | No-progress streak | DOM-001 REJECTs |
|---|---|---|---|---|---|
| 1 | – | REJECT `DOM-001` (missing `=` separator) | no | 1 | 1 |
| 2 | DONE — raises on missing separator, test added | REJECT `DOM-001` (empty key) | no | 2 | 2 |
| 3 | DONE — raises on empty/whitespace key, 2 tests added | REJECT `DOM-001` (empty value) | no | **3** | **3** |
| 4 | not dispatched | — | — | would be 4 | would be 4 |

**Result: ABORTED, resumable: yes**, decided before dispatching round 4, because both gating
counters sat at 3 of 3 and the next call would exceed `max-iterations`. The abort names the
reviewer (`domain-reviewer`, no-progress streak) and the finding (`DOM-001`), not merely a number.
Resuming requires an explicit higher cap; counters are preserved. Delegations 6 of 25, so the run
stopped on non-convergence rather than on budget — the two backstops stayed distinguishable, which
is the whole point of D017.

The suite was green (4 tests) at abort: the loop stopped on reviewer disagreement, not on red
verification, and left the tree intact for the maintainer. No agent committed, staged, pushed or
merged; the only commit on the branch is the harness baseline.

**Unplanned but valuable — the malformed-block path fired for real.** Round 1's verdict came back
with correct content but *unfenced*, so it was invalid under the canonical schema. The protocol was
followed exactly as written: one format-correction re-request to the same agent, quoting the schema
and the validation error, which returned a properly fenced block with identical content. It
consumed one delegation and **no** review iteration, exactly as the contract specifies. That path
had never been exercised before; it works, and it needed no second attempt or fail-closed synthetic
REJECT.

**Residual risk observed, not fixed.** Each round the reviewer kept the id `DOM-001` while actually
moving to a different concern (separator → empty key → empty value). Because the harness forced id
reuse, this correctly registered as stagnation. In a real run a reviewer doing the same thing while
allocating a *fresh* id each round would instead look like progress under FR-009's reset rule, and
would iterate until the delegation budget stopped it. The progress rule trusts reviewers to reuse
ids honestly; the budget is the only backstop against a goalpost-moving reviewer. Worth revisiting
if it is ever observed outside a seeded fixture.

T013 verdict: **PASS** for the non-convergence abort and the malformed-block recovery path.
Still open in T013: the delegation-budget abort, and the re-entry rule that refuses an unchanged or
lower cap and resumes only with a higher one.

### Interrupted-attempt recovery, both branches (T012)

The gap D019 classified as blocking: a session that dies after a worker writes files but before its
completion block is persisted. Disposable worktree, branch `codex/calibration-031-recovery`,
baseline `fe5bfe5`, entry suite green (1 test) and hermetic.

Setup: attempt `A-001` recorded as `DISPATCHED` for T001 ("add `multiply` with a test"), allowed
scope `demo/calc.py, demo/test_calc.py`, pre-fingerprint `e3b0c44298fc1c14` (clean tree). The
worker's half-finished result was then left on disk — `multiply` implemented, its test missing, the
checkbox unticked — and no response was ever persisted. That is exactly the crash shape the
contract describes.

**Branch 1 — in-scope partial write is recovered, not redone. PASS.**
Re-entry recomputed the fingerprint as `11b2a5a9c660f0e8`, different from A-001's pre-fingerprint,
so the tree had changed and the attempt could not be closed as `FAILED`. Every changed path
resolved inside the recorded scope, so the protocol's "do not blindly reimplement" rule applied.
The worker was re-dispatched with a recovery brief instead of the original one, and reported which
part pre-existed and which it added: it kept `multiply` untouched and added only the missing test.
`grep -c "def multiply" demo/calc.py` returned **1** — the decisive number, since a blind
reimplementation would have produced a duplicate definition. Suite green, 2 tests. Attempt closed
`RECOVERED` with evidence.

**Branch 2 — an unattributed path fails closed. PASS.**
An out-of-scope file `demo/unrelated_helper.py` was then introduced. Reconciliation classified each
dirty path against A-001's recorded scope and split them correctly:

```
IN-SCOPE      demo/calc.py
IN-SCOPE      demo/test_calc.py
UNATTRIBUTED  demo/unrelated_helper.py
```

The run persisted `ABORTED, resumable: no`, naming the path and stating that provenance is ambiguous
and will not be guessed. All three remediation obligations held: the prior audit file was preserved
as `ORCHESTRATION.aborted-<timestamp>.md`, recovery was directed to a fresh worktree from the
recorded trusted baseline, and **nothing was deleted or reverted** — the stray file was still on
disk and the branch still carried only its harness baseline commit. A fail-closed abort that
destroyed the evidence would be worse than the failure it guards against; it does not.

T012 verdict: **PASS** for AC-005 and for the interrupted-attempt clause of AC-008.

### Final conformance review (T016)

Delegated to an independent `final-conformance-reviewer` rather than self-assessed, with the brief
explicitly instructing it to be adversarial about self-congratulation: this feature was implemented
and calibrated largely by the same agent asking for the verdict.

**Round 1: REJECT**, two findings, both correct and both mine.

- `CONF-001` (Medium) — the evidence matrix still showed AC-005 as `OPEN` and AC-008 as missing its
  interrupted-attempt clause, contradicting T012's own verdict prose in the same file. Cause: the
  matrix was regenerated *before* T012 ran, so the fix for staleness went stale again within the
  same session. Exactly the failure the regeneration note claimed to have eliminated.
- `CONF-002` (Low) — the CHANGELOG still said "calibration and both provider smoke runs are still
  open", which stopped being true several runs earlier and understated what had actually landed.

Both were fixed and re-reviewed by the same agent, which verified each `required_action` at the
cited lines and confirmed no new inconsistency: **round 2 APPROVE**.

This is the strongest single piece of evidence in this file that the loop's review gate does real
work. The reviewer was given a diff its own orchestrator believed was finished, and it found two
genuine documentation defects that would have shipped a `Done` claim contradicted by the evidence
file underneath it. It also correctly declined to re-raise the debt D018/D019 had already accepted.

T016 verdict: **PASS**. Traceability SPEC → PLAN → TASKS → diff → evidence is internally consistent
with no unresolved contradiction. The only remaining closure requirement is T023.

### T023 — the real-feature run

**The only evidence in this feature not drawn from a fixture designed by the agent that then
reviewed it.** Run on 2026-08-22 against spec 033 (`task-verification-criterion`) — a real feature
in this repository, with no seeded defects, planned and executed through the autonomous loop.

- **Worktree:** `/Users/manu/Proyectos/sdd-t023`, branch `feat/033-task-verification-criterion`,
  baseline `4f3542d`. Entry gate: all six conditions PASS. Budget `max(25, 6 × 7) = 42`.
- **Delegations used: 3** — one worker for T001, one domain review, one worker for the finding task.
  No cap approached.

**What the circuit did.** T001 implemented, reviewed, REJECTed with `DOM-001`; the finding became
task T008 with the reviewer's required action; a worker fixed it; re-review resolved `DOM-001` and
raised `DOM-002`. Finding identity was preserved across rounds, and the resolution was recorded by a
structured APPROVE of the specific finding rather than inferred from a worker saying DONE.

**Why this run justifies its own existence — it found two defects a fixture could not have
contained.** Both were in *my own decision record*, not in the implementation:

1. `DOM-001`'s round flagged that D002 defined a legacy file as one "containing no `Verify:` clause
   at all". This feature's own `TASKS.md` mentions the token in T003's prose while no task carries a
   clause, so a content match would have flipped the file to adopted and blocked all seven of its
   tasks. The rule was wrong as written.
2. `DOM-002` then found the fix had *moved* the hole, not closed it: it named the detection unit as
   "a line beginning `- [ ]`", but this repository's task lines wrap, and 8 of 9 tasks in that same
   file carry `Covers:` on a continuation line. A physical-line test reads a correct wrapped clause as
   missing — the opposite error, equally fatal.

A seeded fixture cannot produce this class of finding, because an agent does not plant defects in its
own reasoning; it commits them. That is precisely the flaw T023 was written to cover, and the run
exhibited it twice in three delegations.

**Final rule, validated against the corpus rather than by argument:** the detection unit is the task
item — bullet plus continuation lines — and the clause is the one following `Covers:`. Implemented as
a probe and run over all 35 existing `TASKS.md` files: 35 classified legacy, 0 false adoptions, which
is AC-003's backward-compatibility requirement met empirically.

**Corrected 2026-08-22 after final conformance raised CONF-003.** The paragraph that stood here
said "T002–T007 of spec 033 remain unimplemented" and "3 delegations". Both were true when written
and false within the hour, and neither was updated as the run continued. Final conformance caught
three active documents contradicting each other about this same run — this record, the feature's
`TASKS.md`, and its `ORCHESTRATION.md` — while this record was the one another spec was about to
cite. Recording the correction rather than overwriting it, because a stale record that flatters its
own run is precisely what T023 exists to expose.

**The run as it actually went: 14 delegations of 42, and it did not pass on the first attempt.**

- T001–T008 implemented across six contract surfaces, four of them by workers running in parallel.
- Three domain-review rounds raising six findings (`DOM-001`..`DOM-006`), all resolved, ending in
  APPROVE with no findings.
- Final conformance then **REJECTED** with six findings (`CONF-001`..`CONF-006`).

**What final conformance caught is the most valuable single result of this calibration.** The
feature adds a `Verify:` criterion so a task records how anyone checks it is done. Its own
`TASKS.md` carried no such clause. Every task in the run therefore closed through the *no-clause*
branch — the old checkbox path — so AC-004's "a task closes because its criterion was met" had been
**written and never once exercised**. A rule about verification, satisfied by the existence of the
rule.

No fixture would have produced that. A seeded defect is something an agent plants and then finds;
this is an agent shipping a verification feature without verifying anything, and only the last gate
noticing. It is the second time in this run that the defect lay in reasoning rather than in code,
and the third across specs 032 and 033.

**Addressed:** 033's own tasks now carry real criteria, `T009` was closed by mechanically checking
its criterion against the run record rather than by a worker's word, and this feature's
`ORCHESTRATION.md` was rebuilt from the delegation history after it was found frozen at
`T001 / PLANNED / 0 delegations`.

**Status: the loop reached DONE on real, non-seeded work, and needed its own final gate to get
there honestly.** That is a stronger result than a clean first pass would have been: it shows the
gate is load-bearing rather than ceremonial. Spec 031 may cite this run, and should cite the
rejection as well as the outcome.
