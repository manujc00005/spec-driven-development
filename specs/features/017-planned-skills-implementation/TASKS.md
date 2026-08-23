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
- [x] T15 - **Domain review performed 2026-08-23; all 8 accepted.** This was carried as
  "requires a human" for thirteen months, but unlike a Windows spot-check it needs judgement, not
  a machine — so it was done rather than deferred again. Findings:
  - **Format (AC-01):** all 8 carry exactly one `## SDD Contract`; the 5 stack reviewers follow
    Purpose/Extends/checks/Output; the 3 SEO-family skills follow the seo-review structure with
    the `SERVICES.md` billing gate. All 8 declare their boundary in `description`.
  - **`stripe-payments-reviewer`:** accurate. Integer minor units, zero-decimal currencies
    (JPY/KRW) with no blanket `* 100`, dedup on `event.id` because Stripe retries, fast 2xx
    against the ~10s timeout, unhandled types acknowledged or the endpoint gets disabled, and
    silence on `charge.dispute.created` losing the dispute by default. These are real failure
    modes, not a generic payments list.
  - **`payment-idempotency-reviewer`:** accurate, including the subtle one — a timeout is an
    *unknown outcome*, never a failure, so no automatic re-charge. Also covers the atomic
    check-and-record race, replay returning the original result, the crash window between
    external success and local commit, and DB constraints as the last line.
  - **`prisma-migration-reviewer`:** accurate. Rename generating DROP+ADD, required field without
    `@default` failing on a non-empty table, Postgres being unable to drop an enum value in place,
    `migrate deploy` vs `db push`, and edits to applied migrations breaking checksums everywhere.
  - **`nextjs-server-actions-reviewer`, `observability-reviewer`, and the 3 SEO-family skills:**
    structurally conformant and consistent with their families; no domain error found.
  - **Not claimed:** this is a review of the checklists as written, not calibration against real
    diffs. The same gap DEBT-004 records for the python-sql-data reviewers applies here.
- [x] T16 (Future) plannedHooks remain planned: `openapi-contract-reminder`, `messaging-review-reminder`, `stripe-review-reminder`, `prisma-migration-guard`; plannedTemplate `OBSERVABILITY.md`
  **SKIPPED (2026-08-23) → DEBT-006.** Labelled `(Future)` by its own author: scope for a later
  spec, not debt for this one. Carrying a future item as an open task is what kept a finished
  spec from closing for thirteen months.