# TASKS — 016 Install hooks/lib in profile mode

- [x] T01 Reproduce: fresh profile install lacks `hooks/lib/` (audit 2026-07-21 + pre-fix run: guardrail exit 127 on `git push --force`)
- [x] T02 Fix `install.sh` profile branch (`copy_tree_safely` for `hooks/lib`)
- [x] T03 Fix `install.ps1` profile branch (`Copy-TreeSafely` for `hooks\lib`)
- [x] T04 Add `scripts/install.test.sh` (AC-01/02/03) — 5/5 PASS
- [x] T05 Negative check: test assertions fail against pre-fix installer
- [x] T06 `scripts/check-consistency.sh` still passes
- [ ] T07 (User) Windows runtime spot-check of `install.ps1` (goes with the existing update.ps1 spot-check backlog)
- [ ] T08 (User) Review + commit (audit made no commits; note `feat/adopt-graphify-skill` has unrelated in-flight changes — consider a separate branch off main for this fix)
