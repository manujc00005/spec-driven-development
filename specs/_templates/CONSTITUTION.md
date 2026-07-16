<!--
Draft template — not a literal extraction.

skills/project-init/SKILL.md describes an interview process (project basics,
architecture, quality gates) and instructs the agent to generate
specs/CONSTITUTION.md "filling in all sections" from the answers, but it does
not embed a fixed section-by-section template the way SPEC.md/PLAN.md/
TASKS.md/DECISIONS.md do.

This file is a reasonable draft skeleton inferred from that interview
structure, provided so the folder isn't empty. Running `/project-init` is
still the source of truth — it will ask the questions below and replace every
TODO with project-specific content instead of leaving a generic placeholder.
-->

# Project Constitution

## Project basics

- **Name:** TODO: project name
- **Description:** TODO: one-sentence description
- **Primary stack:** TODO: e.g. Next.js, Angular, Java/Spring Boot, or a combination
- **Nature:** TODO: public-facing app | internal tool | API-only service
- **Handles personal data of EU/regulated users:** TODO: yes/no — affects which compliance review applies

## Architecture

- **Package/module structure:** TODO: e.g. feature-based, layer-based
- **Existing architecture decisions that must be respected:** TODO
- **Database:** TODO: e.g. PostgreSQL, MySQL, MongoDB
- **Design system / component library:** TODO: e.g. Tailwind, shadcn/ui, Material, PrimeNG, custom

## Quality gates

- **Minimum test coverage:** TODO
- **Mandatory reviews before merging:** TODO: e.g. security, database, API, SEO, privacy
- **Required CI/CD checks:** TODO: e.g. type check, lint, build, tests
- **Explicitly forbidden patterns:** TODO

## Billing boundary

- **Rule:** never implement SEO/GEO/AEO/advanced-analytics work unless the corresponding service is declared contracted in `specs/SERVICES.md`. If the file is missing, treat no billable add-on as contracted (conservative default) and suggest running `/project-init`.
- **When work is detected but not contracted:** log an entry to `specs/UPSELLS.md` (date, opportunity, evidence, related spec, status) instead of implementing it.
- **Baseline quality vs. billable service:**

| Included in web baseline | Billable (requires contracted service) |
|---|---|
| Unique title/description per page | JSON-LD / schema.org |
| Semantic HTML | Sitemap/robots strategy |
| Alt text | OG/Twitter optimization |
| Responsive | hreflang |
| Accessibility | Strategic canonicals |
| Reasonable performance | Keyword research |
| | llms.txt |
| | GEO entity work |
| | Ranking-oriented CWV optimization |

This table is owner-editable — adjust it per project during `/project-init` if the commercial boundary differs.

## Notes

Run `/project-init` to populate this file through an interview instead of filling in the TODOs by hand.
