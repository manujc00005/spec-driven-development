#!/bin/bash
# DEPRECATED (2026-07-13, Phase 5 — see specs/features/005-.../DECISIONS.md D001).
# Superseded by hooks/java-build-test-guard.sh, a strict superset (Maven-first + Gradle
# fallback, opt-in fast tests via SDD_JAVA_HOOK_RUN_TESTS, safe JSON output). Kept on disk
# and installable so existing wirings do not break. Do NOT wire both — they would compile
# twice per .java edit. New setups should wire java-build-test-guard instead.
source "$(dirname "${BASH_SOURCE[0]}")/lib/claude-json.sh"

INPUT="$(claude_json_read_stdin)"
FILE="$(claude_json_get_file_path "$INPUT")"

[ -n "$FILE" ] || exit 0
echo "$FILE" | grep -q '\.java$' || exit 0
[ -f ./mvnw ] || exit 0
./mvnw compile -q 2>&1 | tail -30 || true
