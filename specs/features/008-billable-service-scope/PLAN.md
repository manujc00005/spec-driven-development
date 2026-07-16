# Implementation Plan: billable-service-scope

## Summary

Introduce a declared, machine-readable record of contracted client services (`specs/SERVICES.md`), gate the SEO review pipeline on it (profile split + conditional recommendation), harden `seo-review` itself (dead-delegation removal, hreflang checklist), and encode the billing boundary as a constitutional rule with an UPSELLS.md capture path. Nine files touched, two created; markdown/JSON only, no executable code.

## Related spec

`specs/features/008-billable-service-scope/SPEC.md`

## Impacted areas

- `profiles.json` — profile manifest (consumed by install.sh / install.ps1)
- `skills/project-init/SKILL.md` — interview + generation steps
- `skills/spec-create/SKILL.md` — spec generation procedure
- `skills/frontend-review/SKILL.md` — line 27 recommendation logic
- `skills/seo-review/SKILL.md` — remove dead "Delegation to SEO agent" block; add hreflang / internationalization checklist section (D006)
- `specs/_templates/CONSTITUTION.md`, `specs/_templates/SPEC.md` — templates
- `specs/_templates/SERVICES.md`, `specs/_templates/UPSELLS.md` — new templates
- `README.md` — profiles documentation

## Proposed approach

Work outside-in from the source of truth:

1. **Templates first** (SERVICES.md, UPSELLS.md): define the canonical service vocabulary and formats everything else references. SERVICES.md is a checklist of the 13 catalog services with contracted yes/no, contract date, and notes; UPSELLS.md is an append-only opportunity log.
2. **Producers next** (project-init, CONSTITUTION template): the interview gains one grouped question ("Which services has the client contracted? Default: web only"); Step 3 generates SERVICES.md alongside CONSTITUTION.md; the constitution gains the Billing boundary section with the baseline-vs-billable table so the rule governs every downstream skill that reads the constitution.
3. **Consumers last** (spec-create, frontend-review, profiles.json, README): spec-create stamps declared services into each new SPEC; frontend-review's public-page branch becomes a three-way decision (contracted → recommend `/seo-review`; not contracted → append UPSELLS.md entry, do not implement; SERVICES.md absent → conservative default + suggest `/project-init`); profiles.json moves seo-review into the new `seo-geo-addon` overlay modeled character-for-character on the messaging-event-driven profile structure (description, default:false, skills, plannedSkills: `["aeo-review", "geo-review", "ai-visibility-review"]`, note with explicit multi-profile syntax).
4. **Harden seo-review itself**, independent of the gating mechanism: remove the "Delegation to SEO agent" block (the `seo` agent does not exist in `agents/`, so this is dead text — zero behavioral change, the checklist fallback already runs every time) and add the hreflang / internationalization checklist section, so that when `seo-geo-addon` IS installed, it delivers what it claims to review (D006).

Ordering matters: consumers reference the vocabulary file, so it must exist first for internal links to resolve. Step 4 has no dependency on steps 1–3 and can happen in parallel.

## Alternatives considered

- **SPEC frontmatter as source of truth (per-feature)** — rejected: a client contract spans the whole project, not one feature; per-spec declaration invites drift and re-asking. Project-level SERVICES.md with per-spec stamping gives one source of truth plus local visibility (D001).
- **Keep seo-review in next-prisma-web but gate only the recommendation** — rejected: installing a paid-service skill by default still invites use; the overlay-profile mechanism already exists and matches the commercial model exactly (D003).
- **A `disabled: true` profile like blockchain-crypto** — rejected: seo-geo-addon must be installable normally when sold; `default: false` suffices.
- **Blocking hook now** — deferred: diff-scanning guard (`billable-scope-guard`) is valuable but separable; shipping the declaration + constitution rule first keeps this change reviewable (explicit non-goal).
- **Build a real `agents/seo.md` now instead of removing the dead delegation** — rejected: designing a proper SEO agent is a separably-scoped effort with its own evaluation criteria; this feature's job is to stop overselling, not to build the missing reviewer (D006).
- **Ship `seo-geo-addon` with `seo-review` alone, implying SEO/GEO/AEO are all covered** — rejected: a coverage audit showed `seo-review` is technical-SEO-only; shipping it unlabeled as the addon for three services would oversell in the other direction. `plannedSkills` now names all three future reviewers explicitly (D006).

## Dependencies

None external. Internal precondition: installer treats profiles.json generically (verified against messaging-event-driven; re-verified empirically in T009).

## Risks

- **Boundary-table disputes**: where "web quality" ends and "billable SEO" begins is a business judgment; mitigated by putting the table in one place (CONSTITUTION template) and marking it owner-editable.
- **README drift**: README states "all 43 skills exist"; adding a profile without touching skill count is safe, but the profiles table must be updated or CI consistency check (feature 007) may flag it — T007 covers README, T009 runs validation.
- **Existing installed projects** keep old behavior until re-installed — accepted and documented (non-goal).
- **Unconditional-recommendation regressions**: other skills could re-introduce free SEO advice later; the constitutional rule is the durable backstop.

## Test strategy

- JSON validation of profiles.json (`jq`).
- Empirical installer test: `install.sh --profile next-prisma-web` and `--profile next-prisma-web,seo-geo-addon` into temp dirs; assert `skills/seo-review/` absent/present respectively (AC-002).
- Text-level assertions (grep) that frontend-review has no unconditional recommendation and that the conditional + UPSELLS branches exist (AC-003).
- Text-level assertions (grep) that `seo-review/SKILL.md` has no `seo` agent delegation reference and does contain an hreflang / internationalization checklist section (AC-008).
- Manual read-through simulating a fresh web-only project across project-init → spec-create → frontend-review (AC-001, AC-005).
- Regression: `git diff --stat` confirms only the nine declared files changed; existing specs/features/* untouched.

## Rollback strategy

Single revert — all changes are markdown/JSON in one commit series with no data or code migration. Reverting restores seo-review to next-prisma-web and removes the templates; already-installed client projects are unaffected in either direction.

## PLAN verification checklist

- [x] The plan covers all acceptance criteria.
- [x] The plan avoids behavior outside the spec.
- [x] Risks are documented.
- [x] Test strategy is documented.
- [x] Rollback strategy is documented.
- [x] SPEC.md status has been updated to `Ready`.
