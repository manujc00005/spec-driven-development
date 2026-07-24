---
name: spec-plan
description: Convert an approved SPEC.md into an implementation plan, task list, and decision log.
---

## SDD Contract

```yaml
category: lifecycle
inputs: [SPEC.md]
outputs: [PLAN.md, TASKS.md, DECISIONS.md]
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

Your task is to transform an existing `SPEC.md` into an implementation plan.

## Core rules

- Do not implement production code.
- Do not modify application code.
- Read the target `SPEC.md` first.
- Only plan specs whose status is `Draft`. If status is already `Ready` or beyond, confirm with the user before overwriting.
- Inspect the repository before planning.
- Follow existing architecture and naming conventions.
- If the spec is ambiguous, document the ambiguity instead of inventing behavior.
- Every implementation task must map back to one or more acceptance criteria.
- Keep tasks small enough to be implemented independently.
- After creating PLAN.md, TASKS.md, and DECISIONS.md, update `Status` in `SPEC.md` from `Draft` to `Ready`.

## Required files

Create or update these files in the same feature folder:

- `PLAN.md`
- `TASKS.md`
- `DECISIONS.md`

## PLAN.md template

# Implementation Plan: <feature-name>

## Summary

Brief summary of what will be implemented.

## Related spec

Path to the related `SPEC.md`.

## Impacted areas

List modules, folders, services, components, entities, APIs, jobs, tests, or config likely to change.

## Proposed approach

Describe the implementation approach.

## Alternatives considered

Describe alternatives and why they were rejected.

## Dependencies

List external services, libraries, data, infrastructure, or team dependencies.

## Risks

List technical, product, security, performance, or delivery risks.

## Test strategy

Describe unit, integration, E2E, manual, and regression testing.

## Rollback strategy

Describe how to revert or disable the change if needed.

## PLAN verification checklist

- [ ] The plan covers all acceptance criteria.
- [ ] The plan avoids behavior outside the spec.
- [ ] Risks are documented.
- [ ] Test strategy is documented.
- [ ] Rollback strategy is documented.
- [ ] SPEC.md status has been updated to `Ready`.

## TASKS.md template

# Tasks: <feature-name>

## Phase 1: Preparation

- [ ] T001 - Task description. Covers: AC-XXX.

## Phase 2: Implementation

- [ ] T002 - Task description. Covers: AC-XXX.

## Phase 3: Tests

- [ ] T003 - Task description. Covers: AC-XXX.

## Phase 4: Review

- [ ] T004 - Task description. Covers: AC-XXX.

## DECISIONS.md template

# Decisions: <feature-name>

## Decision log

### D001 - <decision-title>

**Date:** <YYYY-MM-DD>

**Status:** Proposed | Accepted | Rejected

**Context:**

**Decision:**

**Reasoning:**

**Consequences:**

## Output

After planning, summarize:

- Plan path
- Tasks path
- Decisions path
- Proposed approach
- First implementation task
- Main risks

## Chaining behavior

After creating PLAN.md, TASKS.md, and DECISIONS.md, **immediately proceed** to run spec-analyze behavior on the same feature path. Do not wait for the user to run `/spec-analyze` manually.

If spec-analyze returns Ready → present: "Ready to implement. First task: T001 — [description]."
If spec-analyze returns Partial/Not ready → present blocking issues and stop.

## Recommended next command

Only shown if chaining is blocked: `/spec-analyze <path>`

## Context economy

- Read only the files needed for the current task.
- Prefer the active feature folder over scanning the whole repository.
- Do not inspect unrelated specs.
- Do not inspect archived specs unless explicitly asked.
- Do not paste full file contents unless explicitly requested.
- Keep the response short and actionable.
- Always suggest the next command when useful.
