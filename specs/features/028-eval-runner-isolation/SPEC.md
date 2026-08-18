# Feature Spec: eval-runner-isolation

## Status

Done

## Problem

`scripts/skill-eval.sh` sandboxes the **working directory** but not the **operator's
configuration**, and it cannot verify the model identity it records. Two consequences, both
already documented as accepted limitations:

1. **Config contamination.** `evals/README.md:142-146` states it plainly: *"A user-level config
   still loads — for Claude Code, `~/.claude/CLAUDE.md` — so results carry whatever standing
   instructions the operator has. Two runs on different machines are therefore not strictly
   comparable. This is stated, not solved."* User-level plugins, hooks, memory, output styles and
   saved model/effort settings all leak into **both arms**. A standing instruction that shapes
   output (e.g. "always answer concisely") silently moves the control arm toward the treatment
   arm, compressing the very delta the harness exists to measure.

2. **Unverifiable model identity.** FR-006 of spec 022 requires a model identifier because *"a
   result without a model identifier is not evidence"*, but the check is satisfiable by assertion.
   `SKILL_EVAL_MODEL=claude-sonnet-5` with a runner of `claude -p` passes
   [skill-eval.sh:117](scripts/skill-eval.sh:117) and writes `| model | claude-sonnet-5 |` into
   the result file while the CLI actually runs whatever its release default is. The recorded model
   can be false, and nothing in the artifact reveals it.

The reference implementation reviewed for this work (`i-have-adhd`, `evals/runners.example.json`)
solves both at the invocation site: `--setting-sources ""` to drop operator config, and an
explicit `--model` pin so the model is chosen by the harness rather than by the operator's saved
settings or the CLI release.

## Goal

A result file produced by `skill-eval.sh` states, verifiably, the configuration conditions it was
produced under — so two runs on two machines are comparable, and a reader can tell an isolated run
from a contaminated one without trusting the operator.

## Non-goals

- **Replacing the free-form `SKILL_EVAL_RUNNER` contract with a runner registry.** The
  `runners.example.json` shape (declarative per-provider command + response format) is a larger
  change tied to cost metering; it belongs to a separate spec.
- **Cost metering and budget caps** (`--max-budget-usd`, unmetered-runner rejection). Separate
  concern, separate spec.
- **Reworking the scenario corpus.** Every scenario in `evals/scenarios/` is superseded (spec 022,
  D010); replacing it is spec 023's job. This feature must not depend on that landing.
- **Resumability and retry-on-provider-failure.** Separate concern.
- **A PowerShell sibling.** `skill-eval.sh` ships without a `.ps1` today and this feature does not
  add one.
- **Changing verdict thresholds or the verdict cascade.** Untouched.

## Users / Actors

- **Contributor** changing a discipline or mindset skill, who must attach an `evals/results/` file
  to the PR (`CONTRIBUTING.md:51-60`).
- **Reviewer** reading that result file and deciding whether it is evidence.
- **Maintainer** comparing results produced on different machines or at different dates.

## Current behavior

- `SKILL_EVAL_RUNNER` is an arbitrary command string, `eval`'d at
  [skill-eval.sh:168](scripts/skill-eval.sh:168) inside an empty `mktemp -d` sandbox.
- Isolation flags are entirely the operator's responsibility. The script neither suggests nor
  checks them. The documented example — `claude -p --model claude-sonnet-5` — carries none.
- Model identity comes from `$SKILL_EVAL_MODEL`, or failing that a regex over the runner string
  ([skill-eval.sh:76-78](scripts/skill-eval.sh:76)). Either source is an unchecked claim.
- The result file records `model` and `runner` verbatim and says nothing about isolation.
- `evals/README.md` documents the gap as unsolved.

## Desired behavior

- The script knows the isolation flags for the runners it can recognize and tells the operator
  what is missing, naming the flag.
- A run whose model identity rests only on `$SKILL_EVAL_MODEL`, with no pin in the runner command,
  is rejected — the identifier must be traceable to the command actually executed.
- The result file carries an explicit isolation status, so an un-isolated run is legible as such
  rather than indistinguishable from an isolated one.
- `evals/README.md` no longer claims the contamination is unsolved; it states what is now
  enforced and what genuinely remains.

## Functional requirements

- FR-001: The script MUST detect whether the configured `SKILL_EVAL_RUNNER` isolates the call from
  operator-level configuration, for **both** runner families the repo supports: Claude Code and
  Codex. Codex is a first-class provider across this framework (`adapters/`, profile support), so
  it is enforced on the same footing as Claude Code, not routed through the opt-out.
- FR-002: When isolation cannot be confirmed, the script MUST refuse to run — exit non-zero before
  any model call — and name the exact missing flag in the error. A warning that still runs is not
  acceptable: it is read once, ignored, and leaves a result file indistinguishable from a clean
  one (D-Q2).
- FR-003: An explicit opt-out MUST exist for unrecognized or custom runners, so a contributor is
  never hard-blocked from using a provider the repo does not know about.
- FR-004: A run started under the FR-003 opt-out MUST be recorded in the result file as
  un-isolated. The opt-out downgrades the artifact; it never produces a result indistinguishable
  from an isolated one.
- FR-005: For a **recognized** provider, the model identifier MUST be derivable from the executed
  runner command. Supplying only `$SKILL_EVAL_MODEL` with no pin in the command MUST be rejected,
  since the recorded identifier would be an unverifiable claim (this narrows spec 022 FR-006
  rather than replacing it). Under the FR-003 opt-out there is no command to derive from, so
  `$SKILL_EVAL_MODEL` remains the identifier of record and is recorded as operator-asserted
  (D004).
- FR-006: The result file MUST carry an isolation field alongside `model` and `runner`, stating
  which mechanism was applied or that none was.
- FR-007: The documented example runner in `skill-eval.sh --help`, `evals/README.md` and
  `CONTRIBUTING.md` MUST be an isolated, model-pinned invocation. All three currently show
  `claude -p --model <id>` and must agree after the change.
- FR-008: `evals/README.md` MUST replace the "stated, not solved" paragraph with an accurate
  description of what isolation now covers and what residual contamination remains.
- FR-009: `scripts/skill-eval.test.sh` MUST cover the new paths with its stubbed runner, adding no
  model calls to the test suite.
- FR-010: Behaviour for a runner that is already correctly isolated and pinned MUST be unchanged —
  same prompts, same arms, same verdict cascade, same exit codes.
- FR-011: ~~The Codex isolation flag set MUST be verified against a real `codex exec` invocation
  before this feature closes~~ — **downgraded 2026-08-07 (D011).** The Codex CLI is not available
  on the maintainer's machine and the rest of the feature is complete, so verification moves from
  a close-blocking gate to **declared debt**: recorded in `docs/KNOWN_DEBT.md` as DEBT-001 and
  carried in the PR description. The flags remain enforced from day one (FR-001); what changed is
  only that shipping them unverified no longer blocks `Done`.
- FR-012: Because FR-011 no longer gates the close, the Codex refusal message MUST say that the
  flag set is unverified and point at `--allow-unisolated`. A wrong flag would otherwise hard-block
  a working Codex runner with an error that reads as authoritative and offers no way past it.

## Non-functional requirements

- **Performance:** No additional model calls. Detection is string inspection of the runner
  command; cost is zero.
- **Security:** The runner string is already passed to `eval`; this feature MUST NOT widen that
  surface. Detection must not interpolate the runner string into a second shell context.
- **Observability:** The isolation status must be visible in two places — the pre-run summary the
  operator reads before spending tokens, and the committed result file.
- **Maintainability:** Adding a runner family must be a table entry, not a new branch in
  `run_arm`. Adapters live under `adapters/`; keep provider knowledge consistent with that.
- **Portability:** Bash 3.2 (macOS default) and Git Bash on Windows, matching the rest of
  `scripts/`. No associative arrays.

## API / Interface changes

- `scripts/skill-eval.sh`: one new opt-out flag or environment variable (name to be fixed in
  PLAN) enabling FR-003. No change to positional arguments, `--reps`, or `--out`.
- `SKILL_EVAL_MODEL` narrows from "identifier of record" to a redundant cross-check: it may
  confirm the pin found in the command, but may no longer stand alone (FR-005). This is a
  **breaking change for any operator relying on it alone**, and the error must say so.
- Result-file table gains one row (FR-006). Existing rows keep their names and order, so already
  committed results stay readable.

## Data model changes

None. No persistence, schema, or migration.

## Edge cases

- Runner is neither `claude` nor `codex` (a wrapper script, `env VAR=x claude …`, an absolute
  path, or an SDK shim): unrecognized → FR-003 opt-out path, not a false-confidence pass.
- Runner is a shell pipeline or carries quoted arguments containing the literal text of a flag:
  detection must not be fooled by a flag name appearing inside a quoted prompt fragment.
- `--setting-sources` present but non-empty (e.g. `--setting-sources project`): partial isolation.
  Must not count as isolated.
- `--model` present but the value is a wrapper alias rather than a model id: recorded verbatim;
  the harness cannot resolve aliases and must not pretend to.
- `SKILL_EVAL_RUNNER` unset: the existing print-the-prompts-and-exit path
  ([skill-eval.sh:98-115](scripts/skill-eval.sh:98)) must still work and must show an isolated
  example.
- Both `SKILL_EVAL_MODEL` and a `--model` pin present and **disagreeing**: an error, not a silent
  preference for one.
- Isolation flags supplied for one provider but the command invokes another (`--ignore-user-config`
  passed to `claude`): must not be accepted as isolation.

## Acceptance criteria

- AC-001: With `SKILL_EVAL_RUNNER='claude -p --model <id>'` (no isolation flag), the script exits
  non-zero before any model call, and the message names the missing flag.
- AC-002: With the isolation flag and a `--model` pin present, the script runs to completion and
  produces a result file whose isolation field states the mechanism applied.
- AC-003: With a recognized provider, `SKILL_EVAL_MODEL=<id>` set, no `--model` in the runner
  command and **no** `--allow-unisolated`, the script exits non-zero citing FR-005; no result file
  is written. With `--allow-unisolated` and an unrecognized runner, the same environment variable
  is accepted (see AC-004).
- AC-004: Under the FR-003 opt-out, the script runs and the result file's isolation field says the
  run was un-isolated, in terms a reviewer can act on.
- AC-005: An already-isolated, pinned runner produces byte-identical arm prompts and the same
  verdict as before the change, given the same responses (verified with the stubbed runner).
- AC-006: `evals/README.md` contains no *unqualified* claim that config contamination is unsolved.
  A narrowed, accurate caveat naming what genuinely remains satisfies this criterion; the current
  blanket "This is stated, not solved" does not. Its documented runner matches the one in
  `skill-eval.sh --help` and `CONTRIBUTING.md`.
- AC-007: `bash scripts/skill-eval.test.sh` passes and makes zero network calls.
- AC-008: `bash scripts/check-consistency.sh` passes.
- AC-009: An empirical check is recorded in DECISIONS stating whether `--setting-sources ""`
  excludes user-level `CLAUDE.md` on the pinned CLI version, with the observation that supports it
  (see Open questions Q1).
- AC-010: A `codex exec` runner missing `--ignore-user-config` or `--ephemeral` is rejected with
  the same hard error as the Claude Code path, naming the Codex-specific missing flag — not a
  generic message and not the opt-out path.
- AC-011: ~~The Codex flag set has been exercised against a real `codex exec` invocation... The
  feature does not reach `Done` on an unverified flag table.~~ **Downgraded 2026-08-07 (D011).**
  Replaced by: the unverified Codex flag table is recorded as DEBT-001 in `docs/KNOWN_DEBT.md`,
  named in the PR description, and surfaced in the refusal message itself (AC-012). Verification
  against a real CLI remains outstanding and is tracked there, not here.
- AC-012: A Codex runner refused for a missing isolation flag states that the flag set is
  unverified and names `--allow-unisolated` as the way past it, so the first operator with Codex
  installed can self-diagnose a wrong table instead of being hard-blocked by an error that sounds
  certain.

## Test scenarios

- **Unit:** flag detection against a table of runner strings, covering **both providers** —
  isolated, un-isolated, partially isolated, wrong-provider flags (Codex flags on `claude` and
  vice versa), quoted-flag-inside-prompt, wrapper command.
- **Integration:** `skill-eval.test.sh` end-to-end with the stubbed runner across all four gates
  (isolated pass, missing-isolation reject, missing-pin reject, opt-out downgrade), asserting exit
  codes and result-file content.
- **E2E:** not applicable — a real sweep costs tokens and is deliberately off the CI path.
- **Manual:** two runs that cannot be automated. (a) A real two-arm Claude Code run on a machine
  with a non-empty `~/.claude/CLAUDE.md`, to confirm the isolated invocation actually starts clean
  — evidence for AC-009. (b) A real `codex exec` invocation confirming the Codex flag set is
  accepted and does isolate — evidence for AC-011. (b) requires installing the Codex CLI, which
  is not present on the maintainer's current machine.

## Assumptions

- Claude Code's `--setting-sources ""` suppresses operator-level settings; whether it also
  suppresses user-level `CLAUDE.md` memory is version-dependent and is verified, not assumed
  (Q1).
- Codex isolation is `--ignore-user-config --ephemeral`, per the reviewed reference
  implementation. **Enforced from day one** (FR-001), but unverified at spec time: the Codex CLI
  is not installed on the maintainer's current machine, so FR-011 requires a real invocation
  before close. If the real flags differ, FR-001's table is corrected — the decision to cover
  Codex is not revisited.
- `--tools ""` is deliberately excluded. `evals/README.md:75-77` already establishes that
  disabling tools does not fix scenario grounding — it makes the model ask for a paste instead —
  and it would change what the arms measure.
- No existing committed result file needs regenerating; results are dated observations and stay
  valid as records of what was observed.
- Nothing in `evals/` is installed into user projects (`evals/README.md:5-6`), so this change
  cannot affect installed profiles.

## Open questions

- ~~**Q1 (verify during implementation, not blocking):** Does `--setting-sources ""` exclude
  user-level `CLAUDE.md`, or only `settings.json` sources?~~ **Resolved 2026-08-07 — it excludes
  user memory.** Measured on Claude Code 2.1.223 with a canary in `~/.claude/CLAUDE.md`: present in
  the response without the flag, absent with it, with the no-flag arm acting as the control that
  makes the result meaningful. FR-008 was written from the observation. See D007.
- ~~**Q2 (blocking — design):** hard error or loud warning?~~ **Resolved 2026-08-06 — hard
  error**, with the FR-003 opt-out as the only escape. Folded into FR-002.
- ~~**Q3 (scope):** ship Codex enforcement unverified, or route Codex through the opt-out?~~
  **Resolved 2026-08-06 — Codex is enforced on the same footing as Claude Code.** Codex is a
  first-class provider throughout this framework and is not treated as an exception. The
  unverified-flags risk is handled by FR-011 (verify before close) rather than by narrowing scope.
  **Amended 2026-08-07 (D011):** FR-011 was later downgraded, so that risk is no longer handled by
  a close gate — it ships as DEBT-001 in `docs/KNOWN_DEBT.md`, softened by FR-012. The decision to
  cover Codex is unchanged; only the gate on it was removed.

## Contracted services

`specs/SERVICES.md` does not exist → all billable add-ons treated as NOT contracted (conservative
default). Run `/project-init` to declare them. No billable add-on service (`seo-geo-addon` or
otherwise) is involved in this feature.
