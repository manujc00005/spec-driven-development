#Requires -Version 5.1
<#
    PowerShell self-test for hooks/scope-keeper-reminder.ps1 (spec 036, AC-012).

    The hook runs before EVERY Edit/Write in every session, so its hard contract
    is "never fail an edit" (D002): every case below asserts exit 0, including
    the malformed and hostile ones.

    Usage: pwsh -File scripts/mindset-hook.test.ps1
#>

$ErrorActionPreference = "Continue"

$RepoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Hook     = Join-Path $RepoRoot "hooks/scope-keeper-reminder.ps1"
$TmpBase  = Join-Path ([System.IO.Path]::GetTempPath()) ("sdd-mindset-test-" + [System.Guid]::NewGuid().ToString("N").Substring(0, 8))
New-Item -ItemType Directory -Path $TmpBase -Force | Out-Null

$script:Passed = 0
$script:Failed = 0
function Pass([string]$m) { Write-Host "[PASS] $m"; $script:Passed++ }
function Fail([string]$m, [string]$d = "") {
    Write-Host "[FAIL] $m" -ForegroundColor Red
    if ($d) { Write-Host "       $d" -ForegroundColor Red }
    $script:Failed++
}

# Each run gets its own TMP so markers never leak between cases.
function Invoke-Hook {
    param([string]$Payload, [string]$KillSwitch = $null)
    # .NET's GetTempPath() resolves TMP before TEMP on Windows, and TMPDIR on
    # Unix. Redirect all three or the hook writes its marker to the real temp
    # dir while the assertions look somewhere else - which is exactly how this
    # test passed on macOS and failed on windows-latest.
    $prevTmpdir = $env:TMPDIR; $prevTemp = $env:TEMP; $prevTmp = $env:TMP
    $prevKill = $env:SDD_SCOPE_REMINDER
    $env:TMPDIR = $TmpBase; $env:TEMP = $TmpBase; $env:TMP = $TmpBase
    if ($null -ne $KillSwitch) { $env:SDD_SCOPE_REMINDER = $KillSwitch }
    try {
        $out = $Payload | & pwsh -NoProfile -File $Hook 2>$null | Out-String
        return [pscustomobject]@{ Out = $out.Trim(); Code = $LASTEXITCODE }
    } finally {
        $env:TMPDIR = $prevTmpdir; $env:TEMP = $prevTemp; $env:TMP = $prevTmp
        $env:SDD_SCOPE_REMINDER = $prevKill
    }
}
function Sid([string]$id) { '{"session_id":"' + $id + '","tool_name":"Edit"}' }

try {
    # --- AC-001 / AC-008 ---------------------------------------------------
    $r = Invoke-Hook (Sid "s-one")
    if ($r.Code -eq 0 -and $r.Out -match '"systemMessage"') {
        Pass "AC-001 first edit emits a systemMessage and exits 0"
    } else { Fail "AC-001 no message or non-zero exit" "code=$($r.Code)" }

    if ($r.Out -match '\[scope-keeper\]' -and $r.Out -match '/scope-keeper' -and
        $r.Out -match 'reminder, not a gate' -and $r.Out -match 'SDD_SCOPE_REMINDER=0') {
        Pass "AC-008 message is tagged, names the skill, disclaims enforcement, documents the kill-switch"
    } else { Fail "AC-008 message missing a required element" $r.Out.Substring(0, [Math]::Min(160, $r.Out.Length)) }

    try { $r.Out | ConvertFrom-Json | Out-Null; Pass "AC-001 the emitted payload is valid JSON" }
    catch { Fail "AC-001 emitted payload is not valid JSON" }

    # --- AC-002 ------------------------------------------------------------
    $r2 = Invoke-Hook (Sid "s-one")
    if ($r2.Code -eq 0 -and -not $r2.Out) { Pass "AC-002 a second edit in the same session is silent" }
    else { Fail "AC-002 hook repeated itself within one session" "code=$($r2.Code)" }

    # --- AC-003 ------------------------------------------------------------
    $r3 = Invoke-Hook (Sid "s-two")
    if ($r3.Out -match '"systemMessage"') { Pass "AC-003 a different session is reminded" }
    else { Fail "AC-003 a new session was not reminded" }

    # --- AC-004 ------------------------------------------------------------
    $r4 = Invoke-Hook (Sid "s-three") -KillSwitch "0"
    if ($r4.Code -eq 0 -and -not $r4.Out) { Pass "AC-004 SDD_SCOPE_REMINDER=0 silences the hook" }
    else { Fail "AC-004 kill-switch ignored" "code=$($r4.Code)" }

    # --- AC-005 ------------------------------------------------------------
    $badOk = $true
    foreach ($p in @("", "{", "not json at all", '{"tool_name":"Edit"}', '{"session_id":""}')) {
        $rb = Invoke-Hook $p
        if ($rb.Code -ne 0) { $badOk = $false; Fail "AC-005 non-zero exit on payload: '$p'" "code=$($rb.Code)" }
    }
    if ($badOk) { Pass "AC-005 empty, malformed and session-less payloads all exit 0" }

    # --- AC-006 ------------------------------------------------------------
    # Asserting "no marker with .. in its name" is too weak: an UNsanitised id
    # makes the write fail, so no such marker exists either way. Assert the
    # POSITIVE property - a hostile id still yields a usable, throttling marker
    # under a safe name, which only holds if the sanitiser actually ran.
    $canary = Join-Path $TmpBase "canary-must-survive"
    Set-Content $canary "do not delete"
    Get-ChildItem -Path $TmpBase -Filter ".sdd-scope-reminder-*" -Force -ErrorAction SilentlyContinue |
        Remove-Item -Force -ErrorAction SilentlyContinue
    $hostile = '{"session_id":"../../../../../../etc/passwd","tool_name":"Edit"}'
    $r6  = Invoke-Hook $hostile
    $marks = @(Get-ChildItem -Path $TmpBase -Filter ".sdd-scope-reminder-*" -Force -ErrorAction SilentlyContinue)
    $unsafe = @($marks | Where-Object { $_.Name -match '\.\.' }).Count
    $r6b = Invoke-Hook $hostile
    if ($r6.Code -eq 0 -and $marks.Count -eq 1 -and $unsafe -eq 0 -and
        $r6.Out -and -not $r6b.Out -and (Test-Path $canary)) {
        Pass "AC-006 a traversing session id is sanitised into a usable, throttling marker"
    } else {
        Fail "AC-006 traversal not neutralised" "code=$($r6.Code) markers=$($marks.Count) unsafe=$unsafe"
    }

    # --- AC-007 ------------------------------------------------------------
    $before = (& git -C $RepoRoot status --porcelain | Out-String)
    Invoke-Hook (Sid "s-tree") | Out-Null
    $after = (& git -C $RepoRoot status --porcelain | Out-String)
    if ($before -eq $after) { Pass "AC-007 the hook writes nothing inside the project tree" }
    else { Fail "AC-007 the hook dirtied the working tree" }
}
finally {
    Remove-Item -Path $TmpBase -Recurse -Force -ErrorAction SilentlyContinue
}

Write-Host ""
Write-Host "Results: $script:Passed passed, $script:Failed failed"
if ($script:Failed -gt 0) { exit 1 }
