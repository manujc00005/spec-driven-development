# Tasks: autonomous-loop-residual-calibration

Every task below produces **evidence**, not behavior. A task is done when its
`CALIBRATION.md` entry lets a reader reconstruct the run without this conversation:
environment, baseline, seed, observed counters, terminal result, and safety log.

Runs are ordered riskiest-assumption-first (PLAN, "Proposed approach"), not by criterion number.

## Phase 1: Preparation

- [x] T001 - Create `CALIBRATION.md` with the Environment, Baseline verification and
  Acceptance-criteria evidence matrix sections, mirroring 031's layout, and record the shared
  fixture conventions: disposable worktree path pattern, non-default branch, hermetic suite, and
  the two sizing rules (fixture exceeds the threshold under test; fixture cannot read this feature
  folder). Done when the matrix lists AC-001..AC-008 as NOT RUN with the task that will close each.
  Covers: AC-008.

## Phase 2: Implementation

- [x] T002 - (superseded by T012 per D006) Seeded run: a single finding alternating REJECT/APPROVE past `max-iterations` must
  abort on the per-finding REJECT total while no per-reviewer no-progress streak ever reaches the
  cap. Fixture must produce at least `max-iterations + 1` rejects of the same
  `<reviewer>:<finding-id>` with an approval between them. Done when the record shows both counter
  families with their values and names the finding that failed to converge.
  Covers: AC-003.

- [ ] T003 - Seeded run: a reviewer rejecting more than `max-iterations` times consecutively while
  resolving a previously open finding each round must reach a legitimate DONE. Fixture must run
  strictly more rounds than the cap. Done when the record shows the streak resetting on each
  progress-carrying REJECT and a terminal DONE, proving caps measure stagnation and not workload.
  Covers: AC-004.

- [x] T004 - Seeded run: a reviewer that allocates a fresh finding id every round while drifting to
  a new concern. Observe whether the progress rule reads the drift as progress and what ultimately
  bounds the run. Done when AC-007 has a written verdict — a recorded tolerance with its reasoning,
  or a specified mitigation — backed by this run's counters.
  Covers: AC-007.

- [x] T005 - Seeded run: a non-autonomous `sdd-orchestrate` invocation behaves exactly as before
  autonomous mode existed, and the default-branch refusal fires on Claude Code. Done when the
  record shows the refusal block verbatim and a non-autonomous run producing no
  `ORCHESTRATION.md`.
  Covers: AC-005.

- [x] T006 - Seeded run: a non-lifecycle production change made after the implementation freeze
  invalidates final conformance and returns the loop to REVIEW, while lifecycle-only writes do not.
  Done when the record shows both arms — the seeded production edit invalidating the frozen
  fingerprint, and a lifecycle-only write leaving it intact.
  Covers: AC-006.

- [x] T007 - Seeded run: exhaust the delegation budget and observe a recoverable abort naming the
  budget and the count. Fixture sized so the floor budget of 25 is reached; the record must be
  unambiguously distinguishable from a non-convergence abort and state which fired first.
  Covers: AC-001.

- [x] T008 - Re-entry after T007's budget abort: refuse an omitted cap, refuse an equal cap, refuse
  a lower cap, and resume only on an explicit increase. Done when the record shows all four
  outcomes, every counter preserved across re-entry, and the cap change appended before any work.
  Depends on T007 having produced a resumable abort.
  Covers: AC-002.

## Phase 3: Tests

- [x] T009 - Run `./scripts/check-consistency.sh`; it must exit 0 and leave `git status --porcelain`
  exactly as it found it. Confirm 031's evidence matrix lost no criterion it had already closed as
  PASS. Covers: AC-008.

## Phase 4: Review

- [x] T010 - Update 031's evidence matrix so no criterion it closed as PARTIAL remains PARTIAL
  without a reason that outlived this spec, citing each 032 run that closed it. Append; never
  rewrite a 031 run record. Covers: AC-008.

- [ ] T011 - Run `/spec-review` and `/qa-review` on this feature, then `/spec-close`. If any run in
  Phase 2 found a genuine defect, this task stops and routes it to a scoped follow-up instead of
  closing. Covers: AC-001, AC-002, AC-003, AC-004, AC-005, AC-006, AC-007, AC-008.

## Phase 5: Amended criteria (D006)

- [x] T012 - Single seeded run closing both AC-003 (as amended) and AC-004: a fixture of independent
  defects revealed one per round, where one previously-resolved defect regresses mid-run. Done when
  the record shows more than `max-iterations` consecutive progress-carrying REJECTs reaching a
  legitimate DONE, and, at the regression round, one finding id's per-finding total incrementing
  while its reviewer's no-progress streak resets to zero. Covers: AC-003, AC-004.

- [ ] T013 - (from DEFECT-001, per D007) Fix the per-finding REJECT counter so it increments only
  when a finding is re-reported after a dispatched repair attempt for that finding, leaving it
  untouched while the finding sits unworked in the queue. Own decision record required. Covers: AC-003.
- [ ] T014 - Re-run AC-004 after T013 lands. Covers: AC-004.
