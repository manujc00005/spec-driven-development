---
name: java-spring-reviewer
description: Review Java/Spring backend code for Spring-specific idioms, transaction boundaries, bean scope, DTO/entity leakage, exception handling, and null-safety. Extends backend-review and routes to the java-spring subagent.
triggers:
  - After `/spec-review` on Java/Spring changes
  - After `/backend-review` when the project is Spring Boot
  - When the user asks to "review my Spring code" or "check my service layer"
  - Triggered automatically by `/review-all` when `pom.xml` or Spring annotations are detected
---

# Java/Spring Reviewer

## Purpose

Catch Spring-specific anti-patterns and idiom violations that generic `backend-review` misses.
This skill **extends** `backend-review` — it does not replace it. Run `backend-review` first for
general service/data-access quality, then this for Spring-specific depth.

## Extends

- **Skill:** `backend-review`
- **Subagent:** `java-spring` (controllers, services, repositories, JPA entities, security, migrations)

## What this skill checks (beyond backend-review)

### Transaction boundaries

- `@Transactional` on the correct layer (service, not controller or repository).
- Read-only transactions annotated with `@Transactional(readOnly = true)`.
- No `@Transactional` on private methods (silently ignored by Spring proxies).
- No nested `@Transactional` with incompatible propagation causing unexpected behavior.
- LazyInitializationException risks: entity access outside transaction scope.

### Bean scope and lifecycle

- Singleton beans holding mutable state (thread-safety risk).
- Prototype beans injected into singletons without `ObjectProvider` or `@Lookup`.
- `@PostConstruct` doing heavy work that should be lazy or async.
- Circular dependencies masked by `@Lazy` instead of fixed architecturally.

### DTO / entity separation

- JPA entities exposed directly in REST responses (coupling persistence to API contract).
- Entity fields leaking internal IDs, audit columns, or associations the client shouldn't see.
- Missing mapper layer (MapStruct, manual) between entity and DTO.

### Exception handling

- Business exceptions thrown as generic `RuntimeException` instead of domain-specific types.
- `@ControllerAdvice` / `@RestControllerAdvice` missing or inconsistent.
- Swallowed exceptions (`catch (Exception e) {}`) hiding failures.
- HTTP status codes not matching the error semantics (e.g., 500 for a validation failure).

### Null-safety and validation

- `Optional` used as method parameter or field (anti-pattern in Spring).
- Missing `@NotNull` / `@Valid` on controller parameters.
- Nullable returns from repository methods without `Optional` wrapper.
- `@RequestBody` without `@Valid` when the DTO has constraints.

### Spring configuration

- Hardcoded values that should come from `@Value` or `@ConfigurationProperties`.
- Missing `@Configuration` or `@Component` on classes that need Spring management.
- `@Autowired` on fields instead of constructor injection (testability, immutability).

## Output format

```markdown
## Java/Spring Review

**Verdict:** PASS | PASS WITH NOTES | FAIL

### Findings

| # | Category | Severity | File:Line | Finding | Action |
|---|---|---|---|---|---|
| 1 | Transaction | High | `OrderService.java:45` | `@Transactional` on private method — not proxied | Move to public method or extract |

### Positive observations

- (What's done well)

### Required actions before merge

- [ ] (Blockers)
```

## What this skill does NOT do

- Does not re-check general code quality (that's `backend-review`).
- Does not review API contracts (that's `spring-boot-api-reviewer`).
- Does not review security config (that's `spring-security-reviewer`).
- Does not review performance (that's `java-performance-reviewer`).
- Does not modify code.
