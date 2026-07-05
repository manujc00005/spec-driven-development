# Roadmap — Java/Spring backend profile + Graphify context layer

> **Status: PLAN ONLY.** Nothing in this document is implemented yet. No commits, no changes to
> `C:\ProgramData\ClaudeConfig`, no dependency installs. This file describes the intended extension
> of `spec-driven-development` and the order in which to build it.

Legend used throughout:

- **[CORE]** — installed for every project, stack-agnostic.
- **[DEFAULT PROFILE]** — the `java-spring-backend` profile, enabled by default for the author's work.
- **[OPTIONAL]** — a profile enabled explicitly per project (`next-prisma-web`, `payments-fintech`).
- **[OPTIONAL — DISABLED]** — `blockchain-crypto`; ships but is off unless explicitly enabled.
- **[PLANNED]** — depends on external tooling not yet integrated (Graphify).

---

## 1. Current state

What already exists in the distribution repo (`spec-driven-development`) and must be **extended, not duplicated**:

**Skills (32 folders + 1 guardrails template = "33"):**
lifecycle — `sdd`, `sdd-medium`, `sdd-full`, `sdd-guardrails`, `project-init`, `spec-create`, `spec-clarify`,
`spec-plan`, `spec-analyze`, `spec-implement`, `spec-review`, `spec-close`, `spec-status`, `spec-update`,
`spec-resume`; reviews — `qa-review`, `security-review`, `database-review`, `api-review`, `backend-review`,
`frontend-review`, `seo-review`, `performance-review`, `privacy-compliance-review`, `refactor-review`,
`review-all`; support — `architect-review`, `test-engineer`, `debugger`, `prototype`, `decision-mapping`,
`pr-description`, `handoff`.

**Subagents already available (do not re-implement):** `java-spring` (controllers/services/repositories/JPA/
security/migrations), `database` (PostgreSQL/MySQL, Flyway, JPA/Hibernate, HikariCP, Testcontainers),
`api-design` (Spring Boot REST, OpenAPI/Swagger, versioning, breaking-change detection), `testing`
(JUnit 5, Mockito, Testcontainers), `security` (OWASP, Spring Boot auth). The review skills already route
to these.

**Hooks (8 families / 15 scripts):** `git-guardrails` (`.ps1` only), `sdd-spec-guard`, `sdd-status-banner`,
`project-init-check`, `ts-check`, `eslint-fix`, `prettier-format`, `maven-compile` (all `.ps1`+`.sh` except
git-guardrails). Wired by default in `settings.template.json`: `git-guardrails`, `ts-check`, `eslint-fix`,
`prettier-format`, `maven-compile`, `sdd-status-banner`, `project-init-check`. `sdd-spec-guard` is opt-in.

**Docs / templates / install:** `README.md`, `docs/INSTALL.md`, `CLAUDE.md.example`,
`settings.template.json` (`${CLAUDE_PROJECT_DIR}`, PowerShell-only), `specs/_templates/`
(`SPEC.md`, `PLAN.md`, `TASKS.md`, `DECISIONS.md`, draft `CONSTITUTION.md`), `examples/README.md`
(placeholder), `install.ps1/.sh`, `link-project.ps1/.sh` (idempotent, backups, dry-run, opt-in linking).

**Reference projects reviewed (author's real code):**
- `spring-ai-agent-utils-main` — multi-module **Maven** (`mvnw`, `pom.xml`; `-common`, `-bom`, `-a2a`). Representative of the author's real stack.
- `spring-and-spring-boot-main` — multi-module **Gradle** (`gradlew`, `build.gradle`). A labs/tutorial repo, **not** the author's production build tool.

> **Confirmed by the author:** the primary build tool is **Maven**. The existing `maven-compile` hook is
> therefore correct for the default profile and is **kept and extended**, not replaced. Gradle support is
> secondary/optional detection only (nice-to-have), not a driver of the design.

---

## 2. Main gap

The current SDD is well-engineered but **stack-generic**. Verified by grep across `skills/`: `Prisma`,
`Stripe`, `Kafka`, `RabbitMQ`, `webhook`, `idempoten`, `Docker`, `Kubernetes`, `outbox`, `saga`, `Pact`,
`WireMock` appear in **0 skills**; observability and messaging are effectively uncovered.

For a Java/Spring backend + microservices + messaging + fintech engineer this means:

1. **No default profile.** The framework treats every project the same. There is no "this is a Spring Boot
   microservice" mode that pre-loads the right reviews and hooks.
2. **Messaging / event-driven is a blind spot.** No coverage for Kafka/RabbitMQ, exactly-once vs
   at-least-once, consumer idempotency, outbox, saga/compensation, dead-letter handling.
3. **Distributed-systems patterns are unreviewed.** No microservices-patterns or contract-testing review,
   which is where "being wrong is expensive" for the author's domain.
4. **Observability and deployment (k8s/Helm/ArgoCD) are undocumented and unreviewed.**
5. **Context cost is high.** Without an architecture map, every plan/review re-scans the repo — expensive
   on large multi-module microservice codebases. This is the Graphify gap.

The fix is **profiles + a context layer**, not rewriting the 33 skills. The generic core stays; profiles
add stack-specific skills/hooks/templates on top; Graphify cuts token cost.

---

## 3. Target profiles

| Profile | Status | Enables |
|---|---|---|
| `core` | **[CORE]** | Lifecycle skills, guardrails, generic reviews, safety hooks, context layer |
| `java-spring-backend` | **[DEFAULT PROFILE]** | Java/Spring reviews, messaging, microservices patterns, contract testing, observability, k8s deploy, Java build/test hooks |
| `next-prisma-web` | **[OPTIONAL]** | Prisma/Stripe/Server-Actions reviews + JS/TS hooks (from prior roadmap) |
| `payments-fintech` | **[OPTIONAL]** | Idempotency, reconciliation, money/units safety, PSP webhook verification — layers on top of `java-spring-backend` or `next-prisma-web` |
| `blockchain-crypto` | **[OPTIONAL — DISABLED BY DEFAULT]** | On-chain/tx/wallet reviews — **never auto-enabled**; must be explicitly turned on |

**Profile model:** a project declares its profiles in `specs/CONSTITUTION.md` (new `## Profiles` section)
and/or the install/link script copies only the selected profiles' skills+hooks. `core` is always present.
`java-spring-backend` is the author's default. Blockchain is shipped but inert.

---

## 4. Graphify / context strategy   **[PLANNED — depends on external Graphify]**

Graphify is an **architecture discovery layer**, used for **impact analysis, never as source of truth**
(consistent with the existing README "Graphify (Planned)" section). The actual files, tests, and the
engineer's judgment remain authoritative.

**Artifact:** Graphify produces `GRAPH_REPORT.md` (+ optional `graphify-out/`, already gitignored) at repo
root — a module/dependency map + impact hints.

**When to run Graphify:**
- Before `/spec-plan`, `/spec-analyze`, `/architect-review` on **medium/large** changes (multi-module,
  cross-service, schema+code coupled).
- On `/sdd-onboard` of an existing project (initial map).
- **Not** for trivial or single-file changes — the map isn't worth the run.

**Which commands must read `GRAPH_REPORT.md` before scanning:**
`spec-plan`, `spec-analyze`, `architect-review`, `backend-review`, `microservices-patterns-reviewer`,
`event-driven-reviewer`, `spec-implement` (impacted-modules section only). Each reads the map **first**
and only opens the files the map flags as impacted, instead of walking the tree.

**How to avoid token waste:**
- Prefer `GRAPH_REPORT.md` over a full-repo scan when the map is fresh.
- Read only the impacted subgraph relevant to the active feature.
- Cache the "reading list" in the feature's `DECISIONS.md` so re-entry doesn't re-derive it.

**Staleness detection (`graphify-stale-reminder` hook, §6):**
- Compare `GRAPH_REPORT.md` mtime against the latest commit / newest source-file mtime.
- If source is newer than the map, or the map is older than N days, warn: "GRAPH_REPORT.md is stale — re-run
  Graphify before relying on it for impact analysis." Never block; only remind.

**If Graphify is not installed:**
- All Graphify-aware skills degrade gracefully: detect the absence of `GRAPH_REPORT.md`, print a one-line
  note, and fall back to the current bounded-scan behavior. Graphify is an **accelerator, never a hard
  dependency** — no skill fails because it's missing.

---

## 5. New skills proposed

Overlap is called out explicitly. "**Extends**" = thin Java/Spring-profile wrapper that routes to an
existing skill/subagent and adds domain checks; it must **not** re-implement the base skill.

| Skill | Purpose | When to use | Inputs | Output | Priority |
|---|---|---|---|---|---|
| `java-spring-reviewer` | Java/Spring idioms: bean scope, `@Transactional` boundaries, DTO/entity leakage, exception handling, null-safety. **Extends** `backend-review` + `java-spring` agent | Backend Java change | Java diff, build files | Verdict + findings (file:line) | **High** |
| `spring-boot-api-reviewer` | Spring REST contracts, DTO/versioning, error semantics, OpenAPI drift. **Extends** `api-review` + `api-design` agent | Endpoint/DTO change | Controllers, OpenAPI spec | API verdict + breaking-change list | **High** |
| `spring-security-reviewer` | Keycloak/OAuth2/OIDC, SAML, method security, JWT validation, Vault secret access, scopes/roles. **Extends** `security-review` | Auth/IAM/secrets change | Security config, filters, Vault usage | Security verdict | **High** |
| `event-driven-reviewer` | Producer/consumer idempotency, ordering, delivery semantics, DLQ, poison messages, schema evolution | Any messaging change | Listeners, producers, topic/queue config | Messaging verdict | **High** |
| `kafka-reviewer` | Kafka specifics: partitioning/keys, consumer groups, offset commit strategy, EOS/transactions, retries/backoff, Avro/Schema Registry. **Extends** `event-driven-reviewer` | Kafka change | Kafka config + code | Kafka verdict | **High** |
| `rabbitmq-reviewer` | RabbitMQ specifics: exchange/queue topology, acks, prefetch, DLX, TTL, publisher confirms. **Extends** `event-driven-reviewer` | RabbitMQ change | AMQP config + code | RabbitMQ verdict | Medium |
| `microservices-patterns-reviewer` | Service boundaries, sync-vs-async coupling, resilience (circuit breaker, retry, timeout, bulkhead), API gateway, config/discovery | Cross-service change | Graph map + service code | Patterns verdict | **High** |
| `outbox-pattern-reviewer` | Transactional outbox correctness: same-tx write, relay, dedup, idempotent publish. **Extends** `event-driven-reviewer` | Outbox impl | Outbox table + relay code | Outbox verdict | Medium |
| `saga-orchestration-reviewer` | Saga/choreography: compensation, idempotency, timeouts, partial-failure recovery, state persistence | Distributed transaction | Saga/state code | Saga verdict | Medium |
| `contract-testing-reviewer` | Consumer/provider contracts: Pact, WireMock stubs, OpenAPI-as-contract, backward compat. **Extends** `test-engineer` | Contract/integration change | Pact files, WireMock, OpenAPI | Contract verdict | **High** |
| `observability-reviewer` | Structured logging (no PII), correlation/trace IDs, metrics (Prometheus/Micrometer), spans (Elastic APM), log levels, alert-worthy signals | Service/critical change | Logging/metrics/tracing code | Observability gaps | **High** |
| `kubernetes-deployment-reviewer` | Manifests/Helm/ArgoCD: probes, resource limits, non-root, secrets (no plaintext), rollout strategy, HPA, ConfigMap vs Secret | Infra/deploy change | Dockerfile, manifests, Helm, ArgoCD | Deploy verdict | Medium |
| `java-performance-reviewer` | JVM/Spring perf: N+1 (JPA), connection pool sizing, thread pools, blocking-in-reactive, caching, allocation hot paths. **Extends** `performance-review` | Perf-sensitive Java | Java diff + config | Perf verdict | Medium |
| `context-manager` | Decide the minimal reading list before implementing; compact context in long sessions | Session start / large feature | Context docs + graph map + active spec | Bounded reading list | Medium |
| `graphify-context` | Run/interpret Graphify, produce impact-analysis summary, detect staleness | Before plan/review on medium+ change | Repo tree, `GRAPH_REPORT.md` | Impact summary + impacted modules | **High** (once Graphify exists) |
| `sdd-onboard` | Onboard an existing project: detect stack, architecture, patterns, tech debt; scaffold context docs; **no code changes** | Existing project without SDD | Repo tree, build files, configs | `PROJECT_CONTEXT/TECH_STACK/ARCHITECTURE` + baseline | **High** |

---

## 6. New hooks proposed

Safety model unchanged: reminders **exit 0 + `systemMessage`** (never block); guards **exit 2** (block).
Every hook is **no-op when the stack doesn't apply** (same defensive pattern as existing hooks). Ship as
`.ps1` **and** `.sh`. **None of the blocking guards is auto-wired** in the default template — they ship as
documented opt-in, exactly like `sdd-spec-guard` today.

| Hook | Event | Validates | Behavior | Blocking? |
|---|---|---|---|---|
| `secret-scan` | PreToolUse `Bash` (git commit/push) | `sk_live`, `whsec_`, `AKIA`, `-----BEGIN * KEY-----`, `.env`, Vault tokens in staged diff | Block if secret found | **Guard (opt-in)** |
| `sensitive-file-guard` | PreToolUse `Write\|Edit` | Path ∈ {`.env*`, `application-*.yml` with secrets, `*.pem`, `settings.local.json`, applied migrations, Vault config} | Block unless confirmed | **Guard (opt-in)** |
| `destructive-cmd-guard` | PreToolUse `Bash` | `rm -rf`, `DROP TABLE`, `kubectl delete`, `flyway clean`, `gradle`/`mvn` publish, `git clean` | Block unless confirmed | **Guard (opt-in)** |
| `git-guardrails.sh` | PreToolUse `Bash` (mac/Linux) | Parity with existing `.ps1` (force-push, reset --hard, clean -f) | Block | **Guard** (closes cross-platform gap) |
| `java-build-test-guard` | PostToolUse `Write\|Edit` (`.java`) | Maven-first (`mvnw`); runs compile (+ optional fast tests). Optional Gradle (`gradlew`) fallback | Report compile/test errors; no-op if no build tool present | Reminder |
| `spring-config-guard` | PostToolUse `Write\|Edit` (`application*.yml/.properties`, `bootstrap*`) | Plaintext secrets, missing profile separation, debug/actuator exposure | Warn on risky config | Reminder |
| `openapi-contract-reminder` | PostToolUse `Write\|Edit` (controllers / `openapi*.yml`) | Endpoint/spec changed | Remind `/spring-boot-api-reviewer` + `/contract-testing-reviewer` | Reminder |
| `messaging-review-reminder` | PostToolUse `Write\|Edit` (Kafka/RabbitMQ listeners/producers/config) | Messaging code changed | Remind `/event-driven-reviewer` (+ kafka/rabbitmq) | Reminder |
| `graphify-stale-reminder` | SessionStart / PreToolUse plan | `GRAPH_REPORT.md` older than newest source or > N days | Remind to re-run Graphify | Reminder |

> **Note on `maven-compile` (existing):** Maven is the author's primary build tool, so this hook is correct
> as-is and stays in the `java-spring-backend` profile. `java-build-test-guard` is an **evolution** of it
> (adds optional fast-test run and an optional Gradle fallback), not a replacement. Keep `maven-compile`
> either way — existing users may reference it.

---

## 7. New templates proposed

Under `docs/_templates/` (context/reference docs) and `specs/_templates/` (spec-cycle docs).

| Template | Location | Key fields | Priority |
|---|---|---|---|
| `PROJECT_CONTEXT.md` | `docs/_templates/` | Purpose, bounded contexts, service map, glossary, ownership | **High** |
| `TECH_STACK.md` | `docs/_templates/` | Java version, Spring Boot/Cloud versions, build tool (Maven default; Gradle if present), libs, build/test/run commands | **High** |
| `ARCHITECTURE.md` | `docs/_templates/` | Services, sync/async edges, data stores, boundaries, module diagram | **High** |
| `TESTING.md` | `docs/_templates/` | Test pyramid, JUnit5/Mockito/Testcontainers, per-type command, coverage targets | Medium |
| `SECURITY.md` | `docs/_templates/` | IAM model (Keycloak/OIDC), token/scopes, Vault secrets, PII, rate limiting | Medium |
| `DEPLOYMENT.md` | `docs/_templates/` | Environments, Docker/Helm/ArgoCD, rollout/rollback, migrations, env vars | Medium |
| `CONTRACT_TESTING.md` | `docs/_templates/` | Consumers/providers, Pact broker, WireMock stubs, OpenAPI-as-contract, compat policy | Medium |
| `OBSERVABILITY.md` | `docs/_templates/` | Logging format + correlation IDs, metrics (Prometheus), tracing (APM), dashboards, alerts | Medium |
| `MESSAGING.md` | `docs/_templates/` | Topics/queues, delivery semantics, idempotency, DLQ, schema evolution, ordering | **High** |
| `MICROSERVICES_PATTERNS.md` | `docs/_templates/` | Boundaries, resilience patterns in use, gateway, config/discovery, outbox/saga inventory | Medium |
| `PR_DESCRIPTION.md` | `specs/_templates/` | Summary, changes, tests run, migrations, rollout/rollback, risks (extract from `pr-description` skill) | Medium |
| `REVIEW_REPORT_TEMPLATE.md` | `docs/_templates/` | Common review output: verdict, findings (severity, file:line), evidence, required actions | Medium |

---

## 8. Installation / profile strategy

**No changes yet — this is the intended design.**

**Core (generic), unchanged today:**
```
install.ps1            # → C:\ProgramData\ClaudeConfig (Windows)
install.sh             # → ~/.claude-config (mac/Linux)
```
Installs `core` skills/hooks/templates only.

**Java/Spring backend profile (author default):**
```
install.ps1 -Profile java-spring-backend
./install.sh --profile java-spring-backend
```
Adds the §5 Java/Spring/messaging/microservices/observability/k8s skills, the §6 Java hooks, and the §7
Java templates. Wires `java-build-test-guard` + the reminders; **guards stay opt-in**.

**Optional profiles (explicit only):**
```
install.ps1 -Profile java-spring-backend,payments-fintech
install.ps1 -Profile next-prisma-web
install.ps1 -Profile blockchain-crypto   # never selected automatically
```

**Design constraints for the installer changes:**
- Keep the current safety model intact (idempotent, backups, dry-run, opt-in user linking, never touch
  `settings.local.json`).
- A profile is a subfolder selection, not a rewrite — `skills/` and `hooks/` gain per-profile subtrees
  (e.g. `skills/profiles/java-spring-backend/…`) or a manifest maps profile → file list. Decide the exact
  layout in Phase 2 before writing the installer change.
- `-Profile` defaults to `core` only, so existing behavior is preserved for anyone who doesn't pass it.

---

## 9. Implementation phases

- **Phase 0 — Quick wins (no risk):** LICENSE, fix README staleness (`docs/INSTALL.md` already exists),
  `PR_DESCRIPTION.md` + `REVIEW_REPORT_TEMPLATE.md`, `git-guardrails.sh` (close cross-platform gap),
  `settings.template.sh.json`.
- **Phase 1 — Graphify / context layer:** `PROJECT_CONTEXT/TECH_STACK/ARCHITECTURE` templates,
  `context-manager`, `graphify-context`, `sdd-onboard`, `graphify-stale-reminder`. Graceful degradation
  when Graphify is absent.
- **Phase 2 — Java/Spring profile:** `java-spring-reviewer`, `spring-boot-api-reviewer`,
  `spring-security-reviewer`, `java-performance-reviewer`, `java-build-test-guard` (Maven-first, optional Gradle),
  `spring-config-guard`; installer `-Profile` mechanism; `TESTING/SECURITY/DEPLOYMENT` templates.
- **Phase 3 — Messaging / microservices:** `event-driven-reviewer`, `kafka-reviewer`, `rabbitmq-reviewer`,
  `microservices-patterns-reviewer`, `outbox-pattern-reviewer`, `saga-orchestration-reviewer`,
  `contract-testing-reviewer`, `observability-reviewer`, `kubernetes-deployment-reviewer`;
  `MESSAGING/MICROSERVICES_PATTERNS/CONTRACT_TESTING/OBSERVABILITY` templates; `openapi-contract-reminder`,
  `messaging-review-reminder`.
- **Phase 4 — Defensive hooks:** `secret-scan`, `sensitive-file-guard`, `destructive-cmd-guard`
  (all opt-in guards, documented, never auto-wired).
- **Phase 5 — Examples & dogfooding:** one real Spring Boot microservice feature carried end-to-end through
  the workflow in `examples/`; repo adopts its own `specs/CONSTITUTION.md`.

---

## 10. What NOT to do

- **No blockchain by default.** `blockchain-crypto` ships **[OPTIONAL — DISABLED]** and is never
  auto-enabled or auto-detected into a default.
- **No rewriting the existing 32/33 skills.** New skills extend/route to existing skills and subagents
  (`java-spring`, `database`, `api-design`, `testing`, `security`); they do not duplicate them.
- **No changes to the live config** (`C:\ProgramData\ClaudeConfig`) until the repo is validated. Re-install
  later via `install.ps1 -Force` (which backs up first).
- **No auto-enabling destructive/blocking hooks.** `secret-scan`, `sensitive-file-guard`,
  `destructive-cmd-guard` stay opt-in and documented, mirroring `sdd-spec-guard`.
- **No replacing tests with Graphify.** Graphify is discovery/impact only — it never substitutes running
  the actual tests, and it is never a source of truth.
- **No hard dependency on Graphify.** Every Graphify-aware skill/hook degrades gracefully when
  `GRAPH_REPORT.md` is absent.
- **Keep Next/Prisma/Stripe optional.** They remain an optional profile, not the default.
- **No commits and no dependency installs** as part of this planning work.
