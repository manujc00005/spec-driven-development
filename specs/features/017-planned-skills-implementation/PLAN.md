# PLAN — 017 Implement planned skills and wire them into the review flow

## Approach

1. **Format discovery** — read one exemplar per family before writing anything:
   `java-performance-reviewer` (stack-reviewer shape), `seo-review` (SEO shape),
   `frontend-review` (SERVICES.md billable gating), `/sdd` + `/review-all`
   (where detection/routing live), `check-consistency.sh --fix` (README counts).
2. **Author** the 8 skills, one file each under `skills/<name>/SKILL.md`,
   each declaring what it extends and what it deliberately does NOT cover
   (no checklist overlap with parents or siblings).
3. **Promote** in `profiles.json` with surgical string edits (no JSON
   reserialization — preserves formatting and `$comment` fields).
4. **Wire the flow**: `/sdd` detection additions (profile-gated), `/review-all`
   routing table, `/seo-review` sibling chain. Order inside the SEO family:
   seo → aeo → geo → ai-visibility, each contract-gated.
5. **Truth pass**: README table rows + stale prose, CHANGELOG `[Unreleased]`.
6. **Verify**: consistency check, all self-tests, real install with all five
   profiles, central sync of the two modified core skills (backup first).

## Risks / notes

- The three SEO skills are judgment-heavy domains (AEO/GEO practice evolves);
  checklists encode current practice and should be revisited — flagged T15 for
  user domain review.
- `spec-create` and `sdd-onboard` differ between repo and central for reasons
  outside this spec — deliberately not touched (D6).
