$input_json = $input | Out-String | ConvertFrom-Json -ErrorAction SilentlyContinue
$FILE = $input_json.tool_input.file_path

if (-not $FILE) { exit 0 }
if ($FILE -notmatch '\.(ts|tsx|css|json|js|jsx)$') { exit 0 }

$hasConfig = (Test-Path ".prettierrc*") -or (Test-Path "prettier.config*")
if (-not $hasConfig) { exit 0 }

npx prettier --write $FILE 2>&1 | Out-Null
