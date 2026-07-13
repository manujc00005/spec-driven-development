# Plan: Phase 3 — Messaging / event-driven / microservices patterns

## Approach

2 independent skill deliverables + 2 independent template deliverables + 1 `profiles.json` update.
Skills and templates are fully independent of each other. The `profiles.json` update depends on
both skills/templates existing on disk first (rule 15: shipped items must exist physically before
being moved out of `plannedSkills`/`plannedTemplates`). No installer (`install.ps1`/`install.sh`)
code change is needed — the profile-driven install mechanism already exists (Phase 2); only the
manifest content changes.

## Files to CREATE

| File | Purpose | AC |
|---|---|---|
| `skills/event-driven-reviewer/SKILL.md` | Kafka/RabbitMQ/ActiveMQ delivery semantics, idempotency, retry/DLQ, ordering, schema evolution, correlation IDs/tracing, outbox, saga | AC-002 |
| `skills/microservices-patterns-reviewer/SKILL.md` | Service boundaries, sync/async, DB-per-service, distributed transactions, resilience patterns, contract compatibility | AC-003 |
| `docs/_templates/MESSAGING.md` | Broker topology / naming / consumer groups / schema registry / DLQ policy template | AC-006 |
| `docs/_templates/MICROSERVICES_PATTERNS.md` | Service boundary map / resilience policy / contract-testing setup template | AC-006 |

## Files to MODIFY

| File | Change | AC |
|---|---|---|
| `profiles.json` | `messaging-event-driven`: move 2 skills + 2 templates from planned→shipped; drop 4 superseded plannedSkills. `java-spring-backend`: drop `contract-testing-reviewer` from plannedSkills; update note. | AC-005 |
| `README.md` | Skill count (40→42), repository-structure tree (add 2 skill entries + 2 template entries), "Status of this repository" checklist, "Roadmap" completed list, "Profiles" table/section. No change to blockchain-disabled wording, java-spring-backend-default wording, or Graphify status. | AC-010, AC-011 |
| `docs/INSTALL.md` | Only the "What you'll see for planned items" example, which currently says `messaging-event-driven` "mostly consists of Phase 3 candidates that don't exist in the repo yet" — update to reflect that 2 skills + 2 templates now exist and only the hook remains planned. No other section is touched unless review finds another stale claim. | AC-011 |

## Files NOT touched

- `C:\ProgramData\ClaudeConfig\*`
- `install.ps1` / `install.sh` (no logic change — manifest-only + doc update; the multi-profile
  combination mechanism this plan relies on already exists and works today)
- Any `hooks/*.sh` or `hooks/*.ps1` (no hook shipped this phase — AC-007)
- Existing skills (`backend-review`, `api-review`, `database-review`, `security-review`,
  `architect-review`, `test-engineer`, etc.) — referenced via "Extends", never modified
- `blockchain-crypto` and `payments-fintech` profile entries in `profiles.json`
- `settings.template.json`
- Application code in any target project
- `docs/INSTALL.md` beyond the one stale-example fix noted above

## Design decisions

Full rationale in `DECISIONS.md`. Summary:

- Two consolidated skills instead of six granular ones — `event-driven-reviewer` absorbs
  broker-specific concerns (Kafka/RabbitMQ/ActiveMQ), outbox, and saga/compensation as sections,
  rather than becoming four separate `SKILL.md` files (D001).
- Contract testing (Pact/WireMock/OpenAPI compatibility) is a section inside
  `microservices-patterns-reviewer`, not a standalone skill — it explicitly delegates
  OpenAPI/DTO/breaking-change mechanics to `api-review` (D002).
- Both new skills ship as `skills` of the `messaging-event-driven` profile (`default: false`),
  not `java-spring-backend`. **Verified against the actual installer code** (`install.sh` /
  `install.ps1`): this is an **optional profile**, not an automatic overlay — once any
  `--profile`/`-Profile` flag is passed, only `core` + the explicitly listed profile(s) install;
  the default-profile fallback only fires when *no* profile flag is given at all. Getting both
  `java-spring-backend` and `messaging-event-driven` requires explicitly listing both
  (`--profile java-spring-backend,messaging-event-driven` or repeating the flag) — multiple
  profiles are already supported by the existing installer, this plan does not need to add that
  capability (D003).
- No new hooks this phase — `messaging-review-reminder` and `openapi-contract-reminder` stay
  planned; the decision not to build hooks in Phase 3 is final for this phase, only the future
  *implementation* of those two hooks is deferred (D004).
- `payments-fintech` profile is untouched — out of scope for this phase (D005).
- `README.md` and `docs/INSTALL.md` are updated for accuracy (skill/template counts, profile
  install semantics) — see Files to MODIFY above.

## Dependencies

- None external. Both skills are markdown review guides (like all existing skills in this repo) —
  no runtime dependency, no package install.

## Risks

- Scope overlap with `backend-review`/`api-review`/`database-review`/`security-review`/
  `architect-review` if "Extends" boundaries aren't kept precise — mitigated by AC-001 and an
  explicit "does not cover / see X instead" note in each new skill where overlap is likely.
- `profiles.json` drift (a shipped item declared before the file exists, or vice versa) — mitigated
  by creating skill/template files first, then updating the manifest, then verifying with the
  existing installer's own integrity check (`--dry-run --profile messaging-event-driven`).

## Test strategy

- Manual content review: cross-check each new `SKILL.md` against the full bullet list in
  `SPEC.md` FR-001/FR-002 (checklist, not automated).
- `install.ps1 -DryRun -Profile messaging-event-driven` / `install.sh --dry-run --profile
  messaging-event-driven` — confirms the installer's own shipped-item integrity check passes
  (no `[ERROR] ... declares a SHIPPED item that does not exist`) now that the two skills and two
  templates physically exist.
- `install.ps1 -DryRun -Profile java-spring-backend,messaging-event-driven` / the equivalent
  `install.sh` combined-profile form — confirms both profiles' shipped items are picked up
  together when explicitly combined (the actual, verified way to get both).
- No hook changes → no `bash -n` / functional hook tests needed this phase.
- Doc accuracy: grep `README.md` and `docs/INSTALL.md` for stale counts ("40 skill", "Phase 3
  candidates that don't exist") after the edits land.
- Secret scan on all new/modified files (AC-008) — same lightweight scan used in Phase 2.

## Rollback strategy

Revert the 4 new files, the `profiles.json` diff, and the `README.md`/`docs/INSTALL.md` diffs. No
installer code, no hook, and no other skill is touched, so rollback is a pure file/manifest/doc
revert with no migration concerns.

## PLAN verification checklist

- [x] The plan covers all acceptance criteria (AC-001 through AC-011).
- [x] The plan avoids behavior outside the spec (no new hooks, no payments-fintech, no
      blockchain-crypto, no installer code changes).
- [x] Risks are documented.
- [x] Test strategy is documented.
- [x] Rollback strategy is documented.
- [x] `SPEC.md` status has been updated to `Ready`.
