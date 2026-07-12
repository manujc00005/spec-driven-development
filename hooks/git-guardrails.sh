#!/usr/bin/env bash
# git-guardrails.sh — Cross-platform parity with git-guardrails.ps1
# Blocks destructive git operations in Claude Code Bash tool calls.
# Read-only: never modifies files, never makes commits.
# Exit 0 = allow, Exit 2 = block.

set -euo pipefail

source "$(dirname "${BASH_SOURCE[0]}")/lib/claude-json.sh"

# Read the tool-call JSON from stdin (Claude Code pipes it)
INPUT="$(claude_json_read_stdin)"

# Extract the command string from the tool_input.command field
COMMAND="$(claude_json_get_command "$INPUT")"

if [ -z "$COMMAND" ]; then
  exit 0
fi

# Dangerous patterns — same set as git-guardrails.ps1
DANGEROUS_PATTERNS=(
  "git push"
  "git reset --hard"
  "git clean -fd"
  "git clean -f"
  "git branch -D"
  "git checkout \."
  "git restore \."
  "push --force"
  "reset --hard"
)

for pattern in "${DANGEROUS_PATTERNS[@]}"; do
  if echo "$COMMAND" | grep -qE "$pattern"; then
    echo "BLOCKED: '$COMMAND' matches dangerous pattern '$pattern'. The user has prevented you from doing this." >&2
    exit 2
  fi
done

exit 0
