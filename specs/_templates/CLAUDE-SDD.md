<!--
Installed into a project as specs/CLAUDE-SDD.md by /project-init, which fills
every TODO from its interview. Domain review triggers belong here; product
rules belong in CONSTITUTION.md; process rules in SDD-GUARDRAILS.md.
-->

# Project instructions — TODO: project name (SDD)

## Project context

TODO: 2-4 sentences — what the product is, who uses it, what is business-critical.

**Stack**: TODO: runtime · framework · database/ORM · test runner · key services

**Main modules**: TODO: module → path map (e.g. `ingest → src/lib/ingest`,
`payments → src/services/billing`)

**Current phase / scope source**: TODO: e.g. docs/PLAN.md, roadmap doc, or "n/a"

---

## Consistency Gate — mandatory before `/spec-plan`, `/spec-implement`, `/spec-close`

Before planning, implementing or closing any feature in `specs/features/`, the
rules of **`specs/SDD-GUARDRAILS.md`** apply: Decision State Machine, Source of
Truth Matrix, Active Plan Rule, Naming Hygiene, Units & Money Safety, Deployment
Coupling and the Consistency Gate itself. Mandatory for every spec with more than
one decision in `DECISIONS.md` or touching money/schema/deployment.

---

## Domain-specific review triggers

Beyond the generic SDD triggers:

### `/database-review` is mandatory when:

- TODO: schema/migrations paths change (e.g. `src/db/schema.ts`, `prisma/schema.prisma`)
- TODO: domain-critical tables or constraints (e.g. "any table missing tenant_id",
  "consent fields", "idempotency constraints")

### `/security-review` is mandatory when:

- TODO: public endpoints / webhooks / auth middleware paths
- TODO: secrets and token handling (which env vars, which signing schemes)
- TODO: isolation boundaries (tenancy, roles) whose breach would leak data

### `/privacy-compliance-review` (GDPR) is mandatory when:

- TODO: where PII lives and the single-copy / deletion / export rules
  (delete this section if the project handles no regulated personal data)

### `/performance-review` is recommended when:

- TODO: high-volume tables/queries, polling loops, rendering hot paths

### `/api-review` is mandatory when:

- TODO: which public contracts external parties depend on (webhook status codes,
  DTOs, event payloads)

---

## Non-negotiable domain rules (operational summary)

1. TODO: rule (e.g. "tenant_id on every business table and query")
2. TODO: rule
3. TODO: rule

## Conventions

- TODO: language conventions (code identifiers vs docs)
- TODO: commit style
- TODO: per-task verification commands (e.g. `npm run lint && npm run typecheck && npm run test`)
