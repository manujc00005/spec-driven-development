<#
.SYNOPSIS
Incremental update for an existing SDD install (spec 015): brings the clone
and the central config directory up to date in one command, without ever
touching adopter-owned files. PowerShell parity of scripts/update.sh.

.DESCRIPTION
Sequence: pre-flight (dirty-tree refusal) -> git pull --ff-only -> re-install
with the profiles recorded in <central-dir>/.sdd-install.json -> agents
refresh -> "What's new" report (version delta, CHANGELOG excerpt,
added/updated/skipped counts, CLAUDE.md heading drift).

Safety model (inherited from install.ps1): never deletes, never stashes or
resets the clone, differing files are skipped without -Force (with -Force they
are backed up first), full -DryRun support. A dirty clone or a
non-fast-forward pull is a hard error - resolving divergence is the adopter's
decision, never this script's.

.PARAMETER CentralDir
Central SDD config directory (default: C:\ProgramData\ClaudeConfig).

.PARAMETER ClaudeHome
Per-user Claude Code config directory (default: $env:USERPROFILE\.claude).

.PARAMETER ProjectDir
Linked project to refresh agents in (repeatable: -ProjectDir a,b).

.PARAMETER ClaudeMd
CLAUDE.md file to check for heading drift (repeatable, report-only).

.PARAMETER Force
Passed through to install.ps1 (overwrite differing files, backup first).

.PARAMETER DryRun
Preview all actions without writing anything.

.NOTES
Exit codes: 0 = updated or already current, 1 = pre-flight/pull/install error.
#>

param(
    [string]$CentralDir = "C:\ProgramData\ClaudeConfig",
    [string]$ClaudeHome = "$env:USERPROFILE\.claude",
    [string[]]$ProjectDir = @(),
    [string[]]$ClaudeMd = @(),
    [switch]$Force,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)

function Write-Action([string]$msg) { Write-Host "[update]  $msg" }
function Write-Skip([string]$msg)   { Write-Host "[skip]    $msg" -ForegroundColor DarkYellow }
function Write-Warn2([string]$msg)  { Write-Host "[warn]    $msg" -ForegroundColor Yellow }

if ($DryRun) { Write-Action "DRY RUN MODE  - no files will be written, moved, or linked" }

# ---------------------------------------------------------------------------
# Pre-flight: the clone must be a git repo with a clean working tree (FR-003).
# A dirty tree is refused outright: any automatic stash/reset could destroy
# adopter work. Nothing has been modified when this exits.
# ---------------------------------------------------------------------------
& git -C $RepoRoot rev-parse --git-dir *>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR]   $RepoRoot is not a git repository. Incremental update needs the git clone this framework was installed from (a tarball/zip download cannot be updated this way  - clone the repo instead)." -ForegroundColor Red
    exit 1
}

$dirty = (& git -C $RepoRoot status --porcelain | Out-String).Trim()
if ($dirty) {
    Write-Host "[ERROR]   The clone at $RepoRoot has uncommitted changes  - refusing to pull over them:" -ForegroundColor Red
    $dirty -split "`n" | ForEach-Object { Write-Host "[ERROR]     $_" -ForegroundColor Red }
    Write-Host "[ERROR]   Commit, stash, or discard these changes yourself, then re-run. This script never stashes or resets for you." -ForegroundColor Red
    exit 1
}

$oldHead = (& git -C $RepoRoot rev-parse HEAD | Out-String).Trim()

# ---------------------------------------------------------------------------
# Pull, fast-forward only. A non-ff result means divergence: the adopter's
# call. Offline/credential failures surface git's own message untouched.
# ---------------------------------------------------------------------------
if ($DryRun) {
    Write-Action "[dry-run] would run: git -C $RepoRoot pull --ff-only"
} else {
    & git -C $RepoRoot pull --ff-only
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR]   git pull --ff-only failed (see git's message above)." -ForegroundColor Red
        Write-Host "[ERROR]   If the clone has diverged from upstream (local commits or a fork), merge or rebase it yourself, then re-run. If this is a network/credential issue, fix connectivity and re-run. Nothing was modified." -ForegroundColor Red
        exit 1
    }
}

$newHead = (& git -C $RepoRoot rev-parse HEAD | Out-String).Trim()

if ($oldHead -eq $newHead) {
    $desc = (& git -C $RepoRoot describe --tags --always 2>$null | Out-String).Trim()
    if (-not $desc) { $desc = $newHead }
    Write-Action "Clone already up to date at $desc."
} else {
    $count = (& git -C $RepoRoot rev-list --count "$oldHead..$newHead" | Out-String).Trim()
    Write-Action "Pulled $count commit(s): $($oldHead.Substring(0,9)) -> $($newHead.Substring(0,9))"
}

# ---------------------------------------------------------------------------
# Read the install manifest (FR-004). Absent or corrupt -> unknown-version
# mode; the invoked installer rewrites it at the end of its successful run.
# ---------------------------------------------------------------------------
$manifest = Join-Path $CentralDir ".sdd-install.json"
$oldVersion = ""
$oldCommit = ""
$manifestProfiles = @()
$manifestLink = $false
if (Test-Path $manifest) {
    try {
        $m = Get-Content $manifest -Raw | ConvertFrom-Json
        $oldVersion = "$($m.installedVersion)"
        $oldCommit = "$($m.installedCommit)"
        if ($m.profiles) { $manifestProfiles = @($m.profiles | Where-Object { $_ -is [string] }) }
        if ($m.linkUserClaude -eq $true) { $manifestLink = $true }
        $profLabel = if ($manifestProfiles.Count) { $manifestProfiles -join ',' } else { 'none' }
        $verLabel = if ($oldVersion) { $oldVersion } else { 'unknown' }
        Write-Action "Recorded install: version $verLabel, profiles: $profLabel"
    } catch {
        Write-Warn2 "manifest $manifest exists but is unreadable  - continuing in unknown-version mode (it will be rewritten by this run)"
    }
} else {
    Write-Action "No install manifest at $manifest  - first recorded update (unknown-version mode). This run will write one for next time."
}

# Link mode mirrors the recorded install (FR-007). Use hashtable splatting so
# arguments bind by NAME: array splatting (@("-CentralDir", ...)) is positional
# in PowerShell and would feed the central-dir path into -Profile.
$installArgs = @{ CentralDir = $CentralDir; ClaudeHome = $ClaudeHome }
if ($manifestLink) {
    $installArgs['LinkUserClaude'] = $true
    Write-Action "Recorded install linked ~/.claude  - refreshing its agent copies and links too."
} else {
    $installArgs['SkipLink'] = $true
}
$recordedProfiles = @($manifestProfiles | Where-Object { $_ -ne "core" })
if ($recordedProfiles.Count -gt 0) {
    $installArgs['Profile'] = $recordedProfiles
    Write-Action "Re-installing with recorded profiles: $($manifestProfiles -join ',')"
} else {
    Write-Action "Re-installing with the installer's default profile (no recorded profiles)."
}
if ($DryRun) { $installArgs['DryRun'] = $true }
if ($Force)  { $installArgs['Force'] = $true }

$installLog = (New-TemporaryFile).FullName
try {
    & (Join-Path $RepoRoot "install.ps1") @installArgs 2>&1 | Tee-Object -FilePath $installLog
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR]   install.ps1 failed (see its output above)  - the clone was pulled but the central dir may be partially refreshed. Re-run after fixing the reported problem." -ForegroundColor Red
        exit 1
    }

    # Count parsing rides on the installer's stable line prefixes (see D002).
    $logLines = Get-Content $installLog
    $countNew        = @($logLines | Where-Object { $_ -match ' \(new\)$' }).Count
    $countOverwritten= @($logLines | Where-Object { $_ -match '\(overwritten' }).Count
    $localEditLines  = @($logLines | Where-Object { $_ -match 'differs from the central copy' })
    $countLocalEdits = $localEditLines.Count

    # -----------------------------------------------------------------------
    # "What's new" report (FR-005). From = manifest commit (what the central
    # dir installed) or the clone's pre-pull HEAD in unknown-version mode.
    # -----------------------------------------------------------------------
    $fromRef = if ($oldCommit) { $oldCommit } else { $oldHead }
    & git -C $RepoRoot cat-file -e $fromRef 2>$null
    if ($LASTEXITCODE -ne 0) { $fromRef = $oldHead }
    $fromDesc = (& git -C $RepoRoot describe --tags --always $fromRef 2>$null | Out-String).Trim()
    if (-not $fromDesc) { $fromDesc = $fromRef.Substring(0, [Math]::Min(9, $fromRef.Length)) }
    $toDesc = (& git -C $RepoRoot describe --tags --always $newHead 2>$null | Out-String).Trim()
    if (-not $toDesc) { $toDesc = $newHead.Substring(0, [Math]::Min(9, $newHead.Length)) }

    Write-Host ""
    Write-Action "===== What's new ====="
    if ($fromRef -eq $newHead) {
        Write-Action "Already up to date at $toDesc  - nothing to install."
    } else {
        Write-Action "Updated: $fromDesc -> $toDesc"
        $changelogNew = & git -C $RepoRoot diff "$fromRef..$newHead" -- CHANGELOG.md 2>$null |
            Where-Object { $_ -match '^\+## ' } | ForEach-Object { "  " + $_.Substring(1) }
        if ($changelogNew) {
            Write-Action "Releases in this update (from CHANGELOG.md):"
            $changelogNew | ForEach-Object { Write-Host $_ }
        } else {
            Write-Action "Commits in this update:"
            & git -C $RepoRoot log --oneline "$fromRef..$newHead" 2>$null |
                Select-Object -First 20 | ForEach-Object { Write-Host "  $_" }
        }
    }

    Write-Action "Central dir refreshed: $countNew new file(s), $countOverwritten overwritten, $countLocalEdits skipped with local edits."
    if ($countLocalEdits -gt 0) {
        Write-Warn2 "Local edits detected in $countLocalEdits central-dir file(s) - left untouched. Re-run with -Force to overwrite them (a timestamped backup is taken first):"
        $localEditLines | ForEach-Object {
            $line = $_ -replace '^\[skip\]\s+', '  ' -replace '\s+- rerun.*$', ''
            Write-Host $line
        }
    }
} finally {
    Remove-Item $installLog -ErrorAction SilentlyContinue
}

# ---------------------------------------------------------------------------
# Per-project refresh (FR-007): reuse link-project.ps1, never reimplement copy.
# ---------------------------------------------------------------------------
# Hashtable splat (bind by name); array splat would be positional (see above).
$linkArgs = @{ CentralDir = $CentralDir }
if ($DryRun) { $linkArgs['DryRun'] = $true }
if ($Force)  { $linkArgs['Force'] = $true }
foreach ($proj in $ProjectDir) {
    if (-not (Test-Path $proj)) {
        Write-Warn2 "project dir $proj does not exist  - skipping its agent refresh"
        continue
    }
    Write-Action "Refreshing linked project: $proj"
    & (Join-Path $RepoRoot "link-project.ps1") -ProjectDir $proj @linkArgs
    if ($LASTEXITCODE -ne 0) {
        Write-Warn2 "link-project.ps1 failed for $proj  - refresh it manually with: .\link-project.ps1 -ProjectDir $proj"
    }
}

# ---------------------------------------------------------------------------
# Pending manual steps (FR-007): reminders only, never actions (see D004).
# ---------------------------------------------------------------------------
if ($fromRef -ne $newHead) {
    $newHooks = & git -C $RepoRoot diff --name-only --diff-filter=A "$fromRef..$newHead" -- 'hooks/*.sh' 2>$null
    if ($newHooks) {
        $names = ($newHooks | ForEach-Object { ($_ -replace 'hooks/', '') -replace '\.sh$', '' }) -join ' '
        Write-Warn2 "This update ships new hook script(s): $names"
        Write-Warn2 "  Wire them into each project that should enforce them: .\scripts\wire-hooks.ps1 -ProjectDir <project>"
    }
    $exampleChanged = & git -C $RepoRoot diff --name-only "$fromRef..$newHead" -- CLAUDE.md.example 2>$null
    if ($exampleChanged -and $ClaudeMd.Count -eq 0) {
        Write-Warn2 "CLAUDE.md.example changed in this update. Pass -ClaudeMd <your-project-CLAUDE.md> to see which sections are new to merge."
    }
}

if ($manifestLink -and $ProjectDir.Count -eq 0) {
    Write-Action "Note: agent copies in any linked projects are not refreshed by this run  - pass -ProjectDir <path> for each, or re-run .\link-project.ps1 there."
}

# ---------------------------------------------------------------------------
# CLAUDE.md drift check (FR-006). Heading-level, CRLF-safe, report-only:
# the target is never written (see D004). Mirrors update.sh exactly.
# ---------------------------------------------------------------------------
$exampleMd = Join-Path $RepoRoot "CLAUDE.md.example"
foreach ($target in $ClaudeMd) {
    if (-not (Test-Path $exampleMd)) {
        Write-Warn2 "CLAUDE.md drift check skipped  - $exampleMd not found"
        break
    }
    if (-not (Test-Path $target)) {
        Write-Warn2 "CLAUDE.md drift check: target $target not found  - skipping (advisory only)"
        continue
    }
    $haveHeadings = @(Get-Content $target | ForEach-Object { $_.TrimEnd("`r", "`n") } |
        Where-Object { $_.StartsWith("## ") } | ForEach-Object { $_.Substring(3).Trim() })
    $have = @{}
    foreach ($h in $haveHeadings) { $have[$h] = $true }
    $missing = @()
    Get-Content $exampleMd | ForEach-Object { $_.TrimEnd("`r", "`n") } |
        Where-Object { $_.StartsWith("## ") } | ForEach-Object {
            $h = $_.Substring(3).Trim()
            if (-not $have.ContainsKey($h)) { $missing += $h; $have[$h] = $true }
        }
    if ($missing.Count -gt 0) {
        Write-Warn2 "CLAUDE.md drift  - $target is missing these sections from CLAUDE.md.example (pending manual merge):"
        $missing | ForEach-Object { Write-Host "  ## $_" }
    } else {
        Write-Action "CLAUDE.md drift  - $target has every section from CLAUDE.md.example (no merge pending)."
    }
}

Write-Action "Done."
