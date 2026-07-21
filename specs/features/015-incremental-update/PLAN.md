# Implementation Plan: incremental-update

## Summary

Give existing adopters a one-command, non-destructive update path: (1) the installers additionally write an install manifest (`<central-dir>/.sdd-install.json` — version, commit, timestamp, accumulated profiles); (2) new `scripts/update.sh`/`update.ps1` sequence pre-flight → `git pull --ff-only` → re-install with the recorded profiles → agents refresh → a "What's new" report including CLAUDE.md heading drift; (3) docs and CI wired accordingly. Everything inherits the existing safety model (never delete, skip-differing-unless-`--force` with timestamped backup, full `--dry-run`).

## Related spec

`specs/features/015-incremental-update/SPEC.md`

## Impacted areas

- `install.sh`, `install.ps1` — additive manifest write at the end of a successful non-dry-run install.
- `scripts/update.sh`, `scripts/update.ps1` — new script pair.
- `scripts/update.test.sh` — new test harness (temp git repos with tags).
- `.github/workflows/consistency.yml` — one added step to run `update.test.sh`; existing shellcheck (`scripts/*.sh`) and PowerShell parse gates cover the new files automatically.
- `docs/INSTALL.md` — new "Updating an existing install" section; existing update prose revised in place.
- `README.md` — Quickstart mention of the update command (no count markers affected — the consistency checker does not inventory `scripts/`).

## Proposed approach

1. **Manifest first (T001–T002).** Add a `write_install_manifest` step to both installers: `git describe --tags --always` (falling back to commit hash), ISO timestamp, resolved profile list merged with any existing manifest's list, source clone path, `schemaVersion: 1`. Write failure is a warning, never an install error; `--dry-run` writes nothing. This lands independently — even without `update.sh`, installs start recording state.
2. **`update.sh` in three slices (T003–T007).** Skeleton with flags + pre-flight (dirty-tree refusal, `--ff-only` pull, clean error paths) → re-install invocation (recorded profiles, unknown-version fallback, pass-through of `--dry-run`/`--force`/`--central-dir`/`--claude-home`) → report (version delta, tag-to-tag CHANGELOG excerpt with `git log --oneline` fallback, aggregated added/updated/skipped counts parsed from installer output, "local edits detected" list, "already up to date" idempotent path) → agents refresh + `--project-dir` handling + manual-step reminders → `--claude-md` heading-drift check (CRLF-safe, advisory, never writes).
   The riskiest assumption — that the installer's per-file log output can be aggregated reliably into counts — is validated first inside T004 with a tracer run before building the full report on top of it.
3. **PowerShell parity port (T008)** once bash behavior is settled — porting a moving target twice is the expensive path.
4. **Docs + CI (T009, T011)** and the **test harness (T010)**: unlike `check-consistency.test.sh` (git-less repo copies), update's contract is git-dependent, so the harness builds throwaway *local* git repos (`file://` clones, two tags, no network) and drives real `update.sh` runs against a temp central dir per case.
5. **Full verification (T012):** consistency suite + new suite + shellcheck locally + manual E2E on the maintainer's real central dir.

## Alternatives considered

- **Reimplement copy logic inside `update.sh`** instead of invoking the installer — rejected: two implementations of skip/force/backup semantics will drift; the installer is already idempotent and safe to re-run, so update orchestrates it (spec NFR: "reuses the installer via invocation").
- **Per-project manifests** instead of one in the central dir — rejected: projects are symlinked views of the central dir; per-project state would duplicate and desynchronize. The only genuinely per-project staleness (agents, wire-hooks) is handled via `--project-dir`/reminders.
- **Auto-merge CLAUDE.md drift** (patch missing sections into the target) — rejected by spec non-goal: adopter-owned files are report-only, the merge stays a human decision.
- **`git pull` with merge/rebase fallback** — rejected: a diverged clone is the adopter's decision point; `--ff-only` plus a clear message is the only non-destructive default (FR-003).
- **Distributing update as a skill (`/sdd-update`)** — rejected for this feature: update manages the filesystem/git layer like install/link/wire-hooks; a skill wrapper is a separable follow-up (spec assumption).

## Dependencies

- `python3` (JSON read/write for the manifest) — already a hard dependency of `install.sh` and `check-consistency.sh`; no new dependency.
- `git` on PATH — already required (the clone is the distribution mechanism).
- Bash 3.2 compatibility (macOS default) and `shellcheck -S error` cleanliness — same bar as every existing script.

## Risks

- **Installer-output parsing for report counts (highest).** The report aggregates `[ok]/[skip]` lines from installer output; if log wording changes later, counts silently break. Mitigation: T004 tracer validates parsing first; `update.test.sh` asserts counts so CI catches future drift; parse on stable prefixes (`[ok]`, `[skip]`), not full sentences.
- **Bash 3.2 + shellcheck gate.** No associative arrays, portable `sed`/`date` — same constraints install.sh already navigates; reuse its patterns (the test harness's `sed_inplace` shows the precedent).
- **PowerShell parity drift.** `update.ps1` is a full port, and only a parse gate runs in CI (no execution on Windows). Mitigation: keep the step structure and report text identical; manual Windows spot-check is an explicit task (T012).
- **Git-dependent tests in CI.** Mitigated by using only local `file://` repos created inside the test — no network, no credentials, deterministic tags.
- **Manifest schema evolution.** `schemaVersion` field from day one; unknown/corrupt manifests degrade to unknown-version mode by spec (FR/edge cases), so a future schema bump cannot brick update.

## Test strategy

- **Integration (primary):** `scripts/update.test.sh` — per-case temp setup: bare "origin" repo with two tagged releases, working clone at the older tag, temp central dir installed from it; then assert AC-002 (behind-by-one → exit 0, version delta + artifacts present), AC-003 (immediate re-run → "already up to date", checksums unchanged), AC-004 (dirty clone → exit 1, nothing modified), AC-005 (local central-dir edit → skipped without `--force`, backed up and overwritten with it), AC-006 (`--claude-md` drift reported, target checksum unchanged), AC-007 (no manifest → unknown-version mode + manifest written).
- **CI:** new workflow step runs `update.test.sh`; existing shellcheck and PS parse gates pick up the new files with zero workflow changes.
- **E2E (manual):** run `update.sh` on the maintainer's real central dir across a known release delta; verify the report matches CHANGELOG and linked projects see new skills immediately.
- **Manual:** `update.ps1` parity spot-check on Windows; `--claude-md` against a real project missing "Mindset defaults".
- **Regression:** `check-consistency.sh` + `check-consistency.test.sh` + `graphify.test.sh` stay green (T012).

## Rollback strategy

Additive feature: revert the feature commit(s) to remove the scripts, the installer manifest block, the docs section, and the CI step. A stray `.sdd-install.json` left in an adopter's central dir is inert (nothing else reads it) and can be deleted by hand. No adopter-owned file is ever modified by the feature, so there is nothing to restore on their side; forced overwrites (pre-existing behavior) remain recoverable from `_install-backups/<ts>/`.

## PLAN verification checklist

- [x] The plan covers all acceptance criteria. (AC-001→T001-T002; AC-002→T004-T006,T010; AC-003→T005,T010; AC-004→T003,T010; AC-005→T005,T010; AC-006→T007,T010; AC-007→T004,T010; AC-008→T008,T012; AC-009→T009,T011,T012; AC-010→T010-T011)
- [x] The plan avoids behavior outside the spec. (no auto-merge, no wire-hooks auto-run, no skill wrapper, no packaging)
- [x] Risks are documented.
- [x] Test strategy is documented.
- [x] Rollback strategy is documented.
- [x] SPEC.md status has been updated to `Ready`.
