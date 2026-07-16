# Tasks: billable-service-scope

## Phase 1: Preparation

- [x] T001 - Create `specs/_templates/SERVICES.md`: canonical 13-service vocabulary (web, seo, geo, aeo, ai-visibility, cro, analytics, crm-integration, ai-chatbot, ai-follow-up-automation, ai-commercial-proposals, technical-support, growth-strategy), contracted checklist with date/notes, and the missing-file conservative-default rule stated in the header. Covers: AC-001, AC-005, AC-007.
- [x] T002 - Create `specs/_templates/UPSELLS.md`: append-only opportunity log format (date, opportunity, evidence, related spec, status: open/proposed/won/discarded) with usage note "log, never implement". Covers: AC-003, AC-004.

## Phase 2: Implementation

- [x] T003 - Update `specs/_templates/CONSTITUTION.md`: add "Billing boundary" section — the never-implement-undeclared-billable-services rule, the baseline-quality vs. billable-service table, and the UPSELLS.md instruction. Covers: AC-004.
- [x] T004 - Update `skills/project-init/SKILL.md`: add "Contracted services" question group to the Step 2 interview (default: web only); extend Step 3 to also generate `specs/SERVICES.md` from the answers and include the Billing boundary section in the generated CONSTITUTION.md; update the Output block to list SERVICES.md as created. Covers: AC-001, AC-004.
- [x] T005 - Update `skills/spec-create/SKILL.md` and `specs/_templates/SPEC.md`: spec generation reads `specs/SERVICES.md` and stamps a "Contracted services" line into every new SPEC; absent file → conservative-default note plus suggestion to run `/project-init`. Covers: AC-005.
- [x] T006 - Update `profiles.json`: remove `seo-review` from `next-prisma-web.skills` (update its note); add `seo-geo-addon` overlay profile (default false, skills: [seo-review], plannedSkills: [aeo-review, geo-review, ai-visibility-review], note with billing rationale and explicit `--profile next-prisma-web,seo-geo-addon` syntax). Covers: AC-002, AC-007.
- [x] T007 - Update `skills/frontend-review/SKILL.md` (line 27 area, both Next.js and Angular branches where public pages apply): replace unconditional `/seo-review` recommendation with the three-way conditional (contracted → recommend; not contracted → append `specs/UPSELLS.md` entry, do not implement; SERVICES.md missing → conservative default). Update `README.md` profiles section to document `seo-geo-addon` and the billable-scope concept. Covers: AC-003, AC-006.
- [x] T008 - Harden `skills/seo-review/SKILL.md`: remove the "Delegation to SEO agent" block (the `seo` agent does not exist in `agents/` — dead text, zero behavioral change); add an hreflang / internationalization checklist subsection to the SEO checklist (alternate links present and reciprocal, `x-default` defined, hreflang values match actual locales, canonical and hreflang not contradicting each other). Covers: FR-009, AC-008.

## Phase 3: Tests

- [x] T009 - Validate `jq . profiles.json`; run `install.sh --profile next-prisma-web` and `--profile next-prisma-web,seo-geo-addon` into temp dirs and assert `skills/seo-review/` absent/present; grep-assert frontend-review has no unconditional recommendation; grep-assert `seo-review/SKILL.md` has no `seo` agent delegation reference and does have an hreflang checklist subsection; `git diff --stat` shows only the nine declared files. Covers: AC-002, AC-003, AC-007, AC-008.
- [x] T010 - Manual walkthrough as a fresh web-only client project: read project-init interview → confirm SERVICES.md generation instruction; read spec-create → confirm stamping + conservative default; read frontend-review → confirm UPSELLS path; read seo-review → confirm no dead delegation and hreflang checklist present. Covers: AC-001, AC-004, AC-005, AC-006, AC-008.

## Phase 4: Review

- [x] T011 - Run `/spec-review` and `/qa-review` against all acceptance criteria; run `/sdd-guardrails` for consistency with DECISIONS.md; close via `/spec-close`. Covers: AC-001 through AC-008.
