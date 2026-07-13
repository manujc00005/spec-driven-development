# Tasks: Phase 2 — Java/Spring backend profile

> **Backfill note (2026-07-13, Phase 5).** This feature shipped with SPEC.md + PLAN.md +
> DECISIONS.md but no TASKS.md. Reconstructed from the spec's FRs and shipped artifacts as
> part of `005-framework-hardening-and-cross-platform-polish` (D006).

- [x] T001 — Create `skills/java-spring-reviewer/SKILL.md`. Covers: AC-001.
- [x] T002 — Create `skills/spring-boot-api-reviewer/SKILL.md`. Covers: AC-001.
- [x] T003 — Create `skills/spring-security-reviewer/SKILL.md`. Covers: AC-001.
- [x] T004 — Create `skills/java-performance-reviewer/SKILL.md`. Covers: AC-001.
- [x] T005 — Create `hooks/java-build-test-guard.ps1` + `.sh`. Covers: AC-002, AC-007.
- [x] T006 — Create `hooks/spring-config-guard.ps1` + `.sh`. Covers: AC-003, AC-007.
- [x] T007 — Create `docs/_templates/TESTING.md`, `SECURITY.md`, `DEPLOYMENT.md`. Covers: AC-004.
- [x] T008 — Add `-Profile`/`--profile` to both installers, reading `profiles.json`. Covers:
      AC-005 (as superseded — see DECISIONS D006), AC-006.
- [x] T009 — Secret/PII/path scan. Covers: AC-008.

## Verification (performed 2026-07-13, Phase 5 close)

- AC-001 ✓ all four skills exist and carry an explicit "Extends" reference (grep-verified).
- AC-002 ✓ (structural, code-reviewed) `java-build-test-guard` checks `mvnw`/`mvnw.cmd`
  first, `gradlew`/`gradlew.bat` only as fallback, no-op otherwise; compile-only by default,
  tests only behind `SDD_JAVA_HOOK_RUN_TESTS`; always exit 0.
- AC-003 ✓ (structural, code-reviewed) `spring-config-guard` warns (exit 0 + systemMessage)
  on plaintext secrets / `include=*` / `debug=true` in non-local profiles; never prints the
  matched secret value; skips `application-local.*`/`application-dev.*`.
- AC-004 ✓ the three templates exist and are Maven/Spring-centric.
- AC-005 ✓ **as superseded** — planned items skip gracefully; missing *shipped* items are a
  deliberate hard error since profiles.json 0.4.0. See DECISIONS D006 (this spec) and
  D001/D005 for the full chain.
- AC-006 ✓ no-flag behavior = core + default profile (verified in the 2026-07 audit against
  both installers' resolution logic).
- AC-007 ✓ `bash -n` passes on both `.sh` hooks (re-run in Phase 5 verification).
- AC-008 ✓ scan clean.
