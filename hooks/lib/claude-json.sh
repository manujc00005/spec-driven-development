#!/usr/bin/env bash
# claude-json.sh — Shared, dependency-free JSON helpers for Claude Code hooks.
# Source this file from a hook script; it is not meant to be executed directly.
#
# No jq. No python3. Every hook that reads the tool-call payload on stdin or
# emits a systemMessage back to Claude Code should go through these functions
# instead of duplicating ad-hoc parsing/escaping.
#
# Scope note: this is deliberately not a general JSON parser. Claude Code's
# tool-call payload is a flat, single-line JSON object whose fields of
# interest (tool_input.file_path, tool_input.command, tool_response.filePath)
# are simple top-level string values, so a bounded regex + manual
# escape/unescape is sufficient. On malformed or unexpected input, every
# function below returns an empty string rather than erroring — callers are
# expected to no-op (exit 0) when the field they need comes back empty.

# --- JSON string escape/unescape (character-by-character, no pattern-substitution) ---

# Raw text -> JSON string content (caller adds the surrounding quotes).
claude_json_escape() {
  local input="$1"
  local out="" c
  local i len
  len=${#input}
  for (( i=0; i<len; i++ )); do
    c="${input:i:1}"
    case "$c" in
      "\\") out+="\\\\" ;;
      "\"") out+="\\\"" ;;
      $'\n') out+="\\n" ;;
      $'\t') out+="\\t" ;;
      $'\r') out+="\\r" ;;
      *) out+="$c" ;;
    esac
  done
  printf '%s' "$out"
}

# JSON string content (no surrounding quotes) -> raw text.
# Unknown escapes pass the backslash through unchanged rather than failing —
# safe for a file path that then simply won't resolve to a real file (the
# caller no-ops on a missing file).
claude_json_unescape() {
  local input="$1"
  local out="" c next
  local i len
  len=${#input}
  i=0
  while (( i < len )); do
    c="${input:i:1}"
    if [ "$c" = "\\" ]; then
      next="${input:i+1:1}"
      case "$next" in
        "\\") out+="\\"; i=$((i + 2)) ;;
        "\"") out+="\""; i=$((i + 2)) ;;
        n) out+=$'\n'; i=$((i + 2)) ;;
        t) out+=$'\t'; i=$((i + 2)) ;;
        r) out+=$'\r'; i=$((i + 2)) ;;
        /) out+="/"; i=$((i + 2)) ;;
        *) out+="$c"; i=$((i + 1)) ;;
      esac
    else
      out+="$c"
      i=$((i + 1))
    fi
  done
  printf '%s' "$out"
}

# --- Reading the incoming Claude Code tool-call JSON ---

# Reads the full JSON payload from stdin and prints it. Usage:
#   INPUT="$(claude_json_read_stdin)"
claude_json_read_stdin() {
  cat
}

# --- Field extraction (no jq) ---

# Best-effort extraction of a top-level string field by key name from a flat,
# single-line JSON blob, e.g. claude_json_get_field "$INPUT" "file_path".
# Prints the unescaped value, or an empty string if the key is absent or the
# input isn't well-formed enough to match.
claude_json_get_field() {
  local json="$1" key="$2" value=""
  local pattern
  pattern='"'"${key}"'"[[:space:]]*:[[:space:]]*"((\\.|[^"\\])*)"'
  if [[ "$json" =~ $pattern ]]; then
    value="$(claude_json_unescape "${BASH_REMATCH[1]}")"
  fi
  printf '%s' "$value"
}

# tool_input.file_path, falling back to tool_response.filePath — matches the
# jq filter `.tool_input.file_path // .tool_response.filePath // empty` used
# by the PostToolUse format/lint/build hooks.
claude_json_get_file_path() {
  local json="$1" value
  value="$(claude_json_get_field "$json" "file_path")"
  if [ -z "$value" ]; then
    value="$(claude_json_get_field "$json" "filePath")"
  fi
  printf '%s' "$value"
}

# tool_input.command — used by hooks inspecting Bash tool calls.
claude_json_get_command() {
  local json="$1"
  claude_json_get_field "$json" "command"
}

# --- Emitting output back to Claude Code ---

# Safely emits {"systemMessage": "..."} — escapes the message so embedded
# quotes/backslashes/newlines can't break the JSON or inject extra keys.
claude_json_emit_system_message() {
  local msg="$1" escaped
  escaped="$(claude_json_escape "$msg")"
  printf '{"systemMessage": "%s"}\n' "$escaped"
}
