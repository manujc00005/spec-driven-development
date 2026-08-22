---
name: spec-review
description: Review current code changes against the active specification, plan, tasks, and decision log. Not for behaviour and regression review (use /qa-review) or for running every applicable review at once (use /review-all).
---

## SDD Contract

```yaml
category: lifecycle
inputs: [git-diff, SPEC.md, PLAN.md, TASKS.md, DECISIONS.md]
outputs: [review-findings]
side_effects: none
writes_code: false
writes_specs: false
analysis_only: true
primary_agent: final-conformance-reviewer
secondary_agents: [solution-architect]
profile_scope: all
provider_specific: false
```

You are working in Spec-Driven Development mode.

Your task is to review the current implementation against the related SDD files.

## Active feature context

If no path is provided, use the most recently referenced feature path from the current conversation. If none found, ask the user.

## Core rules

- Do not modify code unless explicitly requested.
- Read the relevant `SPEC.md`, `PLAN.md`, `TASKS.md`, and `DECISIONS.md`.
- Inspect the current git diff.
- Check whether the implementation matches the acceptance criteria.
- Identify behavior outside the spec.
- Identify missing tests.
- Identify risky abstractions, unnecessary changes, and unclear decisions.
- Be direct and specific.
- If the verdict is **Pass**, update `Status` in `SPEC.md` to `In Review`.
- **This skill is the only authorized performer of `In Progress` → `In Review`.** A spec marked `In Review` by any other means is an unverified claim, and it silently defeats `/spec-close`'s precondition check. See `sdd-guardrails` section 11.
- **`Ready` is accepted only under a recorded exception.** Some features are legitimately executed outside `/spec-implement` — a calibration spec whose own decision routes the work to the maintainer's session, for example — so `/spec-implement` never runs and the spec stays at `Ready` with the work done. In that case, and only when the feature's `DECISIONS.md` contains an **Accepted** decision explaining why `/spec-implement` was bypassed, this skill may perform `Ready` → `In Review` on a **Pass**. It must name that decision in its output. Without such a decision, `Ready` is refused: tell the user to run `/spec-implement`. A `Proposed` decision does not qualify. The citation is the point — an exception nobody has to justify in writing is the silent status edit section 11 exists to prevent.
- If the verdict is **Partial** or **Fail**, do not change the status.

## Review checklist

Check:

- Does the implementation satisfy every acceptance criterion?
- Are all completed tasks actually implemented?
- Is there behavior not described in the spec?
- Are edge cases handled?
- Are tests sufficient?
- Are naming and architecture consistent with the project?
- Were unrelated files changed?
- Were decisions documented?
- Is rollback still possible?

## Output format

# Spec Review

## Verdict

Pass | Partial | Fail

## Matches spec

List what correctly matches the spec.

## Deviations from spec

List behavior or changes outside the spec.

## Missing requirements

List acceptance criteria or requirements not fully covered.

## Missing or weak tests

List test gaps.

## Risky changes

List risky implementation details.

## Unrelated changes

List unrelated files or changes.

## Recommended next actions

Give concrete next steps to fix any issues found.

## Recommended next command

Logic:
- If verdict is **Fail** or **Partial**: fix issues, then re-run `/spec-review <path>`
- If verdict is **Pass**: always → `/qa-review <path>`

## Context economy

- Read only the files needed for the current task.
- Prefer the active feature folder over scanning the whole repository.
- Do not inspect unrelated specs.
- Do not inspect archived specs unless explicitly asked.
- Do not paste full file contents unless explicitly requested.
- Keep the response short and actionable.
- Always suggest the next command when useful.

## Concise review output

- Report only meaningful findings.
- Do not list empty sections unless required by the output format.
- Do not repeat requirements that are already satisfied.
- Prioritize confirmed issues over theoretical risks.
- Keep recommendations concrete.
- Always end with the next recommended command.
