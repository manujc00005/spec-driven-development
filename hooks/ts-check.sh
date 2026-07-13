#!/bin/bash
source "$(dirname "${BASH_SOURCE[0]}")/lib/claude-json.sh"

INPUT="$(claude_json_read_stdin)"
FILE="$(claude_json_get_file_path "$INPUT")"

[ -n "$FILE" ] || exit 0
echo "$FILE" | grep -qE '\.(ts|tsx)$' || exit 0
[ -f tsconfig.json ] || exit 0
npx tsc --noEmit 2>&1 | tail -20 || true
