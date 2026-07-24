---
name: spec-update
description: Update an existing spec mid-implementation. Propagates changes to PLAN.md, TASKS.md, and DECISIONS.md and identifies impacted tasks.
---

## SDD Contract

```yaml
category: lifecycle
inputs: [SPEC.md, PLAN.md, TASKS.md, DECISIONS.md]
outputs: [updated-SPEC.md, updated-PLAN.md, updated-TASKS.md]
side_effects: writes-specs
writes_code: false
writes_specs: true
analysis_only: false
primary_agent: solution-architect
secondary_agents: []
profile_scope: all
provider_specific: false
```

You are working in Spec-Driven Development mode.

Your task is to update an existing feature specification after new information, requirement changes, or scope adjustments.

## Core rules

- Do not implement production code.
- Read the current `SPEC.md`, `PLAN.md`, `TASKS.md`, and `DECISIONS.md` before making any changes.
- Apply only the changes the user explicitly described.
- Do not silently change acceptance criteria without flagging the impact.
- Every change to SPEC.md that affects acceptance criteria must be propagated to TASKS.md.
- Every change that represents a decision (e.g. scope change, new constraint, rejected alternative) must be recorded in DECISIONS.md.
- Do not change the spec status unless the user instructs it.

## Update process

1. Read all four SDD files for the target feature.
2. Identify what the user wants to change (requirements, scope, actors, edge cases, ACs, non-goals, etc.).
3. Apply the changes to `SPEC.md`.
4. Identify which tasks in `TASKS.md` are impacted:
   - Tasks that cover changed or removed ACs → mark with `[NEEDS REVIEW]` comment.
   - Tasks already completed that covered removed ACs → flag as potentially over-implemented.
   - New ACs that have no task → add new tasks in the relevant phase.
5. Update `PLAN.md` if the proposed approach, risks, dependencies, or rollback strategy change.
6. Record the update as a new decision entry in `DECISIONS.md`.

## DECISIONS.md entry for spec updates

Use this format:

### DXXX - Spec updated: <short reason>

**Date:** <YYYY-MM-DD>

**Status:** Accepted

**Context:**

What changed and why (new requirement, constraint, discovered edge case, stakeholder feedback, etc.).

**Decision:**

What was changed in the spec and what was not changed.

**Reasoning:**

Why this change is necessary.

**Consequences:**

Which tasks are impacted. Which completed tasks may need to be revisited. Any new risks introduced.

## Output

After updating, summarize:

- Spec path
- Changes made to SPEC.md (sections changed, ACs added/removed/modified)
- Tasks impacted (list task IDs and their new state)
- New tasks added (if any)
- Decision recorded (ID and title)
- Recommended next command (`/spec-implement` to continue, or `/spec-plan` if the plan changed significantly)

## Context economy

- Read only the files needed for the current task.
- Prefer the active feature folder over scanning the whole repository.
- Do not inspect unrelated specs.
- Do not inspect archived specs unless explicitly asked.
- Do not paste full file contents unless explicitly requested.
- Keep the response short and actionable.
- Always suggest the next command when useful.
