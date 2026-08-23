# DECISIONS — 017 Implement planned skills and wire them into the review flow

| # | Decision | Rationale | Status |
|---|---|---|---|
| D1 | Two format families, matching existing siblings | Stack reviewers copy the `java-performance-reviewer` shape (triggers/Purpose/Extends/checks/Output/NOT-do); the SEO family copies `seo-review`'s shape ("You are acting as…", checklist, Context economy). Consistency beats novelty. | Active |
| D2 | All three SEO-family skills gate on `specs/SERVICES.md` with the upsell fallback | Same billable-service model spec 008 established for `seo-review` via `frontend-review`; an uncontracted run logs to `specs/UPSELLS.md` and stops — never free work. | Active |
| D3 | `/review-all` gained a routing **table**, not inlined checklists | Inlining 12 stack checklists would bloat the skill and drift from the sources of truth; the table routes to skills that each declare "extends X, run X first". This also wired the *pre-existing* stack reviewers, which review-all previously never mentioned (latent gap). | Active |
| D4 | Payments split: Stripe-specific vs processor-agnostic idempotency | Mirrors the planned entries as declared; the Stripe skill covers the SDK/webhook surface, the idempotency skill covers replay math that applies to any processor (and defers broker semantics to `event-driven-reviewer`). Cross-referenced as siblings. | Active |
| D5 | `plannedHooks` and `OBSERVABILITY.md` template stay planned | User asked for the skills; hooks are enforcement surface with different risk (they execute on every tool call) and deserve their own spec. | Active |
| D6 | Central sync for modified `sdd`/`review-all` done by targeted copy with backup, not `install.sh --force` | Blanket `--force` would also overwrite `spec-create`/`sdd-onboard`, which differ in central for unknown reasons (possibly local edits). Only the two files this spec touched were synced. | Active |
| D7 | No commits | Audit-session constraint; `feat/adopt-graphify-skill` carries unrelated in-flight work — recommend a dedicated branch. | Active |

---

### D00A - Status section added; T16 proposed as Skipped

**Date:** 2026-08-22

**Status:** Accepted

**Context:**

This spec predates the `## Status` convention and was invisible to `/spec-status` and to automated
sweeps, found only by grepping for SPECs lacking the section.

**Decision:**

Add `## Status: In Progress`. Record that **T16 should be `Skipped`, not done** — the decision to
actually skip it belongs to the maintainer and is proposed here, not applied.

**Reasoning:**

All 8 skills in this spec's scope ship on disk and no longer appear under `plannedSkills`. The only
`plannedSkills` left in `profiles.json` — `iac-review`, `kubernetes-review`, `rightsizing-advisor` —
belong to `delivery-operations` (spec 024), not to this spec's scope.

T16 is labelled `(Future)` in its own text and lists four `plannedHooks` that remain deliberately
planned. Carrying a future item as an open task on a finished spec is what keeps this spec from ever
closing; it is scope for a later spec, not debt for this one.

T15 (human domain review of the 8 checklists) is a genuine blocker and stays open.

**Consequences:**

- This spec cannot close until T15 is done by a human with the relevant domain knowledge, or is
  explicitly waived.
- If the maintainer accepts the T16 proposal, it should be moved to a follow-up spec rather than
  deleted, so the four planned hooks are not lost.
