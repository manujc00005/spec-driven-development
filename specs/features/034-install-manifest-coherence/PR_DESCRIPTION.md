# Pull Request Description

## Summary

The install manifest recorded a single commit for the whole profile set while a run only installed
files for its **active** profiles — so it routinely claimed a freshness it had never verified, and
`update.sh` trusted that claim. This PR makes freshness per-profile, adds a way to remove a profile
(previously impossible), and unfreezes two shipped READMEs that `--force` never refreshed.

## Related spec

`specs/features/034-install-manifest-coherence/`

Spec status at time of PR: **Done**

## Acceptance criteria coverage

- AC-001: partial run stamps only active profiles, names the rest, exit unchanged — **Covered**
- AC-002: `update` delta computed from the oldest per-profile commit — **Covered**
- AC-003: `schemaVersion: 1` migrates in place, no re-install — **Covered**
- AC-004: byte-identical manifest on an identical re-run — **Covered**
- AC-005: removal deletes exclusives, keeps shared, backs everything up — **Covered**
- AC-006: a removed profile stays removed across `update` — **Covered**
- AC-007: `--remove-profile core` refused, nothing changed — **Covered**
- AC-008: `--dry-run` removal writes nothing, reports both sets — **Covered**
- AC-009: same profile in `--profile` and `--remove-profile` refused before any write — **Covered**
- AC-010: traversing and unknown names refused before any deletion — **Covered**
- AC-011: shipped READMEs refreshed under `--force`, previous content backed up — **Covered**
- AC-012: shipped files match the repo after a full refresh — **Covered**
- AC-013: PowerShell parity, proven by CI rather than a manual spot-check — **Covered**
- AC-014: consistency + suites green and wired into CI — **Covered** (structural: no in-test label)

## Changes

- **`.sdd-install.json` → `schemaVersion: 2`**, adding a `profileState` map of
  `{commit, version, installedAt}` per profile. `profiles` and the top-level
  `installedVersion`/`installedCommit` keep their shape, so a pre-034 reader still resolves.
- **`install.sh` / `install.ps1`**: per-profile stamping; v1→v2 migration; end-of-run warning naming
  every recorded profile the run did not refresh, with the exact refresh command; new
  `--remove-profile` / `-RemoveProfile`; `agents/README.md` and `hooks/README.md` routed through the
  normal backup-then-overwrite path; `usage()` no longer truncates its own options list.
- **`scripts/update.sh` / `update.ps1`**: delta computed from the oldest per-profile commit; the
  recorded profile list is replayed verbatim, `core` included.
- **Tests**: `scripts/install.test.sh` +21 assertions (it had **zero** manifest coverage);
  `scripts/update.test.sh` +3; new `scripts/install.test.ps1` (16) and `scripts/update.test.ps1` (3).
- **CI**: `install.test.sh` wired into the `check` job — it was never being run — and both
  PowerShell suites added to the existing `windows-latest` runner.
- **Docs**: `docs/INSTALL.md` and `CHANGELOG.md`.

## Decisions made

Eleven, all `Accepted`, in `DECISIONS.md`. The load-bearing ones:

- **D001** — `update` replays the recorded profile list verbatim including `core`;
  `defaults.profile` applies only to a direct call with no `--profile`. Needed no new flag, since
  `--profile core` already resolves.
- **D002/D003** — v2 schema shape, and the knowingly-optimistic v1 migration (it asserts nothing the
  v1 format did not already assert).
- **D004** — removal derives ownership from `profiles.json` alone and never deletes without a backup.
- **D005** — Windows parity is a CI gate, not a manual spot-check. *Amended at review*: the original
  subset contradicted AC-013, so the tests were widened rather than the AC narrowed.
- **D006** — `install.test.sh` wired into CI *before* new assertions were written into it.
- **D010** — a removal-only run does not fall back to `defaults.profile`. Found by testing: without
  it, `--remove-profile X` deleted X and re-installed it in the same pass.
- **D011** — two fixes outside the stated scope, kept deliberately (see Risks).

## Tests

- **Tests added or updated**: `install.test.sh` (5 → 29), `update.test.sh` (7 → 10), new
  `install.test.ps1` (16), new `update.test.ps1` (3).
- **Tests run**: all five suites, `shellcheck -S error`, and the `.ps1` parse gate.
- **Test results**: **100 assertions passing, 0 failing.** shellcheck clean; 19 `.ps1` files parse.
- **Mutation-tested**: reverting the shared-item protection fails AC-005; restoring the original
  newest-commit delta fails AC-002 with the exact bug message; removing the final-set ownership fix
  fails 2 assertions. The tests bite.
- **Manual testing**: E2E against a faithful copy of a real 8-profile central dir — a partial run
  named the 6 unrefreshed profiles, and a full refresh left `diff -rq` clean. Three attacks on the
  delete path (item-name traversal, absolute path, symlink escape) were executed and blocked.

## Risks

- **`update.ps1` had no automated coverage before this PR** and its manifest logic was rewritten
  here. Now covered by `update.test.ps1`, but that suite is new and unexercised by real CI yet.
- **D011 lands two out-of-scope fixes.** One repairs a **pre-existing spec 015 defect**:
  PowerShell 7's `ConvertFrom-Json` turns ISO stamps into `[datetime]`, so `install.ps1` never
  produced a byte-identical manifest — spec 015's AC-003 held on bash only. It could not be deferred
  without shipping a knowingly failing AC. Anyone auditing spec 015 should read D011.
- **CI has not run.** `consistency.yml` triggers only on `main` and PRs targeting `main`; every gate
  above was reproduced locally. This PR is the first real execution.
- `_install-backups/<ts>` has second granularity — pre-existing, shared by every backup path, no
  observed collision.

## Follow-up work

- **Local hand-edits inside the central dir are silently clobbered by the next `--force`.** Deferred
  at close and still open; FR-015 widened its blast radius to the two shipped READMEs. Deserves its
  own spec. Immediate mitigation for this maintainer: port the local `scope-keeper` bullet into
  `skills/scope-keeper/SKILL.md` before the next `--force` run.
- **Spec 030** (`Draft`) also touches `update.sh` reporting and `install.sh` profile handling.
  Whichever lands second reconciles.

## Checklist

- [x] Implementation matches all acceptance criteria in the spec
- [x] No behavior outside the spec was introduced *(two exceptions, both recorded in D011)*
- [x] Tests were added or updated for changed behavior
- [x] All decisions are documented in DECISIONS.md
- [x] SPEC.md status is up to date (`Done`)
- [x] Security-sensitive behavior was reviewed — `/security-review` Pass; traversal and symlink
      attacks executed against the delete path and blocked
- [ ] Database changes were reviewed — n/a, no database
- [ ] Performance-sensitive paths were reviewed — n/a, no performance NFR
- [x] No unrelated files were changed — `skills/`, `agents/`, `hooks/` and `profiles.json` untouched
