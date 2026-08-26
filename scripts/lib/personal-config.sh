#!/usr/bin/env bash
#
# personal-config.sh — shared manifest and merge logic for export/import of the
# personal Claude layer. Sourced by export-personal-config.sh and
# import-personal-config.sh; never executed directly.
#
# See specs/features/038-portable-personal-config/ for the decisions behind the
# semantics here. The two that shape everything:
#   D001 - the payload lives outside this (public) repository.
#   D002 - import NEVER overwrites. Missing -> copy. Identical -> skip.
#          Differing -> leave the target alone, write <name>.incoming, report.
#
# Requires python3, which install.sh already requires. (The dependency-free rule
# applies to hooks/, not to scripts the user runs on purpose - D005.)

# --- T001: the manifest -----------------------------------------------------
#
# The single declarative list of what qualifies as personal config. Anything not
# named here is never exported, so a new file appearing in ~/.claude cannot leak
# by default. Adding a category is a one-line edit.
#
# Format: <kind>:<path-relative-to-its-root>
#   home:<p>    -> $CLAUDE_HOME/<p>       (~/.claude)
#   central:<p> -> $CENTRAL_DIR/<p>       (~/.claude-config)
#   glob:<p>    -> $CLAUDE_HOME/<p>, shell-expanded
PERSONAL_MANIFEST=(
  "central:CLAUDE.md"
  "home:settings.json"
  "home:agents"
  "home:plugins/installed_plugins.json"
  "home:plugins/known_marketplaces.json"
  "glob:projects/*/memory"
)

# Never exported, under any name, ever. `install.sh` already holds this rule
# constitutionally for its own writes; FR-002 extends it to the payload.
PERSONAL_NEVER=("settings.local.json")

# --- T003: credential detector ----------------------------------------------
#
# Best-effort and deliberately noisy: a false positive costs one --allow-suspicious,
# a false negative costs a credential in a git repo. Refuses on suspicion.
PERSONAL_SECRET_RE='(token|secret|api[-_]?key|password|passwd|Bearer [A-Za-z0-9._-]{8,}|-----BEGIN [A-Z ]*PRIVATE KEY-----)'

# scan_for_secrets <file> -> prints "<file>:<lineno>:<line>" for each hit, rc 1 if any
scan_for_secrets() {
  local f="$1"
  [ -f "$f" ] || return 0
  # Only scan text; a binary match would be noise.
  if ! LC_ALL=C grep -Iq . "$f" 2>/dev/null; then return 0; fi
  local hits
  hits="$(LC_ALL=C grep -nEi "$PERSONAL_SECRET_RE" "$f" 2>/dev/null || true)"
  [ -z "$hits" ] && return 0
  printf '%s\n' "$hits" | while IFS= read -r line; do
    printf '%s:%s\n' "$f" "$line"
  done
  return 1
}

# --- T005: classifier -------------------------------------------------------
#
# The core of FR-004. Pure: reads, never writes. A symlink target is reported as
# `differs` and never followed - replacing what a symlink points at is exactly the
# silent destruction D002 exists to prevent.
#
# classify <source-file> <target-path> -> prints missing|identical|differs
classify() {
  local src="$1" dst="$2"
  [ -L "$dst" ] && { echo differs; return; }
  [ -e "$dst" ] || { echo missing; return; }
  if cmp -s "$src" "$dst"; then echo identical; else echo differs; fi
}

# --- T006: MEMORY.md additive merge -----------------------------------------
#
# Appends only index lines absent from the target, under a dated marker. Never
# reorders, rewrites or removes - D003. Existing content stays byte-identical,
# which AC-005 verifies by diffing the head of the result against the original.
#
# merge_memory_index <payload-MEMORY.md> <target-MEMORY.md> -> rc 0; prints count appended
merge_memory_index() {
  local src="$1" dst="$2"
  python3 - "$src" "$dst" <<'PY'
import sys, datetime, pathlib
src, dst = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
incoming = src.read_text(encoding="utf-8").splitlines()
current  = dst.read_text(encoding="utf-8").splitlines()
have = {l.strip() for l in current if l.strip()}
# Only pointer lines carry meaning in an index; prose headers are not merged.
new = [l for l in incoming if l.strip().startswith("- ") and l.strip() not in have]
if not new:
    print(0); sys.exit(0)
stamp = datetime.date.today().isoformat()
body = dst.read_text(encoding="utf-8").rstrip("\n")
body += f"\n\n<!-- imported {stamp} -->\n" + "\n".join(new) + "\n"
dst.write_text(body, encoding="utf-8")
print(len(new))
PY
}

# --- T007: settings.json merge ----------------------------------------------
#
# Top-level absent keys only. A local key always wins; arrays are never merged
# element-wise, because that would duplicate hooks or resurrect ones deliberately
# removed - D004. Invalid JSON on either side refuses this file and continues.
#
# merge_settings_json <payload> <target> -> rc 0 merged (prints keys added), rc 2 refused
merge_settings_json() {
  local src="$1" dst="$2"
  python3 - "$src" "$dst" <<'PY'
import sys, json, pathlib
src, dst = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
try:
    incoming = json.loads(src.read_text(encoding="utf-8"))
    current  = json.loads(dst.read_text(encoding="utf-8"))
except Exception as e:
    print(f"invalid JSON: {e}", file=sys.stderr); sys.exit(2)
if not isinstance(incoming, dict) or not isinstance(current, dict):
    print("not a JSON object", file=sys.stderr); sys.exit(2)
added = [k for k in incoming if k not in current]
for k in added:
    current[k] = incoming[k]
if added:
    dst.write_text(json.dumps(current, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(",".join(added))
PY
}
