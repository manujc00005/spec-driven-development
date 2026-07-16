# graphify-stale-reminder.ps1 — Reminder + background auto-refresh hook (never blocks).
# Resolves the Graphify report at .graphify/GRAPH_REPORT.md (canonical) with a
# legacy fallback to GRAPH_REPORT.md at project root. If the graph is missing or
# stale (>7 days older than the newest source file) and the graphify CLI is on
# PATH, it refreshes the graph in a detached background run guarded by a lock
# (.graphify/.update.lock, ignored after 10 minutes so a crashed run self-heals).
# Set SDD_GRAPHIFY_AUTO=0 to disable auto-refresh (reminder-only behavior).
# Exit 0 always — this is a reminder, not a guard.

$staleDays = 7
$lockMaxAgeSeconds = 600
$auto = if ($env:SDD_GRAPHIFY_AUTO) { $env:SDD_GRAPHIFY_AUTO } else { "1" }

# Canonical path first, legacy root fallback
$GraphReport = $null
if (Test-Path ".graphify/GRAPH_REPORT.md") {
    $GraphReport = ".graphify/GRAPH_REPORT.md"
} elseif (Test-Path "GRAPH_REPORT.md") {
    $GraphReport = "GRAPH_REPORT.md"
}

# Spawns a detached `graphify update` when auto-refresh is allowed: CLI on PATH,
# SDD_GRAPHIFY_AUTO != 0, and no lock younger than $lockMaxAgeSeconds.
# Returns $true if a refresh was started.
function Try-AutoRefresh {
    if ($auto -eq "0") { return $false }
    if (-not (Get-Command graphify -ErrorAction SilentlyContinue)) { return $false }
    $lock = ".graphify/.update.lock"
    # The background wrapper may delete the lock between Test-Path and Get-Item;
    # an unreadable lock is treated as absent.
    $lockItem = Get-Item $lock -ErrorAction SilentlyContinue
    if ($lockItem) {
        $age = ((Get-Date) - $lockItem.LastWriteTime).TotalSeconds
        if ($age -le $lockMaxAgeSeconds) { return $false } # a refresh is already running
    }
    New-Item -ItemType Directory -Path ".graphify" -Force | Out-Null
    New-Item -ItemType File -Path $lock -Force | Out-Null
    Start-Process -WindowStyle Hidden -FilePath "powershell" -ArgumentList @(
        "-NoProfile", "-Command",
        "graphify update . --no-description --no-label *> `$null; Remove-Item -Force '.graphify/.update.lock' -ErrorAction SilentlyContinue"
    ) | Out-Null
    return $true
}

# If no graph report exists, refresh in background (when possible) or remind
if (-not $GraphReport) {
    if (Try-AutoRefresh) {
        Write-Output '{"systemMessage":"[Graphify] Graph report not found - refreshing in background (graphify update). It will be available at .graphify/GRAPH_REPORT.md shortly."}'
    } else {
        Write-Output '{"systemMessage":"[Graphify] GRAPH_REPORT.md not found. Consider running Graphify for architecture discovery and impact analysis before planning."}'
    }
    exit 0
}

# Check staleness: compare graph mtime vs newest source file
$graphTime = (Get-Item $GraphReport).LastWriteTime

# Find newest source file (Java/TS/config) — limit scan depth for performance
$newestSource = Get-ChildItem -Path "." -Recurse -Include "*.java","*.ts","*.tsx","*.kt","pom.xml","build.gradle","package.json" -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -notmatch '(node_modules|target|build|\.git)' } |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1

if ($newestSource -and ($newestSource.LastWriteTime - $graphTime).Days -gt $staleDays) {
    $age = ($newestSource.LastWriteTime - $graphTime).Days
    if (Try-AutoRefresh) {
        Write-Output "{`"systemMessage`":`"[Graphify] Graph report is $age days older than the newest source file - refreshing in background (graphify update).`"}"
    } else {
        Write-Output "{`"systemMessage`":`"[Graphify] GRAPH_REPORT.md is $age days older than the newest source file. Consider re-running Graphify before relying on it for impact analysis.`"}"
    }
}

exit 0
