# Tasks: eval-runner-isolation

Boundary for every implementation task: `scripts/skill-eval.sh`, `scripts/skill-eval.test.sh`,
`evals/README.md`, `CONTRIBUTING.md`, and this feature folder. Nothing else.

## Phase 1: Preparation

- [x] T000 - **Do this before touching the script.** Capture the golden prompt fixture at `HEAD`:
  run the unset-runner print path (`SKILL_EVAL_RUNNER` unset) for one scenario and commit both arm
  prompts under the feature folder. T011's byte-identity assertion is worthless if the baseline is
  generated from the already-modified script. Covers: AC-005.
  → `fixtures/verifier-{control,treatment}.prompt.golden`, captured at `8764577` with
  `scripts/skill-eval.sh` verified identical to `HEAD`. Provenance and the T011 assertion contract
  are in `fixtures/README.md`.

- [x] T001 - Add the runner tokenizer and provider-detection helpers to `scripts/skill-eval.sh` as
  pure functions, not yet wired into any gate. Tokenize via `printf '%s' "$RUNNER" | xargs -n1`
  (never a second `eval`, per D005); detect the provider by skipping leading `env` /
  `VAR=value` / `-u VAR` arguments and taking `basename` of the first bare word. Unmatched quotes
  must fail, not fall through. Covers: AC-001, AC-010 (foundation).

- [x] T002 - Add the provider table as a newline-delimited constant parsed with `while read` — no
  associative arrays, Bash 3.2 must run it. Rows: `claude` requiring `--setting-sources` with an
  empty value and a `--model` pin; `codex` requiring `--ignore-user-config`, `--ephemeral`, and a
  `--model` pin. Covers: AC-001, AC-010.

## Phase 2: Implementation

- [x] T003 - Wire the isolation gate. Place it after the unset-runner print path
  (`skill-eval.sh:98-115`, which must still exit 0) and before the model-identity check at line
  117. Recognized provider missing a required token exits 1 naming the provider and the exact
  missing flag. Partial isolation (`--setting-sources project`) and wrong-provider flags (Codex
  flags on `claude`) are not isolation. Unrecognized runner exits 1 pointing at
  `--allow-unisolated`. Covers: AC-001, AC-010.

- [x] T004 - Add the `--allow-unisolated` CLI flag to the argument loop and its semantics: it
  permits an unrecognized runner and re-legalizes `$SKILL_EVAL_MODEL` as the identifier of record.
  It does not exempt a *recognized* provider from its flags — a `claude` runner missing
  `--setting-sources` is still refused (D003, D004). Covers: AC-004.

- [x] T005 - Replace the model-identity check at `skill-eval.sh:117` with the pin gate. For a
  recognized provider the identifier is read from `--model` in the command; a missing pin exits 1
  citing that an env-only identifier is an unverifiable claim; `$SKILL_EVAL_MODEL` disagreeing with
  the pin exits 1 rather than silently preferring either. Under `--allow-unisolated` the env
  variable is accepted and flagged as operator-asserted. Covers: AC-003.

- [x] T006 - Record isolation where a reviewer looks: one new row in the result-file table between
  `runner` and `reps per arm`, stating the mechanism applied or `NONE — un-isolated run`, plus the
  model provenance (command-pinned vs operator-asserted); and one new `isolation:` line in the
  pre-run summary printed before the token spend. Existing rows keep their names and order.
  Covers: AC-002, AC-004.

- [x] T007 - Update the in-script header (lines 3–26) to document `--allow-unisolated` and show an
  isolated, model-pinned example runner. **Update the `--help` range at `skill-eval.sh:41`
  (`sed -n '3,26p'`) to match the new header length** — editing one without the other silently
  truncates the help output. Covers: AC-006.

- [x] T008 - Update `CONTRIBUTING.md` (~line 58) so its documented runner is the isolated,
  pinned invocation and matches the script header verbatim. Covers: AC-006.

- [x] T009 - Rewrite the "Residual contamination that the sandbox does not remove" paragraph in
  `evals/README.md:142-146` to state what isolation now enforces and what genuinely remains, and
  update the runner in its "Running it" section. **Blocked on T012** — the honest wording depends
  on whether `--setting-sources ""` excludes user-level `CLAUDE.md`. Do not write this from an
  assumption. Covers: AC-006, AC-008.

## Phase 3: Tests

- [x] T010 - Extend `scripts/skill-eval.test.sh` with the gate cases, reusing the existing
  `assert_exit` / `assert_verdict` helpers: isolated claude passes; isolated codex passes; claude
  missing `--setting-sources` refused; codex missing `--ignore-user-config` refused with a
  Codex-specific message; partial `--setting-sources project` refused; Codex flags on `claude`
  refused; `--model` inside a quoted prompt fragment not counted as a pin; `env -u X
  /abs/path/claude` detected as `claude`; env-only identifier refused for a recognized provider;
  `$SKILL_EVAL_MODEL` disagreeing with the command pin refused rather than silently resolved; a
  shell-pipeline runner not accepted as isolated on the strength of its first word; opt-out runs
  and records the downgrade. Every existing case must keep passing — add `--allow-unisolated` to
  the stub invocations rather than weakening a gate. Zero network calls.
  Covers: AC-001, AC-002, AC-003, AC-004, AC-007, AC-010.

- [x] T011 - Add the regression assertions: both arm prompts byte-identical to pre-change output
  for an isolated runner, and the five verdict cases at `skill-eval.test.sh:184-198` producing
  unchanged verdicts and exit codes. Capture the prompt baseline **before** T001 edits the script
  — run the unset-runner print path at `HEAD` and commit the two prompts as a golden fixture —
  rather than regenerating it afterwards from the modified script, which would assert nothing.
  Covers: AC-005.

## Phase 4: Review

- [x] T012 - **Maintainer, not an agent.** Run one real two-arm Claude Code sweep from a machine
  with a non-empty `~/.claude/CLAUDE.md`, with and without `--setting-sources ""`, and record in
  `DECISIONS.md` (D007) whether user-level memory is excluded, with the observation that supports
  it. Unblocks T009. Covers: AC-009.
  → Done 2026-08-07 on CLI 2.1.223. `--setting-sources ''` DOES suppress user-level `CLAUDE.md`
  (canary present without the flag, absent with it). Recorded in D007.

- [~] T013 - **[DEFERRED 2026-08-07 — D011]** Install the Codex CLI and run one real `codex exec`
  invocation confirming `--ignore-user-config --ephemeral` are accepted and do isolate, plus the
  correct pin flag spelling. Record in `DECISIONS.md` (D008); correct the T002 table row if the
  real flags differ. ~~Covers: AC-011.~~
  → No longer blocks close. Tracked as **DEBT-001** in `docs/KNOWN_DEBT.md`. Still the only thing
  that would make the Codex row trustworthy; deferring it does not make it verified.

- [x] T017 - Add the unverified-flags caveat to the Codex refusal message: state that the flag set
  has not been checked against a real CLI and name `--allow-unisolated` as the way past it. Applies
  only to the `codex` provider — the Claude Code flags are verified (D007) and must not carry the
  same hedge. Add a test asserting the caveat appears for codex and does NOT appear for claude.
  Covers: AC-012.
  → Implemented as a fourth column in `PROVIDER_TABLE` (`verified`/`unverified`) rather than a
  hardcoded provider name, so closing DEBT-001 is flipping one field. Both directions pinned:
  flipping `claude` to `unverified` makes the negative test fail, so the assertion is not vacuous.

- [x] T018 - Close the `/spec-review` and `/qa-review` findings on the verified column: (a) a
  provider row that omits the fourth field currently defaults to **verified**, the one place in
  this feature that fails open — and it fails open on the very claim the feature polices, in front
  of the one person guaranteed not to have verified anything yet; (b) nothing pins that behaviour;
  (c) the refusal message cites `DEBT-001 in docs/KNOWN_DEBT.md`, a claim about repository contents
  that nothing keeps in step. Invert the test so anything that is not literally `verified` is
  treated as unverified, and pin both the three-field row and the referenced document.
  Covers: AC-012.
  → Condition inverted to `!= "verified"`. The hardcoded `DEBT-001` citation was dropped from the
  message rather than tested around: the ID belongs to one provider, the file is the stable
  pointer, so removing it eliminates the sync hazard instead of guarding it. Two cases added —
  a three-field row hedges, and the cited register exists and covers the unverified provider.
  Suite: 56 → 58.

- [x] T014 - Run `bash scripts/skill-eval.test.sh` and `bash scripts/check-consistency.sh`, then
  `/spec-review specs/features/028-eval-runner-isolation`. Covers: AC-007, AC-008.
  → 58 assertions passing, zero network calls; check-consistency green; four review cycles run
  (spec-review ×4, qa-review ×3), the last of each clean.

- [x] T016 - Close the `/qa-review` findings (2026-08-07) on the `fake_provider` tests: the three
  `PATH`-based cases assert only the `isolation:` line and the exit code, both of which a **real**
  CLI would satisfy, so if the fake bin directory were ever missing they would spend real API
  calls and still report PASS — contradicting the suite header's "No model is ever called".
  Assert the stub was the thing invoked, make `fake_provider` fail loudly instead of returning an
  empty path, and add the missing exit-status assertion to `assignment-prefix`.
  Covers: AC-007.
  → `assert_stub_ran` checks the stub's per-arm counter under `$TMP_BASE/state-<case>/`, which
  only exists if the stub answered. Proven by sabotage: forcing `fake_provider` to return an empty
  path made all three cases fail with "the run escaped to whatever PATH resolved to"; restored and
  green. Suite: 50 → 54 assertions.

- [x] T015 - Remediate the four findings from `/spec-review` and `/qa-review` (2026-08-07):
  (a) provider detection reads a bare `VAR=value` shell-assignment prefix as the command, so
  `FOO=1 claude --setting-sources '' --model m` — valid, isolated, and eval'd correctly — is
  falsely refused (D010); (b) "missing `--setting-sources`" and "`--setting-sources` with a
  non-empty value" emit a byte-identical error, so neither test discriminates; (c) the two
  happy-path tests discard the exit status and would pass even if the run failed after printing
  the isolation line; (d) the golden prompt test is built from the real `evals/scenarios/verifier.md`
  and `skills/verifier/SKILL.md`, so an edit to either fails it with "the gates must not change
  what is sent" — a wrong diagnosis that spec 023 is scheduled to trigger.
  Covers: AC-002, AC-005, AC-007.
  → (a) fixed via D010, both directions pinned; (b) distinct messages plus a mirror test that
  fails if they stop discriminating; (c) exit-status assertions on both happy paths; (d)
  `fixtures/inputs.sha256` guard — a changed scenario or SKILL.md now reports "goldens are stale",
  not "the gates changed prompts". Suite: 42 → 50 assertions.
