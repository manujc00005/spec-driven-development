#Requires -Version 5.1
<#
    PowerShell self-test for scripts/update.ps1 (spec 034, AC-013).

    update.ps1's manifest reader and delta logic were rewritten by spec 034
    (oldest-per-profile commit, verbatim profile replay) and had no automated
    coverage at all - the exact gap that let a manifest idempotence bug survive
    three specs in install.ps1 behind a parse-only Windows gate.

    Covers AC-002 (delta floor is the oldest per-profile commit) and AC-006 /
    AC-006b (a removed profile is not resurrected, including when core is all
    that remains recorded).

    Each case builds its own throwaway src/origin/clone/central, so nothing
    touches ~/.claude or the real central config.

    Usage: pwsh -File scripts/update.test.ps1
#>

$ErrorActionPreference = "Continue"

$RepoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$TmpBase  = Join-Path ([System.IO.Path]::GetTempPath()) ("sdd-update-test-" + [System.Guid]::NewGuid().ToString("N").Substring(0, 8))
New-Item -ItemType Directory -Path $TmpBase -Force | Out-Null

$script:Passed = 0
$script:Failed = 0
function Pass([string]$m) { Write-Host "[PASS] $m"; $script:Passed++ }
function Fail([string]$m, [string]$d = "") {
    Write-Host "[FAIL] $m" -ForegroundColor Red
    if ($d) { Write-Host "       $d" -ForegroundColor Red }
    $script:Failed++
}

# git is invoked directly, never through a wrapper: a PowerShell function with
# ValueFromRemainingArguments swallows -m, and `git commit` then opens an editor
# and blocks forever waiting on stdin.
function Invoke-Git {
    param([string]$Dir, [string[]]$Arguments)
    & git -C $Dir @Arguments 2>&1 | Out-Null
}

# Build src (two tagged releases) -> bare origin -> clone reset one release
# behind -> central dir installed from that clone.
function Build-Env {
    param([string]$Name)
    $root    = Join-Path $TmpBase $Name
    $src     = Join-Path $root "src"
    $origin  = Join-Path $root "origin.git"
    $clone   = Join-Path $root "clone"
    $central = Join-Path $root "central"
    New-Item -ItemType Directory -Path $root -Force | Out-Null

    Copy-Item $RepoRoot $src -Recurse -Force
    Remove-Item (Join-Path $src ".git") -Recurse -Force -ErrorAction SilentlyContinue

    Invoke-Git $src @("init", "--quiet")
    Invoke-Git $src @("config", "user.email", "test@example.com")
    Invoke-Git $src @("config", "user.name", "sdd test")
    Invoke-Git $src @("add", "-A")
    Invoke-Git $src @("commit", "--quiet", "-m", "v0.1.0")
    Invoke-Git $src @("tag", "v0.1.0")
    $ch = Join-Path $src "CHANGELOG.md"
    "## [0.2.0] - release two`n`n" + (Get-Content $ch -Raw) | Set-Content $ch -Encoding utf8
    Invoke-Git $src @("add", "-A")
    Invoke-Git $src @("commit", "--quiet", "-m", "v0.2.0")
    Invoke-Git $src @("tag", "v0.2.0")

    & git clone --quiet --bare $src $origin 2>&1 | Out-Null
    & git clone --quiet $origin $clone 2>&1 | Out-Null
    Invoke-Git $clone @("reset", "--hard", "--quiet", "v0.1.0")

    return [pscustomobject]@{ Clone = $clone; Central = $central }
}

function Invoke-Update {
    param([string]$Clone, [string]$Central)
    & pwsh -NoProfile -File (Join-Path $Clone "scripts/update.ps1") -CentralDir $Central 2>&1 | Out-String
}

try {
    # --- AC-002: the delta floor is the OLDEST per-profile commit ----------
    $e = Build-Env "ac002"
    & pwsh -NoProfile -File (Join-Path $e.Clone "install.ps1") `
        -CentralDir $e.Central -SkipLink -Profile java-spring-backend 2>&1 | Out-Null
    $v1 = (& git -C $e.Clone rev-parse v0.1.0 | Out-String).Trim()
    $v2 = (& git -C $e.Clone rev-parse v0.2.0 | Out-String).Trim()

    # Exactly what a partial install used to leave behind: the top level claims
    # the new commit while a recorded profile's files are still at the old one.
    $mp = Join-Path $e.Central ".sdd-install.json"
    $m  = Get-Content $mp -Raw | ConvertFrom-Json
    $m.installedCommit  = $v2
    $m.installedVersion = "v0.2.0"
    $state = [ordered]@{}
    foreach ($name in $m.profiles) {
        $state[$name] = [ordered]@{
            commit      = $(if ($name -eq "core") { $v1 } else { $v2 })
            version     = $(if ($name -eq "core") { "v0.1.0" } else { "v0.2.0" })
            installedAt = "2026-01-01T00:00:00Z"
        }
    }
    $m.profileState = $state
    ($m | ConvertTo-Json -Depth 5) | Set-Content $mp -Encoding utf8

    $out = Invoke-Update -Clone $e.Clone -Central $e.Central
    if ($out -match "Already up to date") {
        Fail "AC-002 delta taken from the newest commit - the stale profile was reported as current"
    } elseif ($out -notmatch "v0\.1\.0 -> v0\.2\.0") {
        Fail "AC-002 delta not computed from the oldest per-profile commit" ($out -split "`n" | Select-String "Updated:|Oldest" | Out-String)
    } elseif ($out -notmatch "Oldest recorded profile") {
        Fail "AC-002 the oldest-profile basis is not stated in the output"
    } else {
        Pass "AC-002 delta is computed from the oldest per-profile commit, not the newest"
    }

    # --- AC-006: a removed profile is not resurrected by update.ps1 --------
    $e2 = Build-Env "ac006"
    & pwsh -NoProfile -File (Join-Path $e2.Clone "install.ps1") `
        -CentralDir $e2.Central -SkipLink -Profile python-sql-data 2>&1 | Out-Null
    if (-not (Test-Path (Join-Path $e2.Central "skills/python-reviewer"))) {
        Fail "AC-006 setup: python-sql-data did not install"
    } else {
        & pwsh -NoProfile -File (Join-Path $e2.Clone "install.ps1") `
            -CentralDir $e2.Central -SkipLink -RemoveProfile python-sql-data 2>&1 | Out-Null
        if (Test-Path (Join-Path $e2.Central "skills/python-reviewer")) {
            Fail "AC-006 setup: -RemoveProfile did not delete the profile's files"
        } else {
            Invoke-Update -Clone $e2.Clone -Central $e2.Central | Out-Null
            if (Test-Path (Join-Path $e2.Central "skills/python-reviewer")) {
                Fail "AC-006 update.ps1 resurrected the removed profile"
            } else {
                Pass "AC-006 a removed profile stays removed across update.ps1"
            }
        }
    }

    # --- AC-006b: removing the LAST non-core profile ----------------------
    # The case D001/D010 exist for: with core alone recorded, the old code
    # passed no -Profile and install.ps1 fell back to defaults.profile.
    $e3 = Build-Env "ac006b"
    & pwsh -NoProfile -File (Join-Path $e3.Clone "install.ps1") `
        -CentralDir $e3.Central -SkipLink -Profile java-spring-backend 2>&1 | Out-Null
    & pwsh -NoProfile -File (Join-Path $e3.Clone "install.ps1") `
        -CentralDir $e3.Central -SkipLink -RemoveProfile java-spring-backend 2>&1 | Out-Null
    $recorded = (Get-Content (Join-Path $e3.Central ".sdd-install.json") -Raw | ConvertFrom-Json).profiles
    if (@($recorded) -join ',' -ne 'core') {
        Fail "AC-006b setup: expected only core recorded, got '$(@($recorded) -join ',')'"
    } else {
        Invoke-Update -Clone $e3.Clone -Central $e3.Central | Out-Null
        if (Test-Path (Join-Path $e3.Central "skills/java-spring-reviewer")) {
            Fail "AC-006b defaults.profile re-added the removed profile through update.ps1"
        } else {
            Pass "AC-006b removing the last non-core profile does not fall back to defaults.profile"
        }
    }
}
finally {
    Remove-Item -Path $TmpBase -Recurse -Force -ErrorAction SilentlyContinue
}

Write-Host ""
Write-Host "Results: $script:Passed passed, $script:Failed failed"
if ($script:Failed -gt 0) { exit 1 }
