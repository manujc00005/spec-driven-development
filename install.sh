#!/usr/bin/env bash
#
# Installs this SDD workflow (skills, hooks, templates, agents) into a central
# Claude Code configuration directory on macOS/Linux, and optionally links your
# per-user Claude Code home (~/.claude) to it. Agents are always COPIED
# per-file (never symlinked as a directory), because ~/.claude/agents commonly
# contains user-authored agents that a directory link would hide.
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
#   --remove-profile <name>  Remove a profile: delete the items ONLY it owns and drop it
#                          from the install manifest, so scripts/update.sh stops
#                          re-installing it. Repeatable. Items still shipped by another
#                          recorded profile are kept; every deleted file is backed up
#                          under _install-backups/<ts>/removed/ first. 'core' cannot be
#                          removed. Combine with --dry-run to see exactly what would go.
#                          A run that only removes does NOT fall back to the default
#                          profile - it would re-install what you just removed.
#   --force                Overwrite differing files (backs up first)
#   --dry-run              Preview actions without writing anything
#   --skip-link            Do not attempt any ~/.claude linking
#   --link-user-claude     Opt-in: link ~/.claude/skills, hooks, CLAUDE.md to the central dir, and copy agents per-file into ~/.claude/agents
#   --no-personal          Skip restoring the personal layer from <central-dir>/personal/
#                          (spec 038). Without a payload present this is a no-op anyway.
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
NO_PERSONAL=0
PROFILE_ARGS=()
REMOVE_PROFILE_ARGS=()

usage() {
  # Print the leading comment block (line 2 to the first non-comment line)
  # rather than a hard-coded line range: a fixed range silently truncates the
  # options list the moment the header grows, which is how --force and friends
  # briefly vanished from --help while spec 034 was being written.
  awk 'NR == 1 { next } /^#/ { sub(/^# ?/, ""); print; next } { exit }' "$0"
}

while [ $# -gt 0 ]; do
  case "$1" in
    --central-dir) CENTRAL_DIR="$2"; shift 2 ;;
    --claude-home) CLAUDE_HOME="$2"; shift 2 ;;
    --profile) PROFILE_ARGS+=("$2"); shift 2 ;;
    --remove-profile) REMOVE_PROFILE_ARGS+=("$2"); shift 2 ;;
    --force) FORCE=1; shift ;;
    --dry-run) DRY_RUN=1; shift ;;
    --skip-link) SKIP_LINK=1; shift ;;
    --link-user-claude) LINK_USER_CLAUDE=1; shift ;;
    --no-personal) NO_PERSONAL=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1"; usage; exit 1 ;;
  esac
done

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"

# ---------------------------------------------------------------------------
# --remove-profile argument validation (spec 034 FR-010, FR-013).
# Pure argument checks, run before anything touches the filesystem. Membership
# in profiles.json is checked later, in remove_profiles(), once the file has
# been parsed - but still before any deletion (FR-008, AC-010).
# ---------------------------------------------------------------------------
for _rp in ${REMOVE_PROFILE_ARGS[@]+"${REMOVE_PROFILE_ARGS[@]}"}; do
  if [ -z "${_rp// /}" ]; then
    echo "[ERROR]   --remove-profile needs a profile name. Nothing was changed."
    exit 1
  fi
  if [ "$_rp" = "core" ]; then
    echo "[ERROR]   'core' cannot be removed: it is alwaysInstalled and every other profile builds on it. Nothing was changed."
    exit 1
  fi
  for _ap in ${PROFILE_ARGS[@]+"${PROFILE_ARGS[@]}"}; do
    case ",$_ap," in
      *",$_rp,"*)
        echo "[ERROR]   profile '$_rp' is named in both --profile and --remove-profile. Refusing to guess which you meant. Nothing was changed."
        exit 1 ;;
    esac
  done
done

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
# Plain indexed arrays, NOT `declare -A` associative arrays: macOS ships bash 3.2
# (pre-GPLv3) as /bin/bash, which has no associative arrays. Uniqueness is already
# guaranteed by the python3 resolver (it aggregates into sets and prints each item
# once, sorted). Empty-array expansions below use the `${arr[@]+"${arr[@]}"}` guard
# because bash 3.2 with `set -u` errors on expanding an empty array.
ACTIVE_SKILLS=()
ACTIVE_HOOKS=()
ACTIVE_TEMPLATES=()
ACTIVE_AGENTS=()
PLANNED_SKILLS=()
PLANNED_HOOKS=()
PLANNED_TEMPLATES=()
PLANNED_AGENTS=()
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

# Spec 034 D010: a run whose point is --remove-profile must not fall back to
# defaults.profile - that would delete the profile and re-install it in the
# same pass. Removal-only runs resolve to core alone; the remaining recorded
# profiles are then reported as unrefreshed by FR-004, which is the honest
# outcome and consistent with D007 (report, never auto-refresh).
SUPPRESS_DEFAULT_PROFILE=0
if [ ${#REMOVE_PROFILE_ARGS[@]} -gt 0 ] && [ ${#PROFILE_ARGS[@]} -eq 0 ]; then
  SUPPRESS_DEFAULT_PROFILE=1
fi

if PY_OUTPUT="$(python3 - "$PROFILES_FILE" "$REQUESTED_CSV" "$SUPPRESS_DEFAULT_PROFILE" <<'PYEOF'
import json
import sys

profiles_file, requested_csv = sys.argv[1], sys.argv[2]
suppress_default = len(sys.argv) > 3 and sys.argv[3] == "1"

try:
    with open(profiles_file, "r", encoding="utf-8") as f:
        data = json.load(f)
except Exception as e:
    print(f"FATAL_ERROR:profiles.json exists but is not valid JSON: {e}")
    sys.exit(1)

requested = [p.strip() for p in requested_csv.split(",") if p.strip()]
if not requested and suppress_default:
    pass  # removal-only run (D010): core alone, no default-profile fallback
elif not requested:
    default_profile = data.get("defaults", {}).get("profile")
    if default_profile:
        requested = [default_profile]
    else:
        # No --profile and no defaults.profile to fall back to. Without this
        # branch the run continues with an empty request and installs core
        # only, exiting 0 - a silent near-empty install that looks like a
        # success, contradicting the stated contract at the top of this file:
        # a profile-aware repo either resolves correctly or refuses.
        #
        # NOTE: keep single quotes BALANCED in this heredoc. bash 3.2 (the
        # macOS default) does not skip heredoc bodies when scanning for the
        # closing paren of $(...), so an odd number of apostrophes here is
        # read as an unterminated string and breaks the whole script.
        print(
            "FATAL_ERROR:no profile requested and profiles.json declares no "
            "'defaults.profile' to fall back to. Refusing to continue with a core-only "
            "install that would look like a success - pass --profile <name>, or repair "
            "defaults.profile in profiles.json."
        )
        sys.exit(1)

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
shipped_agents, planned_agents = set(), set()

for name in active_profiles:
    pdef = profiles.get(name, {})
    shipped_skills.update(pdef.get("skills", []))
    planned_skills.update(pdef.get("plannedSkills", []))
    shipped_hooks.update(pdef.get("hooks", []))
    planned_hooks.update(pdef.get("plannedHooks", []))
    shipped_templates.update(pdef.get("templates", []))
    planned_templates.update(pdef.get("plannedTemplates", []))
    # 'agents'/'plannedAgents' are optional (profiles.json 0.4.0) — a profile
    # without them simply ships no agents (backward compatible).
    shipped_agents.update(pdef.get("agents", []))
    planned_agents.update(pdef.get("plannedAgents", []))

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
for a in sorted(shipped_agents):
    print(f"AGENT:{a}")
for a in sorted(planned_agents):
    print(f"PLANNED_AGENT:{a}")
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
    SKILL:*) ACTIVE_SKILLS+=("${line#SKILL:}") ;;
    PLANNED_SKILL:*) PLANNED_SKILLS+=("${line#PLANNED_SKILL:}") ;;
    HOOK:*) ACTIVE_HOOKS+=("${line#HOOK:}") ;;
    PLANNED_HOOK:*) PLANNED_HOOKS+=("${line#PLANNED_HOOK:}") ;;
    TEMPLATE:*) ACTIVE_TEMPLATES+=("${line#TEMPLATE:}") ;;
    PLANNED_TEMPLATE:*) PLANNED_TEMPLATES+=("${line#PLANNED_TEMPLATE:}") ;;
    AGENT:*) ACTIVE_AGENTS+=("${line#AGENT:}") ;;
    PLANNED_AGENT:*) PLANNED_AGENTS+=("${line#PLANNED_AGENT:}") ;;
  esac
done <<< "$PY_OUTPUT"

# --- Integrity check: every SHIPPED item must exist on disk. A missing
#     shipped item means profiles.json has drifted from the repo. ---
for s in ${ACTIVE_SKILLS[@]+"${ACTIVE_SKILLS[@]}"}; do
  [ -d "$REPO_ROOT/skills/$s" ] || MISSING_SHIPPED+=("skill '$s' (expected at skills/$s/)")
done
for h in ${ACTIVE_HOOKS[@]+"${ACTIVE_HOOKS[@]}"}; do
  found=0
  for hf in "$REPO_ROOT/hooks/$h".*; do [ -f "$hf" ] && found=1; done
  [ "$found" -eq 1 ] || MISSING_SHIPPED+=("hook '$h' (expected hooks/$h.ps1 / hooks/$h.sh)")
done
for t in ${ACTIVE_TEMPLATES[@]+"${ACTIVE_TEMPLATES[@]}"}; do
  if [ ! -f "$REPO_ROOT/specs/_templates/$t" ] && [ ! -f "$REPO_ROOT/docs/_templates/$t" ]; then
    MISSING_SHIPPED+=("template '$t' (expected specs/_templates/$t or docs/_templates/$t)")
  fi
done
for a in ${ACTIVE_AGENTS[@]+"${ACTIVE_AGENTS[@]}"}; do
  [ -f "$REPO_ROOT/agents/$a.md" ] || MISSING_SHIPPED+=("agent '$a' (expected at agents/$a.md)")
done
if [ ${#MISSING_SHIPPED[@]} -gt 0 ]; then
  echo ""
  echo "[ERROR]   profiles.json declares ${#MISSING_SHIPPED[@]} SHIPPED item(s) that do not exist in the repo:"
  for m in "${MISSING_SHIPPED[@]}"; do echo "[ERROR]     - $m"; done
  echo "[ERROR]   This is a manifest/repo integrity failure, not a planned gap  - fix profiles.json (move it to a planned* array if it's genuinely not built yet) or restore the missing file."
  echo ""
fi

log "Active profiles: ${ACTIVE_PROFILES[*]}"
log "Shipped  - skills: ${#ACTIVE_SKILLS[@]} | hooks: ${#ACTIVE_HOOKS[@]} | templates: ${#ACTIVE_TEMPLATES[@]} | agents: ${#ACTIVE_AGENTS[@]}"
log "Planned  - skills: ${#PLANNED_SKILLS[@]} | hooks: ${#PLANNED_HOOKS[@]} | templates: ${#PLANNED_TEMPLATES[@]} | agents: ${#PLANNED_AGENTS[@]}"
for s in ${PLANNED_SKILLS[@]+"${PLANNED_SKILLS[@]}"}; do echo "[planned] skill '$s'  - not installed (planned for a future phase)"; done
for h in ${PLANNED_HOOKS[@]+"${PLANNED_HOOKS[@]}"}; do echo "[planned] hook '$h'  - not installed (planned for a future phase)"; done
for t in ${PLANNED_TEMPLATES[@]+"${PLANNED_TEMPLATES[@]}"}; do echo "[planned] template '$t'  - not installed (planned for a future phase)"; done
for a in ${PLANNED_AGENTS[@]+"${PLANNED_AGENTS[@]}"}; do echo "[planned] agent '$a'  - not installed (planned for a future phase)"; done

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

copy_file_safely() {
  # Single-file variant of copy_tree_safely: new -> copy; identical -> no-op;
  # differs -> skip without --force; differs + --force -> back up to $4, then
  # overwrite. Same excluded-pattern guard as every other copy path.
  local src_file="$1" dest="$2" label="$3" backup="$4"
  if is_excluded "$(basename "$dest")"; then skip "$label (excluded pattern)"; return; fi
  local dest_dir
  dest_dir="$(dirname "$dest")"
  if [ ! -d "$dest_dir" ]; then
    if [ "$DRY_RUN" -eq 1 ]; then log "[dry-run] would create directory $dest_dir"; else mkdir -p "$dest_dir"; fi
  fi
  if [ ! -e "$dest" ]; then
    if [ "$DRY_RUN" -eq 1 ]; then log "[dry-run] would create $dest"; else cp "$src_file" "$dest"; fi
    log "$label  (new)"
    return
  fi
  if cmp -s "$src_file" "$dest"; then return; fi
  if [ "$FORCE" -ne 1 ]; then
    skip "$label differs from the existing copy  - rerun with --force to overwrite (a backup is taken first)"
    return
  fi
  if [ "$DRY_RUN" -eq 1 ]; then
    log "[dry-run] would back up $dest to $backup, then overwrite it with the repo version"
  else
    mkdir -p "$(dirname "$backup")"
    cp "$dest" "$backup"
    cp "$src_file" "$dest"
    log "$label  (overwritten  - previous version backed up to $backup)"
  fi
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

# ---------------------------------------------------------------------------
# Profile removal (spec 034 FR-007..FR-014). The ONLY destructive path in this
# installer, so it is deliberately the most conservative one:
#   * ownership comes from profiles.json alone, never from the filesystem
#     (D004) - an item survives if ANY still-recorded profile ships it;
#   * every deletion is preceded by a backup, and a failed backup ABORTS the
#     removal instead of warning and continuing;
#   * it runs before the install pass, so ownership is computed against the
#     final recorded profile set.
# ---------------------------------------------------------------------------
remove_item_safely() {
  local path="$1" label="$2"
  if [ ! -e "$path" ]; then
    log "  $label  (not installed - nothing to remove)"
    return 0
  fi
  local backup="$CENTRAL_DIR/_install-backups/$TIMESTAMP/removed/$label"
  if [ "$DRY_RUN" -eq 1 ]; then
    log "  [dry-run] would back up $label -> $backup, then delete it"
    return 0
  fi
  if ! mkdir -p "$(dirname "$backup")"; then
    echo "[ERROR]   could not create backup directory for $label  - it was NOT deleted."
    return 1
  fi
  if ! cp -R "$path" "$backup"; then
    echo "[ERROR]   could not back up $label  - it was NOT deleted."
    return 1
  fi
  if ! rm -rf "$path"; then
    echo "[ERROR]   backed up $label but could not delete it  - central dir may be inconsistent."
    return 1
  fi
  log "  removed $label  (backup at $backup)"
  return 0
}

remove_profiles() {
  [ ${#REMOVE_PROFILE_ARGS[@]} -gt 0 ] || return 0

  local plan removed_csv status_file py_rc
  plan="$(mktemp)"
  status_file="$(mktemp)"
  removed_csv="$(IFS=,; echo "${REMOVE_PROFILE_ARGS[*]}")"
  py_rc=0

  local active_csv
  active_csv="$(IFS=,; echo "${ACTIVE_PROFILES[*]:-}")"
  python3 - "$PROFILES_FILE" "$CENTRAL_DIR/.sdd-install.json" "$removed_csv" "$plan" "$active_csv" > "$status_file" 2>&1 <<'PYEOF' || py_rc=$?
import json
import sys

profiles_file, manifest_path, removed_csv, plan_path = sys.argv[1:5]
active_csv = sys.argv[5] if len(sys.argv) > 5 else ""

with open(profiles_file, encoding="utf-8") as f:
    profiles = json.load(f).get("profiles", {})

requested = [p.strip() for p in removed_csv.split(",") if p.strip()]

# AC-010: the name is validated against the closed set of profiles.json keys
# BEFORE anything is deleted. Validating the name against a known set is a
# stronger guard than sanitising a path - a traversing name simply is not a
# profile.
unknown = [p for p in requested if p not in profiles]
if unknown:
    print("FATAL:unknown profile(s): " + ", ".join(unknown)
          + ". Valid profiles: " + ", ".join(profiles.keys()))
    sys.exit(1)

try:
    with open(manifest_path, encoding="utf-8-sig") as f:
        manifest = json.load(f)
    if not isinstance(manifest, dict):
        manifest = {}
except (OSError, ValueError):
    manifest = {}

recorded = [p for p in manifest.get("profiles", []) if isinstance(p, str)]

# FR-011: a valid but unrecorded profile is a no-op with a message, not an error.
to_remove = [p for p in requested if p in recorded]
for p in requested:
    if p not in recorded:
        print("NOOP:" + p)

lines = []
if to_remove:
    # Ownership is computed against the FINAL profile set, not merely the
    # recorded one: a profile being installed in this same run (--profile X
    # --remove-profile Y) is part of the outcome, so an item it ships must be
    # kept rather than deleted-then-reinstalled. Without this, a shared item
    # was backed up, deleted and immediately re-copied - correct in the end,
    # but it reported "removed" for a file that was staying, and a failure
    # between the two steps would have left it gone.
    active = [p.strip() for p in active_csv.split(",") if p.strip()]
    remaining = [p for p in recorded if p not in to_remove]
    for p in active:
        if p not in to_remove and p not in remaining:
            remaining.append(p)
    if "core" not in remaining:
        remaining.append("core")  # alwaysInstalled; never a removal candidate

    KINDS = (("skills", "skill"), ("hooks", "hook"),
             ("templates", "template"), ("agents", "agent"))

    for key, kind in KINDS:
        doomed, kept = set(), set()
        for p in to_remove:
            doomed.update(profiles.get(p, {}).get(key, []) or [])
        for p in remaining:
            kept.update(profiles.get(p, {}).get(key, []) or [])
        for item in sorted(doomed):
            # Defence in depth: profiles.json is repo content, but an item name
            # is joined to a path, so anything path-like is refused outright.
            if not isinstance(item, str) or "/" in item or "\\" in item or item.startswith("."):
                print("FATAL:refusing to act on suspicious item name %r in profile set" % (item,))
                sys.exit(1)
            if item in kept:
                lines.append("KEEP:%s:%s" % (kind, item))
            else:
                lines.append("DEL:%s:%s" % (kind, item))

with open(plan_path, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
    if lines:
        f.write("\n")

for p in to_remove:
    print("REMOVE:" + p)
PYEOF

  # The python block above wrote its status lines to a temp file so this shell
  # can act on them without wrapping a heredoc in $(...) - see the bash 3.2
  # note in the profile resolver.
  local to_remove=()
  local line
  while IFS= read -r line; do
    case "$line" in
      FATAL:*)  echo "[ERROR]   ${line#FATAL:} Nothing was changed." ;;
      NOOP:*)   log "Profile '${line#NOOP:}' is not recorded in the install manifest  - nothing to remove." ;;
      REMOVE:*) to_remove+=("${line#REMOVE:}") ;;
      *)        [ -n "$line" ] && echo "$line" ;;  # surface tracebacks etc.
    esac
  done < "$status_file"
  rm -f "$status_file"

  if [ "$py_rc" -ne 0 ]; then
    rm -f "$plan"
    echo "[ERROR]   --remove-profile failed validation. Nothing was changed."
    exit 1
  fi

  if [ ${#to_remove[@]} -eq 0 ]; then
    rm -f "$plan"
    return 0
  fi

  log "Removing profile(s): ${to_remove[*]}"

  local kind item failed=0
  local kept_count=0
  while IFS=: read -r verb kind item; do
    [ -n "${item:-}" ] || continue
    if [ "$verb" = "KEEP" ]; then
      kept_count=$((kept_count + 1))
      log "  keeping $kind/$item  (still shipped by another recorded profile)"
      continue
    fi
    case "$kind" in
      skill)    remove_item_safely "$CENTRAL_DIR/skills/$item" "skills/$item" || failed=1 ;;
      agent)    remove_item_safely "$CENTRAL_DIR/agents/$item.md" "agents/$item.md" || failed=1 ;;
      template)
        if [ -e "$CENTRAL_DIR/specs/_templates/$item" ]; then
          remove_item_safely "$CENTRAL_DIR/specs/_templates/$item" "specs/_templates/$item" || failed=1
        elif [ -e "$CENTRAL_DIR/docs/_templates/$item" ]; then
          remove_item_safely "$CENTRAL_DIR/docs/_templates/$item" "docs/_templates/$item" || failed=1
        else
          log "  templates/$item  (not installed - nothing to remove)"
        fi ;;
      hook)
        local hook_file found=0
        for hook_file in "$CENTRAL_DIR/hooks/$item".*; do
          [ -e "$hook_file" ] || continue
          found=1
          remove_item_safely "$hook_file" "hooks/$(basename "$hook_file")" || failed=1
        done
        [ "$found" -eq 1 ] || log "  hooks/$item  (not installed - nothing to remove)" ;;
    esac
  done < "$plan"
  rm -f "$plan"

  [ "$kept_count" -gt 0 ] && log "  $kept_count item(s) kept because another recorded profile still ships them."

  if [ "$failed" -ne 0 ]; then
    echo "[ERROR]   removal did not complete (see [ERROR] above). Items reported as 'removed' above ARE deleted and are recoverable from $CENTRAL_DIR/_install-backups/$TIMESTAMP/removed/; the rest were left in place. The manifest was NOT modified, so re-running the same command retries, and 'install.sh --profile <name>' restores the profile outright."
    exit 1
  fi

  # FR-007: drop the profiles from the manifest. Dry-run leaves it untouched
  # (AC-008) - nothing was deleted either, so the record must still match.
  if [ "$DRY_RUN" -eq 1 ]; then
    log "[dry-run] would remove ${to_remove[*]} from the install manifest"
    return 0
  fi
  if ! python3 - "$CENTRAL_DIR/.sdd-install.json" "$(IFS=,; echo "${to_remove[*]}")" <<'PYEOF'
import json
import sys

manifest_path, removed_csv = sys.argv[1:3]
removed = {p for p in removed_csv.split(",") if p}
try:
    with open(manifest_path, encoding="utf-8-sig") as f:
        d = json.load(f)
except (OSError, ValueError):
    raise SystemExit(0)  # nothing recorded to clean up
if not isinstance(d, dict):
    raise SystemExit(0)
d["profiles"] = [p for p in d.get("profiles", []) if p not in removed]
state = d.get("profileState")
if isinstance(state, dict):
    d["profileState"] = {k: v for k, v in state.items() if k not in removed}
with open(manifest_path, "w", encoding="utf-8") as f:
    json.dump(d, f, indent=2)
    f.write("\n")
PYEOF
  then
    warn "profile files were removed but the manifest could not be updated  - re-run the installer to resynchronise it"
    return 0
  fi
  log "Install manifest updated  - removed: ${to_remove[*]}"
}

remove_profiles

# --- Skills (filtered by profile: each skill is a subdirectory) ---
if [ "$PROFILE_FILTERING" -eq 1 ]; then
  for skill_name in ${ACTIVE_SKILLS[@]+"${ACTIVE_SKILLS[@]}"}; do
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
  for hook_name in ${ACTIVE_HOOKS[@]+"${ACTIVE_HOOKS[@]}"}; do
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
    # Spec 034 FR-015/D009: shipped documentation, refreshed like every other
    # shipped file. The old write-once guard protected adopter edits by going
    # permanently stale and reporting nothing; copy_file_safely protects them
    # properly - it only overwrites under --force, and backs up first.
    copy_file_safely "$REPO_ROOT/hooks/README.md" "$CENTRAL_DIR/hooks/README.md" \
      "hooks/README.md" "$CENTRAL_DIR/_install-backups/$TIMESTAMP/hooks/README.md"
  fi
  # Always copy hooks/lib/: it is a shared dependency sourced by several hooks
  # (git-guardrails, sdd-spec-guard, ...), not a per-profile item — without it
  # those hooks crash with exit 1 and guardrails silently stop blocking.
  copy_tree_safely "$REPO_ROOT/hooks/lib" "$CENTRAL_DIR/hooks/lib" "hooks/lib" "$CENTRAL_DIR"
else
  copy_tree_safely "$REPO_ROOT/hooks" "$CENTRAL_DIR/hooks" "hooks" "$CENTRAL_DIR"
fi

# --- Templates (filtered by profile: from both specs/_templates and docs/_templates) ---
if [ "$PROFILE_FILTERING" -eq 1 ]; then
  for tpl_name in ${ACTIVE_TEMPLATES[@]+"${ACTIVE_TEMPLATES[@]}"}; do
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

# --- Agents (filtered by profile: each agent is a single agents/<name>.md file) ---
if [ "$PROFILE_FILTERING" -eq 1 ]; then
  for agent_name in ${ACTIVE_AGENTS[@]+"${ACTIVE_AGENTS[@]}"}; do
    agent_file="$REPO_ROOT/agents/$agent_name.md"
    if [ ! -f "$agent_file" ]; then
      # Already reported under [ERROR] above (shipped item missing from disk) — don't copy.
      continue
    fi
    copy_file_safely "$agent_file" "$CENTRAL_DIR/agents/$agent_name.md" "agents/$agent_name.md" "$CENTRAL_DIR/_install-backups/$TIMESTAMP/agents/$agent_name.md"
  done
  # Always copy agents/README.md if it exists (documentation only, not an agent)
  if [ -f "$REPO_ROOT/agents/README.md" ] && [ ${#ACTIVE_AGENTS[@]} -gt 0 ]; then
    # Spec 034 FR-015/D009 - see the hooks/README.md note above.
    copy_file_safely "$REPO_ROOT/agents/README.md" "$CENTRAL_DIR/agents/README.md" \
      "agents/README.md" "$CENTRAL_DIR/_install-backups/$TIMESTAMP/agents/README.md"
  fi
else
  copy_tree_safely "$REPO_ROOT/agents" "$CENTRAL_DIR/agents" "agents" "$CENTRAL_DIR"
fi

for root_file in CLAUDE.md.example settings.template.json settings.template.sh.json; do
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
log "NOTE: hooks do not run until they are wired into a project's .claude/settings.json."
log "After linking a project (link-project.sh), run scripts/wire-hooks.sh --project-dir <path>"
log "to merge the shipped hook wiring there (explicit, additive, backup first)."
echo ""
log "OPTIONAL: to adopt Graphify (dependency-graph accelerator) in a project, run"
log "scripts/setup-graphify.sh --project-dir <path> — it installs the CLI after"
log "confirmation, generates .graphify/, and scaffolds the curated docs."
echo ""

# Spec 039: links $CLAUDE_HOME/CLAUDE.md to the central one. Returns 0 when the
# question is SETTLED (linked now, already correct, or deliberately left alone)
# and 1 ONLY when the central CLAUDE.md does not exist yet - the one case the
# caller can fix by retrying after the personal import.
#
# No symlink/hardlink/copy ladder here, unlike install.ps1: `ln -s` needs no
# privilege on macOS/Linux, so there is no failure to fall back from (D004).
link_central_claude_md() {
  local claude_md_target="$CENTRAL_DIR/CLAUDE.md"
  local claude_md_link="$CLAUDE_HOME/CLAUDE.md"
  local current

  [ -f "$claude_md_target" ] || return 1

  if [ -L "$claude_md_link" ]; then
    current="$(readlink "$claude_md_link")"
    if [ "$current" = "$claude_md_target" ]; then
      log "CLAUDE.md already correctly linked -> $claude_md_target (no-op)"
    else
      skip "$claude_md_link already exists and is not linked to $claude_md_target  - resolve manually"
    fi
  elif [ -e "$claude_md_link" ]; then
    skip "$claude_md_link exists as a real file  - resolve manually; this script will not touch an existing real CLAUDE.md without you reviewing it first"
  elif [ "$DRY_RUN" -eq 1 ]; then
    log "[dry-run] would create file symlink $claude_md_link -> $claude_md_target"
  else
    ln -s "$claude_md_target" "$claude_md_link"
    log "CLAUDE.md linked -> $claude_md_target"
  fi
  return 0
}

# Spec 039 BUG-1: raised when the link could not be made because the central
# CLAUDE.md did not exist yet, and the personal import may still create it.
CLAUDE_MD_PENDING=0

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

  # Agents are COPIED per-file into $CLAUDE_HOME/agents, never symlinked as a
  # directory: that directory commonly contains user-authored agents that a
  # directory link would hide. Additive only  - existing files that differ are
  # skipped without --force; with --force they are backed up next to
  # themselves first.
  for agent_name in ${ACTIVE_AGENTS[@]+"${ACTIVE_AGENTS[@]}"}; do
    src_agent="$CENTRAL_DIR/agents/$agent_name.md"
    if [ ! -f "$src_agent" ]; then skip "agents/$agent_name.md not present in central dir  - run the install step first"; continue; fi
    copy_file_safely "$src_agent" "$CLAUDE_HOME/agents/$agent_name.md" "~/.claude/agents/$agent_name.md" "$CLAUDE_HOME/agents/$agent_name.md.bak-$TIMESTAMP"
  done

  # Spec 039 BUG-1: on a FIRST install $CENTRAL_DIR/CLAUDE.md does not exist yet
  # - the personal layer, imported near the end of this script, is what creates
  # it. A pending result is retried after that import, and the "does not exist
  # yet" message is deferred to the retry so the transcript never says "skipped"
  # and then "linked" about the same file (D002).
  if ! link_central_claude_md; then CLAUDE_MD_PENDING=1; fi
fi

echo ""
if [ ${#MISSING_SHIPPED[@]} -gt 0 ]; then
  echo "[ERROR]   Finished with ${#MISSING_SHIPPED[@]} shipped item(s) missing from the repo (see [ERROR] lines above). profiles.json is out of sync."
  exit 1
fi

# ---------------------------------------------------------------------------
# Install manifest (spec 015 FR-001): records what this run installed so
# scripts/update.sh can answer "what's new since your version?". Written only
# after a successful non-dry-run install; a write failure is a warning, never
# an install failure. Profiles accumulate across runs (a later
# --profile messaging-event-driven merges into the list); linkUserClaude is
# sticky once any run has linked. A corrupt existing manifest is discarded
# silently  - it is framework-owned state, never adopter content.
# ---------------------------------------------------------------------------
write_install_manifest() {
  local manifest="$CENTRAL_DIR/.sdd-install.json"
  local commit version report
  commit="$(git -C "$REPO_ROOT" rev-parse HEAD 2>/dev/null || echo unknown)"
  version="$(git -C "$REPO_ROOT" describe --tags --always 2>/dev/null || echo "$commit")"
  # Spec 034 FR-004: python reports unrefreshed profiles through a temp file
  # rather than stdout. Capturing stdout would mean wrapping the heredoc in
  # $(...), and bash 3.2 does not skip heredoc bodies when scanning for the
  # closing paren — the same landmine documented in the profile resolver above.
  report="$(mktemp)"
  if ! python3 - "$manifest" "$version" "$commit" "$REPO_ROOT" "$LINK_USER_CLAUDE" "$report" ${ACTIVE_PROFILES[@]+"${ACTIVE_PROFILES[@]}"} <<'PYEOF'
import datetime
import json
import sys

manifest_path, version, commit, source_clone, link_flag, report_path = sys.argv[1:7]
active = sys.argv[7:]

SCHEMA_VERSION = 2

old = {}
try:
    with open(manifest_path, encoding="utf-8-sig") as f:
        loaded = json.load(f)
    if isinstance(loaded, dict):
        old = loaded
except (OSError, ValueError):
    pass  # absent or corrupt -> start fresh; never fatal

# Spec 034 D003: only schema versions this installer understands are carried
# forward. A future version is discarded wholesale rather than misread
# key-by-key, matching the installer's standing refusal to guess.
old_schema = old.get("schemaVersion")
if old_schema not in (1, 2):
    old = {}

existing_profiles = [p for p in old.get("profiles", []) if isinstance(p, str)]
existing_commit = old.get("installedCommit")

# Normalize whatever we found into a {profile: {commit, version, installedAt}}
# map. v1 had no per-profile record, so D003 attributes its single top-level
# commit to every recorded profile: knowingly optimistic, but it asserts
# nothing the v1 format did not already assert for the whole set.
state = {}
raw_state = old.get("profileState")
if not isinstance(raw_state, dict):
    raw_state = {}
for name in existing_profiles:
    entry = raw_state.get(name)
    if isinstance(entry, dict) and isinstance(entry.get("commit"), str):
        state[name] = {
            "commit": entry.get("commit"),
            "version": entry.get("version") or entry.get("commit"),
            "installedAt": entry.get("installedAt"),
        }
    else:
        # v1, or a v2 manifest missing an entry for a recorded profile.
        state[name] = {
            "commit": existing_commit,
            "version": old.get("installedVersion") or existing_commit,
            "installedAt": old.get("installedAt"),
        }

merged = list(dict.fromkeys(existing_profiles + active))

now = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")

# installedAt means "when this version was installed", not "last run": preserve
# it when re-installing the same commit so a no-op update leaves the manifest
# byte-identical (spec 015 AC-003, spec 034 FR-006). Applied per profile.
for name in active:
    previous = state.get(name) or {}
    if previous.get("commit") == commit and previous.get("installedAt"):
        installed_at = previous["installedAt"]
    else:
        installed_at = now
    state[name] = {"commit": commit, "version": version, "installedAt": installed_at}

# Only profiles still on the list keep a record.
state = {name: state[name] for name in merged if name in state}

# Spec 034 FR-004: everything recorded but not active this run kept its old
# files, so it is stale by definition. Reported, never silently refreshed
# (D007).
active_set = set(active)
unrefreshed = [n for n in merged if n not in active_set]
with open(report_path, "w", encoding="utf-8") as f:
    for name in unrefreshed:
        entry = state.get(name) or {}
        stamp = entry.get("version") or entry.get("commit") or "unknown"
        f.write("%s\t%s\n" % (name, stamp))

if existing_commit == commit and old.get("installedAt"):
    top_installed_at = old["installedAt"]
else:
    top_installed_at = now

data = {
    "schemaVersion": SCHEMA_VERSION,
    # Spec 034 FR-005: top level means "the newest commit any profile reached",
    # retained so a pre-034 reader still resolves. It is NOT a freshness claim
    # about every recorded profile — that is what profileState is for, and
    # scripts/update.sh must take its delta from the oldest entry there.
    "installedVersion": version,
    "installedCommit": commit,
    "installedAt": top_installed_at,
    "profiles": merged,
    "profileState": state,
    "linkUserClaude": old.get("linkUserClaude") is True or link_flag == "1",
    "sourceClone": source_clone,
}
with open(manifest_path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)
    f.write("\n")
PYEOF
  then
    rm -f "$report"
    warn "could not write install manifest $manifest  - scripts/update.sh will run in unknown-version mode until a later install succeeds"
    return 0
  fi
  log "Install manifest written -> $manifest"
  report_unrefreshed_profiles "$report"
  rm -f "$report"
}

# Spec 034 FR-004: name every recorded profile this run did not refresh, with
# the commit it is stuck at and the exact command that fixes it. Informational
# only — it must never change the exit code, and it prints nothing when the
# active set already covered every recorded profile.
report_unrefreshed_profiles() {
  local report="$1"
  [ -s "$report" ] || return 0
  local count
  count="$(wc -l < "$report" | tr -d ' ')"
  warn "$count recorded profile(s) were NOT refreshed by this run - their files are still at the commit shown:"
  local name stamp
  while IFS="$(printf '\t')" read -r name stamp; do
    [ -n "$name" ] || continue
    warn "    $name  (installed at $stamp)"
  done < "$report"
  local cmd="./install.sh --force"
  while IFS="$(printf '\t')" read -r name stamp; do
    [ -n "$name" ] || continue
    [ "$name" = "core" ] && continue  # always installed implicitly
    cmd="$cmd --profile $name"
  done < "$report"
  [ "$LINK_USER_CLAUDE" -eq 1 ] && cmd="$cmd --link-user-claude"
  [ "$CENTRAL_DIR" != "$HOME/.claude-config" ] && cmd="$cmd --central-dir $CENTRAL_DIR"
  warn "  refresh them with:  $cmd"
}

if [ "$DRY_RUN" -eq 1 ]; then
  log "[dry-run] would write install manifest $CENTRAL_DIR/.sdd-install.json"
else
  write_install_manifest
fi

# --- Personal layer (spec 038) ---------------------------------------------
# Restores CLAUDE.md, settings.json, agents and memory from <central-dir>/personal/.
# ADDITIVE ONLY: never overwrites an existing file. Absent payload -> silent no-op,
# so a fresh clone installs exactly as it did before this existed.
if [ "$NO_PERSONAL" -eq 0 ] && [ -d "$CENTRAL_DIR/personal" ]; then
  if [ "$DRY_RUN" -eq 1 ]; then
    log "[dry-run] would import the personal layer from $CENTRAL_DIR/personal"
  else
    log "Restoring personal layer from $CENTRAL_DIR/personal ..."
    CENTRAL_DIR="$CENTRAL_DIR" CLAUDE_HOME="$CLAUDE_HOME" \
      bash "$REPO_ROOT/scripts/import-personal-config.sh" || true
  fi
fi

# Spec 039 BUG-1: the personal import above is what creates $CENTRAL_DIR/CLAUDE.md
# on a first install, so the link attempted earlier must be retried here. Only
# now, if the file still is not there, is the skip reported (D002).
if [ "$CLAUDE_MD_PENDING" -eq 1 ]; then
  if ! link_central_claude_md; then
    skip "CLAUDE.md link skipped  - $CENTRAL_DIR/CLAUDE.md does not exist yet (this repo only ships CLAUDE.md.example)"
  fi
fi

log "Done."
