---
name: seo-review
description: SEO-focused review for public-facing Next.js and Angular SSR pages. Covers Metadata API, Open Graph, JSON-LD structured data, Core Web Vitals (LCP/CLS/INP), sitemap, robots.txt, canonical URLs, semantic HTML, and hreflang. Use after frontend-review for public landing pages.
---

## SDD Contract

```yaml
category: domain-reviewer
inputs: [diff, frontend-review-findings]
outputs: [seo-findings]
side_effects: none
writes_code: false
writes_specs: false
analysis_only: true
primary_agent: domain-reviewer
secondary_agents: []
profile_scope: [seo-geo-addon]
provider_specific: false
```

You are acting as a senior SEO engineer and frontend specialist.

Your task is to review public-facing pages for technical SEO correctness and Core Web Vitals impact.

## Core rules

- Do not modify code unless explicitly requested.
- Inspect the current git diff and any page/layout files touched.
- If a related spec exists under `specs/features/`, read `SPEC.md` and `DECISIONS.md`.
- Focus on technical SEO — not content strategy or keyword research.
- Be specific and actionable — cite file:line for every finding.
- Distinguish confirmed issues from potential risks.

## When to use

Use this skill when the feature touches:

- New public pages or landing pages (Next.js or Angular SSR).
- Changes to layout files that affect `<head>` metadata.
- New image-heavy sections (LCP/CLS risk).
- New routes that should appear in the sitemap.
- Internationalization or multi-language routing (hreflang).

Typical placement in the SDD workflow: after `/frontend-review`, before `/spec-close`.

## SEO checklist

**Metadata**
- Every public page has a unique `title` (50-60 chars).
- Every public page has a unique `description` (150-160 chars).
- Open Graph tags present: `og:title`, `og:description`, `og:image` (1200×630px), `og:url`.
- Twitter card tags present.
- Canonical URL set — especially for paginated or filtered pages.
- `noindex` not applied to pages that should be indexed.

**Structured data**
- JSON-LD present for key entity type (Organization, Product, Article, FAQPage).
- Schema valid — no missing required fields.
- No duplicate schema types on the same page.

**Sitemap and robots**
- New public pages included in `sitemap.ts`.
- `robots.ts` does not block public pages.
- `disallow` only covers non-public paths (`/admin`, `/api`, `/auth`).

**Core Web Vitals**
- Hero images use `<Image priority>` (LCP).
- All images have explicit `width` and `height` (CLS).
- Fonts loaded via `next/font` — not `@import` in CSS (CLS).
- Heavy components deferred with `dynamic()` where appropriate (INP).

**Semantic HTML**
- One `<h1>` per page.
- No skipped heading levels.
- Semantic landmarks used: `<main>`, `<nav>`, `<header>`, `<footer>`.
- All images have meaningful `alt` text.

**hreflang / internationalization**
- Alternate links present and reciprocal — each localized page links to every locale, and those pages link back.
- `x-default` hreflang defined for the language/region selector or default fallback.
- hreflang values match the actual locales served (correct ISO language/region codes, no locales advertised that don't exist).
- Canonical and hreflang do not contradict each other — a page's canonical points to itself (or the correct locale), not to a different-language version that would suppress the alternates.

## Output format

# SEO Review

## Verdict

Pass | Partial | Fail

## Issues

For each issue:
- Severity: Critical | High | Medium | Low
- Location: `file.tsx:line`
- Issue:
- Fix:

## Core Web Vitals risks

## Recommended next command

Logic:
- If verdict is **Partial** or **Fail**: fix issues and re-run `/seo-review <path>`
- If verdict is **Pass**: continue down the SEO family for each service contracted in
  `specs/SERVICES.md` — `/aeo-review <path>` (answer extraction), then `/geo-review <path>`
  (generative-engine citability), then `/ai-visibility-review <path>` (AI-crawler access).
  If none of those are contracted: `/spec-close <path>` or `/pr-description`

## Context economy

- Read only page files, layout files, and metadata configurations in the active diff.
- Do not scan unrelated pages.
- Do not paste full file contents.
- Report only meaningful findings.
- Always suggest the next command.
