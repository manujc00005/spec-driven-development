---
name: graphify-context
description: Interpret GRAPH_REPORT.md for impact analysis before planning or reviewing. Detects staleness. Degrades gracefully when Graphify is not installed. Never a source of truth — always an accelerator.
triggers:
  - Before `/spec-plan` on medium/large features
  - Before `/spec-analyze`
  - Before `/architect-review`
  - When the user asks for "impact analysis" or "what does this change affect"
  - During `/sdd-onboard` (initial architecture discovery)
---

# Graphify Context

## Purpose

Use an existing `GRAPH_REPORT.md` (produced by Graphify) to perform **impact analysis** — identifying
which modules, services, and files are affected by a planned change — without scanning the entire repo.

**Graphify is an accelerator, never a source of truth.** This skill reads and interprets the graph;
it does not replace reading the actual code, running tests, or applying engineering judgment.

## Prerequisites

- `GRAPH_REPORT.md` at project root (produced by an external Graphify run).
- If this file does not exist, the skill **degrades gracefully** (see below).

## Inputs

1. **Active spec** — what is changing (domains, endpoints, entities, events).
2. **GRAPH_REPORT.md** — module/dependency graph (if available).
3. **`docs/ARCHITECTURE.md`** — for cross-referencing boundaries (if available).

## Behavior

### When GRAPH_REPORT.md exists

1. **Check freshness:**
   - Compare `GRAPH_REPORT.md` mtime against the most recently modified source file.
   - If the graph is older than the newest source by more than 7 days, mark it **stale** and warn.
   - If stale: still use it for broad orientation, but flag that fine-grained edges may be outdated.
2. **Extract impacted subgraph:**
   - From the spec's declared changes, identify entry-point nodes in the graph.
   - Walk direct and transitive dependencies (max depth 3 unless the spec is cross-cutting).
   - Produce a focused list: impacted modules + their relationships.
3. **Cross-reference with ARCHITECTURE.md:**
   - Check if impacted modules cross a declared boundary (e.g., bounded context, service).
   - If they do, flag it: "This change crosses a service boundary — review communication pattern."
4. **Output:**
   - Impact summary (which modules, which directions, which boundaries crossed).
   - Recommended reading list (feed into `context-manager`).
   - Staleness warning if applicable.

### When GRAPH_REPORT.md does NOT exist (graceful degradation)

1. Print: `"GRAPH_REPORT.md not found. Graphify is not installed or has not been run. Falling back to heuristic impact analysis based on ARCHITECTURE.md and project structure."`
2. If `docs/ARCHITECTURE.md` exists, use its module map + dependency flow for coarse impact analysis.
3. If neither exists, report: `"No architecture map available. Impact analysis will require broader file scanning. Consider running Graphify or filling in docs/ARCHITECTURE.md."`
4. **Never fail. Never block. Always produce a best-effort answer.**

## Output format

```markdown
## Impact Analysis

**Source:** GRAPH_REPORT.md (fresh / stale — generated YYYY-MM-DD)
**Spec:** NNN-feature-name

### Impacted modules

| Module | Relationship | Impact type |
|---|---|---|
| `order-service` | Direct (entry point) | Code change |
| `payment-service` | Downstream consumer | Contract verification needed |
| `notification-service` | Event listener | Verify event schema |

### Boundary crossings

- order-service → payment-service (async: Kafka topic `orders.completed`)

### Recommended actions

- [ ] Read `order-service/src/.../OrderController.java` (entry point)
- [ ] Verify Kafka schema compatibility for `orders.completed`
- [ ] Run contract tests for payment-service consumer

### Staleness note

(If applicable: "Graph is N days stale. Re-run Graphify before finalizing the plan.")
```

## What this skill does NOT do

- Does not **run** Graphify (the user runs it externally).
- Does not **generate** GRAPH_REPORT.md.
- Does not replace reading files — it identifies *which* files matter.
- Does not block any workflow when absent.
- Is never the source of truth — the code is.
