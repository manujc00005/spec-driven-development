#!/usr/bin/env bash
#
# Tests for hooks/graphify-stale-reminder.sh and scripts/setup-graphify.sh.
# Builds a minimal sandbox project per case and stubs the graphify CLI so no
# npm package is needed. See specs/features/010-graphify-first-class-integration.
#
# Usage: scripts/graphify.test.sh

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HOOK="$REPO_ROOT/hooks/graphify-stale-reminder.sh"
SETUP="$REPO_ROOT/scripts/setup-graphify.sh"
TMP_BASE="$(mktemp -d)"
trap 'rm -rf "$TMP_BASE"' EXIT

PASS=0
FAIL=0

# Creates a minimal project sandbox: one source file plus a stub `graphify`
# executable in <sandbox>/stubbin that records its argv to invocations.log.
# Prints the sandbox path.
make_sandbox() {
  local name="$1"
  local dir="$TMP_BASE/$name"
  mkdir -p "$dir/stubbin"
  echo "export const x = 1;" > "$dir/app.ts"
  cat > "$dir/stubbin/graphify" <<'EOF'
#!/usr/bin/env bash
echo "$@" >> "$(dirname "$0")/../invocations.log"
mkdir -p .graphify
touch .graphify/graph.json .graphify/GRAPH_REPORT.md
exit 0
EOF
  chmod +x "$dir/stubbin/graphify"
  echo "$dir"
}

# Backdates a file's mtime by N days (GNU and BSD touch compatible).
backdate_days() {
  local days="$1" file="$2"
  local stamp
  if date -v -1d >/dev/null 2>&1; then
    stamp="$(date -v "-${days}d" +%Y%m%d%H%M)"   # BSD/macOS
  else
    stamp="$(date -d "-${days} days" +%Y%m%d%H%M)" # GNU
  fi
  touch -t "$stamp" "$file"
}

# Runs the hook inside a sandbox. Args: sandbox_dir [extra env as K=V ...]
# Captures stdout to $HOOK_OUT, exit code to $HOOK_EXIT, wall seconds to $HOOK_SECS.
run_hook() {
  local dir="$1"; shift
  local start end
  start=$(date +%s)
  HOOK_OUT="$(cd "$dir" && env PATH="$dir/stubbin:$PATH" "$@" bash "$HOOK" 2>&1)"
  HOOK_EXIT=$?
  end=$(date +%s)
  HOOK_SECS=$((end - start))
}

# Same, but with a minimal PATH that masks any real graphify CLI installed on
# this machine — for the "no CLI" cases (stub removed is not enough when a
# global @sentropic/graphify exists, e.g. under an nvm bin dir).
run_hook_nocli() {
  local dir="$1"; shift
  HOOK_OUT="$(cd "$dir" && env PATH="$dir/stubbin:/usr/bin:/bin" "$@" bash "$HOOK" 2>&1)"
  HOOK_EXIT=$?
}

assert_eq() {
  local name="$1" expected="$2" actual="$3"
  if [ "$expected" = "$actual" ]; then
    echo "[PASS] $name"
    PASS=$((PASS + 1))
  else
    echo "[FAIL] $name: expected '$expected', got '$actual'"
    FAIL=$((FAIL + 1))
  fi
}

assert_contains() {
  local name="$1" needle="$2" haystack="$3"
  if grep -qF "$needle" <<< "$haystack"; then
    echo "[PASS] $name"
    PASS=$((PASS + 1))
  else
    echo "[FAIL] $name: expected output to contain '$needle'"
    echo "       output: $haystack"
    FAIL=$((FAIL + 1))
  fi
}

assert_empty() {
  local name="$1" value="$2"
  if [ -z "$value" ]; then
    echo "[PASS] $name"
    PASS=$((PASS + 1))
  else
    echo "[FAIL] $name: expected empty output, got '$value'"
    FAIL=$((FAIL + 1))
  fi
}

assert_file_exists() {
  local name="$1" file="$2"
  if [ -f "$file" ]; then
    echo "[PASS] $name"
    PASS=$((PASS + 1))
  else
    echo "[FAIL] $name: expected file '$file' to exist"
    FAIL=$((FAIL + 1))
  fi
}

assert_file_absent() {
  local name="$1" file="$2"
  if [ ! -f "$file" ]; then
    echo "[PASS] $name"
    PASS=$((PASS + 1))
  else
    echo "[FAIL] $name: expected file '$file' to be absent"
    FAIL=$((FAIL + 1))
  fi
}

# Waits up to ~3s for the detached refresh to write the stub invocation log.
wait_for_invocation() {
  local dir="$1" i
  for i in 1 2 3 4 5 6; do
    [ -f "$dir/invocations.log" ] && return 0
    sleep 0.5
  done
  return 1
}

# --- Hook: canonical path detection (AC-001) ---

# Fresh report in .graphify/ → silent, exit 0. Tracer case for the path fix.
sandbox="$(make_sandbox fresh-canonical)"
mkdir -p "$sandbox/.graphify"
touch "$sandbox/.graphify/GRAPH_REPORT.md"
backdate_days 1 "$sandbox/app.ts"
run_hook "$sandbox"
assert_eq "fresh canonical report: exit 0" 0 "$HOOK_EXIT"
assert_empty "fresh canonical report: silent" "$HOOK_OUT"

# Absent report, no CLI → reminder, exit 0.
sandbox="$(make_sandbox absent-no-cli)"
rm "$sandbox/stubbin/graphify"
run_hook_nocli "$sandbox"
assert_eq "absent report, no CLI: exit 0" 0 "$HOOK_EXIT"
assert_contains "absent report, no CLI: reminder" "GRAPH_REPORT.md not found" "$HOOK_OUT"

# Stale canonical report, no CLI → staleness warning.
sandbox="$(make_sandbox stale-no-cli)"
rm "$sandbox/stubbin/graphify"
mkdir -p "$sandbox/.graphify"
touch "$sandbox/.graphify/GRAPH_REPORT.md"
backdate_days 9 "$sandbox/.graphify/GRAPH_REPORT.md"
run_hook_nocli "$sandbox"
assert_eq "stale report, no CLI: exit 0" 0 "$HOOK_EXIT"
assert_contains "stale report, no CLI: warning" "days older than the newest source file" "$HOOK_OUT"

# --- Hook: legacy root fallback (AC-002) ---

# Fresh report at legacy root → silent.
sandbox="$(make_sandbox legacy-fresh)"
touch "$sandbox/GRAPH_REPORT.md"
backdate_days 1 "$sandbox/app.ts"
run_hook "$sandbox"
assert_eq "legacy root fresh: exit 0" 0 "$HOOK_EXIT"
assert_empty "legacy root fresh: silent" "$HOOK_OUT"

# Stale report at legacy root, no CLI → staleness warning (fallback detected it).
sandbox="$(make_sandbox legacy-stale)"
rm "$sandbox/stubbin/graphify"
touch "$sandbox/GRAPH_REPORT.md"
backdate_days 9 "$sandbox/GRAPH_REPORT.md"
run_hook_nocli "$sandbox"
assert_eq "legacy root stale: exit 0" 0 "$HOOK_EXIT"
assert_contains "legacy root stale: warning" "days older than the newest source file" "$HOOK_OUT"

# --- Hook: background auto-refresh (AC-005) ---

# Absent report + stub CLI → lock created, background refresh invoked, fast exit.
sandbox="$(make_sandbox refresh-absent)"
run_hook "$sandbox"
assert_eq "auto-refresh on absent: exit 0" 0 "$HOOK_EXIT"
assert_contains "auto-refresh on absent: message" "refreshing in background" "$HOOK_OUT"
[ "$HOOK_SECS" -le 2 ] && echo "[PASS] auto-refresh on absent: foreground <2s" && PASS=$((PASS+1)) \
  || { echo "[FAIL] auto-refresh on absent: took ${HOOK_SECS}s"; FAIL=$((FAIL+1)); }
wait_for_invocation "$sandbox" || true
assert_file_exists "auto-refresh on absent: stub invoked" "$sandbox/invocations.log"
assert_contains "auto-refresh on absent: update args" "update . --no-description --no-label" "$(cat "$sandbox/invocations.log" 2>/dev/null)"

# Stale report + stub CLI → refresh invoked.
sandbox="$(make_sandbox refresh-stale)"
mkdir -p "$sandbox/.graphify"
touch "$sandbox/.graphify/GRAPH_REPORT.md"
backdate_days 9 "$sandbox/.graphify/GRAPH_REPORT.md"
run_hook "$sandbox"
assert_eq "auto-refresh on stale: exit 0" 0 "$HOOK_EXIT"
assert_contains "auto-refresh on stale: message" "refreshing in background" "$HOOK_OUT"
wait_for_invocation "$sandbox" || true
assert_file_exists "auto-refresh on stale: stub invoked" "$sandbox/invocations.log"

# SDD_GRAPHIFY_AUTO=0 → no refresh even with CLI available (AC-005 opt-out).
sandbox="$(make_sandbox refresh-optout)"
run_hook "$sandbox" SDD_GRAPHIFY_AUTO=0
assert_eq "opt-out: exit 0" 0 "$HOOK_EXIT"
assert_contains "opt-out: plain reminder" "GRAPH_REPORT.md not found" "$HOOK_OUT"
sleep 1
assert_file_absent "opt-out: stub NOT invoked" "$sandbox/invocations.log"

# Fresh lock → refresh suppressed (a run is already in flight).
sandbox="$(make_sandbox lock-fresh)"
mkdir -p "$sandbox/.graphify"
touch "$sandbox/.graphify/GRAPH_REPORT.md" "$sandbox/.graphify/.update.lock"
backdate_days 9 "$sandbox/.graphify/GRAPH_REPORT.md"
run_hook "$sandbox"
assert_eq "fresh lock: exit 0" 0 "$HOOK_EXIT"
assert_contains "fresh lock: falls back to warning" "Consider re-running Graphify" "$HOOK_OUT"
sleep 1
assert_file_absent "fresh lock: stub NOT invoked" "$sandbox/invocations.log"

# Expired lock (>10 min) → treated as crashed, refresh proceeds.
sandbox="$(make_sandbox lock-expired)"
mkdir -p "$sandbox/.graphify"
touch "$sandbox/.graphify/GRAPH_REPORT.md" "$sandbox/.graphify/.update.lock"
backdate_days 9 "$sandbox/.graphify/GRAPH_REPORT.md"
backdate_days 1 "$sandbox/.graphify/.update.lock"
run_hook "$sandbox"
assert_eq "expired lock: exit 0" 0 "$HOOK_EXIT"
assert_contains "expired lock: refresh message" "refreshing in background" "$HOOK_OUT"
wait_for_invocation "$sandbox" || true
assert_file_exists "expired lock: stub invoked" "$sandbox/invocations.log"

# --- graphify-scan-reminder.sh (spec 011: AC-001..003) ---

NUDGE="$REPO_ROOT/hooks/graphify-scan-reminder.sh"

# Runs the nudge hook inside a sandbox with empty stdin (PreToolUse pipes JSON).
run_nudge() {
  local dir="$1"; shift
  NUDGE_OUT="$(cd "$dir" && env "$@" bash "$NUDGE" < /dev/null 2>&1)"
  NUDGE_EXIT=$?
}

# No report → silent.
sandbox="$(make_sandbox nudge-no-report)"
run_nudge "$sandbox"
assert_eq "nudge without report: exit 0" 0 "$NUDGE_EXIT"
assert_empty "nudge without report: silent" "$NUDGE_OUT"

# Report present → nudge once, then throttled within TTL.
sandbox="$(make_sandbox nudge-report)"
mkdir -p "$sandbox/.graphify"
touch "$sandbox/.graphify/GRAPH_REPORT.md"
run_nudge "$sandbox"
assert_eq "nudge with report: exit 0" 0 "$NUDGE_EXIT"
assert_contains "nudge with report: message" "graph-first" "$NUDGE_OUT"
assert_file_exists "nudge with report: marker created" "$sandbox/.graphify/.scan-nudge"
run_nudge "$sandbox"
assert_eq "nudge throttled: exit 0" 0 "$NUDGE_EXIT"
assert_empty "nudge throttled: silent within TTL" "$NUDGE_OUT"

# Expired marker (>30 min) → nudges again.
backdate_days 1 "$sandbox/.graphify/.scan-nudge"
run_nudge "$sandbox"
assert_contains "nudge after TTL: message again" "graph-first" "$NUDGE_OUT"

# Legacy root report → nudge fires too.
sandbox="$(make_sandbox nudge-legacy)"
touch "$sandbox/GRAPH_REPORT.md"
run_nudge "$sandbox"
assert_contains "nudge legacy root: message" "graph-first" "$NUDGE_OUT"

# Opt-out → silent even with report.
sandbox="$(make_sandbox nudge-optout)"
mkdir -p "$sandbox/.graphify"
touch "$sandbox/.graphify/GRAPH_REPORT.md"
run_nudge "$sandbox" SDD_GRAPHIFY_NUDGE=0
assert_eq "nudge opt-out: exit 0" 0 "$NUDGE_EXIT"
assert_empty "nudge opt-out: silent" "$NUDGE_OUT"

# --- setup-graphify.sh (AC-006, AC-007) ---

# Runs the setup script inside a sandbox with the stub CLI on PATH and a
# non-existent central dir (forces the repo-template fallback).
run_setup() {
  local dir="$1"; shift
  SETUP_OUT="$(cd "$dir" && env PATH="$dir/stubbin:$PATH" bash "$SETUP" --project-dir "$dir" --central-dir "$TMP_BASE/no-central" --yes "$@" 2>&1)"
  SETUP_EXIT=$?
}

# First run: generates graph, gitignores, scaffolds docs. Second run: idempotent.
sandbox="$(make_sandbox setup-idempotent)"
run_setup "$sandbox"
assert_eq "setup first run: exit 0" 0 "$SETUP_EXIT"
assert_contains "setup first run: CLI already present, no install" "already on PATH" "$SETUP_OUT"
assert_file_exists "setup first run: report generated" "$sandbox/.graphify/GRAPH_REPORT.md"
assert_file_exists "setup first run: GRAPHIFY.md scaffolded" "$sandbox/docs/GRAPHIFY.md"
assert_file_exists "setup first run: PROJECT_GRAPH.md scaffolded" "$sandbox/docs/PROJECT_GRAPH.md"
assert_eq "setup first run: .graphify/ gitignored once" 1 "$(grep -cxF '.graphify/' "$sandbox/.gitignore")"

echo "user notes" > "$sandbox/docs/PROJECT_GRAPH.md"
run_setup "$sandbox"
assert_eq "setup second run: exit 0" 0 "$SETUP_EXIT"
assert_eq "setup second run: .gitignore not duplicated" 1 "$(grep -cxF '.graphify/' "$sandbox/.gitignore")"
assert_eq "setup second run: curated doc untouched" "user notes" "$(cat "$sandbox/docs/PROJECT_GRAPH.md")"

# Step 5: hooks copied into the project and wired into settings.json, once each
# even after two runs (this sandbox ran setup twice above).
assert_file_exists "setup: stale-reminder hook copied" "$sandbox/.claude/hooks/graphify-stale-reminder.sh"
assert_file_exists "setup: scan-reminder hook copied" "$sandbox/.claude/hooks/graphify-scan-reminder.sh"
[ -x "$sandbox/.claude/hooks/graphify-stale-reminder.sh" ] \
  && { echo "[PASS] setup: copied hook is executable"; PASS=$((PASS+1)); } \
  || { echo "[FAIL] setup: copied hook is executable"; FAIL=$((FAIL+1)); }
assert_file_exists "setup: settings.json created" "$sandbox/.claude/settings.json"
python3 -c "import json;json.load(open('$sandbox/.claude/settings.json'))" 2>/dev/null \
  && { echo "[PASS] setup: settings.json valid JSON"; PASS=$((PASS+1)); } \
  || { echo "[FAIL] setup: settings.json valid JSON"; FAIL=$((FAIL+1)); }
assert_eq "setup: stale hook wired once (idempotent)" 1 "$(grep -cF 'graphify-stale-reminder.sh' "$sandbox/.claude/settings.json")"
assert_eq "setup: scan hook wired once (idempotent)" 1 "$(grep -cF 'graphify-scan-reminder.sh' "$sandbox/.claude/settings.json")"

# Wiring never touches settings.local.json and preserves a pre-existing
# settings.json (additive merge + backup).
sandbox="$(make_sandbox setup-wire-preserve)"
mkdir -p "$sandbox/.claude"
printf '{"permissions":{"allow":["Bash"]}}' > "$sandbox/.claude/settings.local.json"
printf '{"hooks":{"Stop":[{"hooks":[{"type":"command","command":"echo keep-me"}]}]}}' > "$sandbox/.claude/settings.json"
run_setup "$sandbox"
assert_eq "wire preserve: exit 0" 0 "$SETUP_EXIT"
assert_eq "wire preserve: settings.local.json untouched" '{"permissions":{"allow":["Bash"]}}' "$(cat "$sandbox/.claude/settings.local.json")"
assert_contains "wire preserve: kept pre-existing Stop hook" "keep-me" "$(cat "$sandbox/.claude/settings.json")"
assert_contains "wire preserve: added stale-reminder" "graphify-stale-reminder.sh" "$(cat "$sandbox/.claude/settings.json")"
ls "$sandbox/.claude/settings.json.bak-"* >/dev/null 2>&1 \
  && { echo "[PASS] wire preserve: backup created"; PASS=$((PASS+1)); } \
  || { echo "[FAIL] wire preserve: backup created"; FAIL=$((FAIL+1)); }

# Step 5: hooks copied into .claude/hooks and wired in settings.json, idempotently.
assert_file_exists "setup wiring: stale-reminder hook copied" "$sandbox/.claude/hooks/graphify-stale-reminder.sh"
assert_file_exists "setup wiring: scan-reminder hook copied" "$sandbox/.claude/hooks/graphify-scan-reminder.sh"
assert_file_exists "setup wiring: settings.json created" "$sandbox/.claude/settings.json"
assert_eq "setup wiring: stale-reminder wired exactly once" 1 "$(grep -c "graphify-stale-reminder.sh" "$sandbox/.claude/settings.json")"
assert_eq "setup wiring: scan-reminder wired exactly once" 1 "$(grep -c "graphify-scan-reminder.sh" "$sandbox/.claude/settings.json")"

# Version-tolerant scope fallback: a CLI that rejects '--scope committed'
# (like documented 0.17.x scopes: auto/tracked/all) must still work via auto.
sandbox="$(make_sandbox setup-scope-fallback)"
cat > "$sandbox/stubbin/graphify" <<'EOF'
#!/usr/bin/env bash
echo "$@" >> "$(dirname "$0")/../invocations.log"
if [[ "$*" == *"--scope committed"* ]]; then exit 1; fi
mkdir -p .graphify
touch .graphify/graph.json .graphify/GRAPH_REPORT.md
exit 0
EOF
chmod +x "$sandbox/stubbin/graphify"
run_setup "$sandbox"
assert_eq "scope fallback: exit 0" 0 "$SETUP_EXIT"
assert_contains "scope fallback: fell back to auto" "Detected with --scope auto" "$SETUP_OUT"
assert_file_exists "scope fallback: report generated" "$sandbox/.graphify/GRAPH_REPORT.md"

# No CLI, npm present, no --yes, closed stdin → declines install gracefully, exit 0.
sandbox="$(make_sandbox setup-decline)"
rm "$sandbox/stubbin/graphify"
printf '#!/usr/bin/env bash\nexit 0\n' > "$sandbox/stubbin/npm" && chmod +x "$sandbox/stubbin/npm"
SETUP_OUT="$(cd "$sandbox" && env PATH="$sandbox/stubbin:/usr/bin:/bin" bash "$SETUP" --project-dir "$sandbox" --central-dir "$TMP_BASE/no-central" < /dev/null 2>&1)"
SETUP_EXIT=$?
assert_eq "setup non-interactive decline: exit 0" 0 "$SETUP_EXIT"
assert_contains "setup non-interactive decline: skip message" "Skipped install" "$SETUP_OUT"

# No npm and no graphify on PATH → actionable message, exit 0.
sandbox="$(make_sandbox setup-no-npm)"
rm "$sandbox/stubbin/graphify"
SETUP_OUT="$(cd "$sandbox" && env PATH="/usr/bin:/bin" bash "$SETUP" --project-dir "$sandbox" --central-dir "$TMP_BASE/no-central" --yes 2>&1)"
SETUP_EXIT=$?
assert_eq "setup without npm: exit 0" 0 "$SETUP_EXIT"
assert_contains "setup without npm: guidance" "npm is not installed" "$SETUP_OUT"

echo
echo "Passed: $PASS  Failed: $FAIL"
[ "$FAIL" -eq 0 ]
