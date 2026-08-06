# Token economy — *Context is a budget*

Usage-based (per-token) pricing is replacing seat-based pricing for AI coding
tools. Under that model, the cost of a change is driven by how much context an
agent reads and which model tier it burns — not by how many people are on a
plan. An agent that loads the whole repository into a long context window on an
expensive model is slow, costly, and harder to review than one that reads a
bounded, justified slice.

SDD treats **context as an engineering budget**. Instead of loading the entire
repository, agents work from specs, bounded reading lists, context providers,
graph-derived impact, and targeted review evidence — and they justify expensive
model/tool usage. This keeps AI-assisted delivery cheaper, faster, and more
reviewable.

This document is the canonical statement of the principle. It does not restate
the rules in full elsewhere — other files cross-reference it.

## The rules and where they live

Each rule of the principle is already implemented by a mechanism in this repo.
This table is the index; the linked file is the source of truth for that rule.

| Rule | Mechanism | Source of truth |
|------|-----------|-----------------|
| Spend the expensive model only on reasoning; use cheap models for mechanics | Cost-aware multi-model routing (spec 004) | [`skills/sdd-orchestrate/SKILL.md`](../skills/sdd-orchestrate/SKILL.md) |
| Read a bounded, justified slice — never the whole repo by default | Bounded reading list | [`skills/context-manager/SKILL.md`](../skills/context-manager/SKILL.md), [`agents/codebase-researcher.md`](../agents/codebase-researcher.md) |
| Derive impact from the graph before any repo-wide sweep | Graph-first impact analysis | [`skills/graphify-context/SKILL.md`](../skills/graphify-context/SKILL.md) |
| Query the graph; read the whole report only as an exception | The **graph access ladder** — `graphify summary` → per-file queries (`review-context`, `review-analysis`, `affected-flows`) → targeted traversal → full `GRAPH_REPORT.md` → never `graph.json`. Measured 2026-08-06: orientation via `summary` costs ~354 tokens against ~7.101 for the report on the same graph, because the scoped commands resolve the graph file inside the CLI process and it never enters context | [`skills/graphify-context/SKILL.md`](../skills/graphify-context/SKILL.md) |
| Prefer summaries over pasted file contents; read only the active feature | Output discipline | [`CLAUDE.md.example`](../CLAUDE.md.example) (`## Token economy`) |
| Declare the reading list and model tier before implementing | `## Context budget` PLAN section, verified by `/spec-analyze` | [`specs/_templates/PLAN.md`](../specs/_templates/PLAN.md), [`skills/spec-analyze/SKILL.md`](../skills/spec-analyze/SKILL.md) |

## How it is enforced

The only hard enforcement is the last row: every `PLAN.md` carries a
`## Context budget` section (a bounded reading list plus a per-phase model
routing note), and `/spec-analyze` checks it. A missing section is a **warning**
so plans authored before adoption still pass; an **empty or placeholder**
section is a **blocker**. A valid budget can be a single line — brevity is fine,
emptiness is not.

The other rules are conventions carried by the skills, agents, and CLAUDE.md
guidance above, applied by the agent as it works.

## What this is *not*

- **No telemetry.** SDD does not measure, log, or account for token usage. The
  budget is a design discipline, not a meter.
- **No hard gate beyond the PLAN check.** Template-to-skill sync and legacy-plan
  coverage are manual review items, not CI-enforced (a future spec may add them).
- **Not a substitute for the code.** Graph and reading lists bound *what to
  read*; the code remains the source of truth.

## Related

- Design principles and the seat→usage positioning: [`README.md`](../README.md)
- Per-project inheritance: the `## Token economy` section of
  [`specs/_templates/CONSTITUTION.md`](../specs/_templates/CONSTITUTION.md),
  carried into generated constitutions by `/project-init`.
