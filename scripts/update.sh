#!/usr/bin/env bash
#
# Incremental update for an existing SDD install (spec 015): brings the clone
# and the central config directory up to date in one command, without ever
# touching adopter-owned files.
#
# Sequence: pre-flight (dirty-tree refusal) -> git pull --ff-only ->
# re-install with the profiles recorded in <central-dir>/.sdd-install.json ->
# agents refresh -> "What's new" report (version delta, CHANGELOG excerpt,
# added/updated/skipped counts, CLAUDE.md heading drift).
#
# Safety model (inherited from install.sh, see its header): never deletes,
# never stashes or resets the clone, differing files are skipped without
# --force (with --force they are backed up first), full --dry-run support.
# A dirty clone or a non-fast-forward pull is a hard error - resolving
# divergence is the adopter's decision, never this script's.
#
# Usage: scripts/update.sh [options]
#
#   --central-dir <path>   Central SDD config directory (default: ~/.claude-config)
#   --claude-home <path>   Per-user Claude Code config directory (default: ~/.claude)
#   --project-dir <path>   Linked project to refresh agents in (repeatable)
#   --claude-md <path>     CLAUDE.md file to check for heading drift (repeatable, report-only)
#   --force                Passed through to install.sh (overwrite differing files, backup first)
#   --dry-run              Preview all actions without writing anything
#   -h, --help             Show this help
#
# Exit codes: 0 = updated or already current, 1 = pre-flight/pull/install error.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

log()  { echo "[update]  $*"; }
skip() { echo "[skip]    $*"; }
warn() { echo "[warn]    $*"; }

CENTRAL_DIR="${CENTRAL_DIR:-$HOME/.claude-config}"
CLAUDE_HOME="${CLAUDE_HOME:-$HOME/.claude}"
DRY_RUN=0
FORCE=0
PROJECT_DIRS=()
CLAUDE_MDS=()

usage() {
  sed -n '2,29p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
}

while [ $# -gt 0 ]; do
  case "$1" in
    --central-dir) CENTRAL_DIR="$2"; shift 2 ;;
    --claude-home) CLAUDE_HOME="$2"; shift 2 ;;
    --project-dir) PROJECT_DIRS+=("$2"); shift 2 ;;
    --claude-md)   CLAUDE_MDS+=("$2"); shift 2 ;;
    --force)       FORCE=1; shift ;;
    --dry-run)     DRY_RUN=1; shift ;;
    -h|--help)     usage; exit 0 ;;
    *) echo "[ERROR]   Unknown option: $1 (see --help)"; exit 1 ;;
  esac
done

[ "$DRY_RUN" -eq 1 ] && log "DRY RUN MODE  - no files will be written, moved, or linked"

# ---------------------------------------------------------------------------
# Pre-flight: the clone must be a git repo with a clean working tree.
# A dirty tree is refused outright (FR-003): any automatic stash/reset could
# destroy adopter work, which is the one thing this script promises never to
# do. Nothing has been modified when this exits.
# ---------------------------------------------------------------------------
if ! git -C "$REPO_ROOT" rev-parse --git-dir >/dev/null 2>&1; then
  echo "[ERROR]   $REPO_ROOT is not a git repository. Incremental update needs the git clone this framework was installed from (a tarball/zip download cannot be updated this way  - clone the repo instead)."
  exit 1
fi

DIRTY="$(git -C "$REPO_ROOT" status --porcelain)"
if [ -n "$DIRTY" ]; then
  echo "[ERROR]   The clone at $REPO_ROOT has uncommitted changes  - refusing to pull over them:"
  echo "$DIRTY" | sed 's/^/[ERROR]     /'
  echo "[ERROR]   Commit, stash, or discard these changes yourself, then re-run. This script never stashes or resets for you."
  exit 1
fi

OLD_HEAD="$(git -C "$REPO_ROOT" rev-parse HEAD)"

# ---------------------------------------------------------------------------
# Pull, fast-forward only (FR-003). A non-ff result means the clone has
# diverged from upstream (local commits, a fork): that merge is the adopter's
# call. Offline/credential failures surface git's own message untouched.
# ---------------------------------------------------------------------------
if [ "$DRY_RUN" -eq 1 ]; then
  log "[dry-run] would run: git -C $REPO_ROOT pull --ff-only"
else
  if ! git -C "$REPO_ROOT" pull --ff-only; then
    echo "[ERROR]   git pull --ff-only failed (see git's message above)."
    echo "[ERROR]   If the clone has diverged from upstream (local commits or a fork), merge or rebase it yourself, then re-run. If this is a network/credential issue, fix connectivity and re-run. Nothing was modified."
    exit 1
  fi
fi

NEW_HEAD="$(git -C "$REPO_ROOT" rev-parse HEAD)"

if [ "$OLD_HEAD" = "$NEW_HEAD" ]; then
  log "Clone already up to date at $(git -C "$REPO_ROOT" describe --tags --always 2>/dev/null || echo "$NEW_HEAD")."
else
  log "Pulled $(git -C "$REPO_ROOT" rev-list --count "$OLD_HEAD..$NEW_HEAD") commit(s): ${OLD_HEAD:0:9} -> ${NEW_HEAD:0:9}"
fi

# ---------------------------------------------------------------------------
# Re-install with the profiles recorded at install time (FR-004). The
# manifest is framework-owned state: absent or corrupt just means
# unknown-version mode  - the installer's default profile applies, and the
# invoked installer rewrites the manifest at the end of its successful run,
# so the *next* update knows the version. utf-8-sig tolerates a BOM in case
# the manifest was written by an older PowerShell.
# ---------------------------------------------------------------------------
MANIFEST="$CENTRAL_DIR/.sdd-install.json"
OLD_VERSION=""
OLD_COMMIT=""
MANIFEST_PROFILES=""
MANIFEST_LINK=0
if [ -f "$MANIFEST" ]; then
  if MANIFEST_DATA="$(python3 - "$MANIFEST" <<'PYEOF'
import json
import sys
try:
    with open(sys.argv[1], encoding="utf-8-sig") as f:
        d = json.load(f)
except (OSError, ValueError):
    sys.exit(1)
print("VERSION:" + str(d.get("installedVersion", "")))
print("COMMIT:" + str(d.get("installedCommit", "")))
print("PROFILES:" + ",".join(p for p in d.get("profiles", []) if isinstance(p, str)))
print("LINK:" + ("1" if d.get("linkUserClaude") is True else "0"))
PYEOF
  )"; then
    while IFS= read -r line; do
      case "$line" in
        VERSION:*)  OLD_VERSION="${line#VERSION:}" ;;
        COMMIT:*)   OLD_COMMIT="${line#COMMIT:}" ;;
        PROFILES:*) MANIFEST_PROFILES="${line#PROFILES:}" ;;
        LINK:*)     MANIFEST_LINK="${line#LINK:}" ;;
      esac
    done <<< "$MANIFEST_DATA"
    log "Recorded install: version ${OLD_VERSION:-unknown}, profiles: ${MANIFEST_PROFILES:-none}"
  else
    warn "manifest $MANIFEST exists but is unreadable  - continuing in unknown-version mode (it will be rewritten by this run)"
  fi
else
  log "No install manifest at $MANIFEST  - first recorded update (unknown-version mode). This run will write one for next time."
fi

# Link mode mirrors the recorded install (FR-007): if the adopter linked
# ~/.claude last time, the installer re-copies agents there and refreshes the
# skills/hooks links in this same pass; otherwise we leave ~/.claude alone.
INSTALL_ARGS=(--central-dir "$CENTRAL_DIR" --claude-home "$CLAUDE_HOME")
if [ "$MANIFEST_LINK" = "1" ]; then
  INSTALL_ARGS+=(--link-user-claude)
  log "Recorded install linked ~/.claude  - refreshing its agent copies and links too."
else
  INSTALL_ARGS+=(--skip-link)
fi
if [ -n "$MANIFEST_PROFILES" ]; then
  IFS=',' read -ra _recorded_profiles <<< "$MANIFEST_PROFILES"
  for p in ${_recorded_profiles[@]+"${_recorded_profiles[@]}"}; do
    [ "$p" = "core" ] && continue  # core is always installed implicitly
    INSTALL_ARGS+=(--profile "$p")
  done
  log "Re-installing with recorded profiles: $MANIFEST_PROFILES"
else
  log "Re-installing with the installer's default profile (no recorded profiles)."
fi
[ "$DRY_RUN" -eq 1 ] && INSTALL_ARGS+=(--dry-run)
[ "$FORCE" -eq 1 ] && INSTALL_ARGS+=(--force)

INSTALL_LOG="$(mktemp)"
trap 'rm -f "$INSTALL_LOG"' EXIT

if ! "$REPO_ROOT/install.sh" "${INSTALL_ARGS[@]}" 2>&1 | tee "$INSTALL_LOG"; then
  echo "[ERROR]   install.sh failed (see its output above)  - the clone was pulled but the central dir may be partially refreshed. Re-run after fixing the reported problem."
  exit 1
fi

# Count parsing rides on the installer's stable line prefixes: a new file is
# logged as "<path> (new)", a forced overwrite contains "(overwritten", and
# an adopter-edited file is skipped with "differs from the central copy".
# Unchanged files are silent. update.test.sh asserts these counts so CI
# catches any future wording drift (see DECISIONS.md D002).
COUNT_NEW="$(grep -c ' (new)$' "$INSTALL_LOG" || true)"
COUNT_OVERWRITTEN="$(grep -c '(overwritten' "$INSTALL_LOG" || true)"
COUNT_LOCAL_EDITS="$(grep -c 'differs from the central copy' "$INSTALL_LOG" || true)"

# ---------------------------------------------------------------------------
# "What's new" report (FR-005). Version delta is measured from the commit
# actually recorded in the manifest (what the central dir last installed) to
# the clone's new HEAD  - this stays correct even if the clone was ahead of
# the central dir. Unknown-version mode falls back to the clone's pre-pull
# HEAD. Between the two points: added CHANGELOG release headers when the file
# moved, otherwise a raw git-log fallback.
# ---------------------------------------------------------------------------
FROM_REF="${OLD_COMMIT:-$OLD_HEAD}"
git -C "$REPO_ROOT" cat-file -e "$FROM_REF" 2>/dev/null || FROM_REF="$OLD_HEAD"
from_desc="$(git -C "$REPO_ROOT" describe --tags --always "$FROM_REF" 2>/dev/null || echo "${FROM_REF:0:9}")"
to_desc="$(git -C "$REPO_ROOT" describe --tags --always "$NEW_HEAD" 2>/dev/null || echo "${NEW_HEAD:0:9}")"

echo ""
log "===== What's new ====="
if [ "$FROM_REF" = "$NEW_HEAD" ]; then
  log "Already up to date at $to_desc  - nothing to install."
else
  log "Updated: $from_desc -> $to_desc"
  # Added CHANGELOG release headers ("## [x.y.z]") in the range, best-effort.
  changelog_new="$(git -C "$REPO_ROOT" diff "$FROM_REF..$NEW_HEAD" -- CHANGELOG.md 2>/dev/null \
    | grep -E '^\+## ' | sed 's/^+/  /' || true)"
  if [ -n "$changelog_new" ]; then
    log "Releases in this update (from CHANGELOG.md):"
    echo "$changelog_new"
  else
    log "Commits in this update:"
    git -C "$REPO_ROOT" log --oneline "$FROM_REF..$NEW_HEAD" 2>/dev/null | sed 's/^/  /' | head -20
  fi
fi

log "Central dir refreshed: ${COUNT_NEW:-0} new file(s), ${COUNT_OVERWRITTEN:-0} overwritten, ${COUNT_LOCAL_EDITS:-0} skipped with local edits."
if [ "${COUNT_LOCAL_EDITS:-0}" -gt 0 ]; then
  warn "Local edits detected in ${COUNT_LOCAL_EDITS} central-dir file(s) — left untouched. Re-run with --force to overwrite them (a timestamped backup is taken first):"
  grep 'differs from the central copy' "$INSTALL_LOG" | sed 's/^\[skip\]    /  /; s/  *- rerun.*$//' || true
fi

# ---------------------------------------------------------------------------
# Per-project refresh (FR-007). Agents are copied into a project's
# .claude/agents (never linked), so a central-dir update does not reach them
# on its own. Re-run link-project.sh for each named project  - it re-copies
# agents and refreshes the skills/hooks links, with the same skip/force/backup
# semantics. We reuse the script rather than reimplement the copy.
# ---------------------------------------------------------------------------
LINK_PROJECT_ARGS=(--central-dir "$CENTRAL_DIR")
[ "$DRY_RUN" -eq 1 ] && LINK_PROJECT_ARGS+=(--dry-run)
[ "$FORCE" -eq 1 ] && LINK_PROJECT_ARGS+=(--force)
for proj in ${PROJECT_DIRS[@]+"${PROJECT_DIRS[@]}"}; do
  if [ ! -d "$proj" ]; then
    warn "project dir $proj does not exist  - skipping its agent refresh"
    continue
  fi
  log "Refreshing linked project: $proj"
  if ! "$REPO_ROOT/link-project.sh" --project-dir "$proj" "${LINK_PROJECT_ARGS[@]}"; then
    warn "link-project.sh failed for $proj  - refresh it manually with: ./link-project.sh --project-dir $proj"
  fi
done

# ---------------------------------------------------------------------------
# Pending manual steps (FR-007). These edit adopter-owned surfaces
# (a project's settings.json, a project's CLAUDE.md) that update never touches
# on its own, so they are surfaced as reminders, not actions (see D004).
# ---------------------------------------------------------------------------
if [ "$FROM_REF" != "$NEW_HEAD" ]; then
  # New hook families in the pulled range -> wiring is a per-project action.
  new_hooks="$(git -C "$REPO_ROOT" diff --name-only --diff-filter=A "$FROM_REF..$NEW_HEAD" -- 'hooks/*.sh' 2>/dev/null || true)"
  if [ -n "$new_hooks" ]; then
    warn "This update ships new hook script(s): $(echo "$new_hooks" | sed 's#hooks/##g; s/\.sh//g' | tr '\n' ' ')"
    warn "  Wire them into each project that should enforce them: ./scripts/wire-hooks.sh --project-dir <project>"
  fi
  # CLAUDE.md.example changed -> adopters may have new sections to merge.
  if [ -n "$(git -C "$REPO_ROOT" diff --name-only "$FROM_REF..$NEW_HEAD" -- CLAUDE.md.example 2>/dev/null || true)" ]; then
    if [ ${#CLAUDE_MDS[@]} -eq 0 ]; then
      warn "CLAUDE.md.example changed in this update. Pass --claude-md <your-project-CLAUDE.md> to see which sections are new to merge."
    fi
  fi
fi

if [ "$MANIFEST_LINK" = "1" ] && [ ${#PROJECT_DIRS[@]} -eq 0 ]; then
  log "Note: agent copies in any linked projects are not refreshed by this run  - pass --project-dir <path> for each, or re-run ./link-project.sh there."
fi

# ---------------------------------------------------------------------------
# CLAUDE.md drift check (FR-006). For each --claude-md target, list the "## "
# section headings present in the shipped CLAUDE.md.example but absent from
# the adopter's file, as sections pending a manual merge. Report-only: the
# target is never written (the installer never touches a real CLAUDE.md, and
# neither does update). Comparison is CRLF-safe and at heading granularity
# only  - content changes inside an existing section are the adopter's to own
# (see D004 / spec assumptions), so they are not flagged.
# ---------------------------------------------------------------------------
EXAMPLE_MD="$REPO_ROOT/CLAUDE.md.example"
for target in ${CLAUDE_MDS[@]+"${CLAUDE_MDS[@]}"}; do
  if [ ! -f "$EXAMPLE_MD" ]; then
    warn "CLAUDE.md drift check skipped  - $EXAMPLE_MD not found"
    break
  fi
  if [ ! -f "$target" ]; then
    warn "CLAUDE.md drift check: target $target not found  - skipping (advisory only)"
    continue
  fi
  missing="$(python3 - "$EXAMPLE_MD" "$target" <<'PYEOF'
import sys

def headings(path):
    out = []
    with open(path, encoding="utf-8-sig", errors="replace") as f:
        for line in f:
            line = line.rstrip("\r\n")
            if line.startswith("## "):
                out.append(line[3:].strip())
    return out

example = headings(sys.argv[1])
have = set(headings(sys.argv[2]))
for h in example:              # preserve example order, de-dup
    if h not in have:
        print(h)
        have.add(h)
PYEOF
  )"
  if [ -n "$missing" ]; then
    warn "CLAUDE.md drift  - $target is missing these sections from CLAUDE.md.example (pending manual merge):"
    echo "$missing" | sed 's/^/  ## /'
  else
    log "CLAUDE.md drift  - $target has every section from CLAUDE.md.example (no merge pending)."
  fi
done

log "Done."
