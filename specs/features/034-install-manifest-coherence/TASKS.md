# Tasks: install-manifest-coherence

Every task names the acceptance criteria it closes. `AC-013` (PowerShell parity) and `AC-014`
(CI/regression) are cross-cutting and are closed by several tasks together.

**Ordering constraint:** T001 precedes Phase 3 (D006 — assertions must land in a harness CI
actually runs). T008 precedes T009 (validate before deleting). T003–T005 precede T012.

## Phase 1: Preparation

- [x] T001 - Wire `scripts/install.test.sh` into the `check` job of
  [`.github/workflows/consistency.yml`](../../../.github/workflows/consistency.yml), next to the
  existing `update.test.sh` step. It is **not currently run**. Verify the pre-existing spec-016
  assertions pass; if any is red, stop and report it as a surfaced regression rather than weakening
  the assertion. Covers: AC-014. (D006)

- [x] T002 - Add manifest fixtures and a `manifest_field <path> <jq-ish key>` read helper to
  `scripts/install.test.sh`: a valid v1 manifest, a valid v2 manifest, a corrupt (non-JSON) one, and
  one with `schemaVersion: 99`. No production code in this task. Covers: AC-003, AC-004.

## Phase 2: Implementation

### Manifest schema v2 (Bash)

- [x] T003 - In `write_install_manifest` ([install.sh:684-733](../../../install.sh:684)), emit
  `schemaVersion: 2` with a `profileState` map of `{commit, version, installedAt}` per profile.
  Rewrite entries **only** for `ACTIVE_PROFILES` (FR-002); carry untouched entries through verbatim. Preserve
  `installedAt` per profile when that profile's recorded commit equals the current commit (the
  spec-015 idempotence rule, applied per profile instead of globally). Keep `profiles` and the
  top-level `installedVersion`/`installedCommit` unchanged in shape. Covers: AC-001, AC-004. (D002)

- [x] T004 - Add manifest normalization on read, used by `install.sh` and `scripts/update.sh`:
  `schemaVersion: 1` → attribute the top-level `installedCommit` to every recorded profile;
  `schemaVersion: 2` → use `profileState`, backfilling any profile listed in `profiles` but missing
  from `profileState`; anything else or unparseable → existing discard-and-rebuild / unknown-version
  mode. Must not require a re-install and must not error on missing keys (FR-003). Covers: AC-003. (D003)

- [x] T005 - After a successful non-dry-run install, warn when `set(profiles) - set(ACTIVE_PROFILES)`
  is non-empty. List each unrefreshed profile with its recorded commit and print the exact refresh
  command. Must not alter the exit code, and must print nothing when the active set covers every
  recorded profile. Covers: AC-001. (D007)

### `update.sh`

- [x] T006 - Compute the "what's new since your version" delta from the **oldest** `profileState`
  commit, never the top-level `installedCommit`. Covers: AC-002. (D002)

- [x] T007 - Pass the recorded profile list **verbatim, including `core`**, instead of stripping
  `core` and passing the remainder ([update.sh:163-168](../../../scripts/update.sh:163)). Leave the
  no-manifest unknown-version path and its `defaults.profile` fallback untouched. Covers: AC-006.
  (D001)

### `--remove-profile` (Bash)

- [x] T008 - Add `--remove-profile <name>` to argument parsing (repeatable) and implement all
  validation **before any filesystem write**: reject a name absent from `profiles.json`; refuse
  `core` with an explanatory message and a non-zero exit; reject the same name appearing in both
  `--profile` and `--remove-profile`; treat a valid-but-unrecorded name as a no-op with a message,
  not an error. Covers: AC-007, AC-009, AC-010; also FR-011 (unrecorded-name no-op), which has no dedicated AC. (D004)

- [x] T009 - (D010 emerged here) Implement removal: compute exclusively-owned items from `profiles.json` only (deletable
  iff present in the removed profile's arrays and in no still-recorded profile's arrays), back each
  file up to `_install-backups/$TIMESTAMP/` **before** deleting, abort the removal if a backup fails,
  then drop the profile from both `profiles` and `profileState`. Removal runs before the install pass
  so ownership is computed against the final recorded set. Covers: AC-005. (D004)

- [x] T010 - Honor `--dry-run` for removal: write nothing, delete nothing, and report both the
  would-delete set and the retained-because-still-owned set. Covers: AC-008.

### Shipped READMEs (Bash)

- [x] T011 - Replace the `[ ! -e "$dest" ]` guards at [install.sh:500](../../../install.sh:500) and
  [install.sh:566](../../../install.sh:566) with `copy_file_safely` calls, passing a backup path
  under `_install-backups/$TIMESTAMP/`. Covers: AC-011, AC-012. (D009)

### PowerShell parity

- [x] T012 - (FR-016) Mirror T003–T005 in `install.ps1` (manifest writer at `:679-733`): schema v2,
  per-profile state, migration, unrefreshed-profile warning. Identical messages and exit codes.
  Covers: AC-013.

- [x] T013 - (FR-016) Mirror T008–T010 in `install.ps1`: `-RemoveProfile`, the full validation set, ownership
  computation, backup-before-delete, and dry-run reporting. Covers: AC-013.

- [x] T014 - (FR-016) Mirror T011 in `install.ps1` (`:475`, `:559`) using its equivalent safe-copy path.
  Covers: AC-013.

- [x] T015 - (FR-016) Mirror T006–T007 in `scripts/update.ps1` (`:110-145`): oldest-commit delta and verbatim
  profile replay. Covers: AC-013.

## Phase 3: Tests

- [x] T016 - Extend `scripts/install.test.sh` with manifest coverage — hermetic temp central dir,
  `--skip-link` throughout: per-profile stamping with a partial active set and the warning naming the
  rest at exit 0 (AC-001); v1→v2 migration with no re-install (AC-003); byte-identical manifest across
  two identical runs (AC-004). Covers: AC-001, AC-003, AC-004, AC-014.

- [x] T017 - Extend `scripts/install.test.sh` with the removal matrix: successful removal deleting
  exclusive files, leaving shared files, and producing backups (AC-005); `--remove-profile core`
  non-zero and inert (AC-007); dry-run writing nothing and reporting both sets (AC-008);
  `--profile x --remove-profile x` non-zero before any write (AC-009); traversal and unknown names
  rejected before deletion (AC-010); README refreshed under `--force` with a backup (AC-011).
  Covers: AC-005, AC-007, AC-008, AC-009, AC-010, AC-011, AC-014.

- [x] T018 - Extend `scripts/update.test.sh` from its existing AC-007 manifest case: delta computed
  from the oldest per-profile commit (AC-002), and a removed profile staying removed across an
  `update.sh` run (AC-006). Covers: AC-002, AC-006, AC-014.

- [x] T019 - Assert the rollback-safety property PLAN.md depends on: a **v1 reader** against a **v2
  manifest** still resolves the correct profile list and commit from the retained top-level keys.
  This is what makes `git revert` safe, so it is asserted rather than assumed. Covers: AC-003.

- [x] T020 - Add `scripts/install.test.ps1` covering AC-001, AC-003, AC-004, AC-005, AC-007,
  AC-008, AC-009, AC-010, AC-011, AC-012, plus the final-set ownership regression. Scoped to this
  spec's behaviors — **not** a port of `install.test.sh`. Covers: AC-013. (D005, amended)

- [x] T021 - Execute `scripts/install.test.ps1` **and `scripts/update.test.ps1`** on the existing
  `windows-latest` runner in `consistency.yml`, as steps separate from the parse-only
  `windows-syntax` gate (which stays as it is). Covers: AC-013, AC-014. (D005, amended)

- [x] T025 - (from `/spec-review`) Compute removal ownership against the final profile set, so an
  item shipped by a profile arriving in the same run is kept rather than deleted and re-copied;
  add `scripts/update.test.ps1` for AC-002/AC-006 on PowerShell (T015 shipped untested); record
  D011 for the two out-of-scope fixes; correct the stray `AC-019` label. Covers: AC-005, AC-013.

## Phase 4: Review

- [x] T022 - Manual E2E on the real `~/.claude-config` (a git repo since `081455a`): commit the
  central dir, run `install.sh --force` with a partial profile set, confirm
  `git -C ~/.claude-config diff` shows changes only for active profiles and that the warning names
  the rest; then run a full-profile refresh and confirm `diff -rq agents ~/.claude-config/agents` and
  `diff -rq hooks ~/.claude-config/hooks` are clean. Covers: AC-012.

- [x] T023 - Run `/security-review` focused on the removal path — traversal guard, deletion confined
  to the central dir, backup-before-delete, and the `core` refusal — then `/review-all` for the rest.
  Confirm `shellcheck -S error` stays clean on the modified scripts and that every CI job is green.
  Covers: AC-014.

- [x] T024 - Document `--remove-profile` / `-RemoveProfile` and manifest schema v2 (including the v1
  migration and the rollback-compatibility property) in `CHANGELOG.md` and the relevant `docs/` page;
  confirm the Codex gap (FR-017, D008) is stated in the shipped docs and not only in DECISIONS;
  run `/spec-close`. Covers: AC-014.
