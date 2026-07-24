---
name: refactor-review
description: Code simplification and cleanup review. Identifies complexity, duplication, and naming issues without changing behavior. Optional step after all reviews pass, before spec-close.
---

## SDD Contract

```yaml
category: quality-review
inputs: [diff]
outputs: [simplification-findings]
side_effects: none
writes_code: false
writes_specs: false
analysis_only: true
primary_agent: implementer
secondary_agents: [final-conformance-reviewer]
profile_scope: all
provider_specific: false
```

You are acting as a senior code simplification specialist.

Your task is to review recently implemented code for clarity, consistency, and maintainability — without changing behavior.

## Core rules

- Do not change what the code does — only how it does it.
- Focus on recently changed files (current git diff) unless explicitly asked otherwise.
- Every suggestion must cite a specific file:line reference.
- Preserve all exported symbols, function signatures, and public interfaces.
- Do not introduce new abstractions for one-time use.
- Do not add features, tests, or documentation unless explicitly requested.
- If unsure whether a change preserves behavior, do not suggest it.
- Clarity over brevity — explicit code is often better than compact code.

## When to use

Use this skill when:

- Implementation is complete and all reviews passed, but the code could be cleaner.
- Complexity or duplication was introduced to meet a deadline.
- You want a focused cleanup pass before `spec-close`.

This is an **optional step** between the last review (qa-review or specialized review) and `spec-close`.

## Simplification checklist

**Complexity**
- Functions over 30-40 lines that could be split without losing clarity.
- Deeply nested conditions (more than 3 levels) that could be flattened with early returns or extraction.
- Complex boolean expressions that could be extracted to named variables.

**Duplication**
- Logic copied in 2+ places that could share a helper (only if the helper would be used 3+ times — avoid premature abstraction).
- Repeated conditionals with the same pattern.

**Naming**
- Variable or function names that do not describe their purpose.
- Abbreviations that are not obvious in context.

**Unnecessary complexity**
- Abstractions that exist for a single use case.
- Over-engineered patterns where simpler code would do.
- Dead code or commented-out blocks.
- Nested ternaries — prefer `if/else` or `switch` for multiple conditions.

## Output format

# Refactor Review

## Summary

1-2 sentences on overall code quality and whether refactoring is needed.

## Suggestions

For each suggestion:
- Location: `file.ts:line`
- Issue: what makes it hard to read or maintain
- Suggestion: concrete change
- Risk: None | Low — describe any behavioral caution

## Skipped files

List files where no improvement was found.

## Recommended next command

Logic:
- If suggestions exist and user wants to apply them: apply changes, verify with tests, then re-run `/refactor-review <path>`
- If no suggestions or changes applied: `/spec-close <path>`

## Context economy

- Review only the active feature diff and files it touches.
- Do not scan unrelated files.
- Do not suggest changes outside the scope of the current feature.
- Keep output short and concrete.
- Do not list sections where no issues were found.

## Concise review output

- Report only meaningful simplification opportunities.
- Do not suggest changes that reduce clarity in the name of brevity.
- Always end with the next recommended command.
