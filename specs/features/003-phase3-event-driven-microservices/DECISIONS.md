<!-- Extracted from skills/spec-plan/SKILL.md — kept in sync with that skill's template. -->
<!-- See skills/sdd-guardrails/SKILL.md, section 1, for the full decision state machine (Proposed / Accepted / Superseded / Rejected / Deferred). -->

# Decisions: Phase 3 — Messaging / event-driven / microservices patterns

## Decision log

### D001 - Consolidate into 2 skills instead of 6 granular ones

**Date:** 2026-07-12

**Status:** Accepted

**Context:** `profiles.json`'s `messaging-event-driven` profile previously declared 6
`plannedSkills` as separate roadmap items: `event-driven-reviewer`, `kafka-reviewer`,
`rabbitmq-reviewer`, `microservices-patterns-reviewer`, `outbox-pattern-reviewer`,
`saga-orchestration-reviewer` — one reviewer per broker/pattern. The user explicitly asked to
avoid this: "Prefiero pocas skills fuertes que orquesten checks internos... No crear 10 skills
pequeñas tipo kafka-reviewer, rabbitmq-reviewer, saga-reviewer, outbox-reviewer."

**Decision:** Ship exactly 2 skills. `kafka-reviewer`, `rabbitmq-reviewer`,
`outbox-pattern-reviewer`, and `saga-orchestration-reviewer` are retired as separate roadmap
items — their entire scope is absorbed as sections/checklists inside `event-driven-reviewer`
(broker-specific delivery-semantics idioms, the outbox pattern, saga/compensation), not as their
own `SKILL.md` files.

**Reasoning:** Kafka, RabbitMQ, and ActiveMQ concerns share the same reviewer *lens* — delivery
semantics, idempotency, DLQ/poison messages, ordering — the broker name changes the API surface,
not the review question being asked. Splitting by broker or by pattern (outbox vs saga) would
multiply files to maintain without adding distinct review logic; a single skill with clear
subsections covers the same ground and is easier to keep internally consistent.

**Consequences:** `profiles.json`'s `messaging-event-driven.plannedSkills` must drop the 4 retired
names (they are not "not yet built" — they no longer exist as a roadmap target at all, superseded
by this decision). Any future request for e.g. a dedicated Kafka-only reviewer should first check
whether `event-driven-reviewer`'s existing Kafka section is actually insufficient before
reintroducing a split.

### D002 - Contract testing is a section of `microservices-patterns-reviewer`, not a standalone skill

**Date:** 2026-07-12

**Status:** Accepted

**Context:** `profiles.json` already listed `contract-testing-reviewer` as a `plannedSkills` entry
under `java-spring-backend` (declared during Phase 2 planning). The existing `api-review` skill's
own description already covers "REST conventions, OpenAPI/Swagger, versioning, backward
compatibility, DTO design, error semantics, pagination, and breaking change detection" — which is
most of what a `contract-testing-reviewer` would otherwise re-implement. The user's brief made this
skill explicitly optional: "Solo créala como skill separada si merece la pena. Si no, intégrala
como sección dentro de `microservices-patterns-reviewer`."

**Decision:** No standalone `contract-testing-reviewer` skill. Contract testing (Pact/WireMock
consumer-driven contract testing, provider/consumer verification workflow, OpenAPI compatibility)
is a **Contract compatibility** section inside `microservices-patterns-reviewer`. That section
explicitly defers pure OpenAPI/DTO/breaking-change mechanics to `api-review` and only adds the
consumer-driven-contract-testing-tooling layer (Pact broker, WireMock stubs) and the cross-service
verification workflow that `api-review` doesn't already cover.

**Reasoning:** Rule 13 (don't duplicate existing skills — orchestrate/extend instead). The
genuinely new ground here (Pact/WireMock tooling, provider-verification workflow) is too thin to
justify its own `SKILL.md` on top of an already-overlapping `api-review`; folding it in keeps one
strong skill instead of one strong skill plus one thin, largely-duplicate one.

**Consequences:** `profiles.json`'s `java-spring-backend.plannedSkills` entry for
`contract-testing-reviewer` is removed (superseded, not simply "not yet built") and its `note`
field is corrected to point at `microservices-patterns-reviewer` instead.

### D003 - Both new skills ship under `messaging-event-driven`, not `java-spring-backend`

**Date:** 2026-07-12

**Status:** Accepted

**Context:** `java-spring-backend` is the default profile (rule 11) — but "default" specifically
means "installed when no `--profile`/`-Profile` flag is passed at all." Not every Java/Spring
project uses Kafka/RabbitMQ/ActiveMQ or a microservices topology — a monolith or a single-service
project shouldn't get messaging/microservices reviewers by default.

**Verification performed:** Read `install.sh` (the `REQUESTED_CSV` → embedded-Python resolution
block) and `install.ps1` (the `$requestedProfiles` block) directly rather than assuming. Both use
an `if/elif` (`if requested: ... elif defaults.profile: ...`): the default-profile fallback
**only** fires when zero `--profile`/`-Profile` values were supplied. The moment the user passes
any explicit profile — `--profile messaging-event-driven` alone, for instance — `requested` is
non-empty, the `elif` never runs, and `active_profiles = ["core"] + requested` only. There is no
step anywhere that merges an explicit request with `defaults.profile`. Multiple profiles **are**
supported (comma-separated in one flag, or the flag repeated), which is how you get both at once.

**Decision:** `event-driven-reviewer` and `microservices-patterns-reviewer` ship as `skills` of the
`messaging-event-driven` profile (`default: false`). It is described as an **optional profile,
conceptually layered on `java-spring-backend`** (its skills assume a Java/Spring service
underneath) — not as an automatic overlay, since installing it does not automatically pull in
`java-spring-backend` or vice versa.

**Reasoning:** Keeps the default profile lean and stack-generic (rule 11: java-spring-backend
stays default; rule 12: Maven stays primary build tool, untouched by this phase either way, since
no build-tool-related file changes in this phase). Documenting the real, verified installer
behavior avoids shipping a spec/README that overpromises automatic bundling.

**Consequences:** Users who want both profiles' skills must explicitly list both in one invocation:
`--profile java-spring-backend,messaging-event-driven` (or repeat the flag) /
`-Profile java-spring-backend,messaging-event-driven`. Requesting `messaging-event-driven` alone
installs `core` + `messaging-event-driven` only — `java-spring-backend` is **not** included unless
named explicitly. `README.md`/`docs/INSTALL.md` must reflect this (see FR-007/FR-008, AC-011) —
no wording implying "installs regardless" or automatic bundling.

### D004 - No new hooks shipped this phase

**Date:** 2026-07-12

**Status:** Accepted

**Context:** `profiles.json` lists `messaging-review-reminder` (under `messaging-event-driven`)
and `openapi-contract-reminder` (under `java-spring-backend`) as `plannedHooks`. The user's Phase
3 brief defines detailed skill requirements but no concrete hook trigger/threshold/output spec.

**Decision:** For Phase 3, ship skills + templates + `profiles.json` updates only — no
`hooks/*.sh` or `hooks/*.ps1` file is created or modified, and both hooks stay in `plannedHooks`.
**This decision — that Phase 3 itself does not build any hook — is Accepted and final for this
phase**, not open for reconsideration mid-phase. What remains **Deferred** is a separate, narrower
thing: the actual future *implementation* of `messaging-review-reminder` and
`openapi-contract-reminder` themselves, which is pushed to a later phase once there's a concrete
spec for their trigger/threshold/output.

**Reasoning:** Avoid scope creep beyond what was explicitly requested. A hook authored without a
concrete trigger spec (which file patterns, which message content, blocking vs reminder) would be
guesswork; better to define it once the two skills' concrete checks have been exercised at least
once. This also keeps rules 5-8 (no `jq`/`python3` in hooks, shared `hooks/lib/claude-json.sh`)
moot for this phase — there is nothing to apply them to yet.

**Consequences:** A future phase should design `messaging-review-reminder` /
`openapi-contract-reminder` from the concrete review checklists in `event-driven-reviewer` /
`microservices-patterns-reviewer`, once those exist, rather than from scratch. Re-opening the
"should Phase 3 ship a hook" question itself would require a new decision entry, not just editing
this one.

### D005 - `payments-fintech` profile stays out of scope

**Date:** 2026-07-12

**Status:** Deferred

**Context:** The user's stated stack includes "Payments/fintech workflows," and `profiles.json`
already declares a separate `payments-fintech` profile (`plannedSkills`:
`stripe-payments-reviewer`, `payment-idempotency-reviewer`), distinct from
`messaging-event-driven`. The Phase 3 "Skills preferidas" section only requested
`event-driven-reviewer` and `microservices-patterns-reviewer` (+ optional
`contract-testing-reviewer`, resolved by D002).

**Decision:** `payments-fintech` remains fully planned/unshipped; not part of Phase 3.
`event-driven-reviewer`'s "idempotent consumers" check is scoped to message-consumer idempotency
(deduplication on redelivery), not payment-API idempotency keys — related concepts, but distinct
review concerns.

**Reasoning:** Explicit skill scoping in the user's brief; avoiding scope creep into a profile
that has its own dedicated future phase.

**Consequences:** A future phase must define `stripe-payments-reviewer` /
`payment-idempotency-reviewer` separately; `event-driven-reviewer` should not be stretched to
cover payment-specific idempotency just because the word "idempotent" appears in both.

### D006 - Drop `CONTRACT_TESTING.md` from `java-spring-backend.plannedTemplates`

**Date:** 2026-07-12

**Status:** Accepted

**Context:** Discovered during implementation (T006/T007). `profiles.json`'s
`java-spring-backend` profile declared `CONTRACT_TESTING.md` as a `plannedTemplates` entry
(alongside `OBSERVABILITY.md`), predating D002's decision to fold contract testing into
`microservices-patterns-reviewer` rather than shipping a standalone skill. While writing
`docs/_templates/MICROSERVICES_PATTERNS.md` (FR-004), its "Contract testing setup" section
already covers exactly what a separate `CONTRACT_TESTING.md` would (Pact/WireMock/broker/provider
verification) — SPEC.md did not originally call this out explicitly.

**Decision:** Remove `CONTRACT_TESTING.md` from `java-spring-backend.plannedTemplates`. Its
content lives in `docs/_templates/MICROSERVICES_PATTERNS.md`'s Contract testing setup section
instead. `OBSERVABILITY.md` is unaffected and stays planned.

**Reasoning:** Same rationale as D002 (don't duplicate/fragment contract-testing content across
two roadmap items when one already covers it) — keeping `CONTRACT_TESTING.md` planned would leave
a stale roadmap entry for content that already shipped under a different filename.

**Consequences:** A future contributor scanning `profiles.json`'s planned arrays won't see a
`CONTRACT_TESTING.md` placeholder and wonder why it was never built — the profile `note` field
now explains where the content actually is.
