# graphify-stale-reminder.ps1 — Reminder hook (never blocks).
# Checks if GRAPH_REPORT.md is absent or stale relative to source files.
# Exit 0 always — this is a reminder, not a guard.

$GraphReport = "GRAPH_REPORT.md"

# If no graph report exists, remind but don't block
if (-not (Test-Path $GraphReport)) {
    Write-Output '{"systemMessage":"[Graphify] GRAPH_REPORT.md not found. Consider running Graphify for architecture discovery and impact analysis before planning."}'
    exit 0
}

# Check staleness: compare graph mtime vs newest source file
$graphTime = (Get-Item $GraphReport).LastWriteTime
$staleDays = 7

# Find newest source file (Java/TS/config) — limit scan depth for performance
$newestSource = Get-ChildItem -Path "." -Recurse -Include "*.java","*.ts","*.tsx","*.kt","pom.xml","build.gradle","package.json" -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -notmatch '(node_modules|target|build|\.git)' } |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1

if ($newestSource -and ($newestSource.LastWriteTime - $graphTime).Days -gt $staleDays) {
    $age = ($newestSource.LastWriteTime - $graphTime).Days
    Write-Output "{`"systemMessage`":`"[Graphify] GRAPH_REPORT.md is $age days older than the newest source file. Consider re-running Graphify before relying on it for impact analysis.`"}"
}

exit 0
