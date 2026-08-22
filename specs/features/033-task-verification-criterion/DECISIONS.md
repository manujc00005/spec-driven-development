# Decisions: task-verification-criterion

## Decision log

### D001 - The clause syntax is fixed before any consumer adopts it

**Date:** 2026-08-22

**Status:** Accepted

**Context:**

`Verify:` becomes a documentation contract that two skills, two templates, two Codex prompts and
thirty existing task lists must agree on. It is the one decision in this feature that is expensive to
reverse.

**Decision:**

T001 fixes the syntax in `specs/_templates/TASKS.md` first, and every later task adopts it rather
than restating it.

**Reasoning:**

Defining the format in the producer and mirroring it outward would leave each surface free to drift,
and drift across an adapter boundary is the failure this framework repeatedly pays for.

**Consequences:**

T001 blocks everything else. That is intended.

### D002 - A legacy task list is one with no `Verify:` anywhere

**Date:** 2026-08-22

**Status:** Accepted

**Context:**

AC-002 wants a blocking finding for a missing clause; AC-003 and AC-007 want every existing file to
keep passing. Both cannot hold without a rule for telling the two apart.

**Decision:**

A `TASKS.md` containing no `Verify:` clause at all is legacy and passes untouched. Once any task in
the file carries one, every task in that file must.

**Reasoning:**

It needs no timestamps, no migration marker and no per-file state — the file's own content decides.
It also gives a natural adoption path: adding one clause opts the file in, which is exactly what
AC-007 asserts.

**Consequences:**

A file half-migrated in a single edit becomes blocking, which is the intended pressure. Nothing is
backfilled automatically.
