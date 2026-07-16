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

- The Graphify report, resolved in this order:
  1. `.graphify/GRAPH_REPORT.md` (canonical — where the Graphify CLI writes it).
  2. `GRAPH_REPORT.md` at project root (legacy fallback). If both exist, `.graphify/` wins.
- If neither exists, the skill **degrades gracefully** (see below). The
  `graphify-stale-reminder` hook auto-refreshes the graph in the background when
  the CLI is installed, so a missing report may simply mean "wait a moment".

## Inputs

1. **Active spec** — what is changing (domains, endpoints, entities, events).
2. **Graphify report** — module/dependency graph (resolved as above, if available).
3. **`docs/ARCHITECTURE.md`** — for cross-referencing boundaries (if available).

## Behavior

**Graph-first doctrine (token saving):** when the report exists, derive the impact
set from the graph BEFORE any repo-wide Glob/Grep/Read sweep. Heuristic scanning
is the fallback, never the default.

### When the Graphify report exists

1. **Check freshness:**
   - Compare the report's mtime against the most recently modified source file.
   - If the graph is older than the newest source by more than 7 days, mark it **stale** and warn.
   - If stale: still use it for broad orientation, but flag that fine-grained edges may be outdated.
2. **Extract impacted subgraph:**
   - From the spec's declared changes, identify entry-point nodes in the graph.
   - Walk direct and transitive dependencies (max depth 3 unless the spec is cross-cutting).
   - Produce a focused list: impacted modules + their relationships.
   - If the `graphify` CLI is on PATH, prefer its read-only queries over manual
     report parsing — they are cheaper than loading the full report into context:
     - `graphify review-context <file>` — what to read before touching a file.
     - `graphify affected-flows <file>` — which flows a change ripples into.
     - `graphify tree <node>` / `graphify path <a> <b>` — dependency walks.
3. **Cross-reference with ARCHITECTURE.md:**
   - Check if impacted modules cross a declared boundary (e.g., bounded context, service).
   - If they do, flag it: "This change crosses a service boundary — review communication pattern."
4. **Output:**
   - Impact summary (which modules, which directions, which boundaries crossed).
   - Recommended reading list (feed into `context-manager`).
   - Staleness warning if applicable.

### When the Graphify report does NOT exist (graceful degradation)

1. Print: `"Graphify report not found (.graphify/GRAPH_REPORT.md or legacy root GRAPH_REPORT.md). Graphify is not installed or has not been run — scripts/setup-graphify.sh adopts it in one step. Falling back to heuristic impact analysis based on ARCHITECTURE.md and project structure."`
2. If `docs/ARCHITECTURE.md` exists, use its module map + dependency flow for coarse impact analysis.
3. If neither exists, report: `"No architecture map available. Impact analysis will require broader file scanning. Consider running Graphify or filling in docs/ARCHITECTURE.md."`
4. **Never fail. Never block. Always produce a best-effort answer.**

## Output format

```markdown
## Impact Analysis

**Source:** .graphify/GRAPH_REPORT.md (fresh / stale — generated YYYY-MM-DD)
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

- Does not **generate** the graph (`graphify detect`/`update` run externally: the
  user via `scripts/setup-graphify.sh`, or the stale-reminder hook in the
  background). Read-only queries (`tree`, `path`, `review-context`,
  `affected-flows`) are allowed.
- Does not replace reading files — it identifies *which* files matter.
- Does not block any workflow when absent.
- Is never the source of truth — the code is.
