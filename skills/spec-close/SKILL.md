---
name: spec-close
description: Close a completed feature. Run after spec-review passes. Resolves open questions, generates an implementation summary, and prepares the feature for handoff.
---

## SDD Contract

```yaml
category: lifecycle
inputs: [SPEC.md, PLAN.md, TASKS.md, DECISIONS.md]
outputs: [closed-SPEC.md, implementation-summary]
side_effects: writes-specs
writes_code: false
writes_specs: true
analysis_only: false
primary_agent: final-conformance-reviewer
secondary_agents: []
profile_scope: all
provider_specific: false
```

You are working in Spec-Driven Development mode.

Your task is to close a completed feature specification after implementation is done and spec-review has passed.

## Active feature context

If no path is provided, use the most recently referenced feature path from the current conversation. If none found, ask the user.

## Core rules

- Do not implement production code.
- Read `SPEC.md`, `PLAN.md`, `TASKS.md`, and `DECISIONS.md`.
- Only run this skill after `/spec-review` has passed (status is `In Review`).
- If status is not `In Review`, stop and tell the user to run `/spec-review` first.
- Be concise. This is a closing ritual, not a full review.

## Close process

1. Read all four SDD files.
2. Verify SPEC.md status is `In Review`. If not, stop.
3. Update `Status` in `SPEC.md` to `Done`.
4. Compare acceptance criteria against completed tasks — confirm full coverage.
5. List any open questions and mark them as:
   - `Resolved` — if the implementation answered them.
   - `Deferred` — if they remain unanswered and should be tracked elsewhere.
6. Identify any behavior that was implemented but is not in the spec (surface it, do not remove it).
7. List any deferred tasks or follow-up items worth tracking.
8. Update `SPEC.md` open questions with their resolution status.
9. Generate a brief implementation summary.

## Output format

# Spec Close: <feature-name>

## Verdict

Closed | Blocked (reason)

## Acceptance criteria coverage

List each AC and whether it was fully covered.

- AC-001: Covered
- AC-002: Covered

## Open questions resolution

For each open question:

- Question: ...
  Status: Resolved | Deferred
  Note: ...

## Unspecified behavior found

List behavior implemented but not described in the spec. If none, write "None".

## Deferred items

List tasks, questions or follow-ups that should be tracked in a future spec. If none, write "None".

## Implementation summary

One or two sentences describing what was built and its scope.

## Recommended next command

`/pr-description`

## Context economy

- Read only the files needed for the current task.
- Prefer the active feature folder over scanning the whole repository.
- Do not inspect unrelated specs.
- Do not inspect archived specs unless explicitly asked.
- Do not paste full file contents unless explicitly requested.
- Keep the response short and actionable.
