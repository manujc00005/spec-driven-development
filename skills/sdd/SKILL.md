---
name: sdd
description: Auto-detect feature complexity and guide the right SDD workflow. Main entry point for any non-trivial feature — replaces sdd-medium and sdd-full.
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

You are guiding a Spec-Driven Development workflow.

Your task is to analyze the feature description, detect its complexity, and recommend the correct workflow and first command.

## Bootstrap check (before anything else)

Check that `specs/CONSTITUTION.md` exists. If it does not, the project has never been initialized: stop and recommend running `/project-init` first — it scaffolds the full `specs/` structure (CONSTITUTION.md, README.md, SDD-GUARDRAILS.md, CLAUDE-SDD.md, features/) that every later step depends on. Do not proceed to complexity detection in an uninitialized project.

## Complexity detection

Choose **full workflow** if the feature involves any of:
- Authentication, authorization, or user sessions
- User data, tenant isolation, or multi-tenancy
- Database schema changes, migrations, or new entities
- Public APIs, external integrations, or third-party services
- File uploads or storage
- Secrets, tokens, or credentials
- Significant ambiguity or unclear requirements
- Large architectural changes or cross-cutting concerns

Choose **medium workflow** if the feature:
- Has clear requirements and limited scope
- Does not touch security-sensitive areas
- Does not require complex database changes
- Has no significant ambiguity

## Review detection

After choosing the workflow, identify which specialized reviews will likely be needed:

- **Database review**: spec mentions schema, migrations, entities, repositories, persistence
- **Security review**: spec mentions auth, user data, tokens, file uploads, PII, secrets
- **Performance review**: spec mentions caching, NFR, large datasets, rendering loops, async jobs
- **API review**: spec mentions new/modified endpoints, DTOs, public contracts, versioning
- **Backend review**: spec mentions services, controllers, business logic, repositories
- **Frontend review**: spec mentions UI components, screens, state, forms, frontend flows

Stack/profile reviewers (detect only if the skill is installed — they extend the generic ones above):

- **Payments** (`/stripe-payments-reviewer`, `/payment-idempotency-reviewer`): spec mentions payments, checkout, Stripe, webhooks, refunds, wallets, credits, ledgers
- **Prisma migrations** (`/prisma-migration-reviewer`): spec mentions Prisma schema or migrations, or the diff touches `prisma/`
- **Server actions** (`/nextjs-server-actions-reviewer`): spec mentions server actions, mutations, or form submissions in a Next.js App Router project
- **Observability** (`/observability-reviewer`): spec mentions logging, metrics, tracing, health checks, or adds a service/consumer/job that must be operable
- **SEO family** (`/seo-review` → `/aeo-review` → `/geo-review` → `/ai-visibility-review`): public pages changed — each step only if that service is contracted in `specs/SERVICES.md`

## Medium workflow (8 steps)

1. `/spec-create` — creates spec with auto-clarify pass
2. `/spec-plan`
3. `/spec-analyze`
4. `/spec-implement` — repeat until all tasks done
5. `/spec-review`
6. `/qa-review`
7. `/spec-close`
8. `/pr-description`

## Full workflow (9+ steps)

1. `/spec-create` — creates spec with auto-clarify pass
2. `/spec-plan`
3. `/spec-analyze`
4. `/spec-implement` — repeat until all tasks done
5. `/spec-review`
6. `/qa-review`
7. Specialized reviews as detected (database, security, performance, api, backend, frontend)
8. `/spec-close`
9. `/pr-description`

## Behavior

When invoked:

1. Ask for feature description if not provided.
2. Detect complexity using the rules above.
3. Identify which specialized reviews will likely be needed.
4. Show the selected workflow, the steps, and detected reviews.
5. **Immediately proceed** through the following chain without waiting for the user:
   a. Run spec-create behavior (create SPEC.md, apply auto-clarify pass)
   b. If blocking questions arise → stop, present them, wait for answers
   c. If no blocking questions → immediately run spec-plan behavior (create PLAN.md, TASKS.md, DECISIONS.md)
   d. Immediately run spec-analyze behavior (verify consistency and coverage)
   e. If spec-analyze is Ready → present: "Ready to implement. First task: T001 — [description]. Run `/spec-implement` to start, or `/spec-implement all` to implement all tasks in sequence."
   f. If spec-analyze is Partial/Not ready → present blocking issues and stop
6. Do not implement production code in this chain.
7. The entire pre-implementation chain runs in a single response unless blocked.

## Output format

# SDD

## Workflow selected

Medium | Full — one-line reason

## Specialized reviews likely needed

List which apply and why. If none, write "None detected."

## Workflow steps

[show the relevant step list]

## First command to run

`/spec-create <feature description>`

## Context economy

- Keep output short and actionable.
- Show the workflow steps and the next command.
- Do not explain the full SDD concept.
- Do not implement code directly.
- Always end with the first command to run.
