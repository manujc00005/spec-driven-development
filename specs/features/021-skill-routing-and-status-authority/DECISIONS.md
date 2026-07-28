<!-- See skills/sdd-guardrails/SKILL.md, section 1, for the full decision state machine (Proposed / Accepted / Superseded / Rejected / Deferred). -->

# Decisions: Skill routing disambiguation and spec-status authority

## Decision log

### D001 - Status authority is a documented convention, not hook-enforced

**Date:** 2026-07-25

**Status:** Accepted

**Context:** The natural instinct is to enforce "only `/spec-review` may set `In Review`" with a
hook, and an earlier verbal suggestion in this project claimed `sdd-spec-guard` "could enforce
it". On inspection that claim is wrong and is corrected here.

**Decision:** Ship the authority rule as guardrails documentation plus explicit sentences in the
owning and non-owning skills and in `agents/solution-architect.md`. Do **not** add or modify any
hook.

**Reasoning:** A `PreToolUse` hook receives the tool call (file path, and for an edit the new
content) but **no attribution of which skill or agent is driving it**. It can therefore detect
that a `Status:` line changed, but it cannot distinguish an authorized `/spec-review` promotion
from an unauthorized manual one — so it could only ever warn, never authorize. Shipping it as
enforcement would be the exact overclaiming this framework rejects elsewhere (hooks are
"guardrails against accidental damage, not a security boundary"). A convention that is honestly
labelled a convention is better than a mechanism that implies a guarantee it cannot give.

**Consequences:** The rule binds behaviour through skill text, which is how every other SDD gate
(`spec-implement` refusing a `Draft` spec, `spec-close` refusing a non-`In Review` spec) already
works. A future non-blocking `spec-status-reminder` hook remains possible and is recorded as
SPEC OQ-1, not as part of this spec. No `profiles.json` change is needed, so no CI rule moves.

### D002 - Terse negative triggers, not the Azure ALL-CAPS block style

**Date:** 2026-07-25

**Status:** Accepted

**Context:** The Azure Skills plugin (design reference for this spec) writes very forceful
routing text: multi-line `WHEN: … DO NOT USE WHEN: …` blocks in the description, plus
"⛔ STOP", "MANDATORY COMPLIANCE", and "You are FORBIDDEN" banners in the body.

**Decision:** Adopt the *idea* (negative triggers naming the correct sibling), reject the
*form*. Each clause is one sentence appended to the existing description:
`Not for <case> — use /<other-skill>.` No ALL-CAPS, no banners, no restructuring.

**Reasoning:** Two reasons, one editorial and one measurable. Editorially, this repository's
voice is calm and gate-driven — enforcement comes from hooks and refusal conditions, not from
shouting at the model, and portfolio readers judge that tone. Measurably, every description is
loaded into context at session start, so an Azure-sized block (~100 extra words per skill)
across a 61-skill catalogue would be a standing per-session cost for routing information that a
single sentence conveys.

**Consequences:** Diff stays small and reviewable; the pattern is easy for contributors to
follow. If a pair later proves genuinely ambiguous despite the clause, that is evidence for
expanding *that* clause, not for adopting block style globally.

### D003 - Negative triggers are bounded to documented confusion pairs, not all 61 skills

**Date:** 2026-07-25

**Status:** Accepted

**Context:** The mechanical option is to give every skill a negative trigger. Most skills have
no plausible confusable sibling (`prisma-migration-reviewer`, `azure`-style stack reviewers,
the billable SEO family already gated by contract checks).

**Decision:** Apply clauses only to the pairs enumerated in PLAN's *Confusion pairs* table.
Adding a pair later is a one-line change, deliberately cheap.

**Reasoning:** A negative trigger only earns its context cost where a real mis-selection is
plausible. Blanket rollout would add tokens to every session for skills nobody confuses, which
contradicts the framework's own context-economy doctrine. The pair list is derived from actual
overlap in the current catalogue (same verb, same artefact, or mindset-vs-procedure siblings),
not from guesswork.

**Consequences:** The pair table in PLAN is the maintained source of truth for what has a
clause. `check-consistency` does not validate descriptions, so coverage is asserted by the
spec's own grep test rather than by CI — an accepted, documented limit.

### D004 - The authority table lives in sdd-guardrails; Limitations renumbers 11 → 12

**Date:** 2026-07-25

**Status:** Accepted

**Context:** The Spec Status Authority table needs one canonical home. `sdd-guardrails` already
owns the Decision State Machine (section 1), the Source of Truth Matrix, and the Consistency
Gate, and is already invoked before plan/implement/close. Its sections are numbered 1–11 and
section numbers are referenced externally (`specs/_templates/DECISIONS.md` points at "section 1").

**Decision:** Insert **Spec Status Authority** as section 11 and renumber the existing
*Limitations* section from 11 to 12, keeping Limitations last.

**Reasoning:** `sdd-guardrails` is where a reader already goes for "which document wins and when"
— the spec-status machine is the same class of rule. A grep confirmed that only *section 1* is
referenced outside the file, so renumbering 11 → 12 breaks nothing, while appending after
Limitations would leave a closing section stranded in the middle of the document.

**Consequences:** Any future external reference should cite section names, not numbers. The
Decision State Machine (section 1) and the new Spec Status Authority (section 11) are deliberately
separate: one governs `DECISIONS.md` entries, the other governs `SPEC.md` status, and conflating
them was part of why the spec-status rule was never written down.

### D005 - FR-006 widened to a negation family; PLAN table generated from shipped text

**Date:** 2026-07-25

**Status:** Accepted

**Context:** `/spec-review` returned **Partial** twice on the delivered work, with two findings
that were both real. (1) FR-006 specified a single literal template,
`Not for <case> — use /<other-skill>.`, but 7 of the 21 shipped clauses opened with `Not a …`,
`Not the …`, or `Not needed …`. (2) PLAN's *Confusion pairs* table, which declares itself "the
maintained source of truth for FR-005", had drifted from the shipped wording in 6 of 21 rows.
Two options were on the table: widen the contract to match the prose (A), or rewrite the 7
clauses to fit the template (B).

**Decision:** Option A. FR-006 now requires *one terse sentence opening with a negation from the
family* `Not for …` / `Not a …` / `Not the …` / `Not needed …` *and naming the correct sibling as
a slash-command*, keeping the No-ALL-CAPS and no-restructuring constraints. AC-005 is updated to
match and additionally requires PLAN's table to equal the shipped text verbatim. The 6 drifted
rows were regenerated **from the actual descriptions** rather than re-typed.

**Reasoning:** The template was too narrow for the mindset-vs-procedure pairs, where the natural
negation is a noun phrase: *"Not the mindset manual on debugging stance — that is /root-causer"*
reads correctly, while a forced `Not for …` variant would be contorted for no gain. FR-006's real
intent — one sentence, calm tone, names the sibling — is fully preserved by the wider family, so
widening the contract costs nothing and improves the prose. Regenerating the table from disk (not
by hand) removes the mechanism that produced the drift in the first place.

**Consequences:** The two review findings are closed at their source. This is a spec correction
made *because* review caught the deviation, which is the workflow behaving as designed: the
implementation was not quietly bent to match a wrong contract, and the contract was not quietly
ignored. Residual limitation unchanged from D003: `check-consistency` still does not validate
descriptions, so clause drift is caught by review, not by CI.

### D006 - Archiving and demotion belong to the human; agent parity covers every write-capable agent

**Date:** 2026-07-25

**Status:** Accepted

**Context:** `/qa-review` returned **Partial** with three gaps in the very state machine this spec
set out to make authoritative. (1) `Archived` is part of the documented lifecycle
(`spec-create`: `Draft → Ready → In Progress → In Review → Done | Archived`) but appeared zero
times in section 11 — combined with "no other skill, agent, or ad-hoc edit may promote a status",
that left **nobody able to archive**. (2) Demotion was said to "follow the same rule" without
naming an owner, which is not a rule. (3) FR-004 applied agent/skill parity to
`solution-architect` only, while `implementer` and `fast-worker` also hold Edit/Write and carried
no status rule at all — `implementer` being the agent behind the one skill that does promote.

**Decision:**
- **Archiving and demotion require an explicit user decision**, recorded in `DECISIONS.md`. No
  skill or agent initiates either; a skill may perform the edit once the user asks.
- **Re-entering a gate re-runs it**: a spec demoted from `In Review` must pass `/spec-review`
  again — the earlier Pass does not carry over.
- **Every write-capable agent carries a status prohibition scoped to what it owns**:
  `solution-architect` (specs only), `implementer` (`Ready` → `In Progress` only),
  `fast-worker` (none). `spec-update` is aligned with the new wording.

**Reasoning:** A state machine with an unreachable state is not authoritative, and "follows the
same rule" is not an owner. Assigning archiving and demotion to the human rather than inventing a
skill owner matches the existing user-instruction exception and reflects what they actually are —
judgment calls about abandoning or reopening work, not mechanical steps. Extending parity to all
three write-capable agents applies the spec-020 lesson completely instead of by example: leaving
two of three agents silent is precisely the kind of partial coverage that produced the original
`security`/`gdpr-spain` drift.

**Consequences:** FR-001/003/004 and AC-001/003/004 widened; T011/T012 added. `sdd-guardrails`
section 11 now covers every state in the documented lifecycle, so "which skill may write this
status" has an answer for all of them. Unchanged: nothing is hook-enforced (D001), and no
`profiles.json`, installer, or hook was touched.
