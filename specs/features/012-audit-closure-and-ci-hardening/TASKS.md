# Tasks: audit-closure-and-ci-hardening

## Phase 1: Implementation (one commit per block)

- [x] T001 - CI hardening: graphify suite step, shellcheck job (`-S error`), Windows ps1-parse job in `.github/workflows/consistency.yml`. Covers: AC-001.
- [x] T002 - Renumber example `002-payment-webhook-idempotency` → `001-...` (git mv) and update all links in `README.md` + `examples/README.md`. Covers: AC-002.
- [x] T003 - Normalize spec 006 status to the standard `## Status` section (drop the frontmatter `status:` key). Covers: AC-003.
- [x] T004 - Badge validation + `--fix` sync in `check-consistency.sh`; badge-drift case in `check-consistency.test.sh`. Covers: AC-004.

## Phase 2: Verification

- [x] T005 - Run full local verification (harness, graphify suite, self-test, shellcheck) and push all pending commits. Covers: all ACs.
