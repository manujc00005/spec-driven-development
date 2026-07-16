<#
.SYNOPSIS
Wires the shipped SDD hooks into a project's .claude\settings.json by merging
the "hooks" key from settings.template.json (the PowerShell wiring).

.DESCRIPTION
Safety model (same spirit as install.ps1 / link-project.ps1):
  - Never touches settings.local.json.
  - Additive and idempotent: for each hook event, only template entries whose
    command string is not already present in that event are appended; existing
    entries are never removed, reordered or rewritten. Re-running is a no-op.
  - A timestamped backup (settings.json.bak-<ts>) is taken before any write.

.PARAMETER ProjectDir
Project to wire (default: current directory).

.PARAMETER Template
Settings template to merge (default: first of $CentralDir\settings.template.json,
<repo>\settings.template.json).

.PARAMETER CentralDir
Central SDD config directory (default: C:\ProgramData\ClaudeConfig).

.PARAMETER DryRun
Preview the merge without writing anything.
#>
[CmdletBinding()]
param(
  [string]$ProjectDir = (Get-Location).Path,
  [string]$Template = "",
  [string]$CentralDir = "C:\ProgramData\ClaudeConfig",
  [switch]$DryRun
)

$ErrorActionPreference = "Stop"
function Log($msg)  { Write-Host "[wire-hooks] $msg" }
function Warn($msg) { Write-Host "[warn]       $msg" }

$RepoRoot = Split-Path -Parent $PSScriptRoot

if (-not $Template) {
  if (Test-Path (Join-Path $CentralDir "settings.template.json")) {
    $Template = Join-Path $CentralDir "settings.template.json"
  } elseif (Test-Path (Join-Path $RepoRoot "settings.template.json")) {
    $Template = Join-Path $RepoRoot "settings.template.json"
  }
}
if (-not $Template -or -not (Test-Path $Template)) {
  Warn "settings.template.json not found (looked in $CentralDir and $RepoRoot)."
  Warn "Run install.ps1 first, or pass -Template <path>."
  exit 1
}

$Target = Join-Path $ProjectDir ".claude\settings.json"
if ($Target -like "*settings.local.json") { Warn "refusing to touch settings.local.json"; exit 1 }

$templateJson = Get-Content $Template -Raw | ConvertFrom-Json
$templateHooks = $templateJson.hooks
if (-not $templateHooks) { Warn "template has no 'hooks' key"; exit 1 }

if (Test-Path $Target) {
  try { $settings = Get-Content $Target -Raw | ConvertFrom-Json }
  catch { Warn "target settings.json is not valid JSON: $_"; exit 1 }
} else {
  $settings = [pscustomobject]@{}
}

if (-not ($settings.PSObject.Properties.Name -contains "hooks")) {
  $settings | Add-Member -NotePropertyName hooks -NotePropertyValue ([pscustomobject]@{})
}

$added = @()
foreach ($eventProp in $templateHooks.PSObject.Properties) {
  $eventName = $eventProp.Name
  if (-not ($settings.hooks.PSObject.Properties.Name -contains $eventName)) {
    $settings.hooks | Add-Member -NotePropertyName $eventName -NotePropertyValue @()
  }
  $existingCmds = @()
  foreach ($group in $settings.hooks.$eventName) {
    foreach ($hook in $group.hooks) { if ($hook.command) { $existingCmds += $hook.command } }
  }
  foreach ($group in $eventProp.Value) {
    $newHooks = @($group.hooks | Where-Object { $existingCmds -notcontains $_.command })
    if ($newHooks.Count -eq 0) {
      foreach ($hook in $group.hooks) { Log "keep: $($hook.command) (already wired)" }
      continue
    }
    $newGroup = [pscustomobject]@{}
    foreach ($p in $group.PSObject.Properties) {
      if ($p.Name -ne "hooks") { $newGroup | Add-Member -NotePropertyName $p.Name -NotePropertyValue $p.Value }
    }
    $newGroup | Add-Member -NotePropertyName hooks -NotePropertyValue $newHooks
    $settings.hooks.$eventName = @($settings.hooks.$eventName) + @($newGroup)
    foreach ($hook in $newHooks) { $added += $hook.command; Log "add:  $($hook.command)" }
  }
}

if ($added.Count -eq 0) {
  Log "already wired - $Target contains every hook from $(Split-Path -Leaf $Template). No changes."
  exit 0
}

if ($DryRun) {
  Log "[dry-run] would write $Target (backup first if it exists)"
  exit 0
}

$claudeDir = Split-Path -Parent $Target
if (-not (Test-Path $claudeDir)) { New-Item -ItemType Directory -Path $claudeDir | Out-Null }
if (Test-Path $Target) {
  $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
  Copy-Item $Target "$Target.bak-$stamp"
  Log "backup: $Target.bak-$stamp"
}
$settings | ConvertTo-Json -Depth 16 | Set-Content -Path $Target -Encoding UTF8
Log "wired hooks into $Target"
