---
name: python-testing-reviewer
description: Review pytest suites for determinism and isolation — fixture scope and leakage, mock and monkeypatch boundaries, parametrization, tmp_path over real paths, test data realism, edge cases, and how scripts and SQL get tested at all. Not for production Python structure, that is /python-reviewer.
triggers:
  - When a test file changes, or a change lands with no test
  - When a fixture, conftest.py, mock or monkeypatch is added or changed
  - When a test touches the filesystem, the clock, the network or a database
  - When the user asks "is this test meaningful?" or "why does this pass locally and fail in CI?"
---

## SDD Contract

```yaml
category: domain-reviewer
inputs: [diff, test-sources, python-sources]
outputs: [python-testing-findings]
side_effects: none
writes_code: false
writes_specs: false
analysis_only: true
primary_agent: domain-reviewer
secondary_agents: []
profile_scope: [python-sql-data]
provider_specific: false
```

# Python Testing Reviewer

## Purpose

Review a pytest suite for the two properties that decide whether anyone will trust it: **it fails
when the code is wrong, and it passes for the same reason every time.**

A suite that is green because it asserts nothing is worse than no suite, because it is quoted as
evidence.

## Extends

`test-engineer` (generic strategy and coverage-gap analysis). This skill is the pytest- and
data-specific layer underneath it.

## What this skill checks

### Does the test actually test anything

- Assertions that cannot fail: `assert result` on a non-empty structure, `assert True`, asserting
  a mock was called when the mock is the only thing under test.
- A test that mocks the function it is meant to exercise.
- No assertion at all — the test passes if nothing raises. Legitimate as a smoke test, but say so.
- Asserting a re-computation of the same expression rather than an expected literal.
- Coverage that is exercised but unasserted: a code path runs, and nothing checks its result.

### Determinism

**This is the finding that turns a suite into noise, and it is usually cheap to fix.**

- `datetime.now()`, `date.today()`, `time.time()` in code under test with no injection or freeze
  point. A test that passes except at midnight, or in another timezone, or on 29 February.
- `random` without a seed; `uuid4()` compared against an expected value.
- Iteration over a `set` or `dict` whose order the test depends on.
- Dependence on test execution order — one test's leftovers making another pass.
- Real network calls, real database connections, real clock sleeps. A test that needs the internet
  is not deterministic.
- Timing-based assertions and `sleep()` used to sequence work.
- Floating point compared with `==` instead of `pytest.approx`.

### Isolation

- Shared mutable state across tests: module-level globals, a class attribute, a cached singleton, a
  configured logger, an imported module's state.
- Environment variables set by a test and never restored — use `monkeypatch.setenv`, which undoes
  itself.
- Files written to the repository or to a fixed path instead of `tmp_path` / `tmp_path_factory`.
- A test that writes to a shared database and depends on being alone with it.
- Tests that pass individually but fail in a full run — or the reverse. Either is the finding.

### Fixtures

- Scope: is a `session`-scoped fixture mutable? Then it is shared state, and one test can poison
  the rest.
- Setup with no teardown, where teardown is needed. `yield` fixtures clean up even when the test
  fails; a fixture that returns and cleans up afterwards does not.
- A fixture doing so much that the test no longer states its own preconditions.
- Fixtures buried in a distant `conftest.py`, so a reader cannot tell what a test's world contains.
- `autouse` fixtures with real effects — they apply to tests whose authors never opted in.
- Duplication that a parametrized or factory fixture would collapse.

### Mocks and monkeypatch

- **Patch location.** `monkeypatch.setattr` / `mock.patch` must target where the name is *used*,
  not where it is defined. Patching the wrong path silently patches nothing, and the test still
  passes.
- Over-mocking: everything the function calls is mocked, so the test asserts the implementation it
  already knows and breaks on every refactor while catching no bug.
- Mocks with no spec, accepting calls with wrong signatures that would fail in production.
- Asserting call counts and arguments where asserting the outcome would be stronger and less
  brittle.
- Hand-rolled patching of globals instead of `monkeypatch`, which restores automatically.
- Mocking a database driver so thoroughly that no SQL is ever exercised — see below.

### Parametrization

- Repeated near-identical test bodies that `@pytest.mark.parametrize` would collapse into a table
  of cases, where the cases become readable as a specification.
- Parametrized cases with no `ids`, so a failure reports `test_x[case3]` and tells you nothing.
- A single case pretending to be a boundary test.
- Mutable objects shared across parametrized cases.

### Edge cases

For data work, ask specifically about:

- Empty input: zero rows, an empty file, an empty result set. Does the code divide by the row
  count?
- One row, and exactly-at-the-boundary batch sizes.
- `None`/`NULL` in every field the code reads.
- Duplicate keys in the input.
- Wrong types and unparseable values arriving from a file or an upstream system.
- Unicode, embedded delimiters, embedded newlines, and a BOM in a CSV.
- Very large values, negative values, zero.
- Dates at DST transitions, at year boundaries, and on 29 February.

### Testing scripts

- Is the script importable, or does it do work at module scope so importing it runs it?
- Is there a callable entry point (`main(argv)`) separable from `if __name__ == "__main__"`, so a
  test can call it with arguments?
- Are argument parsing, exit codes and error paths tested, or only the happy path in the middle?
- Is the exit code asserted? A script's contract with its scheduler is its exit code.
- Is `sys.argv` manipulated directly instead of through `monkeypatch`?

### Testing SQL

State plainly which of these the project does, because the trade-off is real and different
projects settle it differently.

- **Nothing** — the SQL is never executed in a test. Then say so: query correctness is unverified,
  and `sql-query-reviewer` is the only check it gets.
- **Against a real engine** (a container, a local instance, a transactional fixture that rolls
  back). Strongest signal; check that fixtures roll back or truncate, so tests do not depend on
  leftovers.
- **Against an in-memory substitute** (SQLite standing in for another engine). Cheap and fast, but
  it does not share dialect, types or NULL/collation behaviour with the target. A test passing here
  is not evidence the production query works.
- Assert on results, not on the query string. A test that asserts SQL text pins the implementation
  and catches no wrong-result bug.

### Test data

- Fixtures with data too clean to be realistic — no nulls, no duplicates, no odd encodings, when
  the real source has all three.
- Real production data, real names, real emails, real identifiers checked into the repository.
  That is a `security-reviewer` and privacy finding; name it and hand it over.
- Large fixture files where a handful of representative rows would do.
- Expected values maintained by hand in two places, so they drift.

### Suite hygiene

- `@pytest.mark.skip` / `xfail` with no reason and no ticket — a permanently disabled test that
  still counts as a test.
- Broad `pytest.raises(Exception)` that would pass on the wrong exception, including an
  `AttributeError` from a typo.
- Warnings-as-noise: a suite where nothing is configured, so a real deprecation is invisible.
- Tests that take long enough that people stop running them locally.

## What this skill does NOT do

- **Does not replace `pytest`.** It does not run tests, and a passing review is not a passing
  suite. Findings are about the tests as code.
- **Does not replace `coverage.py`.** It reasons about untested behaviour, not line coverage
  percentages.
- Does not review production Python structure (that is `python-reviewer`), SQL correctness (that is
  `sql-query-reviewer`), or pipeline re-run safety (that is `data-pipeline-reviewer`).
- Does not design a test strategy from scratch before implementation — that is `test-engineer`.
- Does not decide merge readiness against acceptance criteria — that is `qa-review`.
- Does not write, run or modify tests.

## Output format

```markdown
## Python Testing Review — <suite or module>

**Verdict:** PASS | PASS WITH NOTES | FAIL

### Findings

| # | Severity | File:Line | Finding | Action |
|---|---|---|---|---|

### Determinism risks

- (Clock, randomness, ordering, network, shared state — each with the test that carries it)

### SQL under test

- (Which of: not executed / real engine / in-memory substitute — and what that does not prove)

### Untested behaviour

- (Behaviour in the diff that no test would catch if it broke)
```

## Context economy

- Read the changed tests, their `conftest.py`, and the code under test. Nothing else.
- Do not read the whole suite to comment on the changed part of it.
- Report tests that would not catch a regression before reporting style.
- Always end with the next recommended command.
