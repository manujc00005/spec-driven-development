<!-- Extracted from skills/spec-plan/SKILL.md — kept in sync with that skill's template. -->

# Tasks: <feature-name>

<!-- Each task line gains a `Verify:` clause after `Covers:`: the criterion anyone checks to call
     the task done. It may be an executable command or an observable human check — nothing in the
     framework executes it; it is text for a human or an agent to act on, not a runner input. A
     human check must name who checks and against what: "Verify: reviewed by hand" alone is not a
     criterion, and must not be reached for as a universal escape from stating one.

     Example (executable): - [ ] T001 - Add rate limiting to the login endpoint. Covers: AC-002.
     Verify: curl the endpoint 11 times in 60s and confirm the 11th call returns 429.

     Example (human check): - [ ] T002 - Migrate the pricing table to the new schema. Covers:
     AC-005. Verify: the DB maintainer confirms the migrated totals match last month's invoice
     totals by hand. -->

## Phase 1: Preparation

- [ ] T001 - Task description. Covers: AC-XXX. Verify: <how anyone checks this is done>.

## Phase 2: Implementation

- [ ] T002 - Task description. Covers: AC-XXX. Verify: <how anyone checks this is done>.

## Phase 3: Tests

- [ ] T003 - Task description. Covers: AC-XXX. Verify: <how anyone checks this is done>.

## Phase 4: Review

- [ ] T004 - Task description. Covers: AC-XXX. Verify: <how anyone checks this is done>.
