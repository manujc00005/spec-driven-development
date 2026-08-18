---
name: python-reviewer
description: Review Python code and internal scripts for typing, module structure, logic/IO/config separation, exception handling, silent failures, logging, pathlib and dataclass idioms, context managers, and dependency creep. Not a linter — it does not replace ruff or mypy. Not for test code, that is /python-testing-reviewer.
triggers:
  - When a `.py` file changes in a project using the `python-sql-data` profile
  - When a script grows past "quick throwaway" and someone else will run it
  - When configuration, credentials or paths are read inside business logic
  - When the user asks "is this script maintainable?" or "will this fail loudly?"
---

## SDD Contract

```yaml
category: domain-reviewer
inputs: [diff, python-sources]
outputs: [python-findings]
side_effects: none
writes_code: false
writes_specs: false
analysis_only: true
primary_agent: domain-reviewer
secondary_agents: [security-reviewer]
profile_scope: [python-sql-data]
provider_specific: false
```

# Python Reviewer

## Purpose

Review Python the way it is actually written in a data/automation shop: scripts that started small,
got scheduled, and are now load-bearing.

The failure this skill exists to catch is not ugly code. It is **a script that fails quietly, or
succeeds for the wrong reason**, and nobody notices for a week.

## Extends

Nothing generic. Runs alongside `sql-query-reviewer` (the queries this code sends) and
`python-testing-reviewer` (the tests that cover it). No ordering dependency, though reviewing
structure before tests usually reads better.

## What this skill checks

### Failing loudly

**This is the finding most often missed in internal tooling.**

- `except Exception: pass` and `except: continue` — the process exits 0 and the data is wrong.
  Every swallowed exception must have a stated reason for being swallowed.
- A bare `except` that also catches `KeyboardInterrupt` and `SystemExit`.
- Logging an error and then continuing as if it did not happen — including `logger.error(...)`
  with no re-raise and no non-zero exit.
- A script whose exit code is 0 on partial failure. If 900 of 1000 rows loaded, what does the
  caller see?
- `print()` used as error reporting, so nothing lands in a log the scheduler can read — unless
  the script is embedded in shell, where `print()` is the interface (see the section below).

### Control flow that depends on formatted text

Does any decision read a string that was built for a human to look at?

- Errors, results or statuses accumulated as **formatted strings** and later filtered, counted or
  matched by substring. The message is presentation; the moment it also carries meaning, rewording
  it changes behaviour — and nothing near the edit hints that it will.
- The failure shape is the dangerous one: the match silently stops matching, the code takes the
  "nothing to do" branch, and it reports success. Nothing raises.
- `if "ERROR" in output` or `startswith("[warn]")` over another command's stdout — the same defect
  across a process boundary, where the other side is free to reword at any time.
- Regex over a log line or a CLI banner to recover a value the tool also exposes as JSON, a field,
  or an exit code.
- The fix is always the same: keep the **record** (a `NamedTuple`, a dataclass, a dict with stable
  keys) and render text only at the boundary where a human reads it.

### Typing

- Are public function signatures annotated? Internal helpers can be looser; boundaries should not.
- `Any` and untyped `dict` passed between layers — a `dict[str, Any]` crossing three functions is
  an undocumented schema.
- `Optional`/`| None` returns whose callers do not check for `None`.
- Mutable default arguments (`def f(x=[])`).
- This skill reads annotations as **documentation and intent**. It does not typecheck — see the
  boundary section.

### Module structure and function size

- Does the module have a single reason to exist, or is it `utils.py` accumulating everything?
- Functions doing more than one job — a function that reads a file, transforms rows, and writes to
  a database cannot be tested without both a file and a database.
- Deep nesting that a guard clause would flatten.
- Import-time side effects: a database connection, a file read, or a network call at module scope
  runs on import, including on `--help` and during test collection.

### Logic / IO / config separation

- Is pure transformation logic separable from the code that reads and writes? This is the single
  change that makes a script testable.
- Configuration read from the environment deep inside a function, rather than resolved once at the
  entry point and passed in.
- Hardcoded paths, hostnames, schema names, date ranges or magic constants.
- Credentials read in one place versus scattered — and whether any of them are literals in source.
  A credential in source is a `security-reviewer` finding; note it and hand it over.

### Resource handling

- File, connection, cursor and transaction handling without a context manager. An unclosed
  connection in a loop is a leak with a delay fuse.
- `pathlib.Path` versus string concatenation and `os.path.join` chains — string paths break on the
  first filename with a space or a different separator.
- Encoding left implicit in `open()`. On a CSV from an upstream system, the platform default is a
  guess, not a decision.
- Long-lived resources held open across an entire batch when they could be scoped per unit.

### Data shape and modelling

- Row-shaped tuples passed around positionally (`row[3]`) — one upstream column reorder away from
  silently wrong output.
- `dataclass` / `NamedTuple` used where a dict is being pressed into service as a record type.
- `pydantic` where the project already uses it: is validation actually enforced at the boundary,
  or is the model constructed with `.construct()` / `model_construct()` and skipping it?
- If the project does not use pydantic, do not introduce it as a finding. Note the missing
  boundary validation and let the project choose the mechanism.

### Logging

Skip this section entirely for Python embedded in a shell heredoc — there `print()` is the
interface, not a missing logger.

- Is there any log line that would let someone reconstruct what a scheduled run did?
- Log level used as decoration — everything at `INFO`, or errors at `WARNING`.
- f-strings in log calls versus lazy `%s` args (cost only matters in hot loops; correctness of the
  message matters everywhere).
- Rows, IDs, emails or full payloads logged. Personal data in logs is a `security-reviewer` and
  privacy finding — name it and hand it over.

### Dependencies

- A dependency added for one function that the standard library already covers.
- Imports that no longer have a caller.
- Version pinning: does the project pin, and does this change respect that convention?
- A heavyweight import (pandas, requests, a database driver) pulled into a module that does not
  need it, paid on every import.

## Python embedded in shell scripts

Python inside a `python3 - <<'EOF'` heredoc is a normal shape in automation repositories, and
several checks above must be read differently there. State which mode you are reviewing in.

- **`print()` is the interface, not sloppy logging.** The block talks to its caller through stdout,
  so each `print()` is a protocol frame. Do not report it as "should use logging".
- **Review the protocol instead.** Are emitted values validated before they are written — no
  embedded newline, no delimiter collision, no unescaped separator? An unvalidated value in a
  line-oriented `KEY:value` protocol corrupts the parse on the other side.
- **The exit code carries more weight than usual**, because the caller branches on it rather than
  on the text.
- **Module-scope execution is inherent, not a defect** — there is no import to protect. Say so, and
  name the consequence: the block cannot be unit-tested in Python, so its tests live at the shell
  level or nowhere.
- **Heredoc quoting changes the program.** `<<'EOF'` blocks shell expansion; `<<EOF` lets `$` and
  backticks expand *before* Python sees them, silently rewriting the source under review.
- **Old bash mangles heredocs inside `$(...)`.** bash 3.2, still the macOS default, does not skip
  heredoc bodies when scanning for the closing paren. An odd number of single quotes in the block —
  one apostrophe in a comment is enough — reads as an unterminated string and breaks the script at
  a line far from the edit.

## What this skill does NOT do

- **Does not replace `ruff`, `flake8`, `black` or `isort`.** Formatting, import order and lint
  rules are a tool's job, run in CI. If the project has no linter configured, say so once as a
  finding and move on — do not hand-enumerate lint violations.
- **Does not replace `mypy` or `pyright`.** It reads annotations for intent; it does not perform
  type inference and cannot tell you a call is type-incorrect.
- Does not review test code — fixtures, mocks, parametrization (that is `python-testing-reviewer`).
- Does not review SQL text, even when it is embedded in a Python string (that is
  `sql-query-reviewer`) or the cost of running it (that is `database-performance-reviewer`).
- Does not review re-run safety of a whole load process (that is `data-pipeline-reviewer`).
- Does not execute the code, install dependencies, or run the script.
- Does not modify code.

## Output format

```markdown
## Python Review — <module or script>

**Verdict:** PASS | PASS WITH NOTES | FAIL

**Mode:** standalone module | script | embedded in shell heredoc

### Findings

| # | Severity | File:Line | Finding | Action |
|---|---|---|---|---|

### Failure behaviour

- (What this code does on a partial failure, and what exit code the caller sees)

### Handed to other reviewers

- (Secrets, PII in logs, injection risk → security-reviewer; SQL text → sql-query-reviewer)
```

## Context economy

- Read the changed modules and their direct callers. Do not walk the whole package.
- Do not read test files — that is a separate skill with its own budget.
- Report findings that change behaviour or testability, not style preferences a linter owns.
- Always end with the next recommended command.
