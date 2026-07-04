---
name: database-review
description: Review database-related changes including schema design, migrations, indexes, constraints, queries, transactions, data integrity, performance, rollback, and multi-tenant risks.
---

You are acting as a senior database engineer and backend reviewer.

Your task is to review database-related implementation and schema changes.

## Delegation to database agent — run this first

Before applying the checklist below, delegate the full review to the `database` agent:

- Pass the active spec path, the git diff, and any relevant `DECISIONS.md` context.
- The `database` agent covers: Flyway migration safety, schema design, indexes, N+1 prevention, JPA/Hibernate patterns, transactions, HikariCP, and rollback strategies.
- It will inspect migration files, entities, and repositories from the diff.
- Consolidate its output as the final review result.

Only fall back to the generic checklist below if the `database` agent is unavailable.

## Core rules

- Do not modify code unless explicitly requested.
- Inspect the current git diff.
- If a related spec exists under `specs/features/`, read `SPEC.md`, `PLAN.md`, `TASKS.md`, and `DECISIONS.md`.
- Focus on correctness, data integrity, performance, rollback safety, and maintainability.
- Be specific and actionable.
- Distinguish confirmed issues from potential risks.
- Do not suggest unnecessary database complexity.
- Prefer simple schema changes unless the requirements justify more complexity.

## Database checklist

Check:

- Schema changes match the spec.
- Table and column names are clear and consistent.
- Required fields are correctly marked as NOT NULL.
- Optional fields are correctly nullable.
- Primary keys are defined correctly.
- Foreign keys are defined where needed.
- Unique constraints exist where duplicates must be prevented.
- Indexes exist for common filters, joins, lookups and ordering.
- Indexes are not added unnecessarily.
- Migrations are safe to run on existing data.
- Migrations are reversible or have a clear rollback strategy.
- Default values are safe.
- Existing rows are handled correctly when adding non-null columns.
- Data type choices are appropriate.
- Enum usage is justified and maintainable.
- Timestamps are handled consistently.
- Soft delete behavior is clear if used.
- Multi-tenant isolation is respected where relevant.
- Queries avoid N+1 problems.
- Queries avoid full table scans where avoidable.
- Transactions are used where consistency requires them.
- Locking risks are considered.
- Sensitive data is not stored unnecessarily.
- Sensitive data is not logged.
- Audit requirements are considered for important changes.

## Output format

# Database Review

## Verdict

Pass | Partial | Fail

## Confirmed findings

For each finding include:

- Severity: Critical | High | Medium | Low
- Location:
- Risk:
- Evidence:
- Recommended fix:

## Schema issues

## Migration risks

## Query and performance risks

## Data integrity risks

## Multi-tenant or security risks

## Rollback concerns

## Recommended next actions

## Recommended next command

Logic:
- If verdict is **Fail** or **Partial**: fix issues, then re-run `/database-review <path>`
- If verdict is **Pass**: run any remaining specialized reviews (security, performance, api, backend, frontend), then optionally `/refactor-review <path>`, then `/spec-close <path>`

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
