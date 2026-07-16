<#
.SYNOPSIS
  Installs this SDD workflow (skills, hooks, templates, agents) into a central
  Claude Code configuration directory on Windows, and optionally links your
  per-user Claude Code home (~/.claude) to it.

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
    - profiles.json separates SHIPPED items (skills/hooks/templates - must
      exist on disk) from PLANNED items (plannedSkills/plannedHooks/
      plannedTemplates - roadmap-only, may not exist). An unknown -Profile
      name, an explicit request for a disabled profile, or a shipped item
      missing from disk are all hard errors (exit 1, before any files are
      touched for the first two; after a full dry-run-style report for the
      third). Planned items are reported as "[planned] ... not installed"
      and never cause an error. Nothing is ever silently skipped for a typo.

.PARAMETER CentralDir
  Where to install the shared SDD configuration. Defaults to
  C:\ProgramData\ClaudeConfig  - the intended central install location on
  Windows for this workflow.

.PARAMETER Profile
  One or more profile names from profiles.json to install (e.g., -Profile
  java-spring-backend). Core profile is always installed. If omitted, the
  default profile from profiles.json is used (java-spring-backend). Pass
  multiple profiles as a comma-separated list or repeat the flag:
    -Profile java-spring-backend,messaging-event-driven
  An unknown profile name or a disabled profile (e.g. blockchain-crypto)
  aborts immediately with a clear error  - it is never silently dropped.

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
  Opt-in: also link $ClaudeHome\skills, \hooks, and \CLAUDE.md to CentralDir,
  and COPY the shipped agent files into $ClaudeHome\agents (per-file, additive
  - never a junction, because that directory commonly contains user-authored
  agents). Off by default because it touches your personal Claude Code
  configuration.

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
  .\install.ps1 -Profile java-spring-backend,messaging-event-driven
  Install core + java-spring-backend + messaging-event-driven profiles into
  the central directory. Only skills/hooks/templates declared in those
  profiles are installed.

.EXAMPLE
  .\install.ps1 -LinkUserClaude
  Also link ~/.claude/skills, hooks, and CLAUDE.md to the central directory
  (only creates links where none exist yet, or where an existing link already
  points to the right place; anything else requires -Force).
#>
param(
    [string]$CentralDir = "C:\ProgramData\ClaudeConfig",
    [string[]]$Profile,
    [switch]$Force,
    [switch]$DryRun,
    [switch]$SkipLink,
    [switch]$LinkUserClaude,
    [string]$ClaudeHome = "$env:USERPROFILE\.claude"
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"

# ---------------------------------------------------------------------------
# Profile resolution
# ---------------------------------------------------------------------------
# Fails loudly (exit 1) on: an unknown profile name (typo protection), an
# explicit request for a disabled profile, or a shipped item declared in
# profiles.json that does not actually exist on disk (manifest/repo drift).
# None of these are silent skips. Only *planned* items are skipped silently
# (by design — they are declared for roadmap visibility, not installation).
$ProfilesFile = Join-Path $RepoRoot "profiles.json"
$ActiveSkills = @()
$ActiveHooks = @()
$ActiveTemplates = @()
$ActiveAgents = @()
$PlannedSkills = @()
$PlannedHooks = @()
$PlannedTemplates = @()
$PlannedAgents = @()
$MissingShipped = @()
$ProfileFiltering = $false

if (-not (Test-Path $ProfilesFile)) {
    Write-Host "[ERROR]   profiles.json not found at $ProfilesFile. This repo requires it for profile-aware installation  - refusing to fall back to installing everything unfiltered." -ForegroundColor Red
    exit 1
}

if (Test-Path $ProfilesFile) {
    try {
        $profilesData = Get-Content $ProfilesFile -Raw | ConvertFrom-Json -ErrorAction Stop
    } catch {
        Write-Host "[ERROR]   profiles.json exists but is not valid JSON: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }

    # Determine which profiles were requested (comma-separated values inside
    # a single -Profile argument are also honored, matching install.sh).
    $requestedProfiles = @()
    if ($Profile.Count -gt 0) {
        foreach ($p in $Profile) { $requestedProfiles += ($p -split ',') | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne '' } }
    } elseif ($profilesData.defaults.profile) {
        $requestedProfiles = @($profilesData.defaults.profile)
    }

    # --- Hard validation: unknown profile name or explicit disabled request ---
    $validProfileNames = @($profilesData.profiles.PSObject.Properties.Name)
    $fatalErrors = @()
    foreach ($pName in $requestedProfiles) {
        if ($validProfileNames -notcontains $pName) {
            $fatalErrors += "Unknown profile '$pName'. Valid profiles: $($validProfileNames -join ', ')"
            continue
        }
        $pDef = $profilesData.profiles.$pName
        if ($pDef.disabled -eq $true) {
            $fatalErrors += "Profile '$pName' is disabled by design (see profiles.json) and cannot be installed via -Profile. This is intentional, not a bug."
        }
    }
    if ($fatalErrors.Count -gt 0) {
        Write-Host ""
        foreach ($e in $fatalErrors) { Write-Host "[ERROR]   $e" -ForegroundColor Red }
        Write-Host "[ERROR]   Aborting before any files are touched. Fix the -Profile argument and re-run." -ForegroundColor Red
        exit 1
    }

    # Core is always installed
    $activeProfileNames = @("core") + $requestedProfiles | Select-Object -Unique

    # --- Collect shipped + planned skills/hooks/templates from active profiles ---
    foreach ($pName in $activeProfileNames) {
        $pDef = $profilesData.profiles.$pName
        if (-not $pDef) { continue }
        if ($pDef.skills) { $ActiveSkills += @($pDef.skills) }
        if ($pDef.plannedSkills) { $PlannedSkills += @($pDef.plannedSkills) }
        if ($pDef.hooks) { $ActiveHooks += @($pDef.hooks) }
        if ($pDef.plannedHooks) { $PlannedHooks += @($pDef.plannedHooks) }
        if ($pDef.templates) { $ActiveTemplates += @($pDef.templates) }
        if ($pDef.plannedTemplates) { $PlannedTemplates += @($pDef.plannedTemplates) }
        # 'agents'/'plannedAgents' are optional (added in profiles.json 0.4.0) — a
        # profile without them simply ships no agents (backward compatible).
        if ($pDef.agents) { $ActiveAgents += @($pDef.agents) }
        if ($pDef.plannedAgents) { $PlannedAgents += @($pDef.plannedAgents) }
    }
    $ActiveSkills = $ActiveSkills | Select-Object -Unique
    $ActiveHooks = $ActiveHooks | Select-Object -Unique
    $ActiveTemplates = $ActiveTemplates | Select-Object -Unique
    $ActiveAgents = $ActiveAgents | Select-Object -Unique
    $PlannedSkills = $PlannedSkills | Select-Object -Unique
    $PlannedHooks = $PlannedHooks | Select-Object -Unique
    $PlannedTemplates = $PlannedTemplates | Select-Object -Unique
    $PlannedAgents = $PlannedAgents | Select-Object -Unique
    $ProfileFiltering = $true

    # --- Integrity check: every SHIPPED item must exist on disk. A missing
    #     shipped item means profiles.json has drifted from the repo (e.g. a
    #     typo'd skill name, or a file that was deleted but not un-declared).
    #     This is reported as a hard error, never a silent skip. ---
    $MissingShipped = @()
    foreach ($s in $ActiveSkills) {
        if (-not (Test-Path (Join-Path (Join-Path $RepoRoot "skills") $s))) {
            $MissingShipped += "skill '$s' (expected at skills\$s\)"
        }
    }
    foreach ($h in $ActiveHooks) {
        $hookMatch = Get-ChildItem -Path (Join-Path $RepoRoot "hooks") -File -Filter "$h.*" -ErrorAction SilentlyContinue
        if (-not $hookMatch -or $hookMatch.Count -eq 0) {
            $MissingShipped += "hook '$h' (expected hooks\$h.ps1 / hooks\$h.sh)"
        }
    }
    foreach ($t in $ActiveTemplates) {
        $inSpecs = Test-Path (Join-Path (Join-Path $RepoRoot "specs\_templates") $t)
        $inDocs = Test-Path (Join-Path (Join-Path $RepoRoot "docs\_templates") $t)
        if (-not $inSpecs -and -not $inDocs) {
            $MissingShipped += "template '$t' (expected specs\_templates\$t or docs\_templates\$t)"
        }
    }
    foreach ($a in $ActiveAgents) {
        if (-not (Test-Path (Join-Path (Join-Path $RepoRoot "agents") "$a.md"))) {
            $MissingShipped += "agent '$a' (expected at agents\$a.md)"
        }
    }
    if ($MissingShipped.Count -gt 0) {
        Write-Host ""
        Write-Host "[ERROR]   profiles.json declares $($MissingShipped.Count) SHIPPED item(s) that do not exist in the repo:" -ForegroundColor Red
        foreach ($m in $MissingShipped) { Write-Host "[ERROR]     - $m" -ForegroundColor Red }
        Write-Host "[ERROR]   This is a manifest/repo integrity failure, not a planned gap  - fix profiles.json (move it to a planned* array if it's genuinely not built yet) or restore the missing file." -ForegroundColor Red
        Write-Host ""
    }

    Write-Host "[install] Active profiles: $($activeProfileNames -join ', ')" -ForegroundColor Cyan
    Write-Host "[install] Shipped  - skills: $($ActiveSkills.Count) | hooks: $($ActiveHooks.Count) | templates: $($ActiveTemplates.Count) | agents: $($ActiveAgents.Count)" -ForegroundColor Cyan
    Write-Host "[install] Planned  - skills: $($PlannedSkills.Count) | hooks: $($PlannedHooks.Count) | templates: $($PlannedTemplates.Count) | agents: $($PlannedAgents.Count)" -ForegroundColor Cyan
    foreach ($s in $PlannedSkills)    { Write-Host "[planned] skill '$s'  - not installed (planned for a future phase)" -ForegroundColor DarkGray }
    foreach ($h in $PlannedHooks)     { Write-Host "[planned] hook '$h'  - not installed (planned for a future phase)" -ForegroundColor DarkGray }
    foreach ($t in $PlannedTemplates) { Write-Host "[planned] template '$t'  - not installed (planned for a future phase)" -ForegroundColor DarkGray }
    foreach ($a in $PlannedAgents)    { Write-Host "[planned] agent '$a'  - not installed (planned for a future phase)" -ForegroundColor DarkGray }
}

# ---------------------------------------------------------------------------

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

function Copy-FileSafely([string]$SrcFile, [string]$DestPath, [string]$Label, [string]$BackupPath) {
    # Single-file variant of Copy-TreeSafely: new -> copy; identical -> no-op;
    # differs -> skip without -Force; differs + -Force -> back up to $BackupPath,
    # then overwrite. Same excluded-pattern guard as every other copy path.
    if (Test-Excluded (Split-Path $DestPath -Leaf)) { Write-Skip "$Label (excluded pattern)"; return }
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
    if ($srcHash -eq $dstHash) { return }
    if (-not $Force) {
        Write-Skip "$Label differs from the existing copy  - rerun with -Force to overwrite (a backup is taken first)"
        return
    }
    if ($DryRun) {
        Write-Action "[dry-run] would back up $DestPath to $BackupPath, then overwrite it with the repo version"
    } else {
        New-Item -ItemType Directory -Path (Split-Path $BackupPath -Parent) -Force | Out-Null
        Copy-Item $DestPath -Destination $BackupPath -Force
        Copy-Item $SrcFile -Destination $DestPath -Force
        Write-Action "$Label  (overwritten  - previous version backed up to $BackupPath)"
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

# --- Skills (filtered by profile: each skill is a subdirectory) ---
$skillsSrc = Join-Path $RepoRoot "skills"
$skillsDst = Join-Path $CentralDir "skills"
if ($ProfileFiltering) {
    foreach ($skillName in $ActiveSkills) {
        $skillDir = Join-Path $skillsSrc $skillName
        if (-not (Test-Path $skillDir)) {
            # Already reported under [ERROR] above (shipped item missing from disk) — don't copy.
            continue
        }
        Copy-TreeSafely $skillDir (Join-Path $skillsDst $skillName) "skills/$skillName" $CentralDir
    }
} else {
    Copy-TreeSafely $skillsSrc $skillsDst "skills" $CentralDir
}

# --- Hooks (filtered by profile: each hook is one or more files with the same base name) ---
$hooksSrc = Join-Path $RepoRoot "hooks"
$hooksDst = Join-Path $CentralDir "hooks"
if ($ProfileFiltering) {
    foreach ($hookName in $ActiveHooks) {
        $hookFiles = Get-ChildItem -Path $hooksSrc -File -Filter "$hookName.*" -ErrorAction SilentlyContinue
        if (-not $hookFiles -or $hookFiles.Count -eq 0) {
            # Already reported under [ERROR] above (shipped item missing from disk) — don't copy.
            continue
        }
        foreach ($hf in $hookFiles) {
            $destPath = Join-Path $hooksDst $hf.Name
            $destDir = Split-Path $destPath -Parent
            if (-not (Test-Path $destDir)) {
                if ($DryRun) { Write-Action "[dry-run] would create directory $destDir" }
                else { New-Item -ItemType Directory -Path $destDir -Force | Out-Null }
            }
            if (-not (Test-Path $destPath)) {
                if ($DryRun) { Write-Action "[dry-run] would create $destPath" }
                else { Copy-Item $hf.FullName -Destination $destPath -Force }
                Write-Action "hooks/$($hf.Name)  (new)"
                continue
            }
            $srcHash = (Get-FileHash $hf.FullName -Algorithm SHA256).Hash
            $dstHash = (Get-FileHash $destPath -Algorithm SHA256).Hash
            if ($srcHash -eq $dstHash) { continue }
            if (-not $Force) {
                Write-Skip "hooks/$($hf.Name) differs  - rerun with -Force to overwrite"
                continue
            }
            $backupPath = Join-Path $CentralDir "_install-backups\$Timestamp\hooks\$($hf.Name)"
            if ($DryRun) {
                Write-Action "[dry-run] would back up and overwrite hooks/$($hf.Name)"
            } else {
                New-Item -ItemType Directory -Path (Split-Path $backupPath -Parent) -Force | Out-Null
                Copy-Item $destPath -Destination $backupPath -Force
                Copy-Item $hf.FullName -Destination $destPath -Force
                Write-Action "hooks/$($hf.Name)  (overwritten  - backup at $backupPath)"
            }
        }
    }
    # Always copy hooks/README.md if it exists
    $hooksReadme = Join-Path $hooksSrc "README.md"
    if (Test-Path $hooksReadme) {
        $destReadme = Join-Path $hooksDst "README.md"
        if (-not (Test-Path $hooksDst)) {
            if (-not $DryRun) { New-Item -ItemType Directory -Path $hooksDst -Force | Out-Null }
        }
        if (-not (Test-Path $destReadme)) {
            if ($DryRun) { Write-Action "[dry-run] would create hooks/README.md" }
            else { Copy-Item $hooksReadme -Destination $destReadme -Force; Write-Action "hooks/README.md  (new)" }
        }
    }
} else {
    Copy-TreeSafely $hooksSrc $hooksDst "hooks" $CentralDir
}

# --- Templates (filtered by profile: from both specs/_templates and docs/_templates) ---
$specsTemplatesSrc = Join-Path $RepoRoot "specs\_templates"
$docsTemplatesSrc = Join-Path $RepoRoot "docs\_templates"
$specsTemplatesDst = Join-Path $CentralDir "specs\_templates"
$docsTemplatesDst = Join-Path $CentralDir "docs\_templates"

if ($ProfileFiltering) {
    foreach ($tplName in $ActiveTemplates) {
        # Check specs/_templates first, then docs/_templates
        $srcFile = Join-Path $specsTemplatesSrc $tplName
        $dstDir = $specsTemplatesDst
        if (-not (Test-Path $srcFile)) {
            $srcFile = Join-Path $docsTemplatesSrc $tplName
            $dstDir = $docsTemplatesDst
        }
        if (-not (Test-Path $srcFile)) {
            # Already reported under [ERROR] above (shipped item missing from disk) — don't copy.
            continue
        }
        if (-not (Test-Path $dstDir)) {
            if ($DryRun) { Write-Action "[dry-run] would create directory $dstDir" }
            else { New-Item -ItemType Directory -Path $dstDir -Force | Out-Null }
        }
        $destPath = Join-Path $dstDir $tplName
        if (-not (Test-Path $destPath)) {
            if ($DryRun) { Write-Action "[dry-run] would create $destPath" }
            else { Copy-Item $srcFile -Destination $destPath -Force }
            Write-Action "templates/$tplName  (new)"
            continue
        }
        $srcHash = (Get-FileHash $srcFile -Algorithm SHA256).Hash
        $dstHash = (Get-FileHash $destPath -Algorithm SHA256).Hash
        if ($srcHash -eq $dstHash) { continue }
        if (-not $Force) {
            Write-Skip "templates/$tplName differs  - rerun with -Force to overwrite"
            continue
        }
        $backupPath = Join-Path $CentralDir "_install-backups\$Timestamp\templates\$tplName"
        if ($DryRun) {
            Write-Action "[dry-run] would back up and overwrite templates/$tplName"
        } else {
            New-Item -ItemType Directory -Path (Split-Path $backupPath -Parent) -Force | Out-Null
            Copy-Item $destPath -Destination $backupPath -Force
            Copy-Item $srcFile -Destination $destPath -Force
            Write-Action "templates/$tplName  (overwritten  - backup at $backupPath)"
        }
    }
} else {
    Copy-TreeSafely $specsTemplatesSrc $specsTemplatesDst "specs/_templates" $CentralDir
    Copy-TreeSafely $docsTemplatesSrc $docsTemplatesDst "docs/_templates" $CentralDir
}

# --- Agents (filtered by profile: each agent is a single agents\<name>.md file) ---
$agentsSrc = Join-Path $RepoRoot "agents"
$agentsDst = Join-Path $CentralDir "agents"
if ($ProfileFiltering) {
    foreach ($agentName in $ActiveAgents) {
        $agentFile = Join-Path $agentsSrc "$agentName.md"
        if (-not (Test-Path $agentFile)) {
            # Already reported under [ERROR] above (shipped item missing from disk) — don't copy.
            continue
        }
        Copy-FileSafely $agentFile (Join-Path $agentsDst "$agentName.md") "agents/$agentName.md" (Join-Path $CentralDir "_install-backups\$Timestamp\agents\$agentName.md")
    }
    # Always copy agents/README.md if it exists (documentation only, not an agent)
    $agentsReadme = Join-Path $agentsSrc "README.md"
    if ((Test-Path $agentsReadme) -and $ActiveAgents.Count -gt 0) {
        $destReadme = Join-Path $agentsDst "README.md"
        if (-not (Test-Path $destReadme)) {
            if ($DryRun) { Write-Action "[dry-run] would create agents/README.md" }
            else {
                if (-not (Test-Path $agentsDst)) { New-Item -ItemType Directory -Path $agentsDst -Force | Out-Null }
                Copy-Item $agentsReadme -Destination $destReadme -Force
                Write-Action "agents/README.md  (new)"
            }
        }
    }
} else {
    Copy-TreeSafely $agentsSrc $agentsDst "agents" $CentralDir
}

foreach ($rootFile in @("CLAUDE.md.example", "settings.template.json", "settings.template.sh.json")) {
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
Write-Action "OPTIONAL: to adopt Graphify (dependency-graph accelerator) in a project, run"
Write-Action "scripts/setup-graphify.ps1 -ProjectDir <path> - it installs the CLI after"
Write-Action "confirmation, generates .graphify/, and scaffolds the curated docs."
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

    # Agents are COPIED per-file into $ClaudeHome\agents, never junctioned:
    # that directory commonly contains user-authored agents that a directory
    # link would hide. Additive only  - existing files that differ are skipped
    # without -Force; with -Force they are backed up next to themselves first.
    foreach ($agentName in $ActiveAgents) {
        $srcAgent = Join-Path (Join-Path $CentralDir "agents") "$agentName.md"
        if (-not (Test-Path $srcAgent)) { Write-Skip "agents/$agentName.md not present in central dir  - run the install step first"; continue }
        Copy-FileSafely $srcAgent (Join-Path (Join-Path $ClaudeHome "agents") "$agentName.md") "~/.claude/agents/$agentName.md" (Join-Path (Join-Path $ClaudeHome "agents") "$agentName.md.bak-$Timestamp")
    }

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
if ($MissingShipped.Count -gt 0) {
    Write-Host "[ERROR]   Finished with $($MissingShipped.Count) shipped item(s) missing from the repo (see [ERROR] lines above). profiles.json is out of sync." -ForegroundColor Red
    exit 1
}
Write-Action "Done."
