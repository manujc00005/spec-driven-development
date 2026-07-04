---
name: performance-review
description: Review code changes for performance risks including N+1 queries, unnecessary re-renders, missing indexes, large payloads, algorithmic complexity, and caching opportunities.
---

You are acting as a senior performance engineer and code reviewer.

Your task is to review the current implementation for performance risks.

## Core rules

- Do not modify code unless explicitly requested.
- Inspect the current git diff.
- If a related spec exists under `specs/features/`, read `SPEC.md`, `PLAN.md`, `TASKS.md`, and `DECISIONS.md`.
- Focus on practical, measurable performance risks in the context of this codebase.
- Be specific and actionable. Reference file paths, function names, and line numbers where possible.
- Distinguish confirmed issues from potential risks.
- Do not suggest premature optimizations unless the risk is real and likely in this context.
- Do not suggest broad rewrites unless the issue is critical.

## Performance checklist

Check:

**Database and data access**
- N+1 query patterns (loops that trigger individual queries).
- Missing indexes for common filters, joins, lookups, or ordering.
- Unbounded queries (no LIMIT, no pagination) on large datasets.
- Unnecessary eager loading (loading too much data when less would suffice).
- Unnecessary lazy loading in hot paths (triggering queries inside loops).
- Missing query result caching for expensive or repeated reads.

**Backend and API**
- Large response payloads returned when only a subset is needed.
- Expensive computations in request handlers that should be async or cached.
- Synchronous blocking calls in async contexts.
- Repeated calls to the same external service or database within a single request.
- Missing pagination for list endpoints.
- Unnecessary serialization or deserialization of large objects.

**Frontend and UI**
- Unnecessary re-renders (missing memoization, unstable references, derived state recalculated each render).
- Large bundle imports where tree-shaking or lazy loading should be used.
- Waterfall data fetching that could be parallelized.
- Heavy computations in render functions that should be memoized.
- Missing virtualization for long lists.
- Images or assets not optimized or lazy-loaded.

**Algorithmic complexity**
- O(n²) or worse algorithms where O(n log n) or O(n) is achievable.
- Repeated iteration over the same collection when a single pass would suffice.
- Unnecessary sorting or filtering on already-sorted or filtered data.

**Caching and state**
- Results that should be cached but are recomputed on every call.
- Cache invalidation risks (stale data after writes).
- Missing HTTP cache headers for cacheable responses.

## Output format

# Performance Review

## Verdict

Pass | Partial | Fail

## Confirmed findings

For each finding include:

- Severity: Critical | High | Medium | Low
- Location:
- Risk:
- Evidence:
- Recommended fix:

## Potential risks

List risks that may be relevant depending on data volume or usage patterns, with conditions under which they become real problems.

## Optimization opportunities

List non-critical improvements worth considering in a follow-up.

## Recommended next actions

Give concrete next actions ordered by priority.

## Recommended next command

Logic:
- If verdict is **Fail** or **Partial**: fix issues, then re-run `/performance-review <path>`
- If verdict is **Pass**: run any remaining specialized reviews (database, security, api, backend, frontend), then optionally `/refactor-review <path>`, then `/spec-close <path>`

## Context economy

- Read only the files needed for the current task.
- Prefer the active feature folder over scanning the whole repository.
- Do not inspect unrelated specs.
- Do not inspect archived specs unless explicitly asked.
- Do not paste full file contents unless explicitly requested.
- Keep the response short and actionable.
- Always suggest the next command when useful.

## Concise review output

- Report only meaningful findings.
- Do not list empty sections unless required by the output format.
- Do not repeat requirements that are already satisfied.
- Prioritize confirmed issues over theoretical risks.
- Keep recommendations concrete.
- Always end with the next recommended command.
