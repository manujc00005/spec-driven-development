# Tasks: windows-install-first-run-fixes

Status legend: `[ ]` pending · `[~]` in progress · `[x]` done · `[!]` blocked

## BUG-1 — CLAUDE.md never linked on a first install

- [x] **T001** — `install.ps1`: extract the `CLAUDE.md` link step into `Invoke-ClaudeMdLink`,
      returning `$false` only when the central file is absent. (AC-001)
- [x] **T002** — `install.ps1`: call it in place, flag pending, retry after the personal import, and
      print the deferred skip message only if it is still pending. (AC-001, D002)
- [x] **T003** — `install.sh`: same extraction as `link_central_claude_md`. (AC-001, AC-009)
- [x] **T004** — `install.sh`: same call/flag/retry/deferred-message wiring. (AC-001, AC-009)

## BUG-2 — central dir discovery

- [x] **T005** — `install.ps1`: add `$DefaultCentralDir` and use it in `Report-UnrefreshedProfiles`
      instead of the bash default. (AC-002, AC-003, D005)
- [x] **T006** — `link-project.ps1`: candidate resolution with the `$HOME\.claude-config` fallback,
      enumerated not-found warning, no false "Run install.ps1 first". (AC-004, AC-006, D003)
- [x] **T007** — `scripts/wire-hooks.ps1`: same resolution for the template search; warning
      enumerates central dir, fallback and repo root. (AC-005, AC-006, D003)

## BUG-3 — privilege-tolerant CLAUDE.md link

- [x] **T008** — `install.ps1`: symlink → hardlink → copy ladder inside `Invoke-ClaudeMdLink`, with a
      warning at each downgrade naming the mechanism and its cost. (AC-007, AC-008, AC-012)
- [x] **T009** — `install.ps1`: recognise an existing `HardLink` at the right target on re-run.
      (AC-007, D006)

## Tests and evidence

- [x] **T010** — `scripts/install.test.sh`: first install + personal payload leaves
      `$CLAUDE_HOME/CLAUDE.md` linked to central. (AC-001, AC-010)
- [x] **T011** — `scripts/install.test.ps1`: same scenario under pwsh, plus a payload-free control
      that must still skip cleanly. (AC-001, AC-009, AC-010)
- [x] **T012** — `scripts/install.test.ps1`: `$DefaultCentralDir` drift guard against the `param()`
      default. (AC-003, AC-010, D005)
- [x] **T013** — `scripts/install.test.ps1`: `link-project.ps1` and `wire-hooks.ps1` discover the
      `$HOME` fallback; not-found warnings enumerate every candidate. (AC-004, AC-005, AC-006)
- [x] **T014** — Run `bash scripts/check-consistency.sh`, `bash scripts/install.test.sh`,
      `pwsh -File scripts/install.test.ps1`; record results. (AC-011)
- [x] **T015** — Audit the tree for false sync claims about hardlink/copy. (AC-012)
- [x] **T016** — CHANGELOG entry under `[Unreleased]`, following the house pattern. (AC-010)

## Evidence

- **T010/T011 are real regressions, not decorations.** Both were run against the pre-fix installers
  extracted from `HEAD` (`git show HEAD:install.sh` / `install.ps1`, executed from the repo root so
  `REPO_ROOT` still resolved). Both reproduced the bug exactly: `<central>/CLAUDE.md` **YES**,
  `~/.claude/CLAUDE.md` **NO**, one `CLAUDE.md link skipped` line. The temporary copies were removed
  and `git status` verified clean afterwards.
- **A defect in this feature's own patch was caught by its own test.** The first
  `scripts/wire-hooks.ps1` version built candidates with `Join-Path`, which resolves the drive
  qualifier and throws `A drive with the name 'C' does not exist` once it iterates a candidate list
  on a non-Windows host. Switched to `[System.IO.Path]::Combine`, identical on Windows.
- **T008/T009 remain unverified on real Windows.** The ladder cannot execute here: on macOS the
  symlink rung always succeeds. The structural assertions in `install.test.ps1` prove the order and
  the warnings exist, not that they work. This feature does not reach `Live` until someone runs the
  manual procedure in PLAN.md on the Windows 11 machine.
