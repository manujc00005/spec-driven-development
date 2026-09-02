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

# --- Manifest helpers and fixtures (spec 034 T002) ------------------------
# manifest_field <manifest> <python-expr over `d`>: print one field, or the
# literal string ERR if the file is absent/unparseable. Keeps every assertion
# below a one-liner instead of an inline heredoc.
manifest_field() {
  python3 - "$1" "$2" <<'PYEOF' 2>/dev/null || echo ERR
import json, sys
try:
    with open(sys.argv[1], encoding="utf-8-sig") as f:
        d = json.load(f)
except (OSError, ValueError):
    print("ERR"); raise SystemExit(0)
try:
    print(eval(sys.argv[2], {"d": d}))
except Exception:
    print("ERR")
PYEOF
}

# Fixture manifests. Each writes to $1; the commit/profile values are the
# arguments so a test can point them at whatever the surrounding case needs.
# write_v1_manifest <path> <commit> <profile>[,<profile>...]
write_v1_manifest() {
  python3 - "$1" "$2" "$3" <<'PYEOF'
import json, sys
path, commit, profiles = sys.argv[1:4]
json.dump({
    "schemaVersion": 1,
    "installedVersion": "v0.0.0-1-g" + commit[:7],
    "installedCommit": commit,
    "installedAt": "2026-01-01T00:00:00+00:00",
    "profiles": [p for p in profiles.split(",") if p],
    "linkUserClaude": False,
    "sourceClone": "/tmp/fixture",
}, open(path, "w", encoding="utf-8"), indent=2)
PYEOF
}

# write_v2_manifest <path> <top-commit> <name:commit>[,<name:commit>...]
write_v2_manifest() {
  python3 - "$1" "$2" "$3" <<'PYEOF'
import json, sys
path, top, spec = sys.argv[1:4]
state, names = {}, []
for item in (x for x in spec.split(",") if x):
    name, _, commit = item.partition(":")
    names.append(name)
    state[name] = {
        "commit": commit,
        "version": "v0.0.0-1-g" + commit[:7],
        "installedAt": "2026-01-01T00:00:00+00:00",
    }
json.dump({
    "schemaVersion": 2,
    "installedVersion": "v0.0.0-1-g" + top[:7],
    "installedCommit": top,
    "installedAt": "2026-01-01T00:00:00+00:00",
    "profiles": names,
    "profileState": state,
    "linkUserClaude": False,
    "sourceClone": "/tmp/fixture",
}, open(path, "w", encoding="utf-8"), indent=2)
PYEOF
}

write_corrupt_manifest() { printf 'not json at all {{{\n' > "$1"; }

# A schemaVersion the installer has never heard of: must be discarded, not
# misread key-by-key.
write_future_manifest() {
  python3 - "$1" <<'PYEOF'
import json, sys
json.dump({
    "schemaVersion": 99,
    "installedCommit": "ffffffffffffffffffffffffffffffffffffffff",
    "profiles": ["core", "from-the-future"],
    "unknownKey": {"shape": "nobody knows"},
}, open(sys.argv[1], "w", encoding="utf-8"), indent=2)
PYEOF
}

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

# ===========================================================================
# Spec 034 - install manifest coherence. Each case uses its own central dir.
# ===========================================================================
HEAD_COMMIT="$(git -C "$REPO_ROOT" rev-parse HEAD 2>/dev/null || echo unknown)"
FAKE_OLD="0123456789abcdef0123456789abcdef01234567"

# --- AC-001: a partial run stamps only the ACTIVE profiles, and names the rest
C1="$TMP_BASE/ac001"
"$REPO_ROOT/install.sh" --central-dir "$C1" --skip-link --profile python-sql-data >/dev/null 2>&1
# Backdate python-sql-data so the carry-through is observable without a second
# repo commit: this is exactly the state a partial install leaves behind.
python3 - "$C1/.sdd-install.json" "$FAKE_OLD" <<'PYEOF'
import json, sys
path, old = sys.argv[1:3]
with open(path, encoding="utf-8") as f: d = json.load(f)
d["profileState"]["python-sql-data"] = {"commit": old, "version": "v0.0.1-old", "installedAt": "2026-01-01T00:00:00+00:00"}
with open(path, "w", encoding="utf-8") as f: json.dump(d, f, indent=2); f.write("\n")
PYEOF
"$REPO_ROOT/install.sh" --central-dir "$C1" --skip-link --profile java-spring-backend >"$TMP_BASE/ac001.log" 2>&1
ac001_rc=$?
kept="$(manifest_field "$C1/.sdd-install.json" 'd["profileState"]["python-sql-data"]["commit"]')"
fresh="$(manifest_field "$C1/.sdd-install.json" 'd["profileState"]["java-spring-backend"]["commit"]')"
if [ "$kept" = "$FAKE_OLD" ] && [ "$fresh" = "$HEAD_COMMIT" ]; then
  pass "AC-001 inactive profile keeps its commit, active profile is restamped"
else
  fail "AC-001 per-profile stamping wrong" "python-sql-data=$kept (want $FAKE_OLD), java-spring-backend=$fresh (want $HEAD_COMMIT)"
fi
if grep -q "NOT refreshed by this run" "$TMP_BASE/ac001.log" && grep -q "python-sql-data" "$TMP_BASE/ac001.log"; then
  pass "AC-001 unrefreshed profile is named in the run output"
else
  fail "AC-001 no warning naming the unrefreshed profile" "$(tail -3 "$TMP_BASE/ac001.log")"
fi
if [ "$ac001_rc" -eq 0 ]; then pass "AC-001 warning does not change the exit code"
else fail "AC-001 run exited non-zero" "exit=$ac001_rc"; fi

# A run covering every recorded profile must stay silent about staleness.
"$REPO_ROOT/install.sh" --central-dir "$C1" --skip-link --force \
  --profile java-spring-backend --profile python-sql-data >"$TMP_BASE/ac001b.log" 2>&1
if grep -q "NOT refreshed" "$TMP_BASE/ac001b.log"; then
  fail "AC-001 warned even though the active set covered every recorded profile"
else
  pass "AC-001 no warning when the active set covers everything recorded"
fi

# --- AC-003: a schemaVersion 1 manifest migrates in place, no re-install ---
C2="$TMP_BASE/ac003"
"$REPO_ROOT/install.sh" --central-dir "$C2" --skip-link --profile java-spring-backend >/dev/null 2>&1
write_v1_manifest "$C2/.sdd-install.json" "$FAKE_OLD" "core,java-spring-backend,python-sql-data"
"$REPO_ROOT/install.sh" --central-dir "$C2" --skip-link --profile java-spring-backend >/dev/null 2>&1
sv="$(manifest_field "$C2/.sdd-install.json" 'd["schemaVersion"]')"
migrated="$(manifest_field "$C2/.sdd-install.json" 'd["profileState"]["python-sql-data"]["commit"]')"
if [ "$sv" = "2" ] && [ "$migrated" = "$FAKE_OLD" ]; then
  pass "AC-003 v1 migrates to v2, attributing the old top-level commit to untouched profiles"
else
  fail "AC-003 migration wrong" "schemaVersion=$sv (want 2), python-sql-data=$migrated (want $FAKE_OLD)"
fi

# A schemaVersion nobody knows is discarded, not misread key-by-key.
write_future_manifest "$C2/.sdd-install.json"
"$REPO_ROOT/install.sh" --central-dir "$C2" --skip-link --profile java-spring-backend >/dev/null 2>&1
future_gone="$(manifest_field "$C2/.sdd-install.json" '"from-the-future" in d["profiles"]')"
if [ "$future_gone" = "False" ]; then
  pass "AC-003 unknown schemaVersion is discarded, not partially trusted"
else
  fail "AC-003 unknown schemaVersion leaked into the rebuilt manifest"
fi

# --- AC-004: byte-identical manifest across two identical runs -------------
C3="$TMP_BASE/ac004"
"$REPO_ROOT/install.sh" --central-dir "$C3" --skip-link --profile java-spring-backend >/dev/null 2>&1
cp "$C3/.sdd-install.json" "$TMP_BASE/ac004-first.json"
"$REPO_ROOT/install.sh" --central-dir "$C3" --skip-link --profile java-spring-backend >/dev/null 2>&1
if cmp -s "$TMP_BASE/ac004-first.json" "$C3/.sdd-install.json"; then
  pass "AC-004 re-running the same commit leaves the manifest byte-identical"
else
  fail "AC-004 manifest changed on an identical re-run" "$(diff "$TMP_BASE/ac004-first.json" "$C3/.sdd-install.json" | head -5)"
fi

# --- T019/rollback: a v1 reader still resolves against a v2 manifest ------
# This is the property the PLAN's rollback strategy depends on, so it is
# asserted rather than assumed: git revert must leave adopters working.
v1_profiles="$(manifest_field "$C3/.sdd-install.json" '",".join(d["profiles"])')"
v1_commit="$(manifest_field "$C3/.sdd-install.json" 'd["installedCommit"]')"
if [ "$v1_commit" = "$HEAD_COMMIT" ] && case ",$v1_profiles," in *",core,"*) true ;; *) false ;; esac; then
  pass "T019 a v1-shaped read (top-level profiles + installedCommit) still resolves on a v2 manifest"
else
  fail "T019 v2 manifest is not readable by a pre-034 reader" "profiles=$v1_profiles commit=$v1_commit"
fi

# --- AC-005: removal deletes exclusives, keeps shared, backs everything up --
C4="$TMP_BASE/ac005"
"$REPO_ROOT/install.sh" --central-dir "$C4" --skip-link \
  --profile java-spring-backend --profile next-prisma-web >/dev/null 2>&1
"$REPO_ROOT/install.sh" --central-dir "$C4" --skip-link --remove-profile next-prisma-web >/dev/null 2>&1
# database-review is shipped by BOTH java-spring-backend and next-prisma-web.
if [ -d "$C4/skills/database-review" ]; then
  pass "AC-005 an item still shipped by a recorded profile survives removal"
else
  fail "AC-005 shared item database-review was deleted"
fi
if [ ! -d "$C4/skills/prisma-migration-reviewer" ]; then
  pass "AC-005 an exclusively-owned item is deleted"
else
  fail "AC-005 exclusive item prisma-migration-reviewer survived removal"
fi
if [ -n "$(find "$C4/_install-backups" -path '*removed*prisma-migration-reviewer*' -name SKILL.md 2>/dev/null)" ]; then
  pass "AC-005 every deleted file is backed up first"
else
  fail "AC-005 no backup found for the deleted skill"
fi
still="$(manifest_field "$C4/.sdd-install.json" '"next-prisma-web" in d["profiles"] or "next-prisma-web" in d["profileState"]')"
if [ "$still" = "False" ]; then
  pass "AC-005 the profile is gone from both profiles and profileState"
else
  fail "AC-005 removed profile still recorded in the manifest"
fi

# --- AC-007/AC-009/AC-010: every refusal, and nothing touched --------------
C5="$TMP_BASE/ac007"
"$REPO_ROOT/install.sh" --central-dir "$C5" --skip-link --profile python-sql-data >/dev/null 2>&1
before_hash="$(tree_hash "$C5")"
refusal_ok=1
for bad_args in "--remove-profile core" "--remove-profile no-such-profile" "--remove-profile ../../etc" "--remove-profile " ; do
  # shellcheck disable=SC2086
  "$REPO_ROOT/install.sh" --central-dir "$C5" --skip-link $bad_args "" >/dev/null 2>&1
  [ $? -ne 0 ] || { refusal_ok=0; fail "AC-007/010 '$bad_args' was not refused"; }
done
"$REPO_ROOT/install.sh" --central-dir "$C5" --skip-link --profile python-sql-data --remove-profile python-sql-data >/dev/null 2>&1
[ $? -ne 0 ] || { refusal_ok=0; fail "AC-009 --profile x --remove-profile x was not refused"; }
[ "$refusal_ok" -eq 1 ] && pass "AC-007/AC-009/AC-010 core, unknown, traversing, empty and conflicting names are all refused"
if [ "$before_hash" = "$(tree_hash "$C5")" ]; then
  pass "AC-007/AC-009/AC-010 no refused invocation changed the central dir"
else
  fail "AC-009 a refused invocation modified the central dir"
fi

# --- AC-006: a removed profile stays removed when the recorded list replays -
# update.sh replays the manifest verbatim (D001); simulate that replay here.
C6="$TMP_BASE/ac006"
"$REPO_ROOT/install.sh" --central-dir "$C6" --skip-link --profile java-spring-backend >/dev/null 2>&1
"$REPO_ROOT/install.sh" --central-dir "$C6" --skip-link --remove-profile java-spring-backend >/dev/null 2>&1
replay="$(manifest_field "$C6/.sdd-install.json" '" ".join("--profile " + p for p in d["profiles"])')"
# shellcheck disable=SC2086
"$REPO_ROOT/install.sh" --central-dir "$C6" --skip-link $replay >/dev/null 2>&1
if [ ! -d "$C6/skills/java-spring-reviewer" ]; then
  pass "AC-006 a removed profile is not resurrected by replaying the recorded list"
else
  fail "AC-006 java-spring-backend came back after removal" "replay args: $replay"
fi

# --- AC-008: dry-run removal writes nothing --------------------------------
C7="$TMP_BASE/ac008"
"$REPO_ROOT/install.sh" --central-dir "$C7" --skip-link \
  --profile java-spring-backend --profile next-prisma-web >/dev/null 2>&1
dry_before="$(tree_hash "$C7")"
"$REPO_ROOT/install.sh" --central-dir "$C7" --skip-link --dry-run \
  --remove-profile next-prisma-web >"$TMP_BASE/ac008.log" 2>&1
if [ "$dry_before" = "$(tree_hash "$C7")" ]; then
  pass "AC-008 --dry-run --remove-profile changes nothing on disk"
else
  fail "AC-008 dry-run removal modified the central dir"
fi
if grep -q "would back up" "$TMP_BASE/ac008.log" && grep -q "keeping" "$TMP_BASE/ac008.log"; then
  pass "AC-008 dry-run reports both what it would delete and what it would keep"
else
  fail "AC-008 dry-run report incomplete" "$(grep -c . "$TMP_BASE/ac008.log") lines"
fi

# --- AC-011: shipped READMEs are refreshed under --force, with a backup ----
C8="$TMP_BASE/ac011"
"$REPO_ROOT/install.sh" --central-dir "$C8" --skip-link --profile java-spring-backend >/dev/null 2>&1
printf 'stale placeholder\n' > "$C8/agents/README.md"
printf 'stale placeholder\n' > "$C8/hooks/README.md"
"$REPO_ROOT/install.sh" --central-dir "$C8" --skip-link --force --profile java-spring-backend >/dev/null 2>&1
if cmp -s "$REPO_ROOT/agents/README.md" "$C8/agents/README.md" && cmp -s "$REPO_ROOT/hooks/README.md" "$C8/hooks/README.md"; then
  pass "AC-011 agents/ and hooks/ README.md are refreshed under --force"
else
  fail "AC-011 a shipped README stayed stale after --force"
fi
if [ -n "$(find "$C8/_install-backups" -name README.md 2>/dev/null)" ]; then
  pass "AC-011 the previous README content is backed up before overwriting"
else
  fail "AC-011 README overwritten without a backup"
fi

# --- Ownership is computed against the FINAL profile set -------------------
# Regression: removing Y while installing X must KEEP an item both ship,
# rather than deleting it and letting the install pass put it back.
C9="$TMP_BASE/ownership"
"$REPO_ROOT/install.sh" --central-dir "$C9" --skip-link --profile java-spring-backend >/dev/null 2>&1
own_out="$("$REPO_ROOT/install.sh" --central-dir "$C9" --skip-link \
  --profile next-prisma-web --remove-profile java-spring-backend 2>&1)"
if grep -q "keeping skill/database-review" <<< "$own_out" && [ -d "$C9/skills/database-review" ]; then
  pass "removal keeps an item shipped by a profile arriving in the same run"
else
  fail "removal ignored an incoming profile when computing ownership" "$(grep -E 'database-review' <<< "$own_out")"
fi
if [ -z "$(find "$C9/_install-backups" -path '*removed*database-review*' 2>/dev/null)" ]; then
  pass "the kept item is never backed up as if it were being deleted"
else
  fail "a kept item was backed up as a deletion"
fi

# --- FR-009 error path: a failed backup must never leave a file deleted -----
# D004 inverts the usual warn-and-continue posture here, because a lost backup
# on a delete is unrecoverable. Never exercised until /qa-review asked.
C10="$TMP_BASE/backupfail"
"$REPO_ROOT/install.sh" --central-dir "$C10" --skip-link --profile python-sql-data >/dev/null 2>&1
mkdir -p "$C10/_install-backups"
chmod 500 "$C10/_install-backups"
bf_out="$("$REPO_ROOT/install.sh" --central-dir "$C10" --skip-link --remove-profile python-sql-data 2>&1)"
bf_rc=$?
chmod 700 "$C10/_install-backups"
if [ "$bf_rc" -ne 0 ] && [ -d "$C10/skills/python-reviewer" ]; then
  pass "FR-009 a failed backup aborts without deleting, and exits non-zero"
else
  fail "FR-009 removal deleted a file it could not back up" "rc=$bf_rc present=$([ -d "$C10/skills/python-reviewer" ] && echo yes || echo no)"
fi
if grep -q "The manifest was NOT modified" <<< "$bf_out" && \
   ! grep -q "nothing deleted" <<< "$bf_out"; then
  pass "FR-009 the failure message describes what actually happened"
else
  fail "FR-009 failure message overstates or misstates the outcome" "$(grep ERROR <<< "$bf_out" | tail -1)"
fi
still_recorded="$(manifest_field "$C10/.sdd-install.json" '"python-sql-data" in d["profiles"]')"
if [ "$still_recorded" = "True" ]; then
  pass "FR-009 a failed removal leaves the manifest untouched, so a re-run retries"
else
  fail "FR-009 manifest was updated despite the removal failing"
fi

# --- Spec 030 AC-006/AC-007/AC-008/AC-017: --all-profiles --------------------
# A blanket request installs every ENABLED profile, excludes the disabled and
# the billable ones, and NAMES both exclusions instead of dropping them quietly.
ALLP_DIR="$TMP_BASE/all-profiles"
allp_out="$(bash "$REPO_ROOT/install.sh" --all-profiles --dry-run \
  --central-dir "$ALLP_DIR/central" --claude-home "$ALLP_DIR/home" --skip-link 2>&1)"; allp_rc=$?
allp_active="$(grep -m1 'Active profiles:' <<< "$allp_out")"
# Every enabled, non-billable profile in profiles.json must appear.
allp_expected="$(python3 - "$REPO_ROOT/profiles.json" <<'PYEOF'
import json, sys
with open(sys.argv[1], encoding="utf-8") as f:
    data = json.load(f)
for name, pdef in data["profiles"].items():
    if pdef.get("disabled") is True or pdef.get("billable") is True:
        continue
    print(name)
PYEOF
)"
allp_missing=""
while IFS= read -r _p; do
  [ -z "$_p" ] && continue
  grep -qF " $_p" <<< "$allp_active" || allp_missing="$allp_missing $_p"
done <<< "$allp_expected"
if [ $allp_rc -ne 0 ]; then
  fail "AC-006 --all-profiles exit" "expected 0, got $allp_rc: $allp_out"
elif [ -n "$allp_missing" ]; then
  fail "AC-006 --all-profiles missing enabled profile(s):$allp_missing" "$allp_active"
elif grep -qF ' blockchain-crypto' <<< "$allp_active"; then
  fail "AC-007 --all-profiles installed the disabled profile" "$allp_active"
elif grep -qF ' seo-geo-addon' <<< "$allp_active"; then
  fail "AC-008 --all-profiles installed the billable add-on" "$allp_active"
elif ! grep -q 'Skipped (billable add-on' <<< "$allp_out"; then
  fail "AC-017 --all-profiles did not name the billable profile it skipped" "$allp_out"
elif ! grep -q 'Skipped (disabled in profiles.json): blockchain-crypto' <<< "$allp_out"; then
  fail "AC-017 --all-profiles did not name the disabled profile it skipped" "$allp_out"
else
  pass "AC-006/007/008/017 --all-profiles installs every enabled profile and names both exclusions"
fi

# AC-007: naming a disabled profile explicitly still fails hard. The blanket
# flag must not have softened the existing refusal.
dis_out="$(bash "$REPO_ROOT/install.sh" --profile blockchain-crypto --dry-run \
  --central-dir "$ALLP_DIR/disabled" --skip-link 2>&1)"; dis_rc=$?
if [ $dis_rc -eq 0 ]; then
  fail "AC-007 an explicit disabled profile no longer fails hard" "$dis_out"
elif ! grep -q 'disabled by design' <<< "$dis_out"; then
  fail "AC-007 disabled refusal lost its message" "$dis_out"
else
  pass "AC-007 an explicitly named disabled profile still fails hard"
fi

# AC-008: the billable add-on is still installable when the adopter asks for it,
# and asking for it alongside --all-profiles must not report it as skipped while
# installing it - that output would contradict itself.
bill_out="$(bash "$REPO_ROOT/install.sh" --all-profiles --profile seo-geo-addon --dry-run \
  --central-dir "$ALLP_DIR/billable" --skip-link 2>&1)"; bill_rc=$?
bill_active="$(grep -m1 'Active profiles:' <<< "$bill_out")"
if [ $bill_rc -ne 0 ]; then
  fail "AC-008 explicit billable opt-in exit" "expected 0, got $bill_rc"
elif ! grep -qF ' seo-geo-addon' <<< "$bill_active"; then
  fail "AC-008 explicitly requested billable profile was not installed" "$bill_active"
elif grep -q 'Skipped (billable add-on' <<< "$bill_out"; then
  fail "AC-008 profile reported as skipped while being installed" "$bill_out"
else
  pass "AC-008 an explicitly named billable profile installs, and is not also reported as skipped"
fi

# --- Spec 030: --all-profiles must not resurrect what --remove-profile deletes -
# Found by /spec-review, not by this suite: unguarded, the blanket expansion
# included the profile being removed, so the run deleted its files, backed them
# up as removed, re-installed them in the same pass, and left the profile
# RECORDED in the manifest. Spec 034 D010's invariant through a door its guard
# did not cover. The combination is now refused outright.
RMDIR="$TMP_BASE/all-profiles-remove"
bash "$REPO_ROOT/install.sh" --profile java-spring-backend,payments-fintech \
  --central-dir "$RMDIR/central" --skip-link >/dev/null 2>&1
rm_out="$(bash "$REPO_ROOT/install.sh" --all-profiles --remove-profile payments-fintech \
  --central-dir "$RMDIR/central" --skip-link 2>&1)"; rm_rc=$?
rm_recorded="$(python3 -c 'import json,sys;print(",".join(json.load(open(sys.argv[1]))["profiles"]))' \
  "$RMDIR/central/.sdd-install.json" 2>/dev/null)"
if [ $rm_rc -eq 0 ]; then
  fail "--all-profiles + --remove-profile was accepted instead of refused" "$rm_out"
elif ! grep -q 'cannot be combined' <<< "$rm_out"; then
  fail "--all-profiles + --remove-profile refused without explaining why" "$rm_out"
elif [ ! -d "$RMDIR/central/skills/stripe-payments-reviewer" ]; then
  fail "the refusal still deleted files - it must change nothing"
elif [ "$rm_recorded" != "core,java-spring-backend,payments-fintech" ]; then
  fail "the refusal modified the manifest" "recorded: $rm_recorded"
else
  pass "--all-profiles + --remove-profile is refused, and nothing is changed"
fi

# The removal must still work on its own - the guard must not have broken it.
solo_out="$(bash "$REPO_ROOT/install.sh" --remove-profile payments-fintech \
  --central-dir "$RMDIR/central" --skip-link 2>&1)"; solo_rc=$?
solo_recorded="$(python3 -c 'import json,sys;print(",".join(json.load(open(sys.argv[1]))["profiles"]))' \
  "$RMDIR/central/.sdd-install.json" 2>/dev/null)"
if [ $solo_rc -ne 0 ]; then
  fail "plain --remove-profile broke" "$solo_out"
elif [ "$solo_recorded" != "core,java-spring-backend" ]; then
  fail "plain --remove-profile did not drop the profile from the manifest" "recorded: $solo_recorded"
elif [ -d "$RMDIR/central/skills/stripe-payments-reviewer" ]; then
  fail "plain --remove-profile left the removed profile's exclusive skill on disk"
else
  pass "plain --remove-profile still removes, guard did not break it"
fi

# The blanket run's reported "Active profiles:" must match what the manifest
# records. The defect above was visible precisely as a disagreement between the
# two, and nothing was asserting it.
AGDIR="$TMP_BASE/all-profiles-manifest-agrees"
ag_out="$(bash "$REPO_ROOT/install.sh" --all-profiles \
  --central-dir "$AGDIR/central" --skip-link 2>&1)"
ag_reported="$(grep -m1 'Active profiles:' <<< "$ag_out" | sed 's/.*Active profiles: //' | tr ' ' '\n' | sort | tr '\n' ',')"
ag_recorded="$(python3 -c 'import json,sys;print(",".join(sorted(json.load(open(sys.argv[1]))["profiles"])))' \
  "$AGDIR/central/.sdd-install.json" 2>/dev/null),"
if [ "$ag_reported" != "$ag_recorded" ]; then
  fail "--all-profiles: reported active profiles disagree with the manifest" "reported: $ag_reported / recorded: $ag_recorded"
else
  pass "--all-profiles: reported active profiles match the manifest exactly"
fi

echo
echo "Results: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ] || exit 1
