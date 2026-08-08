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
# The runner must isolate the call from your own agent configuration and pin a
# model, or the run is refused before it costs anything. Without isolation the
# operator's plugins, hooks, memory and saved settings load into BOTH arms and
# two machines produce incomparable results; without a pin the recorded model is
# a claim about a run that may have used a different one.
#
#   claude:  --setting-sources '' --model <id>
#   codex:   --ignore-user-config --ephemeral --model <id>
#
# Usage: scripts/skill-eval.sh SKILL [--reps N] [--out FILE] [--allow-unisolated]
#
#   --allow-unisolated  permit a runner this script does not recognize (a
#                       wrapper script, an SDK shim). The run proceeds and the
#                       result file is stamped un-isolated with an
#                       operator-asserted model. It never exempts a recognized
#                       provider from its own flags.
#
# Environment:
#   SKILL_EVAL_RUNNER  command that reads a prompt on stdin and writes the
#                      response to stdout, e.g.
#                        export SKILL_EVAL_RUNNER="claude -p --setting-sources '' --model claude-sonnet-5"
#                      Unset: the script prints both arm prompts and stops.
#   SKILL_EVAL_MODEL   model identifier for the result file. For a recognized
#                      provider the '--model' pin in the runner is authoritative
#                      and this may only confirm it; disagreement is an error.
#                      Under --allow-unisolated it is the identifier of record.
#
# Exit codes: 0 = ran (whatever the verdict), 1 = usage/config error,
#             2 = runner failed.

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPS=5
OUT=""
SKILL=""
ALLOW_UNISOLATED=0

die() { echo "[ERROR] $*" >&2; exit 1; }

while [ $# -gt 0 ]; do
  case "$1" in
    --reps) REPS="${2:-}"; shift 2 ;;
    --out)  OUT="${2:-}"; shift 2 ;;
    --allow-unisolated) ALLOW_UNISOLATED=1; shift ;;
    # Keep this range in step with the header block above (ends at 'runner failed.').
    -h|--help) sed -n '3,43p' "$0"; exit 0 ;;
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

# --- runner inspection (spec 028) -------------------------------------------
# The runner string is already eval'd where it EXECUTES, so inspecting it must
# not add a second shell context (D005). xargs parses quotes without being a
# shell, which also means a flag name inside a quoted prompt fragment
# (-p 'use --model here') stays one token and is never mistaken for a real flag.
#
# xargs drops a TRAILING empty argument, so a sentinel is appended and stripped
# again: without it `--setting-sources ''` written last is invisible and a
# correctly isolated runner gets refused (D009).
RUNNER_EOL_SENTINEL='__SDD_RUNNER_EOL__'

runner_parses() {  # $1 = runner string; non-zero on an unmatched quote
  printf '%s %s' "$1" "$RUNNER_EOL_SENTINEL" | xargs -n1 >/dev/null 2>&1
}

runner_tokens() {  # $1 = runner string; one token per line, sentinel removed
  printf '%s %s' "$1" "$RUNNER_EOL_SENTINEL" | xargs -n1 2>/dev/null | sed '$d'
}

# The provider command, seeing past a leading `env` and its own arguments so
# that `env -u VAR /usr/local/bin/claude ...` still resolves to `claude`.
runner_provider() {  # $1 = runner string; prints the provider or returns 1
  local tok base in_env=0 skip=0
  while IFS= read -r tok; do
    if [ "$skip" = 1 ]; then skip=0; continue; fi
    [ -n "$tok" ] || continue
    # A leading `VAR=value` is a shell assignment prefix, not the command. The
    # runner is eval'd, so `FOO=1 claude --setting-sources '' ...` is valid and
    # genuinely isolated; reading `FOO=1` as the provider refused a clean runner
    # and offered only the downgrading opt-out as a way out (D010). The `[!-]`
    # keeps an option like `--model=x` out of this branch.
    case "$tok" in
      [!-]*=*) continue ;;
    esac
    if [ "$in_env" = 1 ]; then
      case "$tok" in
        -u) skip=1; continue ;;
        -*) continue ;;
      esac
    fi
    base="$(basename -- "$tok")"
    if [ "$base" = "env" ]; then in_env=1; continue; fi
    printf '%s\n' "$base"
    return 0
  done < <(runner_tokens "$1")
  return 1
}

runner_has_flag() {  # $1 runner, $2 flag
  runner_tokens "$1" | grep -Fxq -- "$2"
}

# $1 runner, $2 flag. Three outcomes, because "you forgot the flag" and "your
# flag carries a value" need different advice — emitting one message for both
# left the two cases indistinguishable to a reader and to a test.
#   0 = present with an empty value (isolated)
#   1 = present, but carries a value
#   2 = absent
runner_flag_is_empty() {
  local tok take=0
  while IFS= read -r tok; do
    if [ "$take" = 1 ]; then
      [ -z "$tok" ] && return 0
      return 1
    fi
    case "$tok" in
      "$2")   take=1 ;;
      "$2"=)  return 0 ;;
      "$2"=*) return 1 ;;
    esac
  done < <(runner_tokens "$1")
  # Present as the very last token with no value at all is a CLI error, not
  # isolation: fail closed, and report it as carrying no usable value.
  [ "$take" = 1 ] && return 1
  return 2
}

runner_flag_value() {  # $1 runner, $2 flag; prints the value, 1 if absent
  local tok take=0
  while IFS= read -r tok; do
    if [ "$take" = 1 ]; then printf '%s\n' "$tok"; return 0; fi
    case "$tok" in
      "$2")   take=1 ;;
      "$2"=*) printf '%s\n' "${tok#*=}"; return 0 ;;
    esac
  done < <(runner_tokens "$1")
  return 1
}

# Providers this script can vouch for. One row per provider:
#   name | required isolation flags (comma-separated) | pin flag | verified?
# A ':empty' suffix means the flag must be present AND carry an empty value.
# Adding a provider is a row, not a branch. Bash 3.2 (macOS) has no associative
# arrays, so this is a plain string parsed with `read`.
#
# The fourth field records whether the flag set has been checked against a REAL
# CLI, and only the exact string 'verified' counts — omit it, misspell it, or
# add a row without it and the provider hedges. 'claude' was measured on 2.1.223
# (spec 028, D007). 'codex' was taken from a reviewed external implementation and
# never run — see docs/KNOWN_DEBT.md. An unverified provider says so in its
# refusal, so a wrong table reads as this script's problem rather than the
# operator's. Whoever runs the real check flips this field.
PROVIDER_TABLE='claude|--setting-sources:empty|--model|verified
codex|--ignore-user-config,--ephemeral|--model|unverified'

provider_row() {  # $1 = provider name; prints its row or returns 1
  local row
  while IFS= read -r row; do
    [ -n "$row" ] || continue
    case "$row" in
      "$1"'|'*) printf '%s\n' "$row"; return 0 ;;
    esac
  done <<EOF
$PROVIDER_TABLE
EOF
  return 1
}

# --- model identity (FR-006: a result without a model id is not evidence) ---
RUNNER="${SKILL_EVAL_RUNNER:-}"
MODEL="${SKILL_EVAL_MODEL:-}"

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

Set a runner that reads a prompt on stdin and writes the response to stdout.
It must isolate the call from your own agent configuration and pin a model:

    export SKILL_EVAL_RUNNER="claude -p --setting-sources '' --model <model-id>"
    export SKILL_EVAL_RUNNER="codex exec --ignore-user-config --ephemeral --model <model-id>"

Then re-run. The two prompts that would be sent follow.

========================= CONTROL ARM PROMPT =========================
$(build_prompt control)
======================== TREATMENT ARM PROMPT ========================
$(build_prompt treatment)
======================================================================
EOF
  exit 0
fi

# --- isolation and pin gates (spec 028) -------------------------------------
# Both run BEFORE any model call. They fail closed: a warning would be read once
# and ignored, and the file it produced would be indistinguishable from one made
# under real isolation, which is the whole failure being removed here (D001).
runner_parses "$RUNNER" || die "cannot parse SKILL_EVAL_RUNNER — unmatched quote? Got: $RUNNER"

PROVIDER="$(runner_provider "$RUNNER" || true)"
PROVIDER_ROW="$(provider_row "$PROVIDER" || true)"

if [ -n "$PROVIDER_ROW" ]; then
  # A recognized provider is held to its flags whatever --allow-unisolated says:
  # the opt-out exists for runners this script cannot vouch for, not as a way to
  # switch the check off (D003).
  REQUIRED_FLAGS="$(printf '%s' "$PROVIDER_ROW" | cut -d'|' -f2)"
  PIN_FLAG="$(printf '%s' "$PROVIDER_ROW" | cut -d'|' -f3)"

  # An unverified flag set fails closed like any other, but the operator is told
  # the table itself may be wrong and given the way past it. Without this, the
  # first person with that CLI installed hits an authoritative-sounding block
  # with no route forward (FR-012).
  # Anything that is not literally 'verified' counts as unverified, so a row
  # added without the field hedges instead of silently claiming to be checked.
  # Every other gate here fails closed; this one must too — and it would fail
  # open in front of the one person guaranteed not to have verified anything yet,
  # the contributor adding the row.
  UNVERIFIED_NOTE=""
  if [ "$(printf '%s' "$PROVIDER_ROW" | cut -d'|' -f4)" != "verified" ]; then
    UNVERIFIED_NOTE="

NOTE: this flag set has NOT been checked against a real '$PROVIDER' CLI — see docs/KNOWN_DEBT.md. If '$PROVIDER' rejects these flags or spells them differently, the table above is wrong, not your runner. Pass --allow-unisolated to proceed, and please report the real flags."
  fi

  OLD_IFS="$IFS"; IFS=','
  for req in $REQUIRED_FLAGS; do
    IFS="$OLD_IFS"
    case "$req" in
      *:empty)
        flag="${req%:empty}"
        runner_flag_is_empty "$RUNNER" "$flag"
        case $? in
          0) ;;
          1) die \
"runner is not isolated: '$PROVIDER' has $flag, but it carries a value. Only an EMPTY value drops every source, so the operator's plugins, hooks, memory and saved model settings do not leak into both arms.

  got:      $RUNNER
  expected: $PROVIDER ... $flag '' ...

A narrowed source is still a source: results from two machines remain incomparable (evals/README.md).$UNVERIFIED_NOTE"
             ;;
          *) die \
"runner is not isolated: '$PROVIDER' requires $flag with an EMPTY value, so the operator's plugins, hooks, memory and saved model settings do not leak into both arms.

  got:      $RUNNER
  missing:  $flag ''

Without it, results from two machines are not comparable (evals/README.md). If '$PROVIDER' is not really the command being run, use --allow-unisolated.$UNVERIFIED_NOTE"
             ;;
        esac
        ;;
      *)
        runner_has_flag "$RUNNER" "$req" || die \
"runner is not isolated: '$PROVIDER' requires $req, so the operator's own configuration does not leak into both arms.

  got:      $RUNNER
  missing:  $req

Without it, results from two machines are not comparable (evals/README.md).$UNVERIFIED_NOTE"
        ;;
    esac
    IFS=','
  done
  IFS="$OLD_IFS"

  PINNED_MODEL="$(runner_flag_value "$RUNNER" "$PIN_FLAG" || true)"
  [ -n "$PINNED_MODEL" ] || die \
"runner does not pin a model: '$PROVIDER' requires $PIN_FLAG <id>.

  got: $RUNNER

SKILL_EVAL_MODEL alone is not enough for a recognized provider — the CLI would run whatever the operator's saved settings or the current release default to, while the result file recorded your claim instead. A model identifier that cannot be traced to the executed command is not evidence (FR-005)."

  if [ -n "$MODEL" ] && [ "$MODEL" != "$PINNED_MODEL" ]; then
    die "SKILL_EVAL_MODEL ('$MODEL') disagrees with the --model pin in SKILL_EVAL_RUNNER ('$PINNED_MODEL'). Refusing to guess which one describes the run; unset one of them."
  fi
  MODEL="$PINNED_MODEL"
  MODEL_SOURCE="pinned in the runner command"
  # Render the table's internal encoding as the flags an operator would type;
  # ':empty' and the comma separator are implementation detail, and this string
  # ends up in a committed artifact a reviewer reads.
  ISOLATION="\`$(printf '%s' "$REQUIRED_FLAGS" | sed "s/:empty/ ''/g; s/,/ /g")\` ($PROVIDER)"
elif [ "$ALLOW_UNISOLATED" = 1 ]; then
  # No command to derive a model from, so SKILL_EVAL_MODEL becomes the
  # identifier of record — recorded as asserted, never as verified (D004).
  [ -n "$MODEL" ] || die "cannot determine the model identifier — set SKILL_EVAL_MODEL. A result without a model identifier is not evidence (FR-006)."
  MODEL_SOURCE="operator-asserted (SKILL_EVAL_MODEL)"
  ISOLATION="**NONE — un-isolated run** (--allow-unisolated)"
else
  die \
"unrecognized runner '${PROVIDER:-?}' — this script cannot verify that it isolates the call from your agent configuration.

  got: $RUNNER

Known providers: $(printf '%s\n' "$PROVIDER_TABLE" | cut -d'|' -f1 | tr '\n' ' ')

Either use one of them with its isolation flags, or pass --allow-unisolated to run anyway. The opt-out is not free: the result file is stamped un-isolated with an operator-asserted model, which is a weaker artifact."
fi

# Printed before the token spend, so an un-isolated run is visible while it is
# still cheap to abort.
echo "isolation: $ISOLATION"
echo "model:     $MODEL — $MODEL_SOURCE"
echo

TODAY="$(date +%Y-%m-%d)"
[ -n "$OUT" ] || OUT="$REPO_ROOT/evals/results/${SKILL}-${TODAY}.md"

# Resolve OUT to a real absolute path before guarding it. A plain prefix test
# on the raw string is bypassed by any relative segment: `--out
# evals/../skills/x.md` slipped straight through and wrote inside skills/.
# Walk up to the nearest existing ancestor so a not-yet-created directory still
# resolves, then let `pwd -P` collapse `..` and symlinks.
resolve_path() {
  local target="$1" dir tail="" real
  dir="$(dirname "$target")"
  while [ ! -d "$dir" ] && [ "$dir" != "/" ] && [ "$dir" != "." ]; do
    tail="$(basename "$dir")/$tail"
    dir="$(dirname "$dir")"
  done
  # Fail CLOSED. This function runs inside a command substitution, so `die`
  # here would exit only the subshell — the script would carry on with an empty
  # OUT and report success while writing nowhere. Return non-zero instead and
  # let the caller stop. `cd` (not `-d`) is the check that can actually fail:
  # the dirname walk always terminates at `/` or `.`, which are always
  # directories, but either may be unenterable.
  if ! real="$(cd "$dir" 2>/dev/null && pwd -P)"; then
    echo "[ERROR] cannot resolve output path (directory not accessible): $target" >&2
    return 1
  fi
  printf '%s/%s%s\n' "$real" "$tail" "$(basename "$target")"
}

OUT="$(resolve_path "$OUT")" || exit 1
REPO_REAL="$(cd "$REPO_ROOT" && pwd -P)"
case "$OUT" in
  "$REPO_REAL"/skills/*) die "refusing to write inside skills/ — the harness never mutates a skill" ;;
esac
mkdir -p "$(dirname "$OUT")"

WORK="$(mktemp -d)"
SANDBOX="$WORK/sandbox"
mkdir -p "$SANDBOX"
trap 'rm -rf "$WORK"' EXIT

run_arm() {  # $1 = arm name; echoes the hit count
  local arm="$1" hits=0 i resp status
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
    # Grep once and reuse the result: matching twice let the printed status and
    # the tally diverge on a transient read error.
    status="clean"
    if grep -Eqi -- "$PATTERN" "$resp"; then
      hits=$(( hits + 1 ))
      status="FAILURE EXHIBITED"
    fi
    echo "  $arm rep $i/$REPS — $status" >&2
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
# HARMFUL is evaluated FIRST, even when the control arm never failed. A skill
# whose treatment arm exhibits a failure the control did not is the single most
# important thing this harness can surface; reporting it as merely
# "no baseline" buried exactly that signal on a real run.
if [ "$TREATMENT_HITS" -gt "$CONTROL_HITS" ]; then
  VERDICT="HARMFUL"
  VERDICT_NOTE="Treatment exhibited the failure MORE often than control (${TREATMENT_HITS} vs ${CONTROL_HITS}). Prohibition-form guidance applied to an output-shaping failure is the known way to land here — see evals/README.md."
  if [ "$CONTROL_HITS" -lt "$BASELINE_MIN" ]; then
    VERDICT_NOTE="$VERDICT_NOTE Note also that the control failed only ${CONTROL_HITS}/${REPS} times (below the ${BASELINE_MIN} baseline), so the scenario does not establish a problem for this skill to solve in the first place."
  fi
elif [ "$CONTROL_HITS" -lt "$BASELINE_MIN" ]; then
  VERDICT="NO-BASELINE-FAILURE"
  VERDICT_NOTE="The control exhibited the failure only ${CONTROL_HITS}/${REPS} times (needs ≥ ${BASELINE_MIN}). This skill has no demonstrated problem to solve; the treatment arm must NOT be read as a success."
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
  echo "| isolation | $ISOLATION |"
  echo "| model provenance | $MODEL_SOURCE |"
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
