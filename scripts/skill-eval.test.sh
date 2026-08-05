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
  out="$(SKILL_EVAL_RUNNER="bash $stub" SKILL_EVAL_MODEL="stub-model" \
        bash "$dir/scripts/skill-eval.sh" "$FIXTURE_SKILL" --reps 5 2>/dev/null)"
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
  if [ -n "$needle" ] && ! grep -qF "$needle" <<< "$out"; then
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
  bash "$dir/scripts/skill-eval.sh" "$FIXTURE_SKILL"

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
  bash "$dir/scripts/skill-eval.sh" "$FIXTURE_SKILL" --out "$dir/skills/pwned.md"

dir="$(fresh_copy out-inside-skills-relative)"
stub="$(make_stub out-inside-skills-relative 0 0)"
assert_exit "--out reaching skills/ by relative path is refused" 1 "refusing to write inside skills/" \
  env SKILL_EVAL_RUNNER="bash $stub" SKILL_EVAL_MODEL="stub-model" \
  bash "$dir/scripts/skill-eval.sh" "$FIXTURE_SKILL" --out "$dir/evals/../skills/pwned.md"

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
    bash "$dir/scripts/skill-eval.sh" "$FIXTURE_SKILL" --out "$dir/locked/sub/r.md"
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
  bash "$dir/scripts/skill-eval.sh" "$FIXTURE_SKILL" --reps 5 >/dev/null 2>&1
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
  bash "$dir/scripts/skill-eval.sh" "$FIXTURE_SKILL" --reps 5 \
  --out "$dir/skills/$FIXTURE_SKILL/SKILL.md" >/dev/null 2>&1
after="$(find "$dir/skills" -name '*.md' -exec shasum {} + | shasum)"
if [ "$before" = "$after" ]; then
  record "skills/ is unchanged by a run" ok ""
else
  record "skills/ is unchanged by a run" notok "checksums differ"
fi

echo ""
echo "$PASS passed, $FAIL failed."
[ "$FAIL" -eq 0 ]
