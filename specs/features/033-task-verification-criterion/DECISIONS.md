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

A `TASKS.md` is legacy when no **task item** carries a `Verify:` clause. The detection unit is the
task item — a bullet beginning `- [ ]` or `- [x]` **together with its continuation lines, up to the
next bullet** — and within that item the clause is the one **following `Covers:`**. Once any task
item in the file carries one, every task item in that file must.

Two things this rules out, both observed rather than imagined: a raw content match over the file,
which counts prose that merely mentions the token; and a physical-line match, which misses a clause
that wrapped onto a continuation line.

**Revised twice on 2026-08-22, both times after a review round found the rule wrong on this
repository's own files.**

*First revision, from DOM-001's round.* The original wording said "containing no `Verify:` clause at
all", which a naive implementation reads as a substring test over file content. This feature's own
`TASKS.md` falsifies that immediately: T003's description mentions `Verify:` in prose while no task
carries a clause, so a content match would flip the file to adopted and block all seven of its tasks.

*Second revision, from DOM-002's round.* The first fix moved the hole rather than closing it. It
named the unit as "a line beginning `- [ ]` or `- [x]`", but task lines in this repository wrap: in
this feature's own file the bullet sits on line 5 while `Covers:` lands on line 7, and 8 of its 9
tasks are shaped that way. A physical-line test therefore reads a correctly-formed wrapped clause as
missing, and a fully adopted file as legacy — the opposite error, equally fatal.

Recording both passes rather than only the final wording, because the pattern is the lesson: each
attempt was tested against real files and each failed differently. A rule about text formats cannot
be validated by reasoning about the format; it has to meet the corpus.

**Reasoning:**

It needs no timestamps, no migration marker and no per-file state — the file's own content decides.
It also gives a natural adoption path: adding one clause opts the file in, which is exactly what
AC-007 asserts.

**Consequences:**

A file half-migrated in a single edit becomes blocking, which is the intended pressure. Nothing is
backfilled automatically.

### D003 - Parallel workers drift on a shared contract even when told to derive from the source

**Date:** 2026-08-22

**Status:** Accepted

**Context:**

Tasks T002–T005 were run in parallel because they touch disjoint files. They share a contract but do
not define it — the anchor template does — so the parallelism rule's "same files, same contract" test
seemed satisfied by the file half.

It was not. The review found `DOM-003`: the Claude gate stated less of the contract than its Codex
twin, so `Verify: reviewed by hand` blocked on one provider and passed on the other. The fix round
was then briefed explicitly to derive from FR-008 rather than from each other — and drifted again,
in the opposite direction: the Claude gate made a blanket phrase blocking while the Codex prompt
wrote "missing or empty stays the only blocking case", contradicting its own preceding check.

**Decision:**

Recorded as a finding about the method, not patched into the parallelism rule by this spec. The
second drift was repaired by hand rather than by a third delegation round.

**Reasoning:**

Two independent writers producing prose about the same rule will produce different prose, and
"different prose about a gating rule" is a behavioural difference, not a stylistic one. Telling each
to derive from the source removes the copying error but not the interpretation gap. The cheap
mitigation is not better briefs: it is to have one writer produce all surfaces of a shared contract,
or to have a single pass reconcile them afterwards, which is what the review round did here — twice.

**Consequences:**

A follow-up worth considering for the framework: the parallelism rule's "same contract" clause
currently reads as being about files. Two tasks that adopt one contract into different files share
that contract, and this run is evidence that the rule should say so.
