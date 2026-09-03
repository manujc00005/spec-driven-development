---
name: sdd-orchestrate
description: Orchestrate large or risky SDD work across deep-reasoner and fast-worker, or run an approved feature through the autonomous implement-review-fix loop. Use for delegated implementation, analysis, audits, and resumable autonomous closure. For small single-session work, use /sdd.
---

## SDD Contract

```yaml
category: orchestration
inputs: [free-form-goal, autonomous-feature-path]
outputs: [task-classification, delegated-work, synced-SPEC-PLAN-TASKS-DECISIONS, ORCHESTRATION.md]
side_effects: writes-code
writes_code: true
writes_specs: true
analysis_only: false
primary_agent: orchestration-context
secondary_agents: []
profile_scope: all
provider_specific: true
```

You are the orchestrator of a multi-model Spec-Driven Development workflow. Your job is
coordination, decomposition, review, and synthesis — not extensive mechanical work. You
keep the main context focused on requirements, decisions, and validation, and you push
heavy reading and heavy editing into subagents.

ARGUMENTS: either a free-form description of the goal, or:

```text
--autonomous specs/features/<nnn>-<name> [--adopt] [--max-iterations N] [--max-delegations N]
```

`--adopt` (spec 041) is a first-entry-only modifier of `--autonomous` for a feature that is already
`In Progress` because the maintainer started it by hand. It is rejected outside `--autonomous` and
when duplicated, with the other syntactic flag errors, before any feature-state read or write. Once
feature state is read, it is refused as *Already adopted or entered* when a valid `ORCHESTRATION.md`
for the feature already exists — an existing run is resumed, never re-adopted, so the flag is never
passed on re-entry — and as *Adoption not needed* when `SPEC.md` is `Ready`. What it changes is
confined to the entry gate and to state initialization below; the loop after entry is identical.

Both overrides must be positive integers. Defaults: `max-iterations=3`, applied to the two
non-convergence counters defined below, and `max-delegations` computed once at first entry as
`max(25, 6 × unchecked tasks in TASKS.md)` — the budget must absorb a whole feature's re-approvals,
so it scales with the queue rather than being a flat number. Record the computed value and its
inputs in `ORCHESTRATION.md`. Reject unknown flags, missing paths, duplicate overrides,
and non-positive/non-integer values before reading or writing feature state. On first entry the
chosen values become the effective caps. On authenticated re-entry, omitted overrides preserve
them; explicit overrides may only increase them. Refuse a decrease, never reset counters, and log
every accepted cap increase with its old/new value and reason before resuming (D013).

## Intent detection (before anything else)

`--autonomous` is an explicit mode, not a free-form intent. Parse it first and follow the autonomous
protocol below. All invocations without that flag continue through the existing intent detection,
classification, phases, and output unchanged.

Classify what the user is asking FOR, not just what it touches:

- **Analyze / Audit / Investigate / Review / Design** (in any language) → produce analysis
  or a report. Do NOT implement, even if fixes look obvious. Offer the follow-up spec instead.
- **Specify** → stop after SPEC. **Plan** → stop after PLAN/TASKS.
- **Implement / Fix** → run the full flow below.

## Autonomous mode — where the protocol is defined

**The executable contract is the source of truth: `runner/sdd_runner/` (spec 042).** This section
and the ones below are its human-readable projection — the same rules, written for the person or
model that has to follow them. Where this prose and the core disagree, **this prose is wrong**, and
the fix is a `/spec-update` against spec 031 that changes both.

That inverts spec 040 D007, which said the opposite. D007 was correct while this skill was the only
complete definition and the runner transcribed part of it. It stopped being correct once contract
tests began checking every normative value stated here against `sdd_runner.policy`: a cap, status,
severity, trigger or exit code edited here and not there now turns the suite red instead of drifting
quietly. Keep editing this file — it is what a reviewer and a model actually read — and expect the
suite to hold you to the core.

## Autonomous mode — entry gate

Run these checks in order and stop before any delegation or state write if one fails. Report every
failed condition found in the preflight, not merely the first. Each refusal uses:

```text
AUTONOMOUS REFUSED
- condition: <stable condition name>
  observed: <specific evidence>
  remediation: <exact command or action>
```

The six conditions and remediations are (a seventh applies under `--adopt`):

1. **Lifecycle status.** On first entry (no valid `ORCHESTRATION.md` for this feature), `SPEC.md`
   must be exactly `Ready`; otherwise run `/spec-plan <feature-path>`. On authenticated re-entry,
   `In Progress` or `In Review` is allowed only when the state file names the same feature and its
   result is `ACTIVE`, `PAUSED`, or `ABORTED` with `resumable: yes`; a mismatched, non-resumable,
   `Draft`, `Done`, or `Archived` run refuses and names the owning lifecycle action. This
   distinction is D010/D013; it is not permission to edit status.
   Under `--adopt` (spec 041), first entry requires exactly `In Progress`, and every other status
   refuses naming the owning action: `Ready` → *Adoption not needed*, remediation "run without
   `--adopt`"; `Draft` → `/spec-plan <feature-path>`; `In Review` → `/qa-review <feature-path>`
   then `/spec-close <feature-path>` (QA and closure have owning skills; adoption never runs them
   for a feature that already passed `/spec-review`); `Done`/`Archived` → nothing to run. A valid
   `ORCHESTRATION.md` for the feature together with `--adopt` refuses as *Already adopted or
   entered*, remediation "re-enter without `--adopt`"; a stale state file from another feature or a
   non-resumable run is preserved under a timestamped name by the maintainer, as the recovery rule
   below already requires, before adopting.
2. **No open decisions.** `DECISIONS.md` must contain no unresolved/open question or Proposed
   decision that blocks an unchecked task. Remediation: resolve it with `/spec-clarify
   <feature-path>` (first entry) or record the maintainer's answer in `DECISIONS.md` (re-entry).
3. **Runnable task queue.** `TASKS.md` must exist and contain at least one unchecked task or a
   terminal-ready queue; no unchecked blocking prerequisite may precede runnable work.
   Remediation: `/spec-plan <feature-path>` for a missing queue, otherwise resolve the named
   prerequisite in `TASKS.md`/`DECISIONS.md`.
4. **Isolated git location.** The current branch must not be the repository's default branch, or
   the current worktree must be a dedicated linked worktree on a non-default branch. Determine the
   default branch from git metadata; never assume its name. A **detached HEAD** refuses under this
   condition too: it is not an isolated location, it is no location at all, and a commit made there
   is referenced by nothing — which matters most under `--adopt`, where the maintainer's commit is
   both the adoption baseline and the attribution. Remediation: create/switch to a feature branch or
   worktree, e.g. `git switch -c feature/<name>`.
5. **Clean working tree.** `git status --porcelain` must be empty at first entry. On re-entry, only
   paths attributable to the recorded autonomous run may be dirty; any pre-existing/unattributed
   path refuses. Remediation: inspect `git status --short`, then commit/stash/discard manually—the
   orchestrator never does so.
   Under `--adopt` there is no attributable path at all: no run exists yet to attribute anything
   to, so `git status --porcelain` must be empty, and the remediation is the exact commit on the
   feature branch — `git add -A && git commit -m "<pre-adoption work>"` — whose result becomes the
   adoption baseline (D004). `git stash` is acceptable only when the maintainer wants that work
   *excluded* from the feature. The orchestrator never commits or stashes on the maintainer's
   behalf. When conditions 4 and 5 fail together, report them in that order — branch first, tree
   second — so the remediation the maintainer follows lands the commit on the feature branch
   (`git switch -c feature/<name>` carries uncommitted work with it).
6. **Green baseline suite.** Run exactly the verification commands mandated by `PLAN.md` before
   the first implementation delegation. Every command must exit 0 and the complete suite must leave
   the same clean tree it received. Record commands, results, and before/after status in
   `ORCHESTRATION.md` when state is initialized. A zero exit that creates or modifies a path is a
   mutating-baseline refusal, not attributable work. Remediation: make the suite hermetic, clean the
   named generated paths manually, or update the PLAN through `/spec-update`; never attribute
   baseline red or baseline dirt to this run.
7. **Inherited record is computable** (`--adopt` only). The orchestrator must determine the
   adoption baseline commit (`HEAD`), the adoption diff base (`git merge-base <default-branch>
   HEAD`, with the default branch resolved from git metadata such as `origin/HEAD` — never
   assumed), and the set of tasks already checked in `TASKS.md`. If the diff base cannot be
   determined (no default-branch metadata, unrelated histories), refuse as
   *Inherited diff undetermined*; remediation: set the metadata, e.g. `git remote set-head origin
   <branch>`, and re-run. There is no `--base <ref>` flag: provenance comes from git, not from
   arguments (D003).

If every applicable condition passes, initialize or validate `ORCHESTRATION.md` using the canonical
state contract below, then enter the autonomous loop. Permission modes and worktree creation remain caller concerns; the
skill never weakens permissions or mutates git history to make the gate pass.

## Autonomous mode — canonical structured output

These schemas are normative. Delegation briefs must require the relevant block as
the final content in the agent response. Human-readable prose remains above it; control flow reads
only the final fenced YAML block and never infers success from prose.

### Reviewer verdict block

`security-reviewer`, `domain-reviewer`, and `final-conformance-reviewer` must end every autonomous
report with exactly this shape:

```yaml
verdict: APPROVE # APPROVE | REJECT
findings: []
```

For `REJECT`, `findings` must be non-empty and every item must contain all fields:

```yaml
verdict: REJECT
findings:
  - id: SEC-001
    severity: High # Critical | High | Medium | Low
    evidence: path/to/file.ext:42
    summary: One-line description of the confirmed problem
    required_action: Concrete condition that must be satisfied on re-review
```

Finding IDs are stable within a run and use the reviewer namespace (`SEC-`, `DOM-`, `CONF-`). A
reviewer re-reporting the same unresolved issue reuses its ID; a genuinely distinct issue gets the
next ID. Identity is `<reviewer>:<finding-id>` and maps to exactly one row in the durable Findings
registry and exactly one repair task. Re-reporting updates `last seen`, action, and status; it never
allocates another task. `APPROVE` requires `findings: []`; an approval carrying findings is malformed.

**`severity` is a closed enum: `Critical | High | Medium | Low`.** Nothing else is valid *inside*
the verdict block. Review-report vocabulary — `blocker`, `major`, `minor`, `nit`, `P0`, and the
like — is fine in the prose above the block, in a rendered report, in a summary, and in the
Findings-registry rows a human reads; it is **not** fine inside the block a machine parses. A block
carrying one of those values is malformed and takes the malformed-block path below: one format
re-request, then a fail-closed synthetic `REJECT`.

There are no aliases and no implicit normalization. A parser must not map `blocker` to `Critical`
or `minor` to `Low`, because a silent translation makes the gate's own vocabulary unfalsifiable —
nobody can then tell whether a reviewer used the schema or was quietly corrected into it. Reviewers
that think in report language must translate explicitly, in their own output, before emitting the
block.

This rule exists because it was broken. `specs/features/033-task-verification-criterion/ORCHESTRATION.md`
records `blocker`, `major` and `minor` against `final-conformance:CONF-*` rows — the one reviewer
whose agent contract never named the vocabulary (fixed 2026-08-31; see spec 040 D011).

### Worker completion block

`implementer` and `fast-worker` must end every autonomous report with exactly one of:

```yaml
status: DONE
decisions: []
```

```yaml
status: BLOCKED
decisions:
  - The exact undocumented question, copied verbatim
```

`DONE` with decisions or `BLOCKED` without a non-empty decisions list is malformed. Validation
evidence stays in the worker's prose report and is copied into the delegation log.

### Malformed or missing blocks

Validate enum values, required keys, list cardinality, finding IDs, severity, and evidence
locators. An evidence locator is `path:line`, and one finding may legitimately span several
locations — accept `path:line,line`, `path:line-line`, and a list of locators, since a real defect
often lives in a definition and its use site. Rejecting a well-formed multi-location finding as
malformed would burn a retry on a correct review; require a path and at least one line, not exactly
one line. On the first malformed/missing block, re-request once from the same agent with the schema
and the validation error; this counts as a delegation but not a review iteration. If the second
response is still invalid, synthesize a fail-closed reviewer result (never APPROVE):

```yaml
verdict: REJECT
findings:
  - id: ORCH-MALFORMED-<reviewer>-<iteration>
    severity: High
    evidence: agent-output:verdict-block
    summary: Reviewer returned an invalid autonomous verdict twice
    required_action: Return a block conforming to the canonical sdd-orchestrate schema
```

For a worker, two invalid completion blocks become `BLOCKED` with the exact validation errors and
follow the escalation classifier. A synthetic reviewer REJECT closes no finding, so it always
increments that reviewer's no-progress counter and cannot bypass the convergence caps below.

## Autonomous mode — implement/review/fix circuit

Process one unchecked runnable task at a time. Batch only when the existing Parallelism rule proves
the tasks share no files, contracts, state, migrations, or conflict-prone tests. Treat every agent
call as a durable attempt (D014). Before every delegation, allocate `A-NNN`, persist its objective,
task/batch, agent, allowed-path scope, pre-delegation fingerprint, and lifecycle `PLANNED` only
after proving `Delegations used + 1 <= effective max delegations`; then increment the counter and
persist `DISPATCHED` immediately before the call. The budget counts
workers, reviewers, deep-reasoner calls, and structured-output retries. Local commands and
same-context owning-skill calls are logged but do not consume it.

0. *(adopted runs only, spec 041 D005)* Before the first implementation delegation, compute the
   fingerprint and review the inherited diff — `<adoption diff base>..<adoption baseline commit>`
   — with `domain-reviewer`, plus `security-reviewer` when that diff or the SPEC matches the
   Level-3 triggers of step 3. Each is a counted delegation with its own attempt. Parse and persist
   their verdicts exactly as in step 4: findings enter the registry and become
   `(from <finding-id>)` tasks. While an inherited-diff finding of severity `Critical` is open,
   delegate no new spec task — only its finding task; lower severities interleave under the normal
   rule. An empty inherited diff skips this step and the run then behaves as a `Ready` entry. An
   APPROVE here is an approval for that fingerprint and is invalidated by later changes like any
   other. Checked tasks are never re-implemented: the reviewers judge their diff, and the
   `Inherited` table records that this run did not observe their `Verify:` clauses.
1. Delegate the task using the normal full brief and require the completion block.
2. On response, persist `RESPONDED`, the raw outcome reference, and post-delegation fingerprint
   before acting. On `BLOCKED`, follow the escalation protocol below. On `DONE`, verify the claim
   rather than trusting the word DONE: the detection unit is the task item — the bullet beginning
   `- [ ]` or `- [x]` together with its continuation lines, up to the next bullet — and within it the
   clause is the one following `Covers:`. When the task item carries a `Verify:` clause, check the
   claimed completion against that criterion — the task's stop condition — instead of the worker's
   own judgement of doneness. "Checking" never means the loop executing the clause itself (FR-010);
   it means evaluating the claimed completion against it. Record the criterion and the result of
   checking it in both the attempt row and the state block. When the task item carries no `Verify:`
   clause, verify the claimed task checkbox and command evidence as before. Either way, persist
   `VERIFIED`.
3. Compute the reviewed-diff fingerprint, then run `domain-reviewer` for every implemented diff.
   Run `security-reviewer` when the diff/spec matches the existing Level-3 triggers: auth,
   authorization, personal data, payments, migrations, uploads, secrets, public APIs, schema, or
   persistence. Do not invent a second trigger list.
4. Parse and persist each verdict before acting. `APPROVE` is valid only for its recorded diff
   fingerprint. On `REJECT`, upsert every finding in the Findings registry. For a new identity,
   create exactly one unchecked task using the next available stable `TNNN` ID and title suffix
   `(from <finding-id>)`; for an existing identity, update its registry row and reuse its task.
   Include the originating reviewer's `required_action`, allowed files implied by its evidence,
   required re-review, and the SPEC acceptance criterion the finding blocks. If no acceptance
   criterion covers the required action, do not invent one: classify it as a SPEC contradiction and
   route to `/spec-update`.
5. Delegate finding tasks through the same worker path. After *any* implementation change,
   recompute the fingerprint, invalidate every required reviewer APPROVE that does not match it,
   and schedule all stale required reviewers—not only the reviewer that rejected. Preserve finding
   IDs across iterations. An APPROVE resolves every currently open finding owned by that reviewer
   for the approved fingerprint; persist that verdict/fingerprint in each row. No worker DONE or
   absence from a later REJECT resolves a finding implicitly.
6. When no implementation/review task remains, run `final-conformance-reviewer` exactly once on the
   full evidence chain. For an adopted run the brief includes the `Inherited` table, and the
   report labels every inherited checked task whose `Verify:` clause this run did not observe as
   *inherited, verification not observed* — evidence the maintainer supplied by checking the box,
   stated as such rather than claimed as observed. The label does not block APPROVE by itself; it
   makes the provenance honest. Re-run the reviewer only if the diff changes after its APPROVE.

The loop continues until the termination or abort contract below fires. Findings are never marked
resolved merely because a worker says it changed code; only a subsequent structured APPROVE closes
their gate.

## Autonomous mode — convergence caps

Caps exist to detect **stagnation**, never to bound how much work a feature contains. Getting this
backwards is a known defect (D017): gating every reviewer invocation against one counter aborts any
feature with more tasks than the cap, because `domain-reviewer` runs on each implemented diff and
D015 re-runs stale reviewers after every change. A reviewer that keeps approving must never run a
run out of budget.

Track three numbers per reviewer and one per finding:

- **No-progress streak (gates, cap `max-iterations`).** Increment on a `REJECT` — synthetic ones
  included — that resolves none of that reviewer's open findings. Reset to zero on an `APPROVE`,
  and equally on a `REJECT` that resolves at least one previously open finding of that reviewer,
  even when it raises new ones. A reviewer legitimately finding a different real defect each round
  is converging, and iterates as long as the delegation budget allows.
- **Total invocations (audit only, never gates).** Every call, including re-approvals forced by
  another reviewer's fix.
- **Clean re-approval (gates nothing).** A review scheduled only because the fingerprint moved
  consumes the delegation budget and nothing else.
- **Per-finding REJECT total (gates, cap `max-iterations`).** Count a `REJECT` carrying the same
  `<reviewer>:<finding-id>` **only when a repair attempt for that finding has already completed with
  a worker `DONE`** — that is, count failed repairs, not re-reports and not attempts that never
  produced a change. A `BLOCKED` attempt is not a failed repair: nothing was changed, so the finding
  cannot have failed to converge, and counting it would reintroduce the same false positive on a
  finding waiting for a human answer. A finding re-reported while it still
  sits unworked in the queue does not increment anything: it has not failed to converge, it has not
  been asked to. Monotonic per finding once counting starts; this is what catches a flip-flop, which
  a streak reset by intervening approvals would miss, and every flip-flop follows a repair so none
  escape. Counting bare re-reports instead would abort any run whose first review raises more
  findings than `max-iterations`, and would abort it sooner the better the reviewer is at finding
  real problems in one pass.

Before a reviewer call, pre-check only whether that call *could* exceed a gating cap; an over-cap
call is never made or counted. The single format-correction re-request consumes a delegation but no
gating counter. The delegation budget remains the sole global monotonic backstop against an
unbounded run.

## Autonomous mode — escalation protocol

Classify each exact question from a worker `BLOCKED` block independently. It is **auto-resolvable**
only when every statement is true: purely technical; reversible; inside the approved SPEC; and not
in a human-gated domain. Any one of these conditions makes it **human-gated**:

- product or UX behavior the SPEC does not decide;
- money movement, pricing, billing, refunds, or financial liability;
- personal-data handling, retention, consent, erasure, or other RGPD/LOPDGDD scope;
- a public API, published schema, or external contract change not already approved in the SPEC;
- destructive/irreversible work, including deletion or applying a migration to real data;
- evidence that contradicts the SPEC (route through `/spec-update`; never reinterpret it).

For auto-resolvable questions, persist the classification, delegate the exact question plus SDD
context to `deep-reasoner`, and require alternatives, risks, reversibility, and a recommendation.
The orchestrator—not the read-only agent—then appends an Accepted entry to `DECISIONS.md` labeled
"decided by the orchestrator in autonomous mode" and cites the analysis in the delegation log.
Persist the resolution before re-delegating the blocked task.

For human-gated questions, append an open escalation with the verbatim question, trigger, affected
tasks, and `waiting` status. Continue only tasks proven independent under the existing parallelism
rule. When no independent task remains, end the current invocation with `PAUSED`, a compact list of
answers needed, and the resume command. A maintainer answer is written to `DECISIONS.md`, closes the
escalation, and re-enters through the normal state-validation path.

Contradictory reviewer actions follow the same classifier after one deep-reasoner analysis. If the
contradiction touches a human-gated domain, pause; otherwise record the chosen resolution before
creating/revising finding tasks.

## Autonomous mode — durable state contract

`ORCHESTRATION.md` in the active feature folder is authoritative over conversation memory. Create
it only after the entry gate passes. Write it atomically at every phase transition, before each
delegation, after each response/verdict, after each escalation change, and before returning to the
user. Never let more than the currently recorded in-flight action be recoverable only from chat.

Initialize it from `templates/ORCHESTRATION.md`, the canonical scaffold (replace angle-bracket
values; do not leave them). Its sections, in order: the header (`Feature`, `Mode`, `Entry`, the three
adoption fields, timestamps, effective caps), `State`, `Attempts`, `Inherited`, `Findings`,
`Delegation log`, `Escalations`, `Cap changes`, `Closure delta`, `Run result`. The scaffold is the
shape; every rule about its fields lives in this skill.

`Entry` is `ready` for a run that entered at `Ready` and `adopt` for an adopted one (spec 041). A
`ready` run writes `n/a` in the three adoption fields and leaves `Inherited` empty. An adopted run
fills them from gate condition 7 and writes one `Inherited` row per task checked at adoption:
`Verify clause` copies the task's clause or `none`, and `Verification observed by this run` is `no`
for every row — the loop did not see it happen and never re-delegates a checked task. Counters and
the delegation budget start from zero at adoption, the budget computed from the unchecked tasks at
that moment. The adoption baseline commit is the run's recorded trusted baseline for the recovery
rule below. On re-entry, a state file with no `Entry` line is read as `ready` (D007); the history
tables are the only place adoption facts live, so they are never rewritten.

Append attempt, finding, delegation, and cap-change history; never rewrite it to hide a failed
attempt. State is only the current machine-readable summary. Before any agent call, first evaluate
`Delegations used + 1`; if it exceeds the effective budget, abort without allocating an attempt or
incrementing the counter. Otherwise allocate/persist the attempt and increment exactly once. Before
a reviewer call, apply the gating pre-checks defined in Convergence caps — the reviewer's
no-progress streak and, when the reviewer would re-report a finding the loop has already tried to
repair, that finding's REJECT total. Total invocations and clean re-approvals are recorded but
never block a call.

On re-entry, reconcile any active `PLANNED`, `DISPATCHED`, or `RESPONDED` attempt before selecting
work. If the current fingerprint equals its pre-fingerprint, close it as `FAILED` (interrupted with
no writes) and a retry, if allowed, is a new counted attempt. If the tree changed only inside its
recorded allowed paths, do not blindly reimplement: validate the partial result, route it through
the applicable reviewers, and mark it `RECOVERED` or `FAILED` with evidence. If any changed path is
outside scope or provenance is ambiguous, persist a non-resumable fail-closed abort naming every
path; only the maintainer may recover outside autonomous mode. The remediation must preserve the
aborted audit file under a timestamped name, create a clean dedicated worktree from the run's
recorded trusted baseline, and start a new run there—never delete evidence or silently authenticate
the ambiguous tree. A checked task never skips this recovery validation.

Compute approval fingerprints over the deterministic reviewable tree: tracked diff plus sorted
untracked paths and their bytes. Exclude the active feature's `ORCHESTRATION.md`, `CALIBRATION.md`,
and generated `PR_DESCRIPTION.md`; do not exclude production files or tests. This inclusion rule,
not a particular shell utility, is canonical. On re-entry, recompute it: preserve matching
approvals and invalidate every non-matching required approval; schedule all stale required
reviewers before final conformance. Reconcile the recorded current task with checkboxes, Findings,
Attempts, and the real tree; never re-delegate a checked task or duplicate an existing finding task.
A missing/malformed/mismatched state file cannot authenticate re-entry and must fail the entry gate
rather than being guessed back into shape.

## Autonomous mode — termination and abort

The run is **DONE** only when all are simultaneously true:

1. every `TASKS.md` item is checked;
2. every PLAN-mandated verification command has just exited 0;
3. `domain-reviewer` has APPROVE for the current fingerprint;
4. `security-reviewer`, when triggered, has APPROVE for the current fingerprint;
5. `final-conformance-reviewer` has APPROVE for the current fingerprint — for an adopted run, the
   verdict of a brief that carried the `Inherited` table, whose *inherited, verification not
   observed* labels are recorded evidence, not a DONE blocker;
6. no escalation or blocking decision remains open.

Then freeze and persist the fully approved implementation fingerprint. Before invoking lifecycle
skills, record the narrow closure allowlist: the exact lifecycle status/evidence writes declared by
`/spec-review` and `/spec-close`, plus generated `ORCHESTRATION.md`, `CALIBRATION.md`, and
`PR_DESCRIPTION.md`. Run `/spec-review <feature-path>` and require its Pass (the owning skill alone
may set `In Review`), run `/spec-close <feature-path>` and require its gate (the owning skill alone
may set `Done`), then generate `PR_DESCRIPTION.md` via `/pr-description`. Record the observed
closure delta. Expected lifecycle-only/evidence changes do not invalidate the frozen implementation
approval; any production file, test, requirement, PLAN content, TASKS content beyond expected
lifecycle bookkeeping, DECISIONS content, or other unexpected change invalidates final conformance
and returns to REVIEW (or `/spec-update` if requirements changed). Persist `Run result: DONE` only
after the observed delta contains no unexpected change. If an owning skill refuses, remain PAUSED or
recoverably ABORTED with its exact reason; never write the status on its behalf.

Stop before the next action when a reviewer's no-progress streak or a single finding's REJECT total
would exceed `max-iterations`, a delegation would exceed `max-delegations`, two structured-output
attempts fail as defined above and cannot be classified safely, verification remains red outside
the current task's scope, or human-gated work blocks every remaining task. A non-convergence abort
names the reviewer or the finding that failed to converge, never merely the counter value. `PAUSED` is reserved for a concrete maintainer answer. Cap exhaustion,
provider-format failure, and remediable verification failure persist `ABORTED, resumable: yes` with
the exact counter/failure and required remediation. Corrupt or mismatched state and unexplained
out-of-scope writes persist/refuse as `ABORTED, resumable: no`; never guess provenance. Every stop
records open findings/tasks/escalations and last green verification.

Re-entry from a recoverable abort first proves its remediation. Cap exhaustion requires an explicit
higher override; omitted, equal, or lower caps refuse. Accepted increases update the effective cap
and append `Cap changes` before work. The delegation budget, total invocations, and per-finding
REJECT totals remain monotonic across re-entry and are never reset. A no-progress streak keeps its
recorded value on re-entry and continues to reset only through the progress rule above — re-entry
is not a way to clear it.

At every exit—DONE, PAUSED, or ABORTED—assert from the attempt/delegation/command log that the loop did not
run `git commit`, `git push`, `git merge`, apply a real migration, edit secrets, or directly change
SPEC status. The loop may invoke the owning lifecycle skills; that is not a direct transition.

## Task classification

| Level | Signals | Flow |
|---|---|---|
| **1 — Trivial** | copy, translations, small visual tweaks, obvious localized change, formatting, a simple test, type-only changes with no domain impact | Orchestrator → fast-worker → validation. Never use deep-reasoner. SDD docs optional (small-change shortcut). |
| **2 — Normal** | clear-SPEC feature, bounded bug, related components, non-critical business logic | Orchestrator does discovery itself → SPEC/PLAN/TASKS → fast-worker → tests → final review. deep-reasoner only if ambiguity or risk emerges. |
| **3 — High risk/complexity** | payments/Stripe, webhooks, security, authorization, personal data, migrations, concurrency, distributed systems, idempotency, inconsistent state, race conditions, architecture changes, cross-cutting refactors, bugs without clear root cause | Orchestrator → deep-reasoner → PLAN → small TASKS → fast-worker → tests → risk review (deep-reasoner may review; you decide) → final validation. |
| **4 — Investigation/audit** | security audit, payments audit, architecture analysis, root-cause hunt, evaluating a technical proposal | Orchestrator → deep-reasoner → report. No implementation unless explicitly requested afterwards. |

If the goal touches auth, personal data, tenant isolation, public APIs, uploads, secrets,
schema/migrations or persistence, treat it as Level 3 minimum (matches `/sdd` full-workflow
detection).

## Delegation rules

**Spec status is never the orchestrator's to write.** Keeping SPEC/PLAN/TASKS/DECISIONS in sync
means their *content*, not their stage: each `Status` transition is performed by its owning skill
(`/spec-plan` → `Ready`, `/spec-implement` → `In Progress`, `/spec-review` → `In Review`,
`/spec-close` → `Done`). Neither the orchestrator nor a delegated agent may promote a spec
directly — run the owning skill instead. See `sdd-guardrails` section 11.

**deep-reasoner (Opus — expensive, read-only).** Use for: architecture, system design,
complex debugging, root cause, security, concurrency, idempotency, race conditions, data
consistency, delicate migrations, algorithm design, distributed systems, risk analysis,
SPEC/PLAN review, high-risk implementation review, contradictory requirements.
Never for: copy, formatting, boilerplate, trivial changes, or anything you can settle
yourself in less cost.

**fast-worker (Sonnet — implementation).** Use for: approved tasks, code changes, tests,
mechanical refactors, type fixes, boilerplate, docs, formatting, pre-decided small
changes, running verifications. Never delegate a vague task ("implement the whole
feature") — split it first. It will stop and return any undocumented architectural
decision: answer it (document in DECISIONS.md), then re-delegate.

**Every delegation brief must include:** objective · allowed files · SDD docs to read ·
concrete requirements · affected acceptance criteria · mandatory tests · restrictions ·
what NOT to modify · expected response format (the agents have fixed formats — say
"follow your standard format").

**Cost control:** delegate by objective, never dump the conversation; request summarized
structured answers; reuse findings already obtained — no redundant investigations; one
solid delegation beats several speculative ones; don't delegate what the main session
resolves trivially; limit each agent's read/edit scope when viable.

**Parallelism:** parallel fast-worker tasks are allowed ONLY when they cannot touch the
same files, the same contract, the same migration, the same domain state, or shared
tests with real conflict probability. When in doubt, serialize.

**Fallback (never block on a missing model):**
- Fable unavailable as main session → run the orchestrator on Sonnet (`claude --model
  sonnet` or `/model`); this skill's logic is model-agnostic.
- Opus unavailable → delegate the analysis to a general-purpose subagent with `model:
  sonnet` in a separate context, and record in DECISIONS.md that the analysis did not use
  the preferred model.
- Sonnet unavailable → use the nearest available model via the Agent-tool model override.
  Never invent model identifiers.
- `deep-reasoner`/`fast-worker` agents not installed → use general-purpose subagents with
  an explicit model override (`opus`/`sonnet`) and the same brief, and suggest re-running
  the installer.

## Phases

**1 — DISCOVERY.** Understand the request; inspect the repo (prefer delegating broad scans
to keep context clean); locate related features under `specs/features/` and any existing
SPEC; identify affected code/tests/docs; classify level; decide delegation. Produce:
current state, initial scope, detected risks, related SDD docs, delegation decision.

**2 — SPECIFY.** Create or update `SPEC.md` via the `/spec-create` / `/spec-update`
conventions (context, problem, goal, scope, out of scope, functional and non-functional
requirements, security, accessibility, performance, edge cases, acceptance criteria,
assumptions, dependencies, risks, expected tests — as applicable). Never invent repo
behavior; verify it.

**3 — PLAN.** Level 3: delegate to deep-reasoner (current-code analysis, root cause,
architecture, alternatives, trade-offs, risks, compatibility, test strategy,
migration/rollback strategy), then review its output critically and write the final
`PLAN.md` yourself — never paste the subagent's output blindly. Level 2: plan directly
via `/spec-plan`.

**4 — TASKS.** Write `TASKS.md`: small, ordered, independent where possible, verifiable,
with affected files/areas, done-criteria, associated tests, stable IDs (T001…), and zero
open architectural decisions. Never a task like "implement the whole feature".

**5 — IMPLEMENT.** Delegate task-by-task to fast-worker with the full brief (above).
Respect the parallelism rule. Review each returned report; answer returned blocking
questions via DECISIONS.md before re-delegating.

**6 — QA.** Review the real diff; check scope didn't grow; compare against SPEC; check
every acceptance criterion; run relevant tests, typecheck, lint, build (when reasonable),
regression tests; verify no secrets introduced; review migrations/config changes; record
real limitations. For high-risk changes you may use deep-reasoner as reviewer — the final
decision is yours. Use `/spec-review`, `/qa-review` and the specialized reviews the
change triggers.

**7 — CLOSE.** Mark finished tasks; update `DECISIONS.md` with relevant decisions; keep
requirement↔task↔test traceability; summarize modified files, executed and NOT executed
validations, pending risks. Never declare success with unresolved failures. Then
`/spec-close` and `/pr-description` when the user wants a PR.

## Output

End every run with a compact report: classification chosen, delegations made (agent,
objective, outcome), SDD docs created/updated, validations executed with results,
acceptance criteria status, pending risks, and the recommended next command.
