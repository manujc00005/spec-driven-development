# Tasks: Phase 1 — Context layer + Graphify integration

> **Backfill note (2026-07-13, Phase 5).** This feature shipped (commits `83e9477`/`45f152f`)
> with only SPEC.md + PLAN.md. This TASKS.md was reconstructed from the spec's FRs and the
> shipped artifacts as part of `005-framework-hardening-and-cross-platform-polish` (D006).

- [x] T001 — Create `docs/_templates/PROJECT_CONTEXT.md`. Covers: AC-001.
- [x] T002 — Create `docs/_templates/TECH_STACK.md`. Covers: AC-001.
- [x] T003 — Create `docs/_templates/ARCHITECTURE.md`. Covers: AC-001.
- [x] T004 — Create `skills/context-manager/SKILL.md` (bounded reading list). Covers: AC-002.
- [x] T005 — Create `skills/graphify-context/SKILL.md` (GRAPH_REPORT.md interpretation +
      graceful fallback). Covers: AC-003.
- [x] T006 — Create `skills/sdd-onboard/SKILL.md` (stack detection, scaffolding, no code
      changes). Covers: AC-004.
- [x] T007 — Create `hooks/graphify-stale-reminder.ps1` + `.sh`. Covers: AC-005, AC-007.
- [x] T008 — Secret/PII/path scan. Covers: AC-006.

## Verification (performed 2026-07-13, Phase 5 close)

All skills in this phase are prompt artifacts (markdown instructions), so their "behavior"
is verified **structurally** — the instruction text demonstrably contains the required
behavior — and validated in day-to-day dogfooding use since Phase 1. Labeled per the
framework's structural-vs-live distinction:

- AC-001 ✓ (structural) three templates exist with the required field structure; no PII/paths.
- AC-002 ✓ (structural + in-use) `context-manager` instructs a bounded reading list
  ("reading list" contract present in the skill text).
- AC-003 ✓ (structural + in-use) `graphify-context` checks `GRAPH_REPORT.md` (10 references)
  and defines the absent-file fallback path.
- AC-004 ✓ (structural + in-use) `sdd-onboard` detects stack via `pom.xml`/`mvnw`/
  `build.gradle`/`package.json`/`schema.prisma` and forbids modifying application code.
- AC-005 ✓ (structural) `graphify-stale-reminder` compares mtimes, warns, always exits 0 —
  behavior documented and code-reviewed in the 2026-07 audit.
- AC-006 ✓ scan clean.
- AC-007 ✓ `bash -n` passes on the `.sh` hook (re-run in Phase 5 verification, T015 of 005).
