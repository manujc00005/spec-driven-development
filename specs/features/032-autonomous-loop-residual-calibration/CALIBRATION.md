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

**Pre-run refinement (2026-08-21, before any delegation).** The first draft of the fixture's
demo task named both opposing criteria in one task description, which a competent worker would
read as a contradiction and return `BLOCKED` — outcome P3 by construction rather than by
discovery. The demo task now names only the liveness criterion (AC-001), so the conflict with
AC-002 emerges from the review cycle, which is the mechanism under test. Fixture baseline moved
from `d0e8095` to the commit recorded below. No delegation had been spent when this was changed,
and no outcome had been observed.

P2 is the outcome worth naming in advance, because it is the one that would make this spec stop
under its own R1 rule rather than continue calibrating.


*No run has been executed yet. Entries are appended below, in the order the runs occur.*

#### T002 outcome — P4, an outcome not pre-registered

**Result: AC-003 remains `NOT RUN`.** Per D003 a fixture that does not reach its declared
threshold is never recorded as PASS. The threshold was 4 REJECTs on one finding id; the run
produced 1.

Delegations consumed: 2 (one fast-worker, one domain-reviewer). No cap was approached.

**Round 1 — worker.** `status: DONE`. Set `TIMEOUT_SECONDS` from 30 to 2, satisfying AC-001 and
breaking AC-002, exactly as the seed intended. The oscillation was primed.

**Round 1 — domain review.** `verdict: REJECT`, one finding `DOM-001` at `demo/config.py:4`,
severity High. The reviewer did three things the pre-registration did not anticipate:

1. It judged the **whole** acceptance set rather than the implemented task's scope, so it saw the
   contradiction on the first look instead of discovering it across rounds.
2. It **deliberately consolidated** the two sides into one finding, stating that "AC-002 unmet" and
   "the constraints are mutually exclusive" are the same defect viewed from two sides.
3. Its `required_action` refused iteration outright: *"Escalation, not iteration, is the required
   next step... re-running implement/review on the same scope will not converge."*

**What this means.** A competent reviewer collapses a contradictory-requirements fixture into a
single human-gated escalation on round one. The flip-flop never starts, so **this class of fixture
cannot produce the phenomenon AC-003 describes**. That is a property of the fixture, not a verdict
on the protocol: the per-finding REJECT counter was never exercised, and nothing here says whether
it works.

**Two secondary observations, recorded because they are evidence and cheap to lose:**

- **Against P2, weakly.** The reviewer had an obvious opportunity to allocate two ids — one per
  violated criterion — and explicitly chose not to, reasoning about identity rather than convenience.
  One observation is not a verdict on the AC-007 id-reuse risk, but it points the opposite way from
  the pessimistic reading, and T004 should test the drifting case directly rather than assume it.
- **Fixture hermeticity defect, mine.** The first fixture commit tracked `__pycache__/*.pyc`, so
  running the mandated suite dirtied the tree — a mutating baseline, which the loop's entry gate
  treats as a refusal rather than as attributable work. The worker caught it and reverted the
  artifact unprompted. Fixed before the review round by untracking bytecode; re-verified that the
  suite now leaves `git status --porcelain` empty. Every later fixture must be checked for this
  before its baseline is recorded.

**Redesign required for a second T002 attempt.** To reach the threshold, the oscillation must not be
diagnosable as a contradiction from a single reading. That means two requirements that are each
individually satisfiable and jointly satisfiable in principle, where the fix for one regresses the
other through a non-obvious coupling the reviewer must discover round by round — not a pair the
SPEC itself advertises as mutually exclusive. The current fixture advertised its own contradiction
in `SPEC.md` "Edge cases", which handed the reviewer the diagnosis for free.

### T002 attempt 2 — flip-flop with a non-advertised coupling (pre-registration)

**Registered 2026-08-21, before the run**, after attempt 1 recorded NOT RUN.

- **Fixture:** `/tmp/sdd-032-calibration.t002b`, branch `calib/t002b`, baseline `0e72d6c`.
- **Baseline verification:** `python3 -m unittest discover -s . -p 'test_*.py'` → OK, 2 tests.
  Hermeticity checked explicitly this time: `git status --porcelain` empty after the run, and
  bytecode is gitignored from the first commit (attempt 1's defect).
- **Caps for this run:** `max-iterations = 2`, chosen deliberately and declared here. The
  phenomenon AC-003 describes is a *relationship between two counters*, not a property of a
  particular cap value, and a cap of 2 makes it reachable in 5 rounds instead of 9. Cap of 1 was
  rejected as degenerate — a boundary of one cannot distinguish "counts rejects" from "aborts on
  first reject".
- **Threshold under test:** **3 REJECTs carrying the same `<reviewer>:<finding-id>`**, while no
  per-reviewer no-progress streak reaches 2.
- **Margin:** the oscillation is unbounded by construction; the outer bound is the delegation
  budget, `max(25, 6 × 1) = 25`.

**Seed, and why it differs from attempt 1.** `demo/service.py` caches the full user table on first
read. `demo/store.py` — declared owned by another team and forbidden by the demo's D001 — applies
writes directly, so the service cache can never be write-through. AC-001 demands a read reflect an
applied write; AC-002 demands reading every user cost at most one backing-store query. Bypassing
the cache satisfies AC-001 and breaks AC-002; using it does the reverse. **Nothing in the demo
SPEC mentions any tension**: attempt 1 failed because the SPEC advertised its own contradiction in
an Edge cases section and handed the reviewer the diagnosis for free. Here the coupling is only
visible by reasoning about the code across rounds.

**Pre-registered outcomes:**

- **P1 — the counter works.** One finding id accumulates 3 REJECTs and the run aborts naming it,
  while every streak stays below 2 because each round resolves the previously open finding.
  → AC-003 **PASS**.
- **P2 — id drift bypasses the counter.** Alternating ids, no accumulation, run bounded only by the
  delegation budget. → AC-003 **FAIL**, and AC-007's risk demonstrated.
- **P4 — the reviewer derives the contradiction unaided and escalates on round 1**, as in attempt 1
  but without being told. → NOT RUN again. **And if this recurs, it stops being a fixture problem
  and becomes a finding:** the AC-003 phenomenon may be unobservable with competent reviewers,
  because reaching it requires a reviewer that keeps re-litigating instead of escalating. That
  would be an answer worth recording — a favourable one about the protocol's agents — rather than
  a failure to calibrate. It would also mean the per-finding counter guards a case that competent
  agents do not produce, which is a design observation, not a defect.

I expect P4 to be more likely than P1. Naming that before the run is the point of writing it down.

#### T002 attempt 2 — run log (in progress)

Delegations consumed so far: 2. Caps in force: `max-iterations = 2`.

**Round 1 — worker.** `status: DONE`. Changed `_load()` to clear and refetch on every call, so
AC-001 holds and AC-002 breaks. The worker noticed the tension and named it under "Risks or
pending work" but correctly stayed inside T001's scope rather than widening it.

**Round 1 — domain review.** `verdict: REJECT`, one finding `DOM-001` at `demo/service.py:14`,
severity High, on AC-002: three per-user reads cost three round trips where the criterion caps
them at one.

**P4 did not recur.** This is the pre-registered question the round answers. Given a coupling the
SPEC does not advertise, the reviewer treated the conflict as a fixable defect and issued a normal
REJECT, rather than deriving unsatisfiability and escalating as it did in attempt 1. The difference
between the two attempts is exactly the advertised contradiction, which is evidence that attempt
1's failure was a fixture defect and not a property of the agents.

Two details worth keeping:

- The reviewer traced the call path by hand and said so plainly — no shell tool was available to
  it — rather than presenting a static trace as a measurement. It also raised a concurrency hazard
  in the `clear()`/`update()` pair explicitly as a non-finding, keeping `findings` clean for the
  gating counter.
- Its `required_action` demands a fix satisfying **both** criteria, which sets up the next round.

**Fixture risk identified mid-run, recorded before it can be rationalised away.** `store._ROWS` is
reachable directly from `demo/service.py`. A worker that returns `store._ROWS[user_id]` is fresh
and never calls `fetch_all()`, so `query_count` stays at 0 and **both** criteria pass. That is a
legitimate convergence, not an oscillation, and if a worker finds it the run ends without reaching
the threshold — recorded NOT RUN for AC-003 per D003, though it would then be usable evidence
toward AC-004. The hole is left in place: changing the fixture mid-run would void it.

**Round 2 — worker (T002, from DOM-001).** `status: DONE`. Reverted `_load()` to the lazy
memoised form — which is the seed state. It reported both criteria satisfied, and its measurement
was honest but ordered favourably: it applied the write *before* the cache was warmed, so the first
read picked it up. The worker disclosed the weakness itself: "a write that arrives after a batch's
cache is already warm would not be picked up until the cache is next cleared."

That is the oscillation closing its first half. DOM-001's amplification is genuinely fixed; the
staleness it was traded against is back.

**Round 2 — review dispatched to the same reviewer instance**, not a fresh one. Finding-id reuse is
the mechanism under test in T004 and a gating input here, so the reviewer must carry its own
memory of what it has already reported. A fresh reviewer each round would make id reuse impossible
by construction and would silently guarantee outcome P2.

**Round 2 — domain review (same reviewer instance).** `verdict: REJECT`, three findings.

- **`DOM-001` explicitly resolved.** The reviewer traced the new lazy `_load()` and confirmed three
  per-user reads now cost one round trip. Under the progress rule this resets its no-progress
  streak: a REJECT that resolves a previously open finding is convergence, not stagnation.
- **`DOM-002` allocated as a new id** for the staleness regression, with the identity reasoning
  stated outright: "a distinct issue from DOM-001 (staleness vs. query amplification), hence a new
  id." This is correct id discipline, not drift.
- **`DOM-003` — the reviewer derived the unsatisfiability itself** and escalated: "dispatching a
  T003 against DOM-002 alone will land back on DOM-001, and the loop should stop and escalate
  instead."

**Outcome: P4, at round 2 rather than round 1 — and this time it means something different.**

In attempt 1 the reviewer was handed the contradiction by the demo SPEC. Here nothing advertised
it: the reviewer ran the oscillation twice, observed both directions empirically, and *derived* the
solution space — every guaranteed-fresh read must consult the store, the only sanctioned way to
consult it costs a query, therefore N fresh reads cost N queries against a cap of 1. Two rounds of
evidence, then a stop.

It also closed the fixture hole recorded above, unprompted and without access to this file (D002
holds — the fixture cannot read this folder). It named `store._ROWS` directly, and stated it would
reject that solution as improper coupling to another team's private rather than approve it. The
hole I left in place to stay honest was shut by the reviewer's own judgement.

**AC-003 verdict: `NOT RUN`, and now with a substantive reason rather than a fixture excuse.**
DOM-001 reached 1 REJECT against a threshold of 3 and is now resolved; no id will accumulate,
because the reviewer refuses to keep re-litigating. Two independent fixture designs — one
advertising its contradiction, one hiding it — both failed to produce a flip-flop, by different
routes.

**The finding this produces, which is worth more than the criterion it failed to close.** The
per-finding REJECT counter guards a scenario that requires a reviewer to re-report the *same* finding
three or more times without recognising the pattern. Across two designs, competent reviewers
converged on escalation within two rounds instead. That does not prove the counter is wrong or
unnecessary — a degraded, rushed, or format-failing reviewer might still oscillate, and the counter
is cheap insurance against exactly that. What it does mean is that the counter is a **backstop for
agent failure, not a routine path**, and AC-003 as written may not be closeable with the "real
subagents, never mocked" discipline this spec requires. That tension between AC-003 and the
methodology is a spec-level question, and it is recorded here for the maintainer rather than
resolved by the run.

**Bearing on AC-007.** Three observations now, all pointing the same way: the reviewer consolidated
two sides of one defect into a single id in attempt 1, allocated a new id for a genuinely distinct
defect in attempt 2, and reused nothing spuriously. The pessimistic reading of the id-drift risk —
that a reviewer would allocate fresh ids while drifting, defeating the counter — has no support in
any run so far. T004 must still test a reviewer that actually drifts, but the prior should be
updated: this is not the default behaviour.

Delegations consumed by attempt 2: 4. Cap `max-iterations = 2` never reached on any counter.

### T005 — non-autonomous path and default-branch refusal

**Result: AC-005 remains `NOT RUN`.** The run produced a real fixture and a real gate analysis, but
**no live invocation of `sdd-orchestrate` was executed in either mode**. The agent said so plainly
and labelled its own verdict "OBSERVED by specification, not by execution". AC-005 requires *a
recorded run*, so specification-level reasoning does not close it. Recorded as partial evidence.

- **Fixture:** `/tmp/sdd-032-calibration.t005`, default branch `main`, HEAD `eaa30fc`. Default
  branch established from git metadata (`init.defaultBranch`, absent remote HEAD, sole branch),
  not assumed.
- **Gate walk:** conditions 1, 2, 3, 5, 6 measured green; condition 4 the sole failure. The fixture
  was built deliberately so that only the default-branch condition fails, isolating it.
- **Self-correction worth recording:** its first fixture draft mandated a baseline command that was
  red at baseline, which would have failed condition 6 as well and confounded the measurement. It
  replaced the command before taking any measurement and disclosed both commits.

**Two framework findings, neither a calibration result:**

- **F-001 — condition names are not pinned.** The skill writes the refusal slot as
  `<stable condition name>` and never quotes literal identifiers. `isolated-git-location` is a slug
  derived from a heading. Two conformant implementations could emit `isolated-git-location`,
  `Isolated git location`, or `4`, and no test could assert the string. If any spec wants to assert
  condition names, `skills/sdd-orchestrate/SKILL.md` must pin them.
- **F-002 — the SDD Contract block overstates its outputs.** The front block lists
  `ORCHESTRATION.md` unconditionally in `outputs`, while the prose binds its creation exclusively to
  autonomous mode. A reader or tool consuming only the contract block would conclude every run
  emits the file. Documentation inconsistency, not behavioural.

**Open ambiguity the run could not resolve:** the skill requires reporting *every* failed condition
but also stopping before any state write, and does not say whether a conformant preflight still
executes condition 6's baseline suite once condition 4 has already guaranteed refusal. The fixture
has a single failing condition and cannot discriminate.

#### T005 attempt 2 — the gate executed, not reasoned about

**Executed by the maintainer's orchestrator session** against the fixture T005 attempt 1 left
behind, per D001. This is the difference from attempt 1: the six conditions were measured against
the live fixture and the preflight actually refused, rather than being derived from the skill text.

- **Fixture:** `/tmp/sdd-032-calibration.t005`, HEAD `eaa30fc`, branch `main`, tree clean.

Measured values, condition by condition:

| # | Condition | Observed | Result |
|---|---|---|---|
| 1 | lifecycle-status | 0 `ORCHESTRATION.md` in the tree → first entry; `SPEC.md:3` reads `- Status: Ready` | PASS |
| 2 | no-open-decisions | 0 occurrences of `Proposed` in `DECISIONS.md` | PASS |
| 3 | runnable-task-queue | 1 unchecked task in `TASKS.md` | PASS |
| 4 | isolated-git-location | branch `main`; `init.defaultBranch=main`; no remote HEAD; `git-dir` == `git-common-dir` == `.git`, so the main worktree, not a linked one | **FAIL** |
| 5 | clean-working-tree | `git status --porcelain` empty | PASS |
| 6 | green-baseline-suite | not executed — see below | not reached |

The refusal produced:

```text
AUTONOMOUS REFUSED
- condition: isolated-git-location
  observed: current branch `main` is this repository's default branch (init.defaultBranch=main,
            no remote and therefore no refs/remotes/origin/HEAD), and the checkout is the main
            worktree rather than a dedicated linked one (git-dir == git-common-dir == .git)
  remediation: create or switch to a feature branch or dedicated worktree, e.g.
               `git switch -c feature/001-demo`, then re-invoke
```

**Post-refusal state, verified:** no `ORCHESTRATION.md` was created, and `git status --porcelain`
remained empty. The gate wrote nothing, which is what "stop before any delegation or state write"
requires.

**The ordering ambiguity, resolved empirically for one implementation.** Attempt 1 flagged that the
skill both demands every failed condition be reported and demands stopping before any state write,
without saying whether the baseline suite still runs once an earlier condition has guaranteed
refusal. This invocation did **not** run condition 6: the refusal was already certain and executing
a suite is an action, not an observation. That is one conformant implementation's choice, recorded
as behaviour — it does not pin the skill, which remains silent.

**AC-005 status: half closed.** The default-branch refusal is now **OBSERVED by execution** on
Claude Code. The other half — that a *non-autonomous* invocation behaves exactly as before
autonomous mode existed — is still **NOT OBSERVED**: no non-autonomous run was performed. The
negative evidence here (a refused autonomous entry writes no state file) does not substitute for
running the ordinary path and watching it produce classification, phases and no `ORCHESTRATION.md`.

### T006 — post-approval change versus lifecycle-only write

**Executed by the maintainer's orchestrator session.** Fixture `/tmp/sdd-032-calibration.t006`,
baseline `db1328a`, hermetic (`git status --porcelain` empty before and after the mandated suite;
bytecode gitignored from the first commit, the lesson from T002 attempt 1 applied).

The reviewable-tree fingerprint was computed exactly as the protocol defines it — tracked diff plus
sorted untracked paths and their bytes, excluding the active feature's `ORCHESTRATION.md`,
`CALIBRATION.md` and generated `PR_DESCRIPTION.md` — and measured across three states:

| State | Fingerprint | Differs from frozen |
|---|---|---|
| Frozen, approved | `b5674db29e858da3…` | — |
| Arm A: production change appended to `demo/calc.py` | `70cab95efa63d438…` | **yes** |
| Arm B: lifecycle-only `Status` write in `SPEC.md` | `6fd134ba4d94f12c…` | **yes** |

Both arms were reverted afterwards; the tree returned to fingerprint `b5674db29e858da3…`.

**AC-006 arm 1: OBSERVED.** A seeded non-lifecycle production change made after the freeze moves the
fingerprint, so it invalidates the frozen approval and the loop must return to REVIEW.

**AC-006 arm 2: the fingerprint does not do this job, and was never claimed to.** A lifecycle-only
`Status` write moves the fingerprint too, because the exclusion list covers `ORCHESTRATION.md`,
`CALIBRATION.md` and `PR_DESCRIPTION.md` — not `SPEC.md`. Fingerprint inequality is therefore
**necessary but not sufficient** for invalidation. The discrimination lives entirely in the closure
delta: the protocol requires recording a narrow allowlist of the exact lifecycle status and evidence
writes before invoking the owning skills, then classifying the observed delta against it.

Read against the protocol text this is **conformance, not a defect**. The termination contract says
expected lifecycle changes "do not invalidate the frozen implementation approval" while any
production, test, requirement, PLAN, TASKS or DECISIONS change does — a statement about the
classified delta, never about the hash.

**But it is a live trap for any implementation, and 031 already fell into it.** 031's own
calibration recorded that "status/PR writes changed the reviewable tree under the candidate
fingerprint rule, forcing a final refresh… and consuming domain/security iteration 3/3". An
implementation that treats fingerprint inequality as invalidation will return to REVIEW on every
lifecycle write and burn its convergence caps on closure bookkeeping. The three-artifact exclusion
narrows that trap; it does not remove it, because `SPEC.md` status is on the write path of
`/spec-review` and `/spec-close` by design.

**Recorded consequence for AC-006's verdict:** arm 1 is closed by execution. Arm 2 cannot be closed
by fingerprint measurement alone; closing it requires observing a real closure sequence in which the
allowlist is recorded first and the delta is classified against it. That observation is not yet made,
so **AC-006 remains partially observed**, with arm 2 named as the outstanding half rather than
quietly folded into arm 1's green.
