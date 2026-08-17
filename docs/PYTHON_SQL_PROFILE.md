# Python SQL Data Profile

`python-sql-data` is an optional overlay profile. It ships five review skills and nothing else —
no hooks, no templates, no agents.

Install it alongside whatever stack profile the project already uses:

```bash
./install.sh --profile python-sql-data
```

```powershell
.\install.ps1 -Profile python-sql-data
```

Combine it explicitly when the repository has a second stack, e.g.
`--profile java-spring-backend,python-sql-data`.

## Purpose

For projects built out of Python and SQL rather than around a framework: internal scripts,
scheduled automation, reporting and extracts, data validation, and load processes against a
relational database.

The code this profile is aimed at usually has two properties. It started as something small, and
it is now trusted by someone who does not read it. That combination is where the expensive bugs
live — a query that quietly duplicates rows, a load that is not safe to re-run, a script that
exits 0 after failing.

## What it reviews

| Skill | Question it answers |
|---|---|
| [`python-reviewer`](../skills/python-reviewer/SKILL.md) | Is this script maintainable, and does it fail loudly? |
| [`sql-query-reviewer`](../skills/sql-query-reviewer/SKILL.md) | Does this query return the right rows? |
| [`database-performance-reviewer`](../skills/database-performance-reviewer/SKILL.md) | What does it cost, and what does it block while it runs? |
| [`data-pipeline-reviewer`](../skills/data-pipeline-reviewer/SKILL.md) | What happens if it fails halfway, or runs twice? |
| [`python-testing-reviewer`](../skills/python-testing-reviewer/SKILL.md) | Would these tests catch it if it broke? |

Security risk around data access is covered as a **secondary** concern: SQL injection and string
interpolation, credentials in source, personal data in logs and extracts, and over-privileged
database accounts are found by these skills and handed to `security-reviewer`, which owns them.

## Agent routing

No new agents. All five skills are primary-owned by the existing **`domain-reviewer`** agent, and
that is the single entry in the profile's `agentRouting`.

**`security-reviewer`** consumes `python-reviewer`, `sql-query-reviewer` and
`data-pipeline-reviewer` as a secondary agent, declared in each skill's `## SDD Contract`
(`secondary_agents`) rather than as a second routing target. In this framework an `agentRouting`
entry means *ownership*, so a skill appears under exactly one agent — the same convention
`payments-fintech` and `delivery-operations` already follow. See
[`AGENTIC_ROUTING.md`](AGENTIC_ROUTING.md) for the full model.

## What it does not replace

Every one of these remains the source of truth for what it measures. The skills point at them;
they do not stand in for them.

- **`ruff` / `flake8` / `black`** — lint and formatting. If the project has no linter, that is one
  finding, not a hand-written lint report.
- **`mypy` / `pyright`** — type checking. The reviewer reads annotations as intent; it does not
  infer types.
- **`pytest`** — a passing review is not a passing suite.
- **`coverage.py`** — the reviewer reasons about untested behaviour, not coverage percentages.
- **`sqlfluff`** — SQL linting and formatting.
- **`EXPLAIN` / `EXPLAIN ANALYZE`** — no static review can produce or predict a query plan.
- **Database monitoring and slow-query logs** — nothing here knows your production workload.
- **Human database review** — index, lock and migration decisions on a large table are operational
  decisions, and this profile's job is to make sure they get made deliberately, not to make them.

It is also **not data-engineering coverage**. There is no orchestration design, scheduling
topology, data modelling, warehouse architecture, lineage tooling, cost governance or streaming
semantics here. These are reviews of the Python, SQL and load logic that appear in a diff.

## Recommended workflow

1. Create the spec (`/spec-create`, then the usual SDD lifecycle).
2. Identify the affected scripts, queries and tables, and state the expected row volume — several
   findings are unanswerable without it.
3. Review Python structure — `/python-reviewer`.
4. Review SQL correctness — `/sql-query-reviewer`. Before cost, always: a wrong query does not
   deserve an index.
5. Review query performance — `/database-performance-reviewer`.
6. Review data validation and re-run safety — `/data-pipeline-reviewer`, when the change is part
   of a load, sync, extract or scheduled job.
7. Review tests — `/python-testing-reviewer`.
8. Produce evidence: `EXPLAIN` output for the queries flagged as conditional, a pytest run, and a
   re-run of the process against the same input where re-run safety was the question.

Steps 3–7 are also reachable in one pass through `/review-all`, which selects the applicable
reviewers from the spec.

## Example review questions

- Can this query duplicate rows?
- Are `NULL`s handled correctly, or does `NOT IN` quietly return nothing?
- Is the query parameterized, or is a value interpolated into the string?
- Does the script fail loudly, and what exit code does the scheduler see?
- Is the process idempotent — what changes if it runs twice?
- What state is left behind if it dies at row 500 of 1000?
- Are timezones explicit, on both the column and the literal?
- Does the watermark miss late-arriving rows?
- Which index covers this filter, and what does adding a new one cost on write?
- Are the tests deterministic, and would they fail if the code were wrong?
