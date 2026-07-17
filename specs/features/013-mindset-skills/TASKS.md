# Tasks: mindset-skills

Writing order follows user priority so the feature ships gracefully if interrupted:
verifier → scope-keeper → communicator → stopper → honest-advisor → threat-modeler → scout → decomposer → root-causer.

## Phase 1: Preparation

- [x] T001 - Author `skills/verifier/SKILL.md` as the **canonical skeleton template**. Establish the exact section order and headings (thesis line, `## Triggers`, `## Rules`, `## Anti-patterns`, `## Contrast`, `## Closing checklist`), the Rules format (behavior + observable trigger, no adjectives), the bad→good anti-pattern format, the Contrast framing (this manual vs generic model), and a ≤7-item checklist. Include the one-line relationship to the built-in `verify` skill. Cover verifier's normative rules/anti-patterns from SPEC. Frontmatter `name: verifier`, trigger-phrased `description`. ≤~150 lines. Covers: AC-001, AC-002, AC-003, AC-007.

## Phase 2: Implementation

- [x] T002 - Author `skills/scope-keeper/SKILL.md` from the T001 skeleton; cover scope-keeper's normative rules (minimal diff, match surrounding style, no "while I'm at it", no speculative generality) and anti-patterns. Covers: AC-001, AC-002, AC-003.
- [x] T003 - Author `skills/communicator/SKILL.md`; cover lead-with-outcome, complete sentences over arrow-chains, drop-don't-compress, self-contained final message; language-agnostic (non-English edge case). Covers: AC-001, AC-002, AC-003.
- [x] T004 - Author `skills/stopper/SKILL.md`; cover reversible→proceed / destructive→ask, no turn-ending promises, assessment-vs-fix, self-recovery on errors; note the standing-authorization edge case. Covers: AC-001, AC-002, AC-003.
- [x] T005 - Author `skills/honest-advisor/SKILL.md`; cover flawed-premise pushback, one recommendation not a menu, full-strength bad news, assessment-vs-change. **State the `honest-advisor`↔`stopper` boundary** (disagree once with evidence, then proceed or stop per user). Covers: AC-001, AC-002, AC-003, AC-008.
- [x] T006 - Author `skills/threat-modeler/SKILL.md` (tier-2). Open with the one-line relationship to `security-review` (mindset while writing vs audit after). Cover who-can-call / worst-case-input / abuse-case rules; defensive only, no exploit technique. Covers: AC-001, AC-002, AC-003, AC-007.
- [x] T007 - Author `skills/scout/SKILL.md` (tier-2). One-line relationship to `sdd-onboard`/`context-manager` (in-the-moment orientation vs artifact production). Cover read-structure-before-editing, search-before-building, derive-conventions-from-code. Covers: AC-001, AC-002, AC-003, AC-007.
- [x] T008 - Author `skills/decomposer/SKILL.md` (tier-2). One-line relationship to `spec-plan`. Cover decompose-and-find-the-irreversible-decision, skip-planning-when-trivial, risk-first ordering. **State the `decomposer`↔`spec-plan` boundary** (plan artifact belongs to spec-plan; decomposer governs judgment). Covers: AC-001, AC-002, AC-003, AC-007, AC-008.
- [x] T009 - Author `skills/root-causer/SKILL.md` (tier-2). One-line relationship to `debugger` (stance vs 6-phase procedure). Cover reproduce-before-hypothesis, name-why-not-just-gone, distrust-first-explanation, layer-mismatch check. Covers: AC-001, AC-002, AC-003, AC-007.
- [x] T010 - Register the nine skill names in `profiles.json` `core.skills` (31 → 40), in the authoring order above. Covers: AC-004.
- [x] T011 - Update `README.md`: add a **"Mindset skills"** grouping to the skill listing with one-line descriptions matching each frontmatter; update count markers `skills-total` (43→52) and `core-skills` (31→40); update non-marker prose that states 43 (badge line ~15, "all 43 of them" line ~192, tree comment "43 skills" line ~282, "(43 skills)" line ~510). Covers: AC-005.

## Phase 3: Tests

- [x] T012 - Run `bash scripts/check-consistency.sh` → must exit 0 (no orphan-skill, markers aligned). Fix any drift. Manually confirm each of the nine `SKILL.md` is self-contained (E2E scenario) by re-reading it in isolation. Covers: AC-004, AC-002.

## Phase 4: Review

- [x] T013 - Cross-read audit: (a) rule-by-rule pass across all nine — zero rules that are pure adjectives with no observable trigger/condition (FR-009); (b) verify each anti-pattern has a bad→good pair and each manual has a Contrast section (AC-003); (c) cross-read the four tier-2 manuals + verifier against their complemented skills — no contradiction, relationship line present (FR-008/FR-010/AC-007); (d) confirm the two boundary statements exist (AC-008). Covers: AC-006, AC-007, AC-008, AC-003.
