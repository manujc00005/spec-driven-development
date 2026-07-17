# Implementation Plan: audit-closure-and-ci-hardening

## Summary

Four independent blocks, one commit each: (1) CI hardening — graphify suite +
shellcheck + Windows ps1-parse jobs; (2) example renumber 002→001 with link
updates; (3) spec 006 status normalization; (4) badge validation/sync in the
consistency harness with a self-test case. Closes the 2026-07-17 audit.

## Related spec

`specs/features/012-audit-closure-and-ci-hardening/SPEC.md`

## Impacted areas

`.github/workflows/consistency.yml` · `examples/` + `README.md` links ·
`specs/features/006-*/SPEC.md` · `scripts/check-consistency.sh` + `.test.sh`

## Proposed approach

Per the spec's FRs. Badge check mirrors the marker mechanism: same computed
counts, same "auto-fix only when no non-README violations" safety rule, new
`readme-badge` error category. Windows job uses the PowerShell language parser
(no execution). shellcheck pinned to `-S error` — verified clean locally with
0.11.0 before wiring into CI.

## Alternatives considered

- Keeping example numbering with an explanatory note — rejected: renaming is
  cheaper than permanently explaining a gap, and the repo is young.
- Full shellcheck (style warnings) — rejected for now: noise without a
  suppression policy; revisit as roadmap polish.

## Dependencies

GitHub-hosted runner images (shellcheck, pwsh preinstalled). None locally.

## Risks

- CI-only steps can't be fully proven locally (Windows parse) — first push
  validates; parse-only job keeps blast radius near zero.
- Badge regexes must not touch non-total badges (CI badge etc.) — patterns
  anchored to the five known slugs only.

## Test strategy

New badge-drift mutation case in `check-consistency.test.sh`; full local run of
harness + self-test + graphify suite + shellcheck before push.

## Rollback strategy

Each block is one revertable commit. CI changes are additive jobs — deleting a
job restores prior behavior.

## PLAN verification checklist

- [x] The plan covers all acceptance criteria.
- [x] The plan avoids behavior outside the spec.
- [x] Risks are documented.
- [x] Test strategy is documented.
- [x] Rollback strategy is documented.
- [x] SPEC.md status is In Progress.
