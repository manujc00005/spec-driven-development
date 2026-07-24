# Tasks: Agentic Routing and Skill Contracts (Phase 2)

## Phase 1: Preparation

- [x] T001 - Persist the Phase 1 inventory + Skill→Agent matrix into this feature folder (e.g. `INVENTORY.md`) as the durable source for contracts. Covers: AC-007.
- [x] T002 - Apply the decided contract carrier approach (D011: fenced YAML block under a `## SDD Contract` section) by sampling 5–6 representative SKILL.md files across categories to confirm it fits current styles. Covers: AC-004, AC-011.
- [x] T003 - Define the skill-contract schema (fields, enums, required/optional) that `check-consistency` will validate. Covers: AC-004, AC-009.

## Phase 2: Implementation

- [x] T004 - Author `agents/codebase-researcher.md` (read-only + Graphify; bounded context). Covers: AC-001, AC-003, AC-010, AC-013.
- [x] T005 - Author `agents/solution-architect.md` (owns pre-implementation test strategy; proposes DECISIONS). Covers: AC-001, AC-003, AC-013.
- [x] T006 - Author `agents/implementer.md` (edits within boundaries; stops on missing decisions; no commit/push). Covers: AC-001, AC-003, AC-013.
- [x] T007 - Author `agents/security-reviewer.md` (isolated auth/secrets/payments review; analysis-only). Covers: AC-001, AC-003, AC-013.
- [x] T008 - Author `agents/domain-reviewer.md` (loads profile reviewer skills; owns domain test expectations; analysis-only). Covers: AC-001, AC-003, AC-005, AC-013.
- [x] T009 - Author `agents/final-conformance-reviewer.md` (SPEC→…→REVIEW traceability verdict; owns final coverage validation). Covers: AC-001, AC-003, AC-013, AC-014.
- [x] T010 - Add skill-contract metadata to all 61 SKILL.md files in one mechanical pass, values from the Phase 1 matrix. Covers: AC-004, AC-007.
- [x] T011 - Reroute external-subagent references in `java-spring-reviewer`, `spring-boot-api-reviewer`, and `event-driven-reviewer` to `domain-reviewer` (routing target only; bodies unchanged). Covers: AC-005, AC-006.
- [x] T012 - Populate per-profile `agents` and the additive `domain-reviewer` routing map in `profiles.json` (core = all six; overlays add their reviewers); keep `skills` arrays unchanged. Covers: AC-008.
- [x] T013 - Update `agents/README.md` to document the six lifecycle agents alongside `deep-reasoner`/`fast-worker`; confirm installer copies them. Covers: AC-002, AC-011.

## Phase 3: Tests

- [x] T014 - Extend `check-consistency` to validate skill contracts parse and every `primary_agent`, profile agent, and routed reviewer resolves. Covers: AC-009.
- [x] T015 - Add a schema/unit check that all 61 contracts validate; run installer dry-runs per profile; confirm regression checks still pass. Covers: AC-004, AC-008, AC-009, AC-011.
- [x] T016 - Manual agent-boundary walkthrough on a sample feature: confirm reviewers make no code edits and `implementer` stops on a missing decision. Covers: AC-013.

## Phase 4: Review

- [x] T017 - Write the skills-vs-agents documentation explainer and the routing model overview. Covers: AC-015.
- [x] T018 - Verify no project-specific/private content was introduced and Claude Code compatibility is preserved; update `CHANGELOG.md`. Covers: AC-011, AC-012.
- [ ] T019 - Run `/spec-review`, then dispatch the `final-conformance-reviewer` **agent** (dispatched via the Agent tool — it is an agent, not a slash command); confirm it produces a traceability verdict across SPEC→PLAN→TASKS→DIFF→TESTS→REVIEW. Covers: AC-014.
