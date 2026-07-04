---
name: sdd-guardrails
description: Global consistency guardrails for any Spec-Driven Development workflow (SPEC/PLAN/TASKS/DECISIONS or equivalent — RFCs, design docs, implementation plans). Use before /spec-plan, /spec-implement, /spec-close, or any planning/implementation step, whenever the active feature has more than one decision on record, touches money/units, or touches schema/deployment. Detects contradictions between documents, obsolete plans being implemented, decisions used after being superseded, and ambiguous naming reused across versions.
---

# SDD Guardrails

This skill applies to **any project** that uses a spec-driven workflow with
documents like `SPEC.md`, `PLAN.md`, `TASKS.md`, `DECISIONS.md` — or equivalents
(RFCs, design docs, ADRs, implementation plans). It is project-agnostic: it does
not assume any specific stack, domain, or repository structure.

It exists because specs evolve. A feature can go through several rounds of
"actually, let's do it differently" before landing on a final approach, and
nothing forces every document to catch up at the same time. Left unchecked, that
produces exactly the failure modes this skill guards against:

- A plan built on a decision that was later superseded.
- An obsolete plan that still reads as if it were current.
- A function/field name that caused confusion before, reused with a new meaning.
- Acceptance criteria in `SPEC.md` that contradict what `TASKS.md` describes.
- A scope change that didn't force the plan and tasks to be regenerated.
- A money/units feature implemented without a units table or pre-provider validation.
- A schema migration with no documented deployment order.

> **Illustrative example** (not a project-specific rule — just the shape of the
> problem): if `PLAN.md` says to use `getEventMemberDiscount()` but `SPEC.md`
> says that function must not exist anymore, stop and fix the documentation
> before implementing anything. Don't implement around the contradiction.

---

## When to run this skill

Run it — or at minimum mentally walk through the Consistency Gate (section 4) —
before:

- `/spec-plan` (or generating any implementation plan)
- `/spec-implement` (or starting to write code from a plan)
- `/spec-close` (or marking a feature done)

It is most important when any of these are true for the active feature:

- `DECISIONS.md` (or equivalent) has more than one decision recorded.
- The feature touches money, pricing, discounts, taxes, or any unit-sensitive field.
- The feature touches a schema/migration and code that depends on it.
- The spec went through more than one revision (v1 → v2 → ...).
- The scope changed mid-conversation.

For a trivial, single-revision, no-money, no-schema change, this skill is
overkill — use judgment.

---

## 1. Decision State Machine

Every decision record should carry a `Status` from this closed set:

- `Proposed` — on the table, not decided yet.
- `Accepted` — currently in force; plans and tasks may rely on it.
- `Superseded` — replaced by a later decision. Must point to the decision that
  replaces it.
- `Rejected` — evaluated and discarded; not revived without a new decision.
- `Deferred` — explicitly postponed; not blocking, but not resolved either.

**Rules:**

- At most **one** `Accepted` decision per architectural axis (e.g. "data model for
  feature X", "auth mechanism for endpoint Y"). If a new decision is made on the
  same axis, the previous one must flip to `Superseded` in the same change — never
  leave two `Accepted` decisions on the same axis.
- A `Superseded` decision should note what (if anything) is still true about it,
  separate from the mechanism that got replaced. This prevents someone reading the
  old entry from re-implementing the discarded mechanism just because part of its
  reasoning still holds.
- No plan may be built on, or cite as current, a decision that is `Superseded` or
  `Rejected`. If a plan references it for historical context, it must say so
  explicitly ("superseded, do not use").
- If an `Accepted` decision changes status, any plan that depended on it becomes
  obsolete automatically (see section 3) — this is not optional and does not
  require the user to notice and ask for it.

---

## 2. Source of Truth Matrix

Any non-trivial spec should include a table like this (see
`templates/source-of-truth-matrix.md` for a ready-to-paste version):

```md
## Source of Truth Matrix

| Concept | Source of truth | Documents that must reflect it |
|---|---|---|
| Data model | DECISIONS.md + schema | SPEC, PLAN, TASKS |
| Function naming | PLAN | TASKS, tests |
| Business rules | SPEC | PLAN, TASKS, tests |
| Production deployment | DECISIONS.md | PLAN, TASKS |
| Validations | SPEC | PLAN, TASKS, tests |
| Money/units | SPEC + DECISIONS.md | PLAN, TASKS, tests |
| Reviews required | SPEC | PLAN, TASKS |
```

This matrix is what the Consistency Gate (section 4) uses to arbitrate when two
documents disagree about the same concept. If the matrix doesn't exist for a
feature that's complex enough to need one, the gate should ask for it before
continuing rather than guessing which document wins.

---

## 3. Active Plan Rule

Only **one** plan document should be considered active per feature at a time.

- An obsolete plan must start with a clearly visible marker at the top of its body:

  ```md
  > OBSOLETE — Do not implement this plan. Superseded by the decision/plan that follows it.
  ```

- Do not implement from a plan that carries any of these markers in its header or
  active body: `OBSOLETE`, `NEEDS REVIEW`, `PARTIAL`, `SUPERSEDED` — unless the
  task at hand is explicitly to fix the documentation itself, not to ship product
  code.
- When a plan is replaced, don't leave parallel files like `PLAN.v1.md`,
  `PLAN.v2.md` around as if both were live. Mark the old one obsolete and let the
  new content become the single active plan; history belongs in the decisions
  log, not in competing plan files.
- A task list should not contain tasks marked `[NEEDS REVIEW]` while being treated
  as ready for implementation. Resolve the marker (by closing the pending decision
  and rewriting the task) before treating it as implementable.

---

## 4. Consistency Gate

Before generating a new plan, implementing any task, or closing a feature, walk
through this checklist. If anything fails, **stop and ask for correction** —
don't continue while quietly noting the contradiction for later. That's how these
inconsistencies accumulate in practice.

1. **Decisions**: at most one `Accepted` decision per axis? Does the plan rely on
   anything that's actually `Superseded`/`Rejected`?
2. **Plan vs spec**: do the data model, function/file names, and business rules in
   the plan match the Source of Truth Matrix in the spec?
3. **Tasks vs plan**: does each task reference the same names the plan uses for
   that phase? Does any task describe an approach the plan already abandoned (a
   ghost of an earlier version surviving into the current task list)?
4. **Acceptance criteria ↔ tasks, both directions**: does every acceptance
   criterion have at least one task covering it? Does every task cover a real,
   existing acceptance criterion (not an invented one)?
5. **Units and types**: is the same field (price, discount, date, status)
   described with the same unit/type across spec, plan, and tasks? Watch for
   mixed cents/currency-units/percentage without an explicit, named conversion.
6. **Naming consistency**: does the same concept have exactly one name across all
   documents, or are there accidental synonyms referring to the same thing?
7. **Discarded approaches**: is there any live (not explicitly historical/rejected)
   reference to an approach that the decisions log marked `Rejected` or
   `Superseded`?
8. **Blocking questions**: does the spec's "open questions" section have anything
   unresolved or not explicitly marked non-blocking that affects the current plan?
9. **Active plan**: is the current plan free of the markers from section 3?

---

## 5. Naming Hygiene Rule

If a name (function, field, endpoint) already caused confusion — an ambiguous
unit, an unclear contract, a real bug attributable in part to the name — **do not
reuse it**, even if the implementation underneath changes.

- General rule: if the decisions log records that a name was a source of
  confusion, that decision must fix the new name explicitly, and every document
  that references it (spec, plan, tasks) must use that exact new name —
  consistently, not as a loose paraphrase. The Consistency Gate (section 4, item
  6) checks for this literally.
- Names representing money, percentages, or discriminated types should carry a
  suffix indicating unit or shape once the bare name has already proven ambiguous:
  `Cents`, `Percent`, `Type`, `Rule`, `Config`, and similar.
- A final grep/search pass at close-out time should confirm the old name doesn't
  survive anywhere in the codebase — not as a definition, an import, or a
  re-export/alias.

---

## 6. Units & Money Safety Rule

Any feature touching money, pricing, discounts, taxes, or any third-party payment
provider should require, before implementation starts:

- A units table in the spec (which field is in the smallest currency unit, which
  is a 0–100 percentage, which is a UI-facing decimal value before conversion).
  Without this table, the gate should block the plan.
- A validation function invoked **before** any call to the payment provider's SDK.
  No amount reaches the provider without passing through it first.
- Explicit boundary tests: negative amounts, a discount larger than the base
  price, a percentage out of range, an unrecognized/corrupt discount type.
- Whatever reviews this project defines for security, API contracts, backend
  logic, and (if schema changes) database/migrations — treated as required, not
  optional, for this category of feature.
- No mixing units within the same field/variable without an explicit, named
  conversion. Never infer a field's unit from the *range* of the number — that
  pattern is exactly how this class of bug tends to happen (a value that's
  usually a 0–100 percentage but occasionally holds a raw currency amount).
- Names with explicit units where the bare name has already proven ambiguous (see
  section 5).

---

## 7. Deployment Coupling Rule

If a feature includes a schema/migration change **and** code that depends on the
new columns/data to function (not just an optional field with a safe fallback),
the plan or decisions log should answer explicitly, in a `## Deployment coupling`
section:

```md
## Deployment coupling

- Does the new code require the migration applied first? (yes/no, why)
- Is there a data backfill? Is it mandatory in the same step as the migration, or can it be deferred?
- What happens if code and database end up out of sync (migration without code, code without migration)?
- Is there a rollback plan if the deploy fails partway through?
- Does production require a manual step that can't be automated from the current environment?
```

Don't close out a feature without this section filled in when it applies.

---

## 8. Scope Change Protocol

If the scope of an already-planned feature changes mid-conversation (a new
architectural decision, an added requirement, a previously rejected option
revived), follow this order — don't skip steps:

1. Stop any implementation in progress.
2. Update the spec (including the Source of Truth Matrix if affected concepts
   changed).
3. Update the decisions log: mark affected decisions `Superseded`/`Rejected`, add
   the new `Accepted` one, respecting the Decision State Machine (section 1).
4. Mark the previous plan `OBSOLETE` (section 3) if the scope change invalidates it.
5. Regenerate the plan (new active content, not a parallel file).
6. Regenerate the task list — no task from the old plan survives unreviewed;
   tasks already completed that are still valid get a note explaining why they
   still hold.
7. Run the full Consistency Gate (section 4).
8. Only then, allow implementation to proceed.

Don't "keep implementing against the old plan while it's being decided" and don't
"implement partially and document the inconsistency for later."

---

## 9. Pre-Implementation Checklist

Before implementation starts, confirm explicitly:

- [ ] Spec status is ready for implementation (whatever that project calls it).
- [ ] The plan is active, with none of the markers from section 3.
- [ ] No `[NEEDS REVIEW]` tasks blocking the tasks about to be implemented.
- [ ] No two `Accepted` decisions on the same axis in the decisions log.
- [ ] Open questions are closed, or explicitly marked non-blocking.
- [ ] Required reviews for this category of change are identified (see the
  project's own review skills/process for what applies).
- [ ] Tests are defined for the behavior being implemented.
- [ ] The Source of Truth Matrix is present and free of contradictions found by
  the gate.
- [ ] No live reference to a `Rejected`/`Superseded` approach remains.

If any box fails, don't implement — go back to the step that resolves it
(clarify the spec, replan, or fix the decisions log) instead of proceeding around
the gap.

---

## 10. What this looks like in practice

A real (anonymized) pattern this skill is meant to catch: a spec went through
v1 → v2 → a final "Option B" architecture decision. In the process:

| Drift that happened | Rule that should have caught it |
|---|---|
| An old plan (v1, assuming a different storage approach) kept being cited as current after the team moved to v2 | Section 3 (Active Plan Rule) — v1 needed an explicit `OBSOLETE` marker the moment v2 was decided |
| An old "Accepted" decision coexisted with a new one on the same axis, with no supersession recorded | Section 1 (Decision State Machine) — one `Accepted` per axis; the old one should flip to `Superseded` in the same change |
| A proposal to reuse an old, already-ambiguous function name with a new return type, contradicting an acceptance criterion that said the old function "must not exist" | Section 5 (Naming Hygiene) + gate item 6 — an already-confusing name doesn't get reused, and the gate compares names literally across documents |
| Tasks mixed "rewrite the ambiguous function" with a final grep that demanded its absence — a direct contradiction inside the same task list | Gate item 3 (tasks vs plan) + item 6 (naming) |
| A scope change didn't automatically invalidate the active plan until someone noticed by hand | Section 8 (Scope Change Protocol), step 4 — invalidation must happen in the same turn as the scope change, not as later cleanup |
| A money/units feature shipped a partial fix before a units table existed in the spec | Section 6 (Units & Money Safety) — the units table is a prerequisite for planning, not an optional appendix added at the end |
| A migration + backfill had no explicit deployment order until late in the process | Section 7 (Deployment Coupling) — required before close-out, not only documented if someone asks |

---

## 11. Limitations — what stays a manual checklist

This skill helps detect and block contradictions *within the documents*, but it
cannot fully automate:

- **Verification against a real production environment** — if the agent can't
  reach production directly, "no real record violates this assumption" can only
  be confirmed by a manual query before deploying; document it as a deployment
  step, don't assume the gate covers it.
- **Detection of non-literal synonyms** — the gate can grep for identical or
  quoted names, but can't guarantee two differently-named functions don't overlap
  semantically without a human (or a targeted search) confirming intent.
- **Correctness of the underlying data audit** that feeds a backfill or migration
  decision — if that audit was done wrong, the gate won't catch it; it only
  checks document consistency, not the truth of the inputs.
- **Judgment about what counts as "the same architectural axis"** for the
  one-`Accepted`-per-axis rule — grouping decisions under the right axis takes
  judgment, it isn't mechanical.
- **Actually running tests/migrations** — the gate checks document consistency,
  it doesn't replace running the test suite or applying a migration against a
  real database.
- **The content of specialized reviews** (security, database, API, etc.) — the
  gate confirms they're *identified as required* and *not yet done*, but the
  substance of each review is its own process.
