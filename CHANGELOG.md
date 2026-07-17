# Changelog

All notable changes to the SDD framework. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions are
[SemVer](https://semver.org) git tags. Each release maps to the spec trail
under `specs/features/` — the framework is developed with its own workflow.

> Note: the `version` field in `profiles.json` is the **manifest schema
> version** (installer compatibility), not the release version. Releases are
> tags.

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
