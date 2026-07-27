# Feature Spec: Token economy as a first-class framework principle

## Status

Done

## Problem

The framework already practices token economy in several disconnected places —
bounded reading lists (`skills/context-manager`, `agents/codebase-researcher.md`),
graph-first impact analysis (`skills/graphify-context`), cost-aware model routing
(`skills/sdd-orchestrate`, spec 004), and operational rules in
`CLAUDE.md.example` (`## Token economy`, line ~180) — but nothing names the
principle or ties the pieces together.

Two consequences:

1. **Positioning gap.** The industry is shifting from seat-based to usage-based
   (per-token) pricing. "Context discipline saves real money" is the strongest
   market argument for adopting this framework, and the README does not tell
   that story. The only trace is one bullet ("Model cost awareness") in Design
   principles.
2. **Enforcement gap.** Per the framework's own "Enforcement over convention"
   principle, a rule without a mechanism is prose. Today no artifact in the
   feature lifecycle requires the implementer to declare *what will be read*
   and *which model tier does what* before implementation starts, and
   `/spec-analyze` cannot verify context discipline because there is nothing to
   check.

## Goal

Elevate **"Context is a budget"** to a named, documented, and minimally
enforced framework principle:

- README positions it as a unifying design principle connected to the
  seat→usage pricing shift.
- A short `docs/TOKEN_ECONOMY.md` maps each rule of the principle to the
  existing mechanism that implements it (index, not duplicate).
- The PLAN.md template gains a **Context budget** section (bounded reading
  list + model-tier routing per phase), and `/spec-analyze` verifies its
  presence and minimum quality for new plans.
- The CONSTITUTION template gains a token economy section so downstream
  projects inherit the rule.

## Non-goals

- No extension of skill contracts (spec 018 surface) with context-budget
  fields — explicitly deferred to a future spec.
- No hooks, telemetry, or token measurement/accounting of any kind.
- No changes to orchestration logic in `sdd-orchestrate`, `context-manager`,
  `codebase-researcher`, or `graphify-context` — they are referenced, not
  modified.
- No retroactive editing of existing feature specs/plans (001–020).
- No changes to installer scripts beyond what is required for the new doc to
  be picked up (see Open questions).

## Users / Actors

- **Framework adopters** reading the README to decide whether to use SDD.
- **Agents** (Claude Code / Codex adapter) executing `/spec-plan` and
  `/spec-analyze` in downstream projects.
- **Downstream project maintainers** whose `specs/CONSTITUTION.md` is generated
  from the template by `/project-init`.

## Current behavior

- README `## 📐 Design principles` contains a single bullet, "Model cost
  awareness"; `## 🎯 Why it exists` does not mention pricing/cost.
- No `docs/TOKEN_ECONOMY.md` exists.
- The PLAN template exists in two places — embedded in
  `skills/spec-plan/SKILL.md` (line ~47) and shipped at
  `specs/_templates/PLAN.md` — and neither has a context/reading-list section.
- `skills/spec-analyze/SKILL.md` has an Analysis checklist and Output format
  with no notion of context budget.
- `specs/_templates/CONSTITUTION.md` has sections Project basics /
  Architecture / Quality gates / Billing boundary / Notes — no token economy.

## Desired behavior

- README presents "Context is a budget" as a named design principle that
  unifies the four existing mechanisms, and "Why it exists" contains a short
  paragraph on the seat→usage pricing shift.
- `docs/TOKEN_ECONOMY.md` states the principle and contains a rule→mechanism
  mapping table pointing at the existing skills/agents/config.
- New PLANs (021 onward) contain a `## Context budget` section with:
  a bounded reading list (files/globs the implementer may read) and a
  model-routing note (which phases need deep reasoning vs. mechanical work).
- `/spec-analyze` flags a missing or empty `## Context budget` section as a
  finding for new plans, and does **not** fail plans created before this spec.
- `/project-init` output inherits a token economy section from the
  CONSTITUTION template.

## Functional requirements

- FR-001: README `## 📐 Design principles` replaces the "Model cost awareness"
  bullet with a **"Context is a budget"** principle that subsumes model
  routing, bounded reading, graph-first analysis, and summaries-over-pastes.
- FR-002: README `## 🎯 Why it exists` gains one short paragraph (3–5 lines)
  connecting the framework to usage-based pricing economics. No marketing
  fluff; consistent with existing README tone.
- FR-003: New file `docs/TOKEN_ECONOMY.md` (~1 page) containing: the principle
  statement, a table mapping each rule to its implementing mechanism with repo
  paths, and a "what is NOT covered" note (no telemetry, no hard enforcement).
- FR-004: Both PLAN templates (`specs/_templates/PLAN.md` and the embedded
  template in `skills/spec-plan/SKILL.md`) gain a `## Context budget` section
  with two subsections: `Reading list` and `Model routing`. The two templates
  must remain identical in structure.
- FR-005: `skills/spec-plan/SKILL.md` PLAN verification checklist gains an item
  requiring the Context budget section to be filled (not left as placeholder).
- FR-006: `skills/spec-analyze/SKILL.md` Analysis checklist gains a context
  budget check; the Output format gains a corresponding finding section. The
  check reports a **warning** (not a blocker) when the section is missing, and
  a blocker only when the section exists but is empty/placeholder.
- FR-007: `specs/_templates/CONSTITUTION.md` gains a `## Token economy` section
  (rules only, following the template's concise style) that `/project-init`
  carries into generated constitutions.
- FR-008: `CLAUDE.md.example` `## Token economy` section gains a one-line
  cross-reference to `docs/TOKEN_ECONOMY.md` (no content duplication).
- FR-009: `adapters/codex/PARITY.md` is updated if the Codex adapter mirrors
  any of the changed skill prompts (spec-plan / spec-analyze), so parity status
  stays honest.

## Non-functional requirements

- Performance: n/a (docs and prompt templates only).
- Security: n/a.
- Observability: n/a (telemetry explicitly out of scope).
- Maintainability: `docs/TOKEN_ECONOMY.md` must reference mechanisms by repo
  path so drift is detectable; no rule text duplicated across more than one
  file (single source per rule, cross-references elsewhere).

## API / Interface changes

Prompt-level interfaces only:

- PLAN.md document contract: new `## Context budget` section (additive).
- `/spec-analyze` report contract: new finding section (additive).
- CONSTITUTION.md document contract: new `## Token economy` section (additive).

No code, CLI, or installer API changes.

## Data model changes

None.

## Edge cases

- **Pre-021 plans:** `/spec-analyze` run against features 001–020 (or any
  downstream plan created before adoption) must warn, not block, on the
  missing section (FR-006).
- **Template drift:** the PLAN template exists in two files; a change applied
  to only one would silently fork the contract — AC-003 covers both.
- **Codex adapter parity:** if the adapter embeds its own copies of the
  spec-plan/spec-analyze prompts, they must be updated or the gap recorded in
  `PARITY.md` (FR-009).
- **Re-run of `/project-init` on an existing constitution:** the skill already
  supports updating; the new section must be additive so re-runs do not
  destroy user content.
- **Trivial features:** a valid Context budget can legitimately be very short
  ("read only this folder"); the spec-analyze check must accept brevity and
  only reject emptiness/placeholders.

## Acceptance criteria

- AC-001: README Design principles contains a "Context is a budget" bullet
  naming the four mechanisms; the standalone "Model cost awareness" bullet is
  gone; "Why it exists" mentions usage-based pricing in ≤5 lines.
- AC-002: `docs/TOKEN_ECONOMY.md` exists, is ≤120 lines, and every mechanism
  row in its mapping table points to a path that exists in the repo.
- AC-003: `git grep "## Context budget"` matches in exactly two template
  locations: `specs/_templates/PLAN.md` and `skills/spec-plan/SKILL.md`, with
  identical subsection structure (`Reading list`, `Model routing`).
- AC-004: `skills/spec-analyze/SKILL.md` contains the context budget check in
  its Analysis checklist and a corresponding section in its Output format,
  with the warning-vs-blocker distinction from FR-006 stated explicitly.
- AC-005: `specs/_templates/CONSTITUTION.md` contains a `## Token economy`
  section with concrete rules (no TODO/placeholder markers).
- AC-006: `CLAUDE.md.example` references `docs/TOKEN_ECONOMY.md` exactly once;
  no rule text is duplicated between the two files.
- AC-007: `adapters/codex/PARITY.md` reflects the spec-plan/spec-analyze
  changes (either updated prompts or an honest "not yet mirrored" entry).
- AC-008: The PLAN.md created for this very feature (021) contains a filled
  `## Context budget` section — the feature dogfoods its own rule.

## Test scenarios

- Unit: n/a (no executable code).
- Integration: run the repo's CI consistency check (spec 007 tooling) if it
  validates template/skill structure; confirm it passes with the new sections.
- E2E: n/a.
- Manual:
  - Render README and confirm the principle reads coherently in context.
  - Dry-run `/spec-plan` mentally against the new template: confirm the
    Context budget section is generatable from a SPEC without extra input.
  - Run `/spec-analyze specs/features/021-token-economy-principle` after
    planning and confirm the new check fires correctly on its own plan.
  - Run `/spec-analyze` against a pre-021 feature (e.g. 019) and confirm the
    missing section produces a warning, not a blocker.

## Assumptions

- A-001: `docs/` files are consumed from the repo itself (README links) and do
  not need installer changes to be distributed; installers ship `skills/`,
  `agents/`, and `specs/_templates/`. If wrong, see OQ-001.
- A-002: The "four mechanisms" unified by the principle are: (1) cost-aware
  model routing (`sdd-orchestrate`), (2) bounded reading lists
  (`context-manager` skill + `codebase-researcher` agent), (3) graph-first
  impact analysis (`graphify-context`), (4) output discipline
  (summaries-over-pastes rules in `CLAUDE.md.example`).
- A-003: The spec-analyze warning-vs-blocker distinction is expressible in the
  skill's existing verdict vocabulary (it already distinguishes blocking from
  non-blocking findings); no new verdict states are introduced.
- A-004: Extending skill contracts (spec 018) with machine-readable
  context-budget fields is valuable but deliberately deferred; the `## Context
  budget` PLAN section is the minimal enforceable artifact for now.
- A-005: The English name "Context is a budget" is used in all artifacts
  (repo language is English), even though discussion happened in Spanish.

## Open questions

- OQ-001 (RESOLVED): installers copy only `specs/_templates/` and
  `docs/_templates/`, not top-level `docs/`. `docs/TOKEN_ECONOMY.md` is a
  framework-facing doc (README link), needs no manifest change, and does not
  trip the orphan-template check. See D001. A-001 confirmed.
- OQ-002 (RESOLVED): `scripts/check-consistency.sh` does not diff the two PLAN
  templates. AC-003 remains a manual review item, enforced this feature by
  editing both in lockstep + `git grep`. See D003. CI enforcement deferred to
  a future spec (telemetry/hard-gate is a non-goal here).

## Deferred follow-ups

- FU-001: Tighten the `/spec-analyze` Context budget check (and its Codex
  mirror) to treat the shipped template placeholder prose as "unfilled" →
  blocker, and define the verdict when one subsection is filled and the other
  is placeholder. Surfaced by QA review; route via `/spec-update` (FR-006).
- FU-002: Optional CI enforcement of structural sync between
  `specs/_templates/PLAN.md` and the embedded template in
  `skills/spec-plan/SKILL.md` (from OQ-002 / D003).
