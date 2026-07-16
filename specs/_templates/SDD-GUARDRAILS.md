<!--
Installed into a project as specs/SDD-GUARDRAILS.md by /project-init.
This is the per-project instance of the skills/sdd-guardrails doctrine; if the
skill evolves, refresh this file. Project-specific rows are marked TODO.
-->

# SDD Guardrails — Consistency across SPEC / PLAN / TASKS / DECISIONS

Process rules so the agent detects contradictions between documents **before**
planning, implementing or closing — without depending on the user noticing.

Applies to every spec in `specs/features/*/`. It does not replace
`specs/CONSTITUTION.md` (product rules) or `specs/CLAUDE-SDD.md` (domain review
triggers) — it is the process layer connecting them.

---

## 1. Decision State Machine

Every `DECISIONS.md` entry has a `Status` from this closed set:

- `Proposed` — on the table, not decided.
- `Accepted` — current; may be used by PLAN/TASKS.
- `Superseded` — replaced by a later decision. Must link to it (`Superseded by D0XX`).
- `Rejected` — evaluated and discarded; not revived without a new decision.
- `Deferred` — explicitly postponed; neither blocks the current spec nor may be
  assumed resolved.

**Rules:**

- At most **one** `Accepted` decision per architectural axis. A second decision on
  the same axis moves the previous one to `Superseded` in the same change.
- Every `Superseded` decision notes what (if anything) remains true of it and what
  is replaced.
- No `PLAN.md` may rely on a `Superseded`/`Rejected` decision as if current;
  historical references must say "superseded, do not use".
- If an active architecture decision changes status, any `PLAN.md` depending on it
  becomes obsolete automatically (rule 3) — this does not require the user to ask.

## 2. Source of Truth Matrix (mandatory in non-trivial SPEC.md)

```md
## Source of Truth Matrix

| Concept | Source of truth | Documents that must reflect it |
|---|---|---|
| Data model | DECISIONS.md (Accepted) + TODO: schema file path | SPEC, PLAN, TASKS |
| Naming of new functions/files | PLAN.md | TASKS, tests, DECISIONS (if naming hygiene applied) |
| Business rules | SPEC.md | PLAN, TASKS, tests |
| Units & formats (cents/%, dates, ids, TODO: project-specific) | SPEC.md → units section | PLAN, TASKS, code |
| Deployment / migration↔code ordering | DECISIONS.md | PLAN (Risks), TASKS (close-out phase) |
| Provider contracts (TODO: e.g. Stripe, Meta, LLM APIs) | SPEC.md (Acceptance criteria) | PLAN, TASKS, tests |
```

The Consistency Gate (section 4) uses this table to arbitrate when two documents
disagree. If the matrix is missing in a non-trivial spec, the gate must ask for it
before continuing.

## 3. Active Plan Rule

Only **one** active `PLAN.md` per feature.

- An obsolete plan starts literally with:
  `> OBSOLETE — Do not implement this plan. Superseded by the plan that follows D0XX.`
- `/spec-implement` is forbidden from a `PLAN.md` whose active content carries
  `OBSOLETE`, `NEEDS REVIEW`, `PARTIAL` or `SUPERSEDED` — unless the task is fixing
  the documentation itself.
- A replaced plan is not deleted and not duplicated into parallel files: mark it
  `OBSOLETE` and let the new active content replace it (history lives in
  `DECISIONS.md`).
- A `TASKS.md` containing `[NEEDS REVIEW]` tasks is not eligible for
  `/spec-implement` until they are resolved.

## 4. Consistency Gate — mandatory before `/spec-plan`, `/spec-implement`, `/spec-close`

Run this check and **stop to request a correction if anything fails** — never
continue "assuming it will be fixed later":

1. **Decisions**: at most one `Accepted` per axis? Does the PLAN use any decision
   that is actually `Superseded`/`Rejected`?
2. **PLAN vs SPEC**: do data model, names and business rules match the Source of
   Truth Matrix?
3. **TASKS vs PLAN**: does every task use the PLAN's names? Does any task describe
   an approach the PLAN abandoned?
4. **AC ↔ TASKS bidirectional**: every AC covered (`Covers: AC-XXX`) and every task
   covering a real AC?
5. **Units and types**: same field, same unit/format across SPEC, PLAN, TASKS?
6. **Naming consistency**: one name per concept across all four documents?
7. **Discarded approaches**: no active reference to `Rejected`/`Superseded` options?
8. **Blocking questions**: SPEC `Open questions` resolved or marked non-blocking?
9. **Active plan**: `PLAN.md` free of section-3 markers?

On failure: stop, list the exact contradiction (document, line if possible), and
ask for a decision or correction.

## 5. Naming Hygiene Rule

If a function/field name already caused confusion (ambiguous unit, unclear
contract, a real bug partly attributable to the name), it is **not reused** even
if the implementation changes:

- The decision recording it fixes the new name explicitly; SPEC/PLAN/TASKS use it
  literally and identically (gate point 6 verifies).
- Fields representing money, percentages, units or discriminated types carry an
  explicit suffix when the bare name proved ambiguous: `Cents`, `Percent`, `Ms`,
  `Type`, `Rule`, `Config`.
- A close-out grep confirms the old name does not survive anywhere — not as a
  definition, an import, or a re-export.

## 6. Units & Money Safety Rule

Any feature touching payments, prices, discounts, taxes, quotas or any numeric
field with a unit must include, before `/spec-implement`:

- A units table in `SPEC.md` (which field is cents, which is percent 0-100, which
  format for dates/phones/ids). Without it, the gate blocks the plan.
- A named validation function invoked **before** any call to the payment/provider
  SDK; no amount reaches the provider without passing it.
- Explicit boundary tests: negative amount, discount greater than base, percent
  out of 0-100, unrecognized/corrupt type.
- Mandatory reviews: `/security-review`, `/api-review`, `/backend-review`, and
  `/database-review` if schema is touched.
- No field whose unit depends on the value's range; conversions always explicit
  and named.

## 7. Deployment Coupling Rule

If a feature includes a schema migration **and** code that requires it, `PLAN.md`
or `DECISIONS.md` must answer in a `## Deployment coupling` section:

- Does the new code require the migration applied before deploying? (yes/no, why)
- Is there a backfill? Mandatory in the same step, or deferrable?
- What happens if code and DB end up misaligned in either direction?
- Rollback plan if the deploy fails halfway?
- Does production require a manual step?

`/spec-close` cannot pass without this section when it applies.

## 8. Scope Change Protocol

If the scope of an already-planned spec changes, in this order, skipping nothing:

1. Stop any implementation in progress.
2. Update `SPEC.md` (including the Source of Truth Matrix).
3. Update the affected `DECISIONS.md` entries respecting rule 1.
4. Mark the previous `PLAN.md` as `OBSOLETE` if the change invalidates it.
5. Regenerate `PLAN.md` (new active content, no parallel file).
6. Regenerate `TASKS.md` — no task from the old plan survives unreviewed; completed
   tasks that remain valid are marked so with an explicit note.
7. Run the full Consistency Gate.
8. Only then, `/spec-implement`.

## 9. Pre-Implementation Checklist

Before `/spec-implement`, confirm explicitly:

- [ ] `SPEC.md → Status` is `Ready`.
- [ ] `PLAN.md` active, free of section-3 markers.
- [ ] `TASKS.md` without blocking `[NEEDS REVIEW]` tasks.
- [ ] `DECISIONS.md` without two `Accepted` on the same axis.
- [ ] `Open questions` closed or explicitly non-blocking.
- [ ] Required reviews identified (per `specs/CLAUDE-SDD.md` + rules 6/7).
- [ ] Tests defined in `PLAN.md → Test strategy` / `SPEC.md → Test scenarios`.
- [ ] Source of Truth Matrix present and contradiction-free.
- [ ] No active reference to a `Rejected`/`Superseded` approach.

If any box fails, do not implement — go back to `/spec-clarify`, `/spec-plan`, or
fix `DECISIONS.md`.

## 10. Limitations — manual checklist

- Data audits feeding a backfill are executed by hand and documented in
  `DECISIONS.md`; the gate cannot verify them.
- The gate greps literal names; semantic overlap between two different names needs
  human judgment or a targeted grep.
- Grouping decisions under "the same architectural axis" requires judgment.
- The gate reviews document consistency; it does not replace running tests or
  migrations against a real database.
- Specialized reviews: the gate confirms they are identified and pending/executed;
  their content is their own process.
- TODO: project-specific limits the gate cannot verify at runtime (e.g. "every
  query is tenant-filtered") and which tests/reviews cover them instead.
