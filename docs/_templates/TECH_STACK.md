# Tech Stack

> Copy this template into your project as `docs/TECH_STACK.md` and fill it in.
> Claude Code reads this before planning or implementing to know what tools, versions,
> and commands are available — avoiding guesses or outdated assumptions.

## Language & runtime

| Property | Value |
|---|---|
| Language | Java 21 |
| Runtime | JVM (OpenJDK / GraalVM) |
| Framework | Spring Boot 3.x |
| Spring Cloud | (version or "not used") |

## Build tool

| Property | Value |
|---|---|
| Primary | Maven (`./mvnw`) |
| Wrapper | `mvnw` / `mvnw.cmd` |
| Settings | `~/.m2/settings.xml` (if relevant) |

<!-- If Gradle is used instead, replace the above with gradlew equivalents. -->

## Key dependencies

<!-- Only list what's non-obvious or version-sensitive. Don't enumerate every transitive dep. -->

| Dependency | Purpose | Version constraint |
|---|---|---|
| Spring Security | AuthN/AuthZ | |
| Spring Data JPA | Persistence | |
| Flyway | Migrations | |
| Keycloak adapter | OIDC/OAuth2 | |
| Kafka client | Messaging | |
| | | |

## Build commands

| Action | Command |
|---|---|
| Compile | `./mvnw compile` |
| Unit tests | `./mvnw test` |
| Integration tests | `./mvnw verify -Pintegration` |
| Full build (skip tests) | `./mvnw package -DskipTests` |
| Run locally | `./mvnw spring-boot:run -Dspring-boot.run.profiles=local` |
| Lint / format | (Checkstyle / SpotBugs / Google Java Format — specify) |
| Docker build | `docker build -t <image> .` |

## Test commands

| Type | Command | Notes |
|---|---|---|
| Unit | `./mvnw test` | JUnit 5 + Mockito |
| Integration | `./mvnw verify -Pintegration` | Testcontainers (PostgreSQL, Kafka) |
| Contract | `./mvnw verify -Ppact` | Pact provider verification |
| E2E | (describe or "not applicable") | |

## Environment / profiles

| Profile | Purpose | Activation |
|---|---|---|
| `local` | Local dev (H2 or Testcontainers) | `-Dspring.profiles.active=local` |
| `dev` | Shared dev environment | k8s ConfigMap |
| `staging` | Pre-production | k8s ConfigMap |
| `prod` | Production | k8s ConfigMap + Vault |

## Secrets management

| Method | Used for |
|---|---|
| HashiCorp Vault | Production secrets |
| Environment variables | Local dev |
| `application-local.yml` (gitignored) | Local overrides |

## Conventions

<!-- Patterns that Claude should follow when generating code in this project. -->

- Package structure:
- Naming (DTOs, entities, controllers, services):
- Error handling pattern:
- Logging format:
- API versioning:
