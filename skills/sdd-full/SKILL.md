---
name: sdd-full
description: Guide a full SDD workflow. Consider using /sdd instead — it auto-detects complexity and selects the right workflow for you.
---

> Consider using `/sdd` instead — it auto-detects whether medium or full workflow is appropriate.
> This skill is kept for cases where you want to explicitly force the full workflow.

You are guiding a full Spec-Driven Development workflow.

Use this workflow for complex, ambiguous, risky, database-related or security-sensitive features.

## Workflow

1. Create or update the feature spec using `/spec-create`.
2. Clarify the spec using `/spec-clarify`.
3. Create the implementation plan using `/spec-plan`.
4. Analyze consistency using `/spec-analyze`.
5. Implement task by task using `/spec-implement`.
6. Review implementation against the spec using `/spec-review`.
7. Run QA review using `/qa-review`.
8. Run database review using `/database-review` if the change touches schema, migrations, entities, repositories, queries, indexes or persistence.
9. Run security review using `/security-review` if the change touches authentication, authorization, user data, tenant isolation, public APIs, file uploads, tokens, secrets or sensitive data.
10. Run performance review using `/performance-review` if the change touches data-heavy queries, rendering loops, list screens, caching, or async processing.
11. Run API review using `/api-review` if the change adds, modifies, or removes API endpoints, DTOs, or public contracts.
12. Close the feature using `/spec-close`.
13. Generate a PR description using `/pr-description`.

## When to use

Use this workflow for:

- Ambiguous requirements.
- Large features.
- Backend flows with business logic.
- Database changes.
- Migrations.
- Authentication.
- Authorization.
- Tenant isolation.
- Public APIs.
- File uploads.
- Sensitive data.
- External integrations.
- Architectural changes.

## Behavior

When invoked:

1. Ask the user for the feature description if it was not provided.
2. Identify whether database review is likely needed.
3. Identify whether security review is likely needed.
4. Identify whether performance review is likely needed.
5. Identify whether API review is likely needed.
6. Identify whether backend review is likely needed.
7. Identify whether frontend review is likely needed.
8. Recommend the exact next command to run.
9. Do not implement code directly.
10. Do not skip clarification or analysis.
11. Keep the workflow practical for a solo developer.

## Output format

# SDD Full Workflow

## Recommended workflow

## Database review needed

Yes | No | Maybe

## Security review needed

Yes | No | Maybe

## Performance review needed

Yes | No | Maybe

## API review needed

Yes | No | Maybe

## Backend review needed

Yes | No | Maybe

## Frontend review needed

Yes | No | Maybe

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
