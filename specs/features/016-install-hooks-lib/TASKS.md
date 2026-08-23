# TASKS — 016 Install hooks/lib in profile mode

- [x] T01 Reproduce: fresh profile install lacks `hooks/lib/` (audit 2026-07-21 + pre-fix run: guardrail exit 127 on `git push --force`)
- [x] T02 Fix `install.sh` profile branch (`copy_tree_safely` for `hooks/lib`)
- [x] T03 Fix `install.ps1` profile branch (`Copy-TreeSafely` for `hooks\lib`)
- [x] T04 Add `scripts/install.test.sh` (AC-01/02/03) — 5/5 PASS
- [x] T05 Negative check: test assertions fail against pre-fix installer
- [x] T06 `scripts/check-consistency.sh` still passes
- [ ] T07 (User) Windows runtime spot-check of `install.ps1` (goes with the existing update.ps1 spot-check backlog)
  **DEFERRED at close (2026-08-22), not skipped.** AC-04 requires code parity only and
  defers runtime verification by its own wording, so this never blocked closure. It is now
  cheap to retire: spec 034 D005 put a behavioural PowerShell suite on the `windows-latest`
  runner, so the check can be evidence rather than a spot-check nobody performs.
- [ ] T08 (User) Review + commit (audit made no commits; note `feat/adopt-graphify-skill` has unrelated in-flight changes — consider a separate branch off main for this fix)
  **RESOLVED at close (2026-08-22).** Written under an audit constraint that no longer
  applies: the work is committed and on `main`. Left unticked because the tick belonged to a
  review this close supersedes; see D00A.
