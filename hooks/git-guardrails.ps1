$input_json = $input | Out-String | ConvertFrom-Json -ErrorAction SilentlyContinue
$COMMAND = $input_json.tool_input.command

if (-not $COMMAND) { exit 0 }

$dangerousPatterns = @(
    "git push",
    "git reset --hard",
    "git clean -fd",
    "git clean -f",
    "git branch -D",
    "git checkout \.",
    "git restore \.",
    "push --force",
    "reset --hard"
)

foreach ($pattern in $dangerousPatterns) {
    if ($COMMAND -match $pattern) {
        Write-Error "BLOCKED: '$COMMAND' matches dangerous pattern '$pattern'. The user has prevented you from doing this."
        exit 2
    }
}

exit 0
