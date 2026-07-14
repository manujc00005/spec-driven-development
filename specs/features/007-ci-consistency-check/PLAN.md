# Implementation Plan: CI Consistency Check

## Summary

Add `scripts/check-consistency.sh` (bash + embedded python3, same pattern as `install.sh`), a self-test script that injects each drift class into a temp copy of the repo, count markers in `README.md`, and a GitHub Actions workflow that runs the checker on push/PR to `main`.

## Related spec

`specs/features/007-ci-consistency-check/SPEC.md`

## Impacted areas

- `scripts/` (new directory): `check-consistency.sh`, `check-consistency.test.sh`.
- `.github/workflows/consistency.yml` (new — first CI in the repo).
- `README.md`: count markers + short CI section.
- No changes to `profiles.json`, installers, skills, hooks, agents, or templates — the checker is read-only over them.

## Proposed approach

1. **Data extraction (python3 heredoc):** parse `profiles.json` once and emit a flat, line-oriented inventory (category, item, profile, shipped|planned) that the bash side consumes — mirroring how `install.sh` already bridges JSON→bash. Also emit computed counts (de-duplicated unions per category, per-profile shipped counts) for FR-008.
2. **Existence checks (FR-001..004, FR-011):** for each shipped item verify the expected path(s); template resolution order `specs/_templates/` then `docs/_templates/`, same as `install.sh:269`.
3. **Reverse checks (FR-005, FR-006, FR-009):** enumerate disk artifacts (skill dirs with `SKILL.md`, hook family basenames excluding `lib/` and `README.md`, template files, agent `.md` files excluding `README.md`), diff against the union of shipped+planned; separately fail any planned item found on disk and any hook family missing one variant.
4. **Settings wiring (FR-007):** grep hook script paths out of both settings templates (basename match against `hooks/`), then assert the `maven-compile` / `java-build-test-guard` mutual exclusion per template file.
5. **README counts (FR-008):** parse `<!-- count:<key> -->N<!-- /count -->` spans; compare against computed values; enforce the minimum marker set (`skills-total`, `hook-families-total`, `templates-total`, `agents-total`, `<profile>-skills`, `<profile>-hooks`, `<profile>-templates` for profiles shown in the table). Add the markers to `README.md` as part of implementation.
6. **Report format:** one line per violation `[category] item — message`, summary line `N error(s) found`, exit 1 if N>0. Exit 2 for internal errors (unreadable profiles.json path, etc.); invalid JSON is exit 1 with a friendly message (FR-011 / AC-009).
7. **CI workflow:** minimal `consistency.yml` — checkout, run script, `permissions: contents: read`, triggers `push` + `pull_request` on `main`.
8. **Self-test:** `check-consistency.test.sh` copies the repo to a temp dir (rsync/cp excluding `.git`), runs the checker clean (expect 0), then applies one mutation per drift class, asserting exit code 1 and a message match, restoring between cases.

## Alternatives considered

- **Paired `.ps1` checker:** rejected — checkers are repo-maintenance tooling, not shipped artifacts; the pair rule exists for hooks installed on user machines. Git Bash covers local Windows runs (DECISIONS D001).
- **Regex-scanning README prose for any "N skills" claim:** rejected — false positives on subset phrases ("7 review skills", "3 skills + 1 hook") make it unmaintainable. Markers make checked claims explicit (DECISIONS D002).
- **Extending `install.sh --dry-run` as the CI check:** rejected — the installer only validates the shipped→disk direction and mixes install side-effect logic with validation; a read-only checker is simpler and covers six more drift classes.
- **Node/jq implementations:** rejected — python3 is already a de facto dependency of `install.sh`; no reason to add a second JSON toolchain.

## Dependencies

- GitHub Actions availability on the `manujc00005/spec-driven-development` repo (public repo → free runners).
- bash + python3 on runners and on the maintainer's Git Bash (python3 must be on PATH; the script fails with exit 2 and a clear message if not).

## Risks

- **README markers are invisible and can be deleted by future edits** — mitigated: a missing required marker is itself an error (AC-006 direction), so CI catches the deletion.
- **Checker itself drifts from installer semantics** (e.g. template resolution order changes in `install.sh`) — mitigated by comments cross-referencing `install.sh` line anchors and by the self-test.
- **First-ever CI on this repo** — workflow syntax errors only surface on GitHub; mitigated by keeping the workflow minimal and verifying the first run manually (AC-008).
- **Windows line endings / CRLF** in the script breaking bash on Linux — mitigated: write with LF; self-test runs in CI too, so a CRLF regression fails fast.

## Test strategy

- `scripts/check-consistency.test.sh` covers AC-001..007 and AC-009 by mutation-testing a temp copy of the repo (see approach step 8). It runs in the same CI workflow after the real check.
- AC-008 verified by observing the first real workflow run (manual, one-time).
- Local manual run on Git Bash (Windows) before pushing.

## Rollback strategy

Delete `.github/workflows/consistency.yml` (or add `if: false` to the job) to disable CI enforcement; the script and markers are inert without the workflow. No installed artifact or user-facing behavior depends on this feature.

## PLAN verification checklist

- [x] The plan covers all acceptance criteria.
- [x] The plan avoids behavior outside the spec.
- [x] Risks are documented.
- [x] Test strategy is documented.
- [x] Rollback strategy is documented.
- [x] SPEC.md status has been updated to `Ready`.
