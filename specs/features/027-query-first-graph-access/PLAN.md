# Plan: Query-first graph access

## Summary

Invert one ordering statement across six artifacts, add the measurement that justifies it, and add
a presence check so the inversion cannot be silently undone. No code, no new command, no new
dependency.

## Related spec

`specs/features/027-query-first-graph-access/SPEC.md`

## Context budget

Reading list for this change — every file that states the graph access order, and nothing else:

- `skills/graphify-context/SKILL.md` (doctrine owner)
- `skills/context-manager/SKILL.md` (step 1)
- `skills/sdd-workspace-onboarding/SKILL.md` (token rules)
- `agents/codebase-researcher.md` (step 1 + tool constraint)
- `docs/TOKEN_ECONOMY.md` (rule table)
- `docs/WORKSPACE_SDD.md` (ladder)
- `adapters/codex/prompts/sdd-workspace-onboarding.md` (ladder)
- `scripts/check-consistency.{sh,test.sh}` (guard)

Model routing: single tier. This is prose editing against a decided design — no phase warrants a
deeper model.

## Impacted areas

| Area | Change | Risk |
|---|---|---|
| `skills/graphify-context/SKILL.md` | Behavior section reordered | Medium — this is the doctrine other files defer to; wording must not imply Graphify is required |
| `skills/context-manager/SKILL.md` | Step 1 leads with query | Low |
| `skills/sdd-workspace-onboarding/SKILL.md` | Token rules ladder | Low — must stay under the 600-line cap |
| `agents/codebase-researcher.md` | Ladder + no-Bash rule | **Highest** — the agent has no Bash tool, so a naive "run `graphify summary` first" instruction would be unfollowable |
| `docs/TOKEN_ECONOMY.md` | One rule row | Low |
| `docs/WORKSPACE_SDD.md` | Ladder + measured table | Low |
| `adapters/codex/prompts/…` | Ladder | Low |
| `scripts/check-consistency.{sh,test.sh}` | `graph-ladder` presence check + 2 cases | Medium — a checker that over-matches blocks CI |

**Out of bounds:** `install*.{sh,ps1}`, `hooks/**`, `settings.template*.json`, `profiles.json`
(no new skill ships, so no manifest change is needed), every child project.

## Proposed approach

### 1. One ladder, written once, copied verbatim

The five rungs plus three standing conditions become a fixed block. Identical wording everywhere
means drift is visible on inspection, and the checker only has to assert presence of the command
names.

### 2. The no-Bash constraint is the design's sharp edge

`codebase-researcher` declares `tools: Read, Grep, Glob`. It **cannot** run `graphify summary`.
Writing "run the query first" into its contract would produce an instruction it must violate on
every invocation — worse than the report-first status quo, because it teaches the agent that its
own contract is advisory.

So its rule is different in kind: *name the exact command you want and hand back*. This mirrors the
behaviour it already has for graph generation ("do not attempt to invoke Graphify's CLI yourself;
you have no Bash tool, by design"). The ladder is stated for the tool-bearing session; the agent
gets the request protocol.

### 3. Measurement recorded in SPEC, not in `evals/`

`evals/` measures whether a skill changes model behaviour (spec 022). This is a cost measurement of
a CLI, which the eval harness cannot produce and does not model. It belongs in the SPEC as evidence
with its method stated, so it can be re-run rather than trusted.

`docs/TOKEN_ECONOMY.md` explicitly refuses telemetry; a one-off measurement recorded in a spec is
not a meter and does not contradict it.

### 4. Enforcement: presence, not order

The checker asserts each doctrine artifact names the scoped commands. It does **not** try to verify
that `summary` appears before `GRAPH_REPORT.md` — prose ordering is brittle to match and the
false-positive cost (blocked CI on correct text) exceeds the drift it would catch. Same trade-off
recorded in spec 025 D014's checker and spec 022 D006.

## Alternatives considered

| Alternative | Why rejected |
|---|---|
| **Leave the ordering, add a "tip" about queries** | That is exactly the status quo, and it is what produced a 20× cost gap that nobody noticed for four specs |
| **Make the query path mandatory** | Would make Graphify required by the back door, contradicting spec 025 D006 and the README's standing claim |
| **Teach `codebase-researcher` to run queries by granting it Bash** | Its read-only guarantee is structural (no Bash tool at all). Trading that for token savings is a bad exchange, and spec 018 made the isolation deliberate |
| **Enforce ordering in CI by regex** | Brittle against prose; blocks CI on correct text. Presence check only (OQ-1 keeps the door open) |
| **Put the measurement in `evals/results/`** | The harness measures behaviour change under a control arm, not CLI output size. A result file there would misrepresent what was measured |

## Dependencies

- Spec 010 — canonical `.graphify/GRAPH_REPORT.md` path. Unchanged; this feature reorders *access*,
  not location.
- Spec 018 — the agent tool grants that create the no-Bash constraint.
- Spec 025 — the `graph.json` prohibition and the workspace ladder this extends.
- Spec 026 — `docs/TOKEN_ECONOMY.md`, whose rule table gains the ladder.
- Graphify CLI 0.17.1 for the command names. Absence degrades, never blocks.

## Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| A reader concludes Graphify is now required | Medium | High — contradicts a standing README claim | Every ladder states "CLI absent → report is rung 1"; the existing `workspace-claim` guard still runs |
| `codebase-researcher` gets an unfollowable instruction | Medium | High | FR-005 gives it the request protocol instead of the command |
| Command names drift with a Graphify release | Low | Medium | Names verified against 0.17.1 and recorded with the version; OQ-2 tracks re-measurement |
| Checker over-matches and blocks CI | Low | Medium | Presence-only assertion on a short command list; TS-1 asserts the clean tree passes |

## Test strategy

1. `bash scripts/check-consistency.sh` → exit 0.
2. `bash scripts/check-consistency.test.sh` → 0 failures, including two new cases (TS-2, TS-3).
3. `python3 -m json.tool profiles.json` → exit 0.
4. Manual re-read of `agents/codebase-researcher.md` confirming no instruction requires a tool it
   does not have.

## Rollback strategy

Every change is prose in six files plus one checker block. Revert the commit; nothing is installed,
generated or migrated. No runtime state exists to unwind.

## PLAN verification checklist

- [x] Every FR maps to a task
- [x] The no-Bash constraint is treated as a design driver, not an afterthought
- [x] Enforcement scope justified (presence, not order) with the precedent it follows
- [x] Out-of-bounds files enumerated
- [x] Measurement location justified against the existing `evals/` contract
- [x] No commit/push/staging step appears in this plan
