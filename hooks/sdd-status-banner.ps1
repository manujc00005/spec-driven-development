if (-not (Test-Path "specs\features")) { exit 0 }

$statuses = Get-ChildItem "specs\features\*\SPEC.md" -ErrorAction SilentlyContinue | ForEach-Object {
    $lines = Get-Content $_
    for ($i = 0; $i -lt $lines.Count - 1; $i++) {
        if ($lines[$i] -match '^## Status') {
            # skip blank lines after the heading
            $j = $i + 1
            while ($j -lt $lines.Count -and $lines[$j].Trim() -eq '') { $j++ }
            $lines[$j].Trim()
            break
        }
    }
} | Where-Object { $_ } | Group-Object | ForEach-Object { "$($_.Count)x $($_.Name)" }

if (-not $statuses) { exit 0 }

$line = $statuses -join '  '
Write-Output "{`"systemMessage`":`"[SDD] $line`"}"
