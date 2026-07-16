# setup-graphify.ps1 — Adopts Graphify in an SDD project (Windows counterpart
# of setup-graphify.sh): installs the external @sentropic/graphify CLI (with
# confirmation), generates the dependency graph under .graphify/, gitignores
# the raw output, scaffolds the curated docs from templates, and wires the
# Graphify hooks (freshness reminder + graph-first nudge) into the project's
# .claude/settings.json so the whole loop runs with no manual steps.
#
# Safety model (same spirit as wire-hooks.ps1):
#   - Idempotent: re-running refreshes the graph and the copied hook scripts but
#     never duplicates .gitignore entries, overwrites curated docs, or
#     double-wires a hook already present in settings.json.
#   - Degrades gracefully: missing npm is a message, not a failure (exit 0).
#   - Never touches settings.local.json; backs settings.json up before writing.
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

# --- 5. Wire the Graphify hooks (scripts + settings.json) -------------------
# Copies the two Graphify hook scripts into <project>/.claude/hooks/ and merges
# their entries into <project>/.claude/settings.json so the freshness reminder
# (SessionStart) and the graph-first nudge (PreToolUse Grep|Glob) run
# automatically. Repo copies win over the central dir so the scripts stay in
# lockstep with this setup script (the central dir can lag a feature behind).
function Get-HookSource($name) {
    $repo = Join-Path $RepoRoot "hooks/$name"
    $central = Join-Path $CentralDir "hooks/$name"
    if (Test-Path $repo) { return $repo }
    if (Test-Path $central) { return $central }
    return $null
}

$HooksDest = Join-Path $ProjectDir ".claude/hooks"
New-Item -ItemType Directory -Path $HooksDest -Force | Out-Null
$copiedHooks = @()
foreach ($hook in @("graphify-stale-reminder.ps1", "graphify-scan-reminder.ps1")) {
    $src = Get-HookSource $hook
    if ($src) {
        Copy-Item $src (Join-Path $HooksDest $hook) -Force
        Log "Installed hook .claude/hooks/$hook (refreshed to current version)."
        $copiedHooks += $hook
    } else {
        Warn "Hook $hook not found in repo or central dir - skipped (won't be wired)."
    }
}

if ($copiedHooks.Count -eq 0) {
    Warn "No Graphify hooks were available to wire."
} else {
    $settingsPath = Join-Path $ProjectDir ".claude/settings.json"

    # Additive, idempotent merge (matches wire-hooks.ps1 semantics): only append
    # a hook whose command string is not already present in its event. Backs up
    # an existing settings.json before writing. Never targets settings.local.json.
    $template = @{ hooks = @{} }
    if ($copiedHooks -contains "graphify-stale-reminder.ps1") {
        $template.hooks["SessionStart"] = @(@{ hooks = @(@{
            type = "command"
            command = 'powershell -NoProfile -File ${CLAUDE_PROJECT_DIR}/.claude/hooks/graphify-stale-reminder.ps1'
            timeout = 5
            statusMessage = "Graphify freshness check..."
        }) })
    }
    if ($copiedHooks -contains "graphify-scan-reminder.ps1") {
        $template.hooks["PreToolUse"] = @(@{
            matcher = "Grep|Glob"
            hooks = @(@{
                type = "command"
                command = 'powershell -NoProfile -File ${CLAUDE_PROJECT_DIR}/.claude/hooks/graphify-scan-reminder.ps1'
                timeout = 5
                statusMessage = "Graphify graph-first nudge..."
            })
        })
    }

    if (Test-Path $settingsPath) {
        try {
            $settings = Get-Content $settingsPath -Raw | ConvertFrom-Json
        } catch {
            Warn "hook wiring skipped: target settings.json is not valid JSON."
            $settings = $null
        }
    } else {
        $settings = [PSCustomObject]@{}
    }

    if ($null -ne $settings) {
        if (-not $settings.PSObject.Properties["hooks"]) {
            $settings | Add-Member -MemberType NoteProperty -Name hooks -Value ([PSCustomObject]@{})
        }
        $added = @()
        foreach ($event in $template.hooks.Keys) {
            $existingGroups = @()
            if ($settings.hooks.PSObject.Properties[$event]) {
                $existingGroups = @($settings.hooks.$event)
            }
            $existingCmds = @()
            foreach ($g in $existingGroups) {
                foreach ($h in @($g.hooks)) { if ($h.command) { $existingCmds += $h.command } }
            }
            $newGroups = @()
            foreach ($group in $template.hooks[$event]) {
                $newHooks = @($group.hooks | Where-Object { $existingCmds -notcontains $_.command })
                if ($newHooks.Count -eq 0) { continue }
                $ng = @{}
                foreach ($k in $group.Keys) { if ($k -ne "hooks") { $ng[$k] = $group[$k] } }
                $ng["hooks"] = $newHooks
                $newGroups += [PSCustomObject]$ng
                foreach ($h in $newHooks) { $added += $h.command }
            }
            if ($newGroups.Count -gt 0) {
                $merged = @($existingGroups + $newGroups)
                if ($settings.hooks.PSObject.Properties[$event]) {
                    $settings.hooks.$event = $merged
                } else {
                    $settings.hooks | Add-Member -MemberType NoteProperty -Name $event -Value $merged
                }
            }
        }

        if ($added.Count -eq 0) {
            Log "Graphify hooks already wired in .claude/settings.json - no changes."
        } else {
            if (Test-Path $settingsPath) {
                $ts = Get-Date -Format "yyyyMMdd-HHmmss"
                Copy-Item $settingsPath "$settingsPath.bak-$ts"
                Log "backup: $settingsPath.bak-$ts"
            }
            $settings | ConvertTo-Json -Depth 20 | Set-Content -Path $settingsPath -Encoding UTF8
            foreach ($cmd in $added) { Log "wired:  $cmd" }
        }
    }
}

Log "Done. Curate docs/PROJECT_GRAPH.md with god nodes/communities worth versioning."
Log "Graphify hooks are wired: stale-reminder keeps the graph fresh on SessionStart"
Log "(SDD_GRAPHIFY_AUTO=0 disables auto-refresh), scan-reminder nudges graph-first"
Log "on Grep/Glob (SDD_GRAPHIFY_NUDGE=0 opts out)."
exit 0
