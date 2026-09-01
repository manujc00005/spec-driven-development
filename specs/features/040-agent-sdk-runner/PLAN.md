# Implementation Plan: agent-sdk-runner

## Summary

Stabilize spec 040 as an **experimental deterministic core**, not as a provider runtime. The core
parses scripted agent blocks, applies the spec-031 counters and budget, persists the shared
`ORCHESTRATION.md` section schema, resumes its own state, records `run.jsonl`, and exposes a real
non-interactive CLI backed by the first-class stub.

D034 accepts architecture option A before any further runner change:

- exit `0` requires a declared green, non-mutating baseline;
- `--feature` is contained under the repository's `specs/features/` directory;
- concurrent ownership is acquired atomically;
- the repository fingerprint includes the current `HEAD` object ID;
- the core stops at the `_finalize` seam without lifecycle or closure delegation;
- shared state is readable by both executors, but re-entry is performed only by the writer;
- provider routing, format retry, writer-scope enforcement, Claude permissions/timeouts, lifecycle
  delegation and closure automation move to a follow-up spec.

The existing Claude adapter remains optional and lazily imported. The existing Codex adapter
remains gated shut. Neither is part of 040's supported or conformance-tested surface.

D035 reconciles the first later implementation pass. D036 adds the AUDIT-1 completion gate and
D037 resolves AUDIT-2 by narrowing FR-005; D038 reconciles those edits with the canonical task
IDs. D046 makes the `_finalize` cut in code.

**Position as of 2026-09-01:** AUDIT-1, 5, 6, 7 and 9 are closed with their acceptance evidence
(T028…T032), AUDIT-2 is resolved in the contract, and AUDIT-3, 4 and 8 belong to the follow-up
provider spec. The out-of-scope Claude adapter remains unobserved and is labelled as such
everywhere. The suite is **239 tests**, green, with T033 the only open task.

## Related spec

[SPEC.md](SPEC.md) — status `In Review`, classification `EXPERIMENTAL`, conformance `PARTIAL`.

## Architecture boundary

| 040 owns | Follow-up owns |
|---|---|
| Pure parser, counters, budget and classifier | Real provider sessions and transport retry |
| Shared state schema and same-writer resume | Versioned cross-executor hand-off, if ever required |
| Stub backend and local subprocess CLI | Claude/Codex execution and provider parity |
| Feature containment, atomic ownership, `HEAD`-aware fingerprint | Writing-agent `path_scope`, tool permissions and provenance |
| Baseline-gated core convergence | `Finalizer`, lifecycle skills, closure delta and PR description |
| Fail closed on the first malformed scripted response | Canonical provider format re-request |

The code seam is `Loop._finalize`: after T032 the 040 side verifies its baseline, records the core
result and stops. A later `Finalizer` begins on the other side of that seam.

## Impacted areas

**Remaining implementation/evidence work after D038:**

- `runner/sdd_runner/__main__.py` — finish real-path containment under `specs/features/`; the
  current `abspath`/repo-level check is partial.
- `runner/sdd_runner/loop.py` and the smallest supporting module needed — finish the `_finalize`
  cut. Atomic ownership, `HEAD` hashing and the baseline gate are present; their T028/T030/T031
  end-to-end evidence is not.
- `runner/tests/` — regressions for AC-015…AC-019 and the strengthened AC-011.

**Specification and documentation:**

- `specs/features/040-agent-sdk-runner/{SPEC,PLAN,TASKS,DECISIONS}.md` — D034 propagation.
- `specs/features/040-agent-sdk-runner/FINAL_CONFORMANCE_REPORT.md` — remains PARTIAL until the new
  criteria pass independently.
- `docs/SDD-ORCHESTRATION.md`, `CHANGELOG.md`, and `CONTRIBUTING.md` — later task T032 updates their
  supported-surface claims to stub-only experimental core.

**Explicitly not touched by this reconciliation update:** runner code, tests, installers,
manifests, profiles, skills, agents and debt records. D035/D036 record implementation already in
the worktree; D038 only repairs its SDD traceability.

## Context budget

### Reading list

- `specs/features/040-agent-sdk-runner/SPEC.md`, `TASKS.md`, `DECISIONS.md` — current contract and
  historical implementation record.
- `specs/features/031-autonomous-orchestration-loop/SPEC.md` and
  `specs/features/032-autonomous-loop-residual-calibration/SPEC.md` — source protocol, read only for
  the core clauses retained by 040.
- `runner/sdd_runner/__main__.py`, `loop.py`, `resume.py`, `closure.py` — only the functions named by
  AUDIT-1/5/6/7/9 when the remaining implementation and evidence work resumes.
- `runner/tests/integration/test_cli_e2e.py`, `test_resume.py`, `test_finalization.py` — existing
  evidence to revise rather than duplicate.

**Out of budget for remaining 040 implementation:** provider SDK documentation, real provider
calls, further `backends/claude.py` behavior, Codex flag verification, lifecycle-skill behavior,
arbitrary-project portability and checkpoint commits. D035's Claude source hardening does not
expand the supported scope.

### Model routing

| Tasks | Routing | Reason |
|---|---|---|
| T028 baseline gate | CLI evidence completion + adversarial test review | The gate exists; all four completion outcomes must now be proved through the subprocess interface. |
| T029 feature containment | security-focused review | Lexical, absolute and symlink escapes must all be refused before writes. |
| T030 atomic ownership | concurrency-focused review | The test must open the pre-state race, not merely start after `ACTIVE` exists. |
| T031 `HEAD` fingerprint | focused implementation | Small change, high impact; the regression must create a real commit with a clean worktree. |
| T032 `_finalize` boundary | architecture-focused review | Removes provider/lifecycle claims without damaging core convergence or historical artifacts. |
| T033 final conformance | independent reviewer | D033 showed that author-run review is insufficient evidence. |

## Proposed approach

### 1. Preserve the proven core

Do not rewrite the parser, counter arithmetic, budget, state serializer, repair registry, redaction
or stub protocol. Their current tests remain regression evidence. New work is limited to controls
the audit proved were recorded but not enforced.

### 2. Convert evidence into gates

- **Baseline:** represent `NOT DECLARED`, failed and mutating baselines as completion-evidence
  failures. None may reach `DONE`/exit `0`.
- **Containment:** resolve both repository and feature directories, then compare using a
  path-aware containment operation. Refuse before any artifact or lock is created.
- **Ownership:** acquire a per-feature lock with one atomic exclusive-create operation. The loser
  exits `15` before state mutation or backend dispatch. Recovery must not turn stale-lock cleanup
  into another race.
- **Fingerprint:** hash the `HEAD` object ID alongside the existing status/diff material. A commit
  is therefore a state transition even if it leaves the worktree clean.

### 3. Keep state interoperable without guessing

`ORCHESTRATION.md` retains the shared section schema and foreign documents remain parseable for
diagnostics. Re-entry checks the writer and resumes only `sdd_runner` state. A foreign document is
not corrupt: it is a safe exit `16` with a hand-off message. No column normalization or guessed
counter reconstruction is added.

### 4. Cut at `_finalize`

The deterministic loop ends after convergence plus the baseline gate. It records run result
`DONE` as **core completion**, never as lifecycle `Status: Done`, and emits no `lifecycle:*`
dispatch, closure delta or `PR_DESCRIPTION.md`. Provider/lifecycle
code already present in the branch is treated as experimental, out-of-scope source until a
follow-up spec owns and tests it; 040 neither runs nor removes it merely to improve its diff.

### 5. Fail closed at every boundary

Missing completion evidence, an external feature path, lost ownership, changed `HEAD`, foreign
writer state, or an attempted lifecycle step all produce named non-success outcomes. No ambiguous
case is converted to an observation that still permits exit `0`.

## Alternatives considered

- **Implement cross-executor resume.** Rejected. Reconstructing another executor's counters and
  attempt lifecycle without a versioned hand-off is guessing; D014's refusal is the safe behavior.
- **Keep provider and lifecycle closure in 040.** Rejected. AUDIT-3/4/8 are observable only through
  a real provider path, while the deterministic core has independent value and evidence.
- **Delete the Claude and Codex modules now.** Rejected for this correction. Claude remains
  optional/lazy and Codex gated as requested; the follow-up decides whether to rehabilitate or
  replace them.
- **Treat a missing baseline as a warning.** Rejected. A warning that still permits `DONE` repeats
  AUDIT-1 exactly.
- **Use only a PID recorded in `ORCHESTRATION.md` as the lock.** Rejected. It cannot close the
  exists-then-create race that AUDIT-6 identifies.

## Dependencies

- Python stdlib and Git, already required by this repository.
- No SDK, provider credential, Codex CLI, scheduler or billable service is required by spec 040.
- `claude-agent-sdk` remains an optional lazy dependency of out-of-scope experimental source.
- The same optional `claude` extra now declares `anyio>=4`, which the adapter imports directly;
  absence of either dependency fails in provider preflight (D035).
- Existing shell/PowerShell suites remain containment regression evidence.

## Risks

| # | Risk | Severity | Mitigation |
|---|---|---|---|
| R1 | Protocol transcription drifts from 031. | Medium | FR-015's honest transcription guard; no claim of behavioral equivalence. |
| R3 | The delegation budget leaks. | High | Pre-dispatch arithmetic and stub invocation counts remain regression-tested. |
| R5 | Same-writer resume duplicates work or resets counters. | High | Persist-before-transition and existing resume corpus; foreign writers fail closed. |
| R8 | Two starts both believe they own the feature. | **Closed (T030, D044/D045)** | The initial document is published whole or not at all — fsynced to a temporary name, then `os.link`, atomic create-if-absent that never replaces — so a contender sees nothing or a complete document, never a truncated one. Proven by a two-phase barrier at the claim itself: one owner, one exit `15`, one worker dispatch, no exit `16`. The earlier pre-CLI barrier could not reach the window and produced a false positive (D044). |
| R12 | A green suite is mistaken for architecture coverage. | Materialized (D033) | Independent conformance after T028…T032; new tests attack each omitted gate directly. |
| R13 | Old provider/finalization code is mistaken for supported 040 behavior. | **Closed (T032, D046)** | The lifecycle dispatch is gone, not merely undocumented: `LIFECYCLE_STEPS`, `_lifecycle_step` and `_phase_index` are deleted, a converged run records `CORE-COMPLETE`, and restoring either a lifecycle dispatch or the closure delta breaks the boundary tests. Docs in `docs/SDD-ORCHESTRATION.md`, `CHANGELOG.md`, `CONTRIBUTING.md` and `runner/README.md` state the stub-only surface. The PARTIAL verdict still stands until T033. |
| R14 | A committed mutation preserves approval in a live loop. | Medium until T031 | `HEAD` is in the digest; still require a backend commit that proves fail-closed approval invalidation. |
| R15 | Symlink or non-feature path escapes the intended feature root. | Medium until T029 | Repo-level lexical containment is present; resolve then contain under `specs/features/` and assert no artifact outside. |

## Test strategy

- **Retained unit/integration regression:** parser corpus, counters, budget, state round-trip,
  redaction, repair cycle, same-writer resume and stub CLI.
- **AC-015 baseline:** four CLI cases — missing, failing, mutating and passing — with exit code and
  persisted reason asserted.
- **AC-016 containment:** contained path, absolute external path, `..` escape and symlink escape;
  refusals leave no artifact.
- **AC-017 concurrency:** two synchronized processes race before state exists; exactly one owns and
  only one can dispatch.
- **AC-018 fingerprint:** a test backend creates a commit that leaves status and diff clean; the
  changed `HEAD` invalidates approval.
- **AC-019 boundary:** a converged stub run performs no lifecycle dispatch and creates no closure or
  PR-description evidence.
- **Regression:** `check-consistency.sh` and existing installer suites remain green with no SDK or
  Codex CLI.
- **No 040 E2E/manual provider test:** former T018/T022 inputs move to the follow-up.

## Rollback strategy

The runner remains isolated under `runner/` with no installer or adopter dependency. Each safety
fix is independently revertible, but the scope correction itself is normative: reverting it would
restore unsupported provider and closure claims and requires a new decision. Runtime lock files
must have a documented stale-owner recovery path; rollback must never delete a lock owned by a live
process.

## PLAN verification checklist

- [x] Architecture option A is explicit and every audit finding has one owner.
- [x] SPEC acceptance changes are mapped to T028…T033.
- [x] The deterministic core and stub remain in 040; Claude stays lazy and Codex gated.
- [x] Real providers, writer scope, format retry, lifecycle and closure are excluded from 040.
- [x] Risks, tests, dependencies and rollback match the new boundary.
- [x] T028…T032 are implemented and verified (239 tests, green; each with its own negative check).
- [x] T033 revises the conformance verdict to PASS on the corrected scope; classification stays EXPERIMENTAL.
