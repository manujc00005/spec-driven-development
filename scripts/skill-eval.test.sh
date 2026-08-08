#!/usr/bin/env bash
#
# Self-test for scripts/skill-eval.sh. Copies the repo to a temp dir per case,
# installs a fixture scenario and a stub runner, and asserts the harness's exit
# code, verdict and refusals. No model is ever called.
#
# The stub distinguishes the two arms by the "--- SKILL:" marker that
# skill-eval.sh injects into the treatment prompt, and counts reps per arm, so a
# case can pin any control/treatment tally and therefore any verdict — including
# INCONCLUSIVE, which needs treatment strictly between zero and control.
#
# Usage: scripts/skill-eval.test.sh
# See specs/features/022-skill-evidence-harness/TASKS.md T014.

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP_BASE="$(mktemp -d)"
# Restore permissions before deleting: the unresolvable-output case creates a
# mode-000 directory, and an abort between chmod 000 and chmod 755 would leave
# a tree `rm -rf` cannot descend into.
trap 'chmod -R u+rwx "$TMP_BASE" 2>/dev/null; rm -rf "$TMP_BASE"' EXIT

PASS=0
FAIL=0

# The fixture skill is a real one (its SKILL.md is the treatment payload); only
# its scenario is replaced, so no skill directory has to be fabricated.
FIXTURE_SKILL="verifier"

fresh_copy() {
  # NOTE: every word of a `local` statement is expanded before any assignment
  # happens, so `local a="$1" b="$a"` leaves b empty (and trips `set -u`).
  # Keep these on separate lines.
  local case_name="$1"
  local dst="$TMP_BASE/$case_name"
  cp -r "$REPO_ROOT" "$dst"
  rm -rf "$dst/.git" "$dst/evals/results"
  mkdir -p "$dst/evals/results"
  cat > "$dst/evals/scenarios/$FIXTURE_SKILL.md" <<'EOF'
# Scenario: fixture

## Failure under test
Fixture failure, used only by the harness self-test.

## System prompt
You are a fixture.

## User message
Emit the fixture response.

## Observable criterion
The response contains the marker.

## Detection pattern
BOOM
EOF
  echo "$dst"
}

# Build a stub runner that emits the detection marker for the first N reps of
# each arm, so a case can pin any control/treatment tally — and therefore any
# verdict, including INCONCLUSIVE (treatment strictly between zero and control),
# which a per-arm stub cannot express.
#
# $1 = case name, $2 = control hits, $3 = treatment hits; echoes the stub's path
make_stub() {
  local case_name="$1"
  local control_hits="$2"
  local treat_hits="$3"
  local stub="$TMP_BASE/stub-$case_name.sh"
  local state="$TMP_BASE/state-$case_name"
  mkdir -p "$state"
  cat > "$stub" <<EOF
#!/usr/bin/env bash
input=\$(cat)
if grep -q -- "--- SKILL:" <<< "\$input"; then
  arm=treatment; limit=$treat_hits
else
  arm=control; limit=$control_hits
fi
counter="$state/\$arm"
n=\$(( \$(cat "\$counter" 2>/dev/null || echo 0) + 1 ))
echo "\$n" > "\$counter"
if [ "\$n" -le "\$limit" ]; then echo "BOOM"; else echo "fine"; fi
EOF
  chmod +x "$stub"
  echo "$stub"
}

record() {  # $1 = name, $2 = ok/notok, $3 = detail
  if [ "$2" = ok ]; then
    echo "[PASS] $1"
    PASS=$((PASS + 1))
  else
    echo "[FAIL] $1: $3"
    FAIL=$((FAIL + 1))
  fi
}

assert_verdict() {  # $1 name, $2 control hits, $3 treatment hits, $4 expected verdict
  local name="$1" dir out
  dir="$(fresh_copy "$name")"
  local stub
  stub="$(make_stub "$name" "$2" "$3")"
  # The stub is deliberately not a recognized provider, so every stubbed run
  # takes the --allow-unisolated path (spec 028, D004). Verdict logic is what is
  # under test here; the gates have their own cases below.
  out="$(SKILL_EVAL_RUNNER="bash $stub" SKILL_EVAL_MODEL="stub-model" \
        bash "$dir/scripts/skill-eval.sh" "$FIXTURE_SKILL" --reps 5 --allow-unisolated 2>/dev/null)"
  if grep -q "verdict:   $4" <<< "$out"; then
    record "$name" ok ""
  else
    record "$name" notok "expected verdict $4, got: $(grep 'verdict:' <<< "$out")"
  fi
}

assert_exit() {  # $1 name, $2 expected exit, $3 expected substring, then command...
  local name="$1" expect="$2" needle="$3"; shift 3
  local out actual
  out="$("$@" 2>&1)"
  actual=$?
  if [ "$actual" -ne "$expect" ]; then
    record "$name" notok "expected exit $expect, got $actual — $out"
    return
  fi
  # `--` before the pattern: a needle that starts with a dash (e.g. the
  # --allow-unisolated hint) is otherwise parsed as a grep option.
  if [ -n "$needle" ] && ! grep -qF -- "$needle" <<< "$out"; then
    record "$name" notok "expected output to contain '$needle' — $out"
    return
  fi
  record "$name" ok ""
}

# --- refusals ---------------------------------------------------------------

dir="$(fresh_copy unset-runner)"
assert_exit "unset-runner prints prompts, does not guess" 0 "CONTROL ARM PROMPT" \
  env -u SKILL_EVAL_RUNNER bash "$dir/scripts/skill-eval.sh" "$FIXTURE_SKILL"

dir="$(fresh_copy no-model)"
stub="$(make_stub no-model 0 0)"
assert_exit "runner without a model identifier is refused" 1 "model identifier" \
  env -u SKILL_EVAL_MODEL SKILL_EVAL_RUNNER="bash $stub" \
  bash "$dir/scripts/skill-eval.sh" "$FIXTURE_SKILL" --allow-unisolated

dir="$(fresh_copy missing-scenario)"
rm -f "$dir/evals/scenarios/$FIXTURE_SKILL.md"
assert_exit "missing scenario is refused" 1 "no scenario" \
  bash "$dir/scripts/skill-eval.sh" "$FIXTURE_SKILL"

dir="$(fresh_copy unknown-skill)"
assert_exit "unknown skill is refused" 1 "no such skill" \
  bash "$dir/scripts/skill-eval.sh" zzz-not-a-skill

# FR-003: the harness never mutates a skill.
dir="$(fresh_copy out-inside-skills)"
stub="$(make_stub out-inside-skills 0 0)"
assert_exit "--out inside skills/ is refused" 1 "refusing to write inside skills/" \
  env SKILL_EVAL_RUNNER="bash $stub" SKILL_EVAL_MODEL="stub-model" \
  bash "$dir/scripts/skill-eval.sh" "$FIXTURE_SKILL" --allow-unisolated --out "$dir/skills/pwned.md"

dir="$(fresh_copy out-inside-skills-relative)"
stub="$(make_stub out-inside-skills-relative 0 0)"
assert_exit "--out reaching skills/ by relative path is refused" 1 "refusing to write inside skills/" \
  env SKILL_EVAL_RUNNER="bash $stub" SKILL_EVAL_MODEL="stub-model" \
  bash "$dir/scripts/skill-eval.sh" "$FIXTURE_SKILL" --allow-unisolated --out "$dir/evals/../skills/pwned.md"

# An output path whose directory cannot be entered must fail CLOSED. The guard
# runs inside a command substitution, so an `exit` there would kill only the
# subshell and leave the script running with an empty OUT.
if [ "$(id -u)" -eq 0 ]; then
  echo "[SKIP] unreadable output directory fails closed (running as root)"
else
  dir="$(fresh_copy unresolvable-out)"
  stub="$(make_stub unresolvable-out 0 0)"
  mkdir -p "$dir/locked"
  chmod 000 "$dir/locked"
  assert_exit "unresolvable output directory fails closed" 1 "cannot resolve output path" \
    env SKILL_EVAL_RUNNER="bash $stub" SKILL_EVAL_MODEL="stub-model" \
    bash "$dir/scripts/skill-eval.sh" "$FIXTURE_SKILL" --allow-unisolated --out "$dir/locked/sub/r.md"
  chmod 755 "$dir/locked"
fi

# --- verdicts ---------------------------------------------------------------

# Control never fails -> no baseline, whatever the treatment arm did.
assert_verdict no-baseline-failure 0 0 "NO-BASELINE-FAILURE"

# Treatment fails MORE than control: the signal the feature exists to surface.
# Must outrank NO-BASELINE-FAILURE even when the control arm is clean (T016).
assert_verdict harmful-outranks-no-baseline 0 5 "HARMFUL"

# Control fails, treatment does not.
assert_verdict effective 5 0 "EFFECTIVE"

# Both fail equally.
assert_verdict ineffective 5 5 "INEFFECTIVE"

# Treatment reduced the failure but did not eliminate it: the verdict the SPEC
# discusses most, and the one a per-arm stub could not express.
assert_verdict inconclusive 5 2 "INCONCLUSIVE"

# --- result file contract (FR-006) -----------------------------------------

dir="$(fresh_copy result-file)"
stub="$(make_stub result-file 5 0)"
SKILL_EVAL_RUNNER="bash $stub" SKILL_EVAL_MODEL="stub-model" \
  bash "$dir/scripts/skill-eval.sh" "$FIXTURE_SKILL" --reps 5 --allow-unisolated >/dev/null 2>&1
result="$(find "$dir/evals/results" -name "$FIXTURE_SKILL-*.md" | head -1)"
if [ -z "$result" ]; then
  record "result file is written" notok "no result file under evals/results/"
else
  record "result file is written" ok ""
  for needle in "stub-model" "control — failure exhibited | 5/5" \
                "treatment — failure exhibited | 0/5" "manually-read" \
                "### control rep 5" "### treatment rep 5"; do
    if grep -qF "$needle" "$result"; then
      record "result file contains '$needle'" ok ""
    else
      record "result file contains '$needle'" notok "missing from $result"
    fi
  done
fi

# The harness must not have touched any skill — asserted against a run that
# actively TRIES to write into skills/. Checksumming a default run proves
# nothing: its output goes to evals/results/ whether or not a guard exists.
dir="$(fresh_copy no-skill-mutation)"
stub="$(make_stub no-skill-mutation 5 0)"
before="$(find "$dir/skills" -name '*.md' -exec shasum {} + | shasum)"
SKILL_EVAL_RUNNER="bash $stub" SKILL_EVAL_MODEL="stub-model" \
  bash "$dir/scripts/skill-eval.sh" "$FIXTURE_SKILL" --reps 5 --allow-unisolated \
  --out "$dir/skills/$FIXTURE_SKILL/SKILL.md" >/dev/null 2>&1
after="$(find "$dir/skills" -name '*.md' -exec shasum {} + | shasum)"
if [ "$before" = "$after" ]; then
  record "skills/ is unchanged by a run" ok ""
else
  record "skills/ is unchanged by a run" notok "checksums differ"
fi

# --- isolation and pin gates (spec 028) -------------------------------------
# Every case below is refused before any model call, so the whole section is
# free. The stub is only needed where a run is expected to proceed.

# Put a stub on PATH under a recognized provider's name, so the happy path can
# be exercised without calling a real CLI.
fake_provider() {  # $1 = case name, $2 = provider name; echoes the bin dir
  local case_name="$1"
  local provider="$2"
  local bin="$TMP_BASE/bin-$case_name"
  local stub
  stub="$(make_stub "$case_name" 0 0)"
  mkdir -p "$bin"
  cp "$stub" "$bin/$provider"
  chmod +x "$bin/$provider"
  # Runs inside a command substitution, so this cannot abort the suite — it only
  # makes the cause legible. assert_stub_ran below is the actual enforcement.
  [ -x "$bin/$provider" ] || echo "[WARN] fake provider not executable: $bin/$provider" >&2
  echo "$bin"
}

# The stub records a per-arm counter under $TMP_BASE/state-<case>/. Its absence
# means something OTHER than the stub answered the prompt.
#
# This matters because the PATH-based cases assert the `isolation:` line and the
# exit code, and a real CLI satisfies both: the isolation line is printed from
# parsing the runner string, and a real run of this scenario emits no detection
# marker, giving 0 hits and exit 0. On a machine with a real `claude` on PATH —
# which is the normal case — an empty $bin would degrade `PATH="$bin:$PATH"` to
# `":$PATH"`, fall through to the real binary, spend real API calls, and still
# report PASS. The suite header promises no model is ever called; this is what
# enforces it.
assert_stub_ran() {  # $1 = case name
  local name="$1: the stub answered, not a real CLI"
  if [ -f "$TMP_BASE/state-$1/control" ]; then
    record "$name" ok ""
  else
    record "$name" notok \
      "no counter at $TMP_BASE/state-$1/control — the run escaped to whatever PATH resolved to"
  fi
}

# AC-001 — a recognized provider without its isolation flag is refused, and the
# error names the flag rather than complaining generically.
dir="$(fresh_copy iso-claude-missing)"
assert_exit "claude without --setting-sources is refused" 1 "requires --setting-sources" \
  env SKILL_EVAL_RUNNER="claude -p --model m" \
  bash "$dir/scripts/skill-eval.sh" "$FIXTURE_SKILL"

# Partial isolation is not isolation: the flag is present but carries a value.
# The needle must be the phrase unique to THIS case — both refusals used to emit
# a byte-identical message, so either test passed against the other's input.
dir="$(fresh_copy iso-claude-partial)"
assert_exit "--setting-sources with a non-empty value is refused" 1 "carries a value" \
  env SKILL_EVAL_RUNNER="claude -p --setting-sources project --model m" \
  bash "$dir/scripts/skill-eval.sh" "$FIXTURE_SKILL"

# The mirror of the case above: absent must NOT report "carries a value".
dir="$(fresh_copy iso-claude-absent-not-valued)"
out="$(env SKILL_EVAL_RUNNER="claude -p --model m" \
       bash "$dir/scripts/skill-eval.sh" "$FIXTURE_SKILL" 2>&1)"
if grep -qF "carries a value" <<< "$out"; then
  record "a missing flag is not reported as carrying a value" notok "messages do not discriminate: $out"
else
  record "a missing flag is not reported as carrying a value" ok ""
fi

# A bare `VAR=value` prefix is a shell assignment, not the command. The runner is
# eval'd, so this one is genuinely isolated and must reach the run (D010).
dir="$(fresh_copy assignment-prefix)"
bin="$(fake_provider assignment-prefix claude)"
out="$(PATH="$bin:$PATH" SKILL_EVAL_RUNNER="FOO=1 claude -p --setting-sources '' --model pinned-model" \
      bash "$dir/scripts/skill-eval.sh" "$FIXTURE_SKILL" --reps 1 2>&1)"
status=$?
if [ "$status" -eq 0 ]; then
  record "VAR=value prefixed runner exits 0" ok ""
else
  record "VAR=value prefixed runner exits 0" notok "exit $status — $out"
fi
if grep -qF "isolation: \`--setting-sources ''\` (claude)" <<< "$out"; then
  record "a VAR=value prefix does not hide the provider" ok ""
else
  record "a VAR=value prefix does not hide the provider" notok "got: $(grep -iE 'isolation|ERROR' <<< "$out" | head -1)"
fi
assert_stub_ran assignment-prefix

# ...but an option carrying '=' is not an assignment prefix and must not be
# skipped, or `--model=x claude` would silently resolve to a provider.
dir="$(fresh_copy eq-option-not-assignment)"
assert_exit "an --opt=value token is not treated as an assignment" 1 "unrecognized runner '--model=x'" \
  env SKILL_EVAL_RUNNER="--model=x claude" \
  bash "$dir/scripts/skill-eval.sh" "$FIXTURE_SKILL"

# The opt-out cannot rescue a runner that cannot be tokenized at all: there is
# nothing to inspect, so the refusal stands.
dir="$(fresh_copy optout-unparseable)"
assert_exit "--allow-unisolated does not rescue an unparseable runner" 1 "cannot parse SKILL_EVAL_RUNNER" \
  env SKILL_EVAL_RUNNER="claude --model 'unterminated" SKILL_EVAL_MODEL="m" \
  bash "$dir/scripts/skill-eval.sh" "$FIXTURE_SKILL" --allow-unisolated

# A pin flag left dangling with no value is a CLI error, not a pin.
dir="$(fresh_copy dangling-pin)"
assert_exit "a --model with no value is not a pin" 1 "does not pin a model" \
  env SKILL_EVAL_RUNNER="claude --setting-sources '' --model" \
  bash "$dir/scripts/skill-eval.sh" "$FIXTURE_SKILL"

# AC-010 — Codex is enforced on the same footing (D002), with a Codex-specific
# message rather than the generic unrecognized-runner one.
dir="$(fresh_copy iso-codex-missing)"
assert_exit "codex without --ignore-user-config is refused" 1 "requires --ignore-user-config" \
  env SKILL_EVAL_RUNNER="codex exec --ephemeral --model m" \
  bash "$dir/scripts/skill-eval.sh" "$FIXTURE_SKILL"

dir="$(fresh_copy iso-codex-missing-ephemeral)"
assert_exit "codex without --ephemeral is refused" 1 "requires --ephemeral" \
  env SKILL_EVAL_RUNNER="codex exec --ignore-user-config --model m" \
  bash "$dir/scripts/skill-eval.sh" "$FIXTURE_SKILL"

# AC-012 — the Codex table ships unverified (DEBT-001), so its refusal must say
# so and name the way past it. Otherwise the first operator with Codex installed
# hits an authoritative-sounding block over flags nobody ever checked.
dir="$(fresh_copy codex-unverified-caveat)"
assert_exit "codex refusal admits the flag set is unverified" 1 "has NOT been checked against a real 'codex' CLI" \
  env SKILL_EVAL_RUNNER="codex exec --ephemeral --model m" \
  bash "$dir/scripts/skill-eval.sh" "$FIXTURE_SKILL"

# ...and the verified provider must NOT carry the same hedge. Claude Code's
# flags were measured (D007); hedging them would understate what is known.
dir="$(fresh_copy claude-no-unverified-caveat)"
out="$(env SKILL_EVAL_RUNNER="claude -p --model m" \
       bash "$dir/scripts/skill-eval.sh" "$FIXTURE_SKILL" 2>&1)"
if grep -qF "has NOT been checked" <<< "$out"; then
  record "claude refusal does not carry the unverified caveat" notok \
    "a verified provider must not hedge its own flags: $out"
else
  record "claude refusal does not carry the unverified caveat" ok ""
fi

# A row added WITHOUT the verified field must hedge, not claim to be checked.
# Only the literal 'verified' counts. This is the one place in the feature that
# could fail open, and it would do so in front of the contributor adding the
# row — the one person guaranteed not to have verified anything yet.
dir="$(fresh_copy provider-row-missing-field)"
sed -i.bak "s|^codex|newprov\|--some-flag\|--model\ncodex|" "$dir/scripts/skill-eval.sh"
assert_exit "a provider row with no verified field is treated as unverified" 1 "has NOT been checked against a real 'newprov' CLI" \
  env SKILL_EVAL_RUNNER="newprov --model m" \
  bash "$dir/scripts/skill-eval.sh" "$FIXTURE_SKILL"

# The refusal points the operator at a document. Nothing else keeps that pointer
# honest: rename the file and the harness sends a blocked user to a dead path at
# the moment they are already stuck.
if [ -f "$REPO_ROOT/docs/KNOWN_DEBT.md" ] && grep -qF "codex" "$REPO_ROOT/docs/KNOWN_DEBT.md"; then
  record "the debt register cited by the refusal exists and covers codex" ok ""
else
  record "the debt register cited by the refusal exists and covers codex" notok \
    "skill-eval.sh points operators at docs/KNOWN_DEBT.md — it must exist and document the unverified provider"
fi

# One provider's flags do not isolate another's process.
dir="$(fresh_copy iso-wrong-provider)"
assert_exit "codex flags on claude are not isolation" 1 "requires --setting-sources" \
  env SKILL_EVAL_RUNNER="claude --ignore-user-config --ephemeral --model m" \
  bash "$dir/scripts/skill-eval.sh" "$FIXTURE_SKILL"

# An unrecognized runner is refused rather than assumed clean, and the error
# points at the opt-out instead of leaving the operator stuck.
dir="$(fresh_copy iso-unknown)"
stub="$(make_stub iso-unknown 0 0)"
assert_exit "unrecognized runner is refused without the opt-out" 1 "--allow-unisolated" \
  env SKILL_EVAL_RUNNER="bash $stub" SKILL_EVAL_MODEL="stub-model" \
  bash "$dir/scripts/skill-eval.sh" "$FIXTURE_SKILL"

# The opt-out covers runners the script cannot vouch for — never a recognized
# provider dodging its own flags (D003).
dir="$(fresh_copy iso-optout-not-an-exemption)"
assert_exit "--allow-unisolated does not exempt a recognized provider" 1 "requires --setting-sources" \
  env SKILL_EVAL_RUNNER="claude -p --model m" \
  bash "$dir/scripts/skill-eval.sh" "$FIXTURE_SKILL" --allow-unisolated

# AC-003 — for a recognized provider the identifier must come from the command.
dir="$(fresh_copy pin-missing)"
assert_exit "recognized provider without a --model pin is refused" 1 "does not pin a model" \
  env SKILL_EVAL_RUNNER="claude -p --setting-sources ''" SKILL_EVAL_MODEL="claimed-model" \
  bash "$dir/scripts/skill-eval.sh" "$FIXTURE_SKILL"

# Two sources of truth that disagree are an error, not a silent preference.
dir="$(fresh_copy pin-disagreement)"
assert_exit "SKILL_EVAL_MODEL disagreeing with the pin is refused" 1 "disagrees with the --model pin" \
  env SKILL_EVAL_RUNNER="claude --setting-sources '' --model actual" SKILL_EVAL_MODEL="claimed" \
  bash "$dir/scripts/skill-eval.sh" "$FIXTURE_SKILL"

# A flag name inside a quoted prompt fragment is one token, not a flag. Without
# tokenization a substring match would read this as both isolated and pinned.
dir="$(fresh_copy quoted-flag)"
assert_exit "a flag inside a quoted argument is not a real flag" 1 "requires --setting-sources" \
  env SKILL_EVAL_RUNNER="claude -p 'mention --setting-sources and --model here'" \
  bash "$dir/scripts/skill-eval.sh" "$FIXTURE_SKILL"

# An unmatched quote cannot be tokenized, so it is refused rather than guessed at.
dir="$(fresh_copy unparseable-runner)"
assert_exit "an unparseable runner is refused" 1 "cannot parse SKILL_EVAL_RUNNER" \
  env SKILL_EVAL_RUNNER="claude --model 'unterminated" \
  bash "$dir/scripts/skill-eval.sh" "$FIXTURE_SKILL"

# Provider detection sees past `env` and an absolute path, so wrapping a runner
# does not accidentally buy an exemption.
dir="$(fresh_copy provider-behind-env)"
assert_exit "provider is detected behind env and an absolute path" 1 "requires --setting-sources" \
  env SKILL_EVAL_RUNNER="env -u FOO BAR=1 /usr/local/bin/claude -p --model m" \
  bash "$dir/scripts/skill-eval.sh" "$FIXTURE_SKILL"

# AC-002 — the isolated, pinned happy path runs and records the mechanism.
dir="$(fresh_copy iso-happy)"
bin="$(fake_provider iso-happy claude)"
out="$(PATH="$bin:$PATH" SKILL_EVAL_RUNNER="claude -p --setting-sources '' --model pinned-model" \
      bash "$dir/scripts/skill-eval.sh" "$FIXTURE_SKILL" --reps 1 2>&1)"
status=$?
# The isolation line prints before the arms run, so grepping for it proves
# nothing about whether the run survived. Assert the exit code too.
if [ "$status" -eq 0 ]; then
  record "isolated+pinned runner exits 0" ok ""
else
  record "isolated+pinned runner exits 0" notok "exit $status — $out"
fi
if grep -qF "isolation: \`--setting-sources ''\` (claude)" <<< "$out"; then
  record "isolated+pinned runner reports its isolation mechanism" ok ""
else
  record "isolated+pinned runner reports its isolation mechanism" notok "got: $(grep -i isolation <<< "$out")"
fi
if grep -qF "pinned-model — pinned in the runner command" <<< "$out"; then
  record "isolated run takes its model from the command" ok ""
else
  record "isolated run takes its model from the command" notok "got: $(grep -i '^model' <<< "$out")"
fi
assert_stub_ran iso-happy

# AC-010 — Codex reaches the same happy path as Claude Code, not a lesser one.
dir="$(fresh_copy iso-codex-happy)"
bin="$(fake_provider iso-codex-happy codex)"
out="$(PATH="$bin:$PATH" \
      SKILL_EVAL_RUNNER="codex exec --ignore-user-config --ephemeral --model codex-model" \
      bash "$dir/scripts/skill-eval.sh" "$FIXTURE_SKILL" --reps 1 2>&1)"
status=$?
if [ "$status" -eq 0 ]; then
  record "isolated codex runner exits 0" ok ""
else
  record "isolated codex runner exits 0" notok "exit $status — $out"
fi
if grep -qF "isolation: \`--ignore-user-config --ephemeral\` (codex)" <<< "$out"; then
  record "isolated codex runner reports its isolation mechanism" ok ""
else
  record "isolated codex runner reports its isolation mechanism" notok "got: $(grep -i isolation <<< "$out")"
fi
assert_stub_ran iso-codex-happy

# A provider name appearing later in a pipeline does not make the pipeline
# isolated: what runs first is what receives the prompt on stdin.
dir="$(fresh_copy pipeline-runner)"
assert_exit "a provider later in a pipeline does not count" 1 "unrecognized runner 'echo'" \
  env SKILL_EVAL_RUNNER="echo hi | claude -p --setting-sources '' --model m" \
  bash "$dir/scripts/skill-eval.sh" "$FIXTURE_SKILL"

# D009 — xargs drops a trailing empty argument, so the isolation flag written
# last must still be seen. This is the most natural way to write the runner.
dir="$(fresh_copy iso-trailing-empty)"
bin="$(fake_provider iso-trailing-empty claude)"
out="$(PATH="$bin:$PATH" SKILL_EVAL_RUNNER="claude -p --model pinned-model --setting-sources ''" \
      bash "$dir/scripts/skill-eval.sh" "$FIXTURE_SKILL" --reps 1 2>&1)"
if grep -qF "isolation: \`--setting-sources ''\` (claude)" <<< "$out"; then
  record "isolation flag written last is still detected" ok ""
else
  record "isolation flag written last is still detected" notok "got: $(grep -i isolation <<< "$out")"
fi

# AC-004 — the opt-out downgrades the artifact instead of exempting it. An
# un-isolated result must be legible as such without trusting the operator.
dir="$(fresh_copy optout-downgrade)"
stub="$(make_stub optout-downgrade 5 0)"
SKILL_EVAL_RUNNER="bash $stub" SKILL_EVAL_MODEL="asserted-model" \
  bash "$dir/scripts/skill-eval.sh" "$FIXTURE_SKILL" --reps 1 --allow-unisolated >/dev/null 2>&1
result="$(find "$dir/evals/results" -name "$FIXTURE_SKILL-*.md" | head -1)"
if [ -z "$result" ]; then
  record "opt-out run writes a result file" notok "no result file under evals/results/"
else
  record "opt-out run writes a result file" ok ""
  for needle in "| isolation | **NONE — un-isolated run** (--allow-unisolated) |" \
                "| model provenance | operator-asserted (SKILL_EVAL_MODEL) |"; do
    if grep -qF "$needle" "$result"; then
      record "un-isolated result records '$needle'" ok ""
    else
      record "un-isolated result records '$needle'" notok "missing from $result"
    fi
  done
fi

# --- prompt invariance (spec 028, AC-005) -----------------------------------
# FR-010: the gates change what is allowed to RUN, never what is SENT. Compared
# against fixtures captured at 8764577, before the script was touched.
#
# Run against the real repo, not a fresh_copy: the goldens were captured from
# the real evals/scenarios/verifier.md, which fresh_copy replaces. The
# unset-runner path writes nothing, so this is side-effect free.
GOLDEN_DIR="$REPO_ROOT/specs/features/028-eval-runner-isolation/fixtures"

# The prompts are assembled from evals/scenarios/verifier.md and
# skills/verifier/SKILL.md, which this feature does not own. Check them first:
# without this, editing either file fails the comparison below with "the gates
# must not change what is sent" — a wrong diagnosis, and one spec 023 is
# scheduled to trigger when it replaces the scenario corpus.
if (cd "$REPO_ROOT" && shasum -a 256 -c "$GOLDEN_DIR/inputs.sha256" >/dev/null 2>&1); then
  record "golden inputs are unchanged" ok ""
  golden_inputs_ok=1
else
  record "golden inputs are unchanged" notok \
    "evals/scenarios/$FIXTURE_SKILL.md or skills/$FIXTURE_SKILL/SKILL.md changed — the goldens are stale, not the gates. Regenerate them per $GOLDEN_DIR/README.md and update inputs.sha256."
  golden_inputs_ok=0
fi

golden_out="$(env -u SKILL_EVAL_RUNNER -u SKILL_EVAL_MODEL \
              bash "$REPO_ROOT/scripts/skill-eval.sh" "$FIXTURE_SKILL" 2>/dev/null)"

# Locate the banners rather than hardcoding offsets — the pre-run summary gained
# an 'isolation:' line, which shifts every line number.
extract_control()   { awk '/^=+ CONTROL ARM PROMPT =+$/{f=1;next} /^=+ TREATMENT ARM PROMPT =+$/{f=0} f'; }
extract_treatment() { awk '/^=+ TREATMENT ARM PROMPT =+$/{f=1;next} /^=+$/{f=0} f'; }

for arm in control treatment; do
  golden="$GOLDEN_DIR/$FIXTURE_SKILL-$arm.prompt.golden"
  if [ ! -f "$golden" ]; then
    record "$arm prompt matches the pre-change golden" notok "missing fixture: $golden"
    continue
  fi
  if diff -q <(printf '%s\n' "$golden_out" | "extract_$arm") "$golden" >/dev/null 2>&1; then
    record "$arm prompt matches the pre-change golden" ok ""
  elif [ "$golden_inputs_ok" -eq 0 ]; then
    record "$arm prompt matches the pre-change golden" notok \
      "golden is stale (its inputs changed) — regenerate before reading this as a gate regression"
  else
    record "$arm prompt matches the pre-change golden" notok \
      "inputs are unchanged, so the script changed what it sends — the gates must not do that (FR-010)"
  fi
done

echo ""
echo "$PASS passed, $FAIL failed."
[ "$FAIL" -eq 0 ]
