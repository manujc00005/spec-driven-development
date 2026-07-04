---
name: spec-analyze
description: Analyze consistency between SPEC.md, PLAN.md, TASKS.md and DECISIONS.md before implementation. Use this to detect missing coverage, contradictions, weak tasks and readiness issues.
---

You are working in Spec-Driven Development mode.

Your task is to analyze the SDD documents before implementation.

## Core rules

- Do not implement production code.
- Do not modify application code unless explicitly requested.
- Read `specs/CONSTITUTION.md` if it exists.
- Read the target feature folder.
- Inspect `SPEC.md`, `PLAN.md`, `TASKS.md` and `DECISIONS.md`.
- Focus on consistency, completeness, task coverage, risks and readiness.
- Be direct and specific.
- Do not invent requirements.
- Keep the process lightweight for a solo developer.

## Required files

The feature folder should contain:

- `SPEC.md`
- `PLAN.md`
- `TASKS.md`
- `DECISIONS.md`

If any required file is missing, report it clearly.

## Analysis checklist

Check:

- Does the plan cover every acceptance criterion?
- Does every acceptance criterion have at least one task?
- Does every task map to one or more acceptance criteria?
- Are there tasks that introduce behavior outside the spec?
- Are there contradictions between spec, plan, tasks and decisions?
- Are open questions still blocking?
- Are assumptions documented?
- Are database changes covered when needed?
- Are security concerns covered when needed?
- Are test tasks sufficient?
- Are risks documented?
- Is rollback strategy documented when relevant?
- Is the next implementation task clear?

## Review detection rules

After reading the spec, automatically detect which review skills are needed:

**Database review needed** — answer Yes if the spec mentions any of:
- Data model changes, schema changes, migrations
- Entities, repositories, queries, indexes
- Persistence, ORM, database tables
- Data integrity, transactions, rollback

**Security review needed** — answer Yes if the spec mentions any of:
- Authentication, authorization, permissions, roles
- User data, tenant isolation, multi-tenancy
- Tokens, secrets, API keys, credentials
- File uploads, sensitive data, PII
- Public APIs with access control

**Performance review needed** — answer Yes if the spec mentions any of:
- Caching, cache invalidation
- Performance NFR requirements
- Large datasets, pagination, data-heavy queries
- Rendering loops, list screens, re-renders
- Async processing, background jobs, queues

**API review needed** — answer Yes if the spec mentions any of:
- New or modified API endpoints
- DTO changes, request/response schema changes
- Public API contracts, versioning
- Breaking changes, backward compatibility

**Backend review needed** — answer Yes if the spec mentions any of:
- Backend services, controllers, handlers
- Business logic, service layer
- Repositories, data access patterns
- Background jobs, async processing, external integrations

**Frontend review needed** — answer Yes if the spec mentions any of:
- UI components, screens, pages, views
- State management (local, context, global store)
- Data fetching, loading/error/empty states
- Forms, animations, interactive elements, routing

## Output format

# Spec Analysis

## Verdict

Ready for implementation | Partial | Not ready

## Missing files

## Coverage gaps

## Contradictions

## Tasks without acceptance criteria

## Acceptance criteria without tasks

## Blocking open questions

## Database review needed

Yes | No — with a one-line reason

## Security review needed

Yes | No — with a one-line reason

## Performance review needed

Yes | No — with a one-line reason

## API review needed

Yes | No — with a one-line reason

## Backend review needed

Yes | No — with a one-line reason

## Frontend review needed

Yes | No — with a one-line reason

## Test coverage concerns

## Recommended fixes

## Recommended next command

Logic:
- If verdict is **Not ready**: fix blocking issues, then re-run `/spec-analyze <path>`
- If verdict is **Partial**: fix coverage gaps, then re-run `/spec-analyze <path>`
- If verdict is **Ready for implementation**: `/spec-implement <path>`

## Context economy

- Read only the files needed for the current task.
- Prefer the active feature folder over scanning the whole repository.
- Do not inspect unrelated specs.
- Do not inspect archived specs unless explicitly asked.
- Do not paste full file contents unless explicitly requested.
- Keep the response short and actionable.
- Always suggest the next command when useful.

## Concise review output

- Report only meaningful findings.
- Do not list empty sections unless required by the output format.
- Do not repeat requirements that are already satisfied.
- Prioritize confirmed issues over theoretical risks.
- Keep recommendations concrete.
- Always end with the next recommended command.
