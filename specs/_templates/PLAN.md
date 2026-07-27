<!-- Extracted from skills/spec-plan/SKILL.md — kept in sync with that skill's template. -->

# Implementation Plan: <feature-name>

## Summary

Brief summary of what will be implemented.

## Related spec

Path to the related `SPEC.md`.

## Impacted areas

List modules, folders, services, components, entities, APIs, jobs, tests, or config likely to change.

## Context budget

Declare the bounded context this plan needs. Keep it tight — this is the token economy contract: read a justified slice, not the whole repository.

### Reading list

Files, folders, or globs the implementer may read for this feature. Prefer the active feature folder and the specific impacted files over whole-repo scans.

### Model routing

Which phases need a deep-reasoning model vs. a cheap/mechanical one. Justify any expensive model or tool usage.

## Proposed approach

Describe the implementation approach.

## Alternatives considered

Describe alternatives and why they were rejected.

## Dependencies

List external services, libraries, data, infrastructure, or team dependencies.

## Risks

List technical, product, security, performance, or delivery risks.

## Test strategy

Describe unit, integration, E2E, manual, and regression testing.

## Rollback strategy

Describe how to revert or disable the change if needed.

## PLAN verification checklist

- [ ] The plan covers all acceptance criteria.
- [ ] The plan avoids behavior outside the spec.
- [ ] The Context budget section is filled (reading list + model routing), not left as placeholder.
- [ ] Risks are documented.
- [ ] Test strategy is documented.
- [ ] Rollback strategy is documented.
- [ ] SPEC.md status has been updated to `Ready`.
