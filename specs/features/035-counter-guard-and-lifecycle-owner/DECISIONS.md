# Decisions: counter-guard-and-lifecycle-owner

## Decision log

### D001 - The Ready exception is a conjunction, not a softening

**Date:** 2026-08-22

**Status:** Accepted

**Context:**

Spec 032's D009 found that a spec whose work is legitimately driven outside `/spec-implement` has no
owner for `Ready → In Progress`. The obvious fix is to let `/spec-review` accept `Ready`.

**Decision:**

`/spec-review` accepts `Ready` only when the feature's `DECISIONS.md` contains an **accepted**
decision explaining why `/spec-implement` was bypassed, and the review must name that decision in its
output.

**Reasoning:**

Accepting `Ready` unconditionally would delete the protection rather than scope it: any spec could
then reach `In Review` with nothing implemented. The citation requirement is what makes the exception
auditable — an exception nobody has to justify in writing is indistinguishable from the silent status
edit guardrails section 11 exists to prevent.

**Consequences:**

A maintainer who wants the exception must write the decision first. That is the intended friction.

### D002 - The counter rules are guarded behaviourally, not by asserting their prose

**Date:** 2026-08-22

**Status:** Accepted

**Context:**

Spec 032 left D008 and D010 as sentences in a skill file with nothing to catch a regression. The two
candidate guards are a text assertion in `check-consistency.sh` and a behavioural eval scenario.

**Decision:**

A committed eval scenario under `evals/scenarios/`.

**Reasoning:**

Asserting exact sentences in a document is brittle: it fails on harmless rewording, which trains
people to edit around the check instead of respecting the rule, and it cannot tell a reworded rule
from a reversed one. The eval harness measures the thing that actually matters — whether the rule
changes model behaviour — so a rule reworded into meaninglessness shows up as a lost effect.

**Consequences:**

The guard costs provider quota to run and is therefore not a CI gate. It is evidence on demand, not
a tripwire, and this spec says so rather than implying continuous protection.

### D003 - This spec was implemented in the maintainer's session, not through /spec-implement

**Date:** 2026-08-22

**Status:** Accepted

**Context:**

The whole deliverable is three text files: one eval scenario and two skill edits. The work was
decided in full by the SPEC and PLAN before any edit, and the PLAN's model routing says so
explicitly — delegating it would have cost more context than it saved.

**Decision:**

The maintainer's orchestrator session performed the edits directly. `/spec-implement` did not run,
so this spec reaches `/spec-review` at `Ready`.

**Reasoning:**

This is the exact case D001 of this spec creates the exception for, and recording it here is the
condition that exception requires — so this spec is also the first test of its own rule. If the
rule works, `/spec-review` accepts `Ready` and names this decision. If it does not, the rule is
wrong and should be fixed before it ships.

**Consequences:**

None beyond the citation. Had this decision not been written, `/spec-review` would have been
required to refuse and send the work back through `/spec-implement`, which is the intended
friction.
