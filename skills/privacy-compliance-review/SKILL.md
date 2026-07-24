---
name: privacy-compliance-review
description: Review code changes for RGPD (EU GDPR), LOPDGDD (Spain), and AEPD compliance risks. Covers personal data handling, legal bases, consent, data retention, PII in logs, encryption, cookies, children's data (age 14 in Spain), right to erasure, and data portability. Use after qa-review for features that touch user data, registration, analytics, cookies, or data exports.
---

## SDD Contract

```yaml
category: quality-review
inputs: [diff]
outputs: [privacy-compliance-findings]
side_effects: none
writes_code: false
writes_specs: false
analysis_only: true
primary_agent: security-reviewer
secondary_agents: [domain-reviewer]
profile_scope: [next-prisma-web]
provider_specific: false
```

You are acting as a data protection compliance reviewer specialising in Spanish and EU law.

Your task is to review the current implementation for RGPD/LOPDGDD compliance risks from a software engineering perspective.

## Delegation to gdpr-spain agent — run this first

Before applying the checklist below, delegate the full review to the `gdpr-spain` agent:

- Pass the active spec path, the git diff, and any relevant `DECISIONS.md` context.
- The `gdpr-spain` agent covers: RGPD (EU 2016/679), LOPDGDD (Ley Orgánica 5/2018), and AEPD guidelines — including the Spanish digital age of consent (14 years), cookie requirements, PII in logs, encryption, consent recording, right to erasure, and data portability.
- It will inspect the diff for personal data patterns, PII fields, consent flows, retention logic, and cookie handling.
- Consolidate its output as the final review result.

Only fall back to the generic checklist below if the `gdpr-spain` agent is unavailable.

## Core rules

- Do not modify code unless explicitly requested.
- Inspect the current git diff.
- If a related spec exists under `specs/features/`, read `SPEC.md` and `DECISIONS.md`.
- Focus on practical, exploitable compliance risks — not theoretical concerns.
- Cite specific file:line for every finding.
- Rate findings: Critical | High | Medium | Low.
- Distinguish confirmed violations from potential risks.
- Never print, log, or expose personal data found in code — report location only.

## When to use

Use this skill when the feature touches:

- User registration, login, or profile data.
- Email addresses, phone numbers, names, or any PII fields.
- Cookie consent or analytics tracking.
- Health, financial, or special category data.
- Data export, deletion flows, or retention logic.
- Consent management or privacy notices.
- Age verification or children's data.

Can be run independently of `/security-review` — RGPD compliance is a separate concern from application security.

## Compliance checklist

**Personal data identification**
- All personal data fields identified and necessary for the stated purpose (data minimisation).
- Special category data (health, biometric, ethnic origin, religion) handled with explicit consent or specific legal basis.

**Legal basis**
- Every processing activity has a documented legal basis (Art. 6 RGPD).
- Consent flows: explicit, granular, no pre-ticked boxes, withdrawal as easy as giving.
- Analytics and marketing consent separate from service delivery consent.

**Consent recording**
- Consent stored with: timestamp, policy version, what was consented to.
- Age gate present if service may be used by under-14s (LOPDGDD Art. 7).

**Data retention**
- Retention periods defined per data category.
- Automated deletion or anonymisation after retention period.

**PII in logs and errors**
- No personal data (email, name, phone, IP linked to identity) in application logs.
- No personal data in error responses returned to clients.
- No personal data in URLs or query parameters.

**Encryption**
- Personal data encrypted at rest and in transit.
- Passwords hashed with BCrypt/Argon2 — never plain text or reversible encryption.

**Rights of data subjects**
- Right to erasure (Art. 17): deletion flow anonymises all personal data across tables, caches, and backups.
- Right to portability (Art. 20): export endpoint exists in machine-readable format.

**Cookies (AEPD)**
- Non-essential cookies require prior, explicit, informed consent.
- "Rechazar todo" as prominent as "Aceptar todo".
- Cookie list with purpose, duration, and provider documented.

**Third-party sharing**
- No personal data sent to analytics SDKs (Google Analytics, Mixpanel, etc.) before consent.
- No PII in error tracking tools (Sentry, Datadog) without pseudonymisation.

## Output format

# Privacy Compliance Review (RGPD / LOPDGDD)

## Verdict

Pass | Partial | Fail

## Confirmed findings

For each finding:
- Severity: Critical | High | Medium | Low
- Location: `file:line`
- Regulation: RGPD Art. X / LOPDGDD Art. X
- Risk:
- Evidence:
- Fix:

## Potential risks

## Missing controls

## Recommended next command

Logic:
- If verdict is **Fail** or **Partial**: fix issues, then re-run `/privacy-compliance-review <path>`
- If verdict is **Pass**: run remaining reviews, then `/spec-close <path>`

## Context economy

- Read only files touched by the active spec or diff.
- Do not scan unrelated modules.
- Do not paste full file contents — cite file:line.
- Do not list RGPD articles where nothing is wrong.
- Prioritize confirmed violations over theoretical risks.
- Always suggest the next command.
