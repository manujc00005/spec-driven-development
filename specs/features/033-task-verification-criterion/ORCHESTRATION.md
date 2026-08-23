# Orchestration: task-verification-criterion

- Feature: `specs/features/033-task-verification-criterion`
- Mode: `autonomous`
- Started at: `2026-08-22T13:42:00Z` (entry gate passed; see the table below)
- Updated at: `2026-08-22T14:05:08Z`
- Effective max iterations: `3`
- Effective max delegations: `42` (`max(25, 6 × 7 unchecked tasks at first entry)`)
- Purpose: this run is spec 031's T023 — the only calibration evidence drawn from a real,
  non-seeded feature rather than from a fixture designed by the agent that reviews it.

> **Rebuilt 2026-08-22T14:05:08Z after final conformance raised CONF-002.** The first version of this file was
> written at entry and never updated again: it froze at `T001 / PLANNED / 0 delegations` with empty
> tables, while the tree showed eight tasks closed. A state file the contract calls authoritative,
> left describing a run that had moved on, is a worse defect than the gap it hid. Rebuilt from the
> delegation history rather than deleted.

## State

- Phase: `REVIEW`
- Current task: `T009`
- Current attempt: `A-016`
- Current attempt state: `VERIFIED`
- Delegations used: `15`
- Current task verification: `T007 - criterion "check-consistency.sh exits 0 and git status --porcelain byte-identical before and after". Result: MET (exit 0; hashes equal). This is the non-circular observation CONF-008 required. The earlier T009 closure satisfied AC-004's letter only and is retained below for the record.`
- Attributed dirty paths: `specs/_templates/`, `skills/{spec-plan,spec-analyze,sdd-orchestrate}/SKILL.md`, `adapters/codex/prompts/`, and this feature folder
- Baseline verification: `./scripts/check-consistency.sh → exit 0; tree byte-identical before and after`
- No-progress streaks (gating): `domain=0, final-conformance=1`
- Total invocations (audit only): `domain=3, final-conformance=1`
- Approvals: `domain=APPROVE on the six-surface diff`
- Frozen implementation fingerprint: `pending final-conformance re-approval`

## Entry gate

Restored after CONF-009: the CONF-002 rebuild dropped this table, and for spec 031's T023 it is the
proof the run started legitimately.

| Condition | Observed at entry | Result |
|---|---|---|
| lifecycle-status | `SPEC.md` Status = `Ready`; no prior `ORCHESTRATION.md` -> first entry | PASS |
| no-open-decisions | D001, D002 both Accepted; 0 Proposed | PASS |
| runnable-task-queue | 7 unchecked tasks; T001 had no unchecked prerequisite | PASS |
| isolated-git-location | branch `feat/033-task-verification-criterion`; default `main`; dedicated linked worktree at `/Users/manu/Proyectos/sdd-t023` | PASS **at entry** - see the provenance note below |
| clean-working-tree | `git status --porcelain` empty | PASS |
| green-baseline-suite | `./scripts/check-consistency.sh` exit 0; tree byte-identical after | PASS |

### Provenance note (CONF-014)

The worktree this run executed in, `/Users/manu/Proyectos/sdd-t023`, **was removed before the third
conformance round could read it**, and its branch no longer exists. The third gate refused to
certify anything as a result, and was right to: the loop's contract treats ambiguous provenance as a
fail-closed abort, not as something to reason past.

Reconstructed sequence, from what is verifiable rather than from memory:

- The run's own commits (`4f3542d`, `4f7e606`, `40d4ffb`, `7fbfc18`, `687a6f1`) still exist as
  objects but are reachable from no branch.
- The maintainer merged the branch. `main` at `bff425d` carries the feature, and its
  `specs/_templates/TASKS.md` is **ahead of** the run's last commit rather than behind it.
- The second conformance round's fixes (CONF-008 through CONF-012) were **not** in what merged. They
  were recovered from the orphaned commit and cherry-picked onto `review/033-conformance`, which is
  the tree the third gate reads.

**What this costs.** The entry gate's isolation condition passed when the run started and is no
longer demonstrable from the filesystem. This record does not claim otherwise. For spec 031's T023,
that matters: T023 asks for evidence from a real, non-seeded feature, and the *content* of this run
is intact and re-readable, but the *provenance chain* has a documented break in the middle. Whether
that break disqualifies the run as T023 evidence is a maintainer's call, and it should be made
explicitly rather than absorbed by re-running the gate until something passes.

## Attempts

| ID | Agent | Task | State | Outcome |
|---|---|---|---|---|
| A-001 | fast-worker | T001 template clause | VERIFIED | DONE |
| A-002 | domain-reviewer | review T001 | VERIFIED | REJECT, DOM-001 |
| A-003 | fast-worker | T008 (from DOM-001) | VERIFIED | DONE |
| A-004 | domain-reviewer | re-review | VERIFIED | REJECT, DOM-001 resolved, DOM-002 raised |
| A-005 | fast-worker | T002 spec-plan | VERIFIED | DONE |
| A-006 | fast-worker | T003 spec-analyze | VERIFIED | DONE |
| A-007 | fast-worker | T004 sdd-orchestrate | VERIFIED | DONE |
| A-008 | fast-worker | T005 parity mirror | VERIFIED | DONE |
| A-009 | domain-reviewer | full six-surface diff | VERIFIED | REJECT, DOM-003..DOM-006 |
| A-010 | fast-worker | DOM-003 + DOM-004 | VERIFIED | DONE |
| A-011 | fast-worker | DOM-005 + DOM-006 | VERIFIED | DONE |
| A-012 | fast-worker | Codex prompt gaps | VERIFIED | DONE |
| A-013 | domain-reviewer | re-review full diff | VERIFIED | APPROVE, findings: [] |
| A-014 | final-conformance-reviewer | full evidence chain | VERIFIED | REJECT, CONF-001..CONF-006 |
| A-016 | orchestrator | T007, re-closed on its own clause | VERIFIED | criterion: `check-consistency.sh` exits 0 **and** `git status --porcelain` byte-identical before and after. Checked: exit 0, hashes equal. **MET.** Non-circular - the criterion targets tooling the checker does not author. |
| A-015 | orchestrator | T009, closed on its criterion | VERIFIED | criterion checked mechanically: the field exists, names the criterion and its result, and no field in this file is left as a placeholder. Task closed **because the criterion was met**, not because a worker said DONE. |

## Findings

| Reviewer:finding | Task | Severity | Status | Resolving verdict |
|---|---|---|---|---|
| domain:DOM-001 | T008 | Medium | resolved | A-004 APPROVE of the finding |
| domain:DOM-002 | D002 revision | Medium | resolved | A-013 APPROVE |
| domain:DOM-003 | fix round | High | resolved | A-013 APPROVE |
| domain:DOM-004 | fix round | Medium | resolved | A-013 APPROVE |
| domain:DOM-005 | fix round | Medium | resolved | A-013 APPROVE |
| domain:DOM-006 | fix round | Low | resolved | A-013 APPROVE |
| final-conformance:CONF-001 | T009 + clauses | blocker | addressed | pending re-review |
| final-conformance:CONF-002 | this file | blocker | addressed | pending re-review |
| final-conformance:CONF-003 | 031 CALIBRATION | blocker | addressed | pending re-review |
| final-conformance:CONF-004 | 033 TASKS clauses | blocker | addressed | pending re-review |
| final-conformance:CONF-005 | T009 | major | addressed | pending re-review |
| final-conformance:CONF-006 | spec-analyze:86 | minor | addressed | pending re-review |

## Delegation log

Reconstructed from the attempt history. Per-call timestamps and fingerprints were never captured -
the state file was abandoned after the first dispatch, which is the defect CONF-002 named - so they
are recorded as absent rather than back-filled. A fabricated fingerprint is worse than a missing one.

| Agent | Objective | Outcome |
|---|---|---|
| fast-worker x 8 | T001-T005, T008, and the three finding-fix rounds | all DONE |
| domain-reviewer x 3 | T001, the six-surface diff, and its re-review | REJECT, REJECT, APPROVE |
| final-conformance x 2 | full evidence chain, twice | REJECT, REJECT |

**Not reconstructible:** per-attempt `Timestamp`, `Allowed paths`, `Pre fingerprint`, `Post fingerprint`.

## Escalations

None. No worker returned BLOCKED at any point in this run.

## Run result

- Status: `ACTIVE`
- Resumable: `yes`
- Reason: `Final conformance rejected twice. Round two (CONF-007..CONF-012) found T001 missing its own clause, the AC-004 observation partly circular, and this file's own rebuild had deleted the entry gate. All addressed; awaiting the third gate. Status stays ACTIVE until it rules - claiming otherwise is exactly the CONF-010 error.`
