---
name: spec-clarify
description: Clarify and strengthen an existing SPEC.md before planning. Use this to detect ambiguity, missing requirements, unclear acceptance criteria, edge cases and blocking questions.
---

## SDD Contract

```yaml
category: lifecycle
inputs: [SPEC.md]
outputs: [SPEC.md(clarified)]
side_effects: writes-specs
writes_code: false
writes_specs: true
analysis_only: false
primary_agent: solution-architect
secondary_agents: []
profile_scope: all
provider_specific: false
```

You are working in Spec-Driven Development mode.

Your task is to clarify an existing feature specification before implementation planning.

> Note: `/spec-create` now includes a lightweight auto-clarify pass. Use this skill when you need a deeper clarification pass, when the user has answered blocking questions, or when the spec was created externally.

## Core rules

- Do not implement production code.
- Do not modify application code.
- Read `specs/CONSTITUTION.md` if it exists.
- Read the target `SPEC.md`.
- Focus on ambiguity, missing requirements, unclear scope, weak acceptance criteria and hidden edge cases.
- Ask clarification questions only when they are blocking.
- If something is uncertain but not blocking, document it as an assumption.
- Prefer concrete recommendations over vague feedback.
- Keep the process lightweight for a solo developer.

## Clarification checklist

Check:

- Is the problem clearly defined?
- Is the goal clear and measurable?
- Are non-goals defined?
- Are users or actors identified?
- Is current behavior described?
- Is desired behavior described?
- Are functional requirements specific?
- Are non-functional requirements relevant?
- Are API or interface changes clear?
- Are data model changes clear?
- Are edge cases listed?
- Are acceptance criteria testable?
- Are test scenarios useful?
- Are assumptions explicit?
- Are open questions blocking or non-blocking?
- Does the spec mention whether the change touches database, security, external integrations or public APIs?

## Update behavior

If the spec can be improved without user input:

- Update `SPEC.md` directly.
- Add assumptions to the `Assumptions` section.
- Add unresolved doubts to `Open questions`.
- Improve weak acceptance criteria.
- Add missing edge cases.
- Add missing test scenarios.

If clarification is required from the user:

- Do not proceed to planning.
- List the minimum set of blocking questions.
- Provide a recommended default answer for each question when possible.

## Output format

# Spec Clarification

## Verdict

Ready for planning | Needs clarification

## Improvements made

## Assumptions added

## Open questions

## Blocking questions

## Recommended defaults

## Recommended next command

Logic:
- If verdict is **Needs clarification**: answer the blocking questions above, then re-run `/spec-clarify <path>`
- If verdict is **Ready for planning**: `/spec-plan <path>`

## Context economy

- Read only the files needed for the current task.
- Prefer the active feature folder over scanning the whole repository.
- Do not inspect unrelated specs.
- Do not inspect archived specs unless explicitly asked.
- Do not paste full file contents unless explicitly requested.
- Keep the response short and actionable.
- Always suggest the next command when useful.
