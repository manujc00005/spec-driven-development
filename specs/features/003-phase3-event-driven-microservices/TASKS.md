<!-- Extracted from skills/spec-plan/SKILL.md — kept in sync with that skill's template. -->

# Tasks: Phase 3 — Messaging / event-driven / microservices patterns

## Phase 1: Preparation

- [x] T001 - Verify `git status --short` is clean (no uncommitted Phase 0/1/2 work) before starting. Covers: process gate (user rule).
- [x] T002 - Read `specs/features/002-phase2-java-spring-profile/*` and `specs/_templates/*` for structural conventions. Covers: consistency with existing SDD docs.
- [x] T003 - Inspect current `profiles.json`, `skills/`, and existing reviewer skill descriptions (`backend-review`, `api-review`, `database-review`, `security-review`, `architect-review`, `test-engineer`) to map "Extends" boundaries before writing new skills. Covers: AC-001.
- [x] T003a - Verify the actual `--profile`/`-Profile` combination semantics by reading `install.sh`/`install.ps1` source (not assuming) — confirm whether requesting one profile also installs the default profile, and how to combine profiles. Covers: AC-011.

## Phase 2: Implementation

- [x] T004 - Write `skills/event-driven-reviewer/SKILL.md` covering Kafka/RabbitMQ/ActiveMQ, delivery semantics, idempotent consumers, retry/backoff, DLQ/poison messages, ordering, schema evolution, correlation IDs/trace propagation, outbox, saga/compensation, with explicit "Extends" section. Covers: FR-001, AC-001, AC-002.
- [x] T005 - Write `skills/microservices-patterns-reviewer/SKILL.md` covering service boundaries, bounded contexts, sync vs async, shared-DB vs DB-per-service, distributed transactions, saga vs orchestration, timeouts/retries/circuit-breaker/bulkhead, deployment coupling, API ownership, and a Contract compatibility section (Pact/WireMock/OpenAPI/breaking changes) that defers to `api-review`. Covers: FR-002, AC-001, AC-003, AC-004.
- [x] T006 - Write `docs/_templates/MESSAGING.md`. Covers: FR-003, AC-006.
- [x] T007 - Write `docs/_templates/MICROSERVICES_PATTERNS.md`. Covers: FR-004, AC-006.
- [x] T008 - Update `profiles.json`: `messaging-event-driven` (planned→shipped for 2 skills + 2 templates; drop 4 superseded plannedSkills; update note), `java-spring-backend` (drop `contract-testing-reviewer` from plannedSkills; update note). Also dropped `CONTRACT_TESTING.md` from `java-spring-backend.plannedTemplates` — new decision D006 (superseded by `MICROSERVICES_PATTERNS.md`'s Contract testing setup section). Covers: FR-005, FR-006, AC-004, AC-005.
- [x] T009 - Update `README.md`: skill count (40→42), repository-structure tree (add 2 skill entries + 2 template entries), "Status of this repository" checklist, "Roadmap" completed list, "Profiles" table/section — worded per the verified semantics from T003a (optional profile, explicit combination required; no "installed regardless" claim). Did not change the blockchain-disabled, java-spring-backend-default, or Graphify-status wording. Covers: FR-007, AC-010, AC-011.
- [x] T010 - Update `docs/INSTALL.md`'s "What you'll see for planned items" example only, to reflect that `messaging-event-driven` now has 2 shipped skills + 2 shipped templates (only the hook stays planned). Rest of the file left untouched. Covers: FR-008, AC-011.

## Phase 3: Verification

- [x] T011 - Cross-check `event-driven-reviewer` and `microservices-patterns-reviewer` content against every bullet in SPEC.md FR-001/FR-002 (manual checklist, via targeted grep). All 19 event-driven bullets and all 12 microservices-patterns bullets confirmed present (3 contract-testing terms needed a second, looser grep pass due to hyphenation — concepts confirmed present, not missing). Covers: AC-002, AC-003.
- [x] T012 - Confirm no `kafka-reviewer`/`rabbitmq-reviewer`/`outbox-pattern-reviewer`/`saga-orchestration-reviewer`/`contract-testing-reviewer` directory exists under `skills/`. Confirmed absent. Covers: AC-004.
- [x] T013 - Run `install.ps1 -DryRun -Profile messaging-event-driven` (`install.sh --dry-run` hit the pre-existing "python3 not on PATH" environment limitation in this Git Bash shell — expected per D002/D003, not a regression) and confirm no `[ERROR]` about missing shipped items. Confirmed: exit 0, "Active profiles: core, messaging-event-driven" only, both skills + both templates picked up. Covers: AC-005.
- [x] T014 - Run `install.ps1 -DryRun -Profile java-spring-backend,messaging-event-driven` and confirm both profiles' shipped items appear together. Confirmed: exit 0, "Active profiles: core, java-spring-backend, messaging-event-driven", planned list correctly shows only `observability-reviewer`/`openapi-contract-reminder`/`messaging-review-reminder`/`OBSERVABILITY.md`. Covers: AC-011.
- [x] T015 - Confirm `blockchain-crypto.disabled == true`, `defaults.profile == "java-spring-backend"`, `defaults.buildTool == "maven"` are unchanged in `profiles.json`. Confirmed via `ConvertFrom-Json`. Covers: AC-005 (rules 9-12).
- [x] T016 - Confirm no `hooks/*.sh` or `hooks/*.ps1` file was created or modified. Confirmed via `git status --short`. Covers: AC-007 (rules 5-8).
- [x] T017 - Grep `README.md` and `docs/INSTALL.md` for stale references after the edits land. Confirmed clean. Covers: AC-010, AC-011.
- [x] T018 - Secret scan on all new/modified files. No hits. Covers: AC-008.
- [x] T019 - `git status --short` review — confirmed only the expected files changed, nothing under `C:\ProgramData\ClaudeConfig`, nothing committed. Covers: AC-009.
- [x] T019a - Additionally confirmed unknown-profile and explicit-disabled-`blockchain-crypto` requests both fail with a clear `[ERROR]` and exit code 1, before any files are touched (installer validations required by this implementation round, beyond the original TASKS.md scope).

## Phase 4: Review

- [x] T020 - `/spec-review` against this SPEC/PLAN/TASKS. Verdict: PASS. All 11 ACs re-verified independently this round (event-driven-reviewer/microservices-patterns-reviewer bullet coverage, no forbidden skill dirs, hooks untouched, profiles.json invariants, README/docs/INSTALL overlay wording). README skill count verified against the staged Phase 3 state. Unrelated working-tree changes were intentionally excluded from this commit.
- [x] T021 - `/qa-review` for edge cases and regressions. Verdict: PASS. PowerShell dry-runs (messaging-event-driven alone, combined with java-spring-backend, unknown profile, disabled blockchain-crypto) all behave exactly as specified. `bash -n` clean on `install.sh` and all `hooks/*.sh`. `python3` still absent from this Git Bash shell — documented as a pre-existing environment limitation (D002/D003), not a regression; `install.sh`'s own dry-runs correctly fail loud with the documented message. Secret scan clean. No stale "40 skills" references remain.
- [x] T022 - `/spec-close` — gate satisfied (status was `In Review`), all 11 ACs confirmed covered, no open questions to resolve (SPEC.md has no Open Questions section), no unspecified behavior beyond what DECISIONS D006 already documents. `SPEC.md` status → `Done`. No commit made.
