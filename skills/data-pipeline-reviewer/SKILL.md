---
name: data-pipeline-reviewer
description: Review data loads and ETL-style processes for re-run safety — idempotency, duplicate rows, partial failure, retries, incremental watermarks, timezone-explicit timestamps, file format contracts, traceability and reconciliation. Not for the SQL itself, that is /sql-query-reviewer.
triggers:
  - When a load, extract, sync, import/export or scheduled job changes
  - When a process writes to a table it did not write to before
  - When retries, incremental loads or watermarks are added or changed
  - When the user asks "what happens if this runs twice?" or "can I safely re-run yesterday?"
---

## SDD Contract

```yaml
category: domain-reviewer
inputs: [diff, pipeline-sources, schema-context]
outputs: [data-pipeline-findings]
side_effects: none
writes_code: false
writes_specs: false
analysis_only: true
primary_agent: domain-reviewer
secondary_agents: [security-reviewer]
profile_scope: [python-sql-data]
provider_specific: false
```

# Data Pipeline Reviewer

## Purpose

Review a data process against the only question that matters at 3 a.m.: **what happens when it
fails halfway, and can I just run it again?**

Everything else in this skill is a variation on that question.

## Extends

Nothing generic. Runs alongside `sql-query-reviewer` (the statements), `python-reviewer` (the code
around them) and `database-performance-reviewer` (their cost). Hands sensitive-data findings to
`security-reviewer`.

## Scope

Any process that moves or derives data on a schedule or on demand: an ETL job, a nightly load, a
report extract, a sync between two systems, a one-off backfill script that will inevitably be run
more than once. Not tied to any orchestration tool — a `cron` line calling a Python script is in
scope exactly as much as a DAG is.

## What this skill checks

### Idempotency

**This is the finding that decides whether the process is operable.**

- Run the process twice on the same input. Does the output change? Name the mechanism that makes
  it not change — a natural key, a unique constraint, a merge/upsert on a defined key, a
  delete-then-insert of a bounded partition — or state that there is none.
- Plain `INSERT` into a table with no unique constraint: a re-run doubles the rows, and nothing
  errors.
- "Delete everything, then insert" — idempotent, but there is a window where the table is empty.
  Is it in a transaction? Do readers see the gap?
- Upserts whose conflict key does not match the true business key.
- A destination that accumulates across runs (append-only) presented as though it were replaced.
- Non-idempotent side effects that a re-run repeats: emails sent, files pushed, downstream jobs
  triggered, counters incremented, API calls that create.

### Partial failure

- If the process dies at row 500 of 1000, what is the state? Half-loaded, all-or-nothing, or
  unknown?
- Transaction boundaries versus batch boundaries — a commit per batch means partial success is a
  designed state, and someone must be able to resume from it.
- Is there a marker that says how far it got, or does resumption depend on a human reading the
  destination table?
- Does the process report failure to the caller — non-zero exit, alert, failed job status — or
  does it log and exit 0?
- Cleanup of temporary and staging artifacts on the error path.

### Retries

- What is retried, and is that operation safe to repeat? A retry on a non-idempotent write is a
  duplicate generator.
- Is the retry bounded, and does it back off? An immediate infinite retry against a struggling
  database is an outage amplifier.
- Which errors are retried: a timeout deserves a retry, a constraint violation or a parse error
  does not.
- What happens after the last retry — does the record go somewhere a human can find it, or is it
  dropped?

### Duplicates

- Constraint-level protection: is there a unique index on the business key, or does deduplication
  depend entirely on the code being correct?
- Deduplication logic that picks "the latest" row with a non-deterministic tiebreak.
- The same input file processed twice — is there any record of which files have been consumed?
- Duplicates arriving from the source, and whether the process is supposed to collapse them or
  preserve them.

### Incremental loads and watermarks

- What defines "new since last run"? A timestamp column, an id, a batch marker, a file name.
- **Late-arriving and updated rows.** A watermark on `updated_at` misses rows written with an
  earlier timestamp after the watermark moved — the classic silent gap.
- Watermark stored where, and updated when? Advancing it *before* the load succeeds loses data on
  failure. Advancing it after can reprocess a window, which is only safe if the load is idempotent.
- Boundary handling: `>` versus `>=` at the watermark decides between skipping and reprocessing
  one row. Both are defensible; being undecided is not.
- Clock source. If the watermark comes from the process's clock rather than the data's, clock skew
  between machines creates gaps.
- Is a full reload possible, and does anything depend on it never happening?

### Timestamps and timezones

- Is every timestamp column and literal explicit about its zone? Naive datetimes crossing a system
  boundary are a bug waiting for a DST change.
- `datetime.now()` versus `datetime.now(timezone.utc)`.
- Mixed zones: source in local time, destination in UTC, report in a third.
- Daylight-saving transitions on a daily job that partitions by local date — one day has 23 hours
  and one has 25.
- "Today" computed at the start of the run versus at the moment each row is written.

### Input and output contracts

- What does this process promise its consumers about shape, grain and freshness? Is that written
  anywhere?
- Schema drift from the source: a new column, a renamed column, a type change. Does the process
  fail, ignore it, or silently produce wrong output?
- Column order dependence when reading a headerless file or using `SELECT *`.
- Consumers of the output that would break on a change made here.

### File formats

Only where the process touches files.

- **CSV:** encoding, delimiter, quoting, embedded newlines, header presence, and how a numeric-
  looking id keeps its leading zeros. CSV has no types — every one is inferred by whoever reads it.
- **JSON / JSONL:** whole-document parse versus line-by-line, and what a single malformed line does.
- **Parquet / columnar:** schema evolution between files, and type mismatch across partitions.
- Partial file writes: is the output written directly to its final name, so a crash leaves a
  truncated file that looks complete? Write-then-rename is the fix.
- File-name-based date logic and timezone of the naming convention.

### Validation

- Where is input validated — at the boundary, halfway through, or never?
- Row-level rules (nulls in required fields, ranges, referential existence, type conformance).
- Batch-level rules: expected row count, an unexpected drop to zero rows, a volume swing that
  should stop the load rather than publish it.
- What happens to a row that fails validation: rejected to a quarantine table, logged, or silently
  skipped? A silent skip is the finding.
- Whether validation failures can fail the run, or only ever warn.

### Traceability

- Can you take a row in the destination and say which run produced it? A batch id, a load
  timestamp, a source file name on the row or in a run log.
- Is there a run log at all — start, end, rows in, rows out, rows rejected, outcome?
- Are run records kept long enough to investigate a problem noticed a week later?

### Reconciliation

- Is there any check that source and destination agree — counts, sums of a control column, a
  checksum on a key set?
- Does the check run automatically, and can it fail the run?
- Who looks at the result, and what do they do when it disagrees?

### Sensitive data

Hand all of these to `security-reviewer`.

- Personal data copied into staging tables, temp files, logs or error messages, and whether those
  are cleaned up.
- Credentials for source and destination systems: where they come from, and whether any is a
  literal in source or a command line argument visible in the process list.
- Extracts written to a shared path or emailed.
- Whether the process's account has broader rights than the load needs.
- Retention: does anything delete the intermediate copies this process creates?

## What this skill does NOT do

- Does not review the SQL statements themselves (that is `sql-query-reviewer`) or their cost (that
  is `database-performance-reviewer`).
- Does not review general Python structure (that is `python-reviewer`) or the tests (that is
  `python-testing-reviewer`).
- **Does not cover data engineering as a discipline.** No orchestration design, scheduling
  topology, data modelling, warehouse architecture, lineage tooling, cost governance, or streaming
  semantics. This is a review of the process in the diff, against operability questions.
- Does not run the process, read production data, or connect to any system.
- Does not configure or provision anything.
- Does not modify code.

## Output format

```markdown
## Data Pipeline Review — <process>

**Verdict:** PASS | PASS WITH NOTES | FAIL

### Re-run safety

- **Run it twice:** <what changes, and the mechanism that prevents it>
- **Kill it halfway:** <resulting state, and how to resume>
- **Replay yesterday:** <safe / not safe, and why>

### Findings

| # | Severity | File:Line | Finding | Action |
|---|---|---|---|---|

### Contracts

| Input/Output | Shape & grain | Freshness | What breaks on drift |
|---|---|---|---|

### Evidence a run leaves behind

- (Batch id, run log, rejected rows, reconciliation result — or the absence of each)

### Handed to security-reviewer

- (Personal data copies, credential handling, extract destinations, retention)
```

## Context economy

- Read the process entry point and the modules it calls. Do not walk the whole repository.
- Read the destination table's constraints — they are the difference between designed and
  accidental idempotency.
- Lead with re-run safety. Everything else is secondary.
- Always end with the next recommended command.
