#!/usr/bin/env bash
# graphify-stale-reminder.sh — Reminder hook (never blocks).
# Checks if GRAPH_REPORT.md is absent or stale relative to source files.
# Exit 0 always — this is a reminder, not a guard.

set -euo pipefail

GRAPH_REPORT="GRAPH_REPORT.md"
STALE_DAYS=7

# If no graph report exists, remind but don't block
if [ ! -f "$GRAPH_REPORT" ]; then
  echo '{"systemMessage":"[Graphify] GRAPH_REPORT.md not found. Consider running Graphify for architecture discovery and impact analysis before planning."}'
  exit 0
fi

# Check staleness: compare graph mtime vs newest source file
GRAPH_MTIME=$(stat -c %Y "$GRAPH_REPORT" 2>/dev/null || stat -f %m "$GRAPH_REPORT" 2>/dev/null)

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
    echo "{\"systemMessage\":\"[Graphify] GRAPH_REPORT.md is ${DIFF_DAYS} days older than the newest source file. Consider re-running Graphify before relying on it for impact analysis.\"}"
  fi
fi

exit 0
