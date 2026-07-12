# Plan: Phase 2 — Java/Spring backend profile

## Approach

9 independent deliverables (skills, hooks, templates) + 1 installer change. Skills/hooks/templates
are fully independent of each other. The installer change depends on `profiles.json` (already exists).

## Files to CREATE

| File | Purpose | AC |
|---|---|---|
| `skills/java-spring-reviewer/SKILL.md` | Spring idioms, transactions, DTO leakage | AC-001 |
| `skills/spring-boot-api-reviewer/SKILL.md` | REST contracts, OpenAPI drift | AC-001 |
| `skills/spring-security-reviewer/SKILL.md` | Keycloak/OAuth2, method security, Vault | AC-001 |
| `skills/java-performance-reviewer/SKILL.md` | JPA N+1, pools, caching, blocking | AC-001 |
| `hooks/java-build-test-guard.ps1` | Maven-first build/test on .java edit (Windows) | AC-002 |
| `hooks/java-build-test-guard.sh` | Same (macOS/Linux) | AC-002, AC-007 |
| `hooks/spring-config-guard.ps1` | Warn on risky Spring config (Windows) | AC-003 |
| `hooks/spring-config-guard.sh` | Same (macOS/Linux) | AC-003, AC-007 |
| `docs/_templates/TESTING.md` | Test strategy template | AC-004 |
| `docs/_templates/SECURITY.md` | Security/IAM template | AC-004 |
| `docs/_templates/DEPLOYMENT.md` | Deployment/infra template | AC-004 |

## Files to MODIFY

| File | Change | AC |
|---|---|---|
| `install.ps1` | Add `-Profile` parameter, read `profiles.json`, filter files | AC-005, AC-006 |
| `install.sh` | Add `--profile` flag, same logic | AC-005, AC-006 |

## Files NOT touched

- `C:\ProgramData\ClaudeConfig\*`
- `settings.local.json`
- Existing 36 skills (no internal changes)
- `settings.template.json`
- Application code in any target project

## Design decisions

- Skills use "**Extends X**" pattern: they reference the base skill/agent and add stack-specific checks
  on top. They never re-implement what the base already covers.
- Hooks are **reminders** (exit 0 + systemMessage), not guards — they ship opt-in in `profiles.json`
  but are not wired in `settings.template.json` by default.
- `java-build-test-guard` supersedes `maven-compile` functionally but `maven-compile` is NOT deleted
  (backward compatibility). Both can coexist; the user picks one.
- Installer `-Profile` reads `profiles.json`, resolves `core` + selected profile(s), and only copies
  skills/hooks/templates that exist on disk (planned-but-unshipped are silently skipped).

## Verification

- `bash -n` on all new `.sh` files.
- Secret scan on all new/modified files.
- `install.ps1 -DryRun -Profile java-spring-backend` outputs expected file list.
- `git status` + `git diff --stat` for author review.
