#!/usr/bin/env bash
#
# Links a specific project's .claude/skills and .claude/hooks to the central
# SDD configuration directory, via symlinks.
#
# Same safety model as install.sh:
#   - Never touches settings.local.json.
#   - An existing correct link is a no-op.
#   - An existing link pointing elsewhere is left alone unless --force.
#   - An existing real directory is backed up to <path>.bak-<timestamp> before
#     being replaced, and only with --force.
#
# Usage: ./link-project.sh [options]
#
#   --project-dir <path>   Project to link into (default: current directory)
#   --central-dir <path>   Central SDD config directory (default: ~/.claude-config)
#   --force                Overwrite an existing link pointing elsewhere, or
#                           back up and replace a real directory
#   --dry-run              Preview actions without writing anything
#   -h, --help              Show this help

set -euo pipefail

PROJECT_DIR="$(pwd)"
CENTRAL_DIR="${CENTRAL_DIR:-$HOME/.claude-config}"
FORCE=0
DRY_RUN=0

usage() {
  sed -n '2,18p' "$0" | sed 's/^# \{0,1\}//'
}

while [ $# -gt 0 ]; do
  case "$1" in
    --project-dir) PROJECT_DIR="$2"; shift 2 ;;
    --central-dir) CENTRAL_DIR="$2"; shift 2 ;;
    --force) FORCE=1; shift ;;
    --dry-run) DRY_RUN=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1"; usage; exit 1 ;;
  esac
done

TIMESTAMP="$(date +%Y%m%d-%H%M%S)"

log()  { echo "[link-project] $*"; }
skip() { echo "[skip]         $*"; }
warn() { echo "[warn]         $*"; }

if [ ! -d "$CENTRAL_DIR" ]; then
  warn "Central directory $CENTRAL_DIR does not exist. Run install.sh first."
  exit 1
fi

CLAUDE_DIR="$PROJECT_DIR/.claude"
if [ ! -d "$CLAUDE_DIR" ]; then
  if [ "$DRY_RUN" -eq 1 ]; then log "[dry-run] would create $CLAUDE_DIR"; else mkdir -p "$CLAUDE_DIR"; fi
fi

set_dir_link() {
  local link_path="$1" target_path="$2" name="$3"
  local target="$CENTRAL_DIR/$target_path"

  if [ ! -d "$target" ]; then
    skip "$name skipped  - $target does not exist in the central directory"
    return
  fi

  if [ -L "$link_path" ]; then
    local current
    current="$(readlink "$link_path")"
    if [ "$current" = "$target" ]; then
      log "$name already correctly linked -> $target (no-op)"
      return
    fi
    skip "$name is linked to a different target ($current)  - use --force to relink to $target"
    if [ "$FORCE" -ne 1 ]; then return; fi
    if [ "$DRY_RUN" -eq 1 ]; then log "[dry-run] would relink $name to $target"; else
      rm "$link_path"
      ln -s "$target" "$link_path"
      log "$name relinked -> $target"
    fi
    return
  fi

  if [ -e "$link_path" ]; then
    local backup="${link_path}.bak-$TIMESTAMP"
    warn "$name exists as a real directory (not a link)  - this looks like existing project-local content"
    if [ "$FORCE" -ne 1 ]; then
      skip "Not touching $link_path  - rerun with --force to back it up to $backup and replace it with a link"
      return
    fi
    if [ "$DRY_RUN" -eq 1 ]; then
      log "[dry-run] would back up $link_path to $backup and replace it with a symlink to $target"
    else
      mv "$link_path" "$backup"
      ln -s "$target" "$link_path"
      log "$name backed up to $backup and linked -> $target"
    fi
    return
  fi

  if [ "$DRY_RUN" -eq 1 ]; then
    log "[dry-run] would create symlink $link_path -> $target"
  else
    ln -s "$target" "$link_path"
    log "$name linked -> $target"
  fi
}

log "Project:     $PROJECT_DIR"
log "Central dir: $CENTRAL_DIR"
[ "$DRY_RUN" -eq 1 ] && log "DRY RUN MODE  - no files will be written, moved, or linked"
echo ""

set_dir_link "$CLAUDE_DIR/skills" "skills" "skills"
set_dir_link "$CLAUDE_DIR/hooks" "hooks" "hooks"

echo ""
log "settings.local.json is never touched by this script  - wire hook paths in .claude/settings.json yourself,"
log 'e.g. using "${CLAUDE_PROJECT_DIR}/.claude/hooks/git-guardrails.sh" (see settings.template.json).'
echo ""
log "Done."
