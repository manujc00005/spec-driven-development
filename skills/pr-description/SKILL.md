---
name: pr-description
description: Generate a clear pull request description from the current git diff and related specs.
---

## SDD Contract

```yaml
category: lifecycle
inputs: [git-diff, SPEC.md?]
outputs: [PR_DESCRIPTION.md]
side_effects: writes-specs
writes_code: false
writes_specs: true
analysis_only: false
primary_agent: final-conformance-reviewer
secondary_agents: []
profile_scope: all
provider_specific: false
```

You are creating a pull request description.

## Core rules

- Inspect the current git diff.
- If a related spec exists under `specs/features/`, read `SPEC.md`, `PLAN.md`, `TASKS.md`, and `DECISIONS.md`.
- Do not modify files.
- Be concise and specific.
- List every acceptance criterion and whether it is covered.
- Include decisions made during implementation.
- Mention tests run and their results.
- Mention risks and follow-ups.

## Output format

# Pull Request Description

## Summary

One or two sentences describing what this PR does and why.

## Related spec

Path to the spec folder, e.g. `specs/features/000-feature-name/`.

Spec status at time of PR: Draft | Ready | In Progress | Done

## Acceptance criteria coverage

List each AC from the spec and its coverage status:

- AC-001: [description] — Covered | Not covered | Partially covered
- AC-002: [description] — Covered | Not covered | Partially covered

## Changes

Bullet list of concrete changes made (files, components, APIs, migrations, etc.).

## Decisions made

List decisions recorded in `DECISIONS.md` during this implementation. If none, write "None".

## Tests

- Tests added or updated:
- Tests run:
- Test results:
- Manual testing done:

## Risks

List known risks, edge cases not covered, or things that might break.

## Follow-up work

List open questions, deferred tasks, or future spec candidates.

## Checklist

- [ ] Implementation matches all acceptance criteria in the spec
- [ ] No behavior outside the spec was introduced
- [ ] Tests were added or updated for changed behavior
- [ ] All decisions are documented in DECISIONS.md
- [ ] SPEC.md status is up to date
- [ ] Security-sensitive behavior was reviewed (if applicable)
- [ ] Database changes were reviewed (if applicable)
- [ ] Performance-sensitive paths were reviewed (if applicable)
- [ ] No unrelated files were changed

## Context economy

- Read only the files needed for the current task.
- Prefer the active feature folder over scanning the whole repository.
- Do not inspect unrelated specs.
- Do not inspect archived specs unless explicitly asked.
- Do not paste full file contents unless explicitly requested.
- Keep the response short and actionable.
- Always suggest the next command when useful.
