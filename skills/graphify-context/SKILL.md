---
name: graphify-context
description: Interpret GRAPH_REPORT.md for impact analysis before planning or reviewing. Detects staleness. Degrades gracefully when Graphify is not installed. Never a source of truth — always an accelerator. Not for building a reading list when no graph exists — that is /context-manager.
triggers:
  - Before `/spec-plan` on medium/large features
  - Before `/spec-analyze`
  - Before `/architect-review`
  - When the user asks for "impact analysis" or "what does this change affect"
  - During `/sdd-onboard` (initial architecture discovery)
---

## SDD Contract

```yaml
category: context-research
inputs: [GRAPH_REPORT.md]
outputs: [impact-analysis, staleness-flag]
side_effects: none
writes_code: false
writes_specs: false
analysis_only: true
primary_agent: codebase-researcher
secondary_agents: [solution-architect]
profile_scope: all
provider_specific: false
```

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

**Graph-first doctrine (token saving):** derive the impact set from the graph BEFORE any
repo-wide Glob/Grep/Read sweep. Heuristic scanning is the fallback, never the default.

### The graph access ladder

Climb only as far as the question requires. **Reading `GRAPH_REPORT.md` in full is rung 4 — the
exception, not the starting point.** The scoped commands read `graph.json` inside the CLI process
and return a bounded answer, so the model never pays for the file.

Measured on a 1.650-node graph (`graph.json` 3,2 MB), CLI 0.17.1, 2026-08-06:

| Rung | Command | ~tokens |
|---|---|---|
| 1. Orientation | `graphify summary` | **354** |
| 2. Per-file impact | `graphify review-context <file>` · `review-analysis <file>` · `affected-flows <file>` | **103–1.057** |
| 3. Targeted traversal | `graphify tree <node>` · `path <a> <b>` · `explain <node>` | small, bounded |
| 4. **Exception** — full report | read `.graphify/GRAPH_REPORT.md` | **7.101** |
| 5. Never | load `.graphify/graph.json` | 859.376 |

Rung 4 is correct for genuinely global questions (god nodes, community structure) and whenever
the CLI is unavailable. It is wrong as a default: orientation via `summary` is **20× cheaper**.

**Three standing conditions:**

- **CLI absent → the report becomes rung 1.** The ladder degrades; it never blocks. Graphify
  remains optional.
- **No Bash tool → request the command.** An agent that cannot execute (the read-only lifecycle
  agents) names the exact command it needs and hands back — it does not silently fall through to
  the report.
- **Freshness is checked before any rung.** A query against a stale graph is cheap *and wrong*.

### When a graph exists

1. **Check freshness first:**
   - Compare the report's mtime against the most recently modified source file, and the commit it
     was built from (`Built from Git commit:` in the report) against `git rev-parse HEAD`.
   - If the graph is older than the newest source by more than 7 days, or sits many commits behind
     HEAD, mark it **stale** and warn.
   - If stale: still use it for broad orientation, but flag that fine-grained edges may be outdated.
     Refreshing costs no tokens — `graphify update` is local AST extraction, no LLM.
2. **Climb the ladder:** `summary` for orientation, then per-file queries for the files the spec
   names, then targeted traversal. Escalate to the full report only when a query cannot answer the
   question — and say why when you do.
3. **Cross-reference with ARCHITECTURE.md:**
   - Check if impacted modules cross a declared boundary (e.g., bounded context, service).
   - If they do, flag it: "This change crosses a service boundary — review communication pattern."
4. **Output:**
   - Impact summary (which modules, which directions, which boundaries crossed).
   - Recommended reading list (feed into `context-manager`).
   - Staleness warning if applicable.
   - Which rung answered the question — so the next session knows what was enough.

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
