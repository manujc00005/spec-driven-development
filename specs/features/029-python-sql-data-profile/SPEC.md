# Feature Spec: python-sql-data-profile

## Status

Ready

## Problem

The framework has strong profiles for Java/Spring, messaging/event-driven, Next.js/Prisma,
payments/fintech, SEO/GEO and delivery/operations. It has **no profile for the kind of work that
is mostly Python plus relational SQL**: internal scripts, scheduled automation, reporting
extracts, data validation, and load processes against a database.

Today a project like that installs `core` and gets the generic reviewers — `qa-review`,
`security-review`, `performance-review`, `database-review`. Those are real, but none of them asks
the questions that actually decide whether this kind of code is safe:

- Can this query duplicate rows, or silently drop the ones whose column is `NULL`?
- Is this value a bound parameter, or interpolated into the SQL string?
- What happens if this load runs twice, or dies at row 500 of 1000?
- Does this script exit 0 after failing?
- Would these tests fail if the code were wrong?

`database-review` is the closest fit and it is aimed at schema, migrations and constraints — not
at query correctness, not at query cost, and not at the operability of a scheduled process.

## Goal

An optional overlay profile `python-sql-data` that ships reusable review skills for Python code,
SQL correctness, database access cost, data-load re-run safety, and pytest quality — routed to the
existing `domain-reviewer` agent, with `security-reviewer` as secondary wherever data access
carries security risk.

## Non-goals

- **No new agent.** No Python agent, no SQL agent, no data agent. `domain-reviewer` owns these
  skills; `security-reviewer` consumes the security-adjacent ones as secondary.
- **No linter, no formatter, no analyzer.** Nothing here parses Python, typechecks, executes SQL,
  or produces a query plan.
- **No replacement of `ruff`, `mypy`, `pytest`, `coverage.py`, `sqlfluff`, `EXPLAIN` or database
  monitoring.** Each remains the source of truth for what it measures.
- **No database-engine assumption.** Reviews are engine-agnostic relational SQL; engine-specific
  behaviour is stated as an assumption, never asserted.
- **Not data-engineering coverage.** No orchestration design, scheduling topology, data modelling,
  warehouse architecture, lineage tooling, cost governance or streaming semantics. These are
  reviews of the code in a diff.
- **No downstream project changes.** Nothing outside this repository is touched.
- **No database configured, provisioned or connected to.**
- **No installer change** beyond the profile entry `install.sh`/`install.ps1` already read from
  `profiles.json`.
- **No Codex adapter port.** Recorded as an honest gap in `adapters/codex/PARITY.md`, matching how
  every other stack-specific reviewer family is handled.

## Users / Actors

- **Maintainer** working daily in a Python + SQL codebase, running the reviews on their own diffs.
- **`domain-reviewer` agent**, which loads these skills when the profile is active.
- **`security-reviewer` agent**, which receives injection, credential, personal-data and
  privilege findings handed over by three of the five skills.
- **Installer** (`install.sh` / `install.ps1`), which resolves the profile from `profiles.json`.
- **`check-consistency.sh`**, which must validate the new profile with no new checker logic.

## Current behavior

- `profiles.json` declares 8 profiles; none targets Python or SQL work.
- 66 skills on disk. `database-review` covers schema/migrations/constraints;
  `performance-review` is generic; `test-engineer` is strategy-level and stack-agnostic.
- A Python + SQL project gets `core` only, or `core` plus a profile for a stack it does not use.

## Desired behavior

- `profiles.json` declares a ninth profile, `python-sql-data`, shipping five review skills.
- Installing it makes `/python-reviewer`, `/sql-query-reviewer`,
  `/database-performance-reviewer`, `/data-pipeline-reviewer` and `/python-testing-reviewer`
  available, and routes all five to `domain-reviewer`.
- Each skill states, inside the skill, which tool it does not replace — so the boundary travels
  with the skill rather than living only in the profile documentation.
- `docs/PYTHON_SQL_PROFILE.md` explains purpose, coverage, non-replacement, workflow and example
  review questions.
- `check-consistency.sh` validates the profile through its existing generic rules and passes.

## Functional requirements

- FR-001: `profiles.json` declares a `python-sql-data` profile, `default: false`, not disabled,
  shipping exactly the five skills below and no hooks, templates or agents.
- FR-002: `skills/python-reviewer/SKILL.md` reviews typing, module structure, oversized functions,
  logic/IO/config separation, exception handling, silent errors, logging, `pathlib`, dataclasses,
  pydantic where the project already uses it, context managers, script maintainability, import-time
  side effects, configuration and unnecessary dependencies.
- FR-003: `skills/sql-query-reviewer/SKILL.md` reviews query correctness — joins and fan-out,
  filters, `NULL` handling, `GROUP BY`/`HAVING`, window functions, CTEs, subqueries, duplicate
  rows, wrong-result risk, readability, and SQL injection via string interpolation versus bound
  parameters.
- FR-004: `skills/database-performance-reviewer/SKILL.md` reviews indexes, `EXPLAIN`/query plans,
  full scans, cardinality assumptions, N+1 access, pagination, locks, long transactions, batch
  size, materialized views where applicable, query cost, and the write cost of a new index.
- FR-005: `skills/data-pipeline-reviewer/SKILL.md` reviews idempotency, data validation,
  duplicates, retries, timestamps and timezones, CSV/JSON/parquet contracts where applicable,
  incremental loads, partial failure, traceability, reconciliation, and input/output contracts.
- FR-006: `skills/python-testing-reviewer/SKILL.md` reviews pytest usage — fixtures, mocks,
  parametrization, testing scripts, testing queries, test data, edge cases, temporary files,
  `monkeypatch`, test isolation and determinism.
- FR-007: all five skills carry a valid `## SDD Contract` with `primary_agent: domain-reviewer`,
  `analysis_only: true`, `writes_code: false`, `writes_specs: false`, `side_effects: none`,
  `provider_specific: false`, `profile_scope: [python-sql-data]`.
- FR-008: `python-reviewer`, `sql-query-reviewer` and `data-pipeline-reviewer` declare
  `secondary_agents: [security-reviewer]`; `database-performance-reviewer` and
  `python-testing-reviewer` declare an empty list, because neither surfaces a security finding as
  a matter of course.
- FR-009: the profile declares `agentRouting` with `domain-reviewer` owning all five skills, and a
  `note` recording the secondary `security-reviewer` consumption.
- FR-010: every skill carries an explicit section naming the tools it does not replace.
- FR-011: `docs/PYTHON_SQL_PROFILE.md` exists and covers purpose, what it reviews, what it does not
  replace, recommended workflow, and example review questions.
- FR-012: `README.md` mentions the profile in the profile table, the profile total, and the current
  support table — briefly.
- FR-013: `CHANGELOG.md` documents the addition under `[Unreleased] / Added`.
- FR-014: `scripts/check-consistency.sh` passes with **no new checker logic**, because its existing
  generic rules already cover shipped-skill existence, routing-target validity, routed-skill
  existence, per-profile routing coverage, and SDD Contract validity.
- FR-015: no file under `agents/` is created or modified.

## Non-functional requirements

- **Performance:** none of these skills executes anything. Each declares a context-economy section
  bounding what it reads.
- **Security:** the three skills that can surface injection, credentials, personal data or
  over-privileged accounts must hand those findings to `security-reviewer` rather than ruling on
  them, and must say so in the output format.
- **Observability:** each skill emits a verdict and a findings table with `file:line` evidence.
- **Maintainability:** each `SKILL.md` stays under the 600-line cap and each `description` under
  the 400-char cap enforced by `check-consistency.sh`.
- **Honesty:** no skill may claim to replace a tool, guarantee performance, or describe the
  profile as data-engineering coverage. `database-performance-reviewer` must distinguish findings
  that are true from the text (structural) from findings that depend on data volume
  (conditional), because a static reviewer has no query plan.

## API / Interface changes

Five new slash commands: `/python-reviewer`, `/sql-query-reviewer`,
`/database-performance-reviewer`, `/data-pipeline-reviewer`, `/python-testing-reviewer`.

One new installable profile name accepted by `install.sh --profile` and `install.ps1 -Profile`.

No change to any existing command, agent or hook.

## Data model changes

None. `profiles.json` gains one profile object under the existing manifest schema (version
`0.4.0`, unchanged — no new key is introduced).

## Edge cases

- **A skill in two `agentRouting` targets.** The checker permits it mechanically (routed skills are
  collected into a set, with no uniqueness rule), but a routing entry means *ownership* in this
  framework, so dual-listing would assert two owners. Resolved in D002.
- **A project with no linter, no type checker and no tests.** `python-reviewer` reports the absence
  once as a finding; it must not hand-enumerate lint violations in place of the missing tool.
- **Engine-specific SQL semantics** (`NULL` ordering, `GROUP BY` strictness, CTE materialization,
  upsert syntax) where the diff never names the engine. Resolved in D003: state the assumption, or
  ask.
- **A cost question that cannot be settled statically.** Resolved in D004: label it conditional and
  name the `EXPLAIN` to run.
- **A one-off backfill script.** In scope for `data-pipeline-reviewer` — a script that "runs once"
  is run again in practice, and that is exactly when idempotency matters.
- **A repository combining Python/SQL with another stack.** The profile is an overlay and combines
  explicitly: `--profile java-spring-backend,python-sql-data`.
- **README count markers** drift the moment five skills and one profile land. Fixed by
  `check-consistency.sh --fix`, which is the intended mechanism.

## Acceptance criteria

- AC-001: a `python-sql-data` profile exists in `profiles.json` and the file parses as valid JSON.
- AC-002: the profile ships the five new skills, and every one resolves to an existing
  `skills/<name>/SKILL.md`.
- AC-003: each of the five skills contains exactly one `## SDD Contract` yaml block.
- AC-004: each of the five contracts declares `primary_agent: domain-reviewer`.
- AC-005: the three skills that surface security risk declare `security-reviewer` in
  `secondary_agents`; the other two declare an empty list.
- AC-006: `docs/PYTHON_SQL_PROFILE.md` exists and covers the five required sections.
- AC-007: `README.md` mentions the profile briefly, and its count markers and badges are correct.
- AC-008: `CHANGELOG.md` documents the change under `[Unreleased]`.
- AC-009: `scripts/check-consistency.sh` validates that the profile's skills exist and are
  correctly referenced — through existing generic rules, with no logic added.
- AC-010: `git status` shows no new or modified file under `agents/`.
- AC-011: `bash scripts/check-consistency.sh` exits 0 and
  `python3 -m json.tool profiles.json` succeeds.

## Test scenarios

- **Unit:** `scripts/check-consistency.test.sh` — the existing harness must still pass unchanged,
  which is the regression signal that no existing profile broke.
- **Integration:** `bash scripts/check-consistency.sh` on the working tree exits 0.
- **Integration (negative, by construction):** the checker was observed to *fail* on this change
  before the README markers were fixed, and on a routing target or skill name that does not
  resolve — evidence that AC-009 is enforced rather than assumed.
- **Manual:** grep for exaggerated claims across README, docs, skills, `profiles.json`, CHANGELOG
  and this spec folder; classify every hit.
- **Integration (installer):** `bash install.sh --profile python-sql-data --dry-run` resolves the
  profile (`Active profiles: core python-sql-data`) and reports all five skills as `(new)`.
- **Not run:** no *writing* install on macOS, no install on Windows, and no behavioural eval. See
  Assumptions and Open questions.

## Assumptions

- The five skills are **reviewer skills**, not mindset/discipline skills, so they are outside the
  scope of the `evals/` behavioural harness (which covers `communicator`, `scope-keeper`,
  `verifier` and the rest). No eval result is required to ship them, matching how
  `container-review`, `pipeline-review` and the other spec 024 reviewers shipped.
- `install.sh` / `install.ps1` need no change: they read profile names and skill lists from
  `profiles.json` generically. Verified for `install.sh` by a dry-run only; `install.ps1` is
  unverified — see Open questions.
- The manifest schema `version` field stays `0.4.0`: a new profile object uses only keys the
  schema already defines.

## Open questions

- OQ-1: `install.sh --profile python-sql-data --dry-run` passes on macOS — the profile resolves and
  all five skills are reported as new. A **writing** install has not been run, and
  `install.ps1 -Profile python-sql-data` has not been run on Windows at all.
- OQ-2: the five skills have not yet been run against a real Python + SQL diff. Their value is
  unproven until they are, and the first real use should be treated as a calibration pass.

## Contracted services

`specs/SERVICES.md` is absent in this repository → all billable add-ons treated as NOT contracted
(conservative default). Not applicable here: `python-sql-data` is not a billable add-on and ships
no service gate, unlike `seo-geo-addon`.
