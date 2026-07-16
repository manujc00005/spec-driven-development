<!-- Installed into a project as specs/README.md by /project-init. -->

# Specs — TODO: project name

Feature specifications folder using Spec-Driven Development (SDD).

Before any non-trivial change, read `specs/CONSTITUTION.md`.

Before `/spec-plan`, `/spec-implement` or `/spec-close` on any feature with more
than one decision in `DECISIONS.md`, or touching money/schema/deployment, read
`specs/SDD-GUARDRAILS.md` — it defines the Consistency Gate that catches plans
based on superseded decisions and SPEC/PLAN/TASKS contradictions before they
reach implementation.

Domain-specific review triggers for this project live in `specs/CLAUDE-SDD.md`.

---

## Structure of each feature

```
specs/features/001-feature-name/
├── SPEC.md                    — what and why
├── PLAN.md                    — implementation strategy
├── TASKS.md                   — small, actionable tasks
├── DECISIONS.md               — technical decisions with status
└── IMPLEMENTATION_SUMMARY.md  — added on close by /spec-close
```

## Workflow

`/spec-create` → `/spec-clarify` → `/spec-plan` → `/spec-analyze` →
`/spec-implement` → `/spec-review` + specialized reviews → `/spec-close`.

## Features

| # | Feature | Status |
|---|---|---|
| — | TODO: filled in as features are created | — |
