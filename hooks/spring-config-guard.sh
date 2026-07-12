#!/usr/bin/env bash
# spring-config-guard.sh — Reminder hook (never blocks, never modifies files).
# After editing application*.yml or application*.properties, warns on:
# - Plaintext secrets in non-local profiles (reports FILE:LINE + key name only —
#   the matched value itself is NEVER printed, even in the systemMessage)
# - Actuator exposure in non-local profiles
# - debug=true in non-local profiles
# Exit 0 always.
#
# No external interpreter dependency. Both reading the incoming tool-call
# JSON (extracting tool_input.file_path) and emitting the systemMessage JSON
# go through the shared helper in lib/claude-json.sh (character-by-character
# escape/unescape, no pattern-substitution tricks), which every environment
# capable of running this script already has.

set -uo pipefail

source "$(dirname "${BASH_SOURCE[0]}")/lib/claude-json.sh"

INPUT="$(claude_json_read_stdin)"
FILE="$(claude_json_get_field "$INPUT" "file_path")"

if [ -z "$FILE" ]; then exit 0; fi
if ! echo "$FILE" | grep -qE 'application.*\.(yml|yaml|properties)$'; then exit 0; fi

# Skip local profile files — they're expected to have dev secrets
if echo "$FILE" | grep -qE 'application-(local|dev)\.'; then exit 0; fi

if [ ! -f "$FILE" ]; then exit 0; fi

WARNINGS=""

# --- Plaintext secret scan: report file/line/key only, never the value ---
SECRET_HITS=""
HIT_COUNT=0
while IFS= read -r matchline; do
  lineno="${matchline%%:*}"
  content="${matchline#*:}"
  key=$(printf '%s' "$content" | sed -E 's/^[[:space:]]*([A-Za-z0-9_.-]+).*/\1/')
  value=$(printf '%s' "$content" | sed -E 's/^[^:=]*[:=][[:space:]]*//')
  case "$value" in
    '${'*) continue ;;  # already externalized (env var / placeholder ref) — not a leak
  esac
  HIT_COUNT=$((HIT_COUNT + 1))
  if [ "$HIT_COUNT" -le 5 ]; then
    SECRET_HITS="${SECRET_HITS}${FILE}:${lineno} key='${key}'; "
  fi
done < <(grep -inE '(password|secret|token|api[_-]?key)[A-Za-z0-9_.-]*[[:space:]]*[:=][[:space:]]*[^${[:space:]]' "$FILE" 2>/dev/null)

if [ "$HIT_COUNT" -gt 0 ]; then
  EXTRA=""
  if [ "$HIT_COUNT" -gt 5 ]; then EXTRA=" (+$((HIT_COUNT - 5)) more)"; fi
  WARNINGS="${WARNINGS}Possible plaintext secret(s)  - value redacted, never printed  - at: ${SECRET_HITS}${EXTRA}Use Vault, env vars, or Spring Cloud Config for non-local profiles. "
fi

# Check for actuator full exposure
if grep -qE 'exposure\.include\s*[:=]\s*\*' "$FILE" 2>/dev/null; then
  WARNINGS="${WARNINGS}Actuator endpoints fully exposed (include=*). Restrict to health,info,prometheus in non-local profiles. "
fi

# Check for debug mode
if grep -qE '^debug\s*[:=]\s*true' "$FILE" 2>/dev/null; then
  WARNINGS="${WARNINGS}debug=true detected in a non-local profile. This exposes auto-configuration reports. "
fi

if [ -n "$WARNINGS" ]; then
  claude_json_emit_system_message "[Spring Config] ${WARNINGS}"
fi

exit 0
