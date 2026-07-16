# graphify-scan-reminder.ps1 — PreToolUse nudge on Grep/Glob (never blocks).
# When a Graphify report exists (.graphify/GRAPH_REPORT.md, legacy fallback:
# root GRAPH_REPORT.md), reminds the session to prefer graph-first context over
# broad scans. Throttled to one nudge per 30 minutes via the mtime of
# .graphify/.scan-nudge. Set SDD_GRAPHIFY_NUDGE=0 to disable.
# Exit 0 always — reinforcement, not enforcement.

# Consume the tool-call JSON from stdin; content not needed (the settings
# matcher already restricts this hook to Grep|Glob).
$null = [Console]::In.ReadToEnd()

$nudgeTtlSeconds = 1800

if ($env:SDD_GRAPHIFY_NUDGE -eq "0") { exit 0 }

# Canonical path first, legacy root fallback - same order as graphify-stale-reminder.
if (-not (Test-Path ".graphify/GRAPH_REPORT.md") -and -not (Test-Path "GRAPH_REPORT.md")) {
    exit 0
}

$marker = ".graphify/.scan-nudge"
# An unreadable marker (deleted mid-check) is treated as absent.
$markerItem = Get-Item $marker -ErrorAction SilentlyContinue
if ($markerItem) {
    $age = ((Get-Date) - $markerItem.LastWriteTime).TotalSeconds
    if ($age -le $nudgeTtlSeconds) {
        exit 0 # nudged recently - stay quiet
    }
}

New-Item -ItemType Directory -Path ".graphify" -Force | Out-Null
New-Item -ItemType File -Path $marker -Force | Out-Null
Write-Output '{"systemMessage":"[Graphify] A dependency graph is available (.graphify/GRAPH_REPORT.md). Prefer graph-first context - /graphify-context, graphify review-context <file>, graphify affected-flows <file> - over broad Grep/Glob scans to save tokens."}'
exit 0
