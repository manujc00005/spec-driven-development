# Implementation Plan: windows-install-first-run-fixes

## Approach

Three independent defects in installer plumbing. No shared abstraction is worth extracting for
them, so each is fixed where it lives, with the smallest change that removes the failure mode.

The only design decision of consequence is BUG-1's ordering, and it is decided against the
request's stated preference on evidence — see D001.

## Technical plan

### BUG-1 — retry the `CLAUDE.md` link after the personal import

The requested fix was to move the personal-import block *above* the link block. Reading the two
blocks rules that out: the personal payload restores `home/agents` as well as `central/CLAUDE.md`,
and the link block copies the framework agents with `copy_file_safely` / `Copy-FileSafely`, which is
**additive — skip on differ**. Whichever runs first wins. Moving the block therefore silently flips
agent precedence from framework-first to personal-first for every agent present in both. That is a
behaviour change well outside a bugfix, on a code path the reported bug never touched.

So: relocate **only the `CLAUDE.md` link step**, as a retry.

1. Extract the link step into a function — `link_central_claude_md` (bash) /
   `Invoke-ClaudeMdLink` (PowerShell). It returns *settled* (`0` / `$true`) when the link was
   created, was already correct, or was deliberately left alone; *pending* (`1` / `$false`) **only**
   when it was skipped because `<central>/CLAUDE.md` does not exist yet.
2. Call it in its current position. When pending, print nothing and raise a flag — the "does not
   exist yet" message is deferred, because printing it now and linking successfully thirty lines
   later is a contradiction on the user's screen.
3. After the personal-import block, if the flag is up, call it once more. If it is still pending,
   *then* print the skip message.

Everything else — the already-correct no-op, the refusal to touch a real `CLAUDE.md`, dry-run
output, the `MissingShipped` exit — keeps its current behaviour and its current position.

### BUG-2a — compare against the PowerShell default

Introduce `$DefaultCentralDir = "C:\ProgramData\ClaudeConfig"` immediately after `param()`, with a
comment binding it to the parameter default, and use it in `Report-UnrefreshedProfiles`. A
regression test greps both literals out of the file and asserts they agree, so the pair cannot drift
silently. `install.sh`'s equivalent line is already correct against the bash default and is not
touched.

### BUG-2b — fallback discovery in the consumers

A five-line resolver at the top of `link-project.ps1` and `scripts/wire-hooks.ps1`:

- Candidates: the `-CentralDir` value, plus `$HOME\.claude-config` **only when `-CentralDir` was not
  passed explicitly** (`$PSBoundParameters.ContainsKey('CentralDir')`). An explicit path is an
  instruction, not a hint, and must not be second-guessed.
- First existing candidate wins; say so when it is not the first choice.
- Nothing found → warn with every candidate enumerated, then advise `install.ps1` / `-CentralDir`.
  The "Run install.ps1 first" line survives only on that branch, where it is true.

`wire-hooks.ps1` resolves a *template*, not a directory, so its candidate list is the two central
dirs plus `$RepoRoot`, and its not-found warning enumerates all three.

### BUG-3 — symlink → hardlink → copy

Inside `Invoke-ClaudeMdLink`, replace the single `try/catch` with a ladder. Each rung warns on the
way down, naming the mechanism and its exact cost:

- **hardlink** — same volume only; if the central file is later replaced by rename, the two names
  stop being one file and drift with no error.
- **copy** — a snapshot; not kept in sync; re-run the installer after editing the central file.

Because a fallback changes what a *later* run sees, the "already exists" branch learns to recognise
`LinkType -eq 'HardLink'` at the right target and report it as linked-with-caveat. Without that,
every subsequent install on a hardlinked machine would print "resolve manually" about a file the
installer itself created. Adjacent-necessary, not an improvement.

Bash is untouched: POSIX symlinks need no privilege, so there is no failure to catch (D004).

## Testing strategy

Both installers accept a `--claude-home` / `-ClaudeHome` override, so the first-install scenario is
fully hermetic — no test goes near the real `~/.claude`.

- `scripts/install.test.sh`: seed `<central>/personal/central/CLAUDE.md`, run
  `--link-user-claude --claude-home <tmp>`, assert the symlink exists and resolves to central.
- `scripts/install.test.ps1`: the same case under pwsh; a payload-free control case for AC-009; the
  `$DefaultCentralDir` drift guard; and consumer-discovery cases driving `link-project.ps1` and
  `wire-hooks.ps1` with the default absent.

BUG-3 is not reachable on macOS — symlink creation succeeds, so no rung below it executes. Recorded
as such rather than faked with a mock that would prove nothing about Windows.

## Manual Windows verification

```powershell
Remove-Item -Recurse -Force $HOME\.claude -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force $HOME\.claude-config -ErrorAction SilentlyContinue

.\install.ps1 -LinkUserClaude -CentralDir $HOME\.claude-config

Test-Path $HOME\.claude-config\CLAUDE.md
Test-Path $HOME\.claude\CLAUDE.md
Get-Item $HOME\.claude\CLAUDE.md | Format-List FullName,LinkType,Target
```

Run once **without** elevation and Developer Mode off (expect the hardlink rung and its warning),
once **with** (expect `LinkType: SymbolicLink`). Then, with central at `$HOME\.claude-config` and
`C:\ProgramData\ClaudeConfig` absent:

```powershell
.\link-project.ps1 -ProjectDir .
.\scripts\wire-hooks.ps1 -ProjectDir .
```

Both must discover the fallback instead of exiting 1.

## Rollout

Working-tree only. No commit, no push, no staging, per the request.
