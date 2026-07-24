#!/usr/bin/env bash
#
# Self-test for scripts/check-consistency.sh: copies the repo to a temp dir
# per case, injects one drift mutation, and asserts the checker's exit code
# and output. See specs/features/007-ci-consistency-check/TASKS.md T007.
#
# Usage: scripts/check-consistency.test.sh

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CHECKER="$REPO_ROOT/scripts/check-consistency.sh"
TMP_BASE="$(mktemp -d)"
trap 'rm -rf "$TMP_BASE"' EXIT

PASS=0
FAIL=0

fresh_copy() {
  local case_name="$1"
  local dst="$TMP_BASE/$case_name"
  cp -r "$REPO_ROOT" "$dst"
  rm -rf "$dst/.git"
  echo "$dst"
}

# Portable in-place sed: GNU (-i) vs BSD/macOS (-i '') — GNU sed accepts
# --version, BSD sed does not.
sed_inplace() {
  local expr="$1" file="$2"
  if sed --version >/dev/null 2>&1; then
    sed -i "$expr" "$file"
  else
    sed -i '' "$expr" "$file"
  fi
}

# Current (correct) README counts, read dynamically so cases survive future
# skill/hook/agent additions (stale-hardcode failures bit this suite three times).
SKILLS_NOW=$(grep -oE "<!-- count:skills-total -->[0-9]+" "$REPO_ROOT/README.md" | head -1 | grep -oE "[0-9]+")
HOOKS_NOW=$(grep -oE "<!-- count:hook-families-total -->[0-9]+" "$REPO_ROOT/README.md" | head -1 | grep -oE "[0-9]+")
AGENTS_NOW=$(grep -oE "<!-- count:agents-total -->[0-9]+" "$REPO_ROOT/README.md" | head -1 | grep -oE "[0-9]+")

assert_case() {
  local name="$1" expect_exit="$2" expect_grep="$3" dir="$4"
  local out actual_exit
  out="$("$CHECKER" "$dir" 2>&1)"
  actual_exit=$?
  if [ "$actual_exit" -ne "$expect_exit" ]; then
    echo "[FAIL] $name: expected exit $expect_exit, got $actual_exit"
    echo "       output: $out"
    FAIL=$((FAIL + 1))
    return
  fi
  if [ -n "$expect_grep" ] && ! grep -qF "$expect_grep" <<< "$out"; then
    echo "[FAIL] $name: expected output to contain '$expect_grep'"
    echo "       output: $out"
    FAIL=$((FAIL + 1))
    return
  fi
  echo "[PASS] $name"
  PASS=$((PASS + 1))
}

assert_case_fix() {
  local name="$1" expect_exit="$2" expect_grep="$3" dir="$4" check_marker="$5"
  local out actual_exit marker_line
  out="$("$CHECKER" --fix "$dir" 2>&1)"
  actual_exit=$?
  if [ "$actual_exit" -ne "$expect_exit" ]; then
    echo "[FAIL] $name: expected exit $expect_exit, got $actual_exit"
    echo "       output: $out"
    FAIL=$((FAIL + 1))
    return
  fi
  if [ -n "$expect_grep" ] && ! grep -qF "$expect_grep" <<< "$out"; then
    echo "[FAIL] $name: expected output to contain '$expect_grep'"
    echo "       output: $out"
    FAIL=$((FAIL + 1))
    return
  fi
  # If check_marker is specified, verify it was actually written to README.md
  if [ -n "$check_marker" ]; then
    marker_line="<!-- count:${check_marker} -->"
    if ! grep -qF "$marker_line" "$dir/README.md"; then
      echo "[FAIL] $name: marker '$check_marker' not found in README.md after fix"
      FAIL=$((FAIL + 1))
      return
    fi
  fi
  echo "[PASS] $name"
  PASS=$((PASS + 1))
}

# --- control case: unmodified copy must pass clean ---
dir="$(fresh_copy clean)"
assert_case "clean-repo" 0 "Consistency check passed" "$dir"

# --- FR-001..004: missing shipped item per category ---
dir="$(fresh_copy missing-shipped-skill)"
rm -rf "$dir/skills/sdd"
assert_case "missing-shipped-skill" 1 "[shipped-skill] sdd" "$dir"

dir="$(fresh_copy missing-shipped-hook)"
rm -f "$dir/hooks/maven-compile.ps1"
assert_case "missing-shipped-hook-variant" 1 "[shipped-hook] maven-compile" "$dir"

# --- FR-001..004 / FR-009: shipped hook missing one variant (specific test for AC-002/FR-002) ---
dir="$(fresh_copy shipped-hook-missing-sh)"
rm -f "$dir/hooks/git-guardrails.sh"
assert_case "shipped-hook-missing-sh-variant" 1 "[shipped-hook] git-guardrails" "$dir"

dir="$(fresh_copy missing-shipped-template)"
rm -f "$dir/specs/_templates/SPEC.md"
assert_case "missing-shipped-template" 1 "[shipped-template] SPEC.md" "$dir"

dir="$(fresh_copy missing-shipped-agent)"
rm -f "$dir/agents/deep-reasoner.md"
assert_case "missing-shipped-agent" 1 "[shipped-agent] deep-reasoner" "$dir"

# --- FR-001 edge case: skill directory exists but no SKILL.md counts as missing ---
dir="$(fresh_copy shipped-skill-dir-no-skillmd)"
mkdir -p "$dir/skills/sdd-test-empty"  # Create directory but no SKILL.md inside
python3 - "$dir/profiles.json" <<'PYMUT'
import json, sys
path = sys.argv[1]
data = json.load(open(path))
data["profiles"]["core"]["skills"].append("sdd-test-empty")
json.dump(data, open(path, "w"), indent=2)
PYMUT
assert_case "shipped-skill-missing-skillmd" 1 "[shipped-skill] sdd-test-empty" "$dir"

# --- FR-005: orphans per category ---
dir="$(fresh_copy orphan-skill)"
mkdir -p "$dir/skills/zzz-orphan-test"
echo "# orphan" > "$dir/skills/zzz-orphan-test/SKILL.md"
assert_case "orphan-skill" 1 "[orphan-skill] zzz-orphan-test" "$dir"

# --- FR-001 edge case: skill dir without SKILL.md but NOT in profiles.json should not be orphan ---
dir="$(fresh_copy skill-dir-without-skillmd-not-shipped)"
mkdir -p "$dir/skills/zzz-empty-dir"
# Don't add to profiles.json, and don't create SKILL.md
# Should NOT report orphan (because directory without SKILL.md doesn't count as existing)
assert_case "skill-empty-dir-not-shipped" 0 "Consistency check passed" "$dir"

dir="$(fresh_copy orphan-hook)"
echo "# orphan" > "$dir/hooks/zzz-orphan-test.sh"
echo "# orphan" > "$dir/hooks/zzz-orphan-test.ps1"
assert_case "orphan-hook" 1 "[orphan-hook] zzz-orphan-test" "$dir"

dir="$(fresh_copy orphan-template)"
echo "# orphan" > "$dir/specs/_templates/ZZZ_ORPHAN.md"
assert_case "orphan-template" 1 "[orphan-template] ZZZ_ORPHAN.md" "$dir"

dir="$(fresh_copy orphan-agent)"
echo "# orphan" > "$dir/agents/zzz-orphan.md"
assert_case "orphan-agent" 1 "[orphan-agent] zzz-orphan" "$dir"

# --- FR-006: planned item exists on disk (must be promoted in profiles.json) ---
dir="$(fresh_copy planned-drift)"
echo "# planned" > "$dir/hooks/messaging-review-reminder.sh"
echo "# planned" > "$dir/hooks/messaging-review-reminder.ps1"
assert_case "planned-drift" 1 "[planned-drift] hook 'messaging-review-reminder'" "$dir"

# --- FR-009: hook family missing one variant (unshipped, so also an orphan) ---
dir="$(fresh_copy hook-parity)"
echo "# parity" > "$dir/hooks/zzz-parity-test.sh"
assert_case "hook-parity" 1 "[hook-parity] zzz-parity-test" "$dir"

# --- FR-007: settings wiring references a nonexistent hook ---
dir="$(fresh_copy settings-wiring-bad-path)"
sed_inplace 's/git-guardrails\.ps1/nonexistent-hook.ps1/' "$dir/settings.template.json"
assert_case "settings-wiring-bad-path" 1 "[settings-wiring] settings.template.json:nonexistent-hook.ps1" "$dir"

# --- FR-007: forbidden hook pair wired together ---
dir="$(fresh_copy settings-wiring-forbidden-pair)"
sed_inplace 's#\(bash \${CLAUDE_PROJECT_DIR}/.claude/hooks/\)java-build-test-guard\.sh#\1maven-compile.sh", "timeout": 60, "statusMessage": "Maven compile..." }, { "type": "command", "command": "bash ${CLAUDE_PROJECT_DIR}/.claude/hooks/java-build-test-guard.sh#' "$dir/settings.template.sh.json"
assert_case "settings-wiring-forbidden-pair" 1 "wires both 'maven-compile' and 'java-build-test-guard'" "$dir"

# --- FR-008: wrong README count ---
dir="$(fresh_copy readme-wrong-count)"
sed_inplace "s/<!-- count:skills-total -->${SKILLS_NOW}<!-- \\/count -->/<!-- count:skills-total -->9999<!-- \\/count -->/" "$dir/README.md"
assert_case "readme-wrong-count" 1 "readme-count] skills-total" "$dir"

# --- FR-008: missing required README marker ---
dir="$(fresh_copy readme-missing-marker)"
sed_inplace "s/<!-- count:agents-total -->${AGENTS_NOW}<!-- \\/count -->/${AGENTS_NOW}/g" "$dir/README.md"
assert_case "readme-missing-marker" 1 "required count marker missing" "$dir"

# --- FR-008 edge case: stale marker (key in README with no matching computed value) ---
dir="$(fresh_copy readme-stale-marker)"
# Append a marker with a key that doesn't exist in computed values
echo "<!-- count:fake-unknown-key -->9<!-- /count -->" >> "$dir/README.md"
assert_case "readme-stale-marker-key" 1 "not a recognized computed count" "$dir"

# --- FR-011: corrupt profiles.json ---
dir="$(fresh_copy corrupt-json)"
echo "{not valid json" > "$dir/profiles.json"
assert_case "corrupt-json" 1 "not valid JSON" "$dir"

# --- FR-012 / AC-010: --fix with wrong README count should auto-correct ---
dir="$(fresh_copy fix-readme-marker)"
sed_inplace "s/<!-- count:skills-total -->${SKILLS_NOW}<!-- \\/count -->/<!-- count:skills-total -->9999<!-- \\/count -->/" "$dir/README.md"
sed_inplace "s/<!-- count:hook-families-total -->${HOOKS_NOW}<!-- \\/count -->/<!-- count:hook-families-total -->99<!-- \\/count -->/" "$dir/README.md"
assert_case_fix "fix-readme-marker" 0 "[FIXED] readme" "$dir" "skills-total"
# Verify BOTH markers were actually updated with correct values
skills_marker=$(grep -oE "<!-- count:skills-total -->[0-9]+" "$dir/README.md" | head -1 | grep -oE "[0-9]+")
hooks_marker=$(grep -oE "<!-- count:hook-families-total -->[0-9]+" "$dir/README.md" | head -1 | grep -oE "[0-9]+")
if [ "$skills_marker" != "$SKILLS_NOW" ]; then
  echo "[FAIL] fix-readme-marker: skills-total marker not updated correctly (expected $SKILLS_NOW, got $skills_marker)"
  FAIL=$((FAIL + 1))
fi
if [ "$hooks_marker" != "$HOOKS_NOW" ]; then
  echo "[FAIL] fix-readme-marker: hook-families-total marker not updated correctly (expected $HOOKS_NOW, got $hooks_marker)"
  FAIL=$((FAIL + 1))
fi

# --- Spec 012 D003: badge drift is detected and auto-fixed like markers ---
# Read the current (correct) value instead of hardcoding it, so the case
# survives future skill additions.
skills_badge=$(grep -oE "badge/skills-[0-9]+-" "$REPO_ROOT/README.md" | grep -oE "[0-9]+")

dir="$(fresh_copy badge-drift)"
sed_inplace "s|badge/skills-${skills_badge}-|badge/skills-999-|" "$dir/README.md"
assert_case "badge-drift" 1 "readme-badge" "$dir"

dir="$(fresh_copy fix-badge-drift)"
sed_inplace "s|badge/skills-${skills_badge}-|badge/skills-999-|" "$dir/README.md"
assert_case_fix "fix-badge-drift" 0 "[FIXED] readme-badge skills" "$dir" ""
if ! grep -q "badge/skills-${skills_badge}-" "$dir/README.md"; then
  echo "[FAIL] fix-badge-drift: skills badge not restored to ${skills_badge}"
  FAIL=$((FAIL + 1))
fi

# --- FR-012 / AC-010: --fix with non-auto-fixable violations blocks changes ---
dir="$(fresh_copy fix-blocked-by-orphan)"
mkdir -p "$dir/skills/zzz-orphan-test"
echo "# orphan" > "$dir/skills/zzz-orphan-test/SKILL.md"
# Also make README have wrong count to test that it WON'T be fixed
sed_inplace "s/<!-- count:skills-total -->${SKILLS_NOW}<!-- \\/count -->/<!-- count:skills-total -->9999<!-- \\/count -->/" "$dir/README.md"
assert_case_fix "fix-blocked-by-orphan" 1 "[orphan-skill] zzz-orphan-test" "$dir" ""
# Verify the README marker was NOT updated (should still be wrong 44)
actual_marker=$(grep -oE "<!-- count:skills-total -->[0-9]+" "$dir/README.md" | head -1 | grep -oE "[0-9]+")
if [ "$actual_marker" != "9999" ]; then
  echo "[FAIL] fix-blocked-by-orphan: README was incorrectly modified (expected 9999, got $actual_marker)"
  FAIL=$((FAIL + 1))
fi

echo ""
echo "$PASS passed, $FAIL failed."
[ "$FAIL" -eq 0 ]
