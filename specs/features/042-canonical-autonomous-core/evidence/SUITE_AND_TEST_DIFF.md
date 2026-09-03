# Suite count and test-diff evidence — T020 / AC-005

## Count

```
$ PYTHONPATH=runner python3 -m unittest discover -s runner/tests -t runner
Ran 362 tests
OK
```

Baseline on `main` was **276**. The floor AC-005 sets is "at least 276, all passing"; the suite is
at **362** because this feature adds 86 contract tests, not because anything was relaxed.

Run on a machine with **neither** the Claude Agent SDK nor a usable Codex CLI: the Claude backend's
precondition message (`import failed: No module named 'anyio'`) appears in the output of the test
that asserts it fails cleanly, which is what "works with nothing installed" looks like when it is
true.

## No assertion was weakened

```
$ git diff main -- runner/tests | grep -E "^-" | grep -vE "^---" | grep -E "assert|self\.fail"
(none)
```

**Not one deleted or altered assertion line** across the whole test tree.

## No import had to change either

D001 predicted the cost of a package rename as 21 test files of import churn, and chose against it.
The prediction can now be checked: pre-existing test files touched by this feature —

```
$ git diff main --name-only -- runner/tests | grep -v contract/
runner/tests/conformance/PROTOCOL_TRANSCRIPTION.md
runner/tests/conformance/test_transcription.py
```

Two files, and neither for an import path. `test_transcription.py` changed because T018 *registered
more modules* with its guard (`policy`, `protocol`, `resume`, `retry`) and added the
`test_no_row_is_silently_unchecked` case — additive, and the reason the table's last unverified row
is now verified. The other 19 test files are byte-identical to `main`.

That is the evidence for D001: keeping the package name cost one slightly-wrong word and bought a
diff in which every changed line is the refactor itself.
