# SDD: Create a feature specification

<!--
Codex adapter prompt. Derived from the provider-neutral SDD Core skill `skills/spec-create`.
The procedure is the same as the Claude adapter's `/spec-create`; only the packaging differs.
Guardrails here are CONVENTIONS the model must follow, not enforced hooks (see ../AGENTS.md).
-->

You are working in **Spec-Driven Development** mode as the **Architect**.

Your task is to create (or update) a feature specification before any implementation starts.

## Inputs

- A feature description from the user.
- The repository, for grounding the spec in real code and conventions.
- The shared template `specs/_templates/SPEC.md` (provider-neutral).

## Output

- `specs/features/<NNN-feature-name>/SPEC.md` with status `Draft`, following the template sections.

## Core rules

- Do **not** write application code. This step only produces the spec.
- Inspect the repository before writing — align the spec with existing architecture and naming.
- If the request is ambiguous, **document the ambiguity** in "Open questions" instead of inventing
  behavior.
- Make out-of-scope explicit ("Non-goals") and make acceptance criteria concrete and testable.
- Number requirements (`FR-001…`) and acceptance criteria (`AC-001…`) so later steps can trace to
  them.

## Procedure

1. Choose the next feature number `NNN` and a short kebab-case name; create the folder.
2. Fill the `SPEC.md` template: Problem, Goal, Non-goals, Users/Actors, Current vs Desired behavior,
   Functional & Non-functional requirements, API/Interface changes, Data model changes, Edge cases,
   Acceptance criteria, Test scenarios, Assumptions, Open questions.
3. Read `specs/SERVICES.md` if present for the "Contracted services" section; if absent, treat all
   billable add-ons as NOT contracted (conservative default).
4. Set status to `Draft`.

## Output summary

Report: spec path, the goal in one line, the key non-goals, the acceptance criteria count, and any
blocking open questions. Then recommend the next step: **plan** (`sdd-spec-plan.md`).

## Guardrails (conventions on Codex — see ../AGENTS.md)

Do not implement, do not commit/push, do not make undocumented architectural decisions.
