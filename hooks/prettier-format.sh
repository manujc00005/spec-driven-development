#!/bin/bash
FILE=$(jq -r '.tool_input.file_path // .tool_response.filePath // empty')
echo "$FILE" | grep -qE '\.(ts|tsx|css|json|js|jsx)$' || exit 0
ls .prettierrc* prettier.config* 2>/dev/null | grep -q . || exit 0
npx prettier --write "$FILE" 2>/dev/null || true
