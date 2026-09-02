#!/usr/bin/env bash
#
# Tests for scripts/export-personal-config.sh, import-personal-config.sh and
# scripts/lib/personal-config.sh. Builds a synthetic HOME per case - nothing
# under the real ~/.claude is read or written.
#
# See specs/features/038-portable-personal-config/.
#
# Usage: scripts/personal-config.test.sh
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EXPORT="$REPO_ROOT/scripts/export-personal-config.sh"
IMPORT="$REPO_ROOT/scripts/import-personal-config.sh"
TMP_BASE="$(mktemp -d)"
trap 'rm -rf "$TMP_BASE"' EXIT
. "$REPO_ROOT/scripts/lib/personal-config.sh"

PASS=0; FAIL=0
ok()   { PASS=$((PASS+1)); echo "[PASS] $1"; }
bad()  { FAIL=$((FAIL+1)); echo "[FAIL] $1"; [ $# -gt 1 ] && echo "       $2"; }
check(){ if [ "$2" = "$3" ]; then ok "$1"; else bad "$1" "expected [$3] got [$2]"; fi; }

# A populated source machine: central dir + claude home.
make_source() {
  local d="$TMP_BASE/$1"; mkdir -p "$d/central" "$d/home/agents" "$d/home/plugins" \
    "$d/home/projects/proj-a/memory"
  echo "# personal instructions" > "$d/central/CLAUDE.md"
  printf '{\n  "theme": "dark",\n  "hooks": {"SessionStart": []}\n}\n' > "$d/home/settings.json"
  printf '{\n  "permissions": {"allow": ["Bash(ls:*)"]}\n}\n' > "$d/home/settings.local.json"
  echo "custom agent" > "$d/home/agents/my-agent.md"
  echo '{"plugins":[]}' > "$d/home/plugins/installed_plugins.json"
  echo '{"marketplaces":[]}' > "$d/home/plugins/known_marketplaces.json"
  printf -- "- [Alpha](alpha.md) — one\n- [Beta](beta.md) — two\n" > "$d/home/projects/proj-a/memory/MEMORY.md"
  echo "alpha body" > "$d/home/projects/proj-a/memory/alpha.md"
  printf '%s\n' "$d"
}
run_export() { CENTRAL_DIR="$1/central" CLAUDE_HOME="$1/home" bash "$EXPORT" "${@:2}" 2>&1; }
run_import() { CENTRAL_DIR="$1/central" CLAUDE_HOME="$1/home" bash "$IMPORT" "${@:2}" 2>&1; }

echo "--- unit: classify (T005) ---"
U="$TMP_BASE/u"; mkdir -p "$U"; echo same > "$U/a"; echo same > "$U/b"; echo diff > "$U/c"
ln -s "$U/a" "$U/link"
check "classify: missing"   "$(classify "$U/a" "$U/nope")" "missing"
check "classify: identical" "$(classify "$U/a" "$U/b")"    "identical"
check "classify: differs"   "$(classify "$U/a" "$U/c")"    "differs"
check "classify: symlink is differs, never followed" "$(classify "$U/a" "$U/link")" "differs"

echo "--- unit: credential detector (T003) ---"
echo "api_key: abc123def456" > "$U/leaky"; echo "just some prose" > "$U/clean"
if scan_for_secrets "$U/clean" >/dev/null; then ok "detector: clean file passes"; else bad "detector: clean file passes"; fi
if scan_for_secrets "$U/leaky" >/dev/null; then bad "detector: catches api_key"; else ok "detector: catches api_key"; fi
hit="$(scan_for_secrets "$U/leaky" || true)"
case "$hit" in *":1:"*) ok "detector: reports line number" ;; *) bad "detector: reports line number" "$hit" ;; esac

echo "--- unit: MEMORY.md additive merge (T006) ---"
M="$TMP_BASE/m"; mkdir -p "$M"
printf -- "- [Alpha](alpha.md) — one\n- [Beta](beta.md) — two\n"  > "$M/src"
printf -- "- [Alpha](alpha.md) — one\n- [Gamma](gamma.md) — three\n" > "$M/dst"
cp "$M/dst" "$M/dst.orig"
n="$(merge_memory_index "$M/src" "$M/dst")"
check "memory: appends only absent lines" "$n" "1"
head -2 "$M/dst" > "$M/dst.head"
if diff -q "$M/dst.orig" "$M/dst.head" >/dev/null; then ok "memory: existing lines byte-identical"; else bad "memory: existing lines byte-identical"; fi
grep -q "imported $(date +%F)" "$M/dst" && ok "memory: dated marker present" || bad "memory: dated marker present"
n2="$(merge_memory_index "$M/src" "$M/dst")"
check "memory: second merge is a no-op" "$n2" "0"

echo "--- unit: settings.json merge (T007) ---"
S="$TMP_BASE/s"; mkdir -p "$S"
printf '{"theme":"light","hooks":{"a":1}}\n' > "$S/src"
printf '{"theme":"dark"}\n' > "$S/dst"
added="$(merge_settings_json "$S/src" "$S/dst")"
check "settings: adds only absent key" "$added" "hooks"
check "settings: local key wins" "$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["theme"])' "$S/dst")" "dark"
printf 'not json\n' > "$S/bad"
if merge_settings_json "$S/bad" "$S/dst" >/dev/null 2>&1; then bad "settings: refuses invalid JSON"; else ok "settings: refuses invalid JSON"; fi

echo "--- integration: export (T004 / AC-001, AC-002) ---"
SRC="$(make_source src1)"
out="$(run_export "$SRC")"
[ -f "$SRC/central/personal/central/CLAUDE.md" ] && ok "export: CLAUDE.md in payload" || bad "export: CLAUDE.md in payload"
[ -f "$SRC/central/personal/home/settings.json" ] && ok "export: settings.json in payload" || bad "export: settings.json in payload"
[ -f "$SRC/central/personal/home/projects/proj-a/memory/MEMORY.md" ] && ok "export: memory in payload" || bad "export: memory in payload"
if find "$SRC/central/personal" -name "settings.local.json" | grep -q .; then
  bad "export: settings.local.json excluded"; else ok "export: settings.local.json excluded"; fi
[ -f "$SRC/central/personal/MANIFEST.json" ] && ok "export: MANIFEST.json written" || bad "export: MANIFEST.json written"

SRC2="$(make_source src2)"; echo "api_key: SECRETVALUE123" > "$SRC2/home/agents/leaky.md"
out2="$(run_export "$SRC2" || true)"
case "$out2" in *ABORTED*) ok "export: aborts on credential-shaped content" ;; *) bad "export: aborts on credential-shaped content" "$out2" ;; esac
[ -d "$SRC2/central/personal" ] && bad "export: wrote nothing on abort" || ok "export: wrote nothing on abort"
out3="$(run_export "$SRC2" --allow-suspicious || true)"
[ -d "$SRC2/central/personal" ] && ok "export: --allow-suspicious proceeds" || bad "export: --allow-suspicious proceeds"

echo "--- integration: import into empty (AC-003) ---"
DST="$TMP_BASE/dst1"; mkdir -p "$DST/central" "$DST/home"
cp -R "$SRC/central/personal" "$DST/central/personal"
outi="$(run_import "$DST")"
[ -f "$DST/central/CLAUDE.md" ] && ok "import(empty): CLAUDE.md restored" || bad "import(empty): CLAUDE.md restored"
[ -f "$DST/home/projects/proj-a/memory/alpha.md" ] && ok "import(empty): memory restored" || bad "import(empty): memory restored"
case "$outi" in *"conflicts: 0"*) ok "import(empty): zero conflicts" ;; *) bad "import(empty): zero conflicts" "$outi" ;; esac
perm="$(stat -f '%Lp' "$DST/home/settings.json" 2>/dev/null || stat -c '%a' "$DST/home/settings.json")"
check "import: settings.json is 0600" "$perm" "600"

echo "--- integration: import never overwrites (AC-004) ---"
DST2="$TMP_BASE/dst2"; mkdir -p "$DST2/central" "$DST2/home/agents"
cp -R "$SRC/central/personal" "$DST2/central/personal"
echo "LOCAL VERSION - do not lose me" > "$DST2/central/CLAUDE.md"
echo "local agent body" > "$DST2/home/agents/my-agent.md"
before_c="$(shasum "$DST2/central/CLAUDE.md" | awk '{print $1}')"
before_a="$(shasum "$DST2/home/agents/my-agent.md" | awk '{print $1}')"
outc="$(run_import "$DST2")"
after_c="$(shasum "$DST2/central/CLAUDE.md" | awk '{print $1}')"
after_a="$(shasum "$DST2/home/agents/my-agent.md" | awk '{print $1}')"
check "conflict: CLAUDE.md byte-identical after import" "$after_c" "$before_c"
check "conflict: agent byte-identical after import" "$after_a" "$before_a"
[ -f "$DST2/central/CLAUDE.md.incoming" ] && ok "conflict: .incoming written" || bad "conflict: .incoming written"
case "$outc" in *"conflicts: 2"*) ok "conflict: reports exactly 2" ;; *) bad "conflict: reports exactly 2" "$outc" ;; esac

echo "--- integration: idempotence (AC-007) ---"
out_again="$(run_import "$DST")"
case "$out_again" in *"copied: 0"*) ok "idempotent: zero copies on second run" ;; *) bad "idempotent: zero copies on second run" "$out_again" ;; esac
case "$out_again" in *"conflicts: 0"*) ok "idempotent: zero conflicts on second run" ;; *) bad "idempotent: zero conflicts on second run" "$out_again" ;; esac

echo "--- integration: no payload is a no-op (AC-008) ---"
DST3="$TMP_BASE/dst3"; mkdir -p "$DST3/central" "$DST3/home"
outn="$(run_import "$DST3")"
check "no payload: silent no-op" "$(printf '%s' "$outn" | tr -d '[:space:]')" ""

echo
echo "$PASS passed, $FAIL failed."
[ "$FAIL" -eq 0 ]
