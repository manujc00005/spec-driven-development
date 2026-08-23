# How to work in this workspace

Practical guide to the workspace SDD system. If you read one section, read the first.

*(Generated from a template by `/sdd-workspace-init` — adapt freely; this file is yours, not the
tool's. Sections marked `[fill in]` need workspace-specific content.)*

---

## 1. Start here: three files, in this order

Wherever the session opens — root or inside a project — these three answer *"what am I doing and
why?"* without reading anything else:

| # | File | Answers |
|---|---|---|
| 1 | `.sdd-workspace/BOARD.md` | What is active, what is blocked and why. **Generated** |
| 2 | The spec the board marks `In Progress` | The goal, criteria and tasks |
| 3 | That spec's `CEREBRO.md`, if present | Verified `file:line` anchors to resume without rereading |

## 2. The rule that orders everything

**State is generated; rules are written.** If a script can compute it by reading files, nobody
types it.

| What you need | Where | Hand-edited? |
|---|---|---|
| Which specs exist, in which state | `.sdd-workspace/BOARD.md` | **No.** Regenerate |
| What's pending that isn't code | `.sdd-workspace/BACKLOG.md` | Yes — person-actions only |
| A repo's code debt | that repo's `BACKLOG.md` | Yes |
| Binding cross-project decisions | `SHARED_DECISIONS.md` | Yes |
| Cross-project contracts | `INTEGRATION_CONTRACTS.md` | Yes — **never version numbers**: point to the owning data file |
| Who depends on whom | `DEPENDENCY_GRAPH.md` | Yes, with evidence and confidence |

## 3. Day to day

**Starting work:** check the board (`node .sdd-workspace/scripts/board.mjs --list`). If something
is `In Progress` without a blocker, finish it or declare the blocker. The limit is **one**,
measured over unblocked actives — blocked ones wait on someone, they don't compete.

**When something appears mid-change**, classify before touching:

| Class | Criterion | Action |
|---|---|---|
| `BLOCKER` | The current acceptance criterion **cannot** be met without it | Stop. Create the child spec. Set `Blocked-by:` |
| `REQUIRED` | An AC demands it and it's inside the declared files | Do it now |
| `OPTIONAL` | Improves the result; no AC asks for it | `[~]` → the repo's `BACKLOG.md`, dated |
| `FOLLOW-UP` | Real work with its own scope | New spec in `Draft`, **unauthorized**. Zero code |

**A discovered dependency is never implemented inside the change that discovered it** — not even
a two-liner. That exception is where every A→B→C→D chain starts.

**Closing:** `Merged` = code in main, gates green, **zero unchecked tasks**. `Live` = behavior
verified in production, with date and pasted evidence. A spec with one open task is neither.

## 4. Working across projects

One decision, one order.

**The decision** — *does it move a shared contract, or does cross-repo order matter?*

```
NO  →  SIBLING SPECS (the ~90% case)
       One spec per repo, local numbering, linked with  Blocked-by: <repo>/spec#NNN
       No workspace spec. No ceremony.

YES →  PARENT SPEC in .sdd-workspace/specs/features/NNN-slug/
       SPEC.md (the problem BETWEEN projects) + IMPACT_MAP.md
       Children in each repo carry  Parent: workspace/NNN
       The parent NEVER contains code tasks
```

**The order:** contract owner first, always — the contract is documented before any consumer
implements. One repo at a time, to `Merged`, then the next. Atomic commits per repo: don't
simulate an atomicity git doesn't give you across repositories. The parent closes when every
child is `Live`, not `Merged`.

**A repo appears that wasn't in the map?** Stop condition: extend the `IMPACT_MAP`, get it
approved, continue. Never "while I'm here".

**Which workspace doc to update:** state — never (generated). Contracts — only if they change,
and BEFORE implementing. Narrative (the *why*) — only on architecture decisions or
root-caused bugs. If your feature touches neither, there is nothing to update: the workspace
learns by reading the specs.

## 5. The scripts

```bash
node .sdd-workspace/scripts/board.mjs            # regenerate board (SessionStart hook runs this)
node .sdd-workspace/scripts/board.mjs --list     # what /sdd-status runs
node .sdd-workspace/scripts/board.mjs --check    # exit 1 on real warnings — for CI
node .sdd-workspace/scripts/drift.mjs            # do documents contradict the code?
node .sdd-workspace/scripts/link-workspace.mjs   # (re)link child projects to this layer
```

If the board says something false, don't edit it — the defect is in the source spec or the
script. The control question for any file: *did a person write this, or did a script compute it?*
The former can lie and must be checked against the code. The latter only lies if its source does.

## 6. Bounded context

Never read a whole project. Never load a raw `graph.json`. Ladder: workspace docs → `graphify
summary` per project → scoped graph queries → `GRAPH_REPORT.md` → manifests/README → the
`IMPACT_MAP`'s reading list → only the implementation files on that list. `graphify update` costs
no tokens (local AST) — refresh before a serious session instead of reasoning over a stale graph.

## 7. [fill in] Workspace specifics

Production layout, domains, runbooks, the contracts this workspace actually has, and where its
narrative documentation lives.
