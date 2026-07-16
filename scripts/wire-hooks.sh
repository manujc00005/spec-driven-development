#!/usr/bin/env bash
#
# Wires the shipped SDD hooks into a project's .claude/settings.json by merging
# the "hooks" key from settings.template.sh.json.
#
# Safety model (same spirit as install.sh / link-project.sh):
#   - Never touches settings.local.json.
#   - Additive and idempotent: for each hook event, only template entries whose
#     command string is not already present in that event are appended; existing
#     entries are never removed, reordered or rewritten. Re-running is a no-op.
#     (Consequence: a shipped hook you deleted on purpose comes back on re-run —
#     this is an explicit command, so run it only when you want the full set.)
#   - A timestamped backup (settings.json.bak-<ts>) is taken before any write.
#   - Requires python3 (same dependency as install.sh).
#
# Usage: ./wire-hooks.sh [options]
#
#   --project-dir <path>   Project to wire (default: current directory)
#   --template <path>      Settings template to merge (default: first of
#                           $CENTRAL_DIR/settings.template.sh.json,
#                           <repo>/settings.template.sh.json)
#   --central-dir <path>   Central SDD config directory (default: ~/.claude-config)
#   --dry-run              Preview the merge without writing anything
#   -h, --help             Show this help

set -euo pipefail

PROJECT_DIR="$(pwd)"
CENTRAL_DIR="${CENTRAL_DIR:-$HOME/.claude-config}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TEMPLATE=""
DRY_RUN=0

usage() {
  sed -n '2,25p' "$0" | sed 's/^# \{0,1\}//'
}

while [ $# -gt 0 ]; do
  case "$1" in
    --project-dir) PROJECT_DIR="$2"; shift 2 ;;
    --template) TEMPLATE="$2"; shift 2 ;;
    --central-dir) CENTRAL_DIR="$2"; shift 2 ;;
    --dry-run) DRY_RUN=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1"; usage; exit 1 ;;
  esac
done

log()  { echo "[wire-hooks] $*"; }
warn() { echo "[warn]       $*"; }

if ! command -v python3 >/dev/null 2>&1; then
  warn "python3 is required (same dependency as install.sh)."
  exit 2
fi

if [ -z "$TEMPLATE" ]; then
  if [ -f "$CENTRAL_DIR/settings.template.sh.json" ]; then
    TEMPLATE="$CENTRAL_DIR/settings.template.sh.json"
  elif [ -f "$REPO_ROOT/settings.template.sh.json" ]; then
    TEMPLATE="$REPO_ROOT/settings.template.sh.json"
  fi
fi

if [ -z "$TEMPLATE" ] || [ ! -f "$TEMPLATE" ]; then
  warn "settings.template.sh.json not found (looked in $CENTRAL_DIR and $REPO_ROOT)."
  warn "Run install.sh first, or pass --template <path>."
  exit 1
fi

TARGET="$PROJECT_DIR/.claude/settings.json"
case "$TARGET" in
  *settings.local.json) warn "refusing to touch settings.local.json"; exit 1 ;;
esac

TIMESTAMP="$(date +%Y%m%d-%H%M%S)"

RESULT="$(python3 - "$TEMPLATE" "$TARGET" <<'PYEOF'
import json
import os
import sys

template_path, target_path = sys.argv[1], sys.argv[2]

with open(template_path) as f:
    template = json.load(f)
template_hooks = template.get("hooks", {})

if os.path.exists(target_path):
    with open(target_path) as f:
        try:
            settings = json.load(f)
        except json.JSONDecodeError as e:
            print(f"ERROR:target settings.json is not valid JSON: {e}")
            sys.exit(1)
else:
    settings = {}

if not isinstance(settings, dict):
    print("ERROR:target settings.json is not a JSON object")
    sys.exit(1)

def commands_in(groups):
    found = set()
    for group in groups:
        for hook in group.get("hooks", []):
            cmd = hook.get("command")
            if cmd:
                found.add(cmd)
    return found

hooks = settings.setdefault("hooks", {})
added, skipped = [], []

for event, template_groups in template_hooks.items():
    existing_groups = hooks.setdefault(event, [])
    existing_cmds = commands_in(existing_groups)
    for group in template_groups:
        new_hooks = [h for h in group.get("hooks", []) if h.get("command") not in existing_cmds]
        if not new_hooks:
            skipped.extend(h.get("command", "?") for h in group.get("hooks", []))
            continue
        new_group = {k: v for k, v in group.items() if k != "hooks"}
        new_group["hooks"] = new_hooks
        existing_groups.append(new_group)
        added.extend(h.get("command", "?") for h in new_hooks)
        skipped.extend(
            h.get("command", "?") for h in group.get("hooks", []) if h not in new_hooks
        )

if not added:
    print("NOCHANGE")
    sys.exit(0)

print("CHANGED")
for cmd in added:
    print(f"ADD:{cmd}")
for cmd in skipped:
    print(f"SKIP:{cmd}")
print("JSON_START")
print(json.dumps(settings, indent=2))
PYEOF
)" || { warn "${RESULT#ERROR:}"; exit 1; }

if [ "$RESULT" = "NOCHANGE" ]; then
  log "already wired — $TARGET contains every hook from $(basename "$TEMPLATE"). No changes."
  exit 0
fi

echo "$RESULT" | while IFS= read -r line; do
  case "$line" in
    ADD:*)  log "add:  ${line#ADD:}" ;;
    SKIP:*) log "keep: ${line#SKIP:} (already wired)" ;;
  esac
done

NEW_JSON="$(echo "$RESULT" | sed -n '/^JSON_START$/,$p' | sed '1d')"

if [ "$DRY_RUN" -eq 1 ]; then
  log "[dry-run] would write $TARGET (backup first if it exists)"
  exit 0
fi

mkdir -p "$PROJECT_DIR/.claude"
if [ -f "$TARGET" ]; then
  cp "$TARGET" "$TARGET.bak-$TIMESTAMP"
  log "backup: $TARGET.bak-$TIMESTAMP"
fi
printf '%s\n' "$NEW_JSON" > "$TARGET"
log "wired hooks into $TARGET"
log "make the hook scripts executable once: chmod +x <project>/.claude/hooks/*.sh"
