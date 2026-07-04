$input_json = $input | Out-String | ConvertFrom-Json -ErrorAction SilentlyContinue
$FILE = $input_json.tool_input.file_path

if (-not $FILE) { exit 0 }

# Always allow specs/ and .claude/ paths
if ($FILE -match 'specs[\\/]|\.claude[\\/]') { exit 0 }

# Allow root-level .md files (outside specs/features/)
if ($FILE -match '\.md$' -and $FILE -notmatch 'specs[\\/]features') { exit 0 }

# No specs/features dir — not an SDD project, allow
if (-not (Test-Path "specs\features")) { exit 0 }

# Allow if any spec is Ready or In Progress (value is on the line after ## Status, possibly after a blank)
$active = $false
Get-ChildItem "specs\features\*\SPEC.md" -ErrorAction SilentlyContinue | ForEach-Object {
    $lines = Get-Content $_
    for ($i = 0; $i -lt $lines.Count - 1; $i++) {
        if ($lines[$i] -match '^## Status') {
            $j = $i + 1
            while ($j -lt $lines.Count -and $lines[$j].Trim() -eq '') { $j++ }
            if ($lines[$j].Trim() -match '^(Ready|In Progress)$') { $active = $true }
            break
        }
    }
}
if ($active) { exit 0 }

Write-Output '{"continue":false,"stopReason":"No active spec (Ready or In Progress). Run /sdd or /spec-create first."}'
