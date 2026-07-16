<#
.SYNOPSIS
  Links a specific project's .claude\skills and .claude\hooks to the central
  SDD configuration directory via Windows Junctions, and copies the shipped
  agent files into .claude\agents (per-file, additive - never a junction,
  because that directory commonly contains project-authored agents).

.DESCRIPTION
  Use this when a project needs skills/hooks visible locally under its own
  .claude\ folder instead of (or in addition to) relying on the per-user
  ~/.claude linking done by install.ps1 -LinkUserClaude.

  Same safety model as install.ps1:
    - Never touches .claude\settings.local.json.
    - An existing correct link is a no-op.
    - An existing link pointing elsewhere is left alone unless -Force.
    - An existing real directory is backed up to <path>.bak-<timestamp> before
      being replaced, and only with -Force.

.PARAMETER ProjectDir
  The project to link into. Defaults to the current directory.

.PARAMETER CentralDir
  The central SDD configuration directory. Defaults to
  C:\ProgramData\ClaudeConfig.

.PARAMETER Force
  Overwrite an existing link pointing elsewhere, or back up and replace a real
  directory.

.PARAMETER DryRun
  Preview actions without writing, moving, or linking anything.

.EXAMPLE
  .\link-project.ps1 -ProjectDir C:\code\my-app
#>
param(
    [string]$ProjectDir = (Get-Location).Path,
    [string]$CentralDir = "C:\ProgramData\ClaudeConfig",
    [switch]$Force,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"

function Write-Action([string]$msg) { Write-Host "[link-project] $msg" }
function Write-Skip([string]$msg)   { Write-Host "[skip]         $msg" -ForegroundColor DarkYellow }
function Write-Warn2([string]$msg)  { Write-Host "[warn]         $msg" -ForegroundColor Yellow }

if (-not (Test-Path $CentralDir)) {
    Write-Warn2 "Central directory $CentralDir does not exist. Run install.ps1 first."
    exit 1
}

$claudeDir = Join-Path $ProjectDir ".claude"
if (-not (Test-Path $claudeDir)) {
    if ($DryRun) { Write-Action "[dry-run] would create $claudeDir" }
    else { New-Item -ItemType Directory -Path $claudeDir -Force | Out-Null }
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
    if (-not (Test-Path $target)) {
        Write-Skip "$Name skipped  - $target does not exist in the central directory"
        return
    }
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
        $backupPath = "$LinkPath.bak-$Timestamp"
        Write-Warn2 "$Name exists as a real directory (not a link)  - this looks like existing project-local content"
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

Write-Action "Project:      $ProjectDir"
Write-Action "Central dir:  $CentralDir"
if ($DryRun) { Write-Action "DRY RUN MODE  - no files will be written, moved, or linked" }
Write-Host ""

function Copy-AgentFileSafely([string]$SrcFile, [string]$DestPath, [string]$Label) {
    # Agents are COPIED per-file, never junctioned: .claude\agents commonly
    # contains project-authored agents that a directory link would hide.
    # Additive only  - a same-name file that differs is skipped without -Force;
    # with -Force it is backed up next to itself first.
    $destDir = Split-Path $DestPath -Parent
    if (-not (Test-Path $destDir)) {
        if ($DryRun) { Write-Action "[dry-run] would create directory $destDir" }
        else { New-Item -ItemType Directory -Path $destDir -Force | Out-Null }
    }
    if (-not (Test-Path $DestPath)) {
        if ($DryRun) { Write-Action "[dry-run] would create $DestPath" }
        else { Copy-Item $SrcFile -Destination $DestPath -Force }
        Write-Action "$Label  (new)"
        return
    }
    $srcHash = (Get-FileHash $SrcFile -Algorithm SHA256).Hash
    $dstHash = (Get-FileHash $DestPath -Algorithm SHA256).Hash
    if ($srcHash -eq $dstHash) { Write-Action "$Label already up to date (no-op)"; return }
    if (-not $Force) {
        Write-Skip "$Label differs from the central copy  - looks like a project customization; rerun with -Force to overwrite (a backup is taken first)"
        return
    }
    $backupPath = "$DestPath.bak-$Timestamp"
    if ($DryRun) {
        Write-Action "[dry-run] would back up $DestPath to $backupPath, then overwrite it with the central version"
    } else {
        Copy-Item $DestPath -Destination $backupPath -Force
        Copy-Item $SrcFile -Destination $DestPath -Force
        Write-Action "$Label  (overwritten  - previous version backed up to $backupPath)"
    }
}

Set-DirLink (Join-Path $claudeDir "skills") "skills" "skills"
Set-DirLink (Join-Path $claudeDir "hooks") "hooks" "hooks"

# --- Agents: per-file copy from <central>\agents into <project>\.claude\agents ---
$centralAgents = Join-Path $CentralDir "agents"
if (Test-Path $centralAgents) {
    $agentFiles = Get-ChildItem -Path $centralAgents -File -Filter "*.md" | Where-Object { $_.Name -ne "README.md" }
    foreach ($af in $agentFiles) {
        Copy-AgentFileSafely $af.FullName (Join-Path (Join-Path $claudeDir "agents") $af.Name) ".claude/agents/$($af.Name)"
    }
} else {
    Write-Skip "agents skipped  - $centralAgents does not exist in the central directory (re-run install.ps1 to install agents)"
}

Write-Host ""
Write-Action "settings.local.json is never touched by this script  - hooks do not run until wired into"
Write-Action ".claude\settings.json. Run scripts\wire-hooks.ps1 -ProjectDir $ProjectDir to merge the shipped"
Write-Action "wiring (explicit, additive, backup first), or wire paths yourself from settings.template.json."
Write-Host ""
Write-Action "Done."
