<#
.SYNOPSIS
  Thin convenience wrapper that installs BOTH adapters in order (Windows / PowerShell twin of
  install-all.sh):
    1) Claude Code adapter  ->  .\install.ps1
    2) Codex adapter        ->  .\adapters\codex\install-codex.ps1

.DESCRIPTION
  It does NOT modify or reimplement either installer — it only calls them. Each installer stays the
  single source of truth for its own behavior, flags, and safety guarantees. Both are idempotent, so
  re-running this wrapper is safe.

  The two adapters install to DIFFERENT locations and never overlap:
    Claude -> central config dir (+ optional ~\.claude linking)
    Codex  -> AGENTS.md in the target project root + prompts under ~\.codex\prompts

  Codex is prompt-based and UNVERIFIED against a live Codex CLI — see adapters\codex\PARITY.md.

.PARAMETER Profile
  Claude profile(s), forwarded to install.ps1.
.PARAMETER LinkUserClaude
  Forwarded to install.ps1 (opt-in ~\.claude linking + agent copy).
.PARAMETER CodexTarget
  Project root that receives Codex AGENTS.md (forwarded as -Target). Default: current directory.
.PARAMETER CodexHome
  Codex home; prompts land in <CodexHome>\prompts. Forwarded as -CodexHome.
.PARAMETER SkipClaude
  Do not run the Claude installer.
.PARAMETER SkipCodex
  Do not run the Codex installer.
.PARAMETER DryRun
  Forwarded to BOTH installers (preview only; writes nothing).
.PARAMETER Force
  Forwarded to BOTH installers (overwrite differing files after a timestamped backup).
#>

param(
  [string]$Profile,
  [switch]$LinkUserClaude,
  [string]$CodexTarget,
  [string]$CodexHome,
  [switch]$SkipClaude,
  [switch]$SkipCodex,
  [switch]$DryRun,
  [switch]$Force
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$claudeInstaller = Join-Path $RepoRoot "install.ps1"
$codexInstaller = Join-Path $RepoRoot "adapters\codex\install-codex.ps1"

# ---------------------------------------------------------------------------
# 1) Claude Code adapter
# ---------------------------------------------------------------------------
if ($SkipClaude) {
  Write-Host "== [1/2] Claude Code adapter - SKIPPED (-SkipClaude) =="
} else {
  Write-Host "== [1/2] Claude Code adapter -> install.ps1 =="
  if (-not (Test-Path -LiteralPath $claudeInstaller)) {
    Write-Host "[ERROR] not found: $claudeInstaller"; exit 1
  }
  $claudeArgs = @{}
  if ($Profile) { $claudeArgs["Profile"] = $Profile }
  if ($LinkUserClaude) { $claudeArgs["LinkUserClaude"] = $true }
  if ($DryRun) { $claudeArgs["DryRun"] = $true }
  if ($Force) { $claudeArgs["Force"] = $true }
  & $claudeInstaller @claudeArgs
  if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Claude installer exited $LASTEXITCODE - skipping Codex."
    exit $LASTEXITCODE
  }
}

Write-Host ""

# ---------------------------------------------------------------------------
# 2) Codex adapter
# ---------------------------------------------------------------------------
if ($SkipCodex) {
  Write-Host "== [2/2] Codex adapter - SKIPPED (-SkipCodex) =="
} else {
  Write-Host "== [2/2] Codex adapter -> adapters\codex\install-codex.ps1 =="
  if (-not (Test-Path -LiteralPath $codexInstaller)) {
    Write-Host "[ERROR] not found: $codexInstaller"; exit 1
  }
  if ($CodexTarget) {
    Write-Host "   Codex AGENTS.md -> $CodexTarget"
  } else {
    Write-Host "   Codex AGENTS.md: SKIPPED (no -CodexTarget given - AGENTS.md is per-project)."
    Write-Host "                    prompts still install to ~\.codex\prompts."
    Write-Host "                    pass -CodexTarget <your-project> to install AGENTS.md too."
  }
  $codexArgs = @{}
  if ($CodexTarget) { $codexArgs["Target"] = $CodexTarget }
  if ($CodexHome) { $codexArgs["CodexHome"] = $CodexHome }
  if ($DryRun) { $codexArgs["DryRun"] = $true }
  if ($Force) { $codexArgs["Force"] = $true }
  & $codexInstaller @codexArgs
}

Write-Host ""
if ($DryRun) {
  Write-Host "Dry-run complete for all selected adapters. Nothing was written."
} else {
  Write-Host "All selected adapters processed. Reminder: the Codex adapter's guardrails are conventions,"
  Write-Host "not enforced hooks, and it is unverified against a live Codex CLI - see adapters\codex\PARITY.md."
}
