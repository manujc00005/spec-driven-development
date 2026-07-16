# Feature Spec: graphify-scan-nudge

## Status

Done

## Problem

The graph-first doctrine (feature 010, D006) is prose: skills instruct Claude to
derive context from the graph before broad scans, but nothing reinforces it at
the moment of temptation — when Claude actually fires a repo-wide Grep/Glob in a
project whose graph exists. Outside the SDD skill flow (ad-hoc requests), the
doctrine may never even be loaded.

## Goal

A `PreToolUse` hook on `Grep|Glob` that, when a Graphify report exists, emits a
one-line nudge reminding the session to prefer graph-first context. Throttled so
it never becomes noise. Never blocks — reinforcement, not enforcement.

## Non-goals

- Blocking or rejecting Grep/Glob calls (false positives — targeted greps are
  legitimate even under graph-first doctrine).
- Parsing the tool input to judge whether a specific scan is "broad" (heuristic
  too fragile; the nudge is cheap enough to be unconditional-but-throttled).
- Nudging when no graph exists (that is `graphify-stale-reminder`'s job).

## Functional requirements

- FR-001: New hook `graphify-scan-reminder.{sh,ps1}` on `PreToolUse` matcher
  `Grep|Glob`. If no Graphify report exists (`.graphify/GRAPH_REPORT.md`, legacy
  root fallback) → silent exit 0.
- FR-002: If the report exists → emit one `systemMessage` nudge pointing at
  graph-first usage (`/graphify-context`, `graphify review-context`,
  `affected-flows`), then stay silent for a TTL of 30 minutes (marker file
  `.graphify/.scan-nudge`, mtime-based).
- FR-003: Opt-out via `SDD_GRAPHIFY_NUDGE=0`. Exit 0 always; never blocks; never
  modifies files other than the marker.
- FR-004: Wired in both settings templates (`PreToolUse`, matcher `Grep|Glob`),
  listed in `profiles.json` core profile, documented in `hooks/README.md`
  (table row + behavior bullet). README count markers updated via
  `check-consistency.sh --fix`.

## Edge cases

- Marker unreadable/deleted mid-check (race) → treated as absent, nudge fires.
- Report at legacy root only → nudge still fires; marker still lives under
  `.graphify/` (created if needed).
- Stdin JSON is consumed and ignored (matcher already filters the tool).

## Acceptance criteria

- AC-001: No report → no output, exit 0. Report present → nudge emitted, exit 0.
- AC-002: Second invocation within TTL → silent; after TTL expiry → nudges again.
- AC-003: `SDD_GRAPHIFY_NUDGE=0` → silent even with report present.
- AC-004: Both templates wire it on `PreToolUse` `Grep|Glob`; `profiles.json`
  core lists it; `check-consistency.sh` passes (incl. README counts).

## Test scenarios

- Unit: extend `scripts/graphify.test.sh` (sandbox pattern) for AC-001..003.
- Integration: harness + `wire-hooks.sh --dry-run` for AC-004.

## Assumptions

- `systemMessage` (repo-wide hook convention) is the right channel — same bet as
  every other nudge hook in this repo.
- Unconditional-but-throttled beats input inspection: one line per 30 min is
  cheaper than false-positive analysis of scan "breadth".

## Open questions

- None.
