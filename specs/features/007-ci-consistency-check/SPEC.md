# Feature Spec: CI Consistency Check

## Status

Done

## Problem

The repository has four sources that must stay aligned: `profiles.json` (the installer manifest), the artifacts on disk (`skills/`, `hooks/`, `agents/`, `specs/_templates/`, `docs/_templates/`), the settings templates (`settings.template.json`, `settings.template.sh.json`), and the `README.md` (headline counts and per-profile counts). Nothing enforces that alignment today: drift is only discovered manually or at install time. Two real incidents motivated this feature: a hook wiring bug in the settings templates (fixed in `2616e16`) and stale counts in `README.md`. Both should have been caught automatically before merge.

## Goal

A single consistency checker script, run locally and in GitHub Actions on every push and pull request, that fails with an actionable report whenever `profiles.json`, the on-disk artifacts, the settings templates, or the README counts diverge.

## Non-goals

- Validating the *content* of skills, hooks, agents, or templates (quality reviews cover that).
- Unifying the spec metadata format (YAML frontmatter vs `## Status`) — separate backlog item.
- Renaming `examples/002` — separate backlog item.
- Functional tests for hooks or installers — separate backlog item (the checker verifies existence/wiring, not behavior).
- Running the installers in CI.
- Checking prose accuracy in README beyond count claims covered by markers (FR-008).

## Users / Actors

- Maintainers of this repository (currently one person) editing profiles, skills, hooks, templates, or README.
- GitHub Actions (CI runner) executing the check on push/PR.

## Current behavior

- `install.sh` / `install.ps1` fail at install time if a shipped item in `profiles.json` is missing on disk — but only when someone runs the installer.
- Nothing checks the reverse direction (on-disk artifacts not declared in any profile).
- Nothing checks the settings templates' hook wiring.
- Nothing checks README counts.
- The repository has no `.github/` directory and no CI at all.

## Desired behavior

`scripts/check-consistency.sh` exits 0 when everything is aligned, and exits 1 printing one line per violation (category, item, expected vs found) when anything drifts. With `--fix` flag, the script auto-corrects safe violations (README counts) and reports them with `[FIXED]` prefix, while non-auto-fixable violations still cause exit 1 and block changes. A GitHub Actions workflow runs it (without `--fix`) on every push and pull request to `main`.

## Functional requirements

- FR-001: Every skill listed in any profile's `skills` array in `profiles.json` must exist as `skills/<name>/SKILL.md`.
- FR-002: Every hook listed in any profile's `hooks` array must exist as **both** `hooks/<name>.sh` and `hooks/<name>.ps1`.
- FR-003: Every template listed in any profile's `templates` array must exist in `specs/_templates/` or `docs/_templates/` (same resolution order as `install.sh`).
- FR-004: Every agent listed in any profile's `agents` array must exist as `agents/<name>.md`.
- FR-005 (orphans): Every artifact on disk must be referenced by at least one profile (shipped or planned): skill directories under `skills/`, hook families under `hooks/` (a family = basename of paired `.sh`/`.ps1`, excluding `hooks/lib/` and `hooks/README.md`), template files under `specs/_templates/` and `docs/_templates/`, and agent files under `agents/` (excluding `agents/README.md`). Unreferenced artifacts are errors.
- FR-006 (planned drift): An item listed in a `planned*` array must NOT exist on disk. If it ships, `profiles.json` must be updated in the same change; the checker fails otherwise. An item must not appear in both the shipped and planned arrays of the same category.
- FR-007 (settings wiring): Every hook path referenced in `settings.template.json` and `settings.template.sh.json` must resolve to an existing file in `hooks/` (matching by basename). The deprecated pair rule is enforced: `maven-compile` and `java-build-test-guard` must never both be wired in the same settings template.
- FR-008 (README counts): `README.md` count claims wrapped in marker comments (`<!-- count:<key> -->N<!-- /count -->`) must match computed values. At minimum the headline claims are marked and checked: total skills, total hook families, total templates, total agents, and the per-profile counts in the profiles table. Adding the markers to `README.md` is part of this feature.
- FR-009 (hook parity): Every hook family on disk must have both the `.sh` and the `.ps1` variant, whether or not it is referenced by a profile.
- FR-010 (CI): A GitHub Actions workflow at `.github/workflows/consistency.yml` runs the checker on `push` and `pull_request` targeting `main`, on `ubuntu-latest`, and fails the build when the checker exits non-zero.
- FR-011 (sanity): `profiles.json` must parse as valid JSON; a profile with `"disabled": true` must have empty shipped arrays.
- FR-012 (auto-fix): When invoked with `--fix` flag, the script auto-corrects safe violations: (a) updates README count markers to match computed values; (b) reports non-auto-fixable violations (orphans, missing artifacts, planned drift, hook pairs, wiring) as before and exits 1. With `--fix`, fixable violations are corrected and reported with `[FIXED]` prefix; non-fixable violations prevent the script from writing changes and cause exit 1.

## Non-functional requirements

- Performance: the check completes in under 10 seconds on a GitHub runner (pure file-existence and text checks; no network).
- Security: no secrets required; the workflow needs only `contents: read` permission.
- Observability: each violation is one self-explanatory line (`[category] item — expected X, found Y`); the final line summarizes error count.
- Maintainability: single script, no dependencies beyond bash + python3 (both preinstalled on GitHub runners; python3 mirrors the JSON-parsing approach already used by `install.sh`). Windows contributors run it via Git Bash.

## API / Interface changes

- New command: `scripts/check-consistency.sh [--fix]` (exit 0 = consistent, exit 1 = drift or uncorrectable violations, exit 2 = usage/internal error). Without `--fix`, reports violations. With `--fix`, auto-corrects safe violations (README counts) and reports non-auto-fixable violations; if any non-fixable violations exist, no changes are written.
- New CI workflow: `.github/workflows/consistency.yml`.
- `README.md` gains invisible HTML marker comments around count claims and a short "CI" section documenting the check.

## Data model changes

None.

## Edge cases

- A skill directory exists but contains no `SKILL.md` → counts as missing (FR-001) and not as a valid orphan.
- A hook has only one of the two variants → FR-009 violation (and FR-002 if shipped).
- `database-review` is shipped by two profiles (java-spring-backend and next-prisma-web) → must be counted once in totals, not flagged as duplicate.
- The overlap between profiles means per-profile counts can sum to more than the global total — the checker computes the global total as a de-duplicated union.
- `hooks/lib/` (shared helpers) and the `README.md` files inside `hooks/` and `agents/` are not artifacts and must be excluded from orphan detection.
- A count marker present in README with no matching computed key → error (stale marker).
- A computed key with no marker in README → error only for the minimum set in FR-008; other keys are optional markers.
- Marker value formatted with surrounding bold (`**43**`) → the checker must tolerate whitespace/markdown inside the marker span or the marker convention must forbid it (decided in DECISIONS D002: forbid — the marker wraps only the number).

## Acceptance criteria

- AC-001: With the repository in its current (fixed) state plus markers added, `scripts/check-consistency.sh` exits 0.
- AC-002: Removing (or renaming) a shipped skill, hook variant, template, or agent makes the script exit 1 and name the missing item and the profile that ships it. (FR-001..004)
- AC-003: Adding an unreferenced skill directory, hook pair, template file, or agent file makes the script exit 1 naming the orphan. (FR-005)
- AC-004: Creating a file for a `planned*` item (e.g. `hooks/messaging-review-reminder.sh`) makes the script exit 1 telling the maintainer to promote it in `profiles.json`. (FR-006)
- AC-005: Referencing a nonexistent hook in either settings template, or wiring `maven-compile` and `java-build-test-guard` together, makes the script exit 1. (FR-007)
- AC-006: Changing a marked README count to a wrong number makes the script exit 1 showing expected vs found. (FR-008)
- AC-007: Deleting one variant of an unshipped hook pair makes the script exit 1. (FR-009)
- AC-008: The GitHub Actions workflow runs the script on push and PR to `main` and reports failure when the script fails. (FR-010)
- AC-009: Corrupting `profiles.json` (invalid JSON) makes the script exit 1 with a parse error message, not a stack trace.
- AC-010: Running with `--fix` flag auto-corrects README count markers to match computed values and reports `[FIXED] readme key — updated from N to M`. All non-auto-fixable violations (orphans, missing shipped, planned drift, hook pairs, wiring) are still detected and reported; if any exist, the script exits 1 without modifying README. (FR-011)

## Test scenarios

- Unit: not applicable as a separate suite — the script is its own integration surface.
- Integration: `scripts/check-consistency.test.sh` runs the checker against (a) the real repo (expects 0) and (b) a temp copy of the repo with each drift class injected (expects 1 and the right message per class, covering AC-002..007 and AC-009).
- E2E: first CI run on GitHub after push (AC-008), verified manually on the Actions tab.
- Manual: run locally via Git Bash on Windows to confirm cross-platform behavior.

## Assumptions

- GitHub Actions is the CI platform (remote is `github.com/manujc00005/spec-driven-development`).
- python3 and bash are acceptable dependencies (already required by `install.sh`).
- One bash script (no `.ps1` twin) is acceptable for repo-maintenance tooling, unlike shipped hooks which require pairs — recorded in DECISIONS D001.
- The marker convention for README counts is acceptable to the maintainer — recorded in DECISIONS D002.

## Open questions

- None blocking.
