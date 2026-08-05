# Project Changes: `<feature name>`

> Template for `.sdd-workspace/specs/features/<slug>/PROJECT_CHANGES.md`. What **actually** changed,
> per project. See [`../WORKSPACE_SDD.md`](../WORKSPACE_SDD.md).

**Feature:** `<NNN>-<slug>`
**Last updated:** `YYYY-MM-DD`

Filled in **during and after** implementation, from what landed — not from what was planned. The
plan lives in `IMPACT_MAP.md`; this is the record.

## Changes

| Project | Change | Files/areas | Contract impact | Tests |
|---|---|---|---|---|
| `backend-api` | Accept and persist optional `consent` on lead creation | `LeadController`, `Lead` entity, migration `V12__consent.sql` | `POST /v1/leads` — additive optional field, non-breaking | `LeadControllerTest` (+3), migration test |
| `shared-sdk` | Pass `consent` through the create-lead call | `src/leads.ts`, types | npm `@acme/sdk` 2.5.0 — additive | `leads.spec.ts` (+2) |
| `<project>` | `<what changed, in one line>` | `<files or areas — not a full diff>` | `<contract + breaking or not, or "none">` | `<what was added/updated and how many>` |

**Column meanings**

- **Change** — the behavioural change, not the commit message.
- **Files/areas** — enough to locate the change. Whole-diff dumps belong in the diff.
- **Contract impact** — name the contract from `INTEGRATION_CONTRACTS.md` and say whether it is
  breaking. `none` is a valid, meaningful answer.
- **Tests** — what was added or updated. "Existing tests still pass" is not a row entry; it is
  `VALIDATION.md`'s job.

## Projects not changed

Confirmation that the boundary held.

| Project | Listed as | Touched? |
|---|---|---|
| `<project>` | Unaffected | No |
| `<project>` | Unaffected | No |

> If any project was touched that `IMPACT_MAP.md` did not list as affected, record it here **and**
> say when the map was amended and re-approved. An unrecorded out-of-map change is a guardrail
> violation, not a footnote.

## Contract updates landed

| Contract | Updated in `INTEGRATION_CONTRACTS.md` | Before dependent implementation? |
|---|---|---|
| `<contract>` | `YYYY-MM-DD` | `Yes` / `No — explain` |

## Deviations from the plan

| Planned | Actual | Why |
|---|---|---|
| `<what IMPACT_MAP.md said>` | `<what happened>` | `<reason, and whether it was approved>` |

## Follow-ups

Work deliberately left undone. Each needs a home — a project spec, a new workspace feature, or an
explicit "won't do".

| Item | Project | Where it is tracked |
|---|---|---|
| `<item>` | `<project>` | `<spec path or "not tracked — accepted">` |
