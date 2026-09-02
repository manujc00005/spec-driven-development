# Feature Spec: windows-install-first-run-fixes

## Status

Implemented

> `Implemented` 2026-08-28 — 16/16 tasks. Gates: `check-consistency.sh` exit 0,
> `check-consistency.test.sh` 42/42, `install.test.sh` 33/33, `install.test.ps1` 28/28 under
> pwsh 7.5.2 on macOS. BUG-1 was reproduced against the pre-fix installers on both platforms
> before the fix, so its regression tests are known to bite.
>
> **Not `Merged`:** BUG-3's symlink → hardlink → copy ladder cannot execute off Windows — the first
> rung always succeeds here — so it is covered structurally and by review only. Promotion waits on
> the manual Windows 11 procedure in PLAN.md, run once unprivileged and once elevated.

> Numbered **039**, not 032 as the request proposed: `specs/features/032-autonomous-loop-residual-calibration/`
> already owns that slot (closed, on `main`). A second `032-` would break the one convention the
> spec trail relies on. Nothing else about the request changed.

## Problem

A real first install on Windows 11 — central dir at `~/.claude-config`, install from commit
`2965b40` — produced a machine where **the user's global instructions never loaded**, plus two
follow-on failures that the eval suite does not reach. All three are first-run bugs: they need a
*fresh* machine, an *opt-in* `-LinkUserClaude`, and a central dir *away from the Windows default* to
appear at all. The existing installer tests run with `-SkipLink` into a hermetic temp dir, so they
are structurally blind to every one of them.

The machine that surfaced these was then patched by hand (`~/.claude/CLAUDE.md` recreated as a
hardlink, the global `scope-keeper` hook swapped from bash to PowerShell). Those patches are local
and must not be assumed anywhere else — the fix has to make a clean install produce that state on
its own.

## Bugs detected

### BUG-1 — `CLAUDE.md` is never linked on a first install (high)

Both installers link `~/.claude/CLAUDE.md` **before** they restore the personal layer:

| | link step | personal import |
|---|---|---|
| `install.ps1` | 867–889 | 1061–1072 |
| `install.sh` | 933–953 | 1128–1139 |

The repo only ships `CLAUDE.md.example`; the real `<central-dir>/CLAUDE.md` is created by the
personal import (payload entry `personal/central/CLAUDE.md`). So on a first install the order is:

1. Link step runs, finds no `<central>/CLAUDE.md`, prints `CLAUDE.md link skipped`.
2. Personal import runs and **creates** `<central>/CLAUDE.md`.
3. Nothing ever retries the link.

Result: `<central>/CLAUDE.md` exists, `~/.claude/CLAUDE.md` does not, and the user's global
instructions silently do not load. Affects bash and PowerShell equally.

### BUG-2 — `-CentralDir` discovery is broken away from the Windows default (medium)

**BUG-2a — inverted home check.** `install.ps1:1051` decides whether the suggested refresh command
needs `-CentralDir` by comparing against the **bash** default:

```powershell
if ($CentralDir -ne (Join-Path $HOME ".claude-config")) { $cmd = "$cmd -CentralDir $CentralDir" }
```

Backwards on Windows in both directions: an install at the PowerShell default
`C:\ProgramData\ClaudeConfig` gets a redundant `-CentralDir`, and an install at
`$HOME\.claude-config` **omits** it — precisely the case where the command is wrong without it.

**BUG-2b — no discovery in the consumers.** `link-project.ps1:40` and `scripts/wire-hooks.ps1:31`
default to `C:\ProgramData\ClaudeConfig` and stop there. With a valid install at
`$HOME\.claude-config`, `link-project.ps1` exits 1 with *"Run install.ps1 first"* — advice that is
simply false, and that sends the user to re-run an installer that already succeeded.

### BUG-3 — the `CLAUDE.md` symlink needs admin, and the fallback is to give up (medium)

`install.ps1:883` creates the link with `New-Item -ItemType SymbolicLink`. On corporate Windows
without Developer Mode or elevation this fails —
`Se necesitan privilegios de administrador para esta operación` — and the handler warns and moves
on. The user is left with no `~/.claude/CLAUDE.md` at all, which is the same end state as BUG-1
and indistinguishable from it in the wild. Windows offers two weaker mechanisms that need no
privilege (hardlink, copy) and neither is attempted.

## Expected behaviour

- A first install with a personal payload leaves `~/.claude/CLAUDE.md` present and pointing at
  `<central>/CLAUDE.md`, on bash and PowerShell alike.
- An unprivileged Windows install still ends with a usable `~/.claude/CLAUDE.md`, by the strongest
  mechanism available, and says out loud which one it used and what that costs.
- Suggested commands carry `-CentralDir` exactly when the install is not at the PowerShell default.
- `link-project.ps1` and `scripts/wire-hooks.ps1` find an install at `$HOME\.claude-config` when the
  default is absent, and when they find nothing they name every path they checked.

## Non-goals

- **Changing any documented default.** `install.ps1` stays on `C:\ProgramData\ClaudeConfig`;
  `install.sh` stays on `~/.claude-config`.
- **A central-dir pointer file** (`~/.claude/.sdd-central`). The simple fallback covers the observed
  failure; a new on-disk contract with its own staleness story does not belong in a bugfix.
- **Changing bash link behaviour.** POSIX symlinks need no privilege; the hardlink/copy ladder is a
  Windows answer to a Windows problem (D004).
- **Reordering the personal-import block.** Rejected on evidence, see D001.
- **Touching the framework model, profiles, or any downstream project.**

## Regression tests

| Test | Covers | Runs where |
|---|---|---|
| `install.test.sh` — first install + payload leaves `~/.claude/CLAUDE.md` | BUG-1 (bash) | this Mac, CI |
| `install.test.ps1` — same scenario under pwsh | BUG-1 (PowerShell) | this Mac (pwsh 7.5.2), Windows |
| `install.test.ps1` — payload-free install still skips cleanly | AC-009 no-regression | this Mac |
| `install.test.ps1` — `$DefaultCentralDir` agrees with the `param()` default | BUG-2a drift guard | this Mac |
| `install.test.ps1` — `link-project.ps1` / `wire-hooks.ps1` resolve the `$HOME` fallback | BUG-2b | this Mac |
| `install.test.ps1` — not-found warning enumerates every candidate | AC-006 | this Mac |

The symlink→hardlink→copy ladder (BUG-3) **cannot be tested here**: on macOS the first attempt
succeeds, so no fallback ever executes. It is covered by code review plus the manual Windows
procedure in PLAN.md.

## Risks

- **R1 — hardlink same-volume constraint.** A hardlink fails across volumes; the ladder then falls to
  copy. Handled, and stated in the warning.
- **R2 — hardlink silent divergence.** A hardlink is a second name for one inode. If the central file
  is later *replaced by rename* (the usual atomic-write pattern), the two names stop being the same
  file and drift with no error. The warning must say so; the framework must not claim sync.
- **R3 — copy is a snapshot, not a link.** Explicitly warned, never described as synchronized.
- **R4 — deferred skip message.** BUG-1's fix moves the "no central CLAUDE.md" message to after the
  personal import. On the `MissingShipped` failure path the installer exits 1 before reaching it, so
  that one message is lost in a run that is already failing loudly for another reason (D002).
- **R5 — BUG-3 is unverified on real Windows.** No Windows machine in this session. Mitigated by the
  manual procedure; the spec does not reach `Live` until someone runs it.

## Acceptance criteria

- **AC-001** — First install with a personal payload containing `central/CLAUDE.md` leaves
  `~/.claude/CLAUDE.md` created and linked.
- **AC-002** — `install.ps1` keeps the default `C:\ProgramData\ClaudeConfig`.
- **AC-003** — `Report-UnrefreshedProfiles` compares against the PowerShell default.
- **AC-004** — `link-project.ps1` discovers the `$HOME\.claude-config` fallback when the default is
  absent.
- **AC-005** — `scripts/wire-hooks.ps1` discovers the same fallback.
- **AC-006** — Central-dir warnings name every path checked, and no longer say "Run install.ps1
  first" when an install exists elsewhere.
- **AC-007** — `install.ps1` attempts symlink → hardlink → copy for `CLAUDE.md`.
- **AC-008** — Each downgrade emits an explicit warning naming the mechanism and its cost.
- **AC-009** — The bash installer is not broken by the change; the payload-free path behaves exactly
  as before.
- **AC-010** — Regression tests cover the bugs that are testable on this platform, and the untestable
  one is named as such.
- **AC-011** — `check-consistency.sh` passes.
- **AC-012** — No claim anywhere that a hardlink or copy stays perfectly synchronized.
