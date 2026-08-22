#Requires -Version 5.1
<#
    PowerShell parity self-test for install.ps1 (spec 034 T020, D005).

    Scoped deliberately: it covers the subset of acceptance criteria where a
    Bash/PowerShell divergence would be SILENT - per-profile manifest stamping,
    v1 migration, removal ownership, the refusal set, and shipped-README
    refresh. It is NOT a port of scripts/install.test.sh.

    This exists because the repo's Windows CI is parse-only (spec 012 D002,
    about hooks), so every behavioural Windows claim until now rested on a
    manual spot-check - the same task that left specs 015 and 016 unclosed.

    Each case installs into a hermetic temp central dir with -SkipLink, so it
    never touches ~/.claude or the real central config.

    Usage: pwsh -File scripts/install.test.ps1
#>

$ErrorActionPreference = "Continue"

$RepoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$TmpBase  = Join-Path ([System.IO.Path]::GetTempPath()) ("sdd-install-test-" + [System.Guid]::NewGuid().ToString("N").Substring(0, 8))
New-Item -ItemType Directory -Path $TmpBase -Force | Out-Null

$script:Passed = 0
$script:Failed = 0
function Pass([string]$m) { Write-Host "[PASS] $m"; $script:Passed++ }
function Fail([string]$m, [string]$d = "") {
    Write-Host "[FAIL] $m" -ForegroundColor Red
    if ($d) { Write-Host "       $d" -ForegroundColor Red }
    $script:Failed++
}

function Invoke-Install {
    param([string[]]$Arguments)
    & pwsh -NoProfile -File (Join-Path $RepoRoot "install.ps1") @Arguments 2>&1 | Out-String
}

function Read-Manifest([string]$CentralDir) {
    $p = Join-Path $CentralDir ".sdd-install.json"
    if (-not (Test-Path $p)) { return $null }
    try { return Get-Content $p -Raw | ConvertFrom-Json } catch { return $null }
}

$headCommit = (& git -C $RepoRoot rev-parse HEAD 2>$null | Out-String).Trim()
$fakeOld    = "0123456789abcdef0123456789abcdef01234567"

try {
    # --- AC-001: a partial run stamps only the ACTIVE profiles ------------
    $c1 = Join-Path $TmpBase "ac001"
    Invoke-Install @("-CentralDir", $c1, "-SkipLink", "-Profile", "python-sql-data") | Out-Null
    $mp = Join-Path $c1 ".sdd-install.json"
    $m  = Get-Content $mp -Raw | ConvertFrom-Json
    $m.profileState.'python-sql-data'.commit = $fakeOld
    ($m | ConvertTo-Json -Depth 5) | Set-Content $mp -Encoding utf8
    $out = Invoke-Install @("-CentralDir", $c1, "-SkipLink", "-Profile", "java-spring-backend")
    $m2  = Read-Manifest $c1
    if ($m2.profileState.'python-sql-data'.commit -eq $fakeOld -and
        $m2.profileState.'java-spring-backend'.commit -eq $headCommit) {
        Pass "AC-001 inactive profile keeps its commit, active profile is restamped"
    } else {
        Fail "AC-001 per-profile stamping wrong" "python-sql-data=$($m2.profileState.'python-sql-data'.commit) java-spring-backend=$($m2.profileState.'java-spring-backend'.commit)"
    }
    if ($out -match "NOT refreshed by this run" -and $out -match "python-sql-data") {
        Pass "AC-001 unrefreshed profile is named in the run output"
    } else {
        Fail "AC-001 no warning naming the unrefreshed profile"
    }

    # --- AC-004: byte-identical manifest across identical runs ------------
    $c2 = Join-Path $TmpBase "ac004"
    Invoke-Install @("-CentralDir", $c2, "-SkipLink", "-Profile", "java-spring-backend") | Out-Null
    $first = Get-Content (Join-Path $c2 ".sdd-install.json") -Raw
    Invoke-Install @("-CentralDir", $c2, "-SkipLink", "-Profile", "java-spring-backend") | Out-Null
    $second = Get-Content (Join-Path $c2 ".sdd-install.json") -Raw
    if ($first -ceq $second) {
        Pass "AC-004 re-running the same commit leaves the manifest byte-identical"
    } else {
        Fail "AC-004 manifest changed on an identical re-run" "PowerShell 7 re-parses ISO stamps as [datetime]; see Format-ManifestStamp"
    }

    # --- AC-003: schemaVersion 1 migrates in place ------------------------
    $c3 = Join-Path $TmpBase "ac003"
    Invoke-Install @("-CentralDir", $c3, "-SkipLink", "-Profile", "java-spring-backend") | Out-Null
    $v1 = [ordered]@{
        schemaVersion = 1; installedVersion = "v0.0.1-old"; installedCommit = $fakeOld
        installedAt = "2026-01-01T00:00:00Z"
        profiles = @("core", "java-spring-backend", "python-sql-data")
        linkUserClaude = $false; sourceClone = "/tmp/fixture"
    }
    ($v1 | ConvertTo-Json -Depth 4) | Set-Content (Join-Path $c3 ".sdd-install.json") -Encoding utf8
    Invoke-Install @("-CentralDir", $c3, "-SkipLink", "-Profile", "java-spring-backend") | Out-Null
    $m3 = Read-Manifest $c3
    if ($m3.schemaVersion -eq 2 -and $m3.profileState.'python-sql-data'.commit -eq $fakeOld) {
        Pass "AC-003 v1 migrates to v2, attributing the old commit to untouched profiles"
    } else {
        Fail "AC-003 migration wrong" "schemaVersion=$($m3.schemaVersion) python-sql-data=$($m3.profileState.'python-sql-data'.commit)"
    }

    # --- AC-005: removal keeps shared items, deletes exclusives -----------
    $c4 = Join-Path $TmpBase "ac005"
    Invoke-Install @("-CentralDir", $c4, "-SkipLink", "-Profile", "java-spring-backend,next-prisma-web") | Out-Null
    Invoke-Install @("-CentralDir", $c4, "-SkipLink", "-RemoveProfile", "next-prisma-web") | Out-Null
    # database-review is shipped by BOTH profiles; prisma-migration-reviewer by one.
    if (Test-Path (Join-Path $c4 "skills/database-review")) {
        Pass "AC-005 an item still shipped by a recorded profile survives removal"
    } else {
        Fail "AC-005 shared item database-review was deleted"
    }
    if (-not (Test-Path (Join-Path $c4 "skills/prisma-migration-reviewer"))) {
        Pass "AC-005 an exclusively-owned item is deleted"
    } else {
        Fail "AC-005 exclusive item survived removal"
    }
    if (@(Get-ChildItem -Path (Join-Path $c4 "_install-backups") -Recurse -Filter "SKILL.md" -ErrorAction SilentlyContinue).Count -gt 0) {
        Pass "AC-005 every deleted file is backed up first"
    } else {
        Fail "AC-005 no backup found for the deleted skill"
    }
    $m4 = Read-Manifest $c4
    if ($m4.profiles -notcontains "next-prisma-web" -and -not $m4.profileState.'next-prisma-web') {
        Pass "AC-005 the profile is gone from both profiles and profileState"
    } else {
        Fail "AC-005 removed profile still recorded in the manifest"
    }

    # --- AC-007/AC-009/AC-010: the refusal set, and nothing touched -------
    $c5 = Join-Path $TmpBase "ac007"
    Invoke-Install @("-CentralDir", $c5, "-SkipLink", "-Profile", "python-sql-data") | Out-Null
    $before = @(Get-ChildItem -Path $c5 -Recurse -File).Count
    $refusalsOk = $true
    $cases = @(
        @("-RemoveProfile", "core"),
        @("-RemoveProfile", "no-such-profile"),
        @("-RemoveProfile", "../../etc"),
        @("-RemoveProfile", ""),
        @("-Profile", "python-sql-data", "-RemoveProfile", "python-sql-data")
    )
    foreach ($case in $cases) {
        & pwsh -NoProfile -File (Join-Path $RepoRoot "install.ps1") @("-CentralDir", $c5, "-SkipLink") @case *> $null
        if ($LASTEXITCODE -eq 0) { $refusalsOk = $false; Fail "refusal missing for: $($case -join ' ')" }
    }
    if ($refusalsOk) { Pass "AC-007/AC-009/AC-010 core, unknown, traversing, empty and conflicting names are all refused" }
    if (@(Get-ChildItem -Path $c5 -Recurse -File).Count -eq $before) {
        Pass "AC-007/AC-009/AC-010 no refused invocation changed the central dir"
    } else {
        Fail "a refused invocation modified the central dir"
    }

    # --- AC-008: dry-run removal writes nothing, reports both sets --------
    $c7 = Join-Path $TmpBase "ac008"
    Invoke-Install @("-CentralDir", $c7, "-SkipLink", "-Profile", "java-spring-backend,next-prisma-web") | Out-Null
    $dryBefore = @(Get-ChildItem -Path $c7 -Recurse -File).Count
    $dryOut = Invoke-Install @("-CentralDir", $c7, "-SkipLink", "-DryRun", "-RemoveProfile", "next-prisma-web")
    if (@(Get-ChildItem -Path $c7 -Recurse -File).Count -eq $dryBefore) {
        Pass "AC-008 -DryRun -RemoveProfile changes nothing on disk"
    } else {
        Fail "AC-008 dry-run removal modified the central dir"
    }
    if ($dryOut -match "would back up" -and $dryOut -match "keeping") {
        Pass "AC-008 dry-run reports both what it would delete and what it would keep"
    } else {
        Fail "AC-008 dry-run report incomplete"
    }

    # --- Ownership is computed against the FINAL profile set --------------
    $c9 = Join-Path $TmpBase "ownership"
    Invoke-Install @("-CentralDir", $c9, "-SkipLink", "-Profile", "java-spring-backend") | Out-Null
    $ownOut = Invoke-Install @("-CentralDir", $c9, "-SkipLink", "-Profile", "next-prisma-web", "-RemoveProfile", "java-spring-backend")
    if ($ownOut -match "keeping skill/database-review" -and (Test-Path (Join-Path $c9 "skills/database-review"))) {
        Pass "removal keeps an item shipped by a profile arriving in the same run"
    } else {
        Fail "removal ignored an incoming profile when computing ownership"
    }

    # --- AC-011: shipped READMEs refresh under -Force, with a backup ------
    $c6 = Join-Path $TmpBase "ac011"
    Invoke-Install @("-CentralDir", $c6, "-SkipLink", "-Profile", "java-spring-backend") | Out-Null
    Set-Content (Join-Path $c6 "agents/README.md") "stale placeholder" -NoNewline
    Set-Content (Join-Path $c6 "hooks/README.md")  "stale placeholder" -NoNewline
    Invoke-Install @("-CentralDir", $c6, "-SkipLink", "-Force", "-Profile", "java-spring-backend") | Out-Null
    $agentsSame = (Get-Content (Join-Path $c6 "agents/README.md") -Raw) -ceq (Get-Content (Join-Path $RepoRoot "agents/README.md") -Raw)
    $hooksSame  = (Get-Content (Join-Path $c6 "hooks/README.md")  -Raw) -ceq (Get-Content (Join-Path $RepoRoot "hooks/README.md")  -Raw)
    if ($agentsSame -and $hooksSame) {
        Pass "AC-011 agents/ and hooks/ README.md are refreshed under -Force"
    } else {
        Fail "AC-011 a shipped README stayed stale after -Force" "agents=$agentsSame hooks=$hooksSame"
    }
    if (@(Get-ChildItem -Path (Join-Path $c6 "_install-backups") -Recurse -Filter "README.md" -ErrorAction SilentlyContinue).Count -gt 0) {
        Pass "AC-011 the previous README content is backed up before overwriting"
    } else {
        Fail "AC-011 README overwritten without a backup"
    }

    # --- AC-012: after a full refresh, shipped trees match the repo -------
    $c10 = Join-Path $TmpBase "ac012"
    Invoke-Install @("-CentralDir", $c10, "-SkipLink", "-Force", "-Profile", "java-spring-backend") | Out-Null
    $mismatched = @()
    foreach ($rel in @("agents/README.md", "hooks/README.md")) {
        $a = Join-Path $RepoRoot $rel
        $b = Join-Path $c10 $rel
        if (-not (Test-Path $b) -or ((Get-Content $a -Raw) -cne (Get-Content $b -Raw))) { $mismatched += $rel }
    }
    # Every installed skill compared file-by-file against the repo: the
    # in-CI stand-in for the maintainer's `diff -rq` E2E. Walking the INSTALLED
    # side (not the repo side) keeps this about "what is on disk matches its
    # source", without asserting which profile ships what.
    $compared = 0
    $installedSkills = Join-Path $c10 "skills"
    if (Test-Path $installedSkills) {
        foreach ($f in Get-ChildItem $installedSkills -Recurse -File) {
            $rel2 = $f.FullName.Substring($c10.Length).TrimStart([char]92, [char]47)
            $srcFile = Join-Path $RepoRoot $rel2
            if (-not (Test-Path $srcFile)) { continue }   # adopter-local file, not shipped
            $compared++
            if ((Get-Content $srcFile -Raw) -cne (Get-Content $f.FullName -Raw)) { $mismatched += $rel2 }
        }
    }
    if ($compared -lt 20) { $mismatched += "TEST TOO WEAK: only $compared files compared" }
    if ($mismatched.Count -eq 0) {
        Pass "AC-012 shipped files match the repo after a --force run ($compared skill files compared)"
    } else {
        Fail "AC-012 shipped files differ from the repo" ($mismatched -join ", ")
    }
}
finally {
    Remove-Item -Path $TmpBase -Recurse -Force -ErrorAction SilentlyContinue
}

Write-Host ""
Write-Host "Results: $script:Passed passed, $script:Failed failed"
if ($script:Failed -gt 0) { exit 1 }
