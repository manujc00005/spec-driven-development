#!/usr/bin/env bash
# git-guardrails behaviour suite. Runs the same cases against the .sh hook and,
# with HOOK_IMPL=ps1, against the .ps1 twin (CONTRIBUTING rule 2: parity).
#   bash scripts/git-guardrails.test.sh
#   HOOK_IMPL=ps1 bash scripts/git-guardrails.test.sh
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMPL="${HOOK_IMPL:-sh}"
PASS=0; FAIL=0

run_hook() { # $1 = command, $2 = cwd, [$3 = agent_id] → prints block|allow|ask|none
  local payload out rc
  payload="$(python3 -I -c 'import json,sys; d={"session_id":"t","hook_event_name":"PreToolUse","tool_name":"Bash","cwd":sys.argv[2],"tool_input":{"command":sys.argv[1]}}
if sys.argv[3]: d["agent_id"]=sys.argv[3]
print(json.dumps(d))' "$1" "$2" "${3:-}")"
  if [ "$IMPL" = ps1 ]; then
    out="$(printf '%s' "$payload" | (cd "$2" && PATH="$STUBS:$PATH" perl -e 'alarm 30; exec @ARGV' pwsh -NoProfile -File "$ROOT/hooks/git-guardrails.ps1") 2>/dev/null)"; rc=$?
  else
    out="$(printf '%s' "$payload" | (cd "$2" && PATH="$STUBS:$PATH" bash "$ROOT/hooks/git-guardrails.sh") 2>/dev/null)"; rc=$?
  fi
  if [ "$rc" = 2 ]; then echo block
  elif echo "$out" | grep -q '"permissionDecision":"allow"'; then echo allow
  elif echo "$out" | grep -q '"permissionDecision":"ask"'; then echo ask
  elif [ "$rc" = 0 ]; then echo none
  else echo "error($rc)"; fi
}

expect() { # $1 = expected, $2 = label, $3 = command, [$4 = cwd], [$5 = agent_id]
  local got; got="$(run_hook "$3" "${4:-$TMP}" "${5:-}")"
  if [ "$got" = "$1" ]; then PASS=$((PASS + 1)); else FAIL=$((FAIL + 1)); echo "FAIL [$IMPL] $2: expected $1, got $got"; fi
}

TMP="$(mktemp -d)"; STUBS="$TMP/stubs"; mkdir -p "$STUBS"
trap 'rm -rf "$TMP"' EXIT

# --- existing behaviour (regression) ---
expect block "force push" "git push --force origin feat/x"
expect none  "push to a feature branch" "git push -u origin feat/x"
expect block "push to main" "git push origin main"
expect block "reset --hard" "git reset --hard HEAD~1"

# --- subagents never publish ---
expect block "subagent commit" "git commit -m 'x'" "$TMP" "agent-1"
expect block "subagent push" "git push -u origin feat/x" "$TMP" "agent-1"
expect block "subagent PR" "gh pr create --fill" "$TMP" "agent-1"
expect none  "subagent reads git" "git status && git log --oneline -3" "$TMP" "agent-1"
expect none  "main session commit" "git commit -m 'x'"

# --- verification bypass ---
expect block "commit --no-verify" "git commit --no-verify -m 'x'"
expect block "commit -n" "git commit -n -m 'x'"
expect block "push --no-verify" "git push --no-verify origin feat/x"
expect none  "-n inside a commit message" "git commit -m 'add the -n flag'"

# --- ssh: read-only allowed (shapes taken from real history) ---
H="root@203.0.113.7"
expect allow "docker ps" "ssh $H 'docker ps --filter name=app --format \"{{.Image}}\"'"
expect allow "docker logs piped" "ssh -o ConnectTimeout=15 $H \"docker logs --since 24h caddy 2>&1 | tail -12\""
expect allow "psql select" "ssh $H 'docker exec leadplatform-postgres psql -U postgres -d platform -At -c \"select t.slug, count(*) from tenants t group by 1\"'"
expect allow "deployed marker" "ssh $H 'cat /etc/lead-platform/deployed'"
expect allow "health curl" "ssh $H 'curl -s -o /dev/null -w \"health %{http_code}\" http://127.0.0.1:3000/api/health'"
expect allow "loop over containers" "ssh $H 'for c in app worker; do docker inspect \$c --format x; done'"
expect allow "bash -s heredoc, reads only" "ssh $H 'bash -s' <<'EOF'
cat /etc/lead-platform/deployed
docker ps
EOF"
expect allow "git log on server" "ssh $H 'git -C /opt/lead-platform log --oneline -3'"
expect allow "crontab -l" "ssh $H 'crontab -l 2>/dev/null | grep -i backup'"
expect allow "connectivity probe" "ssh -o BatchMode=yes -o ConnectTimeout=3 $H \"echo ok\""

# --- ssh: everything else asks ---
expect ask "psql delete" "ssh $H 'docker exec pg psql -U postgres -d platform -c \"delete from leads\"'"
expect ask "psql update" "ssh $H 'docker exec pg psql -d platform -c \"UPDATE tenants SET x=1\"'"
expect ask "write by redirection" "cat <<'TS' | ssh $H 'cat > /opt/lead-platform/scripts/tmp.ts'"
expect ask "git pull" "ssh $H 'cd /opt/lead-platform && git pull'"
expect ask "docker run" "ssh $H 'docker run --rm -i --network host img'"
expect ask "restart service" "ssh $H 'systemctl restart caddy'"
expect ask "heredoc with rm" "ssh $H 'bash -s' <<'EOF'
rm -rf /tmp/wt-base
EOF"
expect ask "prints env" "ssh $H 'docker exec app env'"
expect ask "reads an env file" "ssh $H 'cat /srv/clients/agency/.env'"
expect ask "release marker without declaring it non-secret" "ssh $H 'cat /etc/lead-platform/deployed.env'"
export SDD_SSH_NONSECRET_FILES="/etc/lead-platform/deployed.env /etc/other/marker.env"
expect allow "declared non-secret file is readable" "ssh $H 'cat /etc/lead-platform/deployed.env'"
expect ask "declared file does not cover a neighbour" "ssh $H 'cat /etc/lead-platform/platform.env'"
expect ask "declared file can still not be overwritten" "ssh $H 'cp /tmp/x /etc/lead-platform/deployed.env'"
unset SDD_SSH_NONSECRET_FILES
expect ask "sources an env file" "ssh $H 'set -a; . /etc/lead-platform/backup.env; set +a; infra/backup.sh'"
expect ask "POST" "ssh $H 'curl -s -X POST http://127.0.0.1:3000/api/x'"
expect ask "operator script" "ssh $H '/usr/local/bin/lp-sync-operator-checkout.sh'"
expect ask "cp a client config" "ssh $H 'f=/opt/c.yaml; cp -p \$f \$f.bak'"
expect ask "scp" "scp report.txt $H:/tmp/"
expect none "unknown command: no decision (permission rules apply)" "ssh $H 'frobnicate --now'"
expect ask "deploy script" "ssh $H 'cd /opt/lead-platform && infra/deploy.sh'"
expect none "ssh without a remote command" "ssh -T git@github.com"
# found by replaying real history: every invocation counts, stdin we cannot see asks
expect ask "two ssh calls, the first writes" "ssh $H 'rm -rf /tmp/x'
ssh $H 'docker ps'"
expect ask "two ssh calls, the second writes" "ssh $H 'docker ps' && ssh $H 'systemctl restart caddy'"
expect allow "two ssh calls, both read" "ssh $H 'docker ps'; ssh $H 'cat /etc/lead-platform/deployed'"
expect ask "SQL piped into psql (not visible)" "cat q.sql | ssh $H 'docker exec -i pg psql -U postgres -d platform -At'"
expect ask "script piped into bash -s (not visible)" "cat deploy.sh | ssh $H 'bash -s'"
expect ask "SQL redirected from a file into psql" "ssh $H 'docker exec -i pg psql -U postgres -d platform' < c.sql"
expect ask "rm hidden behind sh -c and systemd-run" "ssh $H 'systemd-run --unit=x --on-calendar=\"2026-10-19\" /bin/sh -c \"rm -v -- /root/x.dump\"'"
expect none "remote reads, but the local part writes" "rm -f ../tmp.sql; ssh $H 'docker exec pg psql -d platform -At -c \"select 1\"'"
expect allow "local read-only prefix" "cd /repo && ssh $H 'docker ps'"
expect allow "jsonb arrow and comparison inside psql -c" "ssh $H \"docker exec pg psql -d platform -At -c \\\"select slug, settings->>'crmBackend' from tenants where id > 0\\\"\""
expect allow "psql reading a visible heredoc" "ssh $H 'docker exec -i pg psql -d platform -At' <<'SQL'
select count(*) from leads;
SQL"
expect ask "psql heredoc with a write" "ssh $H 'docker exec -i pg psql -d platform' <<'SQL'
update leads set status = 'x';
SQL"
expect ask "redirection after psql -c still counts" "ssh $H 'docker exec pg psql -At -c \"select 1\" > /tmp/out.txt'"
expect none "not ssh at all" "ls -la"

# --- PR / merge verification gate ---
R="$TMP/repo"; mkdir -p "$R"; cd "$R" || exit 1
git init -q -b main; git config user.email t@t; git config user.name t; git config sdd.verifyGate true
echo '{"scripts":{"verify":"true"}}' > package.json; mkdir -p src docs tests/browser; echo a > src/a.ts
git add -A; git commit -qm base; git update-ref refs/remotes/origin/main HEAD
git checkout -qb feat/x
stamp() { printf '%s %s\n' "$(git rev-parse 'HEAD^{tree}')" "$1" > "$(git rev-parse --git-dir)/sdd-verified"; }

echo b > src/a.ts; git commit -qam code
expect block "PR without a stamp" "gh pr create --fill" "$R"
stamp unit
expect block "code change with a unit-only stamp" "gh pr create --fill" "$R"
stamp full
expect none  "code change with a full stamp" "gh pr create --fill" "$R"
echo c > src/a.ts
expect block "dirty tree after verifying" "gh pr create --fill" "$R"
git commit -qam later
expect block "new commit after verifying (stale stamp)" "gh pr create --fill" "$R"
git checkout -q main; git checkout -qb docs/y; echo d > docs/d.md; git add -A; git commit -qm docs; stamp unit
expect none  "docs-only change with a unit stamp" "gh pr ready" "$R"
echo t > tests/browser/x.spec.ts; git add -A; git commit -qm e2e; stamp unit
expect block "browser test change needs full" "gh pr create --fill" "$R"

# merge: the PR head is what counts; gh is stubbed to return it
git checkout -q feat/x; stamp full
printf '#!/bin/sh\necho %s\n' "$(git rev-parse HEAD)" > "$STUBS/gh"; chmod +x "$STUBS/gh"
expect ask   "merge of a verified head asks the owner" "gh pr merge 12 --squash" "$R"
printf '#!/bin/sh\necho %s\n' "$(git rev-parse HEAD~1)" > "$STUBS/gh"
expect block "merge of an unverified head" "gh pr merge 12 --squash" "$R"
rm -f "$STUBS/gh"

N="$TMP/noverify"; mkdir -p "$N"; cd "$N" || exit 1; git init -q -b main
echo '{"scripts":{"verify":"npm test"}}' > package.json   # a verify script alone does not opt in
expect none "no opt-in (even with a verify script): PR not gated" "gh pr create --fill" "$N"
expect ask  "no opt-in: merge still asks" "gh pr merge 3" "$N"

echo "git-guardrails [$IMPL]: $PASS passed, $FAIL failed"
[ "$FAIL" = 0 ]
