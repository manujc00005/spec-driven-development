#!/usr/bin/env bash
# git-guardrails.sh — Cross-platform parity with git-guardrails.ps1
# Blocks destructive git operations in Claude Code Bash tool calls.
# Read-only: never modifies files, never makes commits.
# Exit 0 = allow, Exit 2 = block.

set -euo pipefail

source "$(dirname "${BASH_SOURCE[0]}")/lib/claude-json.sh"

# Read the tool-call JSON from stdin (Claude Code pipes it)
INPUT="$(claude_json_read_stdin)"

# Extract the command string from the tool_input.command field
COMMAND="$(claude_json_get_command "$INPUT")"

if [ -z "$COMMAND" ]; then
  exit 0
fi

block() {
  echo "BLOCKED: '$COMMAND' $1. The user has prevented you from doing this." >&2
  exit 2
}

# Dangerous patterns — same set as git-guardrails.ps1
DANGEROUS_PATTERNS=(
  "git reset --hard"
  "git clean -fd"
  "git clean -f"
  "git branch -D"
  "git checkout \."
  "git restore \."
  "push .*--force"
  "push .*--mirror"
  "push .*--delete"
  "push (.* )?-f( |$)"
  "push (.* )?-d( |$)"
  "push .* \+"
  "push .* :"
  "reset --hard"
  # Skipping the repo's own git hooks skips its gates (pre-commit / pre-push).
  "--no-verify"
  "git( -C [^ ]+)? commit( -[a-zA-Z]+)* -[a-zA-Z]*n[a-zA-Z]*( |$)"
)

for pattern in "${DANGEROUS_PATTERNS[@]}"; do
  if echo "$COMMAND" | grep -qE -- "$pattern"; then
    block "matches dangerous pattern '$pattern'"
  fi
done

# Push only to a named feature branch: `git push [-u|--set-upstream] origin <branch>`.
# Never main/master, never a bare `git push` (it pushes whatever is checked out),
# never force/delete/refspec tricks (blocked above). Merging to main stays the owner's job.
if echo "$COMMAND" | grep -qE "git( -C [^ ]+)? push"; then
  PUSHES="$(echo "$COMMAND" | grep -oE "git( -C [^ ]+)? push[^;&|]*" || true)"
  while IFS= read -r push; do
    [ -z "$push" ] && continue
    if ! echo "$push" | grep -qE "^git( -C [^ ]+)? push( -u| --set-upstream)? origin [A-Za-z0-9._/-]+ *$"; then
      block "is not of the form 'git push [-u] origin <branch>'"
    fi
    branch="$(echo "$push" | awk '{print $NF}')"
    case "$branch" in
      main|master|HEAD) block "pushes to protected branch '$branch'" ;;
    esac
  done <<< "$PUSHES"
fi

# Subagents never publish: commit/push/PR/merge belong to the main session
# (implementer.md, sdd-orchestrate). Settings hooks also fire inside subagents,
# whose payload carries agent_id.
if [ -n "$(claude_json_get_field "$INPUT" "agent_id")" ] \
  && echo "$COMMAND" | grep -qE '(^|[;&|( ])(git( -C [^ ]+)? (commit|push|merge|rebase|tag)|gh pr (create|merge|ready))( |$)'; then
  block "runs inside a subagent; commit, push and PRs belong to the main session"
fi

# Asks the user instead of blocking: the operation may be legitimate, but a
# human decides. Exit 0 with a PreToolUse permission decision.
decide() { # $1 = allow|ask, $2 = reason (shown to the model and the user)
  printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"%s","permissionDecisionReason":"%s"}}\n' \
    "$1" "$(claude_json_escape "$2")"
  exit 0
}

# --- PR / merge verification gate -------------------------------------------
# Opt-in per clone: `git config sdd.verifyGate true` (shared by its worktrees).
# The project's verify script runs its gates and, only if they pass on a CLEAN tree, writes
#   "<tree-sha> <unit|full>"  to  "$(git rev-parse --git-dir)/sdd-verified".
# The stamp names the content that was verified (the tree, not the commit): any
# later change produces another tree and the stamp no longer applies.
# Level needed: "unit" only when every changed path is docs/specs/markdown or a
# non-browser test; anything else (code, components, dependencies, config,
# migrations, i18n...) needs "full", which includes the browser E2E suite.
SAFE_FOR_UNIT_RE='^(docs/|specs/)|\.md$|^tests/'
BROWSER_TESTS_RE='^tests/(browser|e2e)/'

stamp_check() { # $1 = tree to check; prints a reason and returns 1 when not verified
  local tree="$1" stamp_file stamp_tree stamp_level base need changed
  stamp_file="$(git rev-parse --git-dir 2>/dev/null)/sdd-verified"
  if [ ! -f "$stamp_file" ]; then
    echo "no verification stamp: run 'npm run verify' on a clean tree first"; return 1
  fi
  read -r stamp_tree stamp_level < "$stamp_file" || true
  if [ "$stamp_tree" != "$tree" ]; then
    echo "the verified content (tree ${stamp_tree:0:12}) is not what is being shipped (tree ${tree:0:12}): re-run 'npm run verify'"; return 1
  fi
  base="$(git merge-base HEAD origin/main 2>/dev/null || true)"
  need=full
  if [ -n "$base" ]; then
    changed="$(git diff --name-only "$base" HEAD 2>/dev/null || true)"
    if [ -n "$changed" ] \
      && ! echo "$changed" | grep -qvE "$SAFE_FOR_UNIT_RE" \
      && ! echo "$changed" | grep -qE "$BROWSER_TESTS_RE"; then
      need=unit
    fi
  fi
  if [ "$need" = full ] && [ "$stamp_level" != full ]; then
    echo "the change touches more than docs/specs/unit tests, so it needs the full verification (with E2E); the stamp says '$stamp_level'"; return 1
  fi
  return 0
}

if echo "$COMMAND" | grep -qE '(^|[;&|(] *)gh pr (create|ready|merge)( |$)'; then
  CWD="$(claude_json_get_field "$INPUT" "cwd")"
  [ -n "$CWD" ] && cd "$CWD" 2>/dev/null || true
  if [ "$(git config --get sdd.verifyGate 2>/dev/null)" = true ]; then
    if echo "$COMMAND" | grep -qE 'gh pr merge'; then
      # What gets merged is the PR's head, not necessarily the local checkout.
      PR_ARG="$(echo "$COMMAND" | grep -oE 'gh pr merge( +[^-;&| ][^;&| ]*)?' | awk '{print $4}')"
      HEAD_OID="$(gh pr view ${PR_ARG:+"$PR_ARG"} --json headRefOid -q .headRefOid 2>/dev/null || true)"
      TREE="$( [ -n "$HEAD_OID" ] && git rev-parse "${HEAD_OID}^{tree}" 2>/dev/null || true)"
      [ -n "$TREE" ] || block "cannot resolve the PR head locally to check its verification (fetch it first)"
      WHY="$(stamp_check "$TREE")" || block "$WHY"
      # Verified — merging is still the owner's call, every time.
      decide ask "Merge requested. The PR head (tree ${TREE:0:12}) has a valid verification stamp. Merging needs the owner's explicit authorization."
    fi
    [ -z "$(git status --porcelain 2>/dev/null)" ] || block "has uncommitted or untracked changes: the PR would not contain what was verified"
    WHY="$(stamp_check "$(git rev-parse 'HEAD^{tree}' 2>/dev/null)")" || block "$WHY"
  elif echo "$COMMAND" | grep -qE 'gh pr merge'; then
    decide ask "Merge requested. This repository has no verification gate (git config sdd.verifyGate), so nothing proves the PR head was verified. Merging needs the owner's explicit authorization."
  fi
fi

# --- Remote shells (ssh): read-only runs, anything else asks ------------------
# A remote command is allowed only when every command in it is a known
# read-only one. Writes, script execution, anything that would print secrets,
# and anything this parser does not recognise ask the user. scp/rsync always ask.
RO_SIMPLE=" cat head tail grep egrep zgrep ls wc stat date echo printf df du free uptime whoami hostname id pgrep ps test [ true false awk sort uniq cut tr jq column nl basename dirname readlink realpath which type file md5sum sha256sum sha1sum sleep cd set journalctl ss netstat lsof dig host nslookup ping openssl "
SECRET_RE='(^|[ /])(env|printenv)([ "'"'"']|$)|\.env([ "'"'"']|$)|[./]env[a-z]*[ "'"'"']?$|/etc/[^ ]*\.env|secret|id_(rsa|ed25519|ecdsa)|\.pem( |$)|credentials'
MUTATING_SQL_RE='insert|update|delete|alter|drop|create|truncate|grant|revoke|vacuum|reindex|copy|refresh|cluster|call|merge'

ro_line() { # one simple command; returns 0 if read-only
  local line="$1" w1 w2 rest
  # strip leading control keywords, negation, sudo and VAR=value assignments
  line="$(echo "$line" | sed -E 's/^[[:space:]]*//; s/^(then|else|do|elif|if|while|until|!)[[:space:]]+//; s/^sudo[[:space:]]+//')"
  while echo "$line" | grep -qE '^[A-Za-z_][A-Za-z0-9_]*=[^ ]*( |$)'; do
    line="$(echo "$line" | sed -E 's/^[A-Za-z_][A-Za-z0-9_]*=[^ ]*[[:space:]]*//')"
  done
  line="$(echo "$line" | sed -E "s/^[\"'( ]+//; s/[\"') ]+\$//")"
  [ -z "$line" ] && return 0
  echo "$line" | grep -qE '^(fi|done|esac|then|else|do|for [A-Za-z_]+ in .*|[A-Z_]+|\}|\{)$' && return 0
  echo "$line" | grep -qE '^for [A-Za-z_]+ in ' && return 0
  w1="${line%% *}"; rest="${line#"$w1"}"; w2="$(echo "$rest" | awk '{print $1}')"
  case "$RO_SIMPLE" in *" $w1 "*)
    if [ "$w1" = set ]; then
      echo "$rest" | grep -qE '^ *-[euxo]+( pipefail)?( |$)|^ *\+[a-z]+' || return 1
    fi
    return 0 ;;
  esac
  case "$w1" in
    sed) echo "$rest" | grep -qE '(^| )-i' && return 1; return 0 ;;
    find) echo "$rest" | grep -qE -- '-(delete|exec|execdir|ok|fprint)' && return 1; return 0 ;;
    bash|sh)
      # -c '<script>': the script is in the text and gets judged line by line.
      echo "$rest" | grep -qE '^( +-[a-z]+)* +-c ' && return 0
      # reading a script from stdin: only if that script is a heredoc we can see
      [ "${HEREDOC_SEEN:-0}" = 1 ] && echo "$rest" | grep -qE '^( +-[a-z]+| +-o +pipefail)* *$' && return 0
      return 1 ;;
    crontab) [ "$w2" = "-l" ]; return ;;
    systemctl) case "$w2" in status|is-active|is-enabled|is-failed|list-units|list-timers|show|cat) return 0 ;; esac; return 1 ;;
    git)
      rest="$(echo "$rest" | sed -E 's/^ *-C +[^ ]+//')"; w2="$(echo "$rest" | awk '{print $1}')"
      case "$w2" in log|status|rev-parse|show|diff|branch|describe|ls-files|ls-remote|remote|tag) return 0 ;; esac; return 1 ;;
    curl)
      echo "$rest" | grep -qE -- '(^| )(-X|--request|-d|--data[a-z-]*|-F|--form|-T|--upload-file|-K|--config)( |=|$)' && return 1
      echo "$rest" | grep -qE -- '(^| )-o +[^/ ]|(^| )-o +/[^d]|(^| )-O( |$)' && return 1
      return 0 ;;
    docker)
      case "$w2" in
        ps|logs|inspect|images|stats|top|port|version|info) return 0 ;;
        compose) case "$(echo "$rest" | awk '{print $2}')" in ps|logs|config|images|ls) return 0 ;; esac; return 1 ;;
        exec)
          # docker exec [opts] <container> <cmd...>: judge the inner command.
          rest="$(echo "$rest" | sed -E 's/^ *exec//; s/^( +-[a-zA-Z]+( +-e +[^ ]+)?)*//; s/^( +(-e|--env|-u|--user|-w|--workdir) +[^ ]+)*//; s/^ +[^ ]+//')"
          rest="$(echo "$rest" | sed -E 's/^ +//')"
          case "${rest%% *}" in
            psql) { echo "$rest" | grep -qE -- '(^| )(-c|--command)( |=)' || [ "${HEREDOC_SEEN:-0}" = 1 ]; } || return 1
                  echo "$rest" | grep -qE -- '(^| )(-f|--file)( |=)' && return 1; return 0 ;;
            *) ro_line "$rest"; return ;;
          esac ;;
      esac
      return 1 ;;
    psql) { echo "$rest" | grep -qE -- '(^| )(-c|--command)( |=)' || [ "${HEREDOC_SEEN:-0}" = 1 ]; } || return 1
          echo "$rest" | grep -qE -- '(^| )(-f|--file)( |=)' && return 1; return 0 ;;
  esac
  return 1
}

# Positive signs of a write, a script run or a secret: these ASK. Anything that
# is neither recognised read-only nor matches here gets no decision from this
# hook (the user's permission rules apply), so unknown commands add no prompt.
WRITE_RE='(^|[;&|( 	"'"'"'])(rm|mv|cp|chmod|chown|mkdir|touch|ln|kill|pkill|killall|reboot|shutdown|tee|dd|truncate|install|scp|rsync|systemd-run|nohup|setsid)[ 	]|(^|[;&|( 	])sed[ 	]+(-[a-zA-Z]*i|--in-place)|docker[ 	]+(run|start|stop|restart|rm|kill|pull|build|push|cp|update|system|volume|network|compose[ 	]+[^;&|]*(up|down|restart|rm|pull|build|stop|start))|docker[ 	]+exec[^;&|]*[ 	](sh|bash)[ 	]+-c|systemctl[ 	]+(start|stop|restart|reload|enable|disable|mask|unmask|daemon-reload)|git([ 	]+-C[ 	]+[^ ]+)?[ 	]+(pull|checkout|reset|merge|commit|push|fetch|clean|worktree|stash|rebase|switch|restore|apply|am|cherry-pick)|(npm|pnpm|yarn)[ 	]+(install|ci|run|exec|i)[ 	]|(^|[;&|( 	])npx[ 	]|(tsx|node|python3?|ruby|perl)[ 	]+[^ ;&|]+\.(ts|js|mjs|cjs|py|rb|pl)|(^|[;&|( 	"'"'"'])(\./|/|[A-Za-z0-9_.-]+/)[A-Za-z0-9_./-]*\.sh([ 	"'"'"';]|$)|/usr/local/bin/|crontab[ 	]+(-e|-r|[^-l ])|curl[^;&|]*[ 	](-X[ 	]*(POST|PUT|PATCH|DELETE)|--request|-d|--data[a-z-]*|-F|--form|-T|--upload-file)([ 	=]|$)|psql[^;&|]*[ 	](-f|--file)([ 	=]|$)|(^|[;&|( 	])(\.|source)[ 	]+[^ ]'

# Exact paths the user declared non-secret (e.g. a release marker holding only a
# tag), space-separated in SDD_SSH_NONSECRET_FILES (set it in settings "env").
# They are removed only before the SECRET check; write checks still apply.
without_nonsecret() {
  local text="$1" f
  for f in ${SDD_SSH_NONSECRET_FILES:-}; do
    text="${text//"$f"/DECLARED_FILE}"
  done
  printf '%s' "$text"
}

remote_signals_write() { # $1 = remote text; 0 when it shows a write/script/secret sign
  local text="$1"
  echo "$text" | sed -E 's/(-c|--command)( +|=)\\?"[^"]*\\?"//g; s/(-c|--command)( +|=)'"'"'[^'"'"']*'"'"'//g; s/[0-9]*>&[0-9-]+//g; s/[0-9&]*>>? *\/dev\/null//g' | grep -q '>' && return 0
  without_nonsecret "$text" | grep -qEi "$SECRET_RE" && return 0
  echo "$text" | grep -qEiw "$MUTATING_SQL_RE" && return 0
  echo "$text" | grep -qE "$WRITE_RE" && return 0
  return 1
}

remote_is_read_only() { # $1 = remote command text (heredocs included)
  local text="$1" line
  # writes by redirection (2>&1 and >/dev/null are fine)
  # (SQL passed with psql -c is not a redirection: `->>`, `a > 0`. It is still
  # scanned for mutating keywords below.)
  echo "$text" | sed -E 's/(-c|--command)( +|=)\\?"[^"]*\\?"//g; s/(-c|--command)( +|=)'"'"'[^'"'"']*'"'"'//g; s/[0-9]*>&[0-9-]+//g; s/[0-9&]*>>? *\/dev\/null//g' | grep -q '>' && return 1
  echo "$text" | grep -qE '(^|[^-])\btee\b' && return 1
  without_nonsecret "$text" | grep -qEi "$SECRET_RE" && return 1
  echo "$text" | grep -qEiw "$MUTATING_SQL_RE" && return 1
  # A heredoc fed to psql is SQL, not shell: drop its body from the per-command
  # check (it was already scanned for mutating keywords above).
  if echo "$text" | grep -qE "psql[^<]*<<-?['\"]?[A-Za-z_]+"; then
    local term
    term="$(echo "$text" | grep -oE "psql[^<]*<<-?['\"]?[A-Za-z_]+" | head -1 | sed -E "s/.*<<-?['\"]?//")"
    text="$(echo "$text" | awk -v T="$term" '
      skip && $0 ~ ("^[ \t]*" T "[ \t]*$") { skip = 0; next }
      skip { next }
      { print }
      /psql[^<]*<</ { skip = 1 }')"
  fi
  HEREDOC_SEEN=0
  if echo "$text" | grep -qE "<<-?['\"]?[A-Za-z_]+"; then
    HEREDOC_SEEN=1
    text="$(echo "$text" | sed -E "s/<<-?['\"]?[A-Za-z_]+['\"]?//g")"
  fi
  while IFS= read -r line; do
    ro_line "$line" || return 1
  done < <(echo "$text" | sed -E 's/\$\(/\n/g; s/`/\n/g; s/&&|\|\||;|\|/\n/g')
  return 0
}

if echo "$COMMAND" | grep -qE '(^|[;&|(] *)(scp|rsync) '; then
  if echo "$COMMAND" | grep -qE '(scp|rsync) .*[A-Za-z0-9._-]+@[A-Za-z0-9._-]+:'; then
    decide ask "Copies files to or from a remote host (scp/rsync): confirm it."
  fi
fi
# Every ssh invocation in the tool call is judged on its own: its remote text
# runs up to the next ssh invocation (heredocs that follow it included).
SSH_SEGMENTS="$(printf '%s' "$COMMAND" | awk '
  BEGIN { RS = "\001"; re = "(^|[;&|(\n][ \t]*)ssh[ \t]+" }
  {
    s = $0; base = 0; n = 0
    while (match(s, re)) {
      n++; mstart[n] = base + RSTART; rstart[n] = base + RSTART + RLENGTH
      base += RSTART + RLENGTH - 1; s = substr(s, RSTART + RLENGTH)
    }
    for (k = 1; k <= n; k++) {
      stop = (k < n) ? mstart[k + 1] : length($0) + 1
      printf "%s\002", substr($0, rstart[k], stop - rstart[k])
    }
  }')"
# What runs locally before the first ssh. A hook "allow" approves the WHOLE tool
# call, so it is only given when this local part is read-only too.
SSH_PREFIX="$(printf '%s' "$COMMAND" | awk 'BEGIN { RS = "\001" } { if (match($0, /(^|[;&|(\n][ \t]*)ssh[ \t]+/)) printf "%s", substr($0, 1, RSTART - 1) }')"
if [ -n "$SSH_SEGMENTS" ]; then
  ANY_REMOTE=0; UNKNOWN=0
  while IFS= read -r -d $'\002' SEG; do
    # options (some take a value), then the destination, then the remote command
    REMOTE="$(printf '%s' "$SEG" | awk '
      BEGIN { RS = "\001" }
      {
        n = split($0, t, /[ \t]+/); i = 1; skip = " -o -i -p -l -F -J -L -R -D -E -W -b -c -m -S -w -B -e -Q "
        while (i <= n && t[i] ~ /^-/) { opt = t[i]; i++; if (index(skip, " " opt " ")) i++ }
        if (i > n) exit
        i++
        out = ""; for (; i <= n; i++) out = out (out == "" ? "" : " ") t[i]
        printf "%s", out
      }')"
    REMOTE="$(echo "$REMOTE" | sed -E "1s/^[\"']//")"
    [ -n "$(echo "$REMOTE" | tr -d '[:space:]')" ] || continue
    ANY_REMOTE=1
    remote_is_read_only "$REMOTE" && continue
    remote_signals_write "$REMOTE" && decide ask "Remote command may change state on the server, run a script, or print secrets: confirm it."
    # Something is piped into ssh: what the remote side reads from stdin is not
    # visible here, so a non-read-only remote command asks.
    { printf '%s' "$COMMAND" | grep -qE '\|[[:space:]]*ssh[[:space:]]' \
      || printf '%s' "$REMOTE" | grep -qE '(^|[^<0-9])<[[:space:]]*[^<( 	]'; } \
      && decide ask "Input is piped or redirected into a remote command whose effect cannot be checked: confirm it."
    UNKNOWN=1
  done <<< "$SSH_SEGMENTS"$'\002'
  if [ "$ANY_REMOTE" = 1 ] && [ "$UNKNOWN" = 0 ]; then
    if [ -z "$(echo "$SSH_PREFIX" | tr -d '[:space:]')" ] || remote_is_read_only "$SSH_PREFIX"; then
      decide allow "Remote command is read-only (git-guardrails ssh classifier)."
    fi
    exit 0  # remote part is read-only, local part is not: leave it to the permission rules
  fi
fi

exit 0
