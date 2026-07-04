$input_json = $input | Out-String | ConvertFrom-Json -ErrorAction SilentlyContinue
$FILE = $input_json.tool_input.file_path

if (-not $FILE) { exit 0 }
if ($FILE -notmatch '\.java$') { exit 0 }
if (-not (Test-Path "mvnw")) { exit 0 }

& ".\mvnw" compile -q 2>&1 | Select-Object -Last 30
