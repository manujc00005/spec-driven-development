#!/bin/bash
source "$(dirname "${BASH_SOURCE[0]}")/lib/claude-json.sh"

INPUT="$(claude_json_read_stdin)"
FILE="$(claude_json_get_field "$INPUT" "file_path")"
echo "$FILE" | grep -qE 'specs/|\.claude/' && exit 0
# Allow root-level and project docs (.md files outside specs/features/)
echo "$FILE" | grep -qE '\.md$' && ! echo "$FILE" | grep -q 'specs/features' && exit 0
[ -d specs/features ] || exit 0
grep -rql 'In Progress|: Ready' specs/features/ 2>/dev/null && exit 0
printf '{"continue":false,"stopReason":"No active spec (Ready or In Progress). Run /sdd or /spec-create first."}'
