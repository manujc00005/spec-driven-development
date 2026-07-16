# setup-graphify.ps1 — Adopts Graphify in an SDD project (Windows counterpart
# of setup-graphify.sh): installs the external @sentropic/graphify CLI (with
# confirmation), generates the dependency graph under .graphify/, gitignores
# the raw output, and scaffolds the curated docs from templates.
#
# Safety model (same spirit as wire-hooks.ps1):
#   - Idempotent: re-running refreshes the graph but never duplicates
#     .gitignore entries or overwrites existing docs.
#   - Degrades gracefully: missing npm is a message, not a failure (exit 0).
#   - Installs software only after explicit confirmation (or -Yes).
#
# Usage: ./setup-graphify.ps1 [-ProjectDir <path>] [-CentralDir <path>] [-Yes]

param(
    [string]$ProjectDir = (Get-Location).Path,
    [string]$CentralDir = $(if ($env:CENTRAL_DIR) { $env:CENTRAL_DIR } else { Join-Path $HOME ".claude-config" }),
    [switch]$Yes
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ScriptDir

function Log($msg)  { Write-Output "[setup-graphify] $msg" }
function Warn($msg) { Write-Output "[warn]           $msg" }

if (-not (Test-Path $ProjectDir -PathType Container)) {
    Warn "Project directory not found: $ProjectDir"
    exit 1
}
Set-Location $ProjectDir

# --- 1. Ensure the graphify CLI is available -------------------------------
if (-not (Get-Command graphify -ErrorAction SilentlyContinue)) {
    if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
        Warn "npm is not installed, and Graphify is an npm package (@sentropic/graphify)."
        Warn "Install Node.js/npm first (https://nodejs.org), then re-run this script."
        Warn "SDD works fine without Graphify - this only skips the accelerator."
        exit 0
    }
    if (-not $Yes) {
        $answer = Read-Host "[setup-graphify] Install @sentropic/graphify globally via npm? [y/N]"
        if ($answer -notmatch '^(y|yes)$') {
            Log "Skipped install. Re-run with -Yes to install non-interactively."
            exit 0
        }
    }
    Log "Installing @sentropic/graphify globally..."
    npm install -g @sentropic/graphify
    if ($LASTEXITCODE -ne 0) {
        Warn "npm install failed. Check network/permissions and re-run."
        exit 1
    }
} else {
    Log "graphify CLI already on PATH - skipping install."
}

# --- 2. Generate the graph --------------------------------------------------
# Scope values changed across Graphify versions ('committed' worked historically;
# 0.17.x documents auto/tracked/all, where 'auto' = committed + memory files).
# Try the known-good invocation first, then fall back per version.
Log "Detecting project (graphify detect)..."
graphify detect . --scope committed 2>$null
if ($LASTEXITCODE -eq 0) {
    Log "Detected with --scope committed."
} else {
    graphify detect . --scope auto 2>$null
    if ($LASTEXITCODE -eq 0) {
        Log "Detected with --scope auto ('committed' not accepted by this Graphify version)."
    } else {
        graphify detect --help *> $null
        if ($LASTEXITCODE -ne 0) {
            Warn "This Graphify version has no 'detect' subcommand - skipping (update handles detection)."
        } else {
            Warn "graphify detect failed. If this project is not a git repository,"
            Warn "initialize git first (git init; git add -A; git commit) - the"
            Warn "git-based scopes read the git index. Then re-run this script."
            exit 1
        }
    }
}

Log "Generating graph (graphify update . --no-description --no-label)..."
graphify update . --no-description --no-label
if ($LASTEXITCODE -ne 0) {
    Warn "graphify update failed. Inspect the CLI output above, then re-run."
    Warn "(If the flags were rejected, your Graphify version may want a different"
    Warn "invocation - check 'graphify update --help'. A plain 'graphify update .'"
    Warn "may trigger LLM description generation with API costs, so this script"
    Warn "does not fall back to it automatically.)"
    exit 1
}
Log "Graph written to .graphify/ (graph.json + GRAPH_REPORT.md)."

# --- 3. Gitignore the raw output (idempotent) -------------------------------
$gitignoreCovers = (Test-Path ".gitignore") -and
    ((Get-Content ".gitignore") -contains ".graphify/")
if ($gitignoreCovers) {
    Log ".gitignore already covers .graphify/."
} else {
    Add-Content -Path ".gitignore" -Value ".graphify/"
    Log "Added .graphify/ to .gitignore."
}

# --- 4. Scaffold curated docs from templates (never overwrite) --------------
function Get-TemplatePath($name) {
    $central = Join-Path $CentralDir "docs/_templates/$name"
    $repo = Join-Path $RepoRoot "docs/_templates/$name"
    if (Test-Path $central) { return $central }
    if (Test-Path $repo) { return $repo }
    return $null
}

New-Item -ItemType Directory -Path "docs" -Force | Out-Null
foreach ($doc in @("GRAPHIFY.md", "PROJECT_GRAPH.md")) {
    if (Test-Path "docs/$doc") {
        Log "docs/$doc already exists - left untouched."
        continue
    }
    $src = Get-TemplatePath $doc
    if ($src) {
        Copy-Item $src "docs/$doc"
        Log "Scaffolded docs/$doc from template."
    } else {
        Warn "Template $doc not found in $CentralDir/docs/_templates or the repo - skipped."
    }
}

Log "Done. Curate docs/PROJECT_GRAPH.md with god nodes/communities worth versioning."
Log "The graphify-stale-reminder hook keeps the graph fresh (SDD_GRAPHIFY_AUTO=0 disables)."
exit 0
