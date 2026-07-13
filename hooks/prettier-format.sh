#!/bin/bash
source "$(dirname "${BASH_SOURCE[0]}")/lib/claude-json.sh"

INPUT="$(claude_json_read_stdin)"
FILE="$(claude_json_get_file_path "$INPUT")"

[ -n "$FILE" ] || exit 0
echo "$FILE" | grep -qE '\.(ts|tsx|css|json|js|jsx)$' || exit 0
ls .prettierrc* prettier.config* 2>/dev/null | grep -q . || exit 0
npx prettier --write "$FILE" 2>/dev/null || true
