# Implementation Plan: eval-runner-isolation

## Summary

Add two gates to `scripts/skill-eval.sh` that run **before any model call**: a provider-aware
isolation check (Claude Code and Codex, both first-class) and a model-pin check that makes the
recorded model identifier traceable to the command actually executed. Both fail closed. An
explicit `--allow-unisolated` opt-out exists for unrecognized runners and **downgrades the result
file** rather than producing one indistinguishable from a clean run. Documentation in three places
is brought into agreement, and `evals/README.md` stops claiming the contamination is unsolved.

No change to the arms, the prompts, the verdict cascade, or the exit codes for a runner that is
already isolated and pinned.

## Related spec

`specs/features/028-eval-runner-isolation/SPEC.md`

## Impacted areas

| Path | Change |
|---|---|
| `scripts/skill-eval.sh` | Provider table, tokenizer, two gates, opt-out flag, result-file row, header/`--help` |
| `scripts/skill-eval.test.sh` | New refusal and downgrade cases; stub runner adapts to the opt-out path |
| `evals/README.md` | Replace the "stated, not solved" paragraph; update the documented runner |
| `CONTRIBUTING.md` | Update the documented runner (line ~58) so all three sources agree |
| `specs/features/028-eval-runner-isolation/DECISIONS.md` | Records the Q1 and Codex verifications |

Nothing under `skills/`, `hooks/`, `adapters/`, `profiles.json`, or the installers is touched.
`evals/` is never installed into a user project (`evals/README.md:5-6`), so no profile is affected.

## Context budget

### Reading list

- `specs/features/028-eval-runner-isolation/*` — the active feature folder.
- `scripts/skill-eval.sh` (268 lines) — the whole file; the change touches its gate ordering.
- `scripts/skill-eval.test.sh` (240 lines) — the whole file; every existing case passes
  `SKILL_EVAL_MODEL` with an unpinned stub runner and must keep passing.
- `evals/README.md` (155 lines) — FR-008 rewrites one section; the rest is the contract being
  preserved.
- `CONTRIBUTING.md` lines 40–80 only — the eval gate section.

Explicitly **not** read: `skills/**` (the harness never mutates a skill and does not need to read
one to change its own gates), `adapters/codex/prompts/**`, `install*.sh`, `profiles.json`, other
feature folders. Total budget: roughly 700 lines of source plus the feature folder.

### Model routing

| Phase | Model | Justification |
|---|---|---|
| T001–T008 (script + CONTRIBUTING) | cheap / mechanical | Bounded edits to one 268-line bash script against explicit acceptance criteria. No design left open. |
| T009 (README rewrite) | deep reasoning | The honest wording of what isolation does and does not cover is a judgement call about evidence, and it is what a reviewer trusts. Blocked on T012's observation. |
| T010–T011 (tests) | cheap / mechanical | Extends an existing table-driven suite with a stubbed runner. |
| T012, T013 (empirical checks) | maintainer, not a model | Requires a real CLI on a real machine with a non-empty user config. Cannot be delegated to an agent. |

No Graphify query is needed: the impacted surface is four known files, already enumerated.

## Proposed approach

**1. Tokenize the runner string without a second `eval`.**
`$SKILL_EVAL_RUNNER` is already `eval`'d at [skill-eval.sh:168](scripts/skill-eval.sh:168);
inspecting it must not add a second shell context (NFR-Security). Split it with
`printf '%s' "$RUNNER" | xargs -n1`, which parses quotes without being a shell. An unmatched quote
makes `xargs` fail — that becomes a refusal, which is the correct direction. This is what makes
the "flag name inside a quoted prompt fragment" edge case detectable rather than a substring
false-positive.

**2. Provider table, not branches.**
A newline-delimited constant string, three fields per row: provider command, required isolation
tokens, required pin flag. Bash 3.2 has no associative arrays (macOS default shell), so the table
is parsed with `while read`. Adding a provider is a row.

```
claude|--setting-sources=<empty>|--model
codex |--ignore-user-config,--ephemeral|--model
```

**3. Provider detection tolerant of real invocations.**
Skip leading `env` and its `VAR=value` / `-u VAR` arguments, take `basename` of the first bare
word. `env -u SKILL_EVAL_MODEL /usr/local/bin/claude -p …` resolves to `claude`. Anything not in
the table is *unrecognized* — never silently treated as isolated.

**4. Two gates, fail closed, before the token spend.**
Both sit after the existing unset-runner print path
([skill-eval.sh:98-115](scripts/skill-eval.sh:98)) — that path must keep exiting 0 — and before
the model-identity check at line 117, which they replace:

- **Isolation gate.** Recognized provider missing a required token → exit 1 naming the exact flag
  and the provider. Partial isolation (`--setting-sources project`) is not isolation. Codex flags
  on `claude` are not isolation. Unrecognized provider → exit 1 pointing at `--allow-unisolated`.
- **Pin gate.** Recognized provider: the identifier comes from `--model` in the command. If
  `$SKILL_EVAL_MODEL` is also set and disagrees, exit 1 — no silent preference. Missing pin →
  exit 1 citing that an env-only identifier is an unverifiable claim.

**5. The opt-out downgrades rather than exempts.**
`--allow-unisolated` permits an unrecognized runner. Under it, `$SKILL_EVAL_MODEL` is accepted as
the identifier again — there is no command to derive it from — but the result file records both
facts explicitly: isolation `NONE`, model provenance `operator-asserted`. This is also what keeps
the existing 240-line test suite working, since its stub runner is by construction unrecognized
(see D004).

**6. Record it where a reviewer looks.**
One new row in the result-file table between `runner` and `reps per arm`, and one new line in the
pre-run summary the operator reads before spending tokens. Existing rows keep their names and
order so committed results stay readable.

**7. Make the three documented runners agree.**
`skill-eval.sh` header, `evals/README.md`, `CONTRIBUTING.md:58`. Note that `--help` prints a fixed
line range (`sed -n '3,26p' "$0"`, [skill-eval.sh:41](scripts/skill-eval.sh:41)) — editing the
header without updating that range silently truncates the help text.

## Alternatives considered

- **Warning instead of hard error.** Rejected by the maintainer (Q2, D001). A warning is read once
  and ignored, and the artifact it produces is indistinguishable from a clean one — the exact
  failure this feature exists to remove.
- **Restrict enforcement to Claude Code, route Codex through the opt-out.** Proposed during spec
  review and rejected by the maintainer (Q3, D002): Codex is first-class everywhere else in this
  framework. The unverified-flags risk is handled by FR-011 (verify before close) instead of by
  narrowing scope.
- **A declarative `runners.json` registry** (the `i-have-adhd` shape). Rejected for this feature —
  it couples cleanly to cost metering and resumability, which are separate specs. Introducing the
  file now would force the same migration twice.
- **`eval "set -- $RUNNER"` to tokenize.** Rejected: a second shell context over an attacker- or
  typo-controlled string, against the spec's security NFR, for no gain over `xargs`.
- **Put the provider table in `adapters/`.** Rejected: `adapters/codex/` holds prompts, an
  installer, and parity docs — no runtime tables. A table read by one bash script belongs in that
  script (D006).
- **Add `--tools ""` to the isolated invocation.** Rejected in the spec's assumptions:
  `evals/README.md:75-77` already shows that disabling tools does not fix scenario grounding, and
  it would change what the arms measure.

## Dependencies

- ~~**Codex CLI** must be installed to close the feature (FR-011 / AC-011).~~ **No longer a
  dependency (D011).** It is still not present on the maintainer's machine, and the verification is
  still outstanding — it is now tracked as DEBT-001 in `docs/KNOWN_DEBT.md` rather than blocking
  the close. Nothing about the risk changed; only who is holding it.
- A machine with a **non-empty `~/.claude/CLAUDE.md`** for the Q1 observation (AC-009) — otherwise
  the check cannot distinguish "isolated" from "nothing to isolate".
- `xargs` (POSIX, present on macOS, Linux, and Git Bash). No new runtime dependency.

## Risks

| # | Risk | Mitigation |
|---|---|---|
| R1 | The existing test suite breaks: all 240 lines drive an unpinned stub runner with `SKILL_EVAL_MODEL`. | D004 — the opt-out path keeps env-only identifiers legal. Tests add `--allow-unisolated`; T008 asserts the downgrade is recorded. |
| R2 | Codex flags are unverified; the shipped table could be wrong. | ~~FR-011 blocks `Done`.~~ **Accepted as DEBT-001 (D011)** — the close gate was removed, so this risk now ships. Softened by FR-012: the refusal names the flag set as unverified and points at `--allow-unisolated`, so a wrong table is self-diagnosing rather than a dead end. If the real flags differ the table row is corrected; the decision to cover Codex is not revisited. |
| R3 | `--setting-sources ""` may suppress only `settings.json`, not user `CLAUDE.md`. Over-claiming in the README would be worse than the current honest caveat. | T009 resolves it empirically **before** T007 writes the wording. If memory still loads, FR-008 narrows the claim instead of removing the caveat. |
| R4 | `xargs` quote parsing differs from the shell's for exotic runners (backslashes, `$` expansion), causing a false refusal. | The opt-out is the escape hatch; the refusal message names it. Documented as a known limit. |
| R5 | Editing the script header desynchronizes `--help` (`sed -n '3,26p'`). | T006 owns both edits; T008 asserts `--help` still prints the isolated example. |
| R6 | Scope creep toward cost metering and the runner registry while inside the same file. | Declared non-goals in SPEC; `/scope-keeper` before the first edit. |

## Test strategy

- **Unit (table-driven, inside `skill-eval.test.sh`):** provider detection and isolation matching
  over a fixture table — isolated claude, isolated codex, missing one Codex flag, partial
  `--setting-sources project`, Codex flags passed to `claude`, `--model` appearing inside a quoted
  prompt fragment, `env -u X /abs/path/claude`, bare wrapper script.
- **Integration:** the four gates end-to-end with the stub runner — isolated pass, missing-isolation
  reject, missing-pin reject, opt-out downgrade — asserting exit code, error substring, and
  result-file content. Zero network calls, matching the suite's existing contract.
- **Regression:** prompt invariance. Both arm prompts must be byte-identical to pre-change output
  for an isolated runner, and the five verdict cases
  (`skill-eval.test.sh:184-198`) must produce the same verdicts.
- **E2E:** deliberately none. A real sweep costs tokens and is off the CI path by design.
- **Manual:** T009 (Claude Code, machine with non-empty `~/.claude/CLAUDE.md`) and T010
  (`codex exec`). These are the evidence for AC-009 and AC-011 and cannot be automated.
- **Consistency:** `bash scripts/check-consistency.sh` must pass (AC-008).

## Rollback strategy

Revert the commit. The feature touches one script, its test file, and two documents; there is no
migration, no persisted state, and no installed artifact — `profiles.json` never lists `evals/`
and the installers never copy it, so no user project can be mid-upgrade.

Partial rollback is also viable: dropping the pin gate while keeping the isolation gate leaves a
coherent, weaker feature. The reverse is not — a pin gate without isolation records an accurate
model for a contaminated run.

Already-committed result files are unaffected: they are dated observations and remain valid
records of what was observed under the old rules.

## PLAN verification checklist

- [x] The plan covers all acceptance criteria (AC-001…AC-011 mapped in `TASKS.md`).
- [x] The plan avoids behavior outside the spec (non-goals restated under Alternatives; R6).
- [x] The Context budget section is filled (reading list + model routing).
- [x] Risks are documented (R1–R6).
- [x] Test strategy is documented.
- [x] Rollback strategy is documented.
- [x] SPEC.md status has been updated to `Ready`.
