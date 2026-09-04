# T011 — scripts/check-consistency.test.sh

## Run 2 (2026-09-04T20:07:44Z, after the SEC-044-001 fix)

```
[PASS] plugin-wiring-hook-removed
[PASS] plugin-wiring-chained-command
[PASS] plugin-wiring-absolute-path
[PASS] plugin-wiring-missing-file
50 passed, 0 failed.
```

## Run 3 (after the residual fix: unknown keys, suffix, malformed shape)

```
[PASS] plugin-wiring-hook-removed
[PASS] plugin-wiring-chained-command
[PASS] plugin-wiring-absolute-path
[PASS] plugin-wiring-async-key
[PASS] plugin-wiring-suffix-command
[PASS] plugin-wiring-malformed-shape
[PASS] plugin-wiring-missing-file
53 passed, 0 failed.
```

The trailing `exit 1` line in the log is an artefact of the logging command that wrote it (a mistyped path in its first redirection), not the suite: the suite's own summary is `53 passed, 0 failed` and the harness reported exit 0 for the task.

Full log of the latest run: CONSISTENCY_SUITE.log.
