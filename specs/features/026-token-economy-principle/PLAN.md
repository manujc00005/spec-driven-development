# Implementation Plan: Token economy as a first-class framework principle

## Summary

Name and document the **"Context is a budget"** principle, and add the one
enforcement artifact that makes it real: a `## Context budget` section in the
PLAN contract, checked by `/spec-analyze`. All changes are docs and
prompt-template edits — no application code, no installer logic, no telemetry.

## Related spec

`specs/features/026-token-economy-principle/SPEC.md`

## Context budget

### Reading list

Implementer may read only these (all paths relative to repo root):

- `README.md` — sections `## 🎯 Why it exists`, `## 📐 Design principles` only.
- `docs/` (top level, for the new `TOKEN_ECONOMY.md`; sibling docs for tone).
- `specs/_templates/PLAN.md`, `specs/_templates/CONSTITUTION.md`.
- `skills/spec-plan/SKILL.md`, `skills/spec-analyze/SKILL.md`.
- `CLAUDE.md.example` — `## Token economy` section only.
- `adapters/codex/PARITY.md`, `adapters/codex/prompts/sdd-spec-plan.md`,
  `adapters/codex/prompts/sdd-spec-analyze.md`.
- This feature folder.

Do **not** read: other feature specs (001–020), `scripts/*` (already inspected
during planning — see D005), profile skills, agents, hooks.

### Model routing

- Deep reasoning tier: none required — no algorithmic or architectural
  decisions remain; they are all resolved in DECISIONS.md.
- Standard/mechanical tier: all tasks are prose edits and template additions
  suitable for a single implementer pass. `/spec-implement` (or fast-worker)
  is sufficient throughout.

## Impacted areas

| Area | File(s) | Change |
|------|---------|--------|
| Positioning | `README.md` | Rewrite one principle bullet; add pricing paragraph |
| New doc | `docs/TOKEN_ECONOMY.md` | Create (principle + rule→mechanism table) |
| PLAN contract (shipped) | `specs/_templates/PLAN.md` | Add `## Context budget` |
| PLAN contract (skill) | `skills/spec-plan/SKILL.md` | Add `## Context budget` to embedded template + checklist item |
| Analyze contract | `skills/spec-analyze/SKILL.md` | Add checklist check + output section (warning/blocker) |
| Constitution template | `specs/_templates/CONSTITUTION.md` | Add `## Token economy` section |
| Cross-ref | `CLAUDE.md.example` | One-line pointer to the new doc |
| Codex parity | `adapters/codex/prompts/sdd-spec-analyze.md`, `adapters/codex/prompts/sdd-spec-plan.md`, `adapters/codex/PARITY.md` | Mirror analyze check; update PLAN section list; record parity |

## Proposed approach

1. **Positioning first** (README + doc) so the vocabulary is fixed before
   touching contracts. Write `docs/TOKEN_ECONOMY.md` as the canonical statement;
   README and other files cross-reference it (single source per rule, FR-003 /
   NFR maintainability).
2. **Contract edits** to both PLAN templates in lockstep, keeping subsection
   structure (`Reading list`, `Model routing`) byte-identical to avoid the
   template fork risk (AC-003). Add the PLAN verification checklist item.
3. **Enforcement** in `spec-analyze`: one Analysis-checklist line + one Output
   section, encoding the warning-vs-blocker rule (D004).
4. **Inheritance**: add `## Token economy` to the CONSTITUTION template.
5. **Parity + cross-ref last**: mirror the analyze check into the Codex prompt,
   update the spec-plan prompt's inline section enumeration, add the
   `CLAUDE.md.example` pointer, and reconcile `PARITY.md`.
6. **Dogfood**: this PLAN already carries a filled `## Context budget` (AC-008).

## Alternatives considered

- **Duplicate the token-economy rules into README + doc + CLAUDE.md.example.**
  Rejected: violates the framework's own single-source discipline and creates
  drift. Chosen: one canonical doc, cross-references elsewhere.
- **Enforce PLAN/skill template sync in CI (spec 007).** Rejected for this
  spec: telemetry/hard-enforcement is a non-goal, and OQ-002 confirmed the CI
  check has no template-diff facility today. Left as a manual review item;
  a future spec may add it.
- **Machine-readable context-budget fields in skill contracts (spec 018).**
  Rejected/deferred per SPEC A-004 — the PLAN section is the minimal artifact.

## Dependencies

- None external. Relies only on existing files; `docs/TOKEN_ECONOMY.md` is
  README-consumed and not part of any installer manifest (D005 / OQ-001).

## Risks

- **Template fork (AC-003):** the two PLAN templates can drift; not CI-guarded
  (OQ-002). Mitigation: edit both in one task, verify with `git grep`.
- **Codex parity drift:** the analyze prompt is a hand-maintained mirror.
  Mitigation: T-tasks explicitly touch it and `PARITY.md` records the status.
- **Over-blocking legacy plans:** an over-strict check would fail 001–020.
  Mitigation: D004 makes "missing" a warning, only "empty/placeholder" blocks.
- **Scope creep into marketing tone** in README. Mitigation: ≤5-line cap
  (FR-002 / AC-001), reuse existing README voice.

## Test strategy

- No executable code → no unit/integration/E2E suites added.
- **Structural checks (manual + grep):**
  - `git grep -c "## Context budget"` → exactly the two template files.
  - Every path in the `TOKEN_ECONOMY.md` table resolves (`test -e`).
  - No `TODO:`/placeholder left in the new CONSTITUTION section.
- **Regression:** run `bash scripts/check-consistency.sh` — must stay exit 0
  (new top-level `docs/TOKEN_ECONOMY.md` is not a `_templates` entry, so it
  must not trigger orphan-template; confirm).
- **Behavioral (manual):** run `/spec-analyze` on this feature (fires new
  check on a filled section → pass) and on feature 019 (missing section →
  warning, not blocker).

## Rollback strategy

Pure additive doc/template edits on a feature branch. Rollback = `git revert`
of the feature commit(s); no data, no migrations, no runtime state. Downstream
projects that already regenerated a CONSTITUTION keep their copy — harmless.

## PLAN verification checklist

- [x] The plan covers all acceptance criteria.
- [x] The plan avoids behavior outside the spec.
- [x] Risks are documented.
- [x] Test strategy is documented.
- [x] Rollback strategy is documented.
- [ ] SPEC.md status has been updated to `Ready`.
