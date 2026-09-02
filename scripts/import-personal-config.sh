#!/usr/bin/env bash
#
# import-personal-config.sh - restore the personal Claude layer from the payload,
# ADDITIVELY. This never overwrites anything (spec 038, D002):
#
#     target missing   -> copy          (the only case that writes)
#     target identical -> skip
#     target differs   -> leave it alone, write <name>.incoming, report a conflict
#
# Two narrow exceptions, both additive-only:
#   MEMORY.md      - absent index lines appended under a dated marker (D003)
#   settings.json  - absent top-level keys added; a local key always wins (D004)
#
# Why never overwrite, when install.sh does: a framework file has an authoritative
# upstream, so overwriting it is recoverable. A MEMORY.md written on the other
# machine has none - the copy being overwritten IS the only copy.
#
# Usage: scripts/import-personal-config.sh [options]
#   --central-dir <path>   Payload root (default: ~/.claude-config)
#   --claude-home <path>   Destination (default: ~/.claude)
#   --dry-run              Report what would happen, write nothing
#   -h, --help
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=scripts/lib/personal-config.sh
. "$REPO_ROOT/scripts/lib/personal-config.sh"

CENTRAL_DIR="${CENTRAL_DIR:-$HOME/.claude-config}"
CLAUDE_HOME="${CLAUDE_HOME:-$HOME/.claude}"
DRY_RUN=0

usage() { sed -n '2,24p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; }
while [ $# -gt 0 ]; do
  case "$1" in
    --central-dir) CENTRAL_DIR="$2"; shift 2 ;;
    --claude-home) CLAUDE_HOME="$2"; shift 2 ;;
    --dry-run) DRY_RUN=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1"; usage; exit 1 ;;
  esac
done

OUT="$CENTRAL_DIR/personal"
# FR-003: absent payload is a silent no-op, so a fresh clone installs as before.
[ -d "$OUT" ] || exit 0

COPIED=0; SKIPPED=0; CONFLICTS=0; MERGED=0; REFUSED=0
CONFLICT_LOG=""

# Map a payload path back to its destination.
dest_for() {
  local p="$1"
  case "$p" in
    "$OUT"/central/*) printf '%s/%s\n' "$CENTRAL_DIR" "${p#"$OUT"/central/}" ;;
    "$OUT"/home/*)    printf '%s/%s\n' "$CLAUDE_HOME" "${p#"$OUT"/home/}" ;;
  esac
}

# Memory files and settings hold personal content; keep them owner-only.
restrictive() {
  case "$1" in
    */settings.json|*/memory/*) return 0 ;;
    *) return 1 ;;
  esac
}

while IFS= read -r src; do
  [ -n "$src" ] || continue
  [ "$(basename "$src")" = "MANIFEST.json" ] && continue
  dst="$(dest_for "$src")"
  [ -n "$dst" ] || continue

  # FR-002 again on the import side: refuse even if a payload smuggled one in.
  if [ "$(basename "$src")" = "settings.local.json" ]; then
    echo "[import] REFUSED $dst  (never imported - FR-002)"
    REFUSED=$((REFUSED+1)); continue
  fi

  state="$(classify "$src" "$dst")"

  # --- Exception 1: MEMORY.md merges additively when both sides exist ---
  if [ "$state" = "differs" ] && [ "$(basename "$dst")" = "MEMORY.md" ]; then
    if [ "$DRY_RUN" -eq 1 ]; then
      echo "[dry-run] would merge index $dst"
    else
      n="$(merge_memory_index "$src" "$dst")"
      echo "[import] merged  $dst  (+$n index line(s))"
    fi
    MERGED=$((MERGED+1)); continue
  fi

  # --- Exception 2: settings.json merges absent top-level keys ---
  if [ "$state" = "differs" ] && [ "$(basename "$dst")" = "settings.json" ]; then
    if [ "$DRY_RUN" -eq 1 ]; then
      echo "[dry-run] would merge keys into $dst"
    else
      if added="$(merge_settings_json "$src" "$dst" 2>/dev/null)"; then
        echo "[import] merged  $dst  (keys: ${added:-none})"
        MERGED=$((MERGED+1))
      else
        echo "[import] REFUSED $dst  (invalid JSON on one side)"
        REFUSED=$((REFUSED+1))
      fi
    fi
    continue
  fi

  case "$state" in
    missing)
      if [ "$DRY_RUN" -eq 1 ]; then
        echo "[dry-run] would copy  $dst"
      else
        mkdir -p "$(dirname "$dst")"
        cp -p "$src" "$dst"
        restrictive "$dst" && chmod 600 "$dst"
      fi
      COPIED=$((COPIED+1)) ;;
    identical)
      SKIPPED=$((SKIPPED+1)) ;;
    differs)
      # THE rule: the existing file is not touched. Ever.
      if [ "$DRY_RUN" -eq 1 ]; then
        echo "[dry-run] would write $dst.incoming (conflict)"
      else
        cp -p "$src" "$dst.incoming"
        restrictive "$dst" && chmod 600 "$dst.incoming"
      fi
      CONFLICTS=$((CONFLICTS+1))
      CONFLICT_LOG+="    $dst"$'\n' ;;
  esac
done < <(find "$OUT" -type f 2>/dev/null | sort)

echo
echo "[import] copied: $COPIED   identical: $SKIPPED   merged: $MERGED   conflicts: $CONFLICTS   refused: $REFUSED"
if [ "$CONFLICTS" -gt 0 ]; then
  echo "[import] These already existed and were LEFT UNTOUCHED. The incoming version"
  echo "[import] is beside each as <name>.incoming - compare and resolve by hand:"
  printf '%s' "$CONFLICT_LOG"
fi
# FR-008: a conflict is information, not a failure.
exit 0
