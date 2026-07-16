#!/usr/bin/env bash
# graphify-stale-reminder.sh — Reminder + background auto-refresh hook (never blocks).
# Resolves the Graphify report at .graphify/GRAPH_REPORT.md (canonical) with a
# legacy fallback to GRAPH_REPORT.md at project root. If the graph is missing or
# stale (>7 days older than the newest source file) and the graphify CLI is on
# PATH, it refreshes the graph in a detached background run guarded by a lock
# (.graphify/.update.lock, ignored after 10 minutes so a crashed run self-heals).
# Set SDD_GRAPHIFY_AUTO=0 to disable auto-refresh (reminder-only behavior).
# Exit 0 always — this is a reminder, not a guard.

set -euo pipefail

STALE_DAYS=7
LOCK_MAX_AGE_SECONDS=600
AUTO="${SDD_GRAPHIFY_AUTO:-1}"
NOW=$(date +%s)

# Portable mtime (GNU stat -c / BSD stat -f)
mtime() { stat -c %Y "$1" 2>/dev/null || stat -f %m "$1" 2>/dev/null; }

# Canonical path first, legacy root fallback
GRAPH_REPORT=""
if [ -f ".graphify/GRAPH_REPORT.md" ]; then
  GRAPH_REPORT=".graphify/GRAPH_REPORT.md"
elif [ -f "GRAPH_REPORT.md" ]; then
  GRAPH_REPORT="GRAPH_REPORT.md"
fi

# Spawns a detached `graphify update` when auto-refresh is allowed: CLI on PATH,
# SDD_GRAPHIFY_AUTO != 0, and no lock younger than LOCK_MAX_AGE_SECONDS.
# Returns 0 if a refresh was started.
try_auto_refresh() {
  [ "$AUTO" != "0" ] || return 1
  command -v graphify >/dev/null 2>&1 || return 1
  local lock=".graphify/.update.lock" lock_mtime age
  if [ -f "$lock" ]; then
    # The background wrapper may delete the lock between the -f check and the
    # stat; an unreadable lock is treated as absent.
    lock_mtime=$(mtime "$lock" || true)
    if [ -n "$lock_mtime" ]; then
      age=$((NOW - lock_mtime))
      if [ "$age" -le "$LOCK_MAX_AGE_SECONDS" ]; then
        return 1 # a refresh is already running
      fi
    fi
  fi
  mkdir -p .graphify
  touch "$lock"
  nohup bash -c 'graphify update . --no-description --no-label >/dev/null 2>&1; rm -f .graphify/.update.lock' >/dev/null 2>&1 &
  disown 2>/dev/null || true
  return 0
}

# If no graph report exists, refresh in background (when possible) or remind
if [ -z "$GRAPH_REPORT" ]; then
  if try_auto_refresh; then
    echo '{"systemMessage":"[Graphify] Graph report not found - refreshing in background (graphify update). It will be available at .graphify/GRAPH_REPORT.md shortly."}'
  else
    echo '{"systemMessage":"[Graphify] GRAPH_REPORT.md not found. Consider running Graphify for architecture discovery and impact analysis before planning."}'
  fi
  exit 0
fi

# Check staleness: compare graph mtime vs newest source file
GRAPH_MTIME=$(mtime "$GRAPH_REPORT")

# Find newest source file (limit depth for performance)
NEWEST_SOURCE_MTIME=$(find . -maxdepth 5 \
  \( -name "*.java" -o -name "*.ts" -o -name "*.tsx" -o -name "*.kt" -o -name "pom.xml" -o -name "build.gradle" -o -name "package.json" \) \
  -not -path "*/node_modules/*" \
  -not -path "*/target/*" \
  -not -path "*/build/*" \
  -not -path "*/.git/*" \
  -exec stat -c %Y {} \; 2>/dev/null | sort -rn | head -1)

# Fallback for macOS stat
if [ -z "$NEWEST_SOURCE_MTIME" ]; then
  NEWEST_SOURCE_MTIME=$(find . -maxdepth 5 \
    \( -name "*.java" -o -name "*.ts" -o -name "*.tsx" -o -name "*.kt" -o -name "pom.xml" -o -name "build.gradle" -o -name "package.json" \) \
    -not -path "*/node_modules/*" \
    -not -path "*/target/*" \
    -not -path "*/build/*" \
    -not -path "*/.git/*" \
    -exec stat -f %m {} \; 2>/dev/null | sort -rn | head -1)
fi

if [ -n "$NEWEST_SOURCE_MTIME" ] && [ -n "$GRAPH_MTIME" ]; then
  DIFF_SECONDS=$((NEWEST_SOURCE_MTIME - GRAPH_MTIME))
  DIFF_DAYS=$((DIFF_SECONDS / 86400))
  if [ "$DIFF_DAYS" -gt "$STALE_DAYS" ]; then
    if try_auto_refresh; then
      echo "{\"systemMessage\":\"[Graphify] Graph report is ${DIFF_DAYS} days older than the newest source file - refreshing in background (graphify update).\"}"
    else
      echo "{\"systemMessage\":\"[Graphify] GRAPH_REPORT.md is ${DIFF_DAYS} days older than the newest source file. Consider re-running Graphify before relying on it for impact analysis.\"}"
    fi
  fi
fi

exit 0
