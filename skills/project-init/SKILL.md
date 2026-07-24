---
name: project-init
description: Initialize a new project's SDD structure. Creates specs/CONSTITUTION.md, specs/README.md, specs/SDD-GUARDRAILS.md and specs/CLAUDE-SDD.md by interviewing the user about the project stack, architecture rules, coding conventions, security requirements, and review gates. Run this once when starting a new project from the SDD template.
---

## SDD Contract

```yaml
category: lifecycle
inputs: [interview-answers]
outputs: [specs/CONSTITUTION.md, specs/README.md, specs/SDD-GUARDRAILS.md, specs/CLAUDE-SDD.md]
side_effects: writes-specs
writes_code: false
writes_specs: true
analysis_only: false
primary_agent: solution-architect
secondary_agents: []
profile_scope: all
provider_specific: false
```

You are acting as a senior software architect and SDD setup guide.

Your task is to initialize the project's Spec-Driven Development structure by creating the four `specs/` support files every SDD project shares:

- `specs/CONSTITUTION.md` — the permanent rule file that all agents read before reviewing or implementing.
- `specs/README.md` — folder guide and feature index.
- `specs/SDD-GUARDRAILS.md` — the per-project Consistency Gate instance (process rules).
- `specs/CLAUDE-SDD.md` — domain-specific review triggers and operational rules.

## When to use

Run `/project-init` once at the start of a new project, before creating any specs or running any reviews. It is safe to re-run to update an existing constitution.

## Workflow

### Step 1 — Check current state

1. Check if `specs/CONSTITUTION.md` exists.
   - If it exists and has no `TODO:` markers → ask the user if they want to update it. If no, skip to step 1.3 (the other support files may still be missing).
   - If it exists with `TODO:` markers → continue to fill in the missing sections.
   - If it does not exist → copy from the installed templates (`specs/_templates/CONSTITUTION.md` in the central config, e.g. `~/.claude-config/specs/_templates/`) if available, otherwise create from scratch.

2. Check if `specs/features/` directory exists. If not, create it.

3. Check the other three support files, sourcing each from the installed templates (`SPECS-README.md` → `specs/README.md`, `SDD-GUARDRAILS.md` → `specs/SDD-GUARDRAILS.md`, `CLAUDE-SDD.md` → `specs/CLAUDE-SDD.md`):
   - Missing → create it from its template (strip the HTML installation comment at the top).
   - Present with `TODO:` markers → fill them in Step 3.
   - Present without `TODO:` markers → leave untouched.

### Step 2 — Interview the user

Ask the following questions. Wait for answers before proceeding. Group related questions together — do not ask one at a time.

**Round 1 — Project basics:**
- What is the project name and a one-sentence description?
- What is the primary stack? (Next.js, Angular, Java/Spring Boot, or combination)
- Is this a public-facing app, internal tool, or API-only service?
- Does the project handle personal data of EU/Spanish citizens? (affects GDPR rules)

**Round 2 — Architecture:**
- What is the package/module structure? (e.g., feature-based, layer-based)
- Are there any existing architecture decisions that must be respected? (e.g., no class components, DTOs always required, specific ORM)
- What is the database? (PostgreSQL, MySQL, MongoDB, etc.)
- Is there an existing design system or component library? (Tailwind, shadcn/ui, Material, PrimeNG, custom)

**Round 3 — Quality gates:**
- What is the minimum test coverage requirement?
- Which reviews are mandatory before merging? (security, database, API, SEO, GDPR, etc.)
- Are there CI/CD checks that must pass? (type check, lint, build, tests)
- Any patterns that are explicitly forbidden in this project?

**Round 4 — Contracted services:**
- Which services has the client contracted? Default: `web` only. Options (canonical names, matching the agency's Services and Packages catalog): `web`, `seo`, `geo`, `aeo`, `ai-visibility`, `cro`, `analytics`, `crm-integration`, `ai-chatbot`, `ai-follow-up-automation`, `ai-commercial-proposals`, `technical-support`, `growth-strategy`.
- This declaration gates all billable-service behavior downstream (skills installed, review recommendations, implementation boundaries) — see the Billing boundary section in `specs/_templates/CONSTITUTION.md`.

### Step 3 — Generate the specs/ support files

Using the answers:

1. Generate `specs/CONSTITUTION.md` filling in all sections, including the Billing boundary section (rule, boundary table, `UPSELLS.md` instruction — carried over from the template as-is). Do not leave any `TODO:` markers — replace all placeholders with project-specific content based on the interview.
2. Generate `specs/SERVICES.md` from the installed template (`specs/_templates/SERVICES.md`), marking each of the 13 canonical services as contracted (yes, with today's date) or not contracted (no) per the Round 4 answers.
3. Fill `specs/CLAUDE-SDD.md`: project context, stack and module map from Round 1-2; the domain review triggers from Round 2-3 answers (which paths make `/database-review`, `/security-review`, `/api-review` mandatory; keep the GDPR section only if Round 1 said the project handles regulated personal data); the non-negotiable rules and verification commands from Round 3. No `TODO:` markers may remain.
4. Fill the `TODO:` rows of `specs/SDD-GUARDRAILS.md` (Source of Truth Matrix schema path, provider contracts, project-specific gate limitations). Leave the generic rules untouched.
5. Fill `specs/README.md` header (project name, one-line description). The feature index starts empty.

If the user did not answer a question, use a sensible default and note it as a default in the file with a comment `# default — update if needed`.

### Step 4 — Confirm and finalize

Show a summary of the key rules written. Ask the user to confirm or correct any section before saving.

### Step 5 — Graphify adoption (recommended default)

Recommend adopting Graphify so the project starts with a dependency graph from day
one: it accelerates impact analysis and cuts token usage on every plan/review.

- Offer (default yes): run `scripts/setup-graphify.sh --project-dir <this project>`
  (or `setup-graphify.ps1` on Windows) from the SDD checkout. The script installs
  `@sentropic/graphify` only after its own confirmation, generates `.graphify/`,
  gitignores it, and scaffolds `docs/GRAPHIFY.md` + `docs/PROJECT_GRAPH.md`.
- If the user declines: note that everything works without it and they can adopt
  later with the same script.
- Never run npm installs directly from this skill — adoption always goes through
  `setup-graphify`.

## Output

After saving:

```
# Project Init Complete

## Created
- specs/CONSTITUTION.md — N rules defined
- specs/SERVICES.md — contracted services declaration
- specs/README.md — folder guide and feature index
- specs/SDD-GUARDRAILS.md — Consistency Gate instance
- specs/CLAUDE-SDD.md — domain review triggers
- specs/features/ — ready for feature specs

## Key rules
- Stack: [detected stack]
- Mandatory reviews: [list]
- Forbidden patterns: [list]
- GDPR: [yes/no]
- Contracted services: [list]

## Next steps
- Run `/spec-create` to create your first feature spec.
- To activate the hook guardrails in this project, run link-project and then
  scripts/wire-hooks.sh (or wire-hooks.ps1 on Windows) from the SDD repo.
- To adopt Graphify (recommended), run scripts/setup-graphify.sh from the SDD repo.
```

## Context economy

- Ask only the questions above — do not over-interview.
- Do not create feature specs or implementation plans.
- Do not modify any existing code.
- Keep CONSTITUTION.md concise — rules only, no explanations.
