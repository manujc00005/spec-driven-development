#!/bin/bash
FILE=$(jq -r '.tool_input.file_path // .tool_response.filePath // empty')
echo "$FILE" | grep -qE '\.(ts|tsx|js|jsx)$' || exit 0
ls .eslintrc* eslint.config* 2>/dev/null | grep -q . || exit 0
npx eslint --fix "$FILE" 2>&1 | tail -10 || true
