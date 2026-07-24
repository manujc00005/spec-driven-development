---
name: spec-resume
description: Alias for /spec-status <path>. Resume work on a feature after a break — kept for backwards compatibility.
---

## SDD Contract

```yaml
category: lifecycle
inputs: [specs/features/<path>]
outputs: [status-overview]
side_effects: none
writes_code: false
writes_specs: false
analysis_only: true
primary_agent: any
secondary_agents: []
profile_scope: all
provider_specific: false
```

> This skill has been unified with `/spec-status`.
> `/spec-resume <path>` is equivalent to `/spec-status <path>`.
> Prefer `/spec-status <path>` going forward.

You are working in Spec-Driven Development mode.

Your task is to help the user resume work on an existing feature after a break.

## Core rules

- Do not implement production code.
- Do not modify any files.
- Be concise. The goal is a fast re-entry, not a full review.
- Highlight what is actionable, not what is historical.

## Resume process

1. Read `TASKS.md` first — enough for progress and next task.
2. Read `SPEC.md` only if status or open questions are needed.
3. Read `DECISIONS.md` only if there are blocked tasks or the user asks.
4. Read `PLAN.md` only if the next task is unclear from `TASKS.md` alone.
5. Identify the next unchecked task.
6. Flag any tasks marked `[NEEDS REVIEW]`.
7. Recommend the exact next command to run.

## Context economy

- Read `TASKS.md` first. This is enough for progress and next task in most cases.
- Read `SPEC.md` only if status or open questions are needed.
- Read `DECISIONS.md` only if there are blocked tasks or the user explicitly asks.
- Read `PLAN.md` only if the next task is unclear from `TASKS.md` alone.
- Do not paste full file contents.
- Default output: progress + next task + next command. Expand only when there are blockers.

## Output format

# Spec Resume: <feature-name>

## Status

Current spec status: Draft | Ready | In Progress | Done | Archived

## Progress

- Tasks completed: X / Y
- Tasks remaining: Z

## Next task

T00X — description (Covers: AC-XXX)

## Recent decisions

List the last 2-3 decisions from DECISIONS.md with their status.

## Open questions

List any unresolved open questions from SPEC.md. If none, write "None".

## Blocked tasks

List any tasks marked [NEEDS REVIEW] or with unresolved dependencies. If none, write "None".

## Recommended next command
