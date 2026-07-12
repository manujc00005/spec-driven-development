# spring-config-guard.ps1 — Reminder hook (never blocks, never modifies files).
# After editing application*.yml or application*.properties, warns on:
# - Plaintext secrets in non-local profiles (reports FILE:LINE + key name only —
#   the matched value itself is NEVER printed, even in the systemMessage)
# - Actuator exposure in non-local profiles
# - debug=true in non-local profiles
# Exit 0 always.

$input_json = $input | Out-String | ConvertFrom-Json -ErrorAction SilentlyContinue
$FILE = $input_json.tool_input.file_path

if (-not $FILE) { exit 0 }
if ($FILE -notmatch 'application.*\.(yml|yaml|properties)$') { exit 0 }

# Skip local profile files — they're expected to have dev secrets
if ($FILE -match 'application-local\.|application-dev\.') { exit 0 }

if (-not (Test-Path $FILE)) { exit 0 }

$warnings = @()
$lines = Get-Content $FILE -ErrorAction SilentlyContinue

if ($lines) {
    # --- Plaintext secret scan: report file/line/key only, never the value ---
    $secretHits = @()
    for ($i = 0; $i -lt $lines.Count; $i++) {
        $line = $lines[$i]
        if ($line -match '(?i)^\s*([\w.\-]*(?:password|secret|token|api[_-]?key)[\w.\-]*)\s*[:=]\s*(\S.*)$') {
            $key = $Matches[1]
            $val = $Matches[2]
            # Already externalized (env var / placeholder ref) — not a leak.
            if ($val -notmatch '^\$\{') {
                $secretHits += "$($FILE):$($i + 1) key='$key'"
            }
        }
    }
    if ($secretHits.Count -gt 0) {
        $shown = $secretHits | Select-Object -First 5
        $extra = ""
        if ($secretHits.Count -gt 5) { $extra = " (+$($secretHits.Count - 5) more)" }
        $warnings += "Possible plaintext secret(s)  - value redacted, never printed  - at: $($shown -join '; ')$extra. Use Vault, env vars, or Spring Cloud Config for non-local profiles."
    }

    $content = ($lines -join "`n")

    # Check for actuator full exposure
    if ($content -match 'exposure\.include\s*[:=]\s*\*') {
        $warnings += "Actuator endpoints fully exposed (include=*). Restrict to health,info,prometheus in non-local profiles."
    }

    # Check for debug mode
    if ($content -match '(?m)^debug\s*[:=]\s*true') {
        $warnings += "debug=true detected in a non-local profile. This exposes auto-configuration reports."
    }
}

if ($warnings.Count -gt 0) {
    $msg = "[Spring Config] " + ($warnings -join " | ")
    # Build JSON via ConvertTo-Json (not string interpolation) so file paths
    # with backslashes/quotes can never produce malformed or injected JSON.
    $payload = @{ systemMessage = $msg } | ConvertTo-Json -Compress
    Write-Output $payload
}

exit 0
