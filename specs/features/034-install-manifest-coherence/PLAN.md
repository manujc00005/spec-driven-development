# Implementation Plan: install-manifest-coherence

## Summary

Make `<central-dir>/.sdd-install.json` an honest record of the disk, and make the recorded profile
set editable in both directions.

Three changes, in dependency order:

1. **Schema v2 with per-profile state** — each recorded profile carries the commit its files were
   actually written at, plus a v1→v2 migration that needs no re-install, plus an end-of-run
   warning naming profiles this run did not refresh.
2. **`--remove-profile`** — an explicit, backed-up, dry-runnable prune path, with `update.sh` no
   longer able to silently resurrect what was removed.
3. **README freshness** — route `agents/README.md` and `hooks/README.md` through the same
   `copy_file_safely` path as every other shipped file.

Everything is mirrored in PowerShell. The Bash side is defended by `scripts/install.test.sh` and
`scripts/update.test.sh`; the PowerShell side by a new `scripts/install.test.ps1` on the CI
`windows-latest` runner that already exists.

## Related spec

[`SPEC.md`](./SPEC.md) — `specs/features/034-install-manifest-coherence/SPEC.md`

## Impacted areas

| Area | Change |
|---|---|
| [`install.sh`](../../../install.sh) | `write_install_manifest` (v2 + per-profile), `--remove-profile`, unrefreshed-profile warning, README guards at `:500`/`:566` |
| [`install.ps1`](../../../install.ps1) | Same, at `:679-733` (manifest), `:475`/`:559` (READMEs) |
| [`scripts/update.sh`](../../../scripts/update.sh) | Manifest reader `:110-168`: oldest-commit delta, verbatim profile replay |
| [`scripts/update.ps1`](../../../scripts/update.ps1) | Same, at `:110-145` |
| [`scripts/install.test.sh`](../../../scripts/install.test.sh) | First manifest coverage (currently zero assertions) |
| [`scripts/update.test.sh`](../../../scripts/update.test.sh) | Extend existing AC-007 manifest test |
| `scripts/install.test.ps1` | **New** — PowerShell parity harness |
| [`.github/workflows/consistency.yml`](../../../.github/workflows/consistency.yml) | Wire `install.test.sh` (**not currently run**) + the new `.ps1` suite |
| `docs/` , `CHANGELOG.md` | Document the new flag and schema at close |

**Not touched:** `profiles.json` (read-only authority for ownership), any skill/agent/hook content,
`adapters/codex/` (no profile concept — D008).

## Context budget

### Reading list

Bounded to the four scripts and their two harnesses. No whole-repo scan; no other spec folder.

- `specs/features/034-install-manifest-coherence/*` — the active feature folder.
- `install.sh` — regions only: arg parsing (~`:95-107`), profile resolver (~`:130-260`),
  `copy_file_safely` (`:360-390`), README blocks (`:494-503`, `:563-573`), `write_install_manifest`
  (`:684-733`).
- `install.ps1` — the same six regions.
- `scripts/update.sh` (`:110-175`) and `scripts/update.ps1` (`:105-150`).
- `scripts/install.test.sh`, `scripts/update.test.sh` — read in full; both are short (83 / 144 lines).
- `.github/workflows/consistency.yml` — read in full (60 lines).
- `profiles.json` — **structure only** (profile keys and their `skills`/`hooks`/`templates`/`agents`
  arrays). Do not read skill bodies.

Explicitly **out of budget**: `skills/**`, `agents/**`, `hooks/**` file contents, other feature
folders, `evals/**`.

### Model routing

| Phase | Model | Justification |
|---|---|---|
| Phase 1 (schema contract, CI wiring) | cheap/mechanical | Config edits and a written contract already fixed by DECISIONS. |
| Phase 2, T003–T005 (manifest v2 + migration + warning, Bash) | **deep-reasoning** | Migration semantics and the idempotence property (AC-004) interact; getting v1→v2 wrong corrupts adopter state. |
| Phase 2, T008–T010 (removal, Bash) | **deep-reasoning** | The only destructive path in the repo. Ownership computation and the path-safety guard are security-relevant (spec NFR). |
| Phase 2, T011 (READMEs) | cheap/mechanical | Delete two guards, call an existing helper. |
| Phase 2, T012–T015 (PowerShell parity) | cheap/mechanical | Mechanical mirror of decided semantics — but see Risk R4. |
| Phase 3 (tests) | cheap/mechanical | Assertions follow directly from the ACs. |
| Phase 4 (review) | per `/review-all` routing | — |

No Graphify run: four shell scripts, all already located by file:line. A graph would cost more than
it returns here (token-economy principle, spec 026).

## Proposed approach

### 1. Manifest schema v2 (FR-001..FR-006)

`profiles` stays exactly as it is — the ordered list of record that `update.sh` replays. A sibling
`profileState` object keys the same names to `{commit, version, installedAt}`. A run rewrites
`profileState` entries **only** for `ACTIVE_PROFILES`; untouched entries are carried through
verbatim, which is what makes AC-001 hold.

Reading is a single normalization step shared in spirit by all four scripts:

- `schemaVersion == 2` → use `profileState` as-is; backfill any profile present in `profiles` but
  missing from `profileState` from the top-level commit.
- `schemaVersion == 1` → synthesize `profileState` by attributing the top-level `installedCommit`
  to every recorded profile (D002 — knowingly optimistic; it asserts nothing the v1 format did not
  already assert).
- Anything else, or unparseable → existing discard-and-rebuild / unknown-version mode (D003).

Idempotence (AC-004, inherited from spec 015 AC-003) is preserved by the same rule already used for
`installedAt`: when a profile's recorded commit equals the current commit, its `installedAt` is
carried over rather than restamped. Applied per profile instead of once globally.

The warning (FR-004) fires after a successful non-dry-run install when
`set(profiles) - set(ACTIVE_PROFILES)` is non-empty, listing each name with its recorded commit and
the exact refresh command. Informational: it never touches the exit code.

### 2. `--remove-profile` (FR-007..FR-014)

Ordering inside a run: **validate → remove → install**. Removal must complete before the install
pass so ownership is computed against the final recorded set.

- **Validation** (before any filesystem write): name must appear in `profiles.json`; `core` is
  refused (FR-010); the same name in `--profile` and `--remove-profile` is a usage error (FR-013);
  a name recorded nowhere is a no-op with a message, not an error (FR-011).
- **Ownership** is computed purely from `profiles.json`: an item is deletable iff it appears in the
  removed profile's arrays and in **no** still-recorded profile's arrays (FR-008). `core` membership
  therefore protects an item automatically, since `core` is always recorded.
- **Deletion** reuses `_install-backups/$TIMESTAMP/` (FR-009). Nothing is deleted without a backup
  copy landing first — deletion is the one path where a failed backup must abort rather than warn.
- **`--dry-run`** reports both the would-delete set and the retained-because-shared set (FR-012).

### 3. Resurrection fix (D001)

`update.sh` currently strips `core` from the recorded list and passes the rest as `--profile`. With
an empty remainder it passes nothing, and `install.sh` falls back to `defaults.profile`
(`java-spring-backend`) — re-adding a just-removed profile and defeating FR-014.

Fix: `update.sh` passes the recorded list **verbatim, including `core`**. `--profile core` already
resolves correctly today (`core` is a valid, non-disabled profile name), so this needs **no new
flag and no change to `install.sh`'s resolver**. The `defaults.profile` fallback then applies only
where it was meant to — a direct `install.sh` invocation with no `--profile`.

### 4. READMEs (FR-015)

Delete the `[ ! -e "$dest" ]` guards and call `copy_file_safely` with a backup path under
`_install-backups/$TIMESTAMP/`. The helper already implements exactly the required semantics: new →
copy, identical → no-op, differs → skip unless `--force`, differs + `--force` → back up then
overwrite. Net effect is a *smaller* diff than the code it replaces.

## Alternatives considered

- **Per-profile manifest files** (`.sdd-install/<profile>.json`) instead of one nested object.
  Rejected: four scripts in two languages already parse one path; multiplying files multiplies the
  corrupt-state matrix for no gain, and breaks the single-file discard-and-rebuild rule.
- **Auto-refreshing stale profiles** instead of warning. Rejected (D007) — a run naming
  `--profile java-spring-backend` must not start writing `python-sql-data` files. Same reasoning
  spec 030 applied to newly-added profiles.
- **A new `--no-default-profile` flag** to fix the resurrection bug. Rejected in favour of D001:
  passing the recorded list verbatim achieves it with zero new surface.
- **Recomputing per-profile freshness by hashing the disk** rather than recording it. Rejected: it
  answers "does this differ from the current repo?" not "what commit was this installed at", and
  costs a full tree walk on every run.
- **Dropping the top-level `installedCommit`.** Rejected: FR-005 keeps it for backward
  compatibility with any reader not yet updated, redefined as "newest commit any profile reached".
- **Leaving Windows parity to a manual spot-check** (the spec's own non-blocking question).
  Rejected as D005 — see Risks R4.

## Dependencies

- `python3` on macOS/Linux — already a hard requirement of `install.sh` (it exits 1 without it).
- PowerShell 5.1+ on Windows — already required by `install.ps1`.
- GitHub Actions `windows-latest` runner — **already present** in `consistency.yml` for the
  parse-only gate; D005 reuses it to execute the new suite.
- `profiles.json` schema — read-only; no version bump needed.
- **Spec 030** (`Draft`) touches `update.sh` reporting and `install.sh` profile handling. No
  dependency in either direction, but whichever lands second reconciles — recorded so it is not
  discovered at merge time.

## Risks

| # | Risk | Severity | Mitigation |
|---|---|---|---|
| R1 | **Removal deletes something still needed.** Ownership computed wrong ⇒ a shared skill disappears. | **High** | Ownership from `profiles.json` only, never the filesystem (D004); `core` membership is automatic protection; AC-005 asserts the shared-item case explicitly; `--dry-run` reports retained items so the set is inspectable before acting. |
| R2 | **Path traversal via a crafted profile name.** `--remove-profile ../../etc` deleting outside the central dir. | **High** | Name validated against `profiles.json` keys before any filesystem call (AC-010); deletions are computed item names joined to the central dir, never adopter-supplied paths. |
| R3 | **v1→v2 migration corrupts a working manifest.** | Medium | Migration is additive and never drops keys; a manifest that fails to parse falls into the existing discard-and-rebuild path; AC-003 + AC-004 assert migration and idempotence together. |
| R4 | **PowerShell drifts from Bash** — the recurring failure mode that left specs 015 and 016 open on unrun Windows spot-checks. | Medium | D005: `scripts/install.test.ps1` executes on the existing `windows-latest` runner, so parity is a CI gate rather than a manual task nobody performs. |
| R5 | **New tests do not actually gate** — `install.test.sh` is not currently run by CI. | Medium | T001 wires it in *before* Phase 3 writes assertions into it, so the coverage is live the moment it exists. |
| R6 | Adopter loses a hand-edit when FR-015 starts overwriting READMEs. | Low | `copy_file_safely` backs up before overwriting, and only under `--force`. Noted in the spec's Edge cases. |
| R7 | Removing the last non-core profile silently re-adds the default. | **Was High** | Resolved by D001; asserted by AC-006. |

## Test strategy

- **Unit**: n/a (shell + PowerShell) — behavior is covered by the harnesses below.
- **Integration (Bash)**: `scripts/install.test.sh` gains its first manifest coverage — hermetic
  temp central dir + temp clone with two commits, `--skip-link` throughout (never touches
  `~/.claude`). Covers AC-001, AC-003, AC-004, AC-005, AC-007..AC-011.
  `scripts/update.test.sh` extends its existing AC-007 manifest case to cover AC-002
  (oldest-commit delta) and AC-006 (no resurrection after removal).
- **Integration (PowerShell)**: new `scripts/install.test.ps1` mirroring AC-001, AC-003, AC-005,
  AC-007, AC-011 — the subset where a semantic divergence would be silent. Runs on `windows-latest`
  (AC-013).
- **Regression**: `check-consistency.sh`, `check-consistency.test.sh`, `graphify.test.sh` must stay
  green; `shellcheck -S error` must stay clean on the modified `install.sh`/`update.sh`; the
  parse-only `.ps1` gate must stay green (AC-014).
- **E2E (manual, maintainer)**: on the real `~/.claude-config`, which is a git repo since `081455a`
  — commit, run `install.sh --force` with a partial profile set, confirm
  `git -C ~/.claude-config diff` shows changes only for active profiles and that the warning names
  the rest; then a full refresh and confirm the tree goes clean (AC-012).
- **Not tested automatically**: nothing in the AC list. Every AC has a named home above.

## Rollback strategy

- **Code**: the change is confined to four scripts, two harnesses and one workflow file. `git revert`
  of the feature commit restores prior behavior completely; no data migration to unwind.
- **Manifests already migrated to v2**: harmless after a revert — v1 readers use the top-level
  `installedCommit`/`profiles`, both of which v2 retains (FR-005). A reverted installer simply
  ignores `profileState` and rewrites the file on its next run. **This is the property that makes
  the rollback safe and it must be asserted, not assumed** — covered as T019.
- **Files deleted by `--remove-profile`**: recoverable from `_install-backups/<timestamp>/` (FR-009).
  Re-adding the profile with `--profile <name>` reinstalls them from the repo outright.
- **Kill switch**: none needed — every new behavior is behind an explicit flag (`--remove-profile`)
  or is additive and informational (the warning).

## PLAN verification checklist

- [x] The plan covers all acceptance criteria. (AC-001..AC-014 → T001..T024; see TASKS.md.)
- [x] The plan avoids behavior outside the spec. (D001 is the one addition, and it exists to make
      FR-014/AC-006 achievable rather than to extend scope.)
- [x] The Context budget section is filled (reading list + model routing), not left as placeholder.
- [x] Risks are documented.
- [x] Test strategy is documented.
- [x] Rollback strategy is documented.
- [x] SPEC.md status has been updated to `Ready`.
