#!/bin/bash
FILE=$(jq -r '.tool_input.file_path // .tool_response.filePath // empty')
echo "$FILE" | grep -q '\.java$' || exit 0
[ -f ./mvnw ] || exit 0
./mvnw compile -q 2>&1 | tail -30 || true
