$input_json = $input | Out-String | ConvertFrom-Json -ErrorAction SilentlyContinue
$FILE = $input_json.tool_input.file_path

if (-not $FILE) { exit 0 }
if ($FILE -notmatch '\.(ts|tsx)$') { exit 0 }
if (-not (Test-Path "tsconfig.json")) { exit 0 }

npx tsc --noEmit 2>&1 | Select-Object -Last 20
