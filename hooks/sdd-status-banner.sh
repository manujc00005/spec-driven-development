#!/bin/bash
[ -d specs/features ] || exit 0
STATUS=$(grep -rh "^status:" specs/features/*/SPEC.md 2>/dev/null | sed 's/status: *//' | sort | uniq -c)
[ -n "$STATUS" ] || exit 0
ONELINE=$(echo "$STATUS" | awk '{printf "%dx %s  ", $1, $2$3$4}' | sed 's/  $//')
printf '{"systemMessage":"[SDD] %s"}' "$ONELINE"
