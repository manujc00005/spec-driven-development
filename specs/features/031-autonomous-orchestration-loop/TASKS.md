# Tasks: autonomous-orchestration-loop

## Phase 1: Preparation

- [x] T001 - Run the PLAN-mandated baseline suite (`bash scripts/check-consistency.sh` and
  `bash scripts/check-consistency.test.sh`) before changing contracts, and open
  `CALIBRATION.md` with the observed versions/results and the AC evidence matrix. Covers:
  AC-003, AC-007.

## Phase 2: Autonomous protocol

- [x] T002 - Extend `skills/sdd-orchestrate/SKILL.md`'s contract and invocation syntax with
  `--autonomous`, its two cap overrides, the six-condition entry gate, exact refusal/remediation
  output (including a green-but-mutating baseline), authenticated dirty-tree re-entry, and an
  explicit unchanged path for non-autonomous calls. Covers: AC-002, AC-007, AC-010.
  **[NEEDS REVIEW — D017]** the documented `max-delegations` default is now task-relative
  (`max(25, 6 × unchecked tasks at first entry)`), computed and recorded at first entry.
- [x] T003 - Define in `skills/sdd-orchestrate/SKILL.md` the canonical reviewer verdict and
  worker completion schemas, malformed-block fail-closed behavior, reviewer selection, and the
  stable finding-to-task conversion rule. Covers: AC-001, AC-003, AC-006.
- [x] T004 - Define in `skills/sdd-orchestrate/SKILL.md` the escalation classifier,
  deep-reasoner decision-recording path, canonical `ORCHESTRATION.md` scaffold/update order,
  recoverable attempt lifecycle, findings registry, all-stale fingerprint invalidation, monotonic
  cap re-entry, closure delta, DONE/PAUSED/ABORTED conditions, owning-skill status transitions, and
  no-commit/no-push invariants. Covers: AC-001, AC-004, AC-005, AC-006, AC-007, AC-008, AC-009,
  AC-010.
  **[NEEDS REVIEW — D017]** the cap model it implemented counts every reviewer invocation, which
  aborts any feature with more tasks than `max-iterations`. Rewrite to FR-009's two non-convergence
  counters (per-reviewer consecutive REJECTs reset by APPROVE; per-finding REJECT total), exempt
  clean re-approvals from both, keep the delegation budget as the sole monotonic global backstop,
  and record all three counters distinctly in the `ORCHESTRATION.md` scaffold. Covers also: AC-011.

## Phase 3: Agent and provider contracts

- [x] T005 - Update `security-reviewer`, `domain-reviewer`, and
  `final-conformance-reviewer` output contracts to require a final verdict block that references
  the canonical schema while preserving their existing human-readable report. Covers: AC-003.
- [x] T006 - Update `implementer` and `fast-worker` output contracts to require a final
  DONE/BLOCKED completion block that references the canonical schema and returns blocking
  decisions verbatim. Covers: AC-003, AC-004.
- [x] T007 - Document Codex's autonomous sequential degradation in
  `adapters/codex/PARITY.md`: same structured blocks, blackboard state, escalation classifier,
  caps, and safety rules, but no native fan-out or deterministic enforcement. Covers: AC-003,
  AC-005, AC-007.

## Phase 4: Calibration

- [x] T008 - In a disposable worktree and non-default branch, create a demo feature fixture plus a
  seeded reviewer-findable defect; the harness may make the one disposable baseline commit allowed
  by D012, but only commands/results remain in this feature's `CALIBRATION.md`, never the fixture or
  its branch. Covers: AC-001, AC-007.
- [x] T009 - Run the autonomous happy path through REJECT → traceable task → fix → APPROVE →
  all stale reviewers APPROVE the current fingerprint → final conformance → frozen implementation
  fingerprint → owning review/close skills → audited closure delta → PR description. Re-report one
  finding ID and prove it maps to one registry row/task. Covers: AC-001, AC-003, AC-008, AC-009,
  AC-010.
- [x] T010 - Violate each of the six entry conditions independently and record the exact refusal
  and remediation for each case; for baseline verification test both non-zero exit and exit 0 with
  a dirty-tree side effect. Covers: AC-002, AC-010.
- [x] T011 - Seed one technical reversible blocker and one product blocker with an independent
  task; verify autonomous decision recording, human pause, and continued independent work.
  Covers: AC-004.
- [ ] T012 - Interrupt after a worker file write but before its completion block, re-enter from the
  persisted attempt, and verify attributable work is recovered/validated without blind
  reimplementation; separately seed an out-of-scope dirty path and verify fail-closed handling.
  Confirm completed tasks are not repeated and every non-matching required APPROVE is invalidated.
  Covers: AC-005, AC-008.
- [x] T013 - Force repeated no-progress REJECT and malformed verdict output; verify the recoverable
  abort at the per-reviewer consecutive cap with a non-convergence report naming the reviewer and
  the finding. Done: abort fired before round 4 with both gating counters at 3/3, and the
  malformed-block re-request path was exercised for real. Covers: AC-006 (abort + malformed).
- [ ] T022 - Complete the remaining AC-006 evidence T013 did not cover: the delegation-budget abort,
  and re-entry refusing an unchanged or lower cap while resuming only with a higher one, preserving
  counters and logging the cap change. Covers: AC-006 (budget + cap re-entry).
- [x] T017 - Calibrate the cap semantics on a fixture with strictly more unchecked tasks than
  `max-iterations`: prove the long feature reaches DONE with zero cap-related aborts and that a
  fix-forced re-approval decrements only the delegation budget. Covers: AC-011(a), AC-011(b).
- [ ] T021 - Calibrate the two remaining cap behaviors AC-011 needs: a finding alternating
  REJECT/APPROVE past `max-iterations` must abort on the per-finding counter, and a reviewer
  rejecting past the cap while resolving a prior finding each round must keep going. Both need
  seeded reviewer behavior. Covers: AC-011(c), AC-011(d).
- [ ] T014 - Exercise a non-autonomous invocation, the default-branch refusal, and both provider
  paths; inspect command logs to confirm no commit/push or direct status transition occurred. Seed
  allowed lifecycle-only closure changes and one unexpected post-approval implementation change;
  verify only the latter invalidates final approval. Covers: AC-007, AC-010.

## Phase 5: User-facing documentation

- [x] T018 - Add an autonomous-mode section to `docs/SDD-ORCHESTRATION.md` next to the existing
  invocation examples: the `--autonomous` form and its cap overrides, the six entry conditions in
  plain language, what the loop decides alone versus what it escalates, what the two cap kinds mean
  after D017, and how to resume a `PAUSED` or recoverable-`ABORTED` run. Covers: AC-012.
- [x] T019 - Add the `CHANGELOG.md` entry for spec 031 following the format the recent feature
  entries use. Covers: AC-012.

## Phase 6: Verification and review

- [x] T015 - Run `bash scripts/check-consistency.sh` and
  `bash scripts/check-consistency.test.sh` after all contract edits; record actual exit codes and
  resolve only in-scope regressions. Covers: AC-003, AC-007.
- [ ] T016 - Perform final SPEC → PLAN → TASKS → diff → calibration-evidence conformance review,
  confirm AC-001..AC-013 all have evidence, and leave any unavailable real-feature manual run as
  an explicit blocker to `/spec-close` rather than claiming it passed. Covers: AC-001, AC-002,
  AC-003, AC-004, AC-005, AC-006, AC-007, AC-008, AC-009, AC-010, AC-011, AC-012, AC-013.
- [x] T020 - Run the Claude Code provider smoke on the autonomous loop and record it in
  `CALIBRATION.md`. Satisfied by the T017 run: a Claude Code orchestrator session drove real
  `fast-worker`, `domain-reviewer` and `security-reviewer` subagents through the entry gate,
  five tasks, a REJECT, a traceable finding task, a fix and re-approval. Covers: AC-013.
