# Tasks: Phase 0 — Publish-ready baseline

> **Backfill note (2026-07-13, Phase 5).** This feature predates the repo's full SDD
> lifecycle discipline — it shipped (commit `cdb0f67`) with only SPEC.md + PLAN.md. This
> TASKS.md was reconstructed afterwards from the spec's FRs and the shipped artifacts, as
> part of `005-framework-hardening-and-cross-platform-polish` (see its D006/D007). It is an
> honest record of what was delivered, not a contemporaneous task log.

- [x] T001 — Add MIT `LICENSE` at repo root. Covers: AC-001.
- [x] T002 — Fix README contradictions (INSTALL.md existence, Maven default, Graphify
      planned, blockchain disabled). Covers: AC-002.
- [x] T003 — Create `hooks/git-guardrails.sh` with pattern parity to the `.ps1` variant.
      Covers: AC-003.
- [x] T004 — Create `specs/_templates/PR_DESCRIPTION.md`. Covers: AC-004.
- [x] T005 — Create `specs/_templates/REVIEW_REPORT_TEMPLATE.md`. Covers: AC-005.
- [x] T006 — Create `profiles.json` declaring all six profiles, Maven primary. Covers: AC-006.
- [x] T007 — Secret/PII/path scan over new files. Covers: AC-007.

## Verification (performed 2026-07-13, Phase 5 close)

- AC-001 ✓ `LICENSE` is MIT, 2026, author name present.
- AC-002 ✓ current `README.md` (since rewritten) documents `docs/INSTALL.md`, Maven as the
  java profile's primary build tool, Graphify as optional/external, blockchain as disabled.
- AC-003 ✓ `git-guardrails.sh` blocks the same pattern set as `.ps1` (verified by side-by-side
  read); exits 0 on safe commands. The executable bit was **missing in the git index**
  (100644) from Phase 0 until 2026-07-13, when it was fixed via `git add --chmod=+x`
  (005/D007) — recorded honestly rather than claimed as always-true.
- AC-004 ✓ `PR_DESCRIPTION.md` has Summary/Changes/Tests/Migrations/Risks (plus Deployment
  notes, Related).
- AC-005 ✓ `REVIEW_REPORT_TEMPLATE.md` has Verdict, Findings (severity/File:Line), Evidence,
  Required actions.
- AC-006 ✓ `profiles.json` declares `core`, `java-spring-backend` (default),
  `messaging-event-driven`, `payments-fintech`, `next-prisma-web`, `blockchain-crypto`
  (disabled); Maven primary.
- AC-007 ✓ secret/PII/personal-path scan clean (re-run during the 2026-07 audit).
