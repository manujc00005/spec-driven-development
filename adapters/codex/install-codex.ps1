<#
.SYNOPSIS
  Self-contained, copy-only installer for the SDD Codex adapter (Windows / PowerShell twin of
  install-codex.sh).

.DESCRIPTION
  Copies this adapter's operating guide (AGENTS.md) into a target project root, and the lifecycle
  prompts (prompts\*.md) into a Codex prompts directory. It does NOTHING else:
    - never runs the `codex` CLI (not required; not installed in the dev environment this adapter
      was authored in — the adapter is prompt-based and unverified against a live CLI);
    - never touches secrets, .env, or your existing ~/.codex/config.toml;
    - never deletes; overwrites a differing file only with -Force, after a timestamped backup;
    - operates only within this adapter (source) and the target you name (destination).

  See .\README.md and .\PARITY.md for status and limitations.

.PARAMETER Target
  Project root that receives AGENTS.md. Default: current directory.
.PARAMETER CodexHome
  Codex home; prompts land in <CodexHome>\prompts. Default: ~\.codex.
.PARAMETER PromptsOnly
  Copy only the prompts.
.PARAMETER AgentsOnly
  Copy only AGENTS.md.
.PARAMETER DryRun
  Preview only; writes nothing.
.PARAMETER Force
  Overwrite a differing file (after a timestamped .bak-<ts> backup).
#>

param(
  [string]$Target = (Get-Location).Path,
  [string]$CodexHome = (Join-Path $env:USERPROFILE ".codex"),
  [switch]$PromptsOnly,
  [switch]$AgentsOnly,
  [switch]$DryRun,
  [switch]$Force
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"

$doAgents = -not $PromptsOnly
$doPrompts = -not $AgentsOnly

$agentsSrc = Join-Path $ScriptDir "AGENTS.md"
$frameworkRoot = (Resolve-Path (Join-Path $ScriptDir "..\..")).Path
$targetExplicit = $PSBoundParameters.ContainsKey('Target')
$promptsSrcDir = Join-Path $ScriptDir "prompts"
$promptsDstDir = Join-Path $CodexHome "prompts"

function Copy-One {
  param([string]$Src, [string]$Dst)
  if (-not (Test-Path -LiteralPath $Src -PathType Leaf)) {
    Write-Host "[ERROR] source missing: $Src"; return $false
  }
  if (Test-Path -LiteralPath $Dst -PathType Leaf) {
    if ((Get-FileHash -LiteralPath $Src).Hash -eq (Get-FileHash -LiteralPath $Dst).Hash) {
      Write-Host "[skip]   $Dst (identical)"; return $true
    }
    if (-not $Force) {
      Write-Host "[skip]   $Dst (differs - re-run with -Force to overwrite; a backup is taken first)"
      return $true
    }
    if ($DryRun) {
      Write-Host "[dry-run] would back up $Dst -> $Dst.bak-$Timestamp and overwrite"; return $true
    }
    Copy-Item -LiteralPath $Dst -Destination "$Dst.bak-$Timestamp"
    Write-Host "[backup] $Dst -> $Dst.bak-$Timestamp"
    Copy-Item -LiteralPath $Src -Destination $Dst -Force
    Write-Host "[copy]   $Dst (overwritten)"; return $true
  }
  if ($DryRun) { Write-Host "[dry-run] would create $Dst"; return $true }
  $parent = Split-Path -Parent $Dst
  if (-not (Test-Path -LiteralPath $parent)) { New-Item -ItemType Directory -Path $parent -Force | Out-Null }
  Copy-Item -LiteralPath $Src -Destination $Dst
  Write-Host "[copy]   $Dst"; return $true
}

Write-Host "SDD Codex adapter installer (copy-only)"
Write-Host "  source : $ScriptDir"
if ($doAgents -and $targetExplicit) {
  Write-Host "  target : $Target   (AGENTS.md)"
} elseif ($doAgents) {
  Write-Host "  target : (none - AGENTS.md skipped; pass -Target <your-project>)"
}
if ($doPrompts) { Write-Host "  codex  : $promptsDstDir   (prompts)" }
if ($DryRun) { Write-Host "  mode   : DRY-RUN (no files will be written)" }
Write-Host ""

$ok = $true

if ($doAgents) {
  if (-not $targetExplicit) {
    Write-Host "[skip]   AGENTS.md - no -Target given. AGENTS.md is per-project and is never written to the"
    Write-Host "         current directory by default. Pass -Target <your-project> (e.g. -Target .) to install it."
  } elseif (-not (Test-Path -LiteralPath $Target -PathType Container)) {
    Write-Host "[ERROR] target directory does not exist: $Target"; exit 1
  } else {
    $targetAbs = (Resolve-Path -LiteralPath $Target).Path
    if ($targetAbs -eq $frameworkRoot) {
      Write-Host "[skip]   AGENTS.md - refusing to write into the SDD framework repo itself ($frameworkRoot)."
      Write-Host "         Pass -Target <your-project> to install AGENTS.md into a consumer project instead."
    } else {
      if (-not (Copy-One -Src $agentsSrc -Dst (Join-Path $targetAbs "AGENTS.md"))) { $ok = $false }
    }
  }
}

if ($doPrompts) {
  if (-not (Test-Path -LiteralPath $promptsSrcDir -PathType Container)) {
    Write-Host "[ERROR] prompts source missing: $promptsSrcDir"; exit 1
  }
  Get-ChildItem -LiteralPath $promptsSrcDir -Filter *.md | ForEach-Object {
    if (-not (Copy-One -Src $_.FullName -Dst (Join-Path $promptsDstDir $_.Name))) { $ok = $false }
  }
}

Write-Host ""
if ($DryRun) {
  Write-Host "Dry-run complete. Nothing was written."
} else {
  Write-Host "Done. Review .\PARITY.md - the Codex adapter's guardrails are conventions, not enforced hooks."
}
if ($ok) { exit 0 } else { exit 1 }
