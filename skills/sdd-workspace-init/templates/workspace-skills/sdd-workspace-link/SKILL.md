---
name: sdd-workspace-link
description: Links child projects to the workspace governance layer. Inserts into each repo's instruction file the block declaring which workspace it belongs to, what to read before proposing anything, and the cross-repo rules. Idempotent. Use it after adding a new repository to the workspace, or if a session inside a repo doesn't seem to see .sdd-workspace/.
---

## What it does

```bash
node .sdd-workspace/scripts/link-workspace.mjs
```

Writes — or refreshes — a block delimited by `<!-- SDD-WORKSPACE:START/END -->` at the top of each
project's instruction file (`CLAUDE.md`, or `specs/CLAUDE-SDD.md`, or `AGENTS.md`, or `README.md` —
first that exists). The block states which workspace the repo belongs to, the four files to read
before proposing anything, and the three cross-repo rules.

**Idempotent**: if the block exists, it is replaced in place. Never duplicated.

`--check` writes nothing and exits 1 if any project is unlinked. The SessionStart hook uses it to
warn.

## Why it exists

Workspace onboarding builds `.sdd-workspace/` but writes nothing inside child projects — a
governance layer only visible from the root, while most sessions open inside a repo. A session
inside a child would otherwise never see the board, the shared decisions or the contracts.

## Rules

- The block text is edited **in the script**, never in the repos.
- Which repos participate is a decision, not an inference: prefer listing them in
  `.sdd-workspace/workspace.json` over relying on auto-detection.
- It touches nothing outside its own delimiters.
