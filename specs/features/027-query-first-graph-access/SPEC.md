# Feature Spec: Query-first graph access

## Status

Ready

## Problem

Every Graphify-aware artifact in this repo tells the reader to open
`.graphify/GRAPH_REPORT.md` first, and mentions the CLI's scoped queries as an optional
optimisation afterwards — a subordinate clause, not the rule:

- `skills/graphify-context/SKILL.md` step 2: extract the impacted subgraph from the report, then
  *"If the `graphify` CLI is on PATH, prefer its read-only queries over manual report parsing"*.
- `skills/context-manager/SKILL.md` step 1: **"Check for the Graphify report first"**, with queries
  named inside the sub-bullet.
- `agents/codebase-researcher.md` step 1: *"Check for a graph report first"*.
- `docs/TOKEN_ECONOMY.md` states the rule as *"Derive impact from the graph before any repo-wide
  sweep"* — silent on which graph access path.

That ordering was written before anyone measured the two paths. Measured on
`lead-platform` (1.650 nodes, 5.242 edges, `graph.json` = 3,2 MB) on 2026-08-06:

| Access path | Output | ~tokens into context |
|---|---|---|
| `graphify summary` | 1.419 B | **354** |
| `graphify review-analysis <file>` | 890–1.050 B | **222–262** |
| `graphify review-context <file>` | 415–4.228 B | **103–1.057** |
| Read `GRAPH_REPORT.md` in full | 28.404 B | **7.101** |
| Load `graph.json` | 3.437.505 B | 859.376 |

**Orienting via `summary` is 20× cheaper than reading the report.** The scoped commands read
`graph.json` *inside the CLI process* and return a bounded answer; the model never sees the file.
The framework's own default is therefore the expensive path, and the cheap one is documented as a
footnote.

The cost compounds per project. Across the four-project workspace measured the same day
(`base-proyect`, `chat-widget`, `lead-platform`, `proycto-cumbre`), the reports total **18.269
tokens**; four `summary` calls total **~1.400**. That is ~17k tokens burned on orientation, on
every session, for information that a bounded query already answers.

This is not a Graphify bug and not a docs typo. It is the token-economy principle
(`docs/TOKEN_ECONOMY.md`, spec 026) not being applied to the mechanism that exists to serve it.

## Goal

Invert the documented order: **scoped CLI query first; read `GRAPH_REPORT.md` only when a query
cannot answer the question.** Make that ordering explicit and identical in every artifact that
states it, and record the measurement that justifies it so the ordering is evidence-backed rather
than asserted.

## Non-goals

- **No change to Graphify itself**, and no new dependency on it. It stays optional (spec 025 D006).
- **No new hard CI gate on *behaviour*.** Nothing can detect at runtime which path an agent chose.
  Enforcement is limited to asserting the doctrine text exists (see FR-007).
- **No change to the `graph.json` prohibition** — it stands unchanged (spec 025 D003).
- **No new skill, agent, hook, installer or profile change.**
- **No telemetry.** `docs/TOKEN_ECONOMY.md` explicitly refuses token metering; this feature records
  one-off measurements in a spec, not a meter.
- **Not a rewrite of the fallback path.** Graceful degradation when Graphify is absent is unchanged.

## Users / Actors

| Actor | Interest |
|---|---|
| **Any session with a Bash tool** | Gets the cheap path stated as the default instead of buried. |
| **`codebase-researcher`** | Has **no Bash tool by design** — it cannot run a query. It must request one from the orchestrating session. See FR-005; this is the constraint that shapes the whole feature. |
| **Workspace onboarding** | Orients across N projects for ~350 tokens each instead of ~4.500 average. |
| **Maintainer** | Stops paying ~17k tokens per workspace session for orientation. |

## Current behavior

Report-first everywhere; queries mentioned as an optional refinement in three of the four
artifacts and not at all in `docs/TOKEN_ECONOMY.md`. No artifact states what a query costs relative
to a report, so a reader has no basis for preferring one.

## Desired behavior

A single **graph access ladder**, stated identically in every artifact that mentions it:

1. `graphify summary` — orientation, ~350 tokens.
2. `graphify review-context <file>` / `review-analysis <file>` / `affected-flows <file>` — per-file
   impact, ~100–1.100 tokens.
3. `graphify tree <node>` / `path <a> <b>` / `explain <node>` — targeted traversal.
4. `GRAPH_REPORT.md` in full — **only** when the questions above are not answerable by a query, or
   when the CLI is unavailable. This is the exception.
5. `graph.json` — never.

With three standing conditions:

- **CLI absent → the report is the top rung.** The ladder degrades; it never blocks.
- **No Bash tool → request the query.** An agent without Bash names the exact command it needs and
  hands back, rather than silently falling through to the expensive rung.
- **Freshness is checked before either path.** A query against a stale graph is cheap *and wrong*;
  cheapness never justifies skipping the staleness check.

## Functional requirements

- **FR-001** — `skills/graphify-context/SKILL.md` states the ladder as its primary procedure, with
  report-reading demoted to the documented exception.
- **FR-002** — `skills/context-manager/SKILL.md` step 1 leads with the query path.
- **FR-003** — `skills/sdd-workspace-onboarding/SKILL.md` token rules lead with `graphify summary`
  per project, not the report.
- **FR-004** — `docs/WORKSPACE_SDD.md`'s token-saving ladder is updated to match, and carries the
  measured comparison so a reader can see why.
- **FR-005** — `agents/codebase-researcher.md` states the ladder **and** the no-Bash constraint:
  it must name the command it wants run rather than defaulting to the report.
- **FR-006** — `docs/TOKEN_ECONOMY.md`'s rule table names the graph access ladder and points at
  `skills/graphify-context/SKILL.md` as its source of truth.
- **FR-007** — `scripts/check-consistency.sh` asserts that each doctrine artifact mentions the
  scoped-query commands, so a future edit cannot silently revert to report-first.
- **FR-008** — `adapters/codex/prompts/sdd-workspace-onboarding.md` carries the same ladder.
- **FR-009** — The measurement that justifies the inversion is recorded in this SPEC with the
  project, graph size, date and command outputs, so the ordering can be re-checked rather than
  trusted.

## Non-functional requirements

- **NFR-001** — Skill form caps hold: description ≤ 400 chars, body ≤ 600 lines (spec 022).
- **NFR-002** — The ladder wording is identical across artifacts, so drift is visible.
- **NFR-003** — Nothing added here makes Graphify required, or blocks when it is absent.

## API / Interface changes

None. No command is added, removed or renamed.

## Data model changes

None.

## Edge cases

| # | Case | Handling |
|---|---|---|
| E1 | `graphify` CLI not on PATH | Report becomes rung 1. Ladder degrades, never blocks. |
| E2 | Agent has no Bash tool (`codebase-researcher` and the three read-only reviewers) | Name the command, hand back. Never fall through to the report as a silent default. |
| E3 | Graph is stale | Freshness check runs **before** the ladder. A cheap query on a stale graph is still wrong. |
| E4 | A query returns empty (`affected-flows` on a peripheral file returned 0 bytes when measured) | Empty is an answer — the file is in no flow. Do **not** escalate to the report to "check". |
| E5 | Question is genuinely global (e.g. "what are the god nodes?") | `summary` covers it; if not, the report is the correct rung 4 — that is what the exception is for. |
| E6 | `graph.json` exists, no report, no CLI | No graph access. Fall back to `Grep`/`Glob`. Never read the JSON. |

## Acceptance criteria

- **AC-001** — `skills/graphify-context/SKILL.md` leads with the query ladder; report-reading is
  stated as the exception with its condition.
- **AC-002** — `skills/context-manager/SKILL.md` leads with the query path in step 1.
- **AC-003** — `skills/sdd-workspace-onboarding/SKILL.md` token rules put `graphify summary` above
  per-project report reading.
- **AC-004** — `docs/WORKSPACE_SDD.md` carries the updated ladder **and** the measured table.
- **AC-005** — `agents/codebase-researcher.md` carries the ladder and the explicit no-Bash rule.
- **AC-006** — `docs/TOKEN_ECONOMY.md` names the ladder in its rule table.
- **AC-007** — `adapters/codex/prompts/sdd-workspace-onboarding.md` carries the same ladder.
- **AC-008** — `check-consistency.sh` fails if any doctrine artifact stops naming the scoped-query
  commands.
- **AC-009** — `check-consistency.test.sh` proves AC-008 fires when violated.
- **AC-010** — The measurement is recorded with project, date, graph size and per-command output.
- **AC-011** — Graphify remains optional; no artifact claims otherwise, and the existing
  `workspace-claim` guard still passes.
- **AC-012** — `check-consistency.sh` exit 0, `check-consistency.test.sh` 0 failures,
  `profiles.json` parses.

## Test scenarios

| # | Scenario | Expected |
|---|---|---|
| TS-1 | Clean tree | Checker exit 0 |
| TS-2 | Remove the scoped-query mention from `graphify-context/SKILL.md` | Exit 1, `[graph-ladder]` finding |
| TS-3 | Remove it from `agents/codebase-researcher.md` | Exit 1 |
| TS-4 | Full self-test suite | 0 failures |

## Assumptions

- **A1** — The measured ratios are representative for repos of this size (300–2.700 nodes). The
  spec records the method so a larger repo can be re-measured rather than assumed.
- **A2** — `graphify summary` exists in CLI 0.17.1 and is stable enough to name in doctrine. It was
  invoked successfully during measurement.
- **A3** — Sessions that run skills generally have a Bash tool; the six lifecycle agents mostly do
  not. FR-005 exists because of that split.

## Open questions

- **OQ-1** *(non-blocking)* — Should `check-consistency.sh` also assert the ladder's *order* (that
  `summary` appears before `GRAPH_REPORT.md` in the doctrine files) rather than just the presence of
  the commands? Presence is what ships; order-checking is brittle against prose.
- **OQ-2** *(non-blocking)* — The measurement is a point-in-time snapshot on one machine. Worth
  re-measuring when Graphify's output format changes.

## Contracted services

None.
