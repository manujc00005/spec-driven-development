# Feature Spec: audit-closure-and-ci-hardening

## Status

Done

## Problem

A full repo audit (2026-07-17) found no P0 bugs but four actionable gaps:

1. CI runs only the consistency harness — the 66-case Graphify suite
   (`scripts/graphify.test.sh`) is not executed, so regressions in hooks or
   `setup-graphify` would pass CI green. `.ps1` files are never syntax-checked
   anywhere (no local pwsh, no Windows CI), so the advertised sh/ps1 parity is
   review-only. Shell scripts have no static analysis beyond `bash -n`.
2. The only worked example is numbered `002-payment-webhook-idempotency` with
   no `001`, which reads as a missing example to outside visitors.
3. Spec 006 records its status in YAML frontmatter (`status: Done`) while every
   other spec uses the standard `## Status` section — tooling that greps the
   section (e.g. `/spec-status`) misses it.
4. The shields.io badges in README.md are hand-maintained while the count
   markers are harness-enforced; badges already drifted once and were fixed by
   hand during the 008/011 merge.

## Goal

Close all four gaps: CI executes the Graphify suite, shellcheck (severity
error), and a Windows job that parses every `.ps1`; the example is renumbered
to `001` with all links updated; spec 006 uses the standard status section; the
consistency harness checks the five total-count badges and `--fix` syncs them.

## Non-goals

- New examples, CONTRIBUTING.md, releases, or token-saving metrics (roadmap
  horizons 2–3, separate features).
- Shellcheck style-level warnings (only `-S error`; the codebase passes it
  today — verified locally with shellcheck 0.11.0).
- Running behavioral hook tests on Windows (parse-only parity gate for now).

## Functional requirements

- FR-001: `.github/workflows/consistency.yml` runs `scripts/graphify.test.sh`
  on ubuntu, `shellcheck -S error` over all repo shell scripts, and a
  `windows-latest` job that parses every `hooks/*.ps1` and `scripts/*.ps1`
  (plus `install.ps1`/`link-project.ps1`) with the PowerShell language parser,
  failing on any parse error.
- FR-002: `examples/002-payment-webhook-idempotency/` becomes
  `examples/001-payment-webhook-idempotency/` via `git mv`; every reference in
  `README.md` and `examples/README.md` is updated; no stale `002-` references
  remain outside git history.
- FR-003: Spec 006 gains the standard `## Status` / `Done` section and the
  redundant `status:` frontmatter key is removed (other frontmatter keys stay).
- FR-004: `check-consistency.sh` validates the five total badges
  (skills, hook families, templates, agents, profiles) against computed counts,
  reports drift as auto-fixable `readme-badge` errors, and `--fix` rewrites
  them; the self-test gains a badge-drift mutation case.

## Acceptance criteria

- AC-001: Workflow YAML contains the three new steps/jobs; local equivalents
  pass (`graphify.test.sh` 66/66, `shellcheck -S error` clean, ps1 parity by
  review until CI runs).
- AC-002: `grep -rn "002-payment" --include="*.md" .` returns nothing outside
  `.git/` and this spec's own description of the rename; the renamed folder
  retains full history (`git log --follow`).
- AC-003: `grep -A2 "## Status" specs/features/006-*/SPEC.md` returns `Done`;
  frontmatter no longer contains `status:`.
- AC-004: Mutating a badge number makes `check-consistency.sh` exit 1 and
  `--fix` restore it (covered by a new self-test case); full harness and
  self-test suites pass.

## Edge cases

- Badge fix must reuse the marker-fix safety rule: only auto-fix when no
  non-README violations exist.
- The Windows job must not execute hooks (parse only) — hooks assume a project
  context that does not exist on a bare runner.

## Test scenarios

- Unit: new badge-drift case in `check-consistency.test.sh`.
- Integration: full harness + graphify suite + self-test locally; CI proves the
  rest on the next push.

## Assumptions

- `shellcheck` and `pwsh` are preinstalled on GitHub-hosted runners
  (documented runner images); no dependency installation needed in CI.
- Renaming the example is safe: the repo is young and external deep links to
  the `002-` path are unlikely; git history is preserved via rename detection.

## Open questions

- None.
