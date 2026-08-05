# Decisions: Token economy as a first-class framework principle

## Decision log

### D001 - `TOKEN_ECONOMY.md` lives in top-level `docs/`, not `docs/_templates/`

**Date:** 2026-07-27

**Status:** Accepted

**Context:** The doc could go in `docs/` (framework-facing, README-linked) or
`docs/_templates/` (distributed per-project by the installer).

**Decision:** Place it in top-level `docs/`.

**Reasoning:** It is a narrative positioning document about the framework
itself, not a per-project template. OQ-001 confirmed installers copy only
`specs/_templates/` and `docs/_templates/`, so a top-level doc needs no
manifest change and won't trip the orphan-template check in
`scripts/check-consistency.sh`.

**Consequences:** The doc is not distributed into downstream projects; that is
intended. The per-project inheritance path is the CONSTITUTION template (D002).

### D002 - Enforcement = PLAN section + spec-analyze check; skill-contract fields deferred

**Date:** 2026-07-27

**Status:** Accepted

**Context:** The principle needs a mechanism (per "Enforcement over
convention"). Options ranged from a documented PLAN section to machine-readable
context-budget fields in skill contracts (spec 018) or a CI gate (spec 007).

**Decision:** Ship exactly one enforcement artifact now — the `## Context
budget` PLAN section verified by `/spec-analyze`. Defer skill-contract fields
and CI sync enforcement to future specs.

**Reasoning:** Minimal, reviewable, and telemetry-free (a non-goal). The PLAN
section is where reading-list and model-routing decisions naturally belong.

**Consequences:** Structural sync between the two PLAN templates and legacy
plan coverage are not machine-enforced; they remain manual review items
(see D003, D004).

### D003 - Both PLAN templates edited in lockstep; sync stays a manual review item

**Date:** 2026-07-27

**Status:** Accepted

**Context:** The PLAN contract exists twice — `specs/_templates/PLAN.md`
(shipped/installed, also read verbatim by the Codex adapter) and the embedded
copy in `skills/spec-plan/SKILL.md`. OQ-002 confirmed `check-consistency.sh`
does not diff them.

**Decision:** Edit both in a single task (T003) with byte-identical subsection
structure; verify with `git grep`. Do not add CI enforcement in this spec.

**Reasoning:** Adding a template-diff facility to CI is out of scope
(non-goal). A single-task edit plus grep verification is sufficient for a
two-file contract.

**Consequences:** Future edits to one template could silently fork the other;
accepted risk, flagged in PLAN Risks.

### D004 - spec-analyze: missing section = warning; empty/placeholder = blocker

**Date:** 2026-07-27

**Status:** Accepted

**Context:** A strict "section required" check would fail every pre-021 plan
(001–020) and every downstream plan authored before adoption.

**Decision:** `/spec-analyze` reports a **warning** when `## Context budget` is
absent, and a **blocker** only when the section exists but is empty or still
contains placeholder text. Reuse the skill's existing blocking/non-blocking
verdict vocabulary — no new verdict states.

**Reasoning:** Backward-compatible adoption; brevity-tolerant (a valid budget
can be one line). Aligns with SPEC edge cases "Pre-021 plans" and "Trivial
features".

**Consequences:** Adoption is gradual — old plans warn but still pass. The
blocker only bites when an author adds the section and leaves it unfilled.

### D005 - Codex parity: PLAN template inherited verbatim; analyze prompt mirrored by hand

**Date:** 2026-07-27

**Status:** Accepted

**Context:** `adapters/codex/PARITY.md` declares SPEC/PLAN/TASKS/DECISIONS use
the shared `specs/_templates/` verbatim, while `/spec-analyze` is a
hand-maintained prompt mirror at `adapters/codex/prompts/sdd-spec-analyze.md`.
The spec-plan prompt enumerates PLAN sections inline.

**Decision:** Rely on shared-template inheritance for the PLAN `## Context
budget` section (no separate Codex edit needed for the template body), but
explicitly mirror the analyze context-budget check into the Codex analyze
prompt and add "Context budget" to the inline section list in the Codex
spec-plan prompt (T007). Reconcile `PARITY.md`.

**Reasoning:** Keeps the honest-status principle intact — no silent parity gap.

**Consequences:** The Codex analyze prompt remains a manual mirror; recorded in
`PARITY.md` as prompt-based parity (its existing ⚠️ status is unchanged).
