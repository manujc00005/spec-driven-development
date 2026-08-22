# Feature Spec: task-verification-criterion

## Status

Draft

## Problem

`TASKS.md` traces **up** and not **down**. The task format the framework emits is
`- [ ] T001 - Task description. Covers: AC-XXX.`
([spec-plan/SKILL.md:116](../../../skills/spec-plan/SKILL.md:116), mirrored in
[specs/_templates/TASKS.md:7](../../_templates/TASKS.md:7)). A task therefore records *which
requirement it serves* but never *how anyone checks it is done*. "Done" is whatever the agent
holding the task decides "done" means.

Three consequences, all observable in this repo today:

1. **No task-level stop condition for the autonomous loop.** Spec 031 closed the
   implement-review-fix circuit without a human in the middle. Its per-task exit is the model's own
   judgement that the task is finished, bounded only by the caps 032 is calibrating. The caps stop a
   runaway; they cannot tell a finished task from an abandoned one.
2. **`spec-analyze` cannot gate on it.** Its checklist asks whether every AC has a task and every
   task maps to an AC ([spec-analyze/SKILL.md:55](../../../skills/spec-analyze/SKILL.md:55)); no
   question asks whether a task states a checkable outcome. A `TASKS.md` where every item reads
   "improve X" passes readiness today.
3. **The convention already appeared, unowned.** Spec 019's `TASKS.md` carries four hand-written
   `**Verified:** …` notes; no other feature has one, no template defines it, nothing consumes it.
   A maintainer reached for the field, wrote it after the fact, and it never became a rule.

The gap is also what the source material this came from calls its highest-yield rule: turn an order
into a checkable criterion, and the agent stops needing supervision every three minutes.

## Goal

Every task carries an observable verification criterion; `spec-plan` emits it, `spec-analyze` gates
on it, and the autonomous loop consumes it as the per-task stop condition — without invalidating any
of the 32 `TASKS.md` files already on disk.

## Non-goals

- **No rewrite of existing task lists.** The field is additive; features already closed stay valid
  and are not backfilled.
- **No change to the `Covers:` trace, the AC format, or the FR format.**
- **No change to the 031 loop protocol** beyond reading a field that did not exist before. Cap
  semantics, abort classes and re-entry rules belong to 031/032.
- **Not the conversational rule.** "Restate the request as something checkable before starting"
  already lives in the maintainer's global instructions. This spec is the artifact half only.
- **No new verification runner.** The criterion is text a human or an agent can execute; nothing in
  the framework executes it automatically (FR-010). A runner is a separate spec, not a stretch goal
  of this one.

## Users / Actors

Maintainer; `spec-plan`, `spec-analyze`, `spec-implement` and `sdd-orchestrate`; the delegated
`implementer`/`fast-worker` agents; the Codex adapter's equivalent prompts.

## Current behavior

A task states its description and its `Covers:` trace. Completion is asserted by checking the box.
`spec-analyze` reports readiness without ever asking how a task would be proven done, and the
autonomous loop decides task completion by model judgement.

## Desired behavior

A task states its description, its `Covers:` trace, and a `Verify:` clause naming a command to run
or an assertion an observer could check. `spec-plan` emits the field for every task it writes.
`spec-analyze` blocks readiness on a task that lacks one or whose criterion is not observable.
`sdd-orchestrate` treats the criterion as the task's exit condition instead of its own judgement.

## Functional requirements

- FR-001: The task format gains a `Verify:` clause: `- [ ] T001 - Description. Covers: AC-XXX.
  Verify: <command or observable assertion>`.
- FR-002: `spec-plan` emits `Verify:` for every task it writes, in both the skill's template and
  `specs/_templates/TASKS.md`.
- FR-003: `spec-analyze` blocks readiness on any task without a `Verify:` clause, and warns on one
  whose criterion fails the observability test in FR-008.
- FR-004: The gate activates **per file, by content**. A `TASKS.md` containing at least one
  `Verify:` clause has adopted the format, and every task in it must carry one. A `TASKS.md`
  containing none is legacy: it passes every skill and `scripts/check-consistency.sh` unchanged. No
  timestamp, no git history, no migration step.
- FR-005: `sdd-orchestrate --autonomous` uses a task's `Verify:` clause as its per-task exit
  condition and records the outcome of checking it.
- FR-006: The Codex adapter's `sdd-spec-plan` and `sdd-spec-analyze` prompts carry the same rule, so
  the format does not diverge by provider.
- FR-007: `specs/_templates/SDD-GUARDRAILS.md` states the rule alongside the existing AC ↔ TASKS
  bidirectional check ([SDD-GUARDRAILS.md:85](../../_templates/SDD-GUARDRAILS.md:85)).
- FR-008: A criterion is **observable** when it satisfies all three: it names *what is inspected*
  (a command, a file, an output, a recorded run); two people checking it would reach the same
  verdict; and it can fail. "Tests pass" fails the first test, "is correct" fails the second,
  "code is written" fails the third.
- FR-009: `spec-plan` never invents a criterion to satisfy FR-002. A task it cannot state a
  criterion for is an underspecified task: it says so and names what is missing, rather than
  writing a placeholder that passes presence and means nothing.
- FR-010: Nothing in the framework executes a `Verify:` clause. The loop requires that the criterion
  was checked and records the criterion together with its result; running the command is the
  implementing agent's ordinary work, not an automatic step triggered by the field.

## Non-functional requirements

- Security: the field stays inert text. A `Verify:` clause is authored in the same file an agent may
  edit, so auto-executing it would let a written artifact become a command another agent runs
  without reading. FR-010 forecloses that; any future runner is a separate spec with its own threat
  model.
- Maintainability: the field is one line per task and must not require a parser. Nothing may depend
  on strict-regex extraction of `Verify:`.
- Compatibility: additive only. No existing artifact becomes invalid.
- Observability: when the autonomous loop checks a criterion, its record must show the criterion and
  the result, not just a checked box.

## API / Interface changes

Task-line format (documentation-level contract). Touches `skills/spec-plan`, `skills/spec-analyze`,
`skills/sdd-orchestrate`, `specs/_templates/TASKS.md`, `specs/_templates/SDD-GUARDRAILS.md` and the
two Codex prompts named in FR-006.

No database, no external integration, no public runtime API. The only security-relevant surface is
the one OQ-1 decides.

## Data model changes

None.

## Edge cases

- **A task genuinely has no executable check** (a documentation edit, a decision record). The
  criterion is then an observable assertion, not a command — the rule must accept that without
  inviting "Verify: reviewed by hand" as a universal escape.
- **A `Verify:` command that cannot run in the environment holding the task** (needs a provider, a
  Windows host, a real quota). It must degrade to a manual criterion rather than fail the gate.
- **Mixed task lists** — a feature planned before adoption and extended after — must not fail the
  gate on their old items.
- **The criterion is wrong rather than missing.** A task whose `Verify:` passes while the work is
  incomplete is worse than no field at all; the gate must judge observability, not mere presence.
- **A task covering several acceptance criteria** needs a criterion that closes all of them, or the
  task is really two tasks. The gate should say which, not accept a criterion that covers one.
- **The whole-suite escape.** Every task reading `Verify: bash scripts/check-consistency.sh` passes
  presence and observability while distinguishing nothing. A criterion shared verbatim across tasks
  is a warning.
- **A task whose only honest criterion is another human's judgement** (a domain review, a Codex
  spot-check on a machine the agent cannot reach). It is accepted, and must name who checks and
  against what — the field records the dependency instead of hiding it.

## Acceptance criteria

- AC-001: A `TASKS.md` produced by `spec-plan` after this change carries a `Verify:` clause on every
  task (FR-001, FR-002).
- AC-002: `spec-analyze` returns a blocking finding for a task list with a missing `Verify:`, and a
  warning for a criterion failing any of FR-008's three tests, named individually (FR-003, FR-008).
- AC-003: Every `TASKS.md` currently in `specs/features/` still passes `spec-analyze` and
  `scripts/check-consistency.sh` unchanged (FR-004).
- AC-004: An observed autonomous run shows a task closing because its `Verify:` criterion was
  checked, with the criterion and its result in the record (FR-005).
- AC-005: The Codex adapter prompts and the guardrails template state the same rule as the Claude
  Code skills, verified on Codex and not merely written (FR-006, FR-007).
- AC-006: A task carrying a non-executable criterion is accepted, and "Verify: reviewed by hand" as
  a blanket criterion is not (edge case 1).
- AC-007: A `TASKS.md` with no `Verify:` anywhere passes; the same file with one clause added blocks
  on its remaining tasks (FR-004).
- AC-008: No code path in any skill, script or adapter prompt executes a `Verify:` clause, and the
  loop's record shows criterion and result for a task it closed (FR-005, FR-010).
- AC-009: Asked to plan a task whose outcome cannot be stated as a criterion, `spec-plan` reports it
  as underspecified instead of emitting a placeholder (FR-009).

## Test scenarios

- Unit / Integration: `bash scripts/check-consistency.sh` exit 0; `bash scripts/skill-eval.sh` for
  the three skills whose contracts change.
- E2E: one feature planned end-to-end with the new format; one legacy feature re-analyzed to prove
  FR-004, then the same file with a single clause added to prove the flip (AC-007); one seeded
  autonomous run for AC-004.
- Adversarial: a task list where every criterion is the same whole-suite command, and one where a
  task covering three ACs carries a criterion closing one — both must be caught, not passed.
- Manual: Codex verification for AC-005 — required before `Done`, not before `Ready`.

## Assumptions

- Nothing parses the task line with a strict regex today, so an added clause breaks no tooling.
  Verified at authoring time: `check-consistency.sh` does not read `TASKS.md` at all.
- 032 closes before this spec is implemented. The autonomous loop consumes this field, so changing
  the task contract mid-calibration would force 032 to recalibrate against a moving format.
- `spec-implement` and the `implementer`/`fast-worker` agents need no contract change: they already
  read `TASKS.md` as prose, so a new clause reaches them without a new instruction. If that proves
  false during planning, they join the surface in FR-006.
- This repo has no `specs/CONSTITUTION.md` — the framework ships the template without instantiating
  one — so no project-level rule constrains this change beyond the templates it edits.

## Open questions

- OQ-1 — **resolved: record-only** (now FR-010). Executing a clause an agent authored, in a file an
  agent edits, is an execution surface this spec has no reason to open. Taken as the recommended
  default without an explicit maintainer answer; reversible while this spec is `Draft`, and it
  belongs in `DECISIONS.md` when `/spec-plan` creates it.
- OQ-2 — **resolved: activation is per file, by content** (now FR-004). A file holding at least one
  `Verify:` has adopted the format; one holding none is legacy. Needs no git history and no
  migration, and it settles the mixed-list edge case on its own. Same standing as OQ-1: default
  taken, reversible, to be recorded as a decision.
- OQ-3 (non-blocking): should `spec-close` refuse a feature whose closed tasks have unrecorded
  verification results, or is that gate already covered by final conformance?

## Contracted services

Contracted services not declared → all billable add-ons treated as NOT contracted (conservative
default). Run `/project-init` to declare them.
