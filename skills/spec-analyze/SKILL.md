---
name: spec-analyze
description: Analyze consistency between SPEC.md, PLAN.md, TASKS.md and DECISIONS.md before implementation. Use this to detect missing coverage, contradictions, weak tasks and readiness issues. Not for producing PLAN/TASKS/DECISIONS — use /spec-plan.
---

## SDD Contract

```yaml
category: lifecycle
inputs: [SPEC.md, PLAN.md, TASKS.md, DECISIONS.md]
outputs: [consistency-report]
side_effects: none
writes_code: false
writes_specs: false
analysis_only: true
primary_agent: solution-architect
secondary_agents: [final-conformance-reviewer]
profile_scope: all
provider_specific: false
```

You are working in Spec-Driven Development mode.

Your task is to analyze the SDD documents before implementation.

## Core rules

- Do not implement production code.
- Do not modify application code unless explicitly requested.
- **Do not change `SPEC.md`'s `Status`.** This skill returns a readiness verdict; acting on that verdict by promoting `Draft` → `Ready` is `/spec-plan`'s job. A "Ready" verdict here is not a `Ready` status. See `sdd-guardrails` section 11.
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
- Does the plan declare a Context budget (bounded reading list + model routing)? See the "Context budget check" rule below.
- Does every task carry a `Verify:` clause once `TASKS.md` has adopted the format? See the "Verify clause check" rule below.
- Is the next implementation task clear?

## Context budget check

The token economy contract (`docs/TOKEN_ECONOMY.md`) requires each `PLAN.md` to
declare a `## Context budget` section with a bounded `Reading list` and a
`Model routing` note. Apply this rule:

- **Section missing entirely → warning, not a blocker.** Report it under
  "Context budget" in the output, but the verdict may still be `Ready`. This
  keeps plans authored before the rule (and trivial plans) passing.
- **Section present but empty or still holding placeholder text → blocker.**
  The verdict cannot be `Ready`; treat it like an unmet acceptance criterion.
- A valid budget can be short (even one line per subsection). Accept brevity;
  reject only emptiness or unfilled template text.

## Verify clause check

`specs/_templates/TASKS.md` fixes a `Verify:` clause after `Covers:` on every task line: the
criterion anyone checks to call the task done. `TASKS.md` files written before that syntax existed
carry none, and must keep passing unchanged. The criterion may be an executable command or a human
check; nothing in the framework executes it — it is text for a human or an agent to act on, not a
runner input. Apply this rule:

- **Detection unit is the task item, not a line or the raw file.** A task item is a bullet
  beginning `- [ ]` or `- [x]` together with its continuation lines, up to the next bullet. Within
  that item, the clause is the one following `Covers:` — it may sit on the bullet's own line or
  wrap onto a continuation line. Do not match a raw substring of the file (a clause named in prose,
  not stated as a task's own criterion, does not count) and do not match a single physical line
  (a clause that wrapped past the bullet's first line still counts).
- **No task item in the file carries a clause → legacy, passes untouched.** Report nothing; this is
  not a coverage gap.
- **At least one task item carries a clause → the file has adopted the format.** Every task item
  must then carry one. A task item with no `Verify:` at all, or with `Verify:` followed by nothing,
  is a blocking finding naming that task; the verdict cannot be `Ready` while one remains.
- **A human check must name who checks and against what.** A blanket phrase with no reviewer and
  no standard to check against — "Verify: reviewed by hand" and nothing else — does not state a
  criterion. Treat it the same as a missing or empty clause: a blocking finding naming that task.
- **A present, named criterion is also checked against FR-008's observability test — warning, not
  a blocker.** An observable criterion names what is inspected (a command, a file, an output, a
  recorded run), would produce the same verdict for two different checkers, and can fail. A
  criterion missing any of the three — "tests pass" names nothing to inspect, "is correct" is not
  verdict-stable, "code is written" cannot fail — is a warning naming the task and which test it
  failed; it does not block the verdict.

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

## Context budget

Filled | Missing (warning) | Empty/placeholder (blocker) — with a one-line reason. Per the Context budget check rule.

## Verify clauses

Legacy (no task carries one — passes) | Adopted, complete | Adopted, missing on: <task IDs> (blocker). Per the Verify clause check rule.

Observability warnings: none | <task ID>: fails <inspection target | verdict-stable | falsifiable>. Per the observability check rule (warning, not a blocker).

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
