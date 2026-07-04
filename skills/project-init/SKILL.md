---
name: project-init
description: Initialize a new project's SDD structure. Creates specs/CONSTITUTION.md by interviewing the user about the project stack, architecture rules, coding conventions, security requirements, and review gates. Run this once when starting a new project from the SDD template.
---

You are acting as a senior software architect and SDD setup guide.

Your task is to initialize the project's Spec-Driven Development structure by creating `specs/CONSTITUTION.md` — the permanent rule file that all agents read before reviewing or implementing.

## When to use

Run `/project-init` once at the start of a new project, before creating any specs or running any reviews. It is safe to re-run to update an existing constitution.

## Workflow

### Step 1 — Check current state

1. Check if `specs/CONSTITUTION.md` exists.
   - If it exists and has no `TODO:` markers → ask the user if they want to update it. If no, stop.
   - If it exists with `TODO:` markers → continue to fill in the missing sections.
   - If it does not exist → copy from `specs/templates/CONSTITUTION.md` if available, otherwise create from scratch.

2. Check if `specs/features/` directory exists. If not, create it.

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

### Step 3 — Generate CONSTITUTION.md

Using the answers, generate `specs/CONSTITUTION.md` filling in all sections. Do not leave any `TODO:` markers — replace all placeholders with project-specific content based on the interview.

If the user did not answer a question, use a sensible default and note it as a default in the file with a comment `# default — update if needed`.

### Step 4 — Confirm and finalize

Show a summary of the key rules written. Ask the user to confirm or correct any section before saving.

## Output

After saving:

```
# Project Init Complete

## Created
- specs/CONSTITUTION.md — N rules defined
- specs/features/ — ready for feature specs

## Key rules
- Stack: [detected stack]
- Mandatory reviews: [list]
- Forbidden patterns: [list]
- GDPR: [yes/no]

## Next step
Run `/spec-create` to create your first feature spec.
```

## Context economy

- Ask only the questions above — do not over-interview.
- Do not create feature specs or implementation plans.
- Do not modify any existing code.
- Keep CONSTITUTION.md concise — rules only, no explanations.
