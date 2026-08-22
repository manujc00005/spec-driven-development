#!/usr/bin/env bash
#
# Self-test for hooks/scope-keeper-reminder.sh (spec 036).
#
# The hook runs before EVERY Edit/Write in every session, so its hard contract
# is "never fail an edit" (D002): every case below asserts exit 0, including
# the malformed and hostile ones. The rest covers the throttle (once per
# session), the kill-switch, path safety, and that the excerpt has not drifted
# from the skill it quotes (D004).
#
# Usage: scripts/mindset-hook.test.sh

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HOOK="$REPO_ROOT/hooks/scope-keeper-reminder.sh"
TMP_BASE="$(mktemp -d)"
trap 'rm -rf "$TMP_BASE"' EXIT

PASS=0
FAIL=0
pass() { echo "[PASS] $1"; PASS=$((PASS + 1)); }
fail() { echo "[FAIL] $1"; [ -n "${2:-}" ] && echo "       $2"; FAIL=$((FAIL + 1)); }

# Every run gets its own TMPDIR so markers never leak between cases.
run_hook() {
  local payload="$1"
  shift
  printf '%s' "$payload" | env TMPDIR="$TMP_BASE/markers" "$@" bash "$HOOK" 2>/dev/null
}
mkdir -p "$TMP_BASE/markers"

sid() { printf '{"session_id":"%s","tool_name":"Edit","tool_input":{"file_path":"/tmp/x"}}' "$1"; }

# --- AC-001: first edit of a session emits the message, exit 0 -------------
out="$(run_hook "$(sid s-one)")"; rc=$?
if [ "$rc" -eq 0 ] && grep -q '"systemMessage"' <<< "$out"; then
  pass "AC-001 first edit emits a systemMessage and exits 0"
else
  fail "AC-001 no message or non-zero exit" "rc=$rc out=${out:0:80}"
fi

# --- AC-008: the message is identifiable and states it is not a gate -------
if grep -q '\[scope-keeper\]' <<< "$out" \
   && grep -q '/scope-keeper' <<< "$out" \
   && grep -qi 'reminder, not a gate' <<< "$out" \
   && grep -q 'SDD_SCOPE_REMINDER=0' <<< "$out"; then
  pass "AC-008 message is tagged, names the skill, disclaims enforcement, documents the kill-switch"
else
  fail "AC-008 message missing a required element" "${out:0:200}"
fi

# The emitted payload must be parseable JSON - a broken quote here would put
# malformed input into the session.
if printf '%s' "$out" | python3 -c 'import json,sys; json.load(sys.stdin)' 2>/dev/null; then
  pass "AC-001 the emitted payload is valid JSON"
else
  fail "AC-001 emitted payload is not valid JSON" "${out:0:200}"
fi

# --- AC-002: same session stays silent ------------------------------------
out2="$(run_hook "$(sid s-one)")"; rc=$?
if [ "$rc" -eq 0 ] && [ -z "$out2" ]; then
  pass "AC-002 a second edit in the same session is silent"
else
  fail "AC-002 hook repeated itself within one session" "rc=$rc out=${out2:0:80}"
fi

# --- AC-003: a different session is reminded ------------------------------
out3="$(run_hook "$(sid s-two)")"
if grep -q '"systemMessage"' <<< "$out3"; then
  pass "AC-003 a different session is reminded"
else
  fail "AC-003 a new session was not reminded"
fi

# --- AC-004: kill-switch ---------------------------------------------------
out4="$(run_hook "$(sid s-three)" env SDD_SCOPE_REMINDER=0)"; rc=$?
if [ "$rc" -eq 0 ] && [ -z "$out4" ]; then
  pass "AC-004 SDD_SCOPE_REMINDER=0 silences the hook"
else
  fail "AC-004 kill-switch ignored" "rc=$rc out=${out4:0:80}"
fi

# --- AC-005: hostile and degenerate input never fails an edit -------------
bad_ok=1
for payload in '' '{' 'not json at all' '{"tool_name":"Edit"}' '{"session_id":""}' '{"session_id":null}'; do
  run_hook "$payload" >/dev/null 2>&1
  rc=$?
  [ "$rc" -eq 0 ] || { bad_ok=0; fail "AC-005 non-zero exit on payload: ${payload:-<empty>}" "rc=$rc"; }
done
[ "$bad_ok" -eq 1 ] && pass "AC-005 empty, malformed and session-less payloads all exit 0"

# --- AC-006: a traversing session id is sanitised, not merely rejected -----
# Asserting "no marker with .. in its name" is too weak: an UNsanitised id makes
# touch fail, so no such marker exists either way and the test cannot tell the
# two apart (caught by mutating the sanitiser). Assert the POSITIVE property
# instead - a hostile id still produces a usable marker under a safe name, which
# only holds if the sanitiser actually ran.
canary="$TMP_BASE/canary-must-survive"
echo "do not delete" > "$canary"
rm -f "$TMP_BASE/markers"/.sdd-scope-reminder-* 2>/dev/null || true
out6="$(run_hook '{"session_id":"../../../../../../etc/passwd","tool_name":"Edit"}')"
rc=$?
markers="$(find "$TMP_BASE/markers" -maxdepth 1 -name '.sdd-scope-reminder-*' 2>/dev/null)"
marker_count="$(printf '%s\n' "$markers" | grep -c . || true)"
unsafe="$(printf '%s\n' "$markers" | grep -c '\.\.' || true)"
# The throttle must then work for that same id, which proves the marker is the
# one the hook will look for next time - not an orphan.
out6b="$(run_hook '{"session_id":"../../../../../../etc/passwd","tool_name":"Edit"}')"
if [ "$rc" -eq 0 ] && [ "$marker_count" -eq 1 ] && [ "$unsafe" -eq 0 ] \
   && [ -n "$out6" ] && [ -z "$out6b" ] && [ -f "$canary" ]; then
  pass "AC-006 a traversing session id is sanitised into a usable, throttling marker"
else
  fail "AC-006 traversal not neutralised" "rc=$rc markers=$marker_count unsafe=$unsafe first=${#out6} second=${#out6b}"
fi

# --- AC-007: nothing is written inside the project tree -------------------
before="$(cd "$REPO_ROOT" && git status --porcelain 2>/dev/null | sort)"
run_hook "$(sid s-tree)" >/dev/null 2>&1
after="$(cd "$REPO_ROOT" && git status --porcelain 2>/dev/null | sort)"
if [ "$before" = "$after" ]; then
  pass "AC-007 the hook writes nothing inside the project tree"
else
  fail "AC-007 the hook dirtied the working tree" "$(diff <(echo "$before") <(echo "$after") | head -3)"
fi

# --- AC-009: the excerpt has not drifted from the skill -------------------
# D004: the hook necessarily duplicates a little rule text. What must not
# happen is SILENT divergence, so every claim it makes is corroborated here.
SKILL="$REPO_ROOT/skills/scope-keeper/SKILL.md"
if [ ! -f "$SKILL" ]; then
  fail "AC-009 skills/scope-keeper/SKILL.md is missing"
else
  drift=0
  while IFS= read -r claim; do
    grep -qiF "$claim" "$SKILL" || { drift=1; fail "AC-009 hook asserts a rule the skill no longer contains" "$claim"; }
  done <<'CLAIMS'
while I'm at it
speculative generality
Necessary-adjacent
Dead code you created is yours
CLAIMS
  [ "$drift" -eq 0 ] && pass "AC-009 every rule the hook quotes still exists in scope-keeper"
fi

echo
echo "Results: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ] || exit 1
