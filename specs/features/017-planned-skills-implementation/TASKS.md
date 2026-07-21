# TASKS — 017 Implement planned skills and wire them into the review flow

- [x] T01 Study house formats (stack reviewer: `java-performance-reviewer`; SEO family + billable gating: `seo-review` / `frontend-review` SERVICES.md pattern; routing points: `/sdd` review detection, `/review-all`)
- [x] T02 `observability-reviewer` (extends backend-review; logging/PII, correlation+tracing, Micrometer, actuator, alert-readiness)
- [x] T03 `stripe-payments-reviewer` (extends security+backend; raw-body signature, event dedup, idempotency keys, minor units, key/API-version hygiene, lifecycle)
- [x] T04 `payment-idempotency-reviewer` (extends backend+database; replay matrix, atomic dedup, concurrency guards, constraints as last defense, outbox)
- [x] T05 `prisma-migration-reviewer` (extends database-review; generated-SQL reading, rename=DROP trap, required-column backfills, enum/relation changes, migrate-vs-push, CONCURRENTLY, no down migrations)
- [x] T06 `nextjs-server-actions-reviewer` (extends security+backend; action=public endpoint, per-action authz, zod at boundary, server/client seam, revalidation, redirect-outside-try/catch)
- [x] T07 `aeo-review` / T08 `geo-review` / T09 `ai-visibility-review` (seo-review house format + SERVICES.md billable gating + upsell fallback; chained seo → aeo → geo → ai-visibility)
- [x] T10 profiles.json: all 8 promoted planned→skills; plannedSkills now `[]` everywhere; notes updated (payments-fintech no longer "Nothing shipped yet")
- [x] T11 Wiring: `/sdd` profile-gated detection lines; `/review-all` stack-reviewer routing table (covers pre-existing stack reviewers too — closed that gap); `/seo-review` next-command chain to siblings
- [x] T12 README: table rows for next-prisma-web/seo-geo-addon/payments-fintech rewritten; counts via `check-consistency.sh --fix` (53→61 skills, java profile 7→8); stale "all 52"/"planned-only" prose fixed
- [x] T13 CHANGELOG `[Unreleased]` entry (specs 016–017)
- [x] T14 Verification: `check-consistency.sh` PASS; all 4 self-tests PASS (24+66+5+7); install with all 5 profiles ships the 8 skills to central; `sdd`/`review-all` synced to central with backup
- [ ] T15 (User) Review the 8 skill checklists for domain accuracy; commit (no commits made — audit constraint)
- [ ] T16 (Future) plannedHooks remain planned: `openapi-contract-reminder`, `messaging-review-reminder`, `stripe-review-reminder`, `prisma-migration-guard`; plannedTemplate `OBSERVABILITY.md`
