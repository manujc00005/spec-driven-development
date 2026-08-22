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

### D006 - AC-003 is rewritten to test counter divergence, not the abort

**Date:** 2026-08-21

**Status:** Accepted

**Context:**

AC-003 as written required observing the per-finding abort fire: three REJECTs of one finding id.
Two independent fixture designs (T002 attempts 1 and 2) failed to produce it. Both failed the same
way: a competent reviewer that sees the same finding recur reasons about it and escalates rather
than re-litigating. Producing three re-reports of one id requires a reviewer that fails to notice
its own repetition, and this spec's methodology forbids simulating one - fixtures must use real
subagents, never mocked ones. The criterion was therefore unobservable by construction, not by bad
luck.

**Decision:**

AC-003 now requires observing the two counters **diverge** under a regression: the same finding id
re-reported after an intervening round resolved a different finding, so its per-finding total
increments while the no-progress streak resets to zero.

**Reasoning:**

The abort is arithmetic; the behaviour is the divergence. What the per-finding counter defends
against is a streak-only design, which would silently forgive a recurring defect because every
intervening approval resets the streak. Observing total=2 against streak=0 proves the two counters
are independent and that the per-finding one is monotonic across an approval. Whether it then fires
at 3 or 4 follows from the cap, and needs no separate evidence.

Crucially this is observable with competent reviewers, because a **regression** is not a
contradiction. A defect that was fixed and came back is re-reported with its original id as ordinary
review work - no escalation, which is exactly what blocked both earlier attempts.

**Consequences:**

The counter itself is unchanged; only the claim made about it is. It remains cheap insurance
against degraded agents, and this spec now asserts about it only what it can demonstrate. The
amended criterion is closeable by the same run that closes AC-004, since both need a fixture of
independent defects revealed one per round.

### D007 - DEFECT-001 is scoped as a follow-up, and this spec continues

**Date:** 2026-08-21

**Status:** Accepted

**Context:**

T012 round 3 found the first genuine protocol defect of this calibration: the per-finding REJECT
total counts every re-report of a finding, including re-reports of a finding the loop has never
dispatched a repair for. A converging run whose first review raises more findings than
`max-iterations` will abort spuriously, blaming a finding that was merely queued.

**Decision:**

Record it, scope the fix, and continue calibrating. Do not patch
`skills/sdd-orchestrate/SKILL.md` inside this run.

**Reasoning:**

The SPEC's non-goals forbid protocol redesign here and require a defect to become a scoped fix with
its own decision record. Its R1 stop rule triggers on **two or more** genuine defects; this is one.
Patching mid-run would also void the run that found it, since the fixture would then be exercising
a different protocol than the one under calibration.

**Consequences:**

AC-004 cannot close until the fix lands - not because the criterion is wrong, but because the
counter it would have exercised is known-broken, and evidence gathered against a broken counter
would assert nothing. AC-004 is re-run after the fix. If a second genuine defect appears before
then, R1 fires and this spec stops and re-plans rather than continuing to calibrate.

### D008 - The per-finding counter counts failed repairs, not re-reports

**Date:** 2026-08-21

**Status:** Accepted

**Context:**

DEFECT-001, found by T012 round 3. The per-finding REJECT total counted every `REJECT` carrying a
finding id, including re-reports of a finding the loop had never dispatched a repair for. Finding
`DOM-003` reached three rejects across three rounds while waiting its turn in the queue, exceeding
`max-iterations = 2`, in a run that was converging optimally.

**Decision:**

Count a per-finding `REJECT` only when the loop has already dispatched a repair attempt for that
finding. A finding re-reported while still unworked increments nothing. The pre-check in the durable
state contract is worded to match.

**Reasoning:**

The counter exists to catch a flip-flop, and **every flip-flop follows a repair** - a finding cannot
oscillate before anyone has touched it. So gating on failed repairs loses no detection while removing
the false positive entirely. Counting bare re-reports made the abort a function of how many problems
the first review found, which is workload, not stagnation - the precise error D017 corrected for
per-reviewer streaks. The defect was that the per-finding counter, added in the same change,
reintroduced it one level down.

The perverse consequence is worth naming: under the old rule a **better** reviewer aborted the run
sooner, because finding more real problems in one pass raised more ids that then accumulated
re-reports while queued.

**Consequences:**

`skills/sdd-orchestrate/SKILL.md` changes in two places - the counter definition and the pre-check
wording. No counter is removed and no cap value changes. AC-004 can now be re-run against a counter
that is not known-broken, which is T014.

### D009 - A spec whose work is driven outside /spec-implement has no owner for Ready → In Progress

**Date:** 2026-08-22

**Status:** Accepted

**Context:**

The lifecycle is `Draft → Ready → In Progress → In Review → Done`, and guardrails section 11 assigns
each transition to exactly one owning skill: `/spec-plan` sets `Ready`, `/spec-implement` sets
`In Progress`, `/spec-review` sets `In Review`, `/spec-close` sets `Done`.

This spec's work could not go through `/spec-implement`. D001 routes every calibration run to the
maintainer's orchestrator session precisely because the autonomous loop cannot credibly observe
itself. So `/spec-implement` never ran, the spec sat at `Ready` while eight criteria were closed by
execution, and the `Ready → In Progress` transition has no owner in this execution model.

**Decision:**

Record the gap as a framework finding and let `/spec-review` perform `Ready → In Review` for this
spec, with this decision as the written justification.

**Reasoning:**

The two alternatives are worse. Invoking `/spec-implement` to move a status when there is nothing
left to implement manufactures a transition that never happened - the exact unverified claim the
guardrail exists to prevent. Leaving the spec at `Ready` forever would make its lifecycle contradict
its own evidence, which is the failure mode this spec was written to eliminate from 031.

What the guardrail actually protects is that `In Review` is never claimed without verification. That
verification happened: `/spec-review` inspected the diff, confirmed the change is confined to the
two D008 edits the SPEC declared, and found the stale `ORCHESTRATION.md` that this review then
reconciled. The protection held; only the preceding transition's ownership is undefined.

**Consequences:**

A framework follow-up is warranted, outside this spec: either `/spec-review` is authorised to accept
`Ready` as an input state when a recorded decision explains why `/spec-implement` was bypassed, or
the lifecycle gains an owner for maintainer-driven execution. Until then, any spec that legitimately
executes outside `/spec-implement` will hit this same wall, and the workaround must be a recorded
decision rather than a silent status edit.
