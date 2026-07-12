#!/usr/bin/env bash
# java-build-test-guard.sh — Reminder hook (never blocks, never modifies files).
# After a .java file edit:
#   - Maven is the primary build tool (mvnw checked first).
#   - Default action is `mvnw compile` ONLY — no test suite runs unless
#     explicitly opted in via SDD_JAVA_HOOK_RUN_TESTS=1 (or "true"), and even
#     then only fast unit tests (`mvnw test -q -DskipITs`), never a full
#     `verify`/integration suite. This keeps the hook cheap by default.
#   - Gradle (gradlew) is used only as a fallback when no Maven wrapper (mvnw)
#     is present.
#   - No-op if neither mvnw nor gradlew is present.
# Exit 0 always.

set -uo pipefail

source "$(dirname "${BASH_SOURCE[0]}")/lib/claude-json.sh"

INPUT="$(claude_json_read_stdin)"
FILE="$(claude_json_get_field "$INPUT" "file_path")"

if [ -z "$FILE" ]; then exit 0; fi
if ! echo "$FILE" | grep -q '\.java$'; then exit 0; fi

RUN_TESTS=0
if [ "${SDD_JAVA_HOOK_RUN_TESTS:-0}" = "1" ] || [ "${SDD_JAVA_HOOK_RUN_TESTS:-}" = "true" ]; then
  RUN_TESTS=1
fi

# Maven-first (primary build tool) — compile only by default, no heavy suites.
if [ -f "./mvnw" ]; then
  OUTPUT=$(./mvnw compile -q 2>&1 | tail -30)
  if [ $? -ne 0 ]; then
    echo "$OUTPUT"
    echo '{"systemMessage":"[Java Build] Maven compile failed. Fix compilation errors before proceeding."}'
    exit 0
  fi
  if [ "$RUN_TESTS" -eq 1 ]; then
    TEST_OUTPUT=$(./mvnw test -q -DskipITs 2>&1 | tail -30)
    if [ $? -ne 0 ]; then
      echo "$TEST_OUTPUT"
      echo '{"systemMessage":"[Java Build] Maven fast unit tests failed (SDD_JAVA_HOOK_RUN_TESTS opt-in). Fix failing tests before proceeding."}'
    fi
  fi
  exit 0
fi

# Gradle fallback — only used when no Maven wrapper exists.
if [ -f "./gradlew" ]; then
  OUTPUT=$(./gradlew compileJava -q 2>&1 | tail -30)
  if [ $? -ne 0 ]; then
    echo "$OUTPUT"
    echo '{"systemMessage":"[Java Build] Gradle compile failed. Fix compilation errors before proceeding."}'
    exit 0
  fi
  if [ "$RUN_TESTS" -eq 1 ]; then
    TEST_OUTPUT=$(./gradlew test -q 2>&1 | tail -30)
    if [ $? -ne 0 ]; then
      echo "$TEST_OUTPUT"
      echo '{"systemMessage":"[Java Build] Gradle fast test task failed (SDD_JAVA_HOOK_RUN_TESTS opt-in). Fix failing tests before proceeding."}'
    fi
  fi
  exit 0
fi

# No build tool found — no-op
exit 0
