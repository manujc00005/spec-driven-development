# AC-003 evidence — executed polyglot `domain-reviewer` run

**Date:** 2026-09-02 · **Fixture:** a repo with `java-spring-backend` + `python-sql-data`
installed (56 skills), diff touching `src/main/java/com/acme/orders/OrderService.java` and
`etl/load_orders.py`. Run executed against the rewritten `agents/domain-reviewer.md`.

## What AC-003 requires, and what the run showed

| Requirement | Observed |
|---|---|
| Findings from **both** stacks in one pass | Yes — DOM-001..007 (Java) and DOM-008..020 (Python/SQL), one review |
| Names which reviewers ran (FR-016) | Yes — 10 reviewers, each with the changed file that selected it |
| Names files that selected no reviewer | Yes — *"Changed files that selected no reviewer: none"* |
| Does **not** ask which profile applies | Yes — *"several reviewers applying is the normal case, not a stop condition"* |
| Selection by `description`, never `triggers:` | Stated explicitly by the agent, unprompted |

## Reviewers applied, as the run reported them

Java: `backend-review`, `java-spring-reviewer`, `performance-review`,
`java-performance-reviewer`, `observability-reviewer`.
Python/SQL: `database-review`, `python-reviewer`, `sql-query-reviewer`,
`data-pipeline-reviewer`, `database-performance-reviewer`.

Deliberately not run, each with a stated reason: `spring-boot-api-reviewer`, `api-review`
(no API artifact changed), `spring-security-reviewer`, `python-testing-reviewer`,
`security-review` (handed to `security-reviewer`).

## FR-005 confirmed in the field

The T009 coexistence note was applied as written: *"Cross-reference per the coexistence rule in
`database-performance-reviewer`: DOM-001 is an ORM mapping defect, so it is filed here and **not**
restated as a database-performance finding."* The JPA N+1 was filed once under
`java-performance-reviewer`; the query-in-a-loop in the Python ETL was filed separately under
`database-performance-reviewer` (DOM-012). Both kept coverage; neither double-reported.

## Honest limits of this evidence

1. **The agent has no Bash tool** (its definition grants Read, Grep, Glob), so it could not run
   `git diff`. It identified the changed set by inspecting the working tree and reviewed both files
   in full. It said so itself, unprompted. The substance of AC-003 — both stacks reviewed in one
   pass, reviewers named, no profile question — is unaffected, but this was not literally a
   diff-scoped review.
2. **One run, not an eval.** OQ-7 resolved this deliberately: an executed run with a transcript is
   honest evidence and is weaker than a control-arm eval scenario, which is a feature in its own
   right. This does not change that.

## Pre-existing defect the run surfaced (not in this spec's scope)

`skills/backend-review/SKILL.md:42` instructs *"If Java/Spring Boot → delegate the full review to
the `java-spring` agent... Do not apply generic rules"* — read literally it would suppress the
generic base pass entirely. The agent ran the base checklist anyway, per its own Method step 2, and
filed it as a pending-reroute note. Same pattern at `java-performance-reviewer:38`,
`observability-reviewer:38` and `api-review:28,31,35`. This is the known external-subagent reroute
debt that `domain-reviewer`'s Method step 4 already covers; it predates spec 030.
