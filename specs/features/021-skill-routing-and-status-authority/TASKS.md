# Tasks: Skill routing disambiguation and spec-status authority

## Phase 1: Status authority — central rule

- [x] T001 - `skills/sdd-guardrails/SKILL.md`: insert section 11 *Spec Status Authority*
  (transition→owner table, precondition per owner, exclusivity rule, "a written status string is
  not a passed gate", user-instruction exception); renumber *Limitations* 11 → 12. Covers: AC-001.

## Phase 2: Status authority — owning skills

- [x] T002 - `spec-plan`: sole authority for Draft → Ready. Covers: AC-002.
- [x] T003 - `spec-implement`: sole authority for Ready → In Progress. Covers: AC-002.
- [x] T004 - `spec-review`: sole authority for → In Review (Pass verdict only). Covers: AC-002.
- [x] T005 - `spec-close`: sole authority for In Review → Done. Covers: AC-002.

## Phase 3: Status authority — non-owning skills and agent

- [x] T006 - `spec-create`, `spec-clarify`, `spec-analyze`, `sdd-orchestrate`: must-not-promote
  sentence naming the authorized owner. Covers: AC-003.
- [x] T007 - `agents/solution-architect.md`: Forbidden action — promoting spec status outside the
  documented owners. Covers: AC-004.

## Phase 4: Negative triggers

- [x] T008 - Append the one-sentence `Not for … — use /…` clause to the `description` of every
  skill in PLAN's *Confusion pairs* table (21 skills). Covers: AC-005.

## Phase 5: Docs

- [x] T009 - CHANGELOG `[Unreleased]` entry for spec 021. Covers: AC-001..005 (documentation).

## Phase 6: QA closure (D006)

- [x] T011 - `sdd-guardrails` §11: add `Archived` and demotion rows (owner = explicit user
  decision, recorded in `DECISIONS.md`) and the re-entering-a-gate rule. Covers: AC-001.
- [x] T012 - `agents/implementer.md` and `agents/fast-worker.md`: status prohibition scoped to
  what each legitimately owns; align `skills/spec-update` with the new wording.
  Covers: AC-003, AC-004.

## Phase 7: Verification

- [x] T010 - Coverage grep (every pair-table skill has a clause, no ALL-CAPS), protected-path
  guard (`profiles.json`, `hooks/`, `install*`, `settings.template*` untouched), and
  `bash scripts/check-consistency.sh` exit 0. Covers: AC-005, AC-006.
