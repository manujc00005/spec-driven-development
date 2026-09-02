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

.PARAMETER AllProfiles
  Install every ENABLED profile in one explicit request, instead of naming them
  one by one. "Enabled" means simply "not marked disabled" in profiles.json.
  Two exclusions, both reported by name rather than dropped silently:
    * disabled profiles  - never installed by a blanket request; naming one with
      -Profile still fails hard, as before.
    * billable add-ons ("billable": true, e.g. seo-geo-addon) - a blanket request
      must not switch on a service the adopter has not contracted. Name it with
      -Profile to install it.
  Combines with -Profile: the union is installed.

.PARAMETER RemoveProfile
  Remove a profile: delete the items ONLY it owns and drop it from the install
  manifest, so scripts/update.ps1 stops re-installing it. Repeatable. Items
  still shipped by another recorded profile are kept; every deleted file is
  backed up under _install-backups/<ts>/removed/ first. 'core' cannot be
  removed. Combine with -DryRun to see exactly what would go. A run that only
  removes does NOT fall back to the default profile  - that would re-install
  what you just removed.

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
    [switch]$AllProfiles,
    [string[]]$RemoveProfile,
    [switch]$Force,
    [switch]$DryRun,
    [switch]$SkipLink,
    [switch]$LinkUserClaude,
    [string]$ClaudeHome = "$env:USERPROFILE\.claude"
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"

# --- --RemoveProfile argument validation (spec 034 FR-010, FR-013) ---------
# Pure argument checks, before anything touches the filesystem. Membership in
# profiles.json is checked in Remove-Profiles, still before any deletion.
# @($null) yields a one-element array containing $null, so a bare @($RemoveProfile)
# is truthy even when the switch was never passed. Normalise once, use everywhere.
$RemoveProfileList = @()
if ($null -ne $RemoveProfile) { $RemoveProfileList = @($RemoveProfile | Where-Object { $null -ne $_ }) }

foreach ($rp in $RemoveProfileList) {
    if ([string]::IsNullOrWhiteSpace($rp)) {
        Write-Host "[ERROR]   -RemoveProfile needs a profile name. Nothing was changed." -ForegroundColor Red
        exit 1
    }
    if ($rp -eq "core") {
        Write-Host "[ERROR]   'core' cannot be removed: it is alwaysInstalled and every other profile builds on it. Nothing was changed." -ForegroundColor Red
        exit 1
    }
    foreach ($ap in @($Profile)) {
        if (@($ap -split ',' | ForEach-Object { $_.Trim() }) -contains $rp) {
            Write-Host "[ERROR]   profile '$rp' is named in both -Profile and -RemoveProfile. Refusing to guess which you meant. Nothing was changed." -ForegroundColor Red
            exit 1
        }
    }
}

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
    } elseif ($RemoveProfileList.Count -gt 0) {
        # Spec 034 D010: a run whose point is -RemoveProfile must not fall back
        # to defaults.profile - that would delete the profile and re-install it
        # in the same pass. Removal-only runs resolve to core alone; the
        # remaining recorded profiles are then reported as unrefreshed by
        # FR-004, consistent with D007 (report, never auto-refresh).
        $requestedProfiles = @()
    } elseif ($profilesData.defaults.profile) {
        $requestedProfiles = @($profilesData.defaults.profile)
    } else {
        # No -Profile and no defaults.profile to fall back to. Without this
        # branch the run continues with an empty request and installs core
        # only, exiting 0 - a silent near-empty install that looks like a
        # success. Mirrors the same guard in install.sh.
        Write-Host ""
        Write-Host "[ERROR]   no profile requested and profiles.json declares no 'defaults.profile' to fall back to." -ForegroundColor Red
        Write-Host "[ERROR]   Refusing to continue with a core-only install that would look like a success  - pass -Profile <name>, or repair defaults.profile in profiles.json." -ForegroundColor Red
        exit 1
    }

    # Spec 030 FR-008..FR-010: -AllProfiles is an EXPLICIT request for every enabled
    # profile. It expands here, before validation, so it inherits the same unknown-name and
    # disabled-name handling as an explicit -Profile. Two exclusions, both reported by name:
    #   * disabled: true  - never installed by a blanket request (FR-009); naming one with
    #     -Profile still fails hard, and that path is untouched.
    #   * billable: true  - a blanket request must not switch on an uncontracted service
    #     (FR-010). Naming it with -Profile still installs it - the adopter opting in.
    # -AllProfiles unions with -Profile, and a profile named explicitly is never also
    # reported as skipped, which would make the output contradict itself.
    $skippedBillable = @()
    $skippedDisabled = @()
    if ($AllProfiles) {
        foreach ($prop in $profilesData.profiles.PSObject.Properties) {
            $pName = $prop.Name
            if ($requestedProfiles -contains $pName) { continue }
            $pDef = $prop.Value
            if ($pDef.disabled -eq $true) { $skippedDisabled += $pName }
            elseif ($pDef.billable -eq $true) { $skippedBillable += $pName }
            else { $requestedProfiles += $pName }
        }
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

    # Spec 030 AC-017: a blanket request states what it left out, by name.
    if ($skippedBillable.Count -gt 0) {
        Write-Host "[install] Skipped (billable add-on, not installed by -AllProfiles): $($skippedBillable -join ' ')"
        Write-Host "[install]   These are separately-billed services. Install one explicitly with: -Profile <name>"
    }
    if ($skippedDisabled.Count -gt 0) {
        Write-Host "[install] Skipped (disabled in profiles.json): $($skippedDisabled -join ' ')"
    }

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

# Spec 034: ConvertFrom-Json in PowerShell 7 parses ISO-8601-looking strings
# into [datetime] objects, and interpolating one back renders it in the current
# culture ("08/21/2026 16:25:52") instead of the canonical stamp. That silently
# broke manifest idempotence on Windows - spec 015 AC-003 held on bash only.
# Every timestamp read back out of a manifest goes through here.
function Format-ManifestStamp {
    param($Value)
    if ($null -eq $Value) { return $null }
    if ($Value -is [datetime]) { return $Value.ToUniversalTime().ToString("yyyy-MM-dd'T'HH:mm:ss'Z'") }
    return "$Value"
}

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

# ---------------------------------------------------------------------------
# Profile removal (spec 034 FR-007..FR-014) - PowerShell mirror of the bash
# remove_profiles(). Same contract: ownership from profiles.json alone (D004),
# a backup before every deletion with a failed backup aborting the run, and it
# executes before the install pass.
# ---------------------------------------------------------------------------
function Remove-ItemSafely {
    param([string]$Path, [string]$Label)
    if (-not (Test-Path $Path)) {
        Write-Action "  $Label  (not installed - nothing to remove)"
        return $true
    }
    $backup = Join-Path $CentralDir "_install-backups/$Timestamp/removed/$Label"
    if ($DryRun) {
        Write-Action "  [dry-run] would back up $Label -> $backup, then delete it"
        return $true
    }
    try {
        $parent = Split-Path $backup -Parent
        if (-not (Test-Path $parent)) { New-Item -ItemType Directory -Path $parent -Force | Out-Null }
        Copy-Item $Path -Destination $backup -Recurse -Force -ErrorAction Stop
    } catch {
        Write-Host "[ERROR]   could not back up $Label  - it was NOT deleted. $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
    try {
        # A junction/symlink must be unlinked, never recursed into: Remove-Item
        # -Recurse on a reparse point can delete the content behind it (same
        # hazard Remove-DirLinkSafely documents above). Central-dir items are
        # normally real directories, but removal is the one path where being
        # wrong is unrecoverable.
        $item = Get-Item $Path -Force
        if ($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) {
            $item.Delete()
        } else {
            Remove-Item $Path -Recurse -Force -ErrorAction Stop
        }
    } catch {
        Write-Host "[ERROR]   backed up $Label but could not delete it  - central dir may be inconsistent." -ForegroundColor Red
        return $false
    }
    Write-Action "  removed $Label  (backup at $backup)"
    return $true
}

function Remove-Profiles {
    if ($RemoveProfileList.Count -eq 0) { return }

    # AC-010: the name is validated against the closed set of profiles.json keys
    # BEFORE anything is deleted. Validating against a known set is a stronger
    # guard than sanitising a path - a traversing name simply is not a profile.
    $validNames = @($profilesData.profiles.PSObject.Properties.Name)
    $unknown = @($RemoveProfileList | Where-Object { $validNames -notcontains $_ })
    if ($unknown.Count -gt 0) {
        Write-Host "[ERROR]   unknown profile(s): $($unknown -join ', '). Valid profiles: $($validNames -join ', '). Nothing was changed." -ForegroundColor Red
        exit 1
    }

    $manifestPath = Join-Path $CentralDir ".sdd-install.json"
    $recorded = @()
    if (Test-Path $manifestPath) {
        try {
            $m = Get-Content $manifestPath -Raw | ConvertFrom-Json
            if ($m.profiles) { $recorded = @($m.profiles | Where-Object { $_ -is [string] }) }
        } catch { }
    }

    $toRemove = @()
    foreach ($p in $RemoveProfileList) {
        if ($recorded -notcontains $p) {
            Write-Action "Profile '$p' is not recorded in the install manifest  - nothing to remove."
        } else {
            $toRemove += $p
        }
    }
    if ($toRemove.Count -eq 0) { return }

    # Ownership is computed against the FINAL profile set, not merely the
    # recorded one: a profile being installed in this same run (-Profile X
    # -RemoveProfile Y) is part of the outcome, so an item it ships must be
    # kept rather than deleted-then-reinstalled.
    $remaining = @($recorded | Where-Object { $toRemove -notcontains $_ })
    foreach ($p in @($activeProfileNames)) {
        if ($toRemove -notcontains $p -and $remaining -notcontains $p) { $remaining += $p }
    }
    if ($remaining -notcontains "core") { $remaining += "core" }

    Write-Action "Removing profile(s): $($toRemove -join ', ')"

    $failed = $false
    $keptCount = 0
    foreach ($pair in @(@("skills","skill"), @("hooks","hook"), @("templates","template"), @("agents","agent"))) {
        $key = $pair[0]; $kind = $pair[1]
        $doomed = @(); $kept = @()
        foreach ($p in $toRemove)  { if ($profilesData.profiles.$p.$key) { $doomed += @($profilesData.profiles.$p.$key) } }
        foreach ($p in $remaining) { if ($profilesData.profiles.$p.$key) { $kept  += @($profilesData.profiles.$p.$key) } }
        foreach ($item in ($doomed | Sort-Object -Unique)) {
            # Defence in depth: profiles.json is repo content, but an item name is
            # joined to a path, so anything path-like is refused outright.
            if ($item -isnot [string] -or $item -match '[\\/]' -or $item.StartsWith(".")) {
                Write-Host "[ERROR]   refusing to act on suspicious item name '$item'. Nothing further was changed." -ForegroundColor Red
                exit 1
            }
            if ($kept -contains $item) {
                $keptCount++
                Write-Action "  keeping $kind/$item  (still shipped by another recorded profile)"
                continue
            }
            switch ($kind) {
                "skill"  { if (-not (Remove-ItemSafely -Path (Join-Path $CentralDir "skills/$item")    -Label "skills/$item"))   { $failed = $true } }
                "agent"  { if (-not (Remove-ItemSafely -Path (Join-Path $CentralDir "agents/$item.md") -Label "agents/$item.md")) { $failed = $true } }
                "template" {
                    $specTpl = Join-Path $CentralDir "specs/_templates/$item"
                    $docsTpl = Join-Path $CentralDir "docs/_templates/$item"
                    if (Test-Path $specTpl)      { if (-not (Remove-ItemSafely -Path $specTpl -Label "specs/_templates/$item")) { $failed = $true } }
                    elseif (Test-Path $docsTpl)  { if (-not (Remove-ItemSafely -Path $docsTpl -Label "docs/_templates/$item"))  { $failed = $true } }
                    else { Write-Action "  templates/$item  (not installed - nothing to remove)" }
                }
                "hook" {
                    $hookFiles = @(Get-ChildItem -Path (Join-Path $CentralDir "hooks") -Filter "$item.*" -File -ErrorAction SilentlyContinue)
                    if ($hookFiles.Count -eq 0) { Write-Action "  hooks/$item  (not installed - nothing to remove)" }
                    foreach ($hf in $hookFiles) {
                        if (-not (Remove-ItemSafely -Path $hf.FullName -Label "hooks/$($hf.Name)")) { $failed = $true }
                    }
                }
            }
        }
    }

    if ($keptCount -gt 0) { Write-Action "  $keptCount item(s) kept because another recorded profile still ships them." }

    if ($failed) {
        Write-Host "[ERROR]   removal did not complete (see [ERROR] above). Items reported as 'removed' above ARE deleted and are recoverable from $CentralDir/_install-backups/$Timestamp/removed/; the rest were left in place. The manifest was NOT modified, so re-running the same command retries, and 'install.ps1 -Profile <name>' restores the profile outright." -ForegroundColor Red
        exit 1
    }

    # FR-007: drop the profiles from the manifest. Dry-run leaves it untouched
    # (AC-008) - nothing was deleted either, so the record must still match.
    if ($DryRun) {
        Write-Action "[dry-run] would remove $($toRemove -join ', ') from the install manifest"
        return
    }
    try {
        $m = Get-Content $manifestPath -Raw | ConvertFrom-Json
        $newProfiles = @($m.profiles | Where-Object { $toRemove -notcontains $_ })
        $newState = [ordered]@{}
        if ($m.profileState) {
            foreach ($name in $newProfiles) {
                if ($m.profileState.$name) {
                    $newState[$name] = [ordered]@{
                        commit      = "$($m.profileState.$name.commit)"
                        version     = "$($m.profileState.$name.version)"
                        installedAt = (Format-ManifestStamp $m.profileState.$name.installedAt)
                    }
                }
            }
        }
        $data = [ordered]@{
            schemaVersion    = 2
            installedVersion = "$($m.installedVersion)"
            installedCommit  = "$($m.installedCommit)"
            installedAt      = (Format-ManifestStamp $m.installedAt)
            profiles         = @($newProfiles)
            profileState     = $newState
            linkUserClaude   = [bool]($m.linkUserClaude -eq $true)
            sourceClone      = "$($m.sourceClone)"
        }
        $json = ($data | ConvertTo-Json -Depth 5) + "`n"
        [System.IO.File]::WriteAllText($manifestPath, $json, (New-Object System.Text.UTF8Encoding($false)))
        Write-Action "Install manifest updated  - removed: $($toRemove -join ', ')"
    } catch {
        Write-Warn2 "profile files were removed but the manifest could not be updated  - re-run the installer to resynchronise it"
    }
}

Remove-Profiles

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
        # Spec 034 FR-015/D009: shipped documentation, refreshed like every
        # other shipped file. The old write-once guard "protected" adopter
        # edits by going permanently stale and reporting nothing.
        Copy-FileSafely -SrcFile $hooksReadme -DestPath $destReadme -Label "hooks/README.md" `
            -BackupPath (Join-Path $CentralDir "_install-backups/$Timestamp/hooks/README.md")
    }
    # Always copy hooks/lib/: it is a shared dependency sourced by several hooks
    # (git-guardrails, sdd-spec-guard, ...), not a per-profile item - without it
    # those hooks crash with exit 1 and guardrails silently stop blocking.
    $hooksLibSrc = Join-Path $hooksSrc "lib"
    if (Test-Path $hooksLibSrc) {
        Copy-TreeSafely $hooksLibSrc (Join-Path $hooksDst "lib") "hooks/lib" $CentralDir
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
        # Spec 034 FR-015/D009 - see the hooks/README.md note above.
        if (-not $DryRun -and -not (Test-Path $agentsDst)) { New-Item -ItemType Directory -Path $agentsDst -Force | Out-Null }
        Copy-FileSafely -SrcFile $agentsReadme -DestPath $destReadme -Label "agents/README.md" `
            -BackupPath (Join-Path $CentralDir "_install-backups/$Timestamp/agents/README.md")
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

# ---------------------------------------------------------------------------
# Install manifest (spec 015 FR-001): records what this run installed so
# scripts/update.ps1 can answer "what's new since your version?". Written only
# after a successful non-dry-run install; a write failure is a warning, never
# an install failure. Profiles accumulate across runs; linkUserClaude is
# sticky once any run has linked. A corrupt existing manifest is discarded
# silently  - it is framework-owned state, never adopter content. Written as
# UTF-8 without BOM so the bash update script's python reader parses it too.
# ---------------------------------------------------------------------------
function Write-InstallManifest {
    $manifestPath = Join-Path $CentralDir ".sdd-install.json"
    try {
        $commit = ""
        try { $commit = (& git -C $RepoRoot rev-parse HEAD 2>&1 | Out-String).Trim() } catch { }
        if ($LASTEXITCODE -ne 0 -or -not $commit) { $commit = "unknown" }
        $version = ""
        try { $version = (& git -C $RepoRoot describe --tags --always 2>&1 | Out-String).Trim() } catch { }
        if ($LASTEXITCODE -ne 0 -or -not $version) { $version = $commit }

        $existingProfiles = @()
        $existingLink = $false
        $existingAt = $null
        $existingCommit = $null
        $existingVersion = $null
        $rawState = $null
        if (Test-Path $manifestPath) {
            try {
                $old = Get-Content $manifestPath -Raw | ConvertFrom-Json
                # Spec 034 D003: only schema versions this installer understands
                # are carried forward. A future version is discarded wholesale
                # rather than misread key-by-key.
                $oldSchema = $old.schemaVersion
                if ($oldSchema -eq 1 -or $oldSchema -eq 2) {
                    if ($old.profiles) { $existingProfiles = @($old.profiles | Where-Object { $_ -is [string] }) }
                    if ($old.linkUserClaude -eq $true) { $existingLink = $true }
                    $existingAt = Format-ManifestStamp $old.installedAt
                    $existingCommit = $old.installedCommit
                    $existingVersion = $old.installedVersion
                    $rawState = $old.profileState
                }
            } catch { }  # absent or corrupt -> start fresh; never fatal
        }

        # Normalize into a per-profile map. v1 had no such record, so D003
        # attributes its single top-level commit to every recorded profile:
        # knowingly optimistic, but it asserts nothing the v1 format did not
        # already assert for the whole set.
        $state = @{}
        foreach ($name in $existingProfiles) {
            $entry = $null
            if ($rawState) { $entry = $rawState.$name }
            if ($entry -and $entry.commit) {
                $stateVersion = $entry.version
                if (-not $stateVersion) { $stateVersion = $entry.commit }
                $state[$name] = @{ commit = "$($entry.commit)"; version = "$stateVersion"; installedAt = (Format-ManifestStamp $entry.installedAt) }
            } else {
                $fallbackVersion = $existingVersion
                if (-not $fallbackVersion) { $fallbackVersion = $existingCommit }
                $state[$name] = @{ commit = "$existingCommit"; version = "$fallbackVersion"; installedAt = (Format-ManifestStamp $existingAt) }
            }
        }

        $merged = New-Object System.Collections.ArrayList
        foreach ($p in ($existingProfiles + @($activeProfileNames))) {
            if ($p -and -not $merged.Contains($p)) { [void]$merged.Add($p) }
        }

        $now = (Get-Date).ToUniversalTime().ToString("yyyy-MM-dd'T'HH:mm:ss'Z'")

        # installedAt means "when this version was installed", not "last run":
        # preserve it when re-installing the same commit so a no-op update leaves
        # the manifest byte-identical (spec 015 AC-003, spec 034 FR-006).
        # Applied per profile.
        foreach ($name in @($activeProfileNames)) {
            $previous = $state[$name]
            if ($previous -and $previous.commit -eq $commit -and $previous.installedAt) {
                $entryAt = Format-ManifestStamp $previous.installedAt
            } else {
                $entryAt = $now
            }
            $state[$name] = @{ commit = "$commit"; version = "$version"; installedAt = "$entryAt" }
        }

        # Only profiles still on the list keep a record, in list order.
        $orderedState = [ordered]@{}
        foreach ($name in $merged) {
            if ($state.ContainsKey($name)) {
                $orderedState[$name] = [ordered]@{
                    commit      = "$($state[$name].commit)"
                    version     = "$($state[$name].version)"
                    installedAt = (Format-ManifestStamp $state[$name].installedAt)
                }
            }
        }

        # Spec 034 FR-004: anything recorded but not active this run kept its old
        # files, so it is stale by definition. Reported, never silently refreshed
        # (D007).
        $unrefreshed = @($merged | Where-Object { @($activeProfileNames) -notcontains $_ })

        if ($existingCommit -eq $commit -and $existingAt) {
            $topInstalledAt = Format-ManifestStamp $existingAt
        } else {
            $topInstalledAt = $now
        }

        $data = [ordered]@{
            schemaVersion    = 2
            # Spec 034 FR-005: top level means "the newest commit any profile
            # reached", retained so a pre-034 reader still resolves. It is NOT a
            # freshness claim about every recorded profile - that is what
            # profileState is for, and update.ps1 takes its delta from the
            # oldest entry there.
            installedVersion = "$version"
            installedCommit  = "$commit"
            installedAt      = "$topInstalledAt"
            profiles         = @($merged)
            profileState     = $orderedState
            linkUserClaude   = [bool]($existingLink -or $LinkUserClaude)
            sourceClone      = "$RepoRoot"
        }
        $json = ($data | ConvertTo-Json -Depth 5) + "`n"
        [System.IO.File]::WriteAllText($manifestPath, $json, (New-Object System.Text.UTF8Encoding($false)))
        Write-Action "Install manifest written -> $manifestPath"

        Report-UnrefreshedProfiles -Unrefreshed $unrefreshed -State $orderedState
    } catch {
        Write-Warn2 "could not write install manifest $manifestPath  - scripts/update.ps1 will run in unknown-version mode until a later install succeeds. Error: $($_.Exception.Message)"
    }
}

# Spec 034 FR-004: name every recorded profile this run did not refresh, with
# the commit it is stuck at and the exact command that fixes it. Informational
# only - it must never change the exit code, and it prints nothing when the
# active set already covered every recorded profile.
function Report-UnrefreshedProfiles {
    param($Unrefreshed, $State)
    if (-not $Unrefreshed -or @($Unrefreshed).Count -eq 0) { return }
    Write-Warn2 "$(@($Unrefreshed).Count) recorded profile(s) were NOT refreshed by this run - their files are still at the commit shown:"
    foreach ($name in $Unrefreshed) {
        $stamp = "unknown"
        if ($State[$name]) {
            if ($State[$name].version) { $stamp = $State[$name].version }
            elseif ($State[$name].commit) { $stamp = $State[$name].commit }
        }
        Write-Warn2 "    $name  (installed at $stamp)"
    }
    $cmd = ".\install.ps1 -Force"
    foreach ($name in $Unrefreshed) {
        if ($name -eq "core") { continue }  # always installed implicitly
        $cmd = "$cmd -Profile $name"
    }
    if ($LinkUserClaude) { $cmd = "$cmd -LinkUserClaude" }
    if ($CentralDir -ne (Join-Path $HOME ".claude-config")) { $cmd = "$cmd -CentralDir $CentralDir" }
    Write-Warn2 "  refresh them with:  $cmd"
}

if ($DryRun) {
    Write-Action "[dry-run] would write install manifest $(Join-Path $CentralDir '.sdd-install.json')"
} else {
    Write-InstallManifest
}

Write-Action "Done."
