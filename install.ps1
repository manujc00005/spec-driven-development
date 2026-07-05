<#
.SYNOPSIS
  Installs this SDD workflow (skills, hooks, templates) into a central Claude Code
  configuration directory on Windows, and optionally links your per-user Claude
  Code home (~/.claude) to it.

.DESCRIPTION
  This script is safe to run from any clone location and safe to re-run:

    - It never deletes anything. It only creates missing files/directories, or
      (with -Force) overwrites a file that differs from the source AFTER taking
      a timestamped backup under <CentralDir>\_install-backups\<timestamp>\.
    - It never touches .claude/settings.local.json, under any path, ever.
    - It never writes CLAUDE.md or settings.json directly  - only
      CLAUDE.md.example and settings.template.json, so an existing real
      CLAUDE.md/settings.json at the central directory is never silently
      replaced.
    - Linking ~/.claude/skills, ~/.claude/hooks, and ~/.claude/CLAUDE.md to the
      central directory is OPT-IN via -LinkUserClaude, because it touches your
      personal Claude Code configuration, not just this repo's target.
    - If ~/.claude/skills or ~/.claude/hooks already exist as a Junction or
      SymbolicLink pointing at the right place, the script reports "already
      linked" and does nothing (idempotent).
    - If they exist as real directories with real data, the script refuses to
      touch them unless -Force is given, and even then backs them up first to
      <path>.bak-<timestamp>.

.PARAMETER CentralDir
  Where to install the shared SDD configuration. Defaults to
  C:\ProgramData\ClaudeConfig  - the intended central install location on
  Windows for this workflow.

.PARAMETER Force
  Allow overwriting files/links that already exist and differ. A backup is
  always taken first. Without -Force, differing files are reported and
  skipped  - nothing is overwritten silently.

.PARAMETER DryRun
  Preview every action without writing, moving, or linking anything.

.PARAMETER SkipLink
  Skip the entire ~/.claude linking step (install content into CentralDir
  only).

.PARAMETER LinkUserClaude
  Opt-in: also link $ClaudeHome\skills, \hooks, and \CLAUDE.md to CentralDir.
  Off by default because it touches your personal Claude Code configuration.

.PARAMETER ClaudeHome
  Your per-user Claude Code configuration directory. Defaults to
  $env:USERPROFILE\.claude (the conventional per-user Claude Code config
  location  - confirm this matches your installed Claude Code version).

.EXAMPLE
  .\install.ps1 -DryRun
  Preview what would happen with the defaults  - nothing is written.

.EXAMPLE
  .\install.ps1
  Install skills/hooks/templates into C:\ProgramData\ClaudeConfig. Does not
  touch ~/.claude.

.EXAMPLE
  .\install.ps1 -LinkUserClaude
  Also link ~/.claude/skills, hooks, and CLAUDE.md to the central directory
  (only creates links where none exist yet, or where an existing link already
  points to the right place; anything else requires -Force).
#>
param(
    [string]$CentralDir = "C:\ProgramData\ClaudeConfig",
    [switch]$Force,
    [switch]$DryRun,
    [switch]$SkipLink,
    [switch]$LinkUserClaude,
    [string]$ClaudeHome = "$env:USERPROFILE\.claude"
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"

function Write-Action([string]$msg) { Write-Host "[install] $msg" }
function Write-Skip([string]$msg)   { Write-Host "[skip]    $msg" -ForegroundColor DarkYellow }
function Write-Warn2([string]$msg)  { Write-Host "[warn]    $msg" -ForegroundColor Yellow }

# Belt-and-suspenders: never touch these, even if a future source tree somehow contains them.
$ExcludePatterns = @('settings.local.json')

function Test-Excluded([string]$relativePath) {
    foreach ($p in $ExcludePatterns) {
        if ($relativePath -like "*$p*") { return $true }
    }
    return $false
}

function Copy-TreeSafely([string]$SourceDir, [string]$TargetDir, [string]$Label, [string]$BackupRoot) {
    if (-not (Test-Path $SourceDir)) {
        Write-Warn2 "$Label`: source $SourceDir not found, skipping"
        return
    }
    $sourceFiles = Get-ChildItem -Path $SourceDir -Recurse -File -Force
    foreach ($f in $sourceFiles) {
        $rel = $f.FullName.Substring($SourceDir.Length).TrimStart('\')
        if (Test-Excluded $rel) { Write-Skip "$Label/$rel (excluded pattern)"; continue }

        $destPath = Join-Path $TargetDir $rel
        $destDir = Split-Path $destPath -Parent

        if (-not (Test-Path $destDir)) {
            if ($DryRun) { Write-Action "[dry-run] would create directory $destDir" }
            else { New-Item -ItemType Directory -Path $destDir -Force | Out-Null }
        }

        if (-not (Test-Path $destPath)) {
            if ($DryRun) { Write-Action "[dry-run] would create $destPath" }
            else { Copy-Item $f.FullName -Destination $destPath -Force }
            Write-Action "$Label/$rel  (new)"
            continue
        }

        $srcHash = (Get-FileHash $f.FullName -Algorithm SHA256).Hash
        $dstHash = (Get-FileHash $destPath -Algorithm SHA256).Hash
        if ($srcHash -eq $dstHash) { continue }

        if (-not $Force) {
            Write-Skip "$Label/$rel differs from the central copy  - rerun with -Force to overwrite (a backup is taken first)"
            continue
        }

        $backupPath = Join-Path $BackupRoot "_install-backups\$Timestamp\$Label\$rel"
        if ($DryRun) {
            Write-Action "[dry-run] would back up $destPath to $backupPath, then overwrite it with the repo version"
        } else {
            New-Item -ItemType Directory -Path (Split-Path $backupPath -Parent) -Force | Out-Null
            Copy-Item $destPath -Destination $backupPath -Force
            Copy-Item $f.FullName -Destination $destPath -Force
            Write-Action "$Label/$rel  (overwritten  - previous version backed up to $backupPath)"
        }
    }
}

function Remove-DirLinkSafely([string]$Path) {
    # Remove-Item on a Junction/SymbolicLink can prompt to recurse into the
    # *target* directory's content in some PowerShell versions, and fails
    # outright in non-interactive sessions (confirmation unavailable). Using
    # .Delete() on the reparse-point item removes only the link itself, never
    # the content behind it.
    (Get-Item $Path -Force).Delete()
}

function Set-DirLink([string]$LinkPath, [string]$TargetPath, [string]$Name) {
    $target = Join-Path $CentralDir $TargetPath
    if (Test-Path $LinkPath) {
        $item = Get-Item $LinkPath -Force
        if ($item.LinkType -eq "Junction" -or $item.LinkType -eq "SymbolicLink") {
            if ($item.Target -eq $target) {
                Write-Action "$Name already correctly linked -> $target (no-op)"
                return
            }
            Write-Skip "$Name is linked to a different target ($($item.Target))  - use -Force to relink to $target"
            if (-not $Force) { return }
            if ($DryRun) { Write-Action "[dry-run] would relink $Name to $target" }
            else {
                Remove-DirLinkSafely $LinkPath
                New-Item -ItemType Junction -Path $LinkPath -Target $target | Out-Null
                Write-Action "$Name relinked -> $target"
            }
            return
        }
        # Real directory with real data  - never touch without -Force, always back up first.
        $backupPath = "$LinkPath.bak-$Timestamp"
        Write-Warn2 "$Name exists as a real directory (not a link)  - this looks like existing local data"
        if (-not $Force) {
            Write-Skip "Not touching $LinkPath  - rerun with -Force to back it up to $backupPath and replace it with a link"
            return
        }
        if ($DryRun) {
            Write-Action "[dry-run] would back up $LinkPath to $backupPath and replace it with a junction to $target"
        } else {
            Move-Item $LinkPath $backupPath
            New-Item -ItemType Junction -Path $LinkPath -Target $target | Out-Null
            Write-Action "$Name backed up to $backupPath and linked -> $target"
        }
    } else {
        if ($DryRun) { Write-Action "[dry-run] would create junction $LinkPath -> $target" }
        else {
            New-Item -ItemType Junction -Path $LinkPath -Target $target | Out-Null
            Write-Action "$Name linked -> $target"
        }
    }
}

# ---------------------------------------------------------------------------

Write-Action "Repo root:            $RepoRoot"
Write-Action "Central config dir:   $CentralDir"
if ($DryRun) { Write-Action "DRY RUN MODE  - no files will be written, moved, or linked" }
Write-Host ""

if (-not (Test-Path $CentralDir)) {
    if ($DryRun) { Write-Action "[dry-run] would create $CentralDir" }
    else { New-Item -ItemType Directory -Path $CentralDir -Force | Out-Null; Write-Action "Created $CentralDir" }
}

Copy-TreeSafely (Join-Path $RepoRoot "skills") (Join-Path $CentralDir "skills") "skills" $CentralDir
Copy-TreeSafely (Join-Path $RepoRoot "hooks") (Join-Path $CentralDir "hooks") "hooks" $CentralDir
Copy-TreeSafely (Join-Path $RepoRoot "specs\_templates") (Join-Path $CentralDir "specs\_templates") "specs/_templates" $CentralDir

foreach ($rootFile in @("CLAUDE.md.example", "settings.template.json")) {
    $src = Join-Path $RepoRoot $rootFile
    $dst = Join-Path $CentralDir $rootFile
    if (-not (Test-Path $src)) { continue }

    if (-not (Test-Path $dst)) {
        if ($DryRun) { Write-Action "[dry-run] would create $dst" } else { Copy-Item $src -Destination $dst -Force }
        Write-Action "$rootFile (new)"
        continue
    }

    $srcHash = (Get-FileHash $src -Algorithm SHA256).Hash
    $dstHash = (Get-FileHash $dst -Algorithm SHA256).Hash
    if ($srcHash -eq $dstHash) { continue }

    if (-not $Force) {
        Write-Skip "$rootFile differs from the version already at $CentralDir  - rerun with -Force to overwrite (backup taken first)"
        continue
    }

    $backupPath = Join-Path $CentralDir "_install-backups\$Timestamp\$rootFile"
    if ($DryRun) {
        Write-Action "[dry-run] would back up and overwrite $rootFile"
    } else {
        New-Item -ItemType Directory -Path (Split-Path $backupPath -Parent) -Force | Out-Null
        Copy-Item $dst -Destination $backupPath -Force
        Copy-Item $src -Destination $dst -Force
        Write-Action "$rootFile (overwritten  - backup at $backupPath)"
    }
}

Write-Host ""
Write-Action "NOTE: CLAUDE.md.example is never installed as CLAUDE.md. If $CentralDir has no"
Write-Action "CLAUDE.md yet, copy CLAUDE.md.example to CLAUDE.md yourself and edit it there."
Write-Host ""

if ($SkipLink) {
    Write-Action "Skipping ~/.claude linking (-SkipLink)."
} elseif (-not $LinkUserClaude) {
    Write-Action "Skipping ~/.claude linking by default  - it touches your personal Claude Code config."
    Write-Action "Re-run with -LinkUserClaude to link $ClaudeHome\skills, \hooks, and \CLAUDE.md to $CentralDir."
} else {
    Write-Host ""
    Write-Action "Linking user Claude home ($ClaudeHome) to the central config..."
    if (-not (Test-Path $ClaudeHome)) {
        if ($DryRun) { Write-Action "[dry-run] would create $ClaudeHome" }
        else { New-Item -ItemType Directory -Path $ClaudeHome -Force | Out-Null }
    }

    Set-DirLink (Join-Path $ClaudeHome "skills") "skills" "skills"
    Set-DirLink (Join-Path $ClaudeHome "hooks") "hooks" "hooks"

    $claudeMdLink = Join-Path $ClaudeHome "CLAUDE.md"
    $claudeMdTarget = Join-Path $CentralDir "CLAUDE.md"
    if (-not (Test-Path $claudeMdTarget)) {
        Write-Skip "CLAUDE.md link skipped  - $claudeMdTarget does not exist yet (this repo only ships CLAUDE.md.example)"
    } elseif (Test-Path $claudeMdLink) {
        $item = Get-Item $claudeMdLink -Force
        if ($item.LinkType -eq "SymbolicLink" -and $item.Target -eq $claudeMdTarget) {
            Write-Action "CLAUDE.md already correctly linked -> $claudeMdTarget (no-op)"
        } else {
            Write-Skip "$claudeMdLink already exists and is not linked to $claudeMdTarget  - resolve manually; this script will not touch an existing real CLAUDE.md without you reviewing it first"
        }
    } else {
        if ($DryRun) {
            Write-Action "[dry-run] would create file symlink $claudeMdLink -> $claudeMdTarget (requires Administrator or Developer Mode)"
        } else {
            try {
                New-Item -ItemType SymbolicLink -Path $claudeMdLink -Target $claudeMdTarget -ErrorAction Stop | Out-Null
                Write-Action "CLAUDE.md linked -> $claudeMdTarget"
            } catch {
                Write-Warn2 "Could not create the CLAUDE.md symlink (needs Administrator or Developer Mode). Skipped. Error: $($_.Exception.Message)"
            }
        }
    }
}

Write-Host ""
Write-Action "Done."
