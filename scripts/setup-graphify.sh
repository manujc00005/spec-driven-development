#!/usr/bin/env bash
#
# Adopts Graphify in an SDD project: installs the external @sentropic/graphify
# CLI (with confirmation), generates the dependency graph under .graphify/,
# gitignores the raw output, and scaffolds the curated docs from templates.
#
# Safety model (same spirit as wire-hooks.sh):
#   - Idempotent: re-running refreshes the graph but never duplicates
#     .gitignore entries or overwrites existing docs.
#   - Degrades gracefully: missing npm is a message, not a failure (exit 0).
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

log "Done. Curate docs/PROJECT_GRAPH.md with god nodes/communities worth versioning."
log "The graphify-stale-reminder hook keeps the graph fresh (SDD_GRAPHIFY_AUTO=0 disables)."
exit 0
