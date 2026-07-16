#!/usr/bin/env bash
# graphify-scan-reminder.sh — PreToolUse nudge on Grep/Glob (never blocks).
# When a Graphify report exists (.graphify/GRAPH_REPORT.md, legacy fallback:
# root GRAPH_REPORT.md), reminds the session to prefer graph-first context over
# broad scans. Throttled to one nudge per 30 minutes via the mtime of
# .graphify/.scan-nudge. Set SDD_GRAPHIFY_NUDGE=0 to disable.
# Exit 0 always — reinforcement, not enforcement.

set -euo pipefail

# Consume the tool-call JSON from stdin; content not needed (the settings
# matcher already restricts this hook to Grep|Glob).
cat >/dev/null 2>&1 || true

NUDGE_TTL_SECONDS=1800

[ "${SDD_GRAPHIFY_NUDGE:-1}" != "0" ] || exit 0

# Canonical path first, legacy root fallback — same order as graphify-stale-reminder.
if [ ! -f ".graphify/GRAPH_REPORT.md" ] && [ ! -f "GRAPH_REPORT.md" ]; then
  exit 0
fi

# Portable mtime (GNU stat -c / BSD stat -f)
mtime() { stat -c %Y "$1" 2>/dev/null || stat -f %m "$1" 2>/dev/null; }

MARKER=".graphify/.scan-nudge"
if [ -f "$MARKER" ]; then
  # An unreadable marker (deleted mid-check) is treated as absent.
  marker_mtime=$(mtime "$MARKER" || true)
  if [ -n "$marker_mtime" ]; then
    age=$(( $(date +%s) - marker_mtime ))
    if [ "$age" -le "$NUDGE_TTL_SECONDS" ]; then
      exit 0 # nudged recently — stay quiet
    fi
  fi
fi

mkdir -p .graphify
touch "$MARKER"
echo '{"systemMessage":"[Graphify] A dependency graph is available (.graphify/GRAPH_REPORT.md). Prefer graph-first context — /graphify-context, graphify review-context <file>, graphify affected-flows <file> — over broad Grep/Glob scans to save tokens."}'
exit 0
