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

| Criterion | Planned evidence | Status |
|---|---|---|
| AC-001 | Disposable happy-path run: REJECT → task → fix → APPROVE → close → PR description | Fixture ready; run pending T009 |
| AC-002 | Six isolated entry-gate refusal cases with remediation | PASS T010: all six isolated; baseline also tested red and green-mutating |
| AC-003 | Five agent contracts match the canonical schema; consistency suite green | Baseline green; contract evidence pending T003/T005/T006/T015 |
| AC-004 | Seeded technical and human-gated blockers, with independent work continuing | PASS T011: D001 recorded before T001; T002 waiting; independent T003 completed; run PAUSED |
| AC-005 | Interrupted run resumes idempotently; fingerprint invalidation is selective | Pending T012 |
| AC-006 | Forced REJECT/malformed verdict aborts exactly at the cap | Pending T013 |
| AC-007 | Default-branch refusal, provider paths, and command-log safety inspection | Dedicated main and disposable calibration branches established; remaining evidence pending T014/T015 |
| AC-008 | Interrupted attempt recovery plus all-stale approval invalidation | All-stale invalidation passed in hardened T009; dirty-write recovery pending T012 |
| AC-009 | Finding registry deduplicates repeated finding IDs | PASS in hardened T009: two SEC-001 rejects → one row and one T002 |
| AC-010 | Clean baseline and frozen-fingerprint closure boundary | PASS: closure boundary T009; red and green-mutating baselines T010 |

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
