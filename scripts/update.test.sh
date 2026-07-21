#!/usr/bin/env bash
#
# Self-test for scripts/update.sh (spec 015 T010). Each case builds a hermetic,
# network-free git setup from the current working tree:
#
#   src/       a fresh git repo: commit + tag v0.1.0, then a "release" commit
#              (new core skill + CHANGELOG header) tagged v0.2.0
#   origin.git a bare clone of src (the "upstream" update pulls from)
#   clone/     a working clone, reset to v0.1.0 on main (one release behind)
#   central/   a central dir installed from the clone at v0.1.0
#
# The clone stays ON a branch (never a detached tag checkout) so
# `git pull --ff-only` fast-forwards it, mirroring a real adopter. Asserts
# AC-002..AC-007 and AC-010.
#
# Usage: scripts/update.test.sh

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP_BASE="$(mktemp -d)"
trap 'rm -rf "$TMP_BASE"' EXIT

PASS=0
FAIL=0
GIT="git -c user.email=test@test -c user.name=test -c init.defaultBranch=main -c commit.gpgsign=false -c tag.gpgsign=false"

pass() { echo "[PASS] $1"; PASS=$((PASS + 1)); }
fail() { echo "[FAIL] $1"; [ -n "${2:-}" ] && echo "       $2"; FAIL=$((FAIL + 1)); }

# Deterministic content hash of a directory tree (portable: BSD + GNU).
tree_hash() { find "$1" -type f -exec cksum {} \; 2>/dev/null | sort; }

# Build src/origin/clone/central for one case. Sets SRC ORIGIN CLONE CENTRAL.
build_env() {
  local name="$1"
  local root="$TMP_BASE/$name"
  SRC="$root/src"; ORIGIN="$root/origin.git"; CLONE="$root/clone"; CENTRAL="$root/central"
  mkdir -p "$root"
  cp -r "$REPO_ROOT" "$SRC"; rm -rf "$SRC/.git"
  ( cd "$SRC"
    $GIT init --quiet
    $GIT add -A && $GIT commit --quiet -m "v0.1.0"
    $GIT tag v0.1.0
    # Release: a new skill declared in the core profile + a CHANGELOG header.
    mkdir -p skills/zzupdatetest
    printf -- '---\nname: zzupdatetest\ndescription: test-only skill.\n---\n# t\n' > skills/zzupdatetest/SKILL.md
    python3 - profiles.json <<'PY'
import json,sys
p=json.load(open(sys.argv[1]))
p["profiles"]["core"]["skills"].append("zzupdatetest")
json.dump(p,open(sys.argv[1],"w"),indent=2)
PY
    printf '## [0.2.0] — release two\n\n%s' "$(cat CHANGELOG.md)" > CHANGELOG.md
    $GIT add -A && $GIT commit --quiet -m "v0.2.0"
    $GIT tag v0.2.0 )
  $GIT clone --quiet --bare "$SRC" "$ORIGIN"
  $GIT clone --quiet "$ORIGIN" "$CLONE" 2>/dev/null
  ( cd "$CLONE" && $GIT reset --hard --quiet v0.1.0 )   # one release behind, on main
  # Install v0.1.0 into the central dir directly, so the manifest records v0.1.0.
  bash "$CLONE/install.sh" --central-dir "$CENTRAL" --skip-link >/dev/null 2>&1
}

# --- AC-002: behind-by-one update reports the delta and installs new artifacts ---
build_env ac002
out="$(bash "$CLONE/scripts/update.sh" --central-dir "$CENTRAL" 2>&1)"; rc=$?
if [ $rc -ne 0 ]; then fail "AC-002 exit" "expected 0, got $rc: $out"
elif ! grep -q "v0.1.0 -> v0.2.0" <<< "$out"; then fail "AC-002 version delta" "$out"
elif ! grep -q "0.2.0" <<< "$(grep -A2 "Releases in this update" <<< "$out")"; then fail "AC-002 changelog excerpt" "$out"
elif [ ! -f "$CENTRAL/skills/zzupdatetest/SKILL.md" ]; then fail "AC-002 new artifact missing in central"
else pass "AC-002 behind-by-one update"; fi

# --- AC-003: immediate re-run is idempotent (already up to date, no changes) ---
build_env ac003
bash "$CLONE/scripts/update.sh" --central-dir "$CENTRAL" >/dev/null 2>&1   # first: applies the update
before="$(tree_hash "$CENTRAL")"
out="$(bash "$CLONE/scripts/update.sh" --central-dir "$CENTRAL" 2>&1)"; rc=$?
after="$(tree_hash "$CENTRAL")"
if [ $rc -ne 0 ]; then fail "AC-003 exit" "expected 0, got $rc"
elif ! grep -qi "up to date" <<< "$out"; then fail "AC-003 message" "$out"
elif [ "$before" != "$after" ]; then fail "AC-003 central dir changed on idempotent re-run"
else pass "AC-003 idempotent re-run"; fi

# --- AC-004: dirty clone is refused before any pull, nothing modified ---
build_env ac004
echo "adopter local change" >> "$CLONE/README.md"
clone_head_before="$($GIT -C "$CLONE" rev-parse HEAD)"
out="$(bash "$CLONE/scripts/update.sh" --central-dir "$CENTRAL" 2>&1)"; rc=$?
clone_head_after="$($GIT -C "$CLONE" rev-parse HEAD)"
if [ $rc -ne 1 ]; then fail "AC-004 exit" "expected 1, got $rc: $out"
elif ! grep -q "README.md" <<< "$out"; then fail "AC-004 names dirty file" "$out"
elif [ "$clone_head_before" != "$clone_head_after" ]; then fail "AC-004 clone HEAD moved despite refusal"
else pass "AC-004 dirty clone refused"; fi

# --- AC-005: adopter-edited central file skipped without --force, overwritten (backup) with it ---
build_env ac005
bash "$CLONE/scripts/update.sh" --central-dir "$CENTRAL" >/dev/null 2>&1
target="$CENTRAL/skills/zzupdatetest/SKILL.md"
echo "ADOPTER EDIT" >> "$target"
out="$(bash "$CLONE/scripts/update.sh" --central-dir "$CENTRAL" 2>&1)"
if ! grep -q "Local edits detected" <<< "$out"; then fail "AC-005 not reported" "$out"
elif ! grep -q "ADOPTER EDIT" "$target"; then fail "AC-005 edit overwritten without --force"
else
  out2="$(bash "$CLONE/scripts/update.sh" --central-dir "$CENTRAL" --force 2>&1)"
  if grep -q "ADOPTER EDIT" "$target"; then fail "AC-005 --force did not overwrite"
  elif ! ls -d "$CENTRAL"/_install-backups/*/ >/dev/null 2>&1; then fail "AC-005 --force made no backup"
  else pass "AC-005 local-edit skip/force/backup"; fi
fi

# --- AC-006: --claude-md drift reported, target never written ---
build_env ac006
bash "$CLONE/scripts/update.sh" --central-dir "$CENTRAL" >/dev/null 2>&1
target="$TMP_BASE/ac006/my-claude.md"
# A CLAUDE.md missing a section the example has (grab the first heading from the example).
missing_heading="$(grep -m1 '^## ' "$CENTRAL/CLAUDE.md.example")"
printf '# My project\n\nsome notes without the shipped sections\n' > "$target"
sum_before="$(cksum < "$target")"
out="$(bash "$CLONE/scripts/update.sh" --central-dir "$CENTRAL" --claude-md "$target" 2>&1)"; rc=$?
sum_after="$(cksum < "$target")"
if [ $rc -ne 0 ]; then fail "AC-006 exit" "expected 0, got $rc"
elif ! grep -qF "$missing_heading" <<< "$out"; then fail "AC-006 missing heading not reported" "$out"
elif [ "$sum_before" != "$sum_after" ]; then fail "AC-006 target CLAUDE.md was modified"
else pass "AC-006 drift report, target untouched"; fi

# --- AC-006b: missing --claude-md target is advisory, exit still 0 ---
build_env ac006b
bash "$CLONE/scripts/update.sh" --central-dir "$CENTRAL" >/dev/null 2>&1
out="$(bash "$CLONE/scripts/update.sh" --central-dir "$CENTRAL" --claude-md "$TMP_BASE/ac006b/nope.md" 2>&1)"; rc=$?
if [ $rc -ne 0 ]; then fail "AC-006b exit" "expected 0, got $rc"
elif ! grep -qi "not found" <<< "$out"; then fail "AC-006b missing target not flagged" "$out"
else pass "AC-006b missing --claude-md advisory"; fi

# --- AC-007: no manifest -> unknown-version mode, and a manifest is written ---
build_env ac007
rm -f "$CENTRAL/.sdd-install.json"
out="$(bash "$CLONE/scripts/update.sh" --central-dir "$CENTRAL" 2>&1)"; rc=$?
if [ $rc -ne 0 ]; then fail "AC-007 exit" "expected 0, got $rc: $out"
elif ! grep -qi "unknown-version\|default profile\|no recorded" <<< "$out"; then fail "AC-007 unknown-version mode not stated" "$out"
elif [ ! -f "$CENTRAL/.sdd-install.json" ]; then fail "AC-007 manifest not written"
else pass "AC-007 unknown-version mode + manifest written"; fi

echo ""
echo "$PASS passed, $FAIL failed."
[ "$FAIL" -eq 0 ]
