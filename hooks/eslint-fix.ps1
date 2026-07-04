$input_json = $input | Out-String | ConvertFrom-Json -ErrorAction SilentlyContinue
$FILE = $input_json.tool_input.file_path

if (-not $FILE) { exit 0 }
if ($FILE -notmatch '\.(ts|tsx|js|jsx)$') { exit 0 }

$hasConfig = (Test-Path ".eslintrc*") -or (Test-Path "eslint.config*")
if (-not $hasConfig) { exit 0 }

npx eslint --fix $FILE 2>&1 | Select-Object -Last 10
