# Feature Spec: billable-service-scope

## Status

Done

## Problem

The framework currently gives away billable services for free. The agency sells "web" and "SEO/GEO/AEO" as separately priced services, but the `next-prisma-web` profile ships `seo-review` by default, and `skills/frontend-review/SKILL.md` (line 27) unconditionally recommends running `/seo-review` after reviewing any public-facing page. There is no machine-readable record of which services a client has actually contracted, so nothing stops the agent (or a developer following the workflow) from implementing SEO/GEO work inside a web-only engagement — silently destroying the upsell.

A coverage audit of `skills/seo-review/SKILL.md` during clarification surfaced two additional defects that belong to this same scope: (a) the skill's checklist covers technical on-page SEO only — hreflang is promised in its description and "When to use" but has zero checklist items, and AEO/GEO/AI-visibility are not covered at all, so an addon shipping only `seo-review` would sell three services and deliver roughly half of one; (b) the skill opens by delegating to a `seo` agent that does not exist in `agents/` (only `deep-reasoner.md` and `fast-worker.md` exist), so the delegation instruction is dead text and the fallback checklist is what actually runs, always.

## Goal

Make "which services the client has paid for" an explicit, declared input to the SDD workflow, and gate all billable-service behavior (skills installed, review recommendations, implementation boundaries) on that declaration. Detected opportunities get logged for sales instead of implemented.

## Non-goals

- No new AEO/GEO/AI-visibility review skills are created now (`aeo-review`, `geo-review`, `ai-visibility-review` are future work, listed only as `plannedSkills`).
- `seo-review` is hardened (hreflang checklist, dead-delegation removal) but NOT expanded into content strategy: keyword research stays out of a code-review skill's scope — it is not reviewable in a git diff and is delivered through the SEO service playbooks, not through this skill.
- No `agents/seo.md` is created now — the dead delegation is removed instead; a real agent can be reintroduced as its own feature when built.
- No hook implementation (`billable-scope-guard` diff scanning is a separate future feature).
- No pricing data anywhere in the framework — only service names.
- No changes to the Java/Spring or messaging profiles.
- No retroactive changes to already-installed projects (installer copies at install time; existing installs are untouched).

## Users / Actors

- **Agency developer** running the SDD workflow on a client web project.
- **AI agent** executing `/project-init`, `/spec-create`, `/frontend-review`, `/spec-implement`.
- **Agency owner** (sales side) who consumes `specs/UPSELLS.md` entries as expansion opportunities.
- **Installer** (`install.sh` / `install.ps1`) consuming `profiles.json`.

## Current behavior

- `profiles.json` → `next-prisma-web.skills` includes `seo-review`; every web install gets SEO review capability bundled.
- `skills/frontend-review/SKILL.md:27` always recommends `/seo-review` for public pages.
- `/project-init` interviews about stack/architecture/quality gates but never asks what services were sold.
- No `SERVICES.md`, no `UPSELLS.md`, no billing-boundary rule in `specs/_templates/CONSTITUTION.md`.

## Desired behavior

- `/project-init` asks which services the client contracted and generates `specs/SERVICES.md` — the single source of truth, using canonical service names: `web`, `seo`, `geo`, `aeo`, `ai-visibility`, `cro`, `analytics`, `crm-integration`, `ai-chatbot`, `ai-follow-up-automation`, `ai-commercial-proposals`, `technical-support`, `growth-strategy`.
- `/spec-create` reads `specs/SERVICES.md` and stamps a "Contracted services" line into every new SPEC. If the file is missing, the spec notes: contracted services not declared → all billable add-ons treated as NOT contracted (conservative default).
- `profiles.json`: `seo-review` removed from `next-prisma-web`; new optional overlay profile `seo-geo-addon` (same pattern as `messaging-event-driven`/`payments-fintech`) ships it, installed only via explicit `--profile next-prisma-web,seo-geo-addon`. The profile declares the full SEO-family roadmap honestly: `plannedSkills: ["aeo-review", "geo-review", "ai-visibility-review"]`, and its note states explicitly that current shipped coverage is technical on-page SEO only — AEO/GEO/AI-visibility reviewers are planned, mirroring the agency catalog where seo, aeo, geo, and ai-visibility are four distinct billable services.
- `skills/seo-review/SKILL.md` hardened: the "Delegation to SEO agent" block is removed (the `seo` agent does not exist; the checklist becomes the primary and only path — zero behavioral change, since the fallback is what always ran), and an **hreflang / internationalization** checklist section is added to close the promised-but-missing gap (alternate links present and reciprocal, `x-default` defined, hreflang values match actual locales, canonical and hreflang not contradicting each other).
- `frontend-review` recommends `/seo-review` only when `specs/SERVICES.md` declares `seo` (or `geo`/`aeo`/`ai-visibility`). When public pages are touched and SEO is NOT contracted, it instructs the agent to append an opportunity entry to `specs/UPSELLS.md` instead — never to implement.
- `specs/_templates/CONSTITUTION.md` gains a **Billing boundary** section: never implement SEO/GEO/AEO/advanced-analytics work unless declared in `SERVICES.md`; log opportunities to `UPSELLS.md`; plus the baseline-quality vs. billable-service boundary table (unique title/description, semantic HTML, alt text, responsive, accessibility, reasonable performance = included web quality; JSON-LD/schema.org, sitemap/robots strategy, OG/Twitter optimization, hreflang, strategic canonicals, keyword research, llms.txt, GEO entity work, ranking-oriented CWV optimization = billable).
- `/project-init` generates that section into the project's `CONSTITUTION.md` from the interview answers.

## Functional requirements

- FR-001: New template `specs/_templates/SERVICES.md` defining the canonical service-name list and a declared-services checklist with contract date and notes fields.
- FR-002: New template `specs/_templates/UPSELLS.md` defining the opportunity log format (date, opportunity, evidence, related spec, status).
- FR-003: `skills/project-init/SKILL.md` — interview gains a "Contracted services" question group; Step 3 additionally generates `specs/SERVICES.md`; generated `CONSTITUTION.md` includes the Billing boundary section.
- FR-004: `specs/_templates/CONSTITUTION.md` — add Billing boundary section (rule + boundary table + UPSELLS.md instruction).
- FR-005: `skills/spec-create/SKILL.md` and `specs/_templates/SPEC.md` — generated specs include a "Contracted services" line sourced from `specs/SERVICES.md`, with the conservative-default note when absent.
- FR-006: `profiles.json` — remove `seo-review` from `next-prisma-web.skills`; add `seo-geo-addon` overlay profile (default false, not disabled) with `skills: ["seo-review"]`, `plannedSkills: ["aeo-review", "geo-review", "ai-visibility-review"]`, and a note documenting the billing rationale and the explicit multi-profile install syntax.
- FR-007: `skills/frontend-review/SKILL.md` — the `/seo-review` recommendation becomes conditional on `specs/SERVICES.md`; the not-contracted path instructs logging to `specs/UPSELLS.md`.
- FR-008: `README.md` — profiles section documents `seo-geo-addon` and the billable-scope concept in one short paragraph.
- FR-009: `skills/seo-review/SKILL.md` — remove the "Delegation to SEO agent" block (the `seo` agent does not exist in `agents/`); add an hreflang / internationalization checklist section (alternate links present and reciprocal, `x-default` defined, hreflang values match actual locales, canonical and hreflang not contradicting each other).

## Non-functional requirements

- Performance: n/a (markdown/JSON edits only).
- Security: no secrets, no client data in any template.
- Observability: n/a.
- Maintainability: `seo-geo-addon` follows the exact structure of existing overlay profiles so the installer needs zero code changes; canonical service names live in exactly one place (`specs/_templates/SERVICES.md`) and other files reference it.

## API / Interface changes

- New files: `specs/_templates/SERVICES.md`, `specs/_templates/UPSELLS.md`.
- Modified: `profiles.json` (manifest contract consumed by both installers), `skills/project-init/SKILL.md`, `skills/spec-create/SKILL.md`, `skills/frontend-review/SKILL.md`, `skills/seo-review/SKILL.md`, `specs/_templates/CONSTITUTION.md`, `specs/_templates/SPEC.md`, `README.md`.
- Installer CLI surface unchanged; new profile reachable via existing `--profile` mechanism.

## Data model changes

None (no database).

## Edge cases

- `specs/SERVICES.md` missing (pre-existing project, or project-init never run) → conservative default: no billable add-ons contracted; skills say so explicitly and suggest running `/project-init`.
- `SERVICES.md` present but malformed / service name not in canonical list → treat unrecognized names as not contracted and flag in review output.
- Mixed repo (Angular + Next.js) in frontend-review → the conditional applies to both branches' public-page recommendation.
- User requests SEO work explicitly in a prompt while `SERVICES.md` says not contracted → constitution rule instructs the agent to surface the conflict, not silently comply (manual override = human edits SERVICES.md first).
- Installer run with `--profile seo-geo-addon` alone → installs core + addon only (documented, mirrors messaging-event-driven behavior — not an error).

## Acceptance criteria

- AC-001: `/project-init` interview text asks for contracted services and its workflow generates `specs/SERVICES.md` using canonical names.
- AC-002: `install.sh --profile next-prisma-web` into a temp dir does NOT install `skills/seo-review/`; `install.sh --profile next-prisma-web,seo-geo-addon` DOES; `profiles.json` passes JSON validation.
- AC-003: `skills/frontend-review/SKILL.md` contains no unconditional `/seo-review` recommendation; the recommendation is gated on `specs/SERVICES.md` declaring an SEO-family service, and the not-contracted branch logs to `specs/UPSELLS.md`.
- AC-004: `specs/_templates/CONSTITUTION.md` contains the Billing boundary section with the rule, the boundary table, and the UPSELLS.md instruction; `project-init` Step 3 instructs generating it.
- AC-005: A spec created via `/spec-create` in a project without `SERVICES.md` carries the conservative-default note; with `SERVICES.md`, it lists the declared services.
- AC-006: `README.md` profiles section documents `seo-geo-addon`.
- AC-007: All 13 canonical service names appear in `specs/_templates/SERVICES.md` and match the agency service catalog.
- AC-008: `skills/seo-review/SKILL.md` contains no reference to a delegated `seo` agent, and its SEO checklist contains an hreflang / internationalization subsection with at least the four checks listed in FR-009.

## Test scenarios

- Unit: n/a (no executable code changed).
- Integration: run `install.sh` twice into temp dirs (web-only vs. web+addon) and assert `skills/seo-review` presence/absence; `jq . profiles.json` validates.
- E2E: n/a.
- Manual: read-through of project-init/spec-create/frontend-review skill texts simulating a fresh web-only project — verify each decision point produces the conservative outcome; verify existing specs/features/* are untouched.

## Assumptions

- The installers consume `profiles.json` generically (adding a well-formed profile requires no installer code change) — verified against the messaging-event-driven precedent; T009 re-verifies empirically.
- `docs/ROADMAP_JAVA_SPRING_CONTEXT.md`'s mention of seo-review is historical documentation and needs no edit.

## Open questions

- None blocking. (Resolved during auto-clarify: source-of-truth location, canonical name list, missing-file default, addon profile contents, baseline/billable boundary, seo-review hardening approach — see DECISIONS.md D001–D006.)
- Resolved at close: all six clarification questions were answered by D001–D006 and implemented. `install.ps1` was not empirically exercised for `seo-geo-addon` (only `install.sh` in T009) — deferred as a one-time Windows dry-run before release, low risk since the installer resolves profiles.json generically.

## Contracted services

Not applicable — this repo is the framework itself, not a client project.
