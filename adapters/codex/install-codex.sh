#!/usr/bin/env bash
#
# install-codex.sh — self-contained, copy-only installer for the SDD Codex adapter.
#
# Copies this adapter's operating guide (AGENTS.md) into a target project root, and the lifecycle
# prompts (prompts/*.md) into a Codex prompts directory. It does NOTHING else:
#   - never runs the `codex` CLI (it is not required, and is not installed in the dev environment
#     this adapter was authored in — the adapter is prompt-based and unverified against a live CLI);
#   - never touches secrets, .env, or your existing ~/.codex/config.toml;
#   - never deletes; overwrites a differing file only with --force, after a timestamped backup;
#   - operates only within this adapter (source) and the target you name (destination).
#
# See ./README.md and ./PARITY.md for status and limitations.
#
# Usage:
#   install-codex.sh [--target DIR] [--codex-home DIR] [--prompts-only|--agents-only]
#                    [--dry-run] [--force] [-h|--help]
#
# Exit codes: 0 = ok (or dry-run), 1 = usage/precondition error.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

TARGET_DIR="$(pwd)"
TARGET_EXPLICIT=false
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
DO_AGENTS=true
DO_PROMPTS=true
DRY_RUN=false
FORCE=false
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"

usage() {
  sed -n '3,26p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
}

while [ $# -gt 0 ]; do
  case "$1" in
    --target) TARGET_DIR="${2:?--target needs a directory}"; TARGET_EXPLICIT=true; shift 2 ;;
    --codex-home) CODEX_HOME="${2:?--codex-home needs a directory}"; shift 2 ;;
    --prompts-only) DO_AGENTS=false; DO_PROMPTS=true; shift ;;
    --agents-only) DO_AGENTS=true; DO_PROMPTS=false; shift ;;
    --dry-run) DRY_RUN=true; shift ;;
    --force) FORCE=true; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "[ERROR] unknown argument: $1" >&2; usage; exit 1 ;;
  esac
done

AGENTS_SRC="$SCRIPT_DIR/AGENTS.md"
FRAMEWORK_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PROMPTS_SRC_DIR="$SCRIPT_DIR/prompts"
PROMPTS_DST_DIR="$CODEX_HOME/prompts"

log() { echo "$1"; }

# copy_one <src> <dst>
# Copy-only, idempotent, backup-on-force. Never deletes.
copy_one() {
  src="$1"; dst="$2"
  if [ ! -f "$src" ]; then
    log "[ERROR] source missing: $src"; return 1
  fi
  dst_parent="$(dirname "$dst")"
  if [ -f "$dst" ]; then
    if cmp -s "$src" "$dst"; then
      log "[skip]   $dst (identical)"
      return 0
    fi
    if [ "$FORCE" != true ]; then
      log "[skip]   $dst (differs — re-run with --force to overwrite; a backup is taken first)"
      return 0
    fi
    if [ "$DRY_RUN" = true ]; then
      log "[dry-run] would back up $dst -> $dst.bak-$TIMESTAMP and overwrite"
      return 0
    fi
    cp "$dst" "$dst.bak-$TIMESTAMP"
    log "[backup] $dst -> $dst.bak-$TIMESTAMP"
    cp "$src" "$dst"
    log "[copy]   $dst (overwritten)"
    return 0
  fi
  if [ "$DRY_RUN" = true ]; then
    log "[dry-run] would create $dst"
    return 0
  fi
  mkdir -p "$dst_parent"
  cp "$src" "$dst"
  log "[copy]   $dst"
}

log "SDD Codex adapter installer (copy-only)"
log "  source : $SCRIPT_DIR"
if [ "$DO_AGENTS" = true ] && [ "$TARGET_EXPLICIT" = true ]; then
  log "  target : $TARGET_DIR   (AGENTS.md)"
elif [ "$DO_AGENTS" = true ]; then
  log "  target : (none — AGENTS.md skipped; pass --target <your-project>)"
fi
[ "$DO_PROMPTS" = true ] && log "  codex  : $PROMPTS_DST_DIR   (prompts)"
[ "$DRY_RUN" = true ] && log "  mode   : DRY-RUN (no files will be written)"
log ""

rc=0

if [ "$DO_AGENTS" = true ]; then
  if [ "$TARGET_EXPLICIT" != true ]; then
    log "[skip]   AGENTS.md — no --target given. AGENTS.md is per-project and is never written to the"
    log "         current directory by default. Pass --target <your-project> (e.g. --target .) to install it."
  elif [ ! -d "$TARGET_DIR" ]; then
    log "[ERROR] target directory does not exist: $TARGET_DIR"; exit 1
  else
    target_abs="$(cd "$TARGET_DIR" && pwd)"
    if [ "$target_abs" = "$FRAMEWORK_ROOT" ]; then
      log "[skip]   AGENTS.md — refusing to write into the SDD framework repo itself ($FRAMEWORK_ROOT)."
      log "         Pass --target <your-project> to install AGENTS.md into a consumer project instead."
    else
      copy_one "$AGENTS_SRC" "$target_abs/AGENTS.md" || rc=1
    fi
  fi
fi

if [ "$DO_PROMPTS" = true ]; then
  if [ ! -d "$PROMPTS_SRC_DIR" ]; then
    log "[ERROR] prompts source missing: $PROMPTS_SRC_DIR"; exit 1
  fi
  for f in "$PROMPTS_SRC_DIR"/*.md; do
    [ -f "$f" ] || continue
    copy_one "$f" "$PROMPTS_DST_DIR/$(basename "$f")" || rc=1
  done
fi

log ""
if [ "$DRY_RUN" = true ]; then
  log "Dry-run complete. Nothing was written."
else
  log "Done. Review ./PARITY.md — the Codex adapter's guardrails are conventions, not enforced hooks."
fi
exit $rc
