<#
    scope-keeper-reminder.ps1 - PreToolUse nudge on Edit/Write/NotebookEdit.

    PowerShell mirror of scope-keeper-reminder.sh (spec 036). The mindset skills
    are declared "always in effect", but a skill is model-invoked: its rules only
    reach context if the assistant chooses to load it. scope-keeper's own
    description names a deterministic trigger - "before your first edit" - and
    this is the harness observing it.

    Fires ONCE per session (keyed on session_id, falling back to a time throttle
    when that field is absent). Set SDD_SCOPE_REMINDER=0 to disable.

    Exit 0 ALWAYS - reinforcement, not enforcement (D002). Nothing here may fail
    an edit.
#>

$ErrorActionPreference = "SilentlyContinue"
$FallbackTtlSeconds = 3600

try {
    # Always drain stdin, even when disabled: an unread payload can hand the
    # caller a broken pipe.
    $input_raw = [Console]::In.ReadToEnd()

    if ($env:SDD_SCOPE_REMINDER -eq "0") { exit 0 }

    $sessionId = ""
    if ($input_raw -match '"session_id"\s*:\s*"([^"\\]*)"') { $sessionId = $Matches[1] }

    # The session id becomes a filename, so it is reduced to a closed character
    # set rather than escaped: "../../etc/passwd" must not be able to name a
    # path at all. Anything that sanitises away falls through to the time
    # throttle (AC-006).
    $safeId = ($sessionId -replace '[^A-Za-z0-9_-]', '')
    if ($safeId.Length -gt 64) { $safeId = $safeId.Substring(0, 64) }

    $tmp = [System.IO.Path]::GetTempPath()
    if ($safeId) {
        $marker = Join-Path $tmp ".sdd-scope-reminder-$safeId"
    } else {
        $marker = Join-Path $tmp ".sdd-scope-reminder-notsid"
    }

    if (Test-Path $marker) {
        if ($safeId) { exit 0 }   # this session has already been reminded
        $age = ((Get-Date).ToUniversalTime() - (Get-Item $marker).LastWriteTimeUtc).TotalSeconds
        if ($age -le $FallbackTtlSeconds) { exit 0 }
    }

    # A marker we cannot write means "remind again next time" - never a reason
    # to stay silent, and never a reason to fail.
    try { New-Item -ItemType File -Path $marker -Force | Out-Null } catch { }

    # Excerpt only. skills/scope-keeper/SKILL.md is the source of truth;
    # scripts/mindset-hook.test.sh asserts these claims still exist there, so
    # the two cannot drift silently (D004).
    $msg = '[scope-keeper] Before this edit - do exactly what was asked: the requested scope IS the deliverable. No drive-by refactors, no "while I am at it", no speculative generality. A real improvement you spot mid-task gets reported, not applied. Necessary-adjacent is in scope (say why); "would be nicer" is not. Dead code your change created is yours to remove; dead code you found is not. Match the surrounding code. Full manual: /scope-keeper. This is a reminder, not a gate - use your judgement. Silence it with SDD_SCOPE_REMINDER=0.'
    $payload = [ordered]@{ systemMessage = $msg }
    Write-Output ($payload | ConvertTo-Json -Compress)
} catch {
    # Never let an internal failure block an edit.
}
exit 0
