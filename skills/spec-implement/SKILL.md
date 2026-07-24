---
name: spec-implement
description: Implement code strictly from an existing SPEC.md, PLAN.md, TASKS.md, and DECISIONS.md.
---

## SDD Contract

```yaml
category: lifecycle
inputs: [SPEC.md, PLAN.md, TASKS.md, DECISIONS.md]
outputs: [code-diff, updated-TASKS.md]
side_effects: writes-code
writes_code: true
writes_specs: true
analysis_only: false
primary_agent: implementer
secondary_agents: []
profile_scope: all
provider_specific: false
```

You are working in Spec-Driven Development mode.

Your task is to implement the next task from an existing feature specification.

## Active feature context

If no path is provided, use the most recently referenced feature path from the current conversation. If none found, ask the user.

## Loop mode

At the start, count unchecked tasks in TASKS.md.

- If the user ran `/spec-implement all` or said "implement all" → implement all remaining tasks sequentially (loop mode).
- If only one task remains → implement it (no prompt needed).
- If multiple tasks remain and no "all" instruction → implement the next task, then ask: "X tasks remaining. Continue with the next task, or stop here to review?"

In loop mode:
- Show progress before each task: "**Task N/Total: T00X — [description]**"
- Update TASKS.md after each task.
- Stop and report immediately if: a test fails, a new architectural decision is needed, or an unresolvable blocker appears.
- After all tasks complete → automatically show implementation summary and recommend `/spec-review`.

## Pre-flight check

Before doing anything else, verify:

1. `PLAN.md` exists in the feature folder. If it does not exist, **stop** and tell the user to run `/spec-plan` first.
2. `SPEC.md` status is `Ready` or `In Progress`. If status is `Draft`, **stop** and tell the user to run `/spec-plan` first to promote the spec to `Ready`.

## Core rules

- Read `SPEC.md`, `PLAN.md`, `TASKS.md`, and `DECISIONS.md` before editing code.
- Implement only the next unchecked task unless explicitly instructed otherwise.
- Do not add behavior outside the spec.
- Do not introduce new abstractions unless the plan requires them or the existing codebase clearly supports them.
- Prefer existing project patterns.
- If implementation requires a new decision, update `DECISIONS.md`.
- Mark completed tasks in `TASKS.md`.
- Add or update tests when behavior changes.
- Run the most relevant tests if possible.
- If tests cannot be run, explain why.
- If this is the first task being implemented (no tasks are checked yet), update `Status` in `SPEC.md` from `Ready` to `In Progress`.

## TDD discipline

Apply test-driven development within each implementation task:

- **Vertical slice**: each task must produce a working, testable increment — not a partial layer.
- **Test through the public interface**: write tests that call the public API of the unit being built, not its internal implementation. Tests must survive refactoring.
- **Tracer bullet first**: before building the full feature, get one end-to-end path passing (even with hard-coded values) to validate the integration seam. Then flesh it out.
- **Minimal code per cycle**: write only the code needed to make the failing test pass. No speculative logic.
- **Refactor only in green**: never refactor while a test is red. Red → fix code → green → refactor → green.
- **No seam available**: if there is no correct test seam for the behavior being implemented, document it in `DECISIONS.md` with the reason (e.g., UI-only, tight coupling, integration boundary). Do not skip the entry silently.

## Before editing

Before modifying files, state:

- Feature folder
- Task being implemented
- Acceptance criteria covered
- Expected files to change
- Any assumptions

## Implementation process

1. Run pre-flight check.
2. Read the SDD files.
3. Inspect the current implementation.
4. Identify the next unchecked task.
5. If this is the first task, update SPEC.md status to `In Progress`.
6. Implement the smallest useful change.
7. Update or add tests.
8. Run relevant checks.
9. Update `TASKS.md`.
10. Update `DECISIONS.md` if a new decision was made.

## Constraints

- Do not silently skip tests.
- Do not mark a task as complete if implementation is partial.
- Do not change unrelated files.
- Do not remove existing behavior unless required by the spec.
- Do not hide uncertainty.

## Output

After implementation, summarize:

- Task completed
- Acceptance criteria covered
- Spec status: (unchanged | updated to In Progress)
- Files changed
- Tests added or updated
- Tests run and result
- Decisions added
- Remaining risks

## Recommended next command

Logic:
- If there are remaining unchecked tasks: `/spec-implement <path>`
- If all tasks are checked: `/spec-review <path>`

## Context economy

- Read only the files needed for the current task.
- Prefer the active feature folder over scanning the whole repository.
- Do not inspect unrelated specs.
- Do not inspect archived specs unless explicitly asked.
- Do not paste full file contents unless explicitly requested.
- Keep the response short and actionable.
- Always suggest the next command when useful.

## Token-saving implementation behavior

- Implement only the next unchecked task unless explicitly instructed otherwise.
- Do not summarize the entire spec, plan or task list.
- Before editing, summarize only: task being implemented, acceptance criteria covered, expected files to change.
- After editing, summarize only: files changed, tests run, task completed, next command.
- Do not create micro-tasks.
- If a task is too small and the next task is tightly related, suggest combining them instead of creating extra implementation rounds.
