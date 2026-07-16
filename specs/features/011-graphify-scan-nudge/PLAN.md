# Implementation Plan: graphify-scan-nudge

## Summary

One new hook family (`graphify-scan-reminder.{sh,ps1}`), wired on `PreToolUse`
`Grep|Glob` in both settings templates, listed in the core profile, documented,
and covered by sandbox tests. Follows `git-guardrails` stdin conventions and
`graphify-stale-reminder` messaging/portability conventions (dual `stat`,
mkdir-safe marker, exit 0 always).

## Related spec

`specs/features/011-graphify-scan-nudge/SPEC.md`

## Impacted areas

- `hooks/graphify-scan-reminder.sh` / `.ps1` (new)
- `settings.template.json` / `settings.template.sh.json` (PreToolUse entry)
- `profiles.json` (core hooks list)
- `hooks/README.md` (row + bullet), `README.md` (count markers via `--fix`)
- `scripts/graphify.test.sh` (new cases)

## Proposed approach

Hook: consume stdin → opt-out check → report resolution (canonical + legacy) →
TTL check on `.graphify/.scan-nudge` mtime (30 min; unreadable marker = absent)
→ touch marker + emit nudge. PS1 parity. Wire, document, test, run
`check-consistency.sh --fix` for README counts.

## Alternatives considered

- Blocking (exit 2) on broad scans — rejected: targeted Grep is legitimate;
  false positives would erode trust in all hooks.
- Inspecting tool_input to detect "broad" patterns — rejected: fragile
  heuristic, and the throttled nudge is cheap enough without it.

## Risks

- Nudge fatigue if TTL too short — 30 min chosen; opt-out env var as escape.
- `systemMessage` visibility to the model varies by Claude Code version — same
  bet the whole repo already makes.

## Test strategy

Sandbox cases in `graphify.test.sh` (AC-001..003); harness + wire-hooks dry-run
(AC-004); regression: full suite re-run.

## Rollback strategy

Revert commit; `SDD_GRAPHIFY_NUDGE=0` is the immediate kill-switch.

## PLAN verification checklist

- [x] The plan covers all acceptance criteria.
- [x] The plan avoids behavior outside the spec.
- [x] Risks are documented.
- [x] Test strategy is documented.
- [x] Rollback strategy is documented.
- [x] SPEC.md status has been updated (In Progress).
