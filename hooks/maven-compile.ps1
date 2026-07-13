# DEPRECATED (2026-07-13, Phase 5 — see specs/features/005-.../DECISIONS.md D001).
# Superseded by hooks/java-build-test-guard.ps1, a strict superset (Maven-first + Gradle
# fallback, opt-in fast tests via SDD_JAVA_HOOK_RUN_TESTS, safe JSON output). Kept on disk
# and installable so existing wirings do not break. Do NOT wire both — they would compile
# twice per .java edit. New setups should wire java-build-test-guard instead.

$input_json = $input | Out-String | ConvertFrom-Json -ErrorAction SilentlyContinue
$FILE = $input_json.tool_input.file_path

if (-not $FILE) { exit 0 }
if ($FILE -notmatch '\.java$') { exit 0 }
if (-not (Test-Path "mvnw")) { exit 0 }

& ".\mvnw" compile -q 2>&1 | Select-Object -Last 30
