#!/bin/bash
source "$(dirname "${BASH_SOURCE[0]}")/lib/claude-json.sh"

INPUT="$(claude_json_read_stdin)"
FILE="$(claude_json_get_file_path "$INPUT")"

[ -n "$FILE" ] || exit 0
echo "$FILE" | grep -qE '\.(ts|tsx|js|jsx)$' || exit 0
ls .eslintrc* eslint.config* 2>/dev/null | grep -q . || exit 0
npx eslint --fix "$FILE" 2>&1 | tail -10 || true
