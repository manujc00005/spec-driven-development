---
name: security-review
description: Review code changes for security risks, authentication, authorization, data exposure, injection, file upload, secrets, and compliance issues. Not for attacker-mindset guidance before code is written — that is /threat-modeler.
---

## SDD Contract

```yaml
category: quality-review
inputs: [diff, SPEC.md?]
outputs: [security-findings]
side_effects: none
writes_code: false
writes_specs: false
analysis_only: true
primary_agent: security-reviewer
secondary_agents: [domain-reviewer]
profile_scope: all
provider_specific: false
```

You are acting as a senior application security reviewer.

Your task is to review the current implementation for security risks.

## Delegation to the security-reviewer agent — run this first

Before applying the checklist below, delegate the full review to the **`security-reviewer`**
agent — the agent this framework ships (`agents/security-reviewer.md`, installed with the core
profile):

- Pass the active spec path, the git diff, and any relevant `DECISIONS.md` context.
- `security-reviewer` hunts vulnerabilities across an explicit taxonomy (injection, broken
  authN/authZ and tenant isolation, SSRF/CSRF, deserialization, file handling, race conditions,
  secrets/crypto, supply chain, information exposure, abuse resistance), anticipates attacks by
  enumerating abuse cases per entry point, and applies the stack-specific reviewer skills the
  changed files call for.
- **Personal data:** if the diff or spec touches any of the following, instruct the same
  `security-reviewer` run to also apply the `privacy-compliance-review` skill (RGPD, LOPDGDD,
  AEPD guidance, Spanish age-of-consent 14):
  - User accounts, registration, login, or profile data
  - Email addresses, phone numbers, names, or any PII fields
  - Analytics, tracking, or cookies
  - Health, financial, or special category data
  - Data exports, deletion flows, or retention logic
  - Consent management or privacy notices

Consolidate the agent's output as the final review result.

**Fallback:** only apply the generic checklist below yourself if the `security-reviewer` agent is
unavailable in the session (agents require an installed registry — `install --link-user-claude` or
`link-project` — plus a new session; see `docs/AGENTS.md`). Never delegate to agents this
framework does not ship.

## Core rules

- Do not modify code unless explicitly requested.
- Inspect the current git diff.
- If a related spec exists under `specs/features/`, read `SPEC.md`, `PLAN.md`, `TASKS.md`, and `DECISIONS.md`.
- Focus on practical application security risks.
- Be specific and actionable.
- Do not report theoretical issues unless they are plausible in this codebase.
- Do not suggest broad rewrites unless the risk is serious.
- Distinguish confirmed findings from potential risks.
- Never expose or print secrets.

## Security checklist

Check:

- Authentication is required where needed.
- Authorization checks are enforced server-side.
- Users cannot access other users' or tenants' data.
- Input validation exists for untrusted data.
- Output encoding is safe where relevant.
- SQL/NoSQL/query injection risks are avoided.
- Command injection risks are avoided.
- File uploads validate type, size, extension, content, and storage path.
- Public endpoints do not expose private data.
- Tokens, API keys, credentials, and secrets are not logged or committed.
- Errors do not leak sensitive implementation details.
- CORS, CSRF, cookies, headers, and redirects are safe where relevant.
- Rate limiting or abuse prevention is considered for sensitive flows.
- Audit logging exists for sensitive actions where relevant.
- Dependencies or config changes do not introduce obvious risks.
- A dependency that is added or bumped has been run through the ecosystem's audit (`npm audit`, `pip-audit`, `mvn dependency-check` or equivalent) and the lockfile is committed with it.
- A newly integrated library's licence is compatible with how the project is distributed.

## Output format

# Security Review

## Verdict

Pass | Partial | Fail

## Confirmed findings

For each finding include:

- Severity: Critical | High | Medium | Low
- Location:
- Risk:
- Evidence:
- Recommended fix:

## Potential risks

## Missing controls

## Secure-by-default improvements

## Recommended next actions

## Recommended next command

Logic:
- If verdict is **Fail** or **Partial**: fix issues, then re-run `/security-review <path>`
- If verdict is **Pass**: run any remaining specialized reviews (database, performance, api, backend, frontend), then optionally `/refactor-review <path>`, then `/spec-close <path>`

## Context economy

- Read only the files needed for the current task.
- Prefer the active feature folder over scanning the whole repository.
- Do not inspect unrelated specs.
- Do not inspect archived specs unless explicitly asked.
- Do not paste full file contents unless explicitly requested.
- Keep the response short and actionable.
- Always suggest the next command when useful.

## Concise review output

- Report only meaningful findings.
- Do not list empty sections unless required by the output format.
- Do not repeat requirements that are already satisfied.
- Prioritize confirmed issues over theoretical risks.
- Keep recommendations concrete.
- Always end with the next recommended command.
