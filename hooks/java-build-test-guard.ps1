# java-build-test-guard.ps1 — Reminder hook (never blocks, never modifies files).
# After a .java file edit:
#   - Maven is the primary build tool (mvnw / mvnw.cmd checked first).
#   - Default action is `mvnw compile` ONLY — no test suite runs unless
#     explicitly opted in via $env:SDD_JAVA_HOOK_RUN_TESTS = "1" (or "true"),
#     and even then only fast unit tests (`mvnw test -q -DskipITs`), never a
#     full `verify`/integration suite. This keeps the hook cheap by default.
#   - Gradle (gradlew / gradlew.bat) is used only as a fallback when no Maven
#     wrapper is present.
#   - No-op if neither mvnw nor gradlew is present.
# Exit 0 always.

$input_json = $input | Out-String | ConvertFrom-Json -ErrorAction SilentlyContinue
$FILE = $input_json.tool_input.file_path

if (-not $FILE) { exit 0 }
if ($FILE -notmatch '\.java$') { exit 0 }

$RunTests = $false
if ($env:SDD_JAVA_HOOK_RUN_TESTS -eq "1" -or $env:SDD_JAVA_HOOK_RUN_TESTS -eq "true") { $RunTests = $true }

function Invoke-MavenCmd([string]$MvnCmd) {
    $compileOutput = & $MvnCmd compile -q 2>&1 | Select-Object -Last 30
    if ($LASTEXITCODE -ne 0) {
        Write-Output $compileOutput
        Write-Output '{"systemMessage":"[Java Build] Maven compile failed. Fix compilation errors before proceeding."}'
        return
    }
    if ($RunTests) {
        $testOutput = & $MvnCmd test -q -DskipITs 2>&1 | Select-Object -Last 30
        if ($LASTEXITCODE -ne 0) {
            Write-Output $testOutput
            Write-Output '{"systemMessage":"[Java Build] Maven fast unit tests failed (SDD_JAVA_HOOK_RUN_TESTS opt-in). Fix failing tests before proceeding."}'
        }
    }
}

function Invoke-MavenWrapperBash {
    $compileOutput = bash -c "./mvnw compile -q" 2>&1 | Select-Object -Last 30
    if ($LASTEXITCODE -ne 0) {
        Write-Output $compileOutput
        Write-Output '{"systemMessage":"[Java Build] Maven compile failed. Fix compilation errors before proceeding."}'
        return
    }
    if ($RunTests) {
        $testOutput = bash -c "./mvnw test -q -DskipITs" 2>&1 | Select-Object -Last 30
        if ($LASTEXITCODE -ne 0) {
            Write-Output $testOutput
            Write-Output '{"systemMessage":"[Java Build] Maven fast unit tests failed (SDD_JAVA_HOOK_RUN_TESTS opt-in). Fix failing tests before proceeding."}'
        }
    }
}

# Maven-first (primary build tool) — compile only by default, no heavy suites.
if (Test-Path "mvnw.cmd") {
    Invoke-MavenCmd ".\mvnw.cmd"
    exit 0
}

if (Test-Path "mvnw") {
    Invoke-MavenWrapperBash
    exit 0
}

# Gradle fallback — only used when no Maven wrapper exists.
if (Test-Path "gradlew.bat") {
    $output = & .\gradlew.bat compileJava -q 2>&1 | Select-Object -Last 30
    if ($LASTEXITCODE -ne 0) {
        Write-Output $output
        Write-Output '{"systemMessage":"[Java Build] Gradle compile failed. Fix compilation errors before proceeding."}'
        exit 0
    }
    if ($RunTests) {
        $testOutput = & .\gradlew.bat test -q 2>&1 | Select-Object -Last 30
        if ($LASTEXITCODE -ne 0) {
            Write-Output $testOutput
            Write-Output '{"systemMessage":"[Java Build] Gradle fast test task failed (SDD_JAVA_HOOK_RUN_TESTS opt-in). Fix failing tests before proceeding."}'
        }
    }
    exit 0
}

if (Test-Path "gradlew") {
    $output = bash -c "./gradlew compileJava -q" 2>&1 | Select-Object -Last 30
    if ($LASTEXITCODE -ne 0) {
        Write-Output $output
        Write-Output '{"systemMessage":"[Java Build] Gradle compile failed. Fix compilation errors before proceeding."}'
        exit 0
    }
    if ($RunTests) {
        $testOutput = bash -c "./gradlew test -q" 2>&1 | Select-Object -Last 30
        if ($LASTEXITCODE -ne 0) {
            Write-Output $testOutput
            Write-Output '{"systemMessage":"[Java Build] Gradle fast test task failed (SDD_JAVA_HOOK_RUN_TESTS opt-in). Fix failing tests before proceeding."}'
        }
    }
    exit 0
}

# No build tool found — no-op
exit 0
