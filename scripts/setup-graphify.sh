#!/usr/bin/env bash
#
# Adopts Graphify in an SDD project: installs the external @sentropic/graphify
# CLI (with confirmation), generates the dependency graph under .graphify/,
# gitignores the raw output, scaffolds the curated docs from templates, and
# wires the Graphify hooks (freshness reminder + graph-first nudge) into the
# project's .claude/settings.json so the whole loop runs with no manual steps.
#
# Safety model (same spirit as wire-hooks.sh):
#   - Idempotent: re-running refreshes the graph and the copied hook scripts but
#     never duplicates .gitignore entries, overwrites curated docs, or
#     double-wires a hook already present in settings.json.
#   - Degrades gracefully: missing npm is a message, not a failure (exit 0);
#     missing python3 copies the hooks but skips settings wiring (non-fatal).
#   - Never touches settings.local.json; backs settings.json up before writing.
#   - Installs software only after explicit confirmation (or --yes).
#
# Usage: ./setup-graphify.sh [options]
#
#   --project-dir <path>   Project to adopt Graphify in (default: current directory)
#   --central-dir <path>   Central SDD config directory (default: ~/.claude-config)
#   --yes                  Skip the npm install confirmation prompt
#   -h, --help             Show this help

set -euo pipefail

PROJECT_DIR="$(pwd)"
CENTRAL_DIR="${CENTRAL_DIR:-$HOME/.claude-config}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ASSUME_YES=0

usage() {
  sed -n '2,19p' "$0" | sed 's/^# \{0,1\}//'
}

while [ $# -gt 0 ]; do
  case "$1" in
    --project-dir) PROJECT_DIR="$2"; shift 2 ;;
    --central-dir) CENTRAL_DIR="$2"; shift 2 ;;
    --yes) ASSUME_YES=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1"; usage; exit 1 ;;
  esac
done

log()  { echo "[setup-graphify] $*"; }
warn() { echo "[warn]           $*"; }

if [ ! -d "$PROJECT_DIR" ]; then
  warn "Project directory not found: $PROJECT_DIR"
  exit 1
fi
cd "$PROJECT_DIR"

# --- 1. Ensure the graphify CLI is available -------------------------------
if ! command -v graphify >/dev/null 2>&1; then
  if ! command -v npm >/dev/null 2>&1; then
    warn "npm is not installed, and Graphify is an npm package (@sentropic/graphify)."
    warn "Install Node.js/npm first (https://nodejs.org), then re-run this script."
    warn "SDD works fine without Graphify — this only skips the accelerator."
    exit 0
  fi
  if [ "$ASSUME_YES" -ne 1 ]; then
    printf "[setup-graphify] Install @sentropic/graphify globally via npm? [y/N] "
    read -r answer || answer="" # closed stdin (non-interactive) counts as "no"
    case "$answer" in
      y|Y|yes|YES) ;;
      *) log "Skipped install. Re-run with --yes to install non-interactively."; exit 0 ;;
    esac
  fi
  log "Installing @sentropic/graphify globally..."
  if ! npm install -g @sentropic/graphify; then
    warn "npm install failed. Check network/permissions and re-run."
    exit 1
  fi
else
  log "graphify CLI already on PATH — skipping install."
fi

# --- 2. Generate the graph --------------------------------------------------
# Scope values changed across Graphify versions ('committed' worked historically;
# 0.17.x documents auto/tracked/all, where 'auto' = committed + memory files).
# Try the known-good invocation first, then fall back per version.
log "Detecting project (graphify detect)..."
if graphify detect . --scope committed 2>/dev/null; then
  log "Detected with --scope committed."
elif graphify detect . --scope auto 2>/dev/null; then
  log "Detected with --scope auto ('committed' not accepted by this Graphify version)."
elif ! graphify detect --help >/dev/null 2>&1; then
  warn "This Graphify version has no 'detect' subcommand — skipping (update handles detection)."
else
  warn "graphify detect failed. If this project is not a git repository,"
  warn "initialize git first (git init && git add -A && git commit) — the"
  warn "git-based scopes read the git index. Then re-run this script."
  exit 1
fi

log "Generating graph (graphify update . --no-description --no-label)..."
if ! graphify update . --no-description --no-label; then
  warn "graphify update failed. Inspect the CLI output above, then re-run."
  warn "(If the flags were rejected, your Graphify version may want a different"
  warn "invocation — check 'graphify update --help'. A plain 'graphify update .'"
  warn "may trigger LLM description generation with API costs, so this script"
  warn "does not fall back to it automatically.)"
  exit 1
fi
log "Graph written to .graphify/ (graph.json + GRAPH_REPORT.md)."

# --- 3. Gitignore the raw output (idempotent) -------------------------------
if [ -e ".gitignore" ] && grep -qxF ".graphify/" .gitignore; then
  log ".gitignore already covers .graphify/."
else
  printf '.graphify/\n' >> .gitignore
  log "Added .graphify/ to .gitignore."
fi

# --- 4. Scaffold curated docs from templates (never overwrite) --------------
template_for() {
  local name="$1"
  if [ -f "$CENTRAL_DIR/docs/_templates/$name" ]; then
    echo "$CENTRAL_DIR/docs/_templates/$name"
  elif [ -f "$REPO_ROOT/docs/_templates/$name" ]; then
    echo "$REPO_ROOT/docs/_templates/$name"
  fi
}

mkdir -p docs
for doc in GRAPHIFY.md PROJECT_GRAPH.md; do
  if [ -f "docs/$doc" ]; then
    log "docs/$doc already exists — left untouched."
    continue
  fi
  src="$(template_for "$doc")"
  if [ -n "$src" ]; then
    cp "$src" "docs/$doc"
    log "Scaffolded docs/$doc from template."
  else
    warn "Template $doc not found in $CENTRAL_DIR/docs/_templates or the repo — skipped."
  fi
done

# --- 5. Wire the Graphify hooks (scripts + settings.json) -------------------
# Copies the two Graphify hook scripts into <project>/.claude/hooks/ and merges
# their entries into <project>/.claude/settings.json so the freshness reminder
# (SessionStart) and the graph-first nudge (PreToolUse Grep|Glob) run
# automatically. Repo copies win over the central dir so the scripts stay in
# lockstep with this setup script (the central dir can lag a feature behind).
hook_src() {
  local name="$1"
  if [ -f "$REPO_ROOT/hooks/$name" ]; then
    echo "$REPO_ROOT/hooks/$name"
  elif [ -f "$CENTRAL_DIR/hooks/$name" ]; then
    echo "$CENTRAL_DIR/hooks/$name"
  fi
}

HOOKS_DEST="$PROJECT_DIR/.claude/hooks"
mkdir -p "$HOOKS_DEST"
copied_stale=0
copied_scan=0
for hook in graphify-stale-reminder.sh graphify-scan-reminder.sh; do
  src="$(hook_src "$hook")"
  if [ -n "$src" ]; then
    cp "$src" "$HOOKS_DEST/$hook"
    chmod +x "$HOOKS_DEST/$hook"
    log "Installed hook .claude/hooks/$hook (executable, refreshed to current version)."
    case "$hook" in
      graphify-stale-reminder.sh) copied_stale=1 ;;
      graphify-scan-reminder.sh)  copied_scan=1 ;;
    esac
  else
    warn "Hook $hook not found in repo or central dir — skipped (won't be wired)."
  fi
done

if ! command -v python3 >/dev/null 2>&1; then
  warn "python3 not found — hook scripts were copied but settings.json was not"
  warn "wired automatically. Run scripts/wire-hooks.sh later (it needs python3)."
elif [ "$copied_stale" = "0" ] && [ "$copied_scan" = "0" ]; then
  warn "No Graphify hooks were available to wire."
else
  SETTINGS="$PROJECT_DIR/.claude/settings.json"
  TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
  # Additive, idempotent merge (matches wire-hooks.sh semantics): only append a
  # hook whose command string is not already present in its event. Backs up an
  # existing settings.json before writing. Never targets settings.local.json.
  WIRE_RESULT="$(python3 - "$SETTINGS" "$copied_stale" "$copied_scan" "$TIMESTAMP" <<'PYEOF'
import json, os, sys, shutil

target_path, want_stale, want_scan, ts = sys.argv[1], sys.argv[2] == "1", sys.argv[3] == "1", sys.argv[4]

template = {"hooks": {}}
if want_stale:
    template["hooks"]["SessionStart"] = [
        {"hooks": [{"type": "command",
                     "command": "bash ${CLAUDE_PROJECT_DIR}/.claude/hooks/graphify-stale-reminder.sh",
                     "timeout": 5, "statusMessage": "Graphify freshness check..."}]}
    ]
if want_scan:
    template["hooks"]["PreToolUse"] = [
        {"matcher": "Grep|Glob",
         "hooks": [{"type": "command",
                     "command": "bash ${CLAUDE_PROJECT_DIR}/.claude/hooks/graphify-scan-reminder.sh",
                     "timeout": 5, "statusMessage": "Graphify graph-first nudge..."}]}
    ]

if os.path.exists(target_path):
    with open(target_path) as f:
        try:
            settings = json.load(f)
        except json.JSONDecodeError as e:
            print(f"ERROR:target settings.json is not valid JSON: {e}")
            sys.exit(1)
    if not isinstance(settings, dict):
        print("ERROR:target settings.json is not a JSON object")
        sys.exit(1)
else:
    settings = {}

def commands_in(groups):
    found = set()
    for group in groups:
        for hook in group.get("hooks", []):
            if hook.get("command"):
                found.add(hook["command"])
    return found

hooks = settings.setdefault("hooks", {})
added = []
for event, template_groups in template["hooks"].items():
    existing_groups = hooks.setdefault(event, [])
    existing_cmds = commands_in(existing_groups)
    for group in template_groups:
        new_hooks = [h for h in group.get("hooks", []) if h.get("command") not in existing_cmds]
        if not new_hooks:
            continue
        new_group = {k: v for k, v in group.items() if k != "hooks"}
        new_group["hooks"] = new_hooks
        existing_groups.append(new_group)
        added.extend(h.get("command", "?") for h in new_hooks)

if not added:
    print("NOCHANGE")
    sys.exit(0)

if os.path.exists(target_path):
    shutil.copy(target_path, f"{target_path}.bak-{ts}")
    print(f"BACKUP:{target_path}.bak-{ts}")
os.makedirs(os.path.dirname(target_path), exist_ok=True)
with open(target_path, "w") as f:
    json.dump(settings, f, indent=2)
    f.write("\n")
for cmd in added:
    print(f"ADD:{cmd}")
PYEOF
)" || { warn "hook wiring skipped: ${WIRE_RESULT#ERROR:}"; WIRE_RESULT="SKIP"; }

  if [ "$WIRE_RESULT" = "NOCHANGE" ]; then
    log "Graphify hooks already wired in .claude/settings.json — no changes."
  elif [ "$WIRE_RESULT" != "SKIP" ]; then
    echo "$WIRE_RESULT" | while IFS= read -r line; do
      case "$line" in
        BACKUP:*) log "backup: ${line#BACKUP:}" ;;
        ADD:*)    log "wired:  ${line#ADD:}" ;;
      esac
    done
  fi
fi

log "Done. Curate docs/PROJECT_GRAPH.md with god nodes/communities worth versioning."
log "Graphify hooks are wired: stale-reminder keeps the graph fresh on SessionStart"
log "(SDD_GRAPHIFY_AUTO=0 disables auto-refresh), scan-reminder nudges graph-first"
log "on Grep/Glob (SDD_GRAPHIFY_NUDGE=0 opts out)."
exit 0
