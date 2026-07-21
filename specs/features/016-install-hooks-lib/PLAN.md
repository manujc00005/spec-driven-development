# PLAN — 016 Install hooks/lib in profile mode

## Approach

Reuse the existing safe-copy helpers instead of writing new copy logic — they
already implement the required semantics (new → copy, identical → no-op,
differs → skip unless force with backup), which satisfies AC-03 by construction.

1. `install.sh`: in the profile-filtering hooks branch, after the per-hook
   loop and README copy, call
   `copy_tree_safely "$REPO_ROOT/hooks/lib" "$CENTRAL_DIR/hooks/lib" ...`.
   The helper warns-and-skips if the source dir is missing, so no extra guard.
2. `install.ps1`: same placement, `Copy-TreeSafely $hooksSrc\lib ...`
   (guarded with `Test-Path` because the PS helper also warns — kept symmetric
   with the sh call site).
3. Regression test `scripts/install.test.sh` (hermetic tmp central dir,
   `--skip-link`, java-spring-backend profile): AC-01 lib file exists,
   AC-02 git-guardrails exit 2 on `git push --force` / exit 0 on benign,
   AC-03 tree-hash-identical re-run.
4. Negative verification: run the pre-fix installer (`git show HEAD:install.sh`)
   into a scratch dir and confirm the test's assertions fail there.

## Why lib/ is copied unconditionally (not per-profile)

`hooks/lib` is a shared runtime dependency of whichever hooks the profile
selects, not a selectable item itself. Modeling it in profiles.json as a hook
would wrongly imply it can be omitted.

## Verification

- `scripts/install.test.sh` → 5/5 PASS.
- Pre-fix installer: lib missing, guardrail exit 127 on `git push --force`
  (crash, non-blocking) — bug reproduced, test discriminates.
- `scripts/check-consistency.sh` → passed (no profiles/README drift introduced).
- Windows runtime check deferred (AC-04) — code-parity change only.
