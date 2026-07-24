# Changelog

All notable changes to the SDD framework. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions are
[SemVer](https://semver.org) git tags. Each release maps to the spec trail
under `specs/features/` — the framework is developed with its own workflow.

> Note: the `version` field in `profiles.json` is the **manifest schema
> version** (installer compatibility), not the release version. Releases are
> tags.

## [Unreleased]

Specs 016–018 · Installer hooks/lib fix, planned skills shipped, agentic routing layer.

### Added
- **Six lifecycle agents** (spec 018) giving the framework's skills an accountable
  consumer: `codebase-researcher` (bounded research, Graphify-first, read-only),
  `solution-architect` (SPEC/PLAN/TASKS/DECISIONS, pre-implementation test strategy,
  specs-only writes), `implementer` (executes approved TASKS within explicit file
  boundaries, the only lifecycle agent that edits application code), `security-reviewer`
  (auth/secrets/payments risk findings, read-only), `domain-reviewer` (stack/domain
  reviewer skills by active profile, read-only), and `final-conformance-reviewer`
  (SPEC → PLAN → TASKS → DIFF → TESTS → REVIEW traceability verdict, read-only). These
  are a separate, independent layer from the existing `deep-reasoner`/`fast-worker`
  model-tier agents (unchanged) — see `docs/AGENTIC_ROUTING.md`.
- `## SDD Contract` metadata block on all 61 skills (`category`, `primary_agent`,
  `secondary_agents`, `profile_scope`, `writes_code`/`writes_specs`/`analysis_only`,
  `side_effects`, `provider_specific`) — every skill now declares which agent owns it.
  Schema documented in `specs/features/018-agentic-routing-and-skill-contracts/CONTRACT_SCHEMA.md`.
- Additive `agentRouting` map in `profiles.json` for the five non-core, non-disabled
  profiles — declares which reviewer skills `domain-reviewer` or `security-reviewer`
  own for that stack. Ignored by older installers (unknown key, no schema break).
- `docs/AGENTIC_ROUTING.md` — the skills-vs-agents explainer and routing model reference.
- `check-consistency.sh` now validates: every skill's `## SDD Contract` parses with
  required fields and known enums; every `primary_agent`/`secondary_agents` entry
  resolves; every `agentRouting` target and routed skill is real; every non-core profile
  skill is covered by `agentRouting` (or explicitly exempted); `blockchain-crypto` stays
  disabled and unrouted; no `test-engineer` agent exists; `deep-reasoner`/`fast-worker`
  keep their declared models.
- 8 skills promoted from planned to shipped (spec 017), completing every
  `plannedSkills` entry in `profiles.json`:
  `observability-reviewer` (java-spring-backend);
  `stripe-payments-reviewer` + `payment-idempotency-reviewer`
  (payments-fintech — the profile ships content for the first time);
  `prisma-migration-reviewer` + `nextjs-server-actions-reviewer`
  (next-prisma-web); `aeo-review` + `geo-review` + `ai-visibility-review`
  (seo-geo-addon — full SEO family, all gated on `specs/SERVICES.md`
  contracts with the upsell-log fallback).
- Stack-specific reviewer routing table in `/review-all` and profile-gated
  detection lines in `/sdd` — the pre-existing stack reviewers
  (java-spring, event-driven, …) are now routed there too, not only the new ones.
- `scripts/install.test.sh` — regression test for the installer (spec 016):
  fresh-install hooks/lib presence, git-guardrails exit-2 blocking behavior,
  idempotent re-run.

### Changed
- `java-spring-reviewer`, `spring-boot-api-reviewer`, and `event-driven-reviewer` (spec
  018) no longer name external, unshipped `java-spring`/`api-design` subagents as their
  routing target — they now route through the repo's own `domain-reviewer` agent. Review
  logic and checklists are unchanged; only the ownership/routing wording changed.

### Fixed
- `install.sh` / `install.ps1` never copied `hooks/lib/` in profile mode,
  leaving every lib-sourcing hook (git-guardrails, sdd-spec-guard,
  java-build-test-guard, maven-compile, spring-config-guard) crashing with
  exit 1 on fresh installs — git-guardrails silently stopped blocking
  dangerous git commands (spec 016, found by the 2026-07-21 integration audit).

### Notes
- Skills remain reusable capabilities; agents are the accountable actors that consume
  them — no skill was converted into an agent, and no skill was deleted or renamed.
- Claude Code compatibility is preserved: all agent files use the same standard
  frontmatter (`name`, `description`, `tools`, and `model` only where already used);
  installers already copied `profiles[*].agents` generically and needed no changes.
- The six lifecycle agents are authored and validated (schema, routing, dry-run installs
  across all profiles) but have not yet been live-installed into a real Claude Code agent
  registry as part of this change — that remains a follow-up verification step, the same
  distinction this changelog already draws for `deep-reasoner`/`fast-worker` in 0.5.0.
- Graphify remains an optional accelerator, never a requirement — `codebase-researcher`
  degrades gracefully when no graph report exists, exactly as `context-manager` and
  `graphify-context` already did.

## [0.5.0] — 2026-07-17

Specs 010–012, 014 · Graphify first-class, audit closure, adoption horizon.

### Added
- `scripts/setup-graphify.{sh,ps1}` — one-step Graphify adoption: consented
  CLI install, graph generation (version-tolerant scope fallback), gitignore,
  curated docs scaffolding, and automatic hook wiring into the project.
- `graphify-scan-reminder` hook (PreToolUse on Grep/Glob): throttled
  graph-first nudge when a dependency graph exists; `SDD_GRAPHIFY_NUDGE=0`
  opt-out.
- Background graph auto-refresh in `graphify-stale-reminder` (SessionStart):
  detached, lock-protected, `SDD_GRAPHIFY_AUTO=0` opt-out.
- Second worked example: `examples/002-server-action-rate-limiting/`
  (TypeScript/Next.js) — sliding-window rate limiting, x-forwarded-for trust
  boundary with attack tests, zod validation, enumeration-resistant responses,
  and a security review whose real finding (SEC-001) is preserved in the trail.
- CI hardening: graphify test suite (66 cases), shellcheck (severity error),
  and a Windows job parsing every `.ps1` — sh/ps1 parity is machine-checked.
- README badges enforced by the consistency harness (`readme-badge` category,
  auto-synced by `--fix`); self-test counts read dynamically instead of
  hardcoded.
- `scripts/graphify.test.sh` — sandboxed suite for the Graphify layer (stubbed
  CLI, no npm needed).
- CHANGELOG.md, CONTRIBUTING.md, and GitHub issue templates.

### Fixed
- Graphify report detection: consumers looked for `GRAPH_REPORT.md` at the
  project root while the CLI writes `.graphify/GRAPH_REPORT.md` — hooks and
  skills now resolve the canonical path with a legacy fallback. The
  `graphify-stale-reminder` hook is now actually wired in both settings
  templates (docs claimed it; no template registered it).
- Race conditions: hook lock deletion between check and stat; `read` on closed
  stdin in `setup-graphify.sh`.
- Worked example renumbered `002` → `001` (no gap); spec 006 status normalized
  to the standard section format.

### Changed
- Graph-first token doctrine: `context-manager` and `graphify-context` derive
  reading lists from the graph (CLI queries preferred) before any repo-wide
  scan; documented across SDD-ORCHESTRATION, GRAPHIFY template, and
  CLAUDE.md.example.

## [0.4.0] — 2026-07-16

Specs 007–009 · CI, scaffolding parity, hook wiring.

### Added
- `scripts/check-consistency.sh` + self-test + GitHub Actions workflow:
  profiles.json ↔ disk ↔ settings templates ↔ README counters drift detection
  (`--fix` auto-corrects README markers).
- `scripts/wire-hooks.{sh,ps1}` — additive, idempotent hook wiring into a
  project's `.claude/settings.json` with timestamped backups;
  `settings.template.sh.json` for macOS/Linux.
- Per-project specs support templates (SPECS-README, SDD-GUARDRAILS,
  CLAUDE-SDD); `/project-init` scaffolds the full `specs/` structure and
  `/sdd` gates on it.

## [0.3.0] — 2026-07-14

Specs 004–006 · Orchestration, onboarding, first example.

### Added
- Multi-model orchestration: `deep-reasoner` (Opus) and `fast-worker` (Sonnet)
  agents + `/sdd-orchestrate` skill with cost-control doctrine.
- `/sdd-onboard` — adaptive onboarding of existing projects (read-only
  analysis, context docs scaffolding) with optional Graphify detection.
- First worked example: payment webhook idempotency (Java/Spring).
- Framework hardening: macOS bash 3.2 compatibility, cross-platform polish,
  corrected hook wiring paths.

## [0.2.0] — 2026-07-13

Specs 002–003 · Stack profiles.

### Added
- `java-spring-backend` profile: JPA/transactions, Spring REST, Spring
  Security, JVM performance reviewers + build/config guard hooks.
- `messaging-event-driven` profile: event-driven and microservices-patterns
  reviewers, messaging templates.

## [0.1.0] — 2026-07-05

Specs 000–001 · Foundation.

### Added
- Core SDD lifecycle skills (`/spec-create` → `/spec-plan` → `/spec-analyze`
  → `/spec-implement` → `/spec-review` → `/spec-close`) with specialized
  reviews (QA, security, database, performance, API).
- Guardrail hooks (git-guardrails, sdd-spec-guard, status banner) in sh/ps1
  parity; profile-aware installer with dry-run and central-config model.
- Graphify-aware context layer (`context-manager`, `graphify-context`) with
  graceful degradation.

Versions 0.1.0–0.4.0 are retrospective milestones reconstructed from the spec
trail and commit history; v0.5.0 is the first tagged release.

[0.5.0]: https://github.com/manujc00005/spec-driven-development/releases/tag/v0.5.0
