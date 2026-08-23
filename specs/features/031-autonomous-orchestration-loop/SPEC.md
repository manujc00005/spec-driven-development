# Feature Spec: autonomous-orchestration-loop

## Status

Done

## Problem

`sdd-orchestrate` can delegate every phase of the SDD workflow, but it cannot *close the
loop* without a human in the middle. Five concrete gaps prevent an unattended run from a
`Ready` spec to a PR-ready branch:

1. **Reviewer output is prose, not a gate.** `security-reviewer`, `domain-reviewer` and
   `final-conformance-reviewer` return severity-ranked findings as formatted text
   ([security-reviewer.md:30](../../../agents/security-reviewer.md:30)). The orchestrator
   has to *interpret* whether a review passed. The repo already learned this lesson the
   hard way: commit `36c3b04` exists because `check-consistency --fix` keyed control flow
   on rendered message text and broke. There is no structured verdict an orchestration
   loop can branch on.

2. **Findings do not flow back into work.** Nothing defines how a REJECT finding becomes
   a new `TASKS.md` item, who implements it, or how the fix gets re-reviewed. Today that
   circuit is closed by the human reading the review and deciding.

3. **There is no escalation rule.** `implementer`/`fast-worker` correctly stop on any
   decision not in `DECISIONS.md` ([implementer.md:16](../../../agents/implementer.md:16)),
   but every stop lands on the human — the skill has no rule distinguishing "technical,
   in-scope, resolvable by deep-reasoner and recordable in DECISIONS.md" from "product
   decision, must wait for the maintainer". Autonomy without that rule either interrupts
   constantly or decides things it must not.

4. **Orchestration state lives only in conversation context.** A long autonomous run will
   hit context compression. Which task is in flight, which review iteration is running,
   and what was already escalated are not persisted anywhere, so a compressed or resumed
   session cannot re-enter the loop reliably. `/spec-status` reads the SDD docs, but the
   loop state (iteration counters, pending escalations) is not in them.

5. **No termination contract.** Neither the exit condition ("done") nor the abort
   condition ("not converging") is defined. Without an iteration cap, an implement→review
   disagreement loops forever; without a machine-checkable done condition, "finished" is
   a judgment call.

## Goal

`sdd-orchestrate` gains an **autonomous mode**: given a feature whose spec is `Ready`
with zero open questions, it runs the implement → review → fix loop end to end without
human input, resolving technical blockers itself via deep-reasoner + `DECISIONS.md`,
pausing only on defined escalation conditions, and terminating in a fully reviewed
working tree plus a generated PR description — never committing, pushing, or merging.
On the nominal green path the human intervenes at exactly three points: approving the spec
(before), answering human-gated escalations (during, only if any), and reviewing the PR (after).
Safety refusals, exhausted caps, invalid permissions, or a red baseline may require additional
maintainer action; those are explicit non-success exits, not hidden autonomous decisions.

## Non-goals

- **No Agent SDK runner, no CI/cron integration.** That is phase 2 — a separate feature.
  This feature makes the loop protocol exist and work inside a Claude Code session.
- **No auto-commit, auto-push, or auto-merge.** The loop ends with an unstaged working
  tree in a dedicated branch/worktree and a PR description file. Publishing is the
  human's. This is a resolved decision, not an open question: the delegated agents'
  own contracts already forbid committing ([implementer.md](../../../agents/implementer.md)
  Forbidden actions), and phase 1 does not carve an exception for the orchestrator.
  Checkpoint commits for audit/bisect/crash-recovery are explicitly deferred to phase 2,
  where the SDK runner — not an agent — could own them.
- **No new agents.** The loop uses the existing seven; the verdict block changes their
  *output contract*, not their responsibilities.
- **No verdict blocks in standalone review skills** (`security-review`, `qa-review`, …).
  Scope is the three reviewer *agents* the orchestrator delegates to. Extending the
  block to user-invoked skills is a natural follow-up, out of scope here.
- **No parallel implementer fan-out beyond the existing parallelism rule**
  ([SKILL.md:82](../../../skills/sdd-orchestrate/SKILL.md)). Autonomy and new
  concurrency at the same time multiplies failure modes.
- **No change to spec Status ownership** (`sdd-guardrails` section 11). Autonomous mode
  *runs* the owning skills at the right moments; it never promotes a status directly.

## Users / Actors

- **Maintainer** — approves the spec, answers escalations, reviews the final PR.
- **Orchestrator session** (`sdd-orchestrate`) — runs the loop, parses verdicts, applies
  the escalation rule, maintains loop state.
- **Delegated agents** — `implementer`/`fast-worker` (execute tasks),
  `deep-reasoner` (resolve technical escalations, high-risk review),
  `security-reviewer`, `domain-reviewer`, `final-conformance-reviewer` (gate),
  `codebase-researcher` (discovery, unchanged).

## Current behavior

`/sdd-orchestrate <goal>` classifies the task, delegates phase by phase, and reports back
to the human between phases. Reviews return prose findings; the human reads them and
decides what happens next. If an agent stops on a missing decision, the run stops until
the human answers. Nothing persists loop state; nothing defines convergence.

## Desired behavior

`/sdd-orchestrate --autonomous <feature-path>` on a `Ready` spec:

1. **Entry gate.** Refuse to start unless all six hold: (a) spec `Status: Ready`;
   (b) `DECISIONS.md` has zero open questions; (c) `TASKS.md` exists with no unchecked
   blocking prerequisites; (d) the session is on a dedicated feature branch or worktree
   (never the default branch); (e) the working tree is clean on first entry, or contains only
   paths attributable to the authenticated run on re-entry; (f) the PLAN-mandated verification
   suite passes at baseline *and leaves the same clean tree* (a pre-existing red or mutating suite
   makes every later verdict unattributable). Each refusal names the exact unmet condition and the
   command that fixes it.
2. **Loop.** Tasks run one at a time by default; batching only under the skill's
   existing parallelism rule. For each completed task or batch: run the applicable
   reviewers → parse their verdict blocks → REJECT findings become new `TASKS.md` items
   (traceable to the finding ID) → re-delegate → re-review. Per-reviewer iteration cap
   (default 3). Any implementation change invalidates every required reviewer APPROVE whose
   fingerprint no longer matches; all stale required reviewers are re-run, not only the reviewer
   that originally rejected. Reviewer selection reuses the skill's existing detection, not new rules:
   `domain-reviewer` on every implemented diff; `security-reviewer` when the change
   matches the Level-3 triggers already listed in the skill (auth, personal data,
   payments, migrations, uploads, secrets, public APIs, schema/persistence);
   `final-conformance-reviewer` exactly once at the end — re-run only if the diff
   changes after its APPROVE.
3. **Blocker handling.** An agent's blocking decision is classified by the escalation
   rule: *auto-resolvable* → deep-reasoner analyzes, orchestrator records the resolution
   in `DECISIONS.md`, re-delegates; *human-gated* → recorded in `ORCHESTRATION.md`,
   loop continues on independent tasks if any, otherwise pauses with a compact
   escalation report.
4. **Termination.** Done ⇔ all tasks checked ∧ mandated verifications green (tests,
   typecheck, lint, build — as the PLAN mandates) ∧ every required reviewer's latest
   verdict is APPROVE ∧ `final-conformance-reviewer` verdict is APPROVE. Then the
   orchestrator runs `/spec-review` and `/spec-close` (owning skills perform their own
   status transitions) and generates the PR description. Abort ⇔ iteration cap exceeded,
   budget cap exceeded, or an unresolvable human-gated escalation blocks all remaining
   tasks — always ending with a report of exactly where and why it stopped. Expected lifecycle-only
   changes made by `/spec-review` and `/spec-close`, plus generated orchestration/calibration/PR
   evidence, are audited separately and do not invalidate the frozen implementation approval;
   any other post-approval change does invalidate it and returns to review.
5. **Resumability.** Re-running `--autonomous` on the same feature re-enters the loop
   from `ORCHESTRATION.md` state idempotently — no repeated work, counters preserved. An interrupted
   delegation is reconciled from its durable attempt record and pre-delegation fingerprint before
   any retry. A recoverable abort may resume after its recorded remediation; counters never reset,
   and cap overrides may only increase the effective caps.

## Functional requirements

- FR-001: `sdd-orchestrate` accepts
  `--autonomous specs/features/<nnn>-<name> [--max-iterations N] [--max-delegations N]`
  and runs the loop in Desired behavior; non-autonomous invocations behave exactly as
  today.
- FR-002: The entry gate refuses to start on any unmet precondition (invalid lifecycle status,
  open questions > 0, missing TASKS.md, default branch, unattributed dirty tree, red baseline suite,
  or a baseline suite that mutates the tree) with the specific unmet condition and remediation named.
  `Ready` is required on first entry; authenticated re-entry follows FR-011.
- FR-003: The three reviewer agents (`security-reviewer`, `domain-reviewer`,
  `final-conformance-reviewer`) end every report with a **verdict block**: a fenced
  `yaml` block with `verdict: APPROVE | REJECT`, and for REJECT a `findings` list where
  each finding has `id`, `severity` (Critical/High/Medium/Low), `evidence` (path:line),
  `summary`, and `required_action`. Prose findings remain above the block for the human;
  control flow keys **only** on the block (precedent: `36c3b04`).
- FR-004: `implementer` and `fast-worker` end every report with a **completion block**
  (`status: DONE | BLOCKED`, and for BLOCKED the undocumented decision(s) verbatim), so
  the orchestrator branches on structure, not prose.
- FR-005: The skill defines a written **escalation rule**. Auto-resolvable: purely
  technical, reversible, inside SPEC scope, and not touching a human-gated domain.
  Human-gated (any one suffices): product/UX behavior the SPEC does not specify; money
  movement or billing; personal-data handling changes (RGPD scope); public API or
  published contract changes not in the SPEC; destructive or irreversible operations
  (data deletion, applied migrations); anything contradicting the SPEC (route to
  `/spec-update`, never silently reinterpret).
- FR-006: Auto-resolved escalations are recorded in `DECISIONS.md` before re-delegation,
  marked as decided by the orchestrator in autonomous mode, citing the deep-reasoner
  analysis — auditable and reversible by the maintainer.
- FR-007: REJECT findings convert to `TASKS.md` items with stable IDs traceable to the
  originating finding (e.g. `T0xx (from SEC-003)`), keeping requirement↔task↔test
  traceability intact. `ORCHESTRATION.md` persists a finding registry keyed by
  `<reviewer>:<finding-id>` with its task ID, severity, required action, status, first/last seen
  iteration, and resolving verdict/fingerprint. Re-entry and re-review update that row rather than
  creating a duplicate task for the same finding. Only an APPROVE from the owning reviewer on the
  current fingerprint resolves its open findings; worker completion or omission does not.
- FR-008: Loop state persists in `ORCHESTRATION.md` inside the feature folder (schema in
  Data model changes) and is updated at every phase transition, delegation, verdict, and
  escalation — before the orchestrator proceeds. Every delegation has a stable `attempt_id`,
  lifecycle (`PLANNED | DISPATCHED | RESPONDED | VERIFIED | RECOVERED | FAILED`), objective,
  allowed-path scope, and pre/post fingerprint. After interruption, an unchanged tree may retry;
  a changed tree is inspected and verified as recovery work rather than blindly re-delegated; a
  change outside the recorded scope fails closed as an unattributed-path escalation.
- FR-009: Caps measure **non-convergence, not workload**. A reviewer invocation that is merely
  re-work — an APPROVE, or a re-review forced only because another reviewer's fix moved the
  fingerprint — never consumes an iteration cap. Two distinct non-convergence counters exist, both
  defaulting to `max-iterations` (3):
  - **Per reviewer:** consecutive **no-progress** `REJECT` verdicts (including synthetic
    fail-closed REJECTs). A REJECT counts as progress — and resets the counter to zero — when it
    resolves at least one finding that reviewer had open, even if it raises new ones; an `APPROVE`
    also resets it. Only a REJECT that closes nothing increments. A reviewer legitimately finding a
    different real defect each round, with the previous one fixed, therefore iterates as long as
    the delegation budget allows; the reviewer's total invocation count is recorded for audit but
    never gates.
  - **Per finding identity:** the total number of `REJECT` verdicts carrying the same
    `<reviewer>:<finding-id>`, taken from its Findings-registry row. This is monotonic per finding
    and is what catches a flip-flop that a consecutive counter would miss.

  Exceeding either produces a recoverable abort naming the reviewer or the finding that failed to
  converge. The **total delegation budget is the global backstop** against unbounded runs and
  remains strictly monotonic: it counts every delegated worker, reviewer, deep-reasoner call, and
  structured-output retry — re-approvals included — while deterministic local commands and
  same-context owning-skill calls are logged but do not consume it. Because the budget must now
  absorb a whole feature's re-approvals, its default is task-relative:
  `max-delegations = max(25, 6 × unchecked tasks at first entry)`, computed once at first entry and
  recorded in `ORCHESTRATION.md`. On authenticated re-entry an explicit override may only increase
  an effective cap; it may never reduce a cap below its stored value or reset any counter. The cap
  change and reason are appended to the audit log before resuming.
- FR-010: Termination and abort behave exactly as Desired behavior step 4 — including
  never committing/pushing and never promoting spec Status outside the owning skills.
- FR-011: Re-entry (Desired behavior step 5) is idempotent: completed tasks are not
  re-delegated, findings are not duplicated, and an APPROVE is reused only while its fingerprint
  equals the current reviewable tree. Mechanism: `ORCHESTRATION.md` records the canonical content
  fingerprint next to each APPROVE and the durable attempt state from FR-008. Any implementation
  change invalidates all non-matching required approvals and schedules those reviewers again.
  Authenticated `PAUSED` and recoverable `ABORTED` runs may re-enter after their recorded
  remediation; unsafe/corrupt-provenance aborts are terminal and require a fresh human-controlled
  run.
- FR-013: Finalization freezes the last fully approved implementation fingerprint before invoking
  owning lifecycle skills. The run records an explicit closure-delta allowlist containing only the
  expected status/evidence writes made by `/spec-review`, `/spec-close`, and generated
  `ORCHESTRATION.md`, `CALIBRATION.md`, and `PR_DESCRIPTION.md`. Allowed closure deltas are audited
  but do not stale implementation approvals. Any production, test, plan, task-content, decision,
  or non-lifecycle SPEC change after the freeze invalidates final conformance and returns to REVIEW.
- FR-012: The Codex adapter documents autonomous mode's degradation: no Agent tool, so
  the loop runs sequentially in one context using the same verdict/completion blocks,
  the same `ORCHESTRATION.md` schema, and the same escalation rule; file-based state is
  provider-neutral by design. (`adapters/codex/` doc change; runtime verification gated
  as in Assumptions.)
- FR-014: Autonomous mode is discoverable from the user-facing documentation, not only from the
  skill contract. `docs/SDD-ORCHESTRATION.md` documents the invocation form, the entry gate, the
  escalation split, what the caps mean, and how to resume a `PAUSED`/recoverable-`ABORTED` run, and
  `CHANGELOG.md` records the feature following the convention every recent feature commit follows.

## Non-functional requirements

- Performance / cost: autonomy must not multiply spend — the existing cost-control rules
  of the skill still bind; the delegation budget (FR-009) is the hard backstop.
- Security: the loop inherits every existing forbidden action (no push, no secrets, no
  `.env`, no applied migrations against real databases); running on the default branch
  is an entry-gate refusal, not a warning.
- Observability: `ORCHESTRATION.md` is the audit log — a maintainer reading only that
  file must be able to reconstruct what ran, what was decided autonomously, and why the
  run ended where it did, including findings, attempts, cap changes, recovery decisions, and the
  exact closure delta.
- Maintainability: the verdict and completion blocks are the *only* new coupling between
  agents and orchestrator; their schema lives in one place (the skill) and the agent
  files reference it.

## API / Interface changes

- `skills/sdd-orchestrate/SKILL.md`: new autonomous-mode section (entry gate, loop
  protocol, escalation rule, caps, termination, re-entry); SDD Contract `outputs` gains
  `ORCHESTRATION.md`.
- `agents/security-reviewer.md`, `agents/domain-reviewer.md`,
  `agents/final-conformance-reviewer.md`: Outputs section gains the mandatory verdict
  block.
- `agents/implementer.md`, `agents/fast-worker.md`: Outputs section gains the mandatory
  completion block.
- `adapters/codex/`: documentation of the degraded sequential mode (FR-012).
- `docs/SDD-ORCHESTRATION.md`: autonomous-mode section for users (FR-014).
- `CHANGELOG.md`: feature entry (FR-014).
- No CLI, installer, or `profiles.json` changes.

## Data model changes

New per-feature artifact `specs/features/<nnn>-<name>/ORCHESTRATION.md`:

- Header: feature path, mode, started-at, invocation caps.
- `## State`: current phase; current task ID; current attempt ID/state; effective caps and counters;
  per-APPROVE reviewed-diff fingerprint; frozen final fingerprint; attributed dirty paths.
- `## Attempts`: one row per attempt — ID, agent, objective, lifecycle, allowed paths,
  pre/post fingerprint, outcome, timestamp. Rows are append-only; State points at the active row.
- `## Findings`: registry keyed by reviewer + finding ID — task, severity, required action,
  status, first/last seen iteration, resolving verdict/fingerprint.
- `## Delegation log`: one line per delegation or same-context lifecycle action — agent/skill,
  objective, outcome (DONE/BLOCKED/APPROVE/REJECT/PASS/REFUSED), timestamp.
- `## Escalations`: open and resolved; each with classification (auto/human), the
  question verbatim, resolution or "waiting".
- `## Cap changes`: append-only old/new cap, invocation, reason, timestamp.
- `## Closure delta`: frozen implementation fingerprint plus every allowed lifecycle/evidence path
  and its observed change; unexpected paths invalidate closure.
- `## Run result`: ACTIVE / PAUSED / DONE / ABORTED, plus `resumable: yes|no`, reason, and required
  remediation. `ABORTED + resumable: yes` authenticates re-entry; counters remain monotonic.

No database, no schema files — markdown only, human-readable first.

## Edge cases

- Reviewer returns no verdict block or a malformed one → one re-request with the format
  reminder; a second failure is treated as REJECT with a single finding "malformed
  verdict" and counts against the iteration cap (never treated as APPROVE).
- Two reviewers' required actions contradict each other → auto-resolution attempt via
  deep-reasoner; if the contradiction touches a human-gated domain, escalate.
- Context compression mid-run → next orchestrator turn re-reads `ORCHESTRATION.md` and
  continues; the file, not the conversation, is authoritative.
- Session dies after a worker edits files but before returning its completion block → re-entry
  compares the active attempt's pre-fingerprint and allowed-path scope with the real tree. It never
  starts a second implementation blindly: it verifies/reviews the partial work as `RECOVERED`, or
  pauses on an unattributed/out-of-scope change.
- One required reviewer APPROVEs and another REJECTs the same fingerprint → the fix invalidates
  every prior APPROVE whose fingerprint is now stale. All stale required reviewers run again before
  final conformance; “only the rejecting reviewer” is never a shortcut around the current-tree gate.
- Fix for finding A regresses finding B repeatedly (flip-flop) → the per-reviewer *consecutive*
  counter resets on each intervening APPROVE and would miss this, so the per-finding-identity
  REJECT count (FR-009) is what fires; the abort report names the finding that never converged.
- A feature has more tasks than `max-iterations` → completing them is workload, not disagreement.
  Clean re-approvals forced by fingerprint invalidation consume the delegation budget only, so a
  long feature runs to completion and only a genuinely stuck reviewer or finding aborts it.
- `DECISIONS.md` acquires a new open question mid-run (e.g. written by a delegated
  agent) → treated as a blocking decision and classified by the escalation rule; the
  entry gate's "zero open questions" applies only at start.
- Human-gated escalation blocks some tasks but not others → independent tasks continue;
  the pause report lists exactly which tasks wait on which answer.
- The spec turns out to be wrong mid-implementation (implementer evidence contradicts a
  requirement) → always human-gated; route through `/spec-update`, never reinterpreted
  autonomously.
- Verification suite is itself broken at entry (tests failing before any change) →
  entry-gate refusal (precondition f), pointing at the failing suite.
- Baseline verification exits 0 but creates/modifies files → entry-gate refusal as a mutating
  baseline, naming the paths; the maintainer must make the suite hermetic or update the PLAN.
- Human answers a pending escalation → the answer is recorded in `DECISIONS.md`, the
  escalation is closed in `ORCHESTRATION.md`, and re-invoking autonomous mode resumes
  through the standard re-entry path — no special "resume after answer" mode.
- A cap is exhausted → record `ABORTED, resumable: yes`; a later invocation may raise (never lower
  or reset) the relevant cap and resume. Corrupt state, mismatched feature identity, or unexplained
  out-of-scope writes are `resumable: no` and require maintainer recovery rather than guesswork.
- `/spec-review` or `/spec-close` changes more than the expected lifecycle fields/evidence → the
  unexpected closure delta invalidates final approval and returns the loop to REVIEW or pauses if
  it changes approved requirements.

## Acceptance criteria

- AC-001: An autonomous run on a prepared demo feature (Ready spec, seeded tasks, one
  seeded reviewer-findable defect) completes with zero human input: the defect is found
  (REJECT), converted to a task, fixed, re-reviewed to APPROVE, and the run ends DONE
  with `/spec-close` executed by its owning skill and a PR description generated.
- AC-002: Each entry-gate precondition, when individually violated, produces a refusal
  naming that precondition and its remediation — verified for all six.
- AC-003: All three reviewer agents' files mandate the verdict block and all five
  agent files' output contracts match the schema in the skill; `check-consistency.sh`
  passes.
- AC-004: A seeded human-gated blocker (e.g. an undocumented product decision) pauses
  the affected tasks, is recorded in `ORCHESTRATION.md` as `human`, and independent
  tasks still complete; a seeded technical blocker is resolved without pausing and
  appears in `DECISIONS.md` as orchestrator-decided.
- AC-005: Killing the session mid-loop and re-invoking autonomous mode resumes without
  re-delegating completed tasks or re-running unaffected APPROVE verdicts. Killing it after a
  worker has changed files but before its response also reconciles the durable attempt without a
  blind second implementation; an out-of-scope path fails closed.
- AC-006: With a reviewer forced to always REJECT, the run aborts at the per-reviewer consecutive
  cap with a non-convergence report naming that reviewer; no infinite loop, no cap bypass. Re-entry
  with no or a lower cap remains refused; a higher cap resumes with preserved counters and an
  audited cap change.
- AC-011: Caps measure stagnation, not workload, proven four ways: (a) a feature whose unchecked
  task count exceeds `max-iterations` runs to DONE with no cap-related abort, and the per-reviewer
  consecutive counters read zero at the end because every review ended in APPROVE; (b) a reviewer
  re-run forced only by another reviewer's fix leaves that reviewer's consecutive counter unchanged
  while the delegation budget still decrements; (c) a finding that alternates REJECT/APPROVE past
  `max-iterations` aborts on the per-finding counter even though no consecutive counter ever
  reached the cap; (d) a reviewer that rejects more than `max-iterations` times in a row while
  resolving a prior finding each round keeps iterating to a legitimate DONE, because progress
  resets the counter — only the run that closes nothing aborts.
- AC-007: A run never executes `git commit`/`git push`, never writes a spec `Status`
  transition from the orchestrator itself, and refuses to start on the default branch.
- AC-008: When domain and security both review fingerprint A, domain APPROVEs, security REJECTs,
  and the fix produces fingerprint B, both stale reviewers approve B before final conformance.
- AC-009: Re-reporting the same finding across review iterations maps to one stable task and one
  findings-registry row; its final resolving verdict and fingerprint are reconstructable from
  `ORCHESTRATION.md` alone.
- AC-010: A green baseline that dirties the tree is refused. On the happy path, lifecycle-only
  closure changes are recorded in the closure delta without invalidating the frozen implementation
  approval; a seeded non-lifecycle post-approval change does invalidate it and forces re-review.
- AC-012: `docs/SDD-ORCHESTRATION.md` documents the autonomous invocation, entry gate, escalation
  split, cap semantics, and resume path, and `CHANGELOG.md` carries the feature entry (FR-014).
- AC-013: Behavioral evidence exists for **both** providers before closure. A provider whose run
  could not execute (quota, missing CLI) is recorded as an explicit unmet blocker in
  `CALIBRATION.md` and blocks `/spec-close`; it is never reported as a pass or silently omitted.

## Test scenarios

- Unit: none — no executable code ships; the contract is markdown. (If a verdict-schema
  lint helper is added to `scripts/`, it gets a bats test like its siblings.)
- Integration: `scripts/check-consistency.sh` green over the modified skill and agent
  contracts (AC-003).
- E2E: scripted calibration run on a disposable demo feature covering AC-001, AC-004,
  AC-005, AC-006, AC-008, AC-009, AC-010, and AC-011 — same style as the spec 029 reviewer
  calibration; evidence recorded in the feature folder. The AC-011 fixture must carry strictly more
  unchecked tasks than `max-iterations`, since a 3-task fixture cannot detect the workload/
  disagreement conflation this spec update exists to fix.
- Manual: one real (non-seeded) small feature run end-to-end by the maintainer before
  the spec closes; Claude Code and Codex smoke runs per AC-013, each recorded as pass or as an
  explicit closure blocker.

## Assumptions

- `max-iterations` 3 is a sensible non-convergence threshold, and a task-relative delegation budget
  (FR-009) is the right global backstop; both overridable per invocation under FR-009's monotonic
  re-entry rule and tunable later with calibration evidence. The `6 ×` factor budgets roughly one
  worker, one domain review, one security review, and one full fix-and-re-review cycle per task;
  the AC-011 run is the first real check on that arithmetic.
- The orchestrator LLM parsing a fenced yaml verdict block is reliable enough as the
  gate mechanism; no separate parser binary is needed for phase 1 (the SDK runner in
  phase 2 will parse the same blocks programmatically — the schema is designed for
  both).
- Autonomous runs execute in a session whose permission mode allows edits without
  per-file prompts (e.g. `acceptEdits` in a worktree); the skill documents this but
  does not manage permissions itself.
- Provider smoke runs gate `Done`, not `Ready`, and AC-013 makes that gate symmetric: a Codex CLI
  is present in this environment, so its run is required rather than deferred, and Claude Code —
  the primary adapter — is not exempt from producing its own behavioral evidence just because the
  Codex run passed.
- `ORCHESTRATION.md` is git-tracked like the other SDD docs — the audit trail travels
  with the branch and appears in the PR.
- The entry-gate baseline check runs the same verification suite the PLAN mandates for
  the loop; on slow suites that cost is accepted — it is what makes every later verdict
  attributable to the change under review. Approved PLAN verification commands are non-interactive,
  repository-scoped, and subject to all inherited forbidden-action rules.

## Open questions

- OQ-1: RESOLVED during clarification — no checkpoint commits in phase 1. The delegated
  agents' contracts already forbid committing, this spec's Non-goals declared
  no-auto-commit, and carving an orchestrator exception would contradict both. Crash
  recovery is the worktree's uncommitted tree plus `ORCHESTRATION.md` re-entry
  (FR-008/FR-011). Checkpoint commits are deferred to the phase-2 SDK runner, which is
  not an agent and could own them.
- **DEFERRED at close (2026-08-22)** — OQ-2 (non-blocking): Should `/spec-status` learn to read `ORCHESTRATION.md` and show
  loop state? Natural follow-up; not required for the loop to function.

## Contracted services

Contracted services not declared → all billable add-ons treated as NOT contracted
(conservative default). Run `/project-init` to declare them.
