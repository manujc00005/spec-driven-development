# Changelog

All notable changes to the SDD framework. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions are
[SemVer](https://semver.org) git tags. Each release maps to the spec trail
under `specs/features/` — the framework is developed with its own workflow.

> Note: the `version` field in `profiles.json` is the **manifest schema
> version** (installer compatibility), not the release version. Releases are
> tags.

## [Unreleased]

Spec 027 · Query-first graph access — the framework's own default was the expensive path.
Spec 025 · Workspace SDD — the first coverage of what happens *between* projects.

### Changed

- **The graph access ladder is inverted (spec 027).** Every Graphify-aware artifact used to say
  "check `GRAPH_REPORT.md` first" and mention the CLI's scoped queries as an optional refinement.
  Measured on a 1.650-node graph (`graph.json` 3,2 MB, CLI 0.17.1): `graphify summary` costs **354
  tokens**, `review-analysis <file>` 222–262, `review-context <file>` 103–1.057 — against **7.101**
  for reading the report in full. **Orientation via `summary` is 20× cheaper**, because the scoped
  commands resolve the graph file inside the CLI process and it never enters context. Across a
  four-project workspace, four `summary` calls cost ~1.400 tokens against ~18.269 for the four
  reports.
  The ladder is now `summary` → per-file queries → targeted traversal → **full report as the
  documented exception** → never `graph.json`, stated identically in `graphify-context`,
  `context-manager`, `sdd-workspace-onboarding`, `agents/codebase-researcher.md`,
  `docs/WORKSPACE_SDD.md`, `docs/TOKEN_ECONOMY.md` and the Codex prompt.
- **`codebase-researcher` gets a request protocol, not the ladder.** It declares
  `tools: Read, Grep, Glob` and has no Bash tool by design, so it *cannot* run a query. Telling it
  to "query first" would be an instruction violated on every invocation. Instead it names the exact
  command it needs and hands back — and must not silently fall through to reading the report just
  because that is the only thing it can open (spec 027 D002).
- Graphify remains optional at every rung: CLI absent → the report becomes rung 1, both absent →
  `Grep`/`Glob` with the context marked partial. `check-consistency.sh` gains a `graph-ladder`
  presence check over the seven doctrine artifacts, plus three test cases. It asserts the commands
  are *named*, not their order — prose ordering is brittle to match and a false positive blocks CI
  on correct text (D003).

Spec 024 · Delivery-operations profile — the first coverage of what happens after merge.

### Added

- **Workspace SDD design** ([`docs/WORKSPACE_SDD.md`](docs/WORKSPACE_SDD.md)) — a layer above
  per-project SDD for features that cross repositories. Records what each project owns, how the
  projects depend on each other and which contracts bind them, in a `.sdd-workspace/` tree at the
  workspace root. Every relationship carries evidence and a closed-vocabulary confidence marker
  (`Confirmed` / `Inferred - requires confirmation` / `Unknown - requires confirmation`), so an
  inference is never recorded as a fact. Cross-project features start with an `IMPACT_MAP.md`, and
  no project outside that map may be modified. Design and documentation only — no orchestration
  code, no installer change, no new agent.
- **`/sdd-workspace-onboarding`** — detects the projects in a workspace folder (by manifest and
  structure, so monorepos and folders of clones both work), summarises each from bounded sources,
  derives cross-project edges with cited evidence, and writes the `.sdd-workspace/` layer. Stops
  for approval before reading deeply, and never writes inside a child project except a
  user-approved Graphify refresh.
- **Ten workspace templates** under [`docs/_templates/`](docs/_templates/), all `WORKSPACE_`-prefixed
  and declared in `profiles.json` so the installer actually ships them: `WORKSPACE_CONTEXT`,
  `WORKSPACE_PROJECTS`, `WORKSPACE_DEPENDENCY_GRAPH`, `WORKSPACE_INTEGRATION_CONTRACTS`,
  `WORKSPACE_SHARED_DECISIONS` (seeded with the D001–D010 baseline), `WORKSPACE_GUARDRAILS`,
  `WORKSPACE_FEATURE_README`, `WORKSPACE_IMPACT_MAP`, `WORKSPACE_PROJECT_CHANGES`,
  `WORKSPACE_VALIDATION`. They first shipped in a `workspace/` subdirectory, which passed CI and
  reached no adopter — `install.sh` copies templates by name and does not recurse. Caught by running
  the install for real; see spec 025 D014, and note that structural CI cannot detect this class of
  defect.
- **Graphify documented as a per-project accelerator for multi-project work** — the workspace layer
  consumes each project's bounded `.graphify/GRAPH_REPORT.md` rather than reading repositories in
  full, and never the raw graph file. There is no merged workspace-wide graph: a super-graph across
  every repository would be larger than any single report and could not be consumed within a bounded
  context. Graphify stays optional; its absence marks the context *partial* and never blocks.
- **`sdd-workspace-onboarding.md` Codex prompt** ([`adapters/codex/prompts/`](adapters/codex/prompts/))
  — the same procedure in prompt packaging, with no native-agent claim and no global configuration.
- `scripts/check-consistency.sh` gains a **`workspace` check class**: the guide, the skill and all
  ten templates must exist, the Codex workspace prompt must exist whenever `adapters/codex/` does,
  and no shipped document may claim Graphify is required or instruct loading the graph file
  wholesale. Claim detection is sentence-scoped with negator suppression, so existing correct
  prohibitions stay clean — covered by a dedicated negative test.

- **`delivery-operations` profile** (8th profile) — reviews how code reaches a machine and stays
  alive there. Optional overlay, combinable with any stack profile:
  `--profile next-prisma-web,delivery-operations`.
- **`/deployment-review`** — the deploy *procedure*: step ordering and stated prerequisites,
  idempotency and what a re-run does after a partial failure, converge vs first boot, rollback
  including the point of no return, secret placement (`ps` exposure, world-readable windows,
  fail-closed vs silent degradation), and **procedure fragmentation as a High-severity finding** —
  an ordered procedure that exists in three documents and in full in none cannot be followed.
- **`/container-review`** — Dockerfile and Compose: image pinning, running as root, healthcheck
  semantics, volume lifecycle (what `down -v` destroys), build-arg secrets surviving in image
  history, multi-stage inheritance, and **port binding as the real perimeter** — Docker inserts
  iptables rules ahead of the host firewall, so a `ufw` rule is not evidence a published port is
  closed.
- **`/pipeline-review`** — what a pipeline actually verifies versus what its job names imply. The
  canonical case: `lint` + `typecheck` + `test` with no build, on a project whose deployable *is* a
  build. Also gating vs reporting, migration-drift detection, secret exposure in logs and
  `pull_request_target`-shaped triggers, artifact provenance, and cache keys that serve stale
  artifacts.
- **`/release-readiness`** — a Go/No-go gate, not a review. Records every precondition as
  *rehearsed* / *written but untested* / *absent*, where "written but untested" never counts as
  satisfied and an undated "yes" is downgraded. Asks whether the rollback was **executed**, the
  restore **rehearsed**, and whether anything would surface a *silent* failure.
- **`docs/_templates/RUNBOOK.md`** — gives the ordered deploy procedure a single home, with dated
  last-followed/last-rehearsed lines that feed `/release-readiness` directly, plus a
  **known counter-intuitive details** section for the knowledge that dies when undocumented.
- `review-all` now detects **Deployment by artifact presence, not spec wording**, and routes to the
  three artifact reviewers. Verified both ways against scratch fixtures: it fires on a repository
  with a Dockerfile and a workflow, and stays silent on one with neither.

### Fixed

- **`kubernetes-deployment-reviewer` was referenced in shipped artifacts and never existed.**
  `skills/spring-security-reviewer/SKILL.md` handed off to it and `docs/_templates/DEPLOYMENT.md`
  told users to run it. Both repointed; the Kubernetes gap is now named honestly rather than
  promised.
- Six unguarded "61 skills" claims in `docs/AGENTIC_ROUTING.md`, `adapters/README.md`,
  `adapters/claude/README.md`, `adapters/codex/prompts/README.md` and `adapters/codex/PARITY.md`.
  `check-consistency.sh` guards count claims only inside `README.md`, so these had no gate —
  extending the checker is recorded as a follow-up (spec 024 OQ-5).

### Not shipped, deliberately

- **`rightsizing-advisor` — the eval said no.** The planned mindset counterweight was written, then
  measured with `scripts/skill-eval.sh` per `CONTRIBUTING.md`: **control 0/5** on
  `claude-sonnet-5`, verdict `NO-BASELINE-FAILURE`. Every control rep declined the unjustified
  Kubernetes upgrade unprompted, so the skill had no demonstrated problem to solve. It moved to
  `plannedSkills`; the scenario and result are committed
  (`evals/results/rightsizing-advisor-2026-08-05.md`). This is spec 022's harness used for a real
  decision for the first time — and it changed the outcome.
- **`iac-review` and `kubernetes-review`** — declared `plannedSkills`. Neither had an evidence base
  in this feature, and a Kubernetes reviewer in the profile's first release would read as an
  endorsement regardless of wording. The four shipped reviewers state plainly that IaC state
  semantics and manifest semantics are covered by no shipped skill.

### Counts

Skills 61 → 65 · Profiles 7 → 8 · Templates 22 → 23 · Agents 8 (unchanged, no new agent) ·
Hook families 12 (unchanged).

Specs 016–021 · Installer hooks/lib fix, planned skills shipped, agentic routing layer,
provider-adapter layer and a first Codex adapter, security-agent hardening, skill-routing
and spec-status authority.

### Added
- **Spec Status Authority** (spec 021) — `sdd-guardrails` section 11 now states the
  `SPEC.md` status machine as an authority table: each transition has exactly one
  authorized performer (`/spec-plan` → `Ready`, `/spec-implement` → `In Progress`,
  `/spec-review` → `In Review`, `/spec-close` → `Done`) with the precondition each must
  verify. No other skill, agent, or ad-hoc edit may promote a status, and writing the
  status string is explicitly not the same as passing the gate it represents — a
  hand-written `In Review` silently defeats `/spec-close`'s own precondition check. The
  rule is mirrored into the four owning skills, into `spec-create`/`spec-clarify`/
  `spec-analyze`/`sdd-orchestrate` as a prohibition, and into
  `agents/solution-architect.md`'s forbidden actions. Documented honestly as a convention:
  a tool-call hook can see a `Status` line change but cannot tell which skill drove it, so
  nothing enforces this mechanically (spec 021 D001).
- **Negative triggers on confusable skills** (spec 021) — 21 skill descriptions gained a
  one-sentence `Not for … — use /…` clause naming the correct sibling, covering the pairs
  that actually overlap at routing time (`spec-create`/`spec-clarify`/`spec-update`,
  `spec-plan`/`spec-analyze`/`architect-review`, `spec-review`/`qa-review`/`review-all`,
  `debugger`/`root-causer`, `security-review`/`threat-modeler`, `verifier`/`qa-review`,
  `scope-keeper`/`refactor-review`, `context-manager`/`graphify-context`,
  `sdd`/`sdd-orchestrate`). Bounded to documented pairs rather than all 61 skills, since
  every description is a standing per-session context cost (D003), and kept to one calm
  sentence rather than block-style ALL-CAPS warnings (D002).
- **Hardened `security-reviewer` agent** (spec 020) — now the framework's explicit owner of
  vulnerability hunting (named taxonomy: injection, broken authN/authZ and tenant isolation,
  SSRF/CSRF, deserialization, file handling, race/TOCTOU, secrets/crypto, supply chain,
  information exposure, abuse resistance), attack anticipation (abuse cases per entry point
  and trust-boundary mapping *before* reading the implementation), and RGPD/LOPDGDD/AEPD
  review via the `privacy-compliance-review` skill. Review discipline: source-to-sink
  tracing separates **Confirmed** from **Potential** findings, structural verification is
  preferred over call-site spot-checks, and a plausibility filter keeps inapplicable
  findings out. Read-only tools and boundaries unchanged; no scanner/pentest capability is
  claimed.
- **Provider-adapter layer** (spec 019) — `docs/PROVIDER_ADAPTERS.md` and an `adapters/`
  tree separating the provider-neutral **SDD Core** (SPEC/PLAN/TASKS/DECISIONS lifecycle,
  review gates, skill contracts, agent responsibility model, guardrail intent) from
  per-provider packaging. `adapters/README.md` is the adapter registry + capability/honesty
  matrix; `adapters/claude/README.md` is a pointer — the Claude Code adapter remains the
  repository root, and no file was moved.
- **Codex adapter** (spec 019) — a first, **prompt-based** adapter under `adapters/codex/`:
  an `AGENTS.md` operating guide, a curated lifecycle-spine of prompts (create → plan →
  analyze → implement → review → close, plus a guardrails/consistency pass) derived from the
  core skills, an example config, and a self-contained, **copy-only** `install-codex.{sh,ps1}`.
  Honest by design — guardrails are conventions (not enforced hooks), the six roles are
  personas (not native subagents with a `tools:` grant), only the lifecycle spine is ported
  (not all 61 skills), and it is **unverified against a live Codex CLI**. The gaps are
  enumerated in `adapters/codex/PARITY.md`.
- **`install-all.{sh,ps1}`** (spec 019) — a thin convenience wrapper that installs both
  adapters by *calling* each installer in order; it does not modify or reimplement
  `install.sh`/`install.ps1`. `--codex-target` installs the per-project `AGENTS.md`; without
  it the Codex prompts still install globally and `AGENTS.md` is skipped — it is never written
  into the current directory or the framework repo itself (a hard guard refuses the latter).
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
- Documentation repositioned as **provider-aware** rather than Claude-specific (spec 019):
  the README header, "What is this?", and `docs/AGENTIC_ROUTING.md`'s "Provider positioning"
  now frame SDD as a provider-neutral core with Claude Code as the primary adapter and Codex
  as a second, prompt-based adapter. No overclaiming — Claude/Codex parity is explicitly
  disclaimed. Count markers and validated badges are unchanged.
- `java-spring-reviewer`, `spring-boot-api-reviewer`, and `event-driven-reviewer` (spec
  018) no longer name external, unshipped `java-spring`/`api-design` subagents as their
  routing target — they now route through the repo's own `domain-reviewer` agent. Review
  logic and checklists are unchanged; only the ownership/routing wording changed.

### Fixed
- `security-review` and `privacy-compliance-review` (spec 020) delegated to `security` /
  `gdpr-spain` subagents this repo never shipped — in any self-contained install the primary
  path could not work and every run fell back to the generic checklist ("el agente security
  no está disponible"). Both skills now delegate to the shipped `security-reviewer` agent
  (their `## SDD Contract` blocks already declared it as `primary_agent`); the inline
  checklists remain as the documented fallback for agent-less sessions. Same drift class,
  same fix as spec 018 D006 (`java-spring`/`api-design` → `domain-reviewer`). A user-level
  stopgap skill created downstream (`software-security-review`) was unified back into the
  agent and retired with a backup (spec 020 D004).
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
- The spec-019 provider-adapter layer is **purely additive**: `profiles.json`, the Claude
  installers (`install.sh`/`install.ps1`), the hook scripts, the settings templates, and
  every `skills/`/`agents/`/`hooks/` file were left untouched. The Codex adapter is honest
  about its limits (prompt-based, no enforced hooks, no native subagents, no profile-filtered
  install) and remains unverified against a live Codex CLI — a tracked follow-up, mirroring
  the structural-vs-live distinction this changelog already draws for the lifecycle agents.

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
