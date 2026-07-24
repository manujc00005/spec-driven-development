---
name: spring-boot-api-reviewer
description: Review Spring Boot REST APIs for contract correctness, DTO design, versioning, error semantics, OpenAPI drift, validation, and backward compatibility. Extends api-review and is consumed by the domain-reviewer agent.
triggers:
  - After `/api-review` on Spring Boot projects
  - When controllers, DTOs, or OpenAPI specs change
  - When the user asks to "review my API" or "check backward compatibility"
  - Triggered automatically by `/review-all` when controller annotations are detected
---

## SDD Contract

```yaml
category: domain-reviewer
inputs: [diff, api-review-findings]
outputs: [spring-api-contract-findings]
side_effects: none
writes_code: false
writes_specs: false
analysis_only: true
primary_agent: domain-reviewer
secondary_agents: [final-conformance-reviewer]
profile_scope: [java-spring-backend]
provider_specific: false
```

# Spring Boot API Reviewer

## Purpose

Catch Spring Boot REST-specific contract issues that generic `api-review` misses: annotation misuse,
missing validation, inconsistent error responses, OpenAPI spec drift, and breaking changes in DTOs.
This skill **extends** `api-review` — run that first for general REST design.

## Extends

- **Skill:** `api-review`
- **Agent:** `domain-reviewer` (REST conventions, OpenAPI/Swagger, versioning, backward compatibility)

## What this skill checks (beyond api-review)

### Controller annotations

- `@RestController` vs `@Controller` + `@ResponseBody` (consistency).
- `@RequestMapping` at class level duplicating path prefixes.
- Missing `@PathVariable` / `@RequestParam` annotations or mismatched names.
- `@ResponseStatus` inconsistent with what `@ControllerAdvice` returns for that exception.
- `produces`/`consumes` media types declared but not matched by the actual response.

### DTO design and validation

- `@Valid` / `@Validated` missing on `@RequestBody` parameters with constrained fields.
- Mutable DTOs without builder or record pattern (Java 17+ records preferred).
- Nested objects in request DTOs without cascading `@Valid`.
- Response DTOs exposing internal IDs that should be opaque or versioned.
- Enum values added to response DTOs without considering client deserialization (breaking for strict clients).

### Error semantics

- Consistent error response shape across all endpoints (RFC 7807 Problem Details or custom standard).
- Status codes matching HTTP semantics (400 for client error, 404 for missing resource, 409 for conflict, 422 for validation).
- Generic 500 returned for catchable business errors.
- Error responses missing correlation/trace IDs for observability.

### OpenAPI / Swagger drift

- `openapi.yml` / `openapi.json` present but not matching actual controller signatures.
- Undocumented endpoints (controller exists, OpenAPI spec doesn't list it).
- Schema mismatch: DTO field types/nullability differ between code and spec.
- Missing `@Operation` / `@ApiResponse` annotations if the project uses springdoc.

### Versioning and backward compatibility

- URL path versioning (`/v1/`, `/v2/`) vs header versioning — consistent within the project.
- Removing or renaming a field in a response DTO (breaking change).
- Adding a required field to a request DTO (breaking for existing callers).
- Changing a field type (e.g., `String` → `Long`) without a new version.

### Pagination and collections

- Unbounded list endpoints (no pagination, no `max` limit).
- Inconsistent pagination style (Spring `Pageable` vs custom vs cursor).
- Missing `totalElements` / `totalPages` in paginated responses (if expected by clients).

## Output format

```markdown
## Spring Boot API Review

**Verdict:** PASS | PASS WITH NOTES | FAIL

### Breaking changes detected

| # | Endpoint | Change | Impact | Mitigation |
|---|---|---|---|---|
| 1 | `GET /v1/orders` | Field `status` type changed String→Enum | Strict clients break | Add `/v2/orders` or deprecation period |

### Findings

| # | Category | Severity | File:Line | Finding | Action |
|---|---|---|---|---|---|
| 1 | Validation | Medium | `OrderController.java:32` | `@RequestBody OrderRequest` missing `@Valid` | Add `@Valid` |

### Contract summary

- Endpoints added:
- Endpoints modified:
- Endpoints removed:
- OpenAPI in sync: yes / no / not present
```

## What this skill does NOT do

- Does not review general REST design principles (that's `api-review`).
- Does not review service/business logic (that's `java-spring-reviewer`).
- Does not review authentication/authorization (that's `spring-security-reviewer`).
- Does not modify code or OpenAPI specs.
