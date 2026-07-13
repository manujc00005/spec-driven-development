# Feature Spec: Phase 2 — Java/Spring backend profile

## Status

Done

> Closed 2026-07-13 during Phase 5 (`005-framework-hardening-and-cross-platform-polish`).
> All ACs verified against on-disk evidence (see the backfilled `TASKS.md` Verification
> section). AC-005 is closed **as superseded**: its "skipped gracefully" wording described
> the pre-0.4.0 installer and was deliberately replaced by the shipped/planned integrity
> model — see DECISIONS D006. Note: Phase 5 also deprecated the `maven-compile` hook in
> favor of this phase's `java-build-test-guard` (wiring-level consolidation, 005/D001).

## Problem

The SDD framework has no stack-specific review intelligence for Java/Spring — the dominant stack of
the author. Existing subagents (`java-spring`, `database`, `api-design`, `testing`, `security`) cover
generic patterns but don't enforce Spring-specific idioms, don't detect Spring Security/Keycloak
misconfigurations, don't catch JPA/transaction anti-patterns, and don't review `application*.yml`
for exposed secrets or debug endpoints.

There is also no installer mechanism to activate only the skills/hooks relevant to a project's stack.

## Goal

Ship 4 Java/Spring review skills, 2 defensive hooks, 3 context templates, and the installer
`-Profile` flag — making the `java-spring-backend` profile a real, activatable unit.

## Non-goals

- Messaging/event-driven skills (Phase 3).
- Kubernetes/deployment reviewer (Phase 3).
- Contract testing reviewer (Phase 3).
- Modifying `C:\ProgramData\ClaudeConfig`.
- Running builds or tests.
- Committing.

## Functional requirements

### Skills

- FR-001: `skills/java-spring-reviewer/SKILL.md` — Bean scope, `@Transactional` boundaries, DTO/entity
  leakage, exception handling, null-safety, Spring idioms. **Extends** `backend-review` + `java-spring` agent.
- FR-002: `skills/spring-boot-api-reviewer/SKILL.md` — REST contracts, DTO versioning, error semantics,
  OpenAPI drift, `@Valid`, response codes. **Extends** `api-review` + `api-design` agent.
- FR-003: `skills/spring-security-reviewer/SKILL.md` — Keycloak/OAuth2/OIDC config, method security,
  JWT validation, Vault access, scopes/roles, CORS, actuator exposure. **Extends** `security-review`.
- FR-004: `skills/java-performance-reviewer/SKILL.md` — N+1 (JPA), connection pool sizing, thread pools,
  blocking-in-reactive, `@Cacheable` misuse, allocation hot paths. **Extends** `performance-review`.

### Hooks

- FR-005: `hooks/java-build-test-guard.ps1` + `.sh` — PostToolUse on `.java`: runs `./mvnw compile`
  (+ optional `./mvnw test -pl <module>` for changed module). Maven-first; Gradle fallback. No-op if
  neither `mvnw` nor `gradlew` present.
- FR-006: `hooks/spring-config-guard.ps1` + `.sh` — PostToolUse on `application*.yml`/`.properties`:
  warns on plaintext secrets, debug/actuator exposure in non-local profiles, missing profile separation.

### Templates

- FR-007: `docs/_templates/TESTING.md` — test pyramid, JUnit5/Mockito/Testcontainers, per-type commands,
  coverage targets, Maven profiles.
- FR-008: `docs/_templates/SECURITY.md` — IAM model (Keycloak/OIDC), token/scopes, Vault secrets, PII,
  rate limiting, CORS.
- FR-009: `docs/_templates/DEPLOYMENT.md` — environments, Docker/Helm/ArgoCD, rollout/rollback,
  migrations, env vars, health probes.

### Installer

- FR-010: Add `-Profile` parameter to `install.ps1` and `--profile` to `install.sh` that reads
  `profiles.json` and installs only the skills/hooks/templates listed in `core` + selected profile(s).
  Default behavior (no flag) = `core` + `java-spring-backend`. Existing safety model preserved.

## Acceptance criteria

- AC-001: Each skill has clear "Extends" reference and does not duplicate base skill logic.
- AC-002: `java-build-test-guard` detects `mvnw` first, `gradlew` second; no-op otherwise. Reports errors.
- AC-003: `spring-config-guard` warns (exit 0 + systemMessage) on: plaintext password/secret/token in
  non-local profiles; `management.endpoints.web.exposure.include=*` in non-local profiles; `debug=true`
  in non-local profiles.
- AC-004: Templates are Maven/Spring-centric with clear placeholder structure.
- AC-005: `install.ps1 -Profile java-spring-backend` installs only core + java-spring-backend
  skills/hooks/templates. Missing skills (planned but not yet created) are skipped gracefully.
- AC-006: `install.ps1` with no `-Profile` flag behaves identically to today + installs core + default.
- AC-007: All `.sh` hooks pass `bash -n`.
- AC-008: No secrets, PII, or hardcoded local paths.
