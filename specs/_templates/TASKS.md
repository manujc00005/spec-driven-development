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

<!-- CLOSING A TASK THAT WAS NOT PERFORMED. `[x]` means "closed out of this spec", not always
     "the work was done". A spec cannot reach Done while its list still shows open items, but
     silently ticking something nobody did is worse than leaving it open. So a task closed
     without being performed keeps the tick AND states how it was closed, on the line below:

       - [x] T007 - Windows runtime spot-check.
         **DEFERRED (2026-08-23) -> DEBT-007.** <why it did not block, and where it now lives>

     Three markers, and they are not interchangeable:
       DEFERRED - still worth doing; tracked in docs/KNOWN_DEBT.md with an id.
       SKIPPED  - deliberately not doing it; the reason must outlive the decision.
       RESOLVED - the work happened, just not through this task (say where).

     DEFERRED and SKIPPED must carry a DEBT id. RESOLVED must not - nothing is pending.
     A tick with no marker means the task was performed, which is the ordinary case. -->

## Phase 1: Preparation

- [ ] T001 - Task description. Covers: AC-XXX. Verify: <how anyone checks this is done>.

## Phase 2: Implementation

- [ ] T002 - Task description. Covers: AC-XXX. Verify: <how anyone checks this is done>.

## Phase 3: Tests

- [ ] T003 - Task description. Covers: AC-XXX. Verify: <how anyone checks this is done>.

## Phase 4: Review

- [ ] T004 - Task description. Covers: AC-XXX. Verify: <how anyone checks this is done>.
