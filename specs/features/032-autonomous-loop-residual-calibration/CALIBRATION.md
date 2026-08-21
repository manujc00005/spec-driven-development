# Calibration: autonomous-loop-residual-calibration

## Environment

- Worktree: `/Users/manu/Proyectos/sdd-032-calibration`
- Branch: `feat/032-calibration-runs`
- Baseline commit: `91cd906`
- Date: 2026-08-21

## Baseline verification

| Command | Result |
|---|---|
| `./scripts/check-consistency.sh` | PASS — exit code 0. "Consistency check passed: profiles.json, disk artifacts, settings wiring, and README counts are aligned." |

`git status --porcelain` was captured before and after the command and is identical in both cases
(hermetic — the command made no change to the working tree). One pre-existing untracked path,
`specs/features/032-autonomous-loop-residual-calibration/ORCHESTRATION.md`, was already present
before this verification ran and is unrelated to `check-consistency.sh`; it is not created or
touched by the baseline command.

Baseline verdict: **GREEN**.

## Fixture conventions

Every calibration run in this feature (T002–T008) must obey the following, shared rules, drawn
from PLAN "Proposed approach" and DECISIONS D002/D003:

- **Disposable worktree.** Each run uses a temporary `git worktree` at a path matching
  `/tmp/sdd-032-calibration.*`, deleted after the run completes.
- **Non-default branch.** The fixture worktree checks out a dedicated, non-default local branch,
  never `main`.
- **Hermetic green baseline.** Before any observed loop command, the fixture's own suite must run
  and exit 0, leaving `git status --porcelain` unchanged (empty in, empty out) — the same
  discipline this file's own Baseline verification just demonstrated.
- **Real subagents only.** Runs are driven with real subagents, never mocked or narrated ones; a
  scripted or narrated substitute cannot exercise the malformed-block and format-retry paths the
  protocol actually handles (PLAN, "Alternatives considered").
- **Sized against the threshold, not the story.** Each fixture must declare, before the run, which
  threshold it is built to exceed and by what margin, and must actually exceed it. A fixture that
  does not reach its declared threshold is recorded as NOT RUN, never as PASS (D003).
- **Blind to its own seeds.** The fixture must contain no path to
  `specs/features/032-autonomous-loop-residual-calibration/`. Seeds are reconstructed by hand into
  the fixture and are recorded in this file only after the run completes, never referenced from
  inside the fixture (D002).

## Acceptance-criteria evidence matrix

| Criterion | Behaviour under test | Closing task | Status | Evidence |
|---|---|---|---|---|
| AC-001 | Delegation-budget exhaustion aborts recoverably, naming the budget and count, and is distinct from a non-convergence abort | T007 | NOT RUN | — |
| AC-002 | Re-entry after a cap-exhaustion abort refuses an omitted, equal or lower cap and resumes only on an explicit increase, preserving counters and logging the cap change | T008 | NOT RUN | — |
| AC-003 | A finding alternating REJECT/APPROVE past `max-iterations` aborts on the per-finding counter while no per-reviewer streak reaches the cap | T002 | NOT RUN | — |
| AC-004 | A reviewer rejecting more than `max-iterations` times in a row while resolving a prior finding each round reaches a legitimate DONE | T003 | NOT RUN | — |
| AC-005 | A non-autonomous invocation behaves exactly as before, and the default-branch refusal fires on Claude Code | T005 | NOT RUN | — |
| AC-006 | A seeded post-approval production change invalidates final conformance and returns the loop to REVIEW, while lifecycle-only writes do not | T006 | NOT RUN | — |
| AC-007 | The id-reuse residual risk is assessed against a reviewer allocating a fresh finding id each round while drifting | T004 | NOT RUN | — |
| AC-008 | 031's evidence matrix is updated so no criterion it closed as PARTIAL remains PARTIAL without a reason that outlived this spec | T010 | NOT RUN | — |

## Calibration runs

### T002 — per-finding REJECT counter under a flip-flop (pre-registration)

**Registered 2026-08-21, before the run.** D003 requires the threshold and margin to be declared
in advance; this section is written first and is not edited afterwards. The outcome is appended
below it.

- **Fixture:** `/tmp/sdd-032-calibration.t002`, branch `calib/t002`, baseline `d0e8095`.
- **Baseline verification:** `python3 -m unittest discover -s . -p 'test_*.py'` → OK, 2 tests,
  `git status --porcelain` empty before and after.
- **Seed (recorded here because the fixture cannot read this folder, per D002):** `demo/config.py`
  exposes one `TIMEOUT_SECONDS` read by two consumers. The demo SPEC states AC-001 (health timeout
  ≤ 2) and AC-002 (bulk timeout ≥ 20) over that single constant, and the demo TASKS confine edits
  to `demo/config.py`, forbidding the structural fix of splitting it. No value satisfies both.
- **Threshold under test:** the per-finding REJECT total, cap `max-iterations = 3`. The run must
  produce **at least 4 REJECTs carrying the same `<reviewer>:<finding-id>`**.
- **Margin:** the oscillation is unbounded by construction — the constant can be flipped forever —
  so the fixture can exceed the cap by any margin. The outer bound is the delegation budget,
  `max(25, 6 × 1) = 25`.

**Pre-registered outcomes.** Exactly one of these is expected; each means something different:

- **P1 — the counter works.** The reviewer reuses one finding id for the recurring defect. Its
  per-finding total reaches 4, the run aborts naming that finding, and no per-reviewer no-progress
  streak ever reaches 3 (each REJECT resolves the other criterion, resetting the streak).
  → AC-003 **PASS**.
- **P2 — the counter is bypassed by id drift.** The reviewer allocates alternating ids (one for the
  health criterion, one for the bulk criterion). Neither id accumulates 4 rejects, and every streak
  resets because each round resolves the previously open finding. Nothing gates, and the run is
  bounded only by the delegation budget. → AC-003 **FAIL**, and direct evidence for the AC-007
  id-reuse residual risk, which would then be demonstrated rather than hypothetical.
- **P3 — the fixture does not reach its threshold.** The worker returns `BLOCKED` on the
  unsatisfiable criteria and the loop escalates before any oscillation occurs. → recorded
  **NOT RUN** per D003, never PASS; the fixture is redesigned.

P2 is the outcome worth naming in advance, because it is the one that would make this spec stop
under its own R1 rule rather than continue calibrating.


*No run has been executed yet. Entries are appended below, in the order the runs occur.*
