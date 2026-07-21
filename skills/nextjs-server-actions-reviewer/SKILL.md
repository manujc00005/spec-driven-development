---
name: nextjs-server-actions-reviewer
description: Review Next.js Server Actions and Route Handlers as the public attack surface they are — per-action auth, input validation at the boundary, secret leakage across the server/client seam, cache revalidation correctness, and redirect/error semantics. Extends security-review and backend-review.
triggers:
  - After `/security-review` when files with `"use server"` or `app/**/route.ts` handlers change
  - When a form, mutation, or data-write flow is added to a Next.js App Router project
  - When the user asks to "review the server action" or "check this form flow"
  - Triggered by `/review-all` when the spec mentions server actions, mutations, or form submissions
---

# Next.js Server Actions Reviewer

## Purpose

Every exported server action is a **public, unauthenticated POST endpoint** — the framework hides
the HTTP, and with it the instincts developers apply to controllers. This skill **extends**
`security-review` (generic auth/injection) and `backend-review` (logic): run those first; this
pass covers the seams specific to the App Router server/client boundary.

## Extends

- **Skills:** `security-review`, `backend-review`
- **Subagent:** `nextjs-prisma` (App Router, RSC boundary model)

## What this skill checks (beyond the generic reviews)

### Actions are endpoints

- **Every** exported action re-checks auth and authorization itself — page-level checks protect
  the page, not the action; anyone can invoke the action directly with a crafted request.
- Authorization uses server-side identity (session/cookie), never IDs or role fields from the
  submitted form data (`formData.get("userId")` for access control is a takeover).
- Actions exported from a `"use server"` **file** are ALL exposed — helper functions in that file
  that shouldn't be endpoints must move out or not be exported.

### Input validation at the boundary

- Arguments and `FormData` are parsed through a schema (zod or equivalent) **inside** the action,
  before any use — TypeScript types are erased at runtime and validate nothing.
- Unexpected/extra fields are stripped (no `...spread` of parsed input into ORM calls —
  mass-assignment via Prisma `data:` object).
- Bound arguments (`.bind(null, id)`) are treated as untrusted too — they arrive from the client.

### The server/client seam

- Values returned from actions to client components are serialized and visible — no secrets,
  internal error objects, or full DB entities in return values; return DTOs.
- No secret-bearing module (`process.env.*`, DB clients) imported into client components; the
  `server-only` package marks the sensitive modules where the codebase uses it.
- Error messages returned to the client are user-safe; stack traces and query details stay in
  server logs.

### Cache and revalidation

- Mutations revalidate what they change: `revalidatePath`/`revalidateTag` present and targeting
  the right scope — a successful write that leaves stale cached reads is a correctness bug.
- No over-broad `revalidatePath("/", "layout")` as a habit — flag when a narrower tag exists.
- `redirect()` is called **outside** try/catch (it throws by design) — a catch block swallowing
  the redirect error is a classic silent bug.

### Abuse resistance

- Actions that send email, create records, or call paid APIs have rate limiting or are flagged
  as missing it (per-IP or per-user, per the project's existing limiter).
- Long-running work is not awaited inline past the response the user needs — defer to a queue
  where one exists.

## Output format

```markdown
## Server Actions Review

**Verdict:** PASS | PASS WITH NOTES | FAIL

### Action inventory

| Action | Auth inside? | Validated input? | Revalidation | Verdict |
|---|---|---|---|---|
| `createOrder` | yes (session) | zod schema | `revalidateTag('orders')` | OK |

### Findings

| # | Category | Severity | File:Line | Finding | Action |
|---|---|---|---|---|---|

### Recommendations

- (Non-blocking hardening)
```

## What this skill does NOT do

- Does not review generic injection/secrets/header security (that's `security-review`).
- Does not review UI states or rendering (that's `frontend-review`).
- Does not review Prisma migrations (that's `prisma-migration-reviewer`).
- Does not modify code.
