---
name: spec-status
description: Show a status overview of all specs (no path), or a deep-dive of a single feature (with path). Replaces spec-resume — use /spec-status <path> to resume work on a feature.
---

You are working in Spec-Driven Development mode.

## Mode detection

- **No path provided** → Overview mode: scan all specs and produce a summary table.
- **Path provided** (e.g. `specs/features/001-product-listing`) → Deep-dive mode: read all SDD files for that feature and produce a resume summary.

---

## Overview mode

Your task is to generate a status overview of all feature specifications in this project.

## Core rules

- Do not modify any files.
- Scan all folders under `specs/features/`.
- For each feature folder, read `SPEC.md` and `TASKS.md`.
- If a file does not exist, note it as missing.
- Count tasks: total, completed (checked `[x]`), and pending (unchecked `[ ]`).
- Extract the `Status` field from `SPEC.md`.
- Sort features by folder number (ascending).

## Output format

Print a summary table followed by per-feature details.

---

# Spec Status

**Date:** <today's date>

## Overview

| # | Feature | Status | Tasks Done | Tasks Left | Blockers |
|---|---------|--------|-----------|-----------|----------|
| 000 | feature-name | Draft / Ready / In Progress / Done | X | Y | None / List |

## Details

For each feature, print:

### <folder-number> — <feature-name>

- **Status:** Draft | Ready | In Progress | Done | Archived
- **Spec:** exists | missing
- **Plan:** exists | missing
- **Tasks:** X done / Y total
- **Next task:** T00X — description (or "All tasks complete" or "No tasks file")
- **Open questions:** list from SPEC.md, or "None"
- **Blockers:** any missing files, unresolved open questions, or tasks marked [NEEDS REVIEW]

---

## Summary

- Total specs: N
- Draft: N
- Ready: N
- In Progress: N
- Done: N
- Archived: N
- Specs with blockers: N

## Recommended actions

List any specs that need attention (e.g. Draft specs with no plan, In Progress specs with blocked tasks, specs with open questions).

---

## Deep-dive mode

When a path is provided, read `SPEC.md`, `TASKS.md`, and `DECISIONS.md` for that feature and produce:

# Feature Resume: <feature-name>

## Status

Current status field from SPEC.md.

## Task progress

X / Y tasks complete. List completed tasks briefly, then list pending tasks with their descriptions.

## Next task

T00X — description. Covers: AC-XXX.

## Recent decisions

Last 2-3 entries from DECISIONS.md (title and decision only — no full context).

## Open questions

List from SPEC.md `Open questions` section. Note which are blocking.

## Recommended next command

Logic (same as spec-resume):
- Status is `Draft` → `/spec-plan <path>`
- Status is `Ready` → `/spec-analyze <path>`
- Status is `In Progress` and tasks remain → `/spec-implement <path>`
- Status is `In Progress` and all tasks done → `/spec-review <path>`
- Status is `In Review` → `/qa-review <path>`
- Status is `Done` → `/spec-close <path>`

---

## Context economy

- Overview mode: read only `SPEC.md` and `TASKS.md` per feature.
- Deep-dive mode: read `SPEC.md`, `TASKS.md`, and `DECISIONS.md` for the target feature only.
- Do not paste full file contents.
- Keep output short and actionable.
- If more than 10 specs in overview mode, focus details on In Progress and blocked specs.
