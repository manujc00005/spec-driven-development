---
name: sdd-status
description: SDD status of the whole workspace — every open spec across all projects, grouped by state, with its blocker and progress. Regenerates BOARD.md before listing, so it never shows stale data. Use it when opening a session, before starting a new spec, or to see what is blocked and why.
---

## What it does

```bash
node .sdd-workspace/scripts/board.mjs --list
```

The script walks `*/specs/features/*/` across every project, regenerates
`.sdd-workspace/BOARD.md`, and prints what is open — grouped by state, with each spec's
`Blocked-by`. Deterministic, no model call: same tree, same output.

## How to present the result

Paste the output as is — it is already formatted. Add **at most two sentences** on top, and only
if they say something the table doesn't:

- **What the real active work is** — the `real WIP` on the first line: `In Progress` specs
  **without** a blocker. If it is 0, say so: everything open is waiting on someone.
- **One warning, if any.** Warnings are findings, not noise: a closed spec with open tasks, or a
  `Merged` one that should already be `Live`.

Do not restate the table in prose, do not summarize spec by spec, do not propose a plan unless
asked.

## What it does NOT do

- **It never modifies a spec.** It only reads, and regenerates `BOARD.md`.
- It does not replace `/spec-status`, which deep-dives one feature inside one repo. This is the
  photo of every project at once.
- If a spec is missing from the board, its `## Status` header is not parseable — the fix goes in
  the spec, never in `BOARD.md`.
