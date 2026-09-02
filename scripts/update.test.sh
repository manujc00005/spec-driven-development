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

# ===========================================================================
# Spec 034 - the manifest must not overstate freshness, and a removed profile
# must stay removed across an update.
# ===========================================================================

# --- AC-002: the delta floor is the OLDEST per-profile commit --------------
# Reproduces the original defect: a partial install bumps the top-level commit
# while leaving a profile's files behind. Reading the top-level value makes
# update.sh report "already up to date" for a profile that is a release stale.
build_env spec034_ac002
V1_COMMIT="$( cd "$CLONE" && $GIT rev-parse v0.1.0 )"
V2_COMMIT="$( cd "$CLONE" && $GIT rev-parse v0.2.0 )"
python3 - "$CENTRAL/.sdd-install.json" "$V1_COMMIT" "$V2_COMMIT" <<'PYEOF'
import json, sys
path, v1, v2 = sys.argv[1:4]
with open(path, encoding="utf-8") as f:
    d = json.load(f)
# Exactly what a partial run used to produce: top level claims the new commit,
# while a recorded profile's files are still at the old one.
d["schemaVersion"] = 2
d["installedCommit"] = v2
d["installedVersion"] = "v0.2.0"
d["profileState"] = {
    name: {"commit": v1 if name == "core" else v2,
           "version": "v0.1.0" if name == "core" else "v0.2.0",
           "installedAt": "2026-01-01T00:00:00+00:00"}
    for name in d.get("profiles", [])
}
with open(path, "w", encoding="utf-8") as f:
    json.dump(d, f, indent=2); f.write("\n")
PYEOF
out="$(bash "$CLONE/scripts/update.sh" --central-dir "$CENTRAL" 2>&1)"; rc=$?
if [ $rc -ne 0 ]; then fail "AC-002/034 exit" "expected 0, got $rc"
elif grep -q "Already up to date" <<< "$out"; then
  fail "AC-002/034 delta taken from the newest commit  - the stale profile was reported as current" "$(grep -E 'up to date|Updated:' <<< "$out")"
elif ! grep -q "v0.1.0 -> v0.2.0" <<< "$out"; then
  fail "AC-002/034 delta not computed from the oldest per-profile commit" "$(grep -E 'Updated:|Oldest' <<< "$out")"
elif ! grep -q "Oldest recorded profile" <<< "$out"; then
  fail "AC-002/034 the oldest-profile basis is not stated in the output" "$out"
else pass "AC-002/034 delta is computed from the oldest per-profile commit, not the newest"; fi

# --- AC-006: a removed profile is not resurrected by update.sh -------------
build_env spec034_ac006
bash "$CLONE/install.sh" --central-dir "$CENTRAL" --skip-link --profile python-sql-data >/dev/null 2>&1
[ -d "$CENTRAL/skills/python-reviewer" ] || fail "AC-006 setup: python-sql-data did not install"
bash "$CLONE/install.sh" --central-dir "$CENTRAL" --skip-link --remove-profile python-sql-data >/dev/null 2>&1
if [ -d "$CENTRAL/skills/python-reviewer" ]; then
  fail "AC-006 setup: --remove-profile did not delete the profile's files"
else
  out="$(bash "$CLONE/scripts/update.sh" --central-dir "$CENTRAL" 2>&1)"; rc=$?
  if [ $rc -ne 0 ]; then fail "AC-006 update.sh exit" "expected 0, got $rc: $(tail -3 <<< "$out")"
  elif [ -d "$CENTRAL/skills/python-reviewer" ]; then
    fail "AC-006 update.sh resurrected the removed profile" "$(grep -i 'recorded profiles' <<< "$out")"
  else pass "AC-006 a removed profile stays removed across update.sh"; fi
fi

# --- AC-006b: removing the LAST non-core profile must not re-add the default
# This is the case D001 and D010 exist for: with core alone recorded, the old
# code passed no --profile and install.sh fell back to defaults.profile.
build_env spec034_ac006b
bash "$CLONE/install.sh" --central-dir "$CENTRAL" --skip-link --profile java-spring-backend >/dev/null 2>&1
bash "$CLONE/install.sh" --central-dir "$CENTRAL" --skip-link --remove-profile java-spring-backend >/dev/null 2>&1
recorded="$(python3 -c 'import json,sys;print(",".join(json.load(open(sys.argv[1]))["profiles"]))' "$CENTRAL/.sdd-install.json" 2>/dev/null)"
out="$(bash "$CLONE/scripts/update.sh" --central-dir "$CENTRAL" 2>&1)"; rc=$?
if [ "$recorded" != "core" ]; then fail "AC-006b setup: expected only core recorded, got '$recorded'"
elif [ $rc -ne 0 ]; then fail "AC-006b update.sh exit" "expected 0, got $rc"
elif [ -d "$CENTRAL/skills/java-spring-reviewer" ]; then
  fail "AC-006b defaults.profile re-added the removed profile through update.sh" "$(grep -i 'recorded profiles\|default profile' <<< "$out")"
else pass "AC-006b removing the last non-core profile does not fall back to defaults.profile"; fi

# ---------------------------------------------------------------------------
# Spec 030 AC-009: a profile the adopter never installed is REPORTED with the
# command that adds it, and is NOT installed. This is defect (3) of the spec:
# update replays the recorded profile list, so a profile added after the last
# install.sh run silently never arrives and nothing says it exists.
# ---------------------------------------------------------------------------
build_env spec030_ac009
# Record an install of core + java-spring-backend only. python-sql-data exists
# in profiles.json but was never asked for.
bash "$CLONE/install.sh" --central-dir "$CENTRAL" --skip-link --profile java-spring-backend >/dev/null 2>&1
out="$(bash "$CLONE/scripts/update.sh" --central-dir "$CENTRAL" 2>&1)"; rc=$?
if [ $rc -ne 0 ]; then fail "AC-009 exit" "expected 0, got $rc: $out"
elif ! grep -q "Profiles available but NOT installed here" <<< "$out"; then
  fail "AC-009 no report emitted" "$out"
elif ! grep -q "python-sql-data" <<< "$out"; then
  fail "AC-009 does not name the missing profile" "$out"
elif ! grep -qF -- "--profile python-sql-data" <<< "$out"; then
  fail "AC-009 does not name the command that would add it" "$out"
elif [ -d "$CENTRAL/skills/python-reviewer" ]; then
  fail "AC-009/FR-012 update INSTALLED the reported profile - it must only report"
elif ! grep -q "billable add-on" <<< "$out"; then
  fail "AC-009 seo-geo-addon reported without naming it as billable" "$out"
else pass "AC-009 unrecorded profile reported, not installed"; fi

# A disabled profile must never be advertised, however the report is built.
if grep -q "blockchain-crypto" <<< "$out"; then
  fail "AC-009 a disabled profile was advertised as available"
else pass "AC-009 disabled profile not advertised"; fi

# ---------------------------------------------------------------------------
# Spec 030 AC-010: with a missing or corrupt manifest the recorded list is
# empty. An ungated comparison would then announce EVERY profile as new, which
# is the confidently wrong answer. It must say it cannot compare instead.
# ---------------------------------------------------------------------------
build_env spec030_ac010
echo "{ this is not valid json" > "$CENTRAL/.sdd-install.json"
out="$(bash "$CLONE/scripts/update.sh" --central-dir "$CENTRAL" 2>&1)"; rc=$?
if [ $rc -ne 0 ]; then fail "AC-010 exit" "expected 0, got $rc: $out"
elif ! grep -q "New profiles: cannot compare" <<< "$out"; then
  fail "AC-010 corrupt manifest did not degrade to 'cannot compare'" "$out"
elif grep -q "Profiles available but NOT installed here" <<< "$out"; then
  fail "AC-010 corrupt manifest listed profiles as new instead of refusing to compare" "$out"
else pass "AC-010 corrupt manifest cannot compare"; fi

# Same requirement with no manifest at all.
build_env spec030_ac010b
rm -f "$CENTRAL/.sdd-install.json"
out="$(bash "$CLONE/scripts/update.sh" --central-dir "$CENTRAL" 2>&1)"; rc=$?
if [ $rc -ne 0 ]; then fail "AC-010b exit" "expected 0, got $rc: $out"
elif ! grep -q "New profiles: cannot compare" <<< "$out"; then
  fail "AC-010b missing manifest did not degrade to 'cannot compare'" "$out"
elif grep -q "Profiles available but NOT installed here" <<< "$out"; then
  fail "AC-010b missing manifest listed profiles as new" "$out"
else pass "AC-010b missing manifest cannot compare"; fi

# Found by /qa-review: an unreadable profiles.json used to fall into the "none"
# branch, reporting "every enabled profile is already recorded" - a false
# reassurance on an error, which is AC-010's failure mode on the other input.
build_env spec030_qa_badprofiles
bash "$CLONE/install.sh" --central-dir "$CENTRAL" --skip-link --profile java-spring-backend >/dev/null 2>&1
cp "$CLONE/profiles.json" "$CLONE/profiles.json.bak"
echo "{ not valid json" > "$CLONE/profiles.json"
out="$(bash "$CLONE/scripts/update.sh" --central-dir "$CENTRAL" 2>&1)" || true
mv "$CLONE/profiles.json.bak" "$CLONE/profiles.json"
if grep -q "New profiles: none" <<< "$out"; then
  fail "QA: unreadable profiles.json reported as 'no new profiles'" "$out"
else pass "QA: unreadable profiles.json is never reported as 'none'"; fi

# The report must warn that --all-profiles re-adds deliberately removed profiles.
build_env spec030_qa_readdwarning
bash "$CLONE/install.sh" --central-dir "$CENTRAL" --skip-link --profile java-spring-backend >/dev/null 2>&1
out="$(bash "$CLONE/scripts/update.sh" --central-dir "$CENTRAL" 2>&1)"
if ! grep -q "Profiles available but NOT installed here" <<< "$out"; then
  fail "QA setup: expected the new-profile report to fire" "$out"
elif ! grep -q "removed on purpose" <<< "$out"; then
  fail "QA: the report suggests --all-profiles without warning it re-adds removed profiles" "$out"
else pass "QA: --all-profiles suggestion carries the re-add warning"; fi

echo ""
echo "$PASS passed, $FAIL failed."
[ "$FAIL" -eq 0 ]
