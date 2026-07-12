---
name: spring-security-reviewer
description: Review Spring Security configuration, Keycloak/OAuth2/OIDC integration, method-level authorization, JWT validation, Vault secret access, CORS, and actuator exposure. Extends security-review.
triggers:
  - After `/security-review` on Spring Boot projects
  - When security config, filters, or IAM-related code changes
  - When the user asks to "review my security config" or "check Keycloak setup"
  - Triggered automatically by `/review-all` when Spring Security or Keycloak dependencies are detected
---

# Spring Security Reviewer

## Purpose

Catch Spring Security-specific misconfigurations that generic `security-review` (OWASP-focused) misses:
filter chain ordering, OAuth2 resource server setup, Keycloak realm/role mapping, method security
annotations, Vault integration, and actuator endpoint exposure.

## Extends

- **Skill:** `security-review`
- **Subagent:** `security` (OWASP Top 10, auth, injection, XSS, CSRF, secrets)

## What this skill checks (beyond security-review)

### SecurityFilterChain configuration

- Filter chain ordering (`@Order`) — more specific chains before general.
- `permitAll()` on endpoints that should require authentication.
- `csrf().disable()` without explicit justification (stateless API with token auth is valid; UI app is not).
- Missing `.authenticated()` or `.hasRole()` on sensitive endpoints.
- `antMatchers` / `requestMatchers` with overly broad patterns (`/**`).
- `sessionManagement` set to STATELESS when the app actually uses sessions (or vice versa).

### OAuth2 / OIDC / Keycloak

- Resource server JWT validation: correct `issuer-uri`, audience validation enabled.
- Keycloak realm role extraction: `KeycloakAuthenticationConverter` or custom `JwtAuthenticationConverter` correctly mapping realm/client roles to Spring authorities.
- Token scope/authority mapping: `SCOPE_` prefix handling, role hierarchy.
- Missing token validation (signature, expiry, issuer, audience) — any of these skipped is critical.
- Refresh token handling: not exposed to frontend in implicit/SPA flows.

### Method-level security

- `@PreAuthorize` / `@Secured` / `@RolesAllowed` consistent within the project (don't mix).
- SpEL expressions in `@PreAuthorize` that reference unavailable beans or misspelled roles.
- `@PreAuthorize` on private methods (not intercepted by proxy).
- Missing method security on service layer when controller security is the only gate (defense in depth).

### Vault / secrets

- Secrets in `application*.yml` instead of Vault / environment variables / sealed secrets.
- Vault paths hardcoded vs using `spring.cloud.vault.kv.backend` + environment-specific config.
- Bootstrap vs application context for Vault initialization (Spring Cloud Vault ordering).

### CORS

- Overly permissive `allowedOrigins("*")` in production profiles.
- `allowCredentials(true)` combined with wildcard origins (browser rejects this).
- CORS config at controller level conflicting with global SecurityFilterChain CORS config.

### Actuator exposure

- `management.endpoints.web.exposure.include=*` in non-local profiles (exposes env, beans, heapdump).
- Actuator endpoints not behind authentication or separate port.
- `/actuator/env` or `/actuator/configprops` accessible (leaks secrets).

### Password / credential handling

- Passwords stored without `PasswordEncoder` (BCrypt, Argon2).
- Custom authentication filters not using constant-time comparison.
- Login endpoints without rate limiting or brute-force protection.

## Output format

```markdown
## Spring Security Review

**Verdict:** PASS | PASS WITH NOTES | FAIL

### Critical findings

| # | Category | Severity | File:Line | Finding | Action |
|---|---|---|---|---|---|
| 1 | Actuator | Critical | `application-prod.yml:12` | `exposure.include=*` in prod | Restrict to health,info,prometheus |

### Authentication flow summary

- Type: OAuth2 Resource Server / Keycloak / Form login / Basic
- Token validation: JWT (issuer-uri) / Opaque (introspection)
- Role source: realm roles / client roles / custom claim
- Method security: @PreAuthorize / @Secured / none

### Required actions before merge

- [ ] (Blockers)
```

## What this skill does NOT do

- Does not review general OWASP vulnerabilities (that's `security-review`).
- Does not review API contracts (that's `spring-boot-api-reviewer`).
- Does not review network/infrastructure security (that's `kubernetes-deployment-reviewer`, Phase 3).
- Does not modify code or configuration.
