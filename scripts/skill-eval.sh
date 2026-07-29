#!/usr/bin/env bash
#
# skill-eval.sh — measure whether a skill changes model behaviour.
#
# Runs one committed scenario through two arms:
#   control   = scenario only, no guidance
#   treatment = scenario + the skill's full SKILL.md
# N times each, tallies how often each arm exhibits the failure, and writes a
# dated result file.
#
# The control arm is mandatory and is the whole point: without it you are
# measuring whether a model can follow instructions, which was never in
# question. See evals/README.md and specs/features/022-skill-evidence-harness/.
#
# Usage: scripts/skill-eval.sh SKILL [--reps N] [--out FILE]
#
# Environment:
#   SKILL_EVAL_RUNNER  command that reads a prompt on stdin and writes the
#                      response to stdout, e.g.
#                        export SKILL_EVAL_RUNNER='claude -p --model claude-sonnet-5'
#                      Unset: the script prints both arm prompts and stops.
#   SKILL_EVAL_MODEL   model identifier for the result file. Optional when the
#                      runner string contains '--model <id>'.
#
# Exit codes: 0 = ran (whatever the verdict), 1 = usage/config error,
#             2 = runner failed.

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPS=5
OUT=""
SKILL=""

die() { echo "[ERROR] $*" >&2; exit 1; }

while [ $# -gt 0 ]; do
  case "$1" in
    --reps) REPS="${2:-}"; shift 2 ;;
    --out)  OUT="${2:-}"; shift 2 ;;
    -h|--help) sed -n '3,26p' "$0"; exit 0 ;;
    -*) die "unknown flag: $1" ;;
    *)  [ -z "$SKILL" ] || die "only one skill at a time (got '$SKILL' and '$1')"
        SKILL="$1"; shift ;;
  esac
done

[ -n "$SKILL" ] || die "usage: scripts/skill-eval.sh SKILL [--reps N] [--out FILE]"
case "$REPS" in (*[!0-9]*|"") die "--reps must be a positive integer, got '$REPS'" ;; esac
[ "$REPS" -ge 1 ] || die "--reps must be at least 1"

SKILL_MD="$REPO_ROOT/skills/$SKILL/SKILL.md"
SCENARIO="$REPO_ROOT/evals/scenarios/$SKILL.md"
[ -f "$SKILL_MD" ]  || die "no such skill: skills/$SKILL/SKILL.md"
[ -f "$SCENARIO" ]  || die "no scenario for '$SKILL' — expected evals/scenarios/$SKILL.md (see evals/README.md)"

# --- scenario parsing -------------------------------------------------------
# Sections are '## <name>' headings; body is everything up to the next '##'.
section() {
  awk -v want="$1" '
    /^## / { inside = (substr($0, 4) == want); next }
    inside { print }
  ' "$SCENARIO"
}

SYS_PROMPT="$(section "System prompt")"
USER_MSG="$(section "User message")"
PATTERN="$(section "Detection pattern" | grep -v '^[[:space:]]*$' | head -1)"

[ -n "$USER_MSG" ] || die "scenario is missing a '## User message' section: $SCENARIO"
[ -n "$PATTERN" ]  || die "scenario is missing a '## Detection pattern' section: $SCENARIO"

# --- model identity (FR-006: a result without a model id is not evidence) ---
RUNNER="${SKILL_EVAL_RUNNER:-}"
MODEL="${SKILL_EVAL_MODEL:-}"
if [ -z "$MODEL" ] && [ -n "$RUNNER" ]; then
  MODEL="$(printf '%s\n' "$RUNNER" | sed -n 's/.*--model[ =]\([^ ]*\).*/\1/p')"
fi

# --- prompts ----------------------------------------------------------------
build_prompt() {  # $1 = arm
  if [ "$1" = "treatment" ]; then
    printf '%s\n\n--- SKILL: %s ---\n%s\n--- END SKILL ---\n\n%s\n' \
      "$SYS_PROMPT" "$SKILL" "$(cat "$SKILL_MD")" "$USER_MSG"
  else
    printf '%s\n\n%s\n' "$SYS_PROMPT" "$USER_MSG"
  fi
}

TOTAL_CALLS=$(( REPS * 2 ))
echo "skill:     $SKILL"
echo "scenario:  evals/scenarios/$SKILL.md"
echo "arms:      control, treatment"
echo "reps:      $REPS each"
echo "calls:     $TOTAL_CALLS model call(s) — a full 9-skill sweep at this rep count is $(( REPS * 2 * 9 ))"
echo

if [ -z "$RUNNER" ]; then
  cat <<EOF
[SKILL_EVAL_RUNNER is unset — printing prompts instead of guessing a runner]

Set a runner that reads a prompt on stdin and writes the response to stdout:

    export SKILL_EVAL_RUNNER='claude -p --model <model-id>'

Then re-run. The two prompts that would be sent follow.

========================= CONTROL ARM PROMPT =========================
$(build_prompt control)
======================== TREATMENT ARM PROMPT ========================
$(build_prompt treatment)
======================================================================
EOF
  exit 0
fi

[ -n "$MODEL" ] || die "cannot determine the model identifier — set SKILL_EVAL_MODEL, or include '--model <id>' in SKILL_EVAL_RUNNER. A result without a model identifier is not evidence (FR-006)."

TODAY="$(date +%Y-%m-%d)"
[ -n "$OUT" ] || OUT="$REPO_ROOT/evals/results/${SKILL}-${TODAY}.md"
case "$OUT" in
  "$REPO_ROOT"/skills/*) die "refusing to write inside skills/ — the harness never mutates a skill" ;;
esac
mkdir -p "$(dirname "$OUT")"

WORK="$(mktemp -d)"
SANDBOX="$WORK/sandbox"
mkdir -p "$SANDBOX"
trap 'rm -rf "$WORK"' EXIT

run_arm() {  # $1 = arm name; echoes the hit count
  local arm="$1" hits=0 i resp
  for i in $(seq 1 "$REPS"); do
    resp="$WORK/$arm-$i.txt"
    # Run the model from an empty scratch directory, never from the repo.
    # A CLI runner inherits its working directory: run it here and the model
    # reads this repo's files and CLAUDE.md, then answers about THIS project
    # instead of the scenario ("src/utils/format.ts doesn't exist..."). That
    # contaminated an entire sweep before it was caught — see D009.
    if ! build_prompt "$arm" | ( cd "$SANDBOX" && eval "$RUNNER" ) > "$resp" 2>"$WORK/$arm-$i.err"; then
      echo "[ERROR] runner failed on $arm rep $i:" >&2
      head -5 "$WORK/$arm-$i.err" >&2
      return 2
    fi
    if grep -Eqi -- "$PATTERN" "$resp"; then
      hits=$(( hits + 1 ))
      printf '%s\n' "$i" >> "$WORK/$arm.hits"
    fi
    echo "  $arm rep $i/$REPS — $(if grep -Eqi -- "$PATTERN" "$resp"; then echo 'FAILURE EXHIBITED'; else echo 'clean'; fi)" >&2
  done
  echo "$hits"
}

echo "running control arm..." >&2
CONTROL_HITS="$(run_arm control)" || exit 2
echo "running treatment arm..." >&2
TREATMENT_HITS="$(run_arm treatment)" || exit 2

# --- verdict ----------------------------------------------------------------
# Thresholds mirror evals/README.md. A split treatment result is INCONCLUSIVE,
# never rounded up: when guidance lands, reps converge.
BASELINE_MIN=2
if [ "$CONTROL_HITS" -lt "$BASELINE_MIN" ]; then
  VERDICT="NO-BASELINE-FAILURE"
  VERDICT_NOTE="The control exhibited the failure only ${CONTROL_HITS}/${REPS} times (needs ≥ ${BASELINE_MIN}). This skill has no demonstrated problem to solve; the treatment arm must NOT be read as a success."
elif [ "$TREATMENT_HITS" -gt "$CONTROL_HITS" ]; then
  VERDICT="HARMFUL"
  VERDICT_NOTE="Treatment exhibited the failure MORE often than control (${TREATMENT_HITS} vs ${CONTROL_HITS}). Prohibition-form guidance applied to an output-shaping failure is the known way to land here — see evals/README.md."
elif [ "$TREATMENT_HITS" -eq 0 ]; then
  VERDICT="EFFECTIVE"
  VERDICT_NOTE="Control failed ${CONTROL_HITS}/${REPS}, treatment ${TREATMENT_HITS}/${REPS}."
elif [ "$TREATMENT_HITS" -ge "$CONTROL_HITS" ]; then
  VERDICT="INEFFECTIVE"
  VERDICT_NOTE="Treatment did not reduce the failure (${TREATMENT_HITS} vs control ${CONTROL_HITS})."
else
  VERDICT="INCONCLUSIVE"
  VERDICT_NOTE="Treatment reduced but did not eliminate the failure (${TREATMENT_HITS}/${REPS} vs control ${CONTROL_HITS}/${REPS}). Variance is itself the metric — do not round this up to a pass."
fi

# --- result file ------------------------------------------------------------
{
  echo "# Skill eval: $SKILL — $TODAY"
  echo
  echo "| Field | Value |"
  echo "|---|---|"
  echo "| skill | \`$SKILL\` |"
  echo "| scenario | \`evals/scenarios/$SKILL.md\` |"
  echo "| model | \`$MODEL\` |"
  echo "| runner | \`$RUNNER\` |"
  echo "| reps per arm | $REPS |"
  echo "| detection pattern | \`$PATTERN\` |"
  echo "| control — failure exhibited | ${CONTROL_HITS}/${REPS} |"
  echo "| treatment — failure exhibited | ${TREATMENT_HITS}/${REPS} |"
  echo "| **verdict** | **$VERDICT** |"
  echo "| manually-read | NO — set to YES only after reading every response below |"
  echo
  echo "$VERDICT_NOTE"
  echo
  echo "> Automated counts overstate both failure and success: template echoes and quoted"
  echo "> counter-examples masquerade as hits. This result is not evidence until every"
  echo "> response below has been read by hand and \`manually-read\` says so."
  echo
  echo "## Failure under test"
  echo
  section "Failure under test"
  echo "## Observable criterion"
  echo
  section "Observable criterion"
  for arm in control treatment; do
    echo "## Responses — $arm arm"
    echo
    for i in $(seq 1 "$REPS"); do
      echo "### $arm rep $i"
      echo
      echo '```'
      cat "$WORK/$arm-$i.txt"
      echo '```'
      echo
    done
  done
} > "$OUT"

echo
echo "control:   ${CONTROL_HITS}/${REPS} exhibited the failure"
echo "treatment: ${TREATMENT_HITS}/${REPS} exhibited the failure"
echo "verdict:   $VERDICT"
echo "written:   ${OUT#"$REPO_ROOT"/}"
echo
echo "Not evidence yet: read every response and set 'manually-read' to YES."
exit 0
