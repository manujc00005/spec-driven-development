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
