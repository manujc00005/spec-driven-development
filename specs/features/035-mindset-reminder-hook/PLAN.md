# Implementation Plan: mindset-reminder-hook

## Summary

Ship one hook, in both shell languages, that puts the scope-keeper rules in context before a
session's first edit — then wire it into `core`, both settings templates, and CI.

## Related spec

[`SPEC.md`](./SPEC.md)

## Impacted areas

| Area | Change |
|---|---|
| `hooks/scope-keeper-reminder.sh` / `.ps1` | **New** — the hook, modelled on `graphify-scan-reminder` |
| `profiles.json` | Declare the hook under `core` |
| `settings.template.json` / `settings.template.sh.json` | New `PreToolUse` matcher |
| `scripts/mindset-hook.test.sh` / `.ps1` | **New** — AC-001..AC-009 / AC-012 |
| `.github/workflows/consistency.yml` | Wire both suites |
| `CLAUDE.md.example`, `CHANGELOG.md` | Document the hook and its kill-switch |
| `~/.claude/CLAUDE.md` (outside the repo) | D005 — applied to the user's machine, not CI-enforced |

**Not touched:** `skills/scope-keeper/SKILL.md` (source of truth for the rules), any other mindset
skill, the model-invoked path.

## Context budget

### Reading list

- `specs/features/035-mindset-reminder-hook/*`
- `hooks/graphify-scan-reminder.sh` / `.ps1` — the exemplar, read in full (both are short)
- `hooks/lib/claude-json.sh` — helper contract only (`claude_json_get_field`,
  `claude_json_emit_system_message`)
- `profiles.json` — the `core` block
- both settings templates — the `PreToolUse` array only
- `skills/scope-keeper/SKILL.md` — the rule bullets, for the excerpt and AC-009

Out of budget: every other skill, agent and spec folder.

### Model routing

| Phase | Model | Justification |
|---|---|---|
| Hook implementation | **deep-reasoning** | Untrusted stdin, a path built from a payload field, and a "must never fail an edit" contract. |
| Wiring, templates, docs | cheap/mechanical | Config edits against an existing shape. |
| Tests | cheap/mechanical | Assertions follow the ACs directly. |

No Graphify run: six files, all already located.

## Proposed approach

Copy the shape that already works — `graphify-scan-reminder` — and change three things: the matcher
(`Edit|Write|NotebookEdit`), the throttle unit (session instead of 30 minutes), and the marker
location (temp dir instead of the project tree).

Order: hook → wiring → tests → CI → docs. The hook is written first because the tests drive it
through stdin, so its interface must exist before assertions can be meaningful.

## Alternatives considered

- **Inline the rules in `CLAUDE.md`** — rejected in D001 (cost on every turn, duplication drift).
- **`UserPromptSubmit` hook** — deterministic but always-on for a rule that only binds when editing.
- **Block the edit when scope looks wrong** — rejected in D002; there is no such predicate.
- **A hook per mindset skill** — `communicator` and `stopper` have no clean `PreToolUse` seam.
- **Marker inside `.graphify/` or the project** — rejected by FR-008; it would show up in the
  adopter's `git status`.

## Dependencies

- The `PreToolUse` + `systemMessage` mechanism, already proven by `graphify-scan-reminder`.
- `hooks/lib/claude-json.sh`, already installed by `core` (spec 016).
- The `windows-latest` runner, already provisioned and now executing behavioural suites (spec 034
  D005).

## Risks

| # | Risk | Severity | Mitigation |
|---|---|---|---|
| R1 | A bug in the hook breaks every `Edit` in every session. | **High** | D002: exit 0 unconditionally; AC-003/AC-005 assert it survives malformed and empty input. |
| R2 | `session_id` is not in the payload, so the hook nags on every edit and gets disabled. | Medium | D003's time-based fallback; AC-005 covers the missing-field case. |
| R3 | Path injection via `session_id` into the marker filename. | Medium | Sanitise to `[A-Za-z0-9_-]`; AC-006 asserts `../../etc/passwd` creates nothing outside the temp dir. |
| R4 | The excerpt drifts from the skill. | Medium | D004 + AC-009: the suite fails when the skill loses a claim the hook makes. |
| R5 | Reminder fatigue → adopters disable it. | Low | Once per session, and `SDD_SCOPE_REMINDER=0` is documented rather than hidden. |

## Test strategy

- **Integration**: `scripts/mindset-hook.test.sh` drives the hook with crafted stdin for every AC —
  first fire, same session silent, new session fires, kill-switch, malformed/empty/no-`session_id`,
  traversal, project tree untouched, message content, excerpt-vs-skill corroboration.
- **PowerShell**: `scripts/mindset-hook.test.ps1` mirrors AC-001..AC-008 (AC-012), on the
  `windows-latest` runner.
- **Regression**: `check-consistency.sh` (AC-010), plus the spec 034 suites and `shellcheck`.
- **Manual**: one live session — reminder before the first edit, silence before the second.

## Rollback strategy

`git revert` removes the hook, its `profiles.json` entry and both template entries. Adopters who
already installed it keep a stale hook file in their central dir until the next `install.sh` run;
harmless, because the hook only ever prints. `SDD_SCOPE_REMINDER=0` is an immediate per-machine
kill-switch that needs no re-install. The marker files are in the temp dir and self-expire.

## PLAN verification checklist

- [x] The plan covers all acceptance criteria.
- [x] The plan avoids behavior outside the spec.
- [x] The Context budget section is filled.
- [x] Risks are documented.
- [x] Test strategy is documented.
- [x] Rollback strategy is documented.
- [x] SPEC.md status has been updated to `Ready`.
