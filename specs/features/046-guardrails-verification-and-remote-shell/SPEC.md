# Feature Spec: git-guardrails — verification gate for PRs and a read-only remote-shell classifier

## Status

Draft

## Problem

Measured on one user's machine (182 sessions, 2026-07 → 2026-11):

1. **PRs and merges with failing tests.** Nothing deterministic stands between "tests red" and
   `gh pr create` / `gh pr merge`. A release broke because Playwright was skipped; a commit landed
   with two failing unit tests because the shell chain did not stop. Private repos on GitHub's free
   plan cannot enforce required checks, so the local hook is the only gate.
2. **Production shells run unattended.** 2 390 `ssh`/`scp` calls as `root` to a production host
   were auto-approved by broad allow rules (`Bash(ssh *)`). About 30 % were writes (`cat > file`,
   `docker run`, config `cp`, SQL against the production database). Replacing the broad rule with
   prefix rules would have kept only ~10 % of the legitimate read-only calls prompt-free.
3. **The installed hook is ahead of this repo.** The user's installed `git-guardrails` (push only as
   `git push [-u] origin <branch>`, no force/delete/refspec) was edited locally and never upstreamed;
   reinstalling from here would regress it to "block every push".

## Goal

- `gh pr create|ready|merge` cannot proceed unless the exact content being shipped was verified at
  the level the change needs; merging always asks the owner.
- `ssh` with a read-only remote command runs without a prompt; anything else asks.
- This repo carries the installed (stricter) push rules.

## Also in this change

- Six hooks whose message was meant for the model (`scope-keeper-reminder`, `graphify-scan-reminder`,
  `graphify-stale-reminder`, `project-init-check`, `java-build-test-guard`, `spring-config-guard`) emitted
  only `systemMessage`, which the docs define as shown to the **user**. They now also emit
  `hookSpecificOutput.additionalContext` (what reaches the model); `sdd-status-banner` stays user-only.
- `ts-check` is no longer wired by default: a whole-project `tsc` per `.ts` edit (~3 s measured) whose
  stdout (exit 0, `PostToolUse`) never reaches the model; type-checking belongs in `verify`/pre-push/CI.
- `spec-create` reserves the number atomically across `origin`, branches, worktrees and claims (was:
  `max(local folder)+1`, via a PowerShell-only command), with abandoned-claim handling and documented
  cross-machine limits.

## Non-goals

- Running tests inside the hook (it only reads a stamp the project's own `verify` writes).
- Writing any project's `verify` script (per-project change).
- Removing broad allow rules from any project's settings (owner decision, separate).
- A shell parser: the classifier is a conservative allowlist — when in doubt it asks.
- Fixing the pre-existing case-insensitive `-match` in the `.ps1` dangerous-pattern loop
  (`git branch -d` is blocked by the .ps1 but not by the .sh) — reported, not changed here.

## Users / Actors

Claude Code sessions (and subagents — settings hooks fire inside them) in repos that wire
`git-guardrails`; the owner, who answers the `ask` prompts.

## Functional requirements

- FR-001: block `--no-verify` anywhere and `git commit -n` (as a flag, not inside a message).
- FR-002: opt-in gate per clone (`git config sdd.verifyGate true`; a `verify` script alone does not opt in — chat-widget's `verify` writes no stamp and would have every PR blocked): the stamp file
  `$(git rev-parse --git-dir)/sdd-verified` holds `<tree-sha> <unit|full>`.
- FR-003: `gh pr create|ready`: block on dirty tree, missing stamp, stamp tree ≠ `HEAD^{tree}`, or
  stamp level below the required one.
- FR-004: required level is `full` unless every path changed since `merge-base(HEAD, origin/main)` is
  under `docs/`, `specs/`, a `.md` file, or a test outside `tests/browser|e2e/` (then `unit`).
- FR-005: `gh pr merge [<pr>]`: resolve the PR head with `gh pr view`, check its tree with FR-003/004
  (block on failure or if unresolvable), then `ask`. Without a `verify` script: `ask`.
- FR-006: each `ssh <dest> <cmd>` invocation is judged on its own: `allow` iff all are read-only and the
  local part before the first `ssh` is read-only; `ask` on a recognised write, mutating SQL, script run,
  secret pattern (minus `SDD_SSH_NONSECRET_FILES`) or hidden stdin into a non-read-only command;
  otherwise no decision (permission rules apply). No remote command → no decision.
- FR-009: subagents (`agent_id` in the payload) cannot commit, push, rebase, tag or create/merge PRs.
- FR-007: `scp`/`rsync` with a remote side → `ask`.
- FR-008: identical behaviour in `.sh` and `.ps1`, proven by one suite run against both.

## Non-functional requirements

- Performance: no network except `gh pr view` on `gh pr merge`; ~0.1 s (.sh) / ~0.4 s (.ps1) per call.
- Security: fail closed to a human (`ask`/block), never open. Reasons never echo secrets.
- Maintainability: one hook, one suite (`scripts/git-guardrails.test.sh`), wired in CI.

## Edge cases

- `gh pr merge` for a head not fetched locally → block with "fetch it first".
- Stamp written on a dirty tree would describe content that is not `HEAD^{tree}`: the contract
  requires `verify` to stamp only on a clean tree (documented in `hooks/README.md`).
- SQL with parentheses (`count(*)`), quoted remote commands, `for … do … done` loops, `bash -s`
  heredocs: covered by the suite.
- Words like `created_at`/`updated_at` do not trigger the mutating-SQL scan (whole-word match).

## Acceptance criteria

- AC-001: `bash scripts/git-guardrails.test.sh` and `HOOK_IMPL=ps1 bash scripts/git-guardrails.test.sh`
  both pass (69/69 each at time of writing).
- AC-002: replayed against the 2 478 historical production `ssh`/`scp` tool calls, **0** calls that match
  the write patterns are allowed, and none of them is left without a decision unless its only write is
  in the local part (governed by the permission rules); the allow/ask/none shares are reported.
- AC-003: `check-consistency.sh`, `install.test.sh` (AC-02 force-push block) and
  `mindset-hook.test.sh` stay green.
- AC-004: a PR whose tree changed after `verify` is blocked; a docs-only change with a `unit` stamp
  passes; a browser-test change with a `unit` stamp is blocked.

## Test scenarios

- Unit/behaviour: `scripts/git-guardrails.test.sh` (sh + ps1).
- Replay: historical command corpus (outside the repo — it contains host names).
- Manual: one real `gh pr create` in a repo with a `verify` script, after install.

## Assumptions

- `origin/main` is the integration branch; repos using another name get `full` required (safe side).
- Settings-file hooks fire for subagents too (documented), so the gate covers them.

## Open questions

- Q-001: should repos without a `verify` script also block `gh pr create`? (Now: not gated.)

## Contracted services

Contracted services not declared → all billable add-ons treated as NOT contracted (conservative
default). Run `/project-init` to declare them.
