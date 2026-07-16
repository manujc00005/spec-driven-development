# Decisions: graphify-scan-nudge

## Decision log

### D001 - Nudge, never block; throttle instead of inspecting input

**Date:** 2026-07-17

**Status:** Accepted

**Context:** Enforcement options for graph-first: block broad scans (exit 2),
inspect tool_input for "breadth", or unconditional throttled reminder.

**Decision:** Unconditional `systemMessage` nudge when a graph exists, at most
once per 30 minutes (marker mtime), `SDD_GRAPHIFY_NUDGE=0` opt-out. No blocking,
no input inspection.

**Reasoning:** Targeted greps are legitimate under graph-first doctrine — any
blocking or breadth heuristic produces false positives that erode trust in the
whole hook system. A reminder at the moment of temptation closes most of the
adherence gap (feature 010 D006 consequence) at near-zero cost.

**Consequences:** Doctrine reinforcement is probabilistic, not guaranteed —
accepted; the guarantee ceiling for LLM behavior is raised, not reached.
