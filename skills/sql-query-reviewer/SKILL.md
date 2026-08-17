---
name: sql-query-reviewer
description: Review SQL queries for correctness before performance — join fan-out and duplicate rows, NULL semantics, GROUP BY/HAVING, window functions, CTEs, subqueries, and parameterization versus string interpolation. Not for query plans, indexes or cost, that is /database-performance-reviewer.
triggers:
  - When a `.sql` file or an embedded SQL string changes
  - When a query is added to a report, extract, dashboard or script
  - When a join, filter or aggregation changes on a query someone trusts
  - When the user asks "can this duplicate rows?" or "is this query safe to run with user input?"
---

## SDD Contract

```yaml
category: domain-reviewer
inputs: [diff, sql-sources, schema-context]
outputs: [sql-findings]
side_effects: none
writes_code: false
writes_specs: false
analysis_only: true
primary_agent: domain-reviewer
secondary_agents: [security-reviewer]
profile_scope: [python-sql-data]
provider_specific: false
```

# SQL Query Reviewer

## Purpose

Answer one question before any other: **does this query return the right rows?**

A slow query is a visible problem. A query that silently returns 1.043 rows where 1.000 exist — or
drops the 37 rows whose `status` is `NULL` — produces a number somebody puts in a report, and
nothing about it looks wrong.

## Extends

Nothing generic. Runs before `database-performance-reviewer`: there is no point tuning a query
that returns the wrong answer. Feeds `security-reviewer` on anything injection-shaped.

## Scope of "SQL"

Relational SQL, reviewed generically. Where a check depends on engine behaviour (NULL ordering,
`GROUP BY` strictness, upsert syntax, window frame defaults), **say which engine you assumed and
that it is an assumption** — do not silently apply one vendor's rules. If the diff or the project
context does not state the engine, ask before ruling on engine-specific semantics.

## What this skill checks

### Duplicate rows and join fan-out

**This is the finding most often missed, and it inflates totals rather than breaking anything.**

- Does every join hit the other side on a unique key, or can it match many rows? A join to a
  one-to-many table multiplies the driving row — and any `SUM` downstream is now wrong.
- `SUM`/`COUNT` computed *after* a fan-out join. `COUNT(DISTINCT …)` used as a patch over a join
  that should have been an aggregate subquery.
- `DISTINCT` used to suppress duplicates whose cause was never diagnosed. Treat every `DISTINCT` as
  a question: what produced the duplicates?
- `UNION ALL` where `UNION` was meant, and `UNION` where `UNION ALL` was meant (the second silently
  pays for a dedup nobody asked for).

### NULL semantics

- `NOT IN (subquery)` where the subquery can yield `NULL` — the whole predicate returns no rows.
- Comparisons with `= NULL` / `!= NULL` instead of `IS NULL` / `IS NOT NULL`.
- `<>` filters that silently exclude `NULL` rows. `status <> 'CANCELLED'` drops rows with no
  status; whether that is intended is a decision, not a detail.
- Arithmetic and string concatenation with a nullable column propagating `NULL` through to output.
- `COUNT(col)` versus `COUNT(*)` — the first skips `NULL`s.
- Aggregates over an empty set returning `NULL` where the caller expects `0`.

### Outer joins that are not

- A `LEFT JOIN` whose right-side column appears in the `WHERE` clause — that is an inner join
  written the long way. Predicates on the outer side belong in `ON`.
- `LEFT JOIN` on a table that is then aggregated, producing `NULL` where `0` was meant.

### Filters and time ranges

- Half-open versus closed date ranges. `BETWEEN '2026-01-01' AND '2026-01-31'` on a timestamp
  column drops most of the last day.
- A function applied to a filtered column (`DATE(created_at) = …`, `UPPER(email) = …`). Correctness
  is usually fine; note it and hand the index consequence to `database-performance-reviewer`.
- Timezone: is the column stored with a zone, and is the literal in the same one? An off-by-hours
  boundary is the classic silent reporting bug.
- Implicit type coercion in a comparison (string to number, string to date).

### GROUP BY, HAVING, and aggregation

- Every non-aggregated select column present in `GROUP BY` — permissive engines will not tell you.
- `HAVING` used for a row-level predicate that belongs in `WHERE` (correct result, unnecessary
  work) and `WHERE` used where a post-aggregate predicate was meant (wrong result).
- Grouping by a nullable column, so all `NULL`s collapse into one bucket.
- Grouping by a display label rather than the key it stands for.

### Window functions, CTEs, subqueries

- Window frame left implicit. The default is `RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`,
  which on ties includes peer rows — rarely what a running total intends.
- `ROW_NUMBER()` deduplication with a non-deterministic `ORDER BY`: ties break differently between
  runs, so "the latest row per key" is not stable.
- `PARTITION BY` that does not match the grain the result claims to have.
- Correlated subqueries in the select list that could be a join — correctness fine, cost noted and
  handed over.
- A CTE referenced several times where the engine may or may not materialize it — flag the
  assumption, do not assert the behaviour.
- CTE chains long enough that no reader can state the grain of the final result. Ask the author to
  state it; if they cannot, that is the finding.

### Readability that affects correctness

- Unqualified column names in a multi-table query — one upstream column addition changes which
  table a bare name resolves to.
- `SELECT *` in anything a program consumes: column order and count become an implicit contract.
- Aliases that lie (`o` for `order_items`), and duplicate aliases across a subquery boundary.
- No comment stating what the query is *for*, on a query that takes ten lines to explain.

### Injection and parameterization

Hand every finding here to `security-reviewer` as well.

- String interpolation of any value into SQL: f-strings, `%`, `.format()`, `+`, template engines.
  A parameter placeholder is the fix, and there is no acceptable exception for "it is internal".
- Table, column and schema names cannot be parameterized — if they are dynamic, is there an
  allow-list, or does user input reach the identifier?
- `ORDER BY <user input>` and dynamic `LIMIT`/`OFFSET`.
- Client-side quoting or escaping written by hand instead of driver parameters.
- Query strings assembled across several functions, where the injection point is far from the
  execution point.
- Whether the account running the query has more rights than the query needs.

## What this skill does NOT do

- **Does not replace `sqlfluff` or any SQL linter.** Formatting, keyword case and layout are a
  tool's job.
- **Does not replace `EXPLAIN`.** It cannot tell you what a planner will do. Index and plan
  questions belong to `database-performance-reviewer`.
- Does not assume one database engine. Engine-specific rulings are stated as assumptions.
- Does not review the Python around the query (that is `python-reviewer`) or the re-run safety of
  the process the query belongs to (that is `data-pipeline-reviewer`).
- Does not connect to a database, run the query, or read data.
- Does not review schema design, migrations or constraints — that is `database-review`.
- Does not modify code.

## Output format

```markdown
## SQL Query Review — <query or file>

**Verdict:** PASS | PASS WITH NOTES | FAIL

**Engine assumed:** <engine, or "not stated — engine-specific checks deferred">

**Grain of the result:** <one row per what>

### Findings

| # | Severity | File:Line | Finding | Wrong-result risk | Action |
|---|---|---|---|---|---|

### Can this duplicate or drop rows?

- (Named joins that can fan out; named filters that exclude NULLs)

### Parameterization

- (Every value that reaches SQL, and whether it is a parameter — handed to security-reviewer)
```

## Context economy

- Read the query and the schema of the tables it touches. Do not read the whole schema.
- Do not read the surrounding application code beyond how the query string is built and executed.
- Report wrong-result risk first, readability second.
- Always end with the next recommended command.
