---
name: sdd-medium
description: Guide a medium SDD workflow. Consider using /sdd instead — it auto-detects complexity and selects the right workflow for you.
---

## SDD Contract

```yaml
category: orchestration
inputs: [feature-description]
outputs: [workflow-recommendation]
side_effects: none
writes_code: false
writes_specs: false
analysis_only: true
primary_agent: orchestration-context
secondary_agents: []
profile_scope: all
provider_specific: false
```

> Consider using `/sdd` instead — it auto-detects whether medium or full workflow is appropriate.
> This skill is kept for cases where you want to explicitly force the medium workflow.

You are guiding a medium Spec-Driven Development workflow.

Use this workflow for non-trivial but relatively clear features.

## Workflow

1. Create or update the feature spec using `/spec-create`.
2. Clarify the spec using `/spec-clarify`.
3. Create the implementation plan using `/spec-plan`.
4. Analyze consistency using `/spec-analyze`.
5. Implement task by task using `/spec-implement`.
6. Review implementation against the spec using `/spec-review`.
7. Run QA review using `/qa-review`.
8. Close the feature using `/spec-close`.
9. Generate a PR description using `/pr-description`.

## When to use

Use this workflow for:

- Medium frontend features.
- Medium backend features.
- Clear API changes.
- Features with limited ambiguity.
- Changes that do not involve sensitive data, authentication, authorization, file uploads or risky database migrations.

## When not to use

Do not use this workflow if the change involves:

- Security-sensitive behavior.
- Authentication or authorization.
- User data or tenant isolation.
- Public APIs with sensitive data.
- File uploads.
- Complex database changes.
- Ambiguous requirements.
- Large architectural changes.

For those cases, use `/sdd-full`.

## Behavior

When invoked:

1. Ask the user for the feature description if it was not provided.
2. Recommend the exact next command to run.
3. Do not implement code directly.
4. Do not skip SDD files.
5. Keep the workflow lightweight.

Note: between step 7 (qa-review) and step 8 (spec-close), specialized reviews may be inserted automatically based on what qa-review detects (backend, frontend, database, security, performance, api). The 9 steps above represent the base workflow.

## Output format

# SDD Medium Workflow

## Recommended workflow

## First command to run

## Notes

## Context economy

- Read only the files needed for the current task.
- Prefer the active feature folder over scanning the whole repository.
- Do not inspect unrelated specs.
- Do not inspect archived specs unless explicitly asked.
- Do not paste full file contents unless explicitly requested.
- Keep the response short and actionable.
- Always suggest the next command when useful.

## Concise workflow output

- Keep output short.
- Show the workflow commands.
- Show the next command.
- Do not explain the whole SDD concept.
- Do not implement code directly.
