#!/bin/bash
source "$(dirname "${BASH_SOURCE[0]}")/lib/claude-json.sh"

INPUT="$(claude_json_read_stdin)"
FILE="$(claude_json_get_file_path "$INPUT")"

[ -n "$FILE" ] || exit 0
echo "$FILE" | grep -q '\.java$' || exit 0
[ -f ./mvnw ] || exit 0
./mvnw compile -q 2>&1 | tail -30 || true
