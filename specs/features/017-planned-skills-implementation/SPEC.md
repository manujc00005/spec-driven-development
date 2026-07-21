# SPEC — 017 Implement planned skills and wire them into the review flow

## Goal

Promote every `plannedSkills` entry in `profiles.json` to a shipped skill and
wire each one into the correct stage of the SDD review flow. After this spec,
`payments-fintech` stops being an empty overlay and no profile ships
aspirational skill names.

## Scope — the 8 planned skills

| Skill | Profile | Extends / family | Stage |
|---|---|---|---|
| `observability-reviewer` | java-spring-backend | extends `backend-review` | after backend-review, features touching logs/metrics/traces/actuator |
| `stripe-payments-reviewer` | payments-fintech | extends `security-review` + `backend-review` | after security-review on Stripe-touching diffs |
| `payment-idempotency-reviewer` | payments-fintech | extends `backend-review` + `database-review` | after backend-review on money-movement flows |
| `prisma-migration-reviewer` | next-prisma-web | extends `database-review` | after database-review when `prisma/` changes |
| `nextjs-server-actions-reviewer` | next-prisma-web | extends `security-review` + `backend-review` | after security-review when server actions change |
| `aeo-review` | seo-geo-addon | sibling of `seo-review`, **billable** | after seo-review, only when contracted in SERVICES.md |
| `geo-review` | seo-geo-addon | sibling of `seo-review`, **billable** | after seo-review, only when contracted in SERVICES.md |
| `ai-visibility-review` | seo-geo-addon | sibling of `seo-review`, **billable** | after seo-review, only when contracted in SERVICES.md |

`plannedHooks` (openapi-contract-reminder, messaging-review-reminder,
stripe-review-reminder, prisma-migration-guard) are **out of scope** — hooks
stay planned.

## Acceptance criteria

- **AC-01** Each of the 8 skills exists as `skills/<name>/SKILL.md` following the
  house format of its family (stack reviewer: triggers/Purpose/Extends/checks/
  Output/NOT-do; SEO family: seo-review structure + SERVICES.md contract gating).
- **AC-02** `profiles.json` lists them under `skills` (removed from
  `plannedSkills`, which become empty arrays — nothing else changes).
- **AC-03** Flow wiring: `/sdd` review-detection covers the new dimensions;
  `/review-all` gains a stack-specific reviewer routing table (covering the
  pre-existing stack reviewers too — closing that gap); `/seo-review` points to
  its new siblings under the same contract gate.
- **AC-04** README profile table stops saying "planned"/"Nothing shipped yet";
  `scripts/check-consistency.sh` passes (count markers via `--fix`).
- **AC-05** All self-tests pass; re-running `install.sh` with all profiles
  ships the new skills to the central dir.
- **AC-06** No commits (user constraint).
