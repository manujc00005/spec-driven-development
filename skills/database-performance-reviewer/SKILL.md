---
name: database-performance-reviewer
description: Review the cost of database access — index coverage, query plans, full scans, cardinality assumptions, N+1 access patterns, pagination, lock and transaction duration, batch size, and the write cost of adding an index. Not for whether the query returns the right rows, that is /sql-query-reviewer.
triggers:
  - When a query is added or changed on a table large enough for cost to matter
  - When an index, materialized view or batch size changes
  - When a query runs inside a loop, or a transaction wraps a long operation
  - When the user asks "why is this slow?" or "should I add an index here?"
---

## SDD Contract

```yaml
category: domain-reviewer
inputs: [diff, sql-sources, schema-context, query-plans]
outputs: [database-performance-findings]
side_effects: none
writes_code: false
writes_specs: false
analysis_only: true
primary_agent: domain-reviewer
secondary_agents: []
profile_scope: [python-sql-data]
provider_specific: false
```

# Database Performance Reviewer

## Purpose

Review what a query costs, and what it costs *everyone else while it runs*.

Two different failures live here. One is a slow query. The other is a query that is fast on the
developer's 500-row copy and takes a lock on a table that a hundred other sessions need — and only
the second one takes the system down.

## Extends

`performance-review` (generic). Runs **after** `sql-query-reviewer`: a wrong query does not deserve
an index.

## The honest limit of a static review

This skill reads SQL, schema and code. **It does not have a query plan, table statistics, or row
counts** unless the diff, the spec or the user supplies them.

That means every cost finding is one of two kinds, and they must be labelled differently:

- **Structural** — true from the text alone: a query inside a loop, an unbounded result set, a
  filter on a column no index covers, a transaction that spans a network call.
- **Conditional** — depends on data volume and distribution: whether a scan is cheaper than an
  index lookup, whether a join order is right, whether a plan will change at scale.

State conditional findings as **"run `EXPLAIN` and check X"**, never as "this will be slow".
A reviewer who asserts a plan they have not seen is guessing with authority.

## What this skill checks

### N+1 and query-in-a-loop

**The most common and most expensive finding in script-driven data work.**

- A query executed once per row of a previous result — including the version hidden behind a
  helper function, a list comprehension, or an ORM lazy attribute touched inside a loop.
- Per-row `INSERT`/`UPDATE` where the driver supports `executemany` or a set-based statement.
- A per-row lookup that a single join or a preloaded dict would replace.
- Ask for the loop's expected iteration count. `for row in rows:` around a query is 3 queries in
  the test and 300.000 in production.

### Result set size

- A query with no `LIMIT` whose result is loaded fully into memory.
- `SELECT *` pulling wide columns — blobs, JSON documents, long text — that nothing reads.
- A full table read into a DataFrame to filter in Python what the database could filter.
- Fetching everything to count it.

### Pagination

- `OFFSET n` on a large offset: the engine still walks the skipped rows, so page 5.000 costs
  5.000 pages of work.
- Pagination without a total-stable `ORDER BY` — rows shift between pages, so a paged export
  silently skips and repeats records.
- Keyset pagination (`WHERE id > :last_id ORDER BY id LIMIT n`) as the alternative when the access
  pattern allows it.

### Index coverage

- For each filter, join and sort column: is there an index that can serve it? Name the index, or
  say none exists.
- Leading-column rule on composite indexes — an index on `(a, b)` does not serve a filter on `b`
  alone.
- A function or a cast applied to an indexed column in the predicate, which disables the index
  unless the engine supports an expression index and one exists.
- A leading wildcard `LIKE '%…'`.
- Low-selectivity columns indexed alone (a boolean, a status with three values) — the index may
  never be chosen.

### The cost of adding an index

An index is not free, and this half of the trade is what review usually skips.

- Every index is paid on every `INSERT`, `UPDATE` and `DELETE` on that table, forever.
- Is the new index redundant with an existing one (a prefix of a composite that already exists)?
- Index count on a write-heavy table.
- How the index will be created: an index build that locks writes on a large table is a deploy
  event, not a migration detail. Say whether a concurrent/online build is available and whether the
  change uses it.
- Disk and memory footprint on a table where that matters.

### Cardinality and volume assumptions

- What row count does this query assume? Ask when the diff does not say.
- A join whose intermediate result is far larger than either input.
- Growth: does the cost stay linear as the table grows, or does it turn quadratic?
- A query correct today because the table has 10.000 rows, with nothing that keeps it correct at
  10 million.

### Locks and transactions

- Transaction scope: does it hold across an HTTP call, a file read, a `sleep`, or user input?
  Everything inside a transaction is lock duration.
- A long-running `UPDATE`/`DELETE` over a whole table where chunking would bound each lock.
- Explicit `SELECT … FOR UPDATE` — the row order it locks in, and whether two processes can take
  the same locks in different orders (deadlock).
- Isolation level, when the code sets one, and what it changes.
- Autocommit assumptions: is the connection in autocommit, and does the code know?
- DDL inside a transaction with data changes.

### Batch size

- Is there one? An unbounded `executemany` is a single enormous transaction.
- Batch size chosen deliberately versus copied from somewhere. State the trade: bigger batches
  amortize round trips, smaller batches bound lock time, memory and redo work.
- Commit frequency, and whether a mid-batch failure leaves a defined state — hand the re-run
  question to `data-pipeline-reviewer`.

### Materialized views, caching and precomputation

Only when the project already uses them, or the query is expensive enough to raise the question.

- A materialized view's refresh cost and staleness window — and whether any consumer assumes it is
  live.
- Whether a refresh blocks readers.
- Precomputed aggregate tables, and what keeps them consistent with the source.
- Do not propose a materialized view as a default fix. It converts a performance problem into a
  freshness-and-consistency problem, which is a design decision the project must make explicitly.

### Connections

- A connection opened per call in a loop rather than pooled or reused.
- Pool size versus expected concurrency.
- Connections leaked on the error path (no context manager, no `finally`).

## What this skill does NOT do

- **Does not replace `EXPLAIN` / `EXPLAIN ANALYZE`.** It tells you where to run it. It cannot
  produce or predict a plan.
- **Does not replace database monitoring, slow-query logs, or profiling.** No static review knows
  what your production workload is doing.
- **Does not perform automated tuning**, and does not claim an index will make a query fast.
- Does not benchmark, execute queries, or connect to a database.
- Does not review query correctness (that is `sql-query-reviewer`).
- Does not review schema design, constraints or migration safety in general — that is
  `database-review`.
- Does not modify code, schema or indexes.

## Output format

```markdown
## Database Performance Review — <query, script or migration>

**Verdict:** PASS | PASS WITH NOTES | FAIL

**Volume assumptions:** <row counts used, and whether they were supplied or assumed>

### Findings

| # | Severity | Kind (structural/conditional) | File:Line | Finding | Action |
|---|---|---|---|---|---|

### Index coverage

| Predicate / join / sort | Covering index | Verdict |
|---|---|---|

### Run EXPLAIN on

- (The specific queries whose cost cannot be settled statically, and what to look for in the plan)

### Lock and transaction footprint

- (What is held, for how long, and who else needs it)
```

## Context economy

- Read the query, the schema of the tables it touches, and the existing indexes on those tables.
- Do not read unrelated migrations or the whole schema history.
- Label every finding structural or conditional. Do not pad the report with conditional guesses.
- Always end with the next recommended command.
