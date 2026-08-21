# Implementation Plan: autonomous-loop-residual-calibration

## Summary

Seven seeded calibration runs, one per behavior spec 031 shipped unexercised, plus a matrix
update that removes every PARTIAL it left behind. This plan produces **evidence, not code**: the
only expected diff is this feature's `CALIBRATION.md` and 031's evidence matrix. A run that finds a
genuine protocol defect stops and records it as a decision here; it never patches
`skills/sdd-orchestrate/SKILL.md` mid-run.

## Related spec

[SPEC.md](SPEC.md)

## Impacted areas

- `specs/features/032-autonomous-loop-residual-calibration/CALIBRATION.md` — created; the sole
  evidence artifact for all seven runs.
- `specs/features/031-autonomous-orchestration-loop/CALIBRATION.md` — the evidence matrix only
  (AC-008). No 031 run record is rewritten; history is appended, never edited.
- `skills/sdd-orchestrate/SKILL.md` — **only** if a run proves the protocol wrong, and then through
  a decision recorded here plus a scoped follow-up. Not expected.
- Disposable worktrees under `/tmp/sdd-032-calibration.*` — created and deleted per run, never
  committed.

## Context budget

### Reading list

- This feature folder in full.
- `specs/features/031-autonomous-orchestration-loop/CALIBRATION.md` — the evidence matrix and the
  run records this spec continues.
- `specs/features/031-autonomous-orchestration-loop/DECISIONS.md` — D013, D017 and D019 define the
  cap semantics and the deferred debt under calibration.
- `skills/sdd-orchestrate/SKILL.md` — the artifact under test.
- `adapters/codex/PARITY.md` — read-only; confirms which asymmetries stay out of scope.
- `scripts/check-consistency.sh` — read-only; the baseline command.

No whole-repo scans. Nothing under `evals/`, `docs/`, or other features.

### Model routing

- **Calibration runs (T002–T008): the maintainer's orchestrator session, not a delegated agent.**
  This mirrors 031's routing (its PLAN routed T008–T014 the same way, "the autonomous protocol is
  the artifact under test") and is recorded as D001 here.
- **Fixture scaffolding (T001): fast-worker.** Building a demo feature and a hermetic test suite is
  mechanical once the sizing rule is fixed.
- **deep-reasoner: only if a run fails.** A calibration run that contradicts the protocol is exactly
  the "evidence contradicts the SPEC" case; the analysis is worth an expensive model, the runs
  themselves are not.

## Proposed approach

Each run is an independent experiment with the discipline 031 established:

1. A disposable worktree on a non-default branch, from a recorded trusted baseline commit.
2. A hermetic green baseline whose suite leaves the tree exactly as it found it.
3. Real subagents — never narrated or mocked ones.
4. A seed that forces the *specific* threshold under test, and nothing else.
5. A `CALIBRATION.md` entry complete enough to reconstruct the run without the chat transcript.

Two sizing rules carry over from 031's mistakes, and they are the reason this plan is not a
formality:

- **Size the fixture against the threshold, not the story.** 031 learned that a three-step fixture
  cannot detect a cap defect: the run ends before the counter can misbehave. Every fixture here
  declares which threshold it must exceed and by how much.
- **The fixture must be blind to its own seeds.** One 031 run was contaminated because the fixture
  could read the spec documenting what it was seeded with. The demo feature therefore lives in the
  disposable worktree with no path to this folder.

Run order is riskiest-assumption-first rather than criterion order. The runs that could falsify
"the 031 protocol is correct as written" go first (per-finding counter, legitimate long
convergence, id-reuse), because a defect there invalidates the cheaper mechanical runs that follow.
The budget-exhaustion pair goes last: it is the most expensive by construction — exhausting the
floor budget costs 25 delegations — and the least likely to surprise.

## Alternatives considered

- **Delegate the runs to the autonomous loop itself.** Rejected: the loop would be instrument and
  subject at once, and a defective loop cannot be trusted to record its own abort. This is D001,
  and it matches 031's own routing rather than inventing a new rule.
- **One combined fixture exercising several criteria per run.** Rejected: the SPEC's edge case
  requires each record to state which counter fired first, and conflating a budget abort with a
  non-convergence abort is precisely the confusion D017 existed to fix.
- **Scripted or mocked reviewers.** Rejected: a mock cannot produce the malformed-block and
  format-retry paths the protocol handles, so it would certify a circuit nobody exercised.
- **Re-running the five Codex-only criteria on Claude Code.** Rejected — out of scope by the SPEC's
  non-goals and already documented in `PARITY.md` under D019.

## Dependencies

- Ordinary subagent quota; no provider beyond what 031 used.
- `git worktree` and `python3` for the demo suites.
- No external service, no real migration, no credential.

## Risks

- **R1 — A run finds a real defect.** Then the SPEC's own stop rule applies: one defect becomes a
  scoped fix with its own decision; **two or more mean the "protocol is correct" assumption is
  wrong and this spec stops and re-plans** instead of continuing to calibrate.
- **R2 — Circularity.** The skill driving each run is the skill under test. Mitigated but not
  eliminated by D001 (observed, not delegated) and D002 (fixture blind to its seeds). Any run whose
  verdict depends on the driving session's own judgement rather than on recorded artifacts must be
  marked as such rather than counted as evidence.
- **R3 — Cost.** AC-001 must exhaust a delegation budget whose floor is 25. This is expensive by
  design and cannot be shortened without changing the thing being measured.
- **R4 — The id-reuse hole may have no cheap mitigation.** AC-007 permits a recorded tolerance as a
  valid outcome. Accepting it is a legitimate result; silently not looking is not.

## Test strategy

- **E2E:** one seeded calibration run per acceptance criterion (T002–T008). The run *is* the test.
- **Integration:** `./scripts/check-consistency.sh` before the first run and after the last; it must
  exit 0 and leave the tree unchanged both times.
- **Regression:** 031's evidence matrix must not lose any criterion it already closed as PASS.
- **Manual:** none. 031's T023 covers the real-feature run and stays open there.

## Rollback strategy

Every artifact is additive documentation on a dedicated branch. Reverting is deleting the branch
and its worktrees; nothing is installed, migrated, or published. If a scoped protocol fix is
triggered by R1, it lands as its own change with its own decision record and is revertible
independently of this evidence.

## PLAN verification checklist

- [x] The plan covers all acceptance criteria (AC-001..AC-008).
- [x] The plan avoids behavior outside the spec.
- [x] The Context budget section is filled (reading list + model routing), not left as placeholder.
- [x] Risks are documented.
- [x] Test strategy is documented.
- [x] Rollback strategy is documented.
- [x] SPEC.md status has been updated to `Ready`.
