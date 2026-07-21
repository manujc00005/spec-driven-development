# Feature Spec: incremental-update

## Status

In Progress

## Problem

The framework evolves fast (15 specs, 5 releases in the CHANGELOG) and is designed to be installed once into a central directory and linked from many projects. Re-running `install.sh`/`install.ps1` after a `git pull` is already safe (idempotent, never deletes, `--force` + backups), but the *update experience* has three real gaps for an existing adopter:

1. **No installed-version record.** The installer writes no stamp of what release/commit was installed, so nothing can answer "what changed since my install?" — the adopter must diff the CHANGELOG by hand.
2. **Multi-step manual ritual.** A correct update is `git pull` + `install.sh` (same profiles as before — which the adopter must remember) + re-run `link-project` where agents are used + re-run `wire-hooks` if new hook families appeared. Each step is documented but nothing sequences them, and forgetting one leaves a partial update (agents are copies, not links, so they silently stay stale).
3. **CLAUDE.md drift is invisible.** The installer only ships `CLAUDE.md.example`; new sections (e.g. "Mindset defaults" from spec 013) never reach an adopter's real per-project `CLAUDE.md`, and nothing tells them a new section exists to merge.

## Goal

A first-class incremental update path: one command that brings an existing install up to date **without breaking or overwriting anything the adopter owns**, and that tells them exactly what is new, what was updated, and what they still need to do by hand.

Concretely:

- `install.sh`/`install.ps1` record an **install manifest** (release version/commit, date, profiles installed) in the central directory.
- New `scripts/update.sh` + `scripts/update.ps1` sequence the whole update: fetch/pull, re-install with the **recorded** profiles, refresh agents, and print a **"what's new since <your version>"** report derived from the CHANGELOG/tags.
- The update report includes a **CLAUDE.md drift check**: sections (`## …` headings) present in the new `CLAUDE.md.example` but absent from a target `CLAUDE.md` are listed as "pending manual merge" — report-only, never auto-merged.
- Everything inherits the existing safety model: never delete, never touch `CLAUDE.md`/`settings.json`/`settings.local.json`, skip-differing-unless-`--force`, timestamped backups, `--dry-run` supported.

## Non-goals

- No auto-merge of `CLAUDE.md` or any adopter-owned file — drift is reported, the merge stays manual.
- No self-update over the network beyond `git pull` of the existing clone (no curl-pipe installers, no release downloads).
- No changes to the linking architecture (central dir + symlinks + copied agents stays as is).
- No package-manager distribution (brew/npm/scoop) — out of scope for this feature.
- No migration tooling for adopter-authored skills/hooks; only the framework's own artifacts are managed.
- No breaking change to existing `install.sh`/`install.ps1` flags or behavior — the manifest write is additive.

## Users / Actors

- **Existing adopters** with a central-dir install (possibly several profiles, possibly `--link-user-claude`, possibly several linked projects).
- **The maintainer (Manuel)** dogfooding updates across his own projects.
- **CI** (`check-consistency.sh`) — must keep passing; may gain awareness of the new scripts.
- `install.sh`/`install.ps1`, `link-project.*`, `wire-hooks.*` — invoked or referenced by the update flow.

## Current behavior

- `install.sh`/`install.ps1`: idempotent, additive, `--force` + timestamped backups under `<central-dir>/_install-backups/<ts>/`, profile-aware via `profiles.json`, never writes `CLAUDE.md`/`settings.json`/`settings.local.json`. Records nothing about what was installed.
- Updates are documented in `docs/INSTALL.md` ("update the central directory once… and every linked location picks up the change"), including the agents-are-copies exception — but as prose, not tooling.
- Releases are SemVer git tags; `CHANGELOG.md` maps each release to its spec trail. `profiles.json`'s `version` field is the manifest **schema** version, not the release version.
- No update command, no installed-version stamp, no drift report.

## Desired behavior

### Install manifest (installer change, additive)

- On every successful (non-dry-run) run, `install.sh`/`install.ps1` write `<central-dir>/.sdd-install.json`:
  - `installedVersion`: nearest reachable git tag (`git describe --tags`) or commit hash of the source clone, plus the commit hash always.
  - `installedAt`: ISO-8601 timestamp.
  - `profiles`: the resolved profile list actually installed (accumulated across runs — a later `--profile messaging-event-driven` run merges into the list, never replaces it).
  - `sourceClone`: absolute path of the repo clone used.
- The file is overwritten by each install run (it is framework-owned state, not adopter content). A malformed or missing manifest is never fatal to `install`.

### `scripts/update.sh` / `scripts/update.ps1`

Runs from the clone (like the other scripts). Steps, in order:

1. **Pre-flight:** refuse to run if the clone's working tree is dirty (clear message, no stash magic). Read `.sdd-install.json` from the central dir; if absent, fall back to "unknown version" mode (steps 3–5 still work, the report says "first recorded update").
2. **Pull:** `git pull --ff-only` on the clone. A non-fast-forward pull is a hard error with guidance (the adopter diverged; they resolve it, not the script).
3. **Re-install:** invoke the platform installer with the profiles recorded in the manifest (or the default, in unknown-version mode). Pass through `--dry-run` and `--force` if given to `update`.
4. **Agents refresh:** re-copy agents exactly as the installer does today (respecting skip/force semantics). If the manifest or arguments name linked projects (`--project-dir`, repeatable), re-run the `link-project` agent copy for each; otherwise print a reminder that agent copies in linked projects may be stale.
5. **Report:** print a "What's new" summary:
   - old version → new version (tags/commits).
   - CHANGELOG sections between the two versions, if both resolve to tags (best-effort; raw `git log --oneline` fallback otherwise).
   - Counts of artifacts added/updated/skipped by the re-install (the installer already logs per-file; update aggregates).
   - **CLAUDE.md drift:** for the central `CLAUDE.md.example` vs each `--claude-md <path>` given (repeatable; default: none), list `## ` headings present in the example but missing from the target, as "sections pending manual merge". Never writes the target.
   - Pending manual steps, when applicable: wire-hooks re-run if new hook families shipped, `link-project` for projects not passed, CLAUDE.md merges.
6. **Exit codes:** 0 = updated (or already current), 1 = pre-flight/pull/install error. "Already up to date" is a success, stated plainly.

### Docs & CI

- `docs/INSTALL.md` gains an "Updating an existing install" section with the one-command flow, replacing the current prose-only guidance (prose is updated, not duplicated).
- `README.md` mentions the update command where install is introduced (Quickstart).
- `check-consistency.sh`: the new scripts join the repo's script inventory expectations if any exist (verify — do not invent new checks beyond keeping current ones green). `update.sh`/`update.ps1` must ship as a parity pair like every other script.

## Functional requirements

- FR-001: `install.sh` and `install.ps1` write `<central-dir>/.sdd-install.json` (version+commit, timestamp, accumulated profiles, source clone path) on every successful non-dry-run install; failure to write it is a warning, never an install failure.
- FR-002: Create `scripts/update.sh` and `scripts/update.ps1` with identical behavior (bash/PowerShell parity, same flags: `--central-dir`, `--claude-home`, `--dry-run`, `--force`, `--project-dir` repeatable, `--claude-md` repeatable).
- FR-003: `update` refuses a dirty clone and a non-fast-forward pull with actionable messages; it never stashes, resets, or discards adopter changes.
- FR-004: `update` re-installs with the manifest's recorded profiles; in unknown-version mode it uses the installer's default and says so.
- FR-005: `update` produces the "What's new" report: version delta, CHANGELOG excerpt (tag-to-tag) or `git log --oneline` fallback, and aggregated added/updated/skipped counts.
- FR-006: `update` reports CLAUDE.md drift for each `--claude-md` target as missing `## ` headings from `CLAUDE.md.example`; it never modifies the target.
- FR-007: `update` re-copies agents to `~/.claude/agents` (when previously linked with `--link-user-claude`, detected via manifest or existing copies) and to each `--project-dir`, with the installer's skip/force/backup semantics.
- FR-008: All destructive-adjacent behavior inherits the safety model: nothing deleted, differing files skipped without `--force`, timestamped backup before any forced overwrite, full `--dry-run` support end-to-end.
- FR-009: `docs/INSTALL.md` documents the update flow (new section) and the Quickstart in `README.md` references it; stale prose about manual update steps is updated in place.
- FR-010: `bash scripts/check-consistency.sh` passes after the change; `update.sh`/`update.ps1` ship as a `.sh`/`.ps1` pair like all other scripts.
- FR-011: `update` is idempotent: running it twice in a row ends with "already up to date" and changes nothing the second time.

## Non-functional requirements

- Performance: `update` adds negligible overhead beyond `git pull` + installer; drift check is heading-level text comparison only.
- Security: no network access beyond `git pull` of the adopter's own clone; no curl-pipe, no telemetry; manifest contains only local paths and versions.
- Observability: every step prints what it did or skipped, matching the installers' `[ok]/[skip]/[dry-run]` log style; the final report is the contract.
- Maintainability: `update.sh` reuses the installer via invocation (never reimplements copy logic); python3-for-JSON only, matching the repo's existing dependency posture; bash 3.2 compatible like `install.sh`.

## API / Interface changes

- New commands: `scripts/update.sh` / `scripts/update.ps1` (flags in FR-002).
- New framework-owned state file: `<central-dir>/.sdd-install.json`.
- `install.sh`/`install.ps1`: additive manifest write; no flag or behavior changes otherwise.

## Data model changes

None (no DB). The install manifest is a new JSON state file, versioned by a `schemaVersion` field so its own format can evolve.

## Edge cases

- **No manifest** (install predates this feature): unknown-version mode — update still works, report degrades gracefully, and the run writes the manifest for next time.
- **Manifest corrupt / hand-edited:** treat as absent (warn, unknown-version mode); never crash.
- **Clone moved or deleted** since install (`sourceClone` stale): update runs from wherever it is invoked; it updates `sourceClone` in the manifest.
- **Adopter modified a shipped skill in the central dir:** existing semantics — reported as differing, skipped without `--force`, backed up with it. The report must surface these prominently ("local edits detected in N files").
- **`git pull` needs credentials / offline:** fail cleanly at step 2 with the git error passed through; nothing else attempted.
- **Untagged clone (shallow or no tags fetched):** version resolution falls back to commit hashes; CHANGELOG excerpt falls back to `git log --oneline old..new`.
- **Multiple profiles across historical installs:** manifest accumulates; update reinstalls the union.
- **`--claude-md` target doesn't exist:** report "file not found" for that target, continue with the rest, exit code still 0 (drift check is advisory).
- **Windows/macOS parity:** identical flags and report content; CRLF-safe reading of CLAUDE.md targets.

## Acceptance criteria

- AC-001: After a fresh `./install.sh` (non-dry-run), `<central-dir>/.sdd-install.json` exists and contains version/commit, timestamp, profiles, and source path; `--dry-run` writes nothing.
- AC-002: On a clone one release behind, `scripts/update.sh` ends exit 0 with a report showing old→new version, a CHANGELOG/`git log` excerpt, and added/updated/skipped counts; the new release's artifacts exist in the central dir afterwards.
- AC-003: Running `update.sh` again immediately reports "already up to date", changes no files (verifiable by mtime/checksum), and exits 0 (FR-011).
- AC-004: With a dirty clone, `update.sh` exits 1 before pulling, with a message naming the dirty files; nothing was modified.
- AC-005: With a central-dir file locally edited by the adopter, `update.sh` without `--force` skips it and lists it under "local edits detected"; with `--force` it overwrites after creating the timestamped backup.
- AC-006: Given `--claude-md <file>` missing a section that `CLAUDE.md.example` has, the report lists that heading under "sections pending manual merge" and the target file's checksum is unchanged.
- AC-007: With no manifest present, `update.sh` completes in unknown-version mode, says so in the report, and writes a manifest.
- AC-008: `update.ps1` produces the same behavior for AC-002–AC-007 on PowerShell (parity).
- AC-009: `bash scripts/check-consistency.sh` exits 0; `docs/INSTALL.md` has the "Updating an existing install" section and README Quickstart references the update command.
- AC-010: A test script (`scripts/update.test.sh`, mirroring `check-consistency.test.sh`'s temp-copy approach) covers AC-002/003/004/005/007 against a mutated temp clone and passes.

## Test scenarios

- Unit: n/a (shell) — covered by the harness below.
- Integration: `scripts/update.test.sh` — temp git clone with two tagged releases; simulate behind-by-one, dirty tree, local edits, missing manifest; assert exit codes, report content, and file states. Runs in CI next to `check-consistency.test.sh`.
- E2E: manual run on the maintainer's real central dir: `git pull` a known delta, run `update.sh`, verify report matches CHANGELOG and linked projects see new skills instantly.
- Manual: Windows run of `update.ps1` for parity spot-check; `--claude-md` against a real project's CLAUDE.md missing "Mindset defaults".

## Assumptions

- Releases continue to be SemVer git tags as CHANGELOG states; tag-to-tag CHANGELOG excerpting keys off those tags.
- The manifest lives in the central dir (not per-project): projects are symlinked views, so central state is the single source of truth; the only per-project staleness (agents, wire-hooks) is handled via `--project-dir` or report reminders.
- `update` is a script pair, not a skill — it manages the filesystem/git layer, same as install/link/wire-hooks; a thin `/sdd-update` skill wrapper can be a later feature if wanted.
- `--ff-only` pull is the right default: adopters who fork/diverge manage their own merges.
- Heading-level (`## `) comparison is the right granularity for CLAUDE.md drift — content changes *inside* an existing section are out of scope for the report (too noisy, adopters legitimately customize).

## Open questions

- OQ-001: Should `update.sh` also re-run `wire-hooks` automatically for `--project-dir` targets when new hook families ship, or only remind? (Default: remind only — wiring edits a project's `settings.json`, which deserves an explicit adopter action.)
- OQ-002: Should the drift check also flag headings the adopter has that the example lacks (reverse drift, e.g. deprecated sections)? (Default: no — adopter-authored sections are legitimate; only example→target direction is reported.)
- OQ-003: Manifest filename: `.sdd-install.json` (hidden, framework-owned) vs `sdd-install.json` (visible). (Default: hidden dotfile — it is state, not documentation.)
