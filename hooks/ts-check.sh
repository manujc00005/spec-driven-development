#!/bin/bash
FILE=$(jq -r '.tool_input.file_path // .tool_response.filePath // empty')
echo "$FILE" | grep -qE '\.(ts|tsx)$' || exit 0
[ -f tsconfig.json ] || exit 0
npx tsc --noEmit 2>&1 | tail -20 || true
