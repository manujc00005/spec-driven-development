#!/usr/bin/env bash
#
# Self-test for install.sh hook installation (spec 016). Regression for the
# audit finding where profile-filtering mode never copied hooks/lib/, leaving
# every lib-sourcing hook (git-guardrails and friends) crashing with exit 1 on
# a fresh install — i.e. guardrails silently not blocking.
#
# Each case installs into a hermetic temp central dir with --skip-link (never
# touches ~/.claude or ~/.claude-config). Asserts AC-01..AC-03:
#   AC-01 hooks/lib/claude-json.sh exists after a profile install
#   AC-02 git-guardrails.sh from the fresh install blocks `git push --force`
#         with exit 2 and allows a benign command with exit 0
#   AC-03 re-running the installer is a no-op (idempotent)
#
# Usage: scripts/install.test.sh

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP_BASE="$(mktemp -d)"
trap 'rm -rf "$TMP_BASE"' EXIT

PASS=0
FAIL=0

pass() { echo "[PASS] $1"; PASS=$((PASS + 1)); }
fail() { echo "[FAIL] $1"; [ -n "${2:-}" ] && echo "       $2"; FAIL=$((FAIL + 1)); }

# Deterministic content hash of a directory tree (portable: BSD + GNU).
tree_hash() { find "$1" -type f -exec cksum {} \; 2>/dev/null | sort; }

CENTRAL="$TMP_BASE/central"

if ! "$REPO_ROOT/install.sh" --central-dir "$CENTRAL" --skip-link \
     --profile java-spring-backend >"$TMP_BASE/install.log" 2>&1; then
  fail "install.sh exited non-zero" "$(tail -5 "$TMP_BASE/install.log")"
  echo; echo "Results: $PASS passed, $FAIL failed"; exit 1
fi
pass "install.sh --profile java-spring-backend into fresh central dir"

# --- AC-01: hooks/lib shipped ---
if [ -f "$CENTRAL/hooks/lib/claude-json.sh" ]; then
  pass "AC-01 hooks/lib/claude-json.sh installed"
else
  fail "AC-01 hooks/lib/claude-json.sh missing after install"
fi

# --- AC-02: git-guardrails works from the fresh install ---
echo '{"tool_name":"Bash","tool_input":{"command":"git push --force"}}' \
  | bash "$CENTRAL/hooks/git-guardrails.sh" >/dev/null 2>&1
rc=$?
if [ "$rc" -eq 2 ]; then
  pass "AC-02 git-guardrails blocks 'git push --force' (exit 2)"
else
  fail "AC-02 git-guardrails did not block 'git push --force'" "exit=$rc (1 = lib missing/crash, 0 = allowed through)"
fi

echo '{"tool_name":"Bash","tool_input":{"command":"git status"}}' \
  | bash "$CENTRAL/hooks/git-guardrails.sh" >/dev/null 2>&1
rc=$?
if [ "$rc" -eq 0 ]; then
  pass "AC-02 git-guardrails allows benign command (exit 0)"
else
  fail "AC-02 git-guardrails broke on benign command" "exit=$rc"
fi

# --- AC-03: idempotent re-run ---
before="$(tree_hash "$CENTRAL")"
if ! "$REPO_ROOT/install.sh" --central-dir "$CENTRAL" --skip-link \
     --profile java-spring-backend >"$TMP_BASE/install2.log" 2>&1; then
  fail "AC-03 second install.sh run exited non-zero" "$(tail -5 "$TMP_BASE/install2.log")"
else
  after="$(tree_hash "$CENTRAL")"
  if [ "$before" = "$after" ]; then
    pass "AC-03 re-run is a no-op (idempotent)"
  else
    fail "AC-03 re-run changed the central dir" "$(diff <(echo "$before") <(echo "$after") | head -5)"
  fi
fi

echo
echo "Results: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ] || exit 1
