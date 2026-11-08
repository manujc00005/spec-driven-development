$input_json = $input | Out-String | ConvertFrom-Json -ErrorAction SilentlyContinue
$COMMAND = $input_json.tool_input.command

if (-not $COMMAND) { exit 0 }

function Block($reason) {
    Write-Error "BLOCKED: '$COMMAND' $reason. The user has prevented you from doing this."
    exit 2
}

$dangerousPatterns = @(
    "git reset --hard",
    "git clean -fd",
    "git clean -f",
    "git branch -D",
    "git checkout \.",
    "git restore \.",
    "push .*--force",
    "push .*--mirror",
    "push .*--delete",
    "push (.* )?-f( |$)",
    "push (.* )?-d( |$)",
    "push .* \+",
    "push .* :",
    "reset --hard",
    # Skipping the repo's own git hooks skips its gates (pre-commit / pre-push).
    "--no-verify",
    "git( -C [^ ]+)? commit( -[a-zA-Z]+)* -[a-zA-Z]*n[a-zA-Z]*( |$)"
)

foreach ($pattern in $dangerousPatterns) {
    if ($COMMAND -match $pattern) {
        Block "matches dangerous pattern '$pattern'"
    }
}

# Push only to a named feature branch: `git push [-u|--set-upstream] origin <branch>`.
# Never main/master, never a bare `git push`, never force/delete/refspec tricks.
if ($COMMAND -match "git( -C [^ ]+)? push") {
    foreach ($m in [regex]::Matches($COMMAND, "git( -C [^ ]+)? push[^;&|]*")) {
        $push = $m.Value.TrimEnd()
        if ($push -notmatch "^git( -C [^ ]+)? push( -u| --set-upstream)? origin [A-Za-z0-9._/-]+$") {
            Block "is not of the form 'git push [-u] origin <branch>'"
        }
        $branch = ($push -split " ")[-1]
        if (@("main", "master", "HEAD") -contains $branch) {
            Block "pushes to protected branch '$branch'"
        }
    }
}

# Subagents never publish: commit/push/PR/merge belong to the main session.
# Settings hooks also fire inside subagents, whose payload carries agent_id.
if ($input_json.agent_id -and $COMMAND -cmatch '(^|[;&|( ])(git( -C [^ ]+)? (commit|push|merge|rebase|tag)|gh pr (create|merge|ready))( |$)') {
    Block "runs inside a subagent; commit, push and PRs belong to the main session"
}

# Asks the user instead of blocking. Exit 0 with a PreToolUse permission decision.
function Decide($decision, $reason) {
    @{ hookSpecificOutput = @{ hookEventName = "PreToolUse"; permissionDecision = $decision; permissionDecisionReason = $reason } } |
        ConvertTo-Json -Compress -Depth 3 | Write-Output
    exit 0
}

function Invoke-GitQuiet([string[]]$GitArgs) {
    $out = & git @GitArgs 2>$null
    if ($LASTEXITCODE -ne 0) { return $null }
    return ($out -join "`n").Trim()
}

# --- PR / merge verification gate (same contract as git-guardrails.sh) --------
$SafeForUnit = '^(docs/|specs/)|\.md$|^tests/'
$BrowserTests = '^tests/(browser|e2e)/'

function Test-Stamp([string]$tree) {
    $gitDir = Invoke-GitQuiet @("rev-parse", "--git-dir")
    $stampFile = if ($gitDir) { Join-Path $gitDir "sdd-verified" } else { "" }
    if (-not $stampFile -or -not (Test-Path $stampFile)) { return "no verification stamp: run 'npm run verify' on a clean tree first" }
    $parts = ((Get-Content $stampFile -TotalCount 1) -split '\s+')
    $stampTree = $parts[0]; $stampLevel = if ($parts.Count -gt 1) { $parts[1] } else { "" }
    if ($stampTree -cne $tree) {
        $st = if ($stampTree.Length -ge 12) { $stampTree.Substring(0, 12) } else { $stampTree }
        $tt = if ($tree.Length -ge 12) { $tree.Substring(0, 12) } else { $tree }
        return "the verified content (tree $st) is not what is being shipped (tree $tt): re-run 'npm run verify'"
    }
    $base = Invoke-GitQuiet @("merge-base", "HEAD", "origin/main")
    $need = "full"
    if ($base) {
        $changed = @((Invoke-GitQuiet @("diff", "--name-only", $base, "HEAD")) -split "`n" | Where-Object { $_ })
        if ($changed.Count -gt 0 -and
            -not ($changed | Where-Object { $_ -cnotmatch $SafeForUnit }) -and
            -not ($changed | Where-Object { $_ -cmatch $BrowserTests })) { $need = "unit" }
    }
    if ($need -eq "full" -and $stampLevel -cne "full") {
        return "the change touches more than docs/specs/unit tests, so it needs the full verification (with E2E); the stamp says '$stampLevel'"
    }
    return $null
}

if ($COMMAND -cmatch '(^|[;&|(] *)gh pr (create|ready|merge)( |$)') {
    if ($input_json.cwd) { Set-Location -LiteralPath $input_json.cwd -ErrorAction SilentlyContinue }
    # Opt-in per clone: `git config sdd.verifyGate true` (shared by its worktrees).
    if ((Invoke-GitQuiet @("config", "--get", "sdd.verifyGate")) -ceq "true") {
        if ($COMMAND -cmatch 'gh pr merge') {
            $prArg = $null
            if ($COMMAND -cmatch 'gh pr merge +([^-;&| ][^;&| ]*)') { $prArg = $Matches[1] }
            $ghArgs = @("pr", "view") + $(if ($prArg) { @($prArg) } else { @() }) + @("--json", "headRefOid", "-q", ".headRefOid")
            $headOid = (& gh @ghArgs 2>$null | Out-String).Trim()
            $tree = if ($headOid) { Invoke-GitQuiet @("rev-parse", "$headOid^{tree}") } else { $null }
            if (-not $tree) { Block "cannot resolve the PR head locally to check its verification (fetch it first)" }
            $why = Test-Stamp $tree
            if ($why) { Block $why }
            Decide "ask" "Merge requested. The PR head (tree $($tree.Substring(0,12))) has a valid verification stamp. Merging needs the owner's explicit authorization."
        }
        if (Invoke-GitQuiet @("status", "--porcelain")) { Block "has uncommitted or untracked changes: the PR would not contain what was verified" }
        $why = Test-Stamp (Invoke-GitQuiet @("rev-parse", "HEAD^{tree}"))
        if ($why) { Block $why }
    } elseif ($COMMAND -cmatch 'gh pr merge') {
        Decide "ask" "Merge requested. This repository has no verification gate (git config sdd.verifyGate), so nothing proves the PR head was verified. Merging needs the owner's explicit authorization."
    }
}

# --- Remote shells (ssh): read-only runs, anything else asks ------------------
$RoSimple = @("cat","head","tail","grep","egrep","zgrep","ls","wc","stat","date","echo","printf","df","du","free","uptime","whoami","hostname","id","pgrep","ps","test","[","true","false","awk","sort","uniq","cut","tr","jq","column","nl","basename","dirname","readlink","realpath","which","type","file","md5sum","sha256sum","sha1sum","sleep","cd","set","journalctl","ss","netstat","lsof","dig","host","nslookup","ping","openssl")
$SecretRe = '(^|[ /])(env|printenv)([ "'']|$)|\.env([ "'']|$)|[./]env[a-z]*[ "'']?$|/etc/[^ ]*\.env|secret|id_(rsa|ed25519|ecdsa)|\.pem( |$)|credentials'
$MutatingSqlRe = '(?i)\b(insert|update|delete|alter|drop|create|truncate|grant|revoke|vacuum|reindex|copy|refresh|cluster|call|merge|pg_terminate_backend|pg_cancel_backend|setval|nextval|pg_reload_conf|pg_rotate_logfile|pg_switch_wal|pg_promote|lo_unlink|lo_import|lo_export|dblink|dblink_exec|set_config|pg_advisory_lock|pg_drop_replication_slot|pg_create_restore_point)\b'

function Test-RoLine([string]$line) {
    $line = $line -replace '^\s*', ''
    $line = $line -creplace '^(then|else|do|elif|if|while|until|!)\s+', ''
    $line = $line -creplace '^sudo\s+', ''
    while ($line -cmatch '^[A-Za-z_][A-Za-z0-9_]*=[^ ]*( |$)') { $line = $line -creplace '^[A-Za-z_][A-Za-z0-9_]*=[^ ]*\s*', '' }
    $line = ($line -replace '^["''( ]+', '') -replace '["'') ]+$', ''
    if (-not $line) { return $true }
    if ($line -cmatch '^(fi|done|esac|then|else|do|[A-Z_]+|\}|\{)$') { return $true }
    if ($line -cmatch '^for [A-Za-z_]+ in ') { return $true }
    $w1 = ($line -split ' ', 2)[0]
    $rest = if ($line.Length -gt $w1.Length) { $line.Substring($w1.Length) } else { "" }
    $w2 = (($rest.Trim()) -split '\s+', 2)[0]
    if ($RoSimple -ccontains $w1) {
        if ($w1 -ceq "set" -and $rest -cnotmatch '^ *-[euxo]+( pipefail)?( |$)|^ *\+[a-z]+') { return $false }
        # read-looking commands that can change the system or write a file:
        if ($w1 -ceq "date" -and $rest -cmatch '(^| )(-s|--set)( |=|$)') { return $false }
        if ($w1 -ceq "hostname" -and $rest -cnotmatch '^ *(-[fIisdA]+ *)*$') { return $false }
        if ($w1 -ceq "sort" -and $rest -cmatch '(^| )(-o|--output)( |=|$)') { return $false }
        if ($w1 -ceq "uniq" -and @(($rest.Trim() -split '\s+') | Where-Object { $_ -and $_ -notmatch '^-' }).Count -gt 1) { return $false }
        return $true
    }
    switch -CaseSensitive ($w1) {
        "sed" { return ($rest -cnotmatch '(^| )-i' -and $rest -cnotmatch "(^|[;{}'`" ])w +[^ ]") }
        "find" { return ($rest -cnotmatch '-(delete|exec|execdir|ok|fprint)') }
        { $_ -ceq "bash" -or $_ -ceq "sh" } {
            # -c '<script>': the script is in the text and gets judged line by line.
            if ($rest -cmatch '^( +-[a-z]+)* +-c ') { return $true }
            # reading a script from stdin: only if that script is a heredoc we can see
            return ($script:HeredocSeen -and $rest -cmatch '^( +-[a-z]+| +-o +pipefail)* *$')
        }
        "crontab" { return ($w2 -ceq "-l") }
        "systemctl" { return (@("status","is-active","is-enabled","is-failed","list-units","list-timers","show","cat") -ccontains $w2) }
        "git" {
            $r = $rest -creplace '^ *-C +[^ ]+', ''
            $g2 = (($r.Trim()) -split '\s+', 2)[0]
            return (@("log","status","rev-parse","show","diff","branch","describe","ls-files","ls-remote","remote","tag") -ccontains $g2)
        }
        "curl" {
            if ($rest -cmatch '(^| )(-X|--request|-d|--data[a-z-]*|-F|--form|-T|--upload-file|-K|--config)( |=|$)') { return $false }
            if ($rest -cmatch '(^| )-o +[^/ ]|(^| )-o +/[^d]|(^| )-O( |$)') { return $false }
            # A GET can have effects too: only health/status-style endpoints on loopback count as reads.
            return ($rest -cmatch 'https?://(127\.0\.0\.1|localhost|\[::1\])(:[0-9]+)?/(api/)?(health|healthz|status|ready|readyz|livez|ping|version|metrics)([/?"'' ]|$)')
        }
        "docker" {
            if (@("ps","logs","inspect","images","stats","top","port","version","info") -ccontains $w2) { return $true }
            if ($w2 -ceq "compose") {
                $c3 = (($rest.Trim()) -split '\s+')[1]
                return (@("ps","logs","config","images","ls") -ccontains $c3)
            }
            if ($w2 -ceq "exec") {
                $r = $rest -creplace '^ *exec', ''
                $r = $r -creplace '^( +-[a-zA-Z]+( +-e +[^ ]+)?)*', ''
                $r = $r -creplace '^( +(-e|--env|-u|--user|-w|--workdir) +[^ ]+)*', ''
                $r = ($r -creplace '^ +[^ ]+', '').TrimStart()
                if (($r -split ' ', 2)[0] -ceq "psql") { return (($r -cmatch '(^| )(-c|--command)( |=)' -or $script:HeredocSeen) -and $r -cnotmatch '(^| )(-f|--file)( |=)') }
                return (Test-RoLine $r)
            }
            return $false
        }
        "psql" { return (($rest -cmatch '(^| )(-c|--command)( |=)' -or $script:HeredocSeen) -and $rest -cnotmatch '(^| )(-f|--file)( |=)') }
    }
    return $false
}

# Positive signs of a write, a script run or a secret: these ASK. Anything that
# is neither recognised read-only nor matches here gets no decision from this
# hook (the user's permission rules apply), so unknown commands add no prompt.
$WriteRe = '(^|[;&|( \t"''])(rm|mv|cp|chmod|chown|mkdir|touch|ln|kill|pkill|killall|reboot|shutdown|tee|dd|truncate|install|scp|rsync|systemd-run|nohup|setsid)[ \t]|(^|[;&|( \t])sed[ \t]+(-[a-zA-Z]*i|--in-place)|docker[ \t]+(run|start|stop|restart|rm|kill|pull|build|push|cp|update|system|volume|network|compose[ \t]+[^;&|]*(up|down|restart|rm|pull|build|stop|start))|docker[ \t]+exec[^;&|]*[ \t](sh|bash)[ \t]+-c|systemctl[ \t]+(start|stop|restart|reload|enable|disable|mask|unmask|daemon-reload)|git([ \t]+-C[ \t]+[^ ]+)?[ \t]+(pull|checkout|reset|merge|commit|push|fetch|clean|worktree|stash|rebase|switch|restore|apply|am|cherry-pick)|(npm|pnpm|yarn)[ \t]+(install|ci|run|exec|i)[ \t]|(^|[;&|( \t])npx[ \t]|(tsx|node|python3?|ruby|perl)[ \t]+[^ ;&|]+\.(ts|js|mjs|cjs|py|rb|pl)|(^|[;&|( \t"''])(\./|/|[A-Za-z0-9_.-]+/)[A-Za-z0-9_./-]*\.sh([ \t"'';]|$)|/usr/local/bin/|crontab[ \t]+(-e|-r|[^-l ])|curl[^;&|]*[ \t](-X[ \t]*(POST|PUT|PATCH|DELETE)|--request|-d|--data[a-z-]*|-F|--form|-T|--upload-file)([ \t=]|$)|psql[^;&|]*[ \t](-f|--file)([ \t=]|$)|(^|[;&|( \t])(\.|source)[ \t]+[^ ]'

# Exact paths the user declared non-secret, space-separated in SDD_SSH_NONSECRET_FILES.
# They are removed only before the SECRET check; write checks still apply.
function Remove-NonSecret([string]$text) {
    foreach ($f in (($env:SDD_SSH_NONSECRET_FILES) -split '\s+' | Where-Object { $_ })) { $text = $text.Replace($f, "DECLARED_FILE") }
    return $text
}

function Test-RemoteSignalsWrite([string]$text) {
    $noSql = ($text -replace '(-c|--command)( +|=)\\?"[^"]*\\?"', '') -replace "(-c|--command)( +|=)'[^']*'", ''
    $noNullRedir = ($noSql -replace '[0-9]*>&[0-9-]+', '') -replace '[0-9&]*>>? */dev/null', ''
    if ($noNullRedir.Contains('>')) { return $true }
    if ((Remove-NonSecret $text) -match $SecretRe) { return $true }
    if ($text -match $MutatingSqlRe) { return $true }
    foreach ($l in ($text -split "`n")) { if ($l -cmatch $WriteRe) { return $true } }
    return $false
}

function Test-RemoteReadOnly([string]$text) {
    # (SQL passed with psql -c is not a redirection; it is still scanned for mutating keywords.)
    $noSql = ($text -replace '(-c|--command)( +|=)\\?"[^"]*\\?"', '') -replace "(-c|--command)( +|=)'[^']*'", ''
    $noNullRedir = ($noSql -replace '[0-9]*>&[0-9-]+', '') -replace '[0-9&]*>>? */dev/null', ''
    if ($noNullRedir.Contains('>')) { return $false }
    if ($text -cmatch '(^|[^-])\btee\b') { return $false }
    if ((Remove-NonSecret $text) -match $SecretRe) { return $false }
    if ($text -match $MutatingSqlRe) { return $false }
    # A heredoc fed to psql is SQL, not shell: drop its body from the per-command
    # check (it was already scanned for mutating keywords above).
    $pm = [regex]::Match($text, "psql[^<]*<<-?['""]?([A-Za-z_]+)")
    if ($pm.Success) {
        $term = $pm.Groups[1].Value; $kept = @(); $skip = $false
        foreach ($ln in ($text -split "`n")) {
            if ($skip) { if ($ln -match "^[ \t]*$([regex]::Escape($term))[ \t]*$") { $skip = $false }; continue }
            $kept += $ln
            if ($ln -cmatch 'psql[^<]*<<') { $skip = $true }
        }
        $text = $kept -join "`n"
    }
    $script:HeredocSeen = $text -match "<<-?['""]?[A-Za-z_]+"
    $text = $text -replace "<<-?['""]?[A-Za-z_]+['""]?", ''
    $split = (($text -replace '\$\(', "`n") -replace '`', "`n") -replace '&&|\|\||;|\|', "`n"
    foreach ($l in ($split -split "`n")) { if (-not (Test-RoLine $l)) { return $false } }
    return $true
}

if ($COMMAND -cmatch '(^|[;&|(] *)(scp|rsync) ' -and $COMMAND -cmatch '(scp|rsync) .*[A-Za-z0-9._-]+@[A-Za-z0-9._-]+:') {
    Decide "ask" "Copies files to or from a remote host (scp/rsync): confirm it."
}
# Every ssh invocation in the tool call is judged on its own: its remote text
# runs up to the next ssh invocation (heredocs that follow it included).
$sshMatches = [regex]::Matches($COMMAND, '(^|[;&|(\n][ \t]*)ssh[ \t]+')
if ($sshMatches.Count -gt 0) {
    $anyRemote = $false; $unknown = $false
    $withValue = @("-o","-i","-p","-l","-F","-J","-L","-R","-D","-E","-W","-b","-c","-m","-S","-w","-B","-e","-Q")
    for ($k = 0; $k -lt $sshMatches.Count; $k++) {
        $start = $sshMatches[$k].Index + $sshMatches[$k].Length
        $stop = if ($k + 1 -lt $sshMatches.Count) { $sshMatches[$k + 1].Index } else { $COMMAND.Length }
        $tokens = @($COMMAND.Substring($start, $stop - $start) -split '[ \t]+')
        $i = 0
        while ($i -lt $tokens.Count -and $tokens[$i].StartsWith("-")) { $opt = $tokens[$i]; $i++; if ($withValue -ccontains $opt) { $i++ } }
        if ($i -ge $tokens.Count) { continue }
        $i++  # destination
        $remote = if ($i -lt $tokens.Count) { ($tokens[$i..($tokens.Count - 1)] -join " ") -replace '^["'']', '' } else { "" }
        if (-not $remote.Trim()) { continue }
        $anyRemote = $true
        if (Test-RemoteReadOnly $remote) { continue }
        if (Test-RemoteSignalsWrite $remote) { Decide "ask" "Remote command may change state on the server, run a script, or print secrets: confirm it." }
        # Something is piped into ssh: what the remote side reads from stdin is not
        # visible here, so a non-read-only remote command asks.
        if ($COMMAND -match '\|\s*ssh\s' -or $remote -match '(^|[^<0-9])<\s*[^<( \t]') { Decide "ask" "Input is piped or redirected into a remote command whose effect cannot be checked: confirm it." }
        $unknown = $true
    }
    if ($anyRemote -and -not $unknown) {
        # A hook "allow" approves the WHOLE tool call: only when the local part
        # before the first ssh is read-only too; otherwise leave it to the rules.
        $prefix = $COMMAND.Substring(0, $sshMatches[0].Index)
        if (-not $prefix.Trim() -or (Test-RemoteReadOnly $prefix)) { Decide "allow" "Remote command is read-only (git-guardrails ssh classifier)." }
        exit 0
    }
}

exit 0
