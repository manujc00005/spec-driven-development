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

    # --- Spec 039 AC-001: first install links the CLAUDE.md the personal import
    # creates. Regression for BUG-1, where the link step ran BEFORE the personal
    # layer and never retried, leaving ~/.claude/CLAUDE.md missing on every fresh
    # machine. Hermetic via -ClaudeHome.
    $c11 = Join-Path $TmpBase "first-central"
    $h11 = Join-Path $TmpBase "first-home"
    New-Item -ItemType Directory -Path (Join-Path $c11 "personal\central") -Force | Out-Null
    Set-Content -Path (Join-Path $c11 "personal\central\CLAUDE.md") -Value "# personal global instructions" -Encoding utf8
    $firstOut = Invoke-Install @("-CentralDir", $c11, "-ClaudeHome", $h11, "-LinkUserClaude", "-Profile", "python-sql-data")
    $centralMd = Join-Path $c11 "CLAUDE.md"
    $homeMd    = Join-Path $h11 "CLAUDE.md"
    if (Test-Path $centralMd) {
        Pass "AC-001 the personal import creates <central>\CLAUDE.md on a first install"
    } else {
        Fail "AC-001 the personal import did not create <central>\CLAUDE.md" ($firstOut -split "`n" | Select-Object -Last 5)
    }
    if (Test-Path $homeMd) {
        Pass "AC-001 ClaudeHome CLAUDE.md exists after a first install"
    } else {
        Fail "AC-001 ClaudeHome CLAUDE.md missing after a first install" ($firstOut -split "`n" | Select-Object -Last 8)
    }
    # D002: the deferred message must not appear when the retry succeeded.
    if ($firstOut -notmatch "CLAUDE\.md link skipped") {
        Pass "AC-001 no contradictory 'link skipped' line when the retry linked the file"
    } else {
        Fail "AC-001 the run reported 'link skipped' for a file it went on to link"
    }

    # --- Spec 039 AC-009: no payload -> unchanged behaviour. The retry must not
    # invent a link, and the skip must still be reported exactly once.
    $c12 = Join-Path $TmpBase "nopayload-central"
    $h12 = Join-Path $TmpBase "nopayload-home"
    $noPayloadOut = Invoke-Install @("-CentralDir", $c12, "-ClaudeHome", $h12, "-LinkUserClaude", "-Profile", "python-sql-data")
    $skipCount = ([regex]::Matches($noPayloadOut, "CLAUDE\.md link skipped")).Count
    if (-not (Test-Path (Join-Path $h12 "CLAUDE.md")) -and $skipCount -eq 1) {
        Pass "AC-009 with no personal payload the skip is reported exactly once and no link is invented"
    } else {
        Fail "AC-009 payload-free path changed behaviour" "link=$(Test-Path (Join-Path $h12 'CLAUDE.md')) skips=$skipCount"
    }

    # --- Spec 039 AC-002/AC-003: the -CentralDir default and $DefaultCentralDir
    # are two literals of the same value (PowerShell cannot read a param()
    # default from inside param(), D005). Guard them against drift, and pin the
    # documented Windows default while we are here.
    $installSrc = Get-Content (Join-Path $RepoRoot "install.ps1") -Raw
    $paramDefault   = [regex]::Match($installSrc, '\[string\]\$CentralDir\s*=\s*"([^"]+)"').Groups[1].Value
    $constantValue  = [regex]::Match($installSrc, '\$DefaultCentralDir\s*=\s*"([^"]+)"').Groups[1].Value
    if ($paramDefault -eq "C:\ProgramData\ClaudeConfig" -and $constantValue -eq $paramDefault) {
        Pass 'AC-002/AC-003 the PowerShell default is C:\ProgramData\ClaudeConfig and $DefaultCentralDir agrees'
    } else {
        Fail "AC-002/AC-003 central-dir default drifted" "param='$paramDefault' constant='$constantValue'"
    }
    # The bash default must no longer appear in the refresh-command decision.
    $reportFn = [regex]::Match($installSrc, '(?s)function Report-UnrefreshedProfiles.*?\n\}').Value
    if ($reportFn -match '\$CentralDir -ne \$DefaultCentralDir' -and $reportFn -notmatch 'Join-Path \$HOME "\.claude-config"') {
        Pass "AC-003 Report-UnrefreshedProfiles compares against the PowerShell default, not the bash one"
    } else {
        Fail "AC-003 Report-UnrefreshedProfiles still uses the wrong default"
    }

    # --- Spec 039 AC-004/AC-005/AC-006: consumer discovery. $HOME is redirected
    # at a temp dir so the case is hermetic and does not depend on this machine
    # having a real ~/.claude-config. HOME and USERPROFILE are both set so the
    # child resolves $HOME the same way on Unix and on Windows.
    function Invoke-WithFakeHome {
        param([string]$Script, [string[]]$Arguments, [string]$FakeHome)
        $prevHome = $env:HOME; $prevProfile = $env:USERPROFILE
        try {
            $env:HOME = $FakeHome; $env:USERPROFILE = $FakeHome
            $out = & pwsh -NoProfile -File (Join-Path $RepoRoot $Script) @Arguments 2>&1 | Out-String
            return @{ Output = $out; ExitCode = $LASTEXITCODE }
        } finally { $env:HOME = $prevHome; $env:USERPROFILE = $prevProfile }
    }

    # A real install at the fallback location, and nothing at the Windows default.
    $fakeHome = Join-Path $TmpBase "fakehome"
    $fallbackCentral = Join-Path $fakeHome ".claude-config"
    Invoke-Install @("-CentralDir", $fallbackCentral, "-SkipLink", "-Profile", "python-sql-data") | Out-Null
    $proj = Join-Path $TmpBase "proj"
    New-Item -ItemType Directory -Path $proj -Force | Out-Null

    $lp = Invoke-WithFakeHome -Script "link-project.ps1" -Arguments @("-ProjectDir", $proj, "-DryRun") -FakeHome $fakeHome
    if ($lp.ExitCode -eq 0 -and $lp.Output -match [regex]::Escape($fallbackCentral)) {
        Pass 'AC-004 link-project.ps1 discovers the $HOME\.claude-config fallback when the default is absent'
    } else {
        Fail "AC-004 link-project.ps1 did not discover the fallback" "rc=$($lp.ExitCode) $($lp.Output)"
    }

    $wh = Invoke-WithFakeHome -Script "scripts/wire-hooks.ps1" -Arguments @("-ProjectDir", $proj, "-DryRun") -FakeHome $fakeHome
    if ($wh.ExitCode -eq 0 -and $wh.Output -notmatch "settings\.template\.json not found") {
        Pass 'AC-005 wire-hooks.ps1 discovers the $HOME\.claude-config fallback when the default is absent'
    } else {
        Fail "AC-005 wire-hooks.ps1 did not discover the fallback" "rc=$($wh.ExitCode) $($wh.Output)"
    }

    # Nothing installed anywhere: NOW "run install.ps1 first" is true, and the
    # warning must name every path it checked.
    $emptyHome = Join-Path $TmpBase "emptyhome"
    New-Item -ItemType Directory -Path $emptyHome -Force | Out-Null
    $lpMissing = Invoke-WithFakeHome -Script "link-project.ps1" -Arguments @("-ProjectDir", $proj, "-DryRun") -FakeHome $emptyHome
    if ($lpMissing.ExitCode -ne 0 -and
        $lpMissing.Output -match "C:\\ProgramData\\ClaudeConfig" -and
        $lpMissing.Output -match [regex]::Escape((Join-Path $emptyHome ".claude-config"))) {
        Pass "AC-006 link-project.ps1 names every path it checked before giving up"
    } else {
        Fail "AC-006 link-project.ps1 warning does not enumerate the checked paths" "rc=$($lpMissing.ExitCode) $($lpMissing.Output)"
    }
    # wire-hooks.ps1's not-found branch is unreachable from inside this repo -
    # $RepoRoot always holds a settings.template.json, which is the last
    # candidate - so its enumeration is asserted on the source, not at runtime.
    $wireSrc = Get-Content (Join-Path $RepoRoot "scripts/wire-hooks.ps1") -Raw
    if ($wireSrc -match 'not found\. Checked: \$\(\(\$templateRoots') {
        Pass "AC-006 wire-hooks.ps1 names every template path it checked before giving up (structural: branch unreachable from this repo)"
    } else {
        Fail "AC-006 wire-hooks.ps1 warning does not enumerate the checked paths"
    }

    # --- Spec 039 AC-007/AC-008/AC-012: the symlink -> hardlink -> copy ladder.
    # NOT executable here: on macOS/Linux the symlink rung always succeeds, so no
    # fallback ever runs. Asserted structurally, and verified for real only by the
    # manual Windows procedure in the spec's PLAN.md.
    $ladderFn = [regex]::Match($installSrc, '(?s)function Invoke-ClaudeMdLink.*?\n\}').Value
    $symIdx  = $ladderFn.IndexOf("ItemType SymbolicLink")
    $hardIdx = $ladderFn.IndexOf("ItemType HardLink")
    $copyIdx = $ladderFn.IndexOf("Copy-Item")
    if ($symIdx -ge 0 -and $hardIdx -gt $symIdx -and $copyIdx -gt $hardIdx) {
        Pass "AC-007 Invoke-ClaudeMdLink attempts symlink, then hard link, then copy (structural: not runnable off Windows)"
    } else {
        Fail "AC-007 the symlink -> hardlink -> copy order is not present" "sym=$symIdx hard=$hardIdx copy=$copyIdx"
    }
    if ($ladderFn -match "Fell back to a HARD LINK" -and $ladderFn -match "Fell back to a COPY" -and
        $ladderFn -match "drift apart" -and $ladderFn -match "NOT kept in sync") {
        Pass "AC-008/AC-012 each downgrade warns, and neither claims to stay synchronized"
    } else {
        Fail "AC-008/AC-012 a downgrade is silent or overstates what it guarantees"
    }
}
finally {
    Remove-Item -Path $TmpBase -Recurse -Force -ErrorAction SilentlyContinue
}

Write-Host ""
Write-Host "Results: $script:Passed passed, $script:Failed failed"
if ($script:Failed -gt 0) { exit 1 }
