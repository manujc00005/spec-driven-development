# Testing Strategy

> Copy this template into your project as `docs/TESTING.md` and fill it in.
> Claude Code reads this to understand what testing tools are available, how to run
> each type of test, and what coverage targets apply.

## Test pyramid

| Layer | Framework | Scope | Speed |
|---|---|---|---|
| Unit | JUnit 5 + Mockito | Single class/method | Fast (<1s) |
| Integration | Spring Boot Test + Testcontainers | Service + DB/broker | Medium (5-30s) |
| Contract | Pact / WireMock / Spring Cloud Contract | Consumer ↔ Provider | Medium |
| E2E | (describe or "not applicable") | Full system | Slow |

## Commands

| Action | Command | Profile / flag |
|---|---|---|
| Unit tests | `./mvnw test` | default |
| Integration tests | `./mvnw verify -Pintegration` | `-Pintegration` |
| Contract tests (provider) | `./mvnw verify -Ppact` | `-Ppact` |
| All tests | `./mvnw verify` | |
| Single test class | `./mvnw test -Dtest=OrderServiceTest` | |
| Coverage report | `./mvnw verify -Pcoverage` | JaCoCo |

## Test infrastructure

| Tool | Purpose | Configuration |
|---|---|---|
| Testcontainers | PostgreSQL, Kafka, Redis for integration tests | `src/test/resources/application-test.yml` |
| WireMock | Mock external HTTP services | `src/test/resources/wiremock/` |
| H2 (if used) | In-memory DB for fast unit tests | `application-test.yml` |

## Coverage targets

| Module | Line coverage | Branch coverage | Notes |
|---|---|---|---|
| Domain / business logic | ≥80% | ≥70% | Critical paths must be covered |
| Controllers | ≥60% | | Focus on happy path + validation |
| Infrastructure | ≥50% | | Integration tests cover this |

## Test patterns

- **Naming:** `<MethodUnderTest>_<Scenario>_<ExpectedResult>` or `should<Expected>_when<Condition>`.
- **Arrange-Act-Assert (AAA):** every test follows this structure.
- **Test data:** use builders/factories, not hardcoded values in each test.
- **Isolation:** unit tests never hit DB/network; integration tests use Testcontainers.
- **Cleanup:** `@Transactional` on integration tests for automatic rollback, or explicit cleanup.

## What NOT to test

- Framework internals (Spring wiring, JPA repository method generation).
- Getters/setters/constructors without logic.
- Third-party library behavior (test the integration, not the library).

## Per-spec test matrix

<!-- When implementing a feature, map each AC to the test type that covers it. -->

| AC | Unit | Integration | Contract | E2E | Manual |
|---|---|---|---|---|---|
| AC-001 | | | | | |
