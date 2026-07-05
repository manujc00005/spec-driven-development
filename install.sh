#!/usr/bin/env bash
#
# Installs this SDD workflow (skills, hooks, templates) into a central Claude
# Code configuration directory on macOS/Linux, and optionally links your
# per-user Claude Code home (~/.claude) to it.
#
# Safe to run from any clone location and safe to re-run:
#   - Never deletes anything. Only creates missing files/directories, or
#     (with --force) overwrites a file that differs from the source AFTER
#     taking a timestamped backup under <central-dir>/_install-backups/<ts>/.
#   - Never touches settings.local.json, under any path, ever.
#   - Never writes CLAUDE.md or settings.json directly  - only
#     CLAUDE.md.example and settings.template.json, so an existing real
#     CLAUDE.md/settings.json at the central directory is never silently
#     replaced.
#   - Linking ~/.claude/skills, ~/.claude/hooks, and ~/.claude/CLAUDE.md is
#     OPT-IN via --link-user-claude, because it touches your personal Claude
#     Code configuration, not just this repo's target.
#
# Usage: ./install.sh [options]
#
#   --central-dir <path>   Central SDD config directory (default: ~/.claude-config)
#   --claude-home <path>   Per-user Claude Code config directory (default: ~/.claude)
#   --force                Overwrite differing files (backs up first)
#   --dry-run              Preview actions without writing anything
#   --skip-link            Do not attempt any ~/.claude linking
#   --link-user-claude     Opt-in: link ~/.claude/skills, hooks, CLAUDE.md to the central dir
#   -h, --help             Show this help
#
# Note on the central directory default: this repo's Windows install target is
# the machine-wide C:\ProgramData\ClaudeConfig. There is no exact macOS/Linux
# equivalent that's writable without elevated privileges by default, so this
# script defaults to a user-level directory (~/.claude-config). If you want a
# genuinely machine-wide, multi-user location analogous to ProgramData, pass
# --central-dir /usr/local/etc/claude-config (may require sudo depending on
# your /usr/local permissions) and run any write step with sudo yourself.

set -euo pipefail

CENTRAL_DIR="${CENTRAL_DIR:-$HOME/.claude-config}"
CLAUDE_HOME="${CLAUDE_HOME:-$HOME/.claude}"
FORCE=0
DRY_RUN=0
SKIP_LINK=0
LINK_USER_CLAUDE=0

usage() {
  sed -n '2,26p' "$0" | sed 's/^# \{0,1\}//'
}

while [ $# -gt 0 ]; do
  case "$1" in
    --central-dir) CENTRAL_DIR="$2"; shift 2 ;;
    --claude-home) CLAUDE_HOME="$2"; shift 2 ;;
    --force) FORCE=1; shift ;;
    --dry-run) DRY_RUN=1; shift ;;
    --skip-link) SKIP_LINK=1; shift ;;
    --link-user-claude) LINK_USER_CLAUDE=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1"; usage; exit 1 ;;
  esac
done

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"

log()  { echo "[install] $*"; }
skip() { echo "[skip]    $*"; }
warn() { echo "[warn]    $*"; }

is_excluded() {
  case "$1" in
    *settings.local.json) return 0 ;;
    *) return 1 ;;
  esac
}

copy_tree_safely() {
  local src_dir="$1" dst_dir="$2" label="$3" backup_root="$4"
  [ -d "$src_dir" ] || { warn "$label: source $src_dir not found, skipping"; return; }

  while IFS= read -r -d '' f; do
    local rel="${f#"$src_dir"/}"
    if is_excluded "$rel"; then skip "$label/$rel (excluded pattern)"; continue; fi

    local dest="$dst_dir/$rel"
    local dest_dir
    dest_dir="$(dirname "$dest")"

    if [ ! -d "$dest_dir" ]; then
      if [ "$DRY_RUN" -eq 1 ]; then log "[dry-run] would create directory $dest_dir"; else mkdir -p "$dest_dir"; fi
    fi

    if [ ! -e "$dest" ]; then
      if [ "$DRY_RUN" -eq 1 ]; then log "[dry-run] would create $dest"; else cp "$f" "$dest"; fi
      log "$label/$rel  (new)"
      continue
    fi

    if cmp -s "$f" "$dest"; then
      continue
    fi

    if [ "$FORCE" -ne 1 ]; then
      skip "$label/$rel differs from the central copy  - rerun with --force to overwrite (a backup is taken first)"
      continue
    fi

    local backup="$backup_root/_install-backups/$TIMESTAMP/$label/$rel"
    if [ "$DRY_RUN" -eq 1 ]; then
      log "[dry-run] would back up $dest to $backup, then overwrite it with the repo version"
    else
      mkdir -p "$(dirname "$backup")"
      cp "$dest" "$backup"
      cp "$f" "$dest"
      log "$label/$rel  (overwritten  - previous version backed up to $backup)"
    fi
  done < <(find "$src_dir" -type f -print0)
}

set_dir_link() {
  local link_path="$1" target_path="$2" name="$3"
  local target="$CENTRAL_DIR/$target_path"

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
    warn "$name exists as a real directory (not a link)  - this looks like existing local data"
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

# ---------------------------------------------------------------------------

log "Repo root:          $REPO_ROOT"
log "Central config dir: $CENTRAL_DIR"
[ "$DRY_RUN" -eq 1 ] && log "DRY RUN MODE  - no files will be written, moved, or linked"
echo ""

if [ ! -d "$CENTRAL_DIR" ]; then
  if [ "$DRY_RUN" -eq 1 ]; then log "[dry-run] would create $CENTRAL_DIR"; else mkdir -p "$CENTRAL_DIR"; log "Created $CENTRAL_DIR"; fi
fi

copy_tree_safely "$REPO_ROOT/skills" "$CENTRAL_DIR/skills" "skills" "$CENTRAL_DIR"
copy_tree_safely "$REPO_ROOT/hooks" "$CENTRAL_DIR/hooks" "hooks" "$CENTRAL_DIR"
copy_tree_safely "$REPO_ROOT/specs/_templates" "$CENTRAL_DIR/specs/_templates" "specs/_templates" "$CENTRAL_DIR"

for root_file in CLAUDE.md.example settings.template.json; do
  src="$REPO_ROOT/$root_file"
  dst="$CENTRAL_DIR/$root_file"
  [ -f "$src" ] || continue

  if [ ! -e "$dst" ]; then
    if [ "$DRY_RUN" -eq 1 ]; then log "[dry-run] would create $dst"; else cp "$src" "$dst"; fi
    log "$root_file (new)"
    continue
  fi

  if cmp -s "$src" "$dst"; then continue; fi

  if [ "$FORCE" -ne 1 ]; then
    skip "$root_file differs from the version already at $CENTRAL_DIR  - rerun with --force to overwrite (backup taken first)"
    continue
  fi

  backup="$CENTRAL_DIR/_install-backups/$TIMESTAMP/$root_file"
  if [ "$DRY_RUN" -eq 1 ]; then
    log "[dry-run] would back up and overwrite $root_file"
  else
    mkdir -p "$(dirname "$backup")"
    cp "$dst" "$backup"
    cp "$src" "$dst"
    log "$root_file (overwritten  - backup at $backup)"
  fi
done

echo ""
log "NOTE: CLAUDE.md.example is never installed as CLAUDE.md. If $CENTRAL_DIR has no"
log "CLAUDE.md yet, copy CLAUDE.md.example to CLAUDE.md yourself and edit it there."
echo ""

if [ "$SKIP_LINK" -eq 1 ]; then
  log "Skipping ~/.claude linking (--skip-link)."
elif [ "$LINK_USER_CLAUDE" -ne 1 ]; then
  log "Skipping ~/.claude linking by default  - it touches your personal Claude Code config."
  log "Re-run with --link-user-claude to link \$CLAUDE_HOME/skills, /hooks, and /CLAUDE.md to $CENTRAL_DIR."
else
  echo ""
  log "Linking user Claude home ($CLAUDE_HOME) to the central config..."
  if [ ! -d "$CLAUDE_HOME" ]; then
    if [ "$DRY_RUN" -eq 1 ]; then log "[dry-run] would create $CLAUDE_HOME"; else mkdir -p "$CLAUDE_HOME"; fi
  fi

  set_dir_link "$CLAUDE_HOME/skills" "skills" "skills"
  set_dir_link "$CLAUDE_HOME/hooks" "hooks" "hooks"

  claude_md_target="$CENTRAL_DIR/CLAUDE.md"
  claude_md_link="$CLAUDE_HOME/CLAUDE.md"
  if [ ! -f "$claude_md_target" ]; then
    skip "CLAUDE.md link skipped  - $claude_md_target does not exist yet (this repo only ships CLAUDE.md.example)"
  elif [ -L "$claude_md_link" ]; then
    current="$(readlink "$claude_md_link")"
    if [ "$current" = "$claude_md_target" ]; then
      log "CLAUDE.md already correctly linked -> $claude_md_target (no-op)"
    else
      skip "$claude_md_link already exists and is not linked to $claude_md_target  - resolve manually"
    fi
  elif [ -e "$claude_md_link" ]; then
    skip "$claude_md_link exists as a real file  - resolve manually; this script will not touch an existing real CLAUDE.md without you reviewing it first"
  else
    if [ "$DRY_RUN" -eq 1 ]; then
      log "[dry-run] would create file symlink $claude_md_link -> $claude_md_target"
    else
      ln -s "$claude_md_target" "$claude_md_link"
      log "CLAUDE.md linked -> $claude_md_target"
    fi
  fi
fi

echo ""
log "Done."
