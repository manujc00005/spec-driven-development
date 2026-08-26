# personal-config.ps1 - export/import of the personal Claude layer (spec 038).
#
# PowerShell counterpart of scripts/export-personal-config.sh and
# import-personal-config.sh, with the same manifest, semantics and summary.
#
# Import NEVER overwrites (D002): missing -> copy, identical -> skip,
# differing -> leave alone, write <name>.incoming, report a conflict.
# Two additive-only exceptions: MEMORY.md index lines, settings.json absent keys.
#
# Usage:
#   .\scripts\personal-config.ps1 -Mode Export [-AllowSuspicious] [-DryRun]
#   .\scripts\personal-config.ps1 -Mode Import [-DryRun]
[CmdletBinding()]
param(
    [Parameter(Mandatory)][ValidateSet('Export','Import')][string]$Mode,
    [string]$CentralDir = "$env:USERPROFILE\.claude-config",
    [string]$ClaudeHome = "$env:USERPROFILE\.claude",
    [switch]$AllowSuspicious,
    [switch]$DryRun
)
$ErrorActionPreference = 'Stop'

# --- T001: the manifest (mirrors PERSONAL_MANIFEST in the .sh lib) ------------
$Manifest = @(
    @{ Kind='central'; Path='CLAUDE.md' },
    @{ Kind='home';    Path='settings.json' },
    @{ Kind='home';    Path='agents' },
    @{ Kind='home';    Path='plugins\installed_plugins.json' },
    @{ Kind='home';    Path='plugins\known_marketplaces.json' },
    @{ Kind='glob';    Path='projects\*\memory' }
)
$NeverExport = @('settings.local.json')
$SecretRe = '(token|secret|api[-_]?key|password|passwd|Bearer [A-Za-z0-9._-]{8,}|-----BEGIN [A-Z ]*PRIVATE KEY-----)'

$Payload = Join-Path $CentralDir 'personal'

function Get-FileHashSafe([string]$p) {
    if (-not (Test-Path -LiteralPath $p)) { return $null }
    (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash
}

# T005: classifier. A symlink is `differs` and never followed.
function Get-Classification([string]$src, [string]$dst) {
    $item = Get-Item -LiteralPath $dst -ErrorAction SilentlyContinue
    if ($item -and $item.LinkType) { return 'differs' }
    if (-not $item) { return 'missing' }
    if ((Get-FileHashSafe $src) -eq (Get-FileHashSafe $dst)) { return 'identical' }
    return 'differs'
}

# T006: MEMORY.md additive merge. Appends absent pointer lines under a dated marker.
function Merge-MemoryIndex([string]$src, [string]$dst) {
    $incoming = Get-Content -LiteralPath $src
    $current  = Get-Content -LiteralPath $dst
    $have = [System.Collections.Generic.HashSet[string]]::new()
    foreach ($l in $current) { if ($l.Trim()) { [void]$have.Add($l.Trim()) } }
    $new = @($incoming | Where-Object { $_.Trim().StartsWith('- ') -and -not $have.Contains($_.Trim()) })
    if ($new.Count -eq 0) { return 0 }
    $stamp = Get-Date -Format 'yyyy-MM-dd'
    Add-Content -LiteralPath $dst -Value "`n<!-- imported $stamp -->"
    Add-Content -LiteralPath $dst -Value $new
    return $new.Count
}

# T007: settings.json merge. Absent top-level keys only; a local key always wins.
function Merge-SettingsJson([string]$src, [string]$dst) {
    try {
        $incoming = Get-Content -LiteralPath $src -Raw | ConvertFrom-Json
        $current  = Get-Content -LiteralPath $dst -Raw | ConvertFrom-Json
    } catch { return $null }   # refused: invalid JSON on one side
    $added = @()
    foreach ($p in $incoming.PSObject.Properties) {
        if (-not $current.PSObject.Properties.Name.Contains($p.Name)) {
            $current | Add-Member -NotePropertyName $p.Name -NotePropertyValue $p.Value
            $added += $p.Name
        }
    }
    if ($added.Count -gt 0) {
        ($current | ConvertTo-Json -Depth 20) | Set-Content -LiteralPath $dst -Encoding UTF8
    }
    return ,$added
}

function Resolve-Entry($entry) {
    switch ($entry.Kind) {
        'central' { @(Join-Path $CentralDir $entry.Path) }
        'home'    { @(Join-Path $ClaudeHome $entry.Path) }
        'glob'    { @(Get-ChildItem -Path (Join-Path $ClaudeHome $entry.Path) -Directory -ErrorAction SilentlyContinue | ForEach-Object { $_.FullName }) }
    }
}

# ============================ EXPORT =========================================
if ($Mode -eq 'Export') {
    $candidates = @(); $refused = 0
    foreach ($e in $Manifest) {
        foreach ($src in (Resolve-Entry $e)) {
            if (-not (Test-Path -LiteralPath $src)) { continue }
            if (Test-Path -LiteralPath $src -PathType Container) {
                $candidates += @(Get-ChildItem -LiteralPath $src -Recurse -File | ForEach-Object { $_.FullName })
            } else { $candidates += $src }
        }
    }
    $filtered = @(); $suspectLog = @()
    foreach ($f in $candidates) {
        if ($NeverExport -contains (Split-Path $f -Leaf)) {
            Write-Host "[export] REFUSED $f  (never exported - FR-002)"; $refused++; continue
        }
        $filtered += $f
        $hits = Select-String -LiteralPath $f -Pattern $SecretRe -AllMatches -ErrorAction SilentlyContinue
        foreach ($h in $hits) { $suspectLog += "$($h.Path):$($h.LineNumber):$($h.Line.Trim())" }
    }
    if ($suspectLog.Count -gt 0 -and -not $AllowSuspicious) {
        Write-Host "`n[export] ABORTED - credential-shaped content in $($suspectLog.Count) place(s):" -ForegroundColor Red
        $suspectLog | ForEach-Object { Write-Host "    $_" }
        Write-Host "`n[export] Nothing was written. Re-run with -AllowSuspicious if these are"
        Write-Host "[export] false positives. The payload repo must be PRIVATE."
        exit 1
    }
    if (-not $DryRun) {
        if (Test-Path -LiteralPath $Payload) { Remove-Item -LiteralPath $Payload -Recurse -Force }
        New-Item -ItemType Directory -Path $Payload -Force | Out-Null
    }
    $copied = 0
    foreach ($f in $filtered) {
        $dest = if ($f.StartsWith($CentralDir)) { Join-Path $Payload (Join-Path 'central' $f.Substring($CentralDir.Length).TrimStart([char]'\', [char]'/')) }
                elseif ($f.StartsWith($ClaudeHome)) { Join-Path $Payload (Join-Path 'home' $f.Substring($ClaudeHome.Length).TrimStart([char]'\', [char]'/')) }
                else { $null }
        if (-not $dest) { continue }
        if ($DryRun) { Write-Host "[dry-run] would copy $f -> $dest" }
        else {
            New-Item -ItemType Directory -Path (Split-Path $dest -Parent) -Force | Out-Null
            Copy-Item -LiteralPath $f -Destination $dest -Force
        }
        $copied++
    }
    if (-not $DryRun) {
        $files = @(Get-ChildItem -LiteralPath $Payload -Recurse -File | ForEach-Object { $_.FullName.Substring($Payload.Length).TrimStart([char]'\', [char]'/') })
        @{ exportedAt=(Get-Date -Format 'o'); sourceMachine=$env:COMPUTERNAME; fileCount=$files.Count; files=$files } |
            ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $Payload 'MANIFEST.json') -Encoding UTF8
    }
    Write-Host "`n[export] copied: $copied   refused: $refused   suspicious: $($suspectLog.Count)"
    Write-Host "[export] payload: $Payload"
    if (-not $DryRun) { Write-Host "[export] commit and push it - the payload repo MUST be private." }
    exit 0
}

# ============================ IMPORT =========================================
# FR-003: absent payload is a silent no-op.
if (-not (Test-Path -LiteralPath $Payload)) { exit 0 }

$copied = 0; $skipped = 0; $conflicts = 0; $merged = 0; $refused = 0
$conflictLog = @()

foreach ($item in (Get-ChildItem -LiteralPath $Payload -Recurse -File | Sort-Object FullName)) {
    $src = $item.FullName
    $leaf = Split-Path $src -Leaf
    if ($leaf -eq 'MANIFEST.json') { continue }
    # Normalise the separator: hardcoding '\' matched nothing on a non-Windows
    # host, so the import silently processed zero files and reported success.
    $rel = $src.Substring($Payload.Length).TrimStart([char]'\', [char]'/')
    $parts = $rel -split '[\\/]', 2
    $dst = if ($parts[0] -eq 'central') { Join-Path $CentralDir $parts[1] }
           elseif ($parts[0] -eq 'home') { Join-Path $ClaudeHome $parts[1] }
           else { $null }
    if (-not $dst) { continue }

    if ($leaf -eq 'settings.local.json') {
        Write-Host "[import] REFUSED $dst  (never imported - FR-002)"; $refused++; continue
    }

    $state = Get-Classification $src $dst

    if ($state -eq 'differs' -and $leaf -eq 'MEMORY.md') {
        if ($DryRun) { Write-Host "[dry-run] would merge index $dst" }
        else { $n = Merge-MemoryIndex $src $dst; Write-Host "[import] merged  $dst  (+$n index line(s))" }
        $merged++; continue
    }
    if ($state -eq 'differs' -and $leaf -eq 'settings.json') {
        if ($DryRun) { Write-Host "[dry-run] would merge keys into $dst" }
        else {
            $added = Merge-SettingsJson $src $dst
            if ($null -eq $added) { Write-Host "[import] REFUSED $dst  (invalid JSON on one side)"; $refused++; continue }
            Write-Host "[import] merged  $dst  (keys: $(if ($added.Count) { $added -join ',' } else { 'none' }))"
            $merged++
        }
        continue
    }

    switch ($state) {
        'missing' {
            if ($DryRun) { Write-Host "[dry-run] would copy  $dst" }
            else {
                New-Item -ItemType Directory -Path (Split-Path $dst -Parent) -Force | Out-Null
                Copy-Item -LiteralPath $src -Destination $dst -Force
            }
            $copied++
        }
        'identical' { $skipped++ }
        'differs' {
            # THE rule: the existing file is not touched. Ever.
            if ($DryRun) { Write-Host "[dry-run] would write $dst.incoming (conflict)" }
            else { Copy-Item -LiteralPath $src -Destination "$dst.incoming" -Force }
            $conflicts++; $conflictLog += "    $dst"
        }
    }
}

Write-Host "`n[import] copied: $copied   identical: $skipped   merged: $merged   conflicts: $conflicts   refused: $refused"
if ($conflicts -gt 0) {
    Write-Host "[import] These already existed and were LEFT UNTOUCHED. The incoming version"
    Write-Host "[import] is beside each as <name>.incoming - compare and resolve by hand:"
    $conflictLog | ForEach-Object { Write-Host $_ }
}
exit 0
