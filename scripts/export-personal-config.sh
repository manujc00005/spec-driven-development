#!/usr/bin/env bash
#
# export-personal-config.sh - collect the personal Claude layer into the payload
# directory, so it can travel to another machine.
#
# The payload is NOT part of this repository: this repo is public, and the memory
# files reference client names and infrastructure (spec 038, D001). It is written
# to <central-dir>/personal/, which the owner keeps in a PRIVATE repo.
#
# Usage: scripts/export-personal-config.sh [options]
#   --central-dir <path>   Payload root (default: ~/.claude-config)
#   --claude-home <path>   Source (default: ~/.claude)
#   --allow-suspicious     Proceed despite credential-shaped content
#   --dry-run              Report what would be written, write nothing
#   -h, --help
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=scripts/lib/personal-config.sh
. "$REPO_ROOT/scripts/lib/personal-config.sh"

CENTRAL_DIR="${CENTRAL_DIR:-$HOME/.claude-config}"
CLAUDE_HOME="${CLAUDE_HOME:-$HOME/.claude}"
ALLOW_SUSPICIOUS=0
DRY_RUN=0

usage() { sed -n '2,16p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; }
while [ $# -gt 0 ]; do
  case "$1" in
    --central-dir) CENTRAL_DIR="$2"; shift 2 ;;
    --claude-home) CLAUDE_HOME="$2"; shift 2 ;;
    --allow-suspicious) ALLOW_SUSPICIOUS=1; shift ;;
    --dry-run) DRY_RUN=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1"; usage; exit 1 ;;
  esac
done

OUT="$CENTRAL_DIR/personal"
COPIED=0; REFUSED=0; SUSPECT=0
SUSPECT_LOG=""

# Resolve one manifest entry to absolute source paths (a glob may yield many).
resolve_entry() {
  local entry="$1" kind="${1%%:*}" rel="${1#*:}"
  case "$kind" in
    central) printf '%s\n' "$CENTRAL_DIR/$rel" ;;
    home)    printf '%s\n' "$CLAUDE_HOME/$rel" ;;
    glob)    # shellcheck disable=SC2086
             for p in $CLAUDE_HOME/$rel; do [ -e "$p" ] && printf '%s\n' "$p"; done ;;
  esac
}

# Path inside the payload that mirrors a source path.
payload_path() {
  local src="$1"
  case "$src" in
    "$CENTRAL_DIR"/*) printf '%s/central/%s\n' "$OUT" "${src#"$CENTRAL_DIR"/}" ;;
    "$CLAUDE_HOME"/*) printf '%s/home/%s\n'    "$OUT" "${src#"$CLAUDE_HOME"/}" ;;
  esac
}

is_never() {
  local base; base="$(basename "$1")"
  for n in "${PERSONAL_NEVER[@]}"; do [ "$base" = "$n" ] && return 0; done
  return 1
}

# --- Pass 1: collect candidate files and scan them (FR-007, before any write) ---
CANDIDATES=()
for entry in "${PERSONAL_MANIFEST[@]}"; do
  while IFS= read -r src; do
    [ -n "$src" ] || continue
    if [ -d "$src" ]; then
      while IFS= read -r f; do CANDIDATES+=("$f"); done < <(find "$src" -type f 2>/dev/null)
    elif [ -f "$src" ]; then
      CANDIDATES+=("$src")
    fi
  done < <(resolve_entry "$entry")
done

FILTERED=()
for f in "${CANDIDATES[@]+"${CANDIDATES[@]}"}"; do
  if is_never "$f"; then
    echo "[export] REFUSED $f  (never exported - FR-002)"
    REFUSED=$((REFUSED+1)); continue
  fi
  FILTERED+=("$f")
  if hits="$(scan_for_secrets "$f")"; then :; else
    SUSPECT=$((SUSPECT+1)); SUSPECT_LOG+="$hits"$'\n'
  fi
done

if [ "$SUSPECT" -gt 0 ] && [ "$ALLOW_SUSPICIOUS" -eq 0 ]; then
  echo
  echo "[export] ABORTED - credential-shaped content in $SUSPECT file(s):"
  printf '%s' "$SUSPECT_LOG" | sed 's/^/    /'
  echo
  echo "[export] Nothing was written. Review these, then re-run with --allow-suspicious"
  echo "[export] if they are false positives. The payload repo must be PRIVATE."
  exit 1
fi

# --- Pass 2: write. `personal/` is export OUTPUT, replaced wholesale (D006) ---
if [ "$DRY_RUN" -eq 0 ]; then
  rm -rf "$OUT"; mkdir -p "$OUT"
fi

for f in "${FILTERED[@]+"${FILTERED[@]}"}"; do
  dest="$(payload_path "$f")"
  [ -n "$dest" ] || continue
  if [ "$DRY_RUN" -eq 1 ]; then
    echo "[dry-run] would copy $f -> $dest"
  else
    mkdir -p "$(dirname "$dest")"
    cp -p "$f" "$dest"
  fi
  COPIED=$((COPIED+1))
done

if [ "$DRY_RUN" -eq 0 ]; then
  python3 - "$OUT" "$COPIED" <<'PY' > "$OUT/MANIFEST.json"
import sys, json, datetime, socket, pathlib
out = pathlib.Path(sys.argv[1])
files = sorted(str(p.relative_to(out)) for p in out.rglob("*") if p.is_file())
print(json.dumps({
    "exportedAt": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
    "sourceMachine": socket.gethostname(),
    "fileCount": len(files),
    "files": files,
}, indent=2))
PY
fi

echo
echo "[export] copied: $COPIED   refused: $REFUSED   suspicious: $SUSPECT"
echo "[export] payload: $OUT"
[ "$DRY_RUN" -eq 0 ] && echo "[export] commit and push it - the payload repo MUST be private."
exit 0
