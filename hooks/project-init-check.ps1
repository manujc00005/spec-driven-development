$CONSTITUTION = "specs\CONSTITUTION.md"

if (-not (Test-Path "specs")) { exit 0 }

if (-not (Test-Path $CONSTITUTION)) {
    Write-Output '{"systemMessage":"[SDD] specs/CONSTITUTION.md not found. Agents will work without project rules. Run /project-init to set up your project constitution."}'
    exit 0
}

$todoCount = (Select-String -Path $CONSTITUTION -Pattern 'TODO:' -ErrorAction SilentlyContinue).Count
if ($todoCount -gt 0) {
    Write-Output "{`"systemMessage`":`"[SDD] specs/CONSTITUTION.md has $todoCount unfilled TODO sections. Run /project-init to complete your project setup.`"}"
}

exit 0
