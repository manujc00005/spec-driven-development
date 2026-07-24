---
name: review-all
description: Run all applicable specialized reviews in one command. Detects which reviews are needed from the spec and runs them sequentially, producing a consolidated report.
---

## SDD Contract

```yaml
category: orchestration
inputs: [SPEC.md, git-diff]
outputs: [consolidated-review-report]
side_effects: none
writes_code: false
writes_specs: false
analysis_only: true
primary_agent: orchestration-context
secondary_agents: []
profile_scope: all
provider_specific: false
```

You are acting as a senior multi-domain code reviewer.

Your task is to detect which specialized reviews apply to this feature and run them all in sequence, producing a single consolidated report.

## Core rules

- Do not modify code unless explicitly requested.
- Read the spec to detect which reviews are needed.
- Inspect the current git diff.
- Run every applicable review checklist in sequence.
- Produce one consolidated report — do not repeat findings across sections.
- Rate issues by severity: Critical | High | Medium | Low.
- Be specific and actionable. Every issue must cite a file:line reference.

## Active feature context

If no path is provided, use the most recently referenced feature path from the conversation. If none found, ask the user.

## Detection rules

Run a review section if the spec mentions:

- **Database**: schema changes, migrations, entities, repositories, persistence, ORM
- **Security**: auth, authorization, user data, tokens, file uploads, PII, secrets
- **Performance**: caching, NFR performance, large datasets, rendering loops, async jobs
- **API**: new/modified endpoints, DTOs, public contracts, versioning
- **Backend**: services, controllers, business logic, repositories, background jobs
- **Frontend**: UI components, screens, state management, forms, frontend flows

## Stack-specific reviewer routing

After the generic checklists, route to the specialized reviewers below when their skill is
installed and their condition matches. Do not inline their checklists here — invoke the skill
(each extends a generic review and assumes it already ran):

| Reviewer | Route when |
|---|---|
| `/java-spring-reviewer` | Java/Spring project and Backend was detected |
| `/spring-boot-api-reviewer` | Java/Spring project and API was detected |
| `/spring-security-reviewer` | Java/Spring project and Security was detected |
| `/java-performance-reviewer` | Java/Spring project and Performance was detected |
| `/observability-reviewer` | Java/Spring project and the diff touches logging, metrics, tracing, actuator, or adds a service/consumer/job |
| `/event-driven-reviewer` | diff touches producers, consumers, topics, or event contracts |
| `/microservices-patterns-reviewer` | change crosses service boundaries or event contracts |
| `/stripe-payments-reviewer` | diff touches Stripe SDK calls, payment webhooks, or checkout/billing |
| `/payment-idempotency-reviewer` | spec mentions payments, refunds, wallets, credits, or ledgers |
| `/prisma-migration-reviewer` | diff touches `prisma/schema*` or `prisma/migrations/` |
| `/nextjs-server-actions-reviewer` | diff touches `"use server"` files or App Router route handlers |
| `/seo-review` + siblings (`/aeo-review`, `/geo-review`, `/ai-visibility-review`) | public pages changed — each only if contracted in `specs/SERVICES.md` (uncontracted → upsell entry, skip) |

## Review process

1. Read the spec and detect which review types apply.
2. Read the git diff once — use it for all review sections.
3. For each applicable review type, run through its checklist.
4. Collect all findings across all review types.
5. Produce the consolidated report below.

## Review checklists

Apply only the sections that are detected as needed.

### Database checklist
- Schema changes match the spec.
- Migrations are safe to run on existing data and reversible.
- Indexes exist for common filters, joins, and lookups.
- Queries avoid N+1 and full table scans.
- Transactions used where consistency requires them.
- Multi-tenant isolation respected.
- Sensitive data not stored or logged unnecessarily.

### Security checklist
- Authentication required where needed.
- Authorization enforced server-side.
- Input validation for untrusted data.
- No SQL/command injection risks.
- File uploads validate type, size, content, storage path.
- Tokens and secrets not logged or committed.
- Errors do not leak internal details.
- Rate limiting considered for sensitive flows.

### Performance checklist
- No N+1 query patterns.
- No unbounded queries on large datasets.
- No unnecessary re-renders or unstable references.
- Heavy computations memoized or moved outside render.
- Lists use stable keys and virtualization where needed.
- No synchronous blocking calls in async contexts.

### API checklist
- No breaking changes to existing endpoints or DTOs.
- Required vs optional fields correctly modeled.
- HTTP status codes semantically correct.
- Error responses consistent and safe.
- Naming conventions consistent with existing API.

### Backend checklist
- Business logic not leaking into controllers or repositories.
- Edge cases handled: empty results, nulls, concurrent updates.
- Errors propagated correctly, not swallowed.
- No hardcoded secrets or environment-specific values.
- Dependencies injected, not hardcoded.

### Frontend checklist
- Loading, error, and empty states all handled per spec.
- No unnecessary re-renders (missing memoization, unstable refs).
- Async state handles race conditions.
- Interactive elements keyboard accessible.
- No content distinguished only by color.

## Output format

# Review All: <feature-name>

## Reviews run

List which review types were detected and run.

## Consolidated verdict

Pass | Partial | Fail

## Findings

For each finding (grouped by severity, not by review type):

**Critical / High / Medium / Low**
- Location: `file.ts:line`
- Type: Database | Security | Performance | API | Backend | Frontend
- Issue:
- Fix:

## Skipped reviews

List review types not applicable and why.

## Recommended next command

Logic:
- If verdict is **Fail** or **Partial**: fix issues, then re-run `/review-all <path>`
- If verdict is **Pass**: optionally `/refactor-review <path>`, then `/spec-close <path>`

## Context economy

- Read the spec once for detection.
- Read the git diff once for all checklists.
- Do not re-read files between review sections.
- Report only meaningful findings.
- Do not list empty sections.
- Always end with the next recommended command.
