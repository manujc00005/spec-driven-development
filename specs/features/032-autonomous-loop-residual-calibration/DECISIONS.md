# Decisions: autonomous-loop-residual-calibration

## Decision log

### D001 - Calibration runs are observed by the maintainer's session, never delegated to the autonomous loop

**Date:** 2026-08-21

**Status:** Accepted

**Context:**

This spec calibrates `sdd-orchestrate --autonomous`. The obvious efficiency is to close it *with*
the autonomous loop, which is what the maintainer initially asked for.

**Decision:**

Every calibration run (T002–T008) is driven from the maintainer's orchestrator session. The
autonomous loop is never the executor of a run that observes the autonomous loop.

**Reasoning:**

The loop would be instrument and subject simultaneously: if the protocol carries the defect
AC-001..AC-007 are designed to expose, the run responsible for detecting it is executed by the
defective thing. This is not a hypothetical — the whole reason these criteria are unexercised is
that 031 could not observe them from inside. 031 reached the same conclusion independently: its
PLAN routed the calibration tasks to the main session because "the autonomous protocol is the
artifact under test". Following that precedent is cheaper than re-litigating it.

**Consequences:**

The runs cost maintainer attention and cannot be parallelized by fan-out. In exchange, each verdict
rests on recorded artifacts rather than on the judgement of the component being judged.

### D002 - Fixtures are blind to the spec that documents their seeds

**Date:** 2026-08-21

**Status:** Accepted

**Context:**

031 recorded that one of its runs was contaminated because the fixture could read the spec
describing what it had been seeded with, so the agent "found" the planted defect by reading about
it rather than by reviewing code.

**Decision:**

Every fixture lives in a disposable worktree containing no path to
`specs/features/032-autonomous-loop-residual-calibration/`, and each run's `CALIBRATION.md` entry
records the seed only after the run completes.

**Consequences:**

Seeds must be reconstructed into the fixture by hand for each run rather than referenced. A run
whose fixture could reach this folder is void and must be repeated.

### D003 - Fixtures are sized against the threshold under test

**Date:** 2026-08-21

**Status:** Accepted

**Context:**

031 discovered that a three-step fixture cannot detect a cap defect: the run terminates before the
counter has the opportunity to misbehave, and the resulting green is meaningless.

**Decision:**

Every fixture declares, before the run, which threshold it must exceed and by what margin. A run
whose fixture did not reach its threshold is recorded as NOT RUN, never as PASS.

**Consequences:**

Runs are more expensive than the minimum that would "work" — most visibly T007, which must consume
the delegation floor of 25 to observe budget exhaustion at all.

### D004 - Run order follows risk, not criterion number

**Date:** 2026-08-21

**Status:** Accepted

**Context:**

The SPEC assumes the 031 protocol is correct and these runs confirm it, and it stops the spec if
two or more runs find genuine defects. That assumption is the expensive-to-reverse one.

**Decision:**

The runs that can falsify the assumption go first — per-finding counter (T002), legitimate long
convergence (T003), id-reuse drift (T004) — before the mechanical backstops (T005–T008).

**Reasoning:**

A defect in the cap model invalidates the cheaper runs that follow, so discovering it after
spending the delegation budget on them would waste the budget and the evidence.

**Consequences:**

AC-001 and AC-002, the two criteria the SPEC names first, are recorded last.

### D005 - OQ-1 is an output of T004, not an input to planning

**Date:** 2026-08-21

**Status:** Accepted

**Context:**

The SPEC leaves OQ-1 open: if the id-reuse risk needs a mitigation, does it belong in the reviewer
agent contracts or in the orchestrator's finding-registry logic? The SPEC marks it non-blocking and
answerable only after AC-007's run.

**Decision:**

OQ-1 blocks no task and is not resolved during planning. T004 produces its answer, or produces the
recorded tolerance that makes the question moot.

**Consequences:**

Planning proceeds with the question open by design. If T004 concludes a mitigation is required, its
location is decided then, with the run's evidence in hand, and scoped as a follow-up rather than
implemented inside this spec.
