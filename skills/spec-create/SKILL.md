---
name: spec-create
description: Create a structured feature specification before implementation. Use this when the user wants to add, change, or refactor a feature.
---

You are working in Spec-Driven Development mode.

Your task is to create or update a feature specification.

## Status lifecycle

Specs follow this lifecycle:

```
Draft → Ready → In Progress → In Review → Done | Archived
```

- `Draft`: spec created, not yet plannable.
- `Ready`: plan and tasks exist, implementation can start.
- `In Progress`: at least one task has been implemented.
- `In Review`: all tasks complete and spec-review passed — QA and specialized reviews pending.
- `Done`: all reviews complete and spec-close run — ready for PR.
- `Archived`: spec abandoned or superseded.

This skill always sets status to **Draft**.

## Core rules

- Do not implement production code.
- Do not modify files outside `specs/features/` unless explicitly requested.
- Inspect `specs/features/` to determine the next folder number before creating.
- Prefer existing project terminology and architecture.
- Ask for clarification only if the missing information blocks the spec.
- If something is uncertain but not blocking, write it as an assumption.
- Add unresolved doubts to `Open questions`.

## Folder naming

Create a new folder under:

`specs/features/`

Use this format:

`<number>-<short-kebab-case-feature-name>`

Example:

`001-user-login`

**IMPORTANT — determining the next number:**
Never rely on Glob to list existing spec folders — it can silently return no results even when folders exist.
Always use a shell command to list the directory and find the highest existing number:

```powershell
Get-ChildItem "specs/features/" -Name | Sort-Object | Select-Object -Last 1
```

If the directory is empty or does not exist, start at `001`.
If folders exist, take the highest number and increment by 1 (zero-padded to 3 digits).

## Required file

Create:

`SPEC.md`

## SPEC.md template

# Feature Spec: <feature-name>

## Status

Draft

## Problem

Describe the problem this feature solves.

## Goal

Describe the desired outcome.

## Non-goals

List what is explicitly out of scope.

## Users / Actors

List who interacts with this feature.

## Current behavior

Describe the current system behavior.

## Desired behavior

Describe the expected behavior after the change.

## Functional requirements

- FR-001:
- FR-002:
- FR-003:

## Non-functional requirements

- Performance:
- Security:
- Observability:
- Maintainability:

## API / Interface changes

Describe endpoints, DTOs, events, UI props, commands, screens, or public interfaces.

## Data model changes

Describe tables, entities, migrations, indexes, schemas, or persistence changes.

## Edge cases

- 
- 

## Acceptance criteria

- AC-001:
- AC-002:
- AC-003:

## Test scenarios

- Unit:
- Integration:
- E2E:
- Manual:

## Assumptions

- 

## Open questions

- 

## Auto-clarify pass

After creating the spec, automatically apply a lightweight clarification pass:

1. Strengthen weak or untestable acceptance criteria.
2. Add missing edge cases that are obvious from the requirements.
3. Document implicit assumptions in the `Assumptions` section.
4. Identify blocking questions (things that change the design) and add to `Open questions`.

Do not ask the user before making improvements that do not require input.
If blocking questions exist, list them and wait for answers before recommending `/spec-plan`.

## Output

After creating and auto-clarifying the spec, summarize:

- Spec path
- Spec status: Draft
- Main requirements
- Improvements made (if any)
- Assumptions added (if any)
- Blocking questions (if any)

## Recommended next command

Logic:
- If blocking questions exist: answer them, then re-run `/spec-clarify <path>` for a deeper pass
- If no blocking questions: `/spec-plan <path>`

## Context economy

- Read only the files needed for the current task.
- Prefer the active feature folder over scanning the whole repository.
- Do not inspect unrelated specs.
- Do not inspect archived specs unless explicitly asked.
- Do not paste full file contents unless explicitly requested.
- Keep the response short and actionable.
- Always suggest the next command when useful.
