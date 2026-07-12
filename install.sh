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
#   - profiles.json separates SHIPPED items (skills/hooks/templates - must
#     exist on disk) from PLANNED items (plannedSkills/plannedHooks/
#     plannedTemplates - roadmap-only, may not exist). An unknown --profile
#     name, an explicit request for a disabled profile, or a shipped item
#     missing from disk are all hard errors (exit 1). Planned items are
#     reported as "[planned] ... not installed" and never cause an error.
#     Nothing is ever silently skipped for a typo.
#   - Requires python3 to resolve profiles.json (stdlib json only - jq is NOT
#     used by this script). If python3 is missing or profiles.json can't be
#     found/parsed, the script fails with a clear error. It never falls back
#     to installing everything unfiltered and never falls back to "no
#     filtering" - a profile-aware repo either resolves correctly or refuses.
#
# Usage: ./install.sh [options]
#
#   --central-dir <path>   Central SDD config directory (default: ~/.claude-config)
#   --claude-home <path>   Per-user Claude Code config directory (default: ~/.claude)
#   --profile <name>       Profile(s) to install (default: java-spring-backend from profiles.json).
#                          Core is always installed. Repeat or comma-separate for multiple:
#                            --profile java-spring-backend --profile messaging-event-driven
#                            --profile java-spring-backend,messaging-event-driven
#                          An unknown or disabled profile name aborts immediately with a
#                          clear error - it is never silently dropped.
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
PROFILE_ARGS=()

usage() {
  sed -n '2,46p' "$0" | sed 's/^# \{0,1\}//'
}

while [ $# -gt 0 ]; do
  case "$1" in
    --central-dir) CENTRAL_DIR="$2"; shift 2 ;;
    --claude-home) CLAUDE_HOME="$2"; shift 2 ;;
    --profile) PROFILE_ARGS+=("$2"); shift 2 ;;
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

# ---------------------------------------------------------------------------
# Profile resolution (requires python3 — NOT jq)
# ---------------------------------------------------------------------------
# Fails loudly (exit 1) on: python3 unavailable, profiles.json missing or
# invalid, an unknown profile name (typo protection), an explicit request for
# a disabled profile, or a shipped item declared in profiles.json that does
# not actually exist on disk (manifest/repo drift). None of these are silent
# skips, and none of them fall back to "install everything" or "no filtering"
# — a profile-aware repo either resolves profiles.json correctly, or the
# installer refuses to guess. Only *planned* items are skipped silently (by
# design — they are declared for roadmap visibility, not installation).
PROFILES_FILE="$REPO_ROOT/profiles.json"
PROFILE_FILTERING=0
declare -A ACTIVE_SKILLS_MAP=()
declare -A ACTIVE_HOOKS_MAP=()
declare -A ACTIVE_TEMPLATES_MAP=()
declare -A PLANNED_SKILLS_MAP=()
declare -A PLANNED_HOOKS_MAP=()
declare -A PLANNED_TEMPLATES_MAP=()
MISSING_SHIPPED=()

if [ ! -f "$PROFILES_FILE" ]; then
  echo "[ERROR]   profiles.json not found at $PROFILES_FILE. This repo requires it for profile-aware installation  - refusing to fall back to installing everything unfiltered."
  exit 1
fi

PY3_OK=0
if command -v python3 >/dev/null 2>&1 && python3 -c "import sys" >/dev/null 2>&1; then
  PY3_OK=1
fi
if [ "$PY3_OK" -ne 1 ]; then
  echo "[ERROR]   python3 is required to resolve profiles.json on macOS/Linux. Install Python 3 or use the Windows installer."
  exit 1
fi

PROFILE_FILTERING=1

# Flatten every --profile occurrence (each may itself be comma-separated) into
# one comma-separated string; python3 does the final split/trim/validation.
REQUESTED_CSV="$(IFS=,; echo "${PROFILE_ARGS[*]:-}")"

if PY_OUTPUT="$(python3 - "$PROFILES_FILE" "$REQUESTED_CSV" <<'PYEOF'
import json
import sys

profiles_file, requested_csv = sys.argv[1], sys.argv[2]

try:
    with open(profiles_file, "r", encoding="utf-8") as f:
        data = json.load(f)
except Exception as e:
    print(f"FATAL_ERROR:profiles.json exists but is not valid JSON: {e}")
    sys.exit(1)

requested = [p.strip() for p in requested_csv.split(",") if p.strip()]
if not requested:
    default_profile = data.get("defaults", {}).get("profile")
    if default_profile:
        requested = [default_profile]

profiles = data.get("profiles", {})
valid_names = list(profiles.keys())

fatal_errors = []
for name in requested:
    if name not in valid_names:
        fatal_errors.append(f"Unknown profile '{name}'. Valid profiles: {', '.join(valid_names)}")
        continue
    if profiles[name].get("disabled") is True:
        fatal_errors.append(
            f"Profile '{name}' is disabled by design (see profiles.json) and cannot be "
            f"installed via --profile. This is intentional, not a bug."
        )

if fatal_errors:
    for e in fatal_errors:
        print(f"FATAL_ERROR:{e}")
    sys.exit(1)

seen = set()
active_profiles = []
for p in ["core"] + requested:
    if p not in seen:
        seen.add(p)
        active_profiles.append(p)

shipped_skills, planned_skills = set(), set()
shipped_hooks, planned_hooks = set(), set()
shipped_templates, planned_templates = set(), set()

for name in active_profiles:
    pdef = profiles.get(name, {})
    shipped_skills.update(pdef.get("skills", []))
    planned_skills.update(pdef.get("plannedSkills", []))
    shipped_hooks.update(pdef.get("hooks", []))
    planned_hooks.update(pdef.get("plannedHooks", []))
    shipped_templates.update(pdef.get("templates", []))
    planned_templates.update(pdef.get("plannedTemplates", []))

print("ACTIVE_PROFILES:" + ",".join(active_profiles))
for s in sorted(shipped_skills):
    print(f"SKILL:{s}")
for s in sorted(planned_skills):
    print(f"PLANNED_SKILL:{s}")
for h in sorted(shipped_hooks):
    print(f"HOOK:{h}")
for h in sorted(planned_hooks):
    print(f"PLANNED_HOOK:{h}")
for t in sorted(shipped_templates):
    print(f"TEMPLATE:{t}")
for t in sorted(planned_templates):
    print(f"PLANNED_TEMPLATE:{t}")
PYEOF
)"; then
  PY_EXIT=0
else
  PY_EXIT=$?
fi

if [ "$PY_EXIT" -ne 0 ]; then
  echo ""
  while IFS= read -r line; do
    line="${line%$'\r'}"  # defensive: strip a trailing CR in case python3's stdout is CRLF-translated (native Windows Python)
    case "$line" in
      FATAL_ERROR:*) echo "[ERROR]   ${line#FATAL_ERROR:}" ;;
    esac
  done <<< "$PY_OUTPUT"
  echo "[ERROR]   Aborting before any files are touched. Fix the --profile argument and re-run."
  exit 1
fi

ACTIVE_PROFILES=()
while IFS= read -r line; do
  line="${line%$'\r'}"  # defensive: strip a trailing CR in case python3's stdout is CRLF-translated (native Windows Python)
  case "$line" in
    ACTIVE_PROFILES:*)
      IFS=',' read -ra ACTIVE_PROFILES <<< "${line#ACTIVE_PROFILES:}"
      ;;
    SKILL:*) ACTIVE_SKILLS_MAP["${line#SKILL:}"]=1 ;;
    PLANNED_SKILL:*) PLANNED_SKILLS_MAP["${line#PLANNED_SKILL:}"]=1 ;;
    HOOK:*) ACTIVE_HOOKS_MAP["${line#HOOK:}"]=1 ;;
    PLANNED_HOOK:*) PLANNED_HOOKS_MAP["${line#PLANNED_HOOK:}"]=1 ;;
    TEMPLATE:*) ACTIVE_TEMPLATES_MAP["${line#TEMPLATE:}"]=1 ;;
    PLANNED_TEMPLATE:*) PLANNED_TEMPLATES_MAP["${line#PLANNED_TEMPLATE:}"]=1 ;;
  esac
done <<< "$PY_OUTPUT"

# --- Integrity check: every SHIPPED item must exist on disk. A missing
#     shipped item means profiles.json has drifted from the repo. ---
for s in "${!ACTIVE_SKILLS_MAP[@]}"; do
  [ -d "$REPO_ROOT/skills/$s" ] || MISSING_SHIPPED+=("skill '$s' (expected at skills/$s/)")
done
for h in "${!ACTIVE_HOOKS_MAP[@]}"; do
  found=0
  for hf in "$REPO_ROOT/hooks/$h".*; do [ -f "$hf" ] && found=1; done
  [ "$found" -eq 1 ] || MISSING_SHIPPED+=("hook '$h' (expected hooks/$h.ps1 / hooks/$h.sh)")
done
for t in "${!ACTIVE_TEMPLATES_MAP[@]}"; do
  if [ ! -f "$REPO_ROOT/specs/_templates/$t" ] && [ ! -f "$REPO_ROOT/docs/_templates/$t" ]; then
    MISSING_SHIPPED+=("template '$t' (expected specs/_templates/$t or docs/_templates/$t)")
  fi
done
if [ ${#MISSING_SHIPPED[@]} -gt 0 ]; then
  echo ""
  echo "[ERROR]   profiles.json declares ${#MISSING_SHIPPED[@]} SHIPPED item(s) that do not exist in the repo:"
  for m in "${MISSING_SHIPPED[@]}"; do echo "[ERROR]     - $m"; done
  echo "[ERROR]   This is a manifest/repo integrity failure, not a planned gap  - fix profiles.json (move it to a planned* array if it's genuinely not built yet) or restore the missing file."
  echo ""
fi

log "Active profiles: ${ACTIVE_PROFILES[*]}"
log "Shipped  - skills: ${#ACTIVE_SKILLS_MAP[@]} | hooks: ${#ACTIVE_HOOKS_MAP[@]} | templates: ${#ACTIVE_TEMPLATES_MAP[@]}"
log "Planned  - skills: ${#PLANNED_SKILLS_MAP[@]} | hooks: ${#PLANNED_HOOKS_MAP[@]} | templates: ${#PLANNED_TEMPLATES_MAP[@]}"
for s in "${!PLANNED_SKILLS_MAP[@]}"; do echo "[planned] skill '$s'  - not installed (planned for a future phase)"; done
for h in "${!PLANNED_HOOKS_MAP[@]}"; do echo "[planned] hook '$h'  - not installed (planned for a future phase)"; done
for t in "${!PLANNED_TEMPLATES_MAP[@]}"; do echo "[planned] template '$t'  - not installed (planned for a future phase)"; done

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

# --- Skills (filtered by profile: each skill is a subdirectory) ---
if [ "$PROFILE_FILTERING" -eq 1 ]; then
  for skill_name in "${!ACTIVE_SKILLS_MAP[@]}"; do
    skill_dir="$REPO_ROOT/skills/$skill_name"
    if [ ! -d "$skill_dir" ]; then
      # Already reported under [ERROR] above (shipped item missing from disk) — don't copy.
      continue
    fi
    copy_tree_safely "$skill_dir" "$CENTRAL_DIR/skills/$skill_name" "skills/$skill_name" "$CENTRAL_DIR"
  done
else
  copy_tree_safely "$REPO_ROOT/skills" "$CENTRAL_DIR/skills" "skills" "$CENTRAL_DIR"
fi

# --- Hooks (filtered by profile: each hook is one or more files with the same base name) ---
if [ "$PROFILE_FILTERING" -eq 1 ]; then
  for hook_name in "${!ACTIVE_HOOKS_MAP[@]}"; do
    found=0
    for hook_file in "$REPO_ROOT/hooks/$hook_name".*; do
      [ -f "$hook_file" ] || continue
      found=1
      fname="$(basename "$hook_file")"
      dest="$CENTRAL_DIR/hooks/$fname"
      dest_dir="$(dirname "$dest")"
      [ -d "$dest_dir" ] || { if [ "$DRY_RUN" -eq 1 ]; then log "[dry-run] would create $dest_dir"; else mkdir -p "$dest_dir"; fi; }
      if [ ! -e "$dest" ]; then
        if [ "$DRY_RUN" -eq 1 ]; then log "[dry-run] would create $dest"; else cp "$hook_file" "$dest"; fi
        log "hooks/$fname  (new)"
      elif ! cmp -s "$hook_file" "$dest"; then
        if [ "$FORCE" -ne 1 ]; then
          skip "hooks/$fname differs  - rerun with --force to overwrite"
        else
          backup="$CENTRAL_DIR/_install-backups/$TIMESTAMP/hooks/$fname"
          if [ "$DRY_RUN" -eq 1 ]; then
            log "[dry-run] would back up and overwrite hooks/$fname"
          else
            mkdir -p "$(dirname "$backup")"
            cp "$dest" "$backup"
            cp "$hook_file" "$dest"
            log "hooks/$fname  (overwritten  - backup at $backup)"
          fi
        fi
      fi
    done
    # If found=0, this was already reported under [ERROR] above (shipped item missing from disk).
  done
  # Always copy hooks/README.md if it exists
  if [ -f "$REPO_ROOT/hooks/README.md" ]; then
    if [ ! -d "$CENTRAL_DIR/hooks" ]; then
      if [ "$DRY_RUN" -eq 1 ]; then log "[dry-run] would create directory $CENTRAL_DIR/hooks"; else mkdir -p "$CENTRAL_DIR/hooks"; fi
    fi
    dest="$CENTRAL_DIR/hooks/README.md"
    if [ ! -e "$dest" ]; then
      if [ "$DRY_RUN" -eq 1 ]; then log "[dry-run] would create hooks/README.md"; else cp "$REPO_ROOT/hooks/README.md" "$dest"; log "hooks/README.md  (new)"; fi
    fi
  fi
else
  copy_tree_safely "$REPO_ROOT/hooks" "$CENTRAL_DIR/hooks" "hooks" "$CENTRAL_DIR"
fi

# --- Templates (filtered by profile: from both specs/_templates and docs/_templates) ---
if [ "$PROFILE_FILTERING" -eq 1 ]; then
  for tpl_name in "${!ACTIVE_TEMPLATES_MAP[@]}"; do
    src_file=""
    dst_dir=""
    if [ -f "$REPO_ROOT/specs/_templates/$tpl_name" ]; then
      src_file="$REPO_ROOT/specs/_templates/$tpl_name"
      dst_dir="$CENTRAL_DIR/specs/_templates"
    elif [ -f "$REPO_ROOT/docs/_templates/$tpl_name" ]; then
      src_file="$REPO_ROOT/docs/_templates/$tpl_name"
      dst_dir="$CENTRAL_DIR/docs/_templates"
    else
      # Already reported under [ERROR] above (shipped item missing from disk) — don't copy.
      continue
    fi
    [ -d "$dst_dir" ] || { if [ "$DRY_RUN" -eq 1 ]; then log "[dry-run] would create $dst_dir"; else mkdir -p "$dst_dir"; fi; }
    dest="$dst_dir/$tpl_name"
    if [ ! -e "$dest" ]; then
      if [ "$DRY_RUN" -eq 1 ]; then log "[dry-run] would create $dest"; else cp "$src_file" "$dest"; fi
      log "templates/$tpl_name  (new)"
    elif ! cmp -s "$src_file" "$dest"; then
      if [ "$FORCE" -ne 1 ]; then
        skip "templates/$tpl_name differs  - rerun with --force to overwrite"
      else
        backup="$CENTRAL_DIR/_install-backups/$TIMESTAMP/templates/$tpl_name"
        if [ "$DRY_RUN" -eq 1 ]; then
          log "[dry-run] would back up and overwrite templates/$tpl_name"
        else
          mkdir -p "$(dirname "$backup")"
          cp "$dest" "$backup"
          cp "$src_file" "$dest"
          log "templates/$tpl_name  (overwritten  - backup at $backup)"
        fi
      fi
    fi
  done
else
  copy_tree_safely "$REPO_ROOT/specs/_templates" "$CENTRAL_DIR/specs/_templates" "specs/_templates" "$CENTRAL_DIR"
  copy_tree_safely "$REPO_ROOT/docs/_templates" "$CENTRAL_DIR/docs/_templates" "docs/_templates" "$CENTRAL_DIR"
fi

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
if [ ${#MISSING_SHIPPED[@]} -gt 0 ]; then
  echo "[ERROR]   Finished with ${#MISSING_SHIPPED[@]} shipped item(s) missing from the repo (see [ERROR] lines above). profiles.json is out of sync."
  exit 1
fi
log "Done."
