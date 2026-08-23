# Tasks: python-sql-data-profile

## Phase 1: Preparation

- [x] T001 - Claim a free spec number: list `specs/features/`, `git fetch --all`, confirm 025-028
  are taken and 029 is free on both local and remote. Covers: D007.
- [x] T002 - Read `scripts/check-consistency.sh` and record the exact contract new skills and the
  new profile must satisfy (contract keys, enums, description cap, body cap, routing rules), so
  authoring targets known rules. Covers: AC-003, AC-004, AC-005, AC-009.
- [x] T003 - Read `profiles.json` shape references (`delivery-operations`, `payments-fintech`,
  `next-prisma-web`) and settle whether a skill may sit in two `agentRouting` targets. Covers:
  AC-005, D002.
- [x] T004 - Read one shipped reviewer skill (`skills/container-review/SKILL.md`) as the prose and
  output-format reference. Covers: AC-003.
- [x] T005 - Confirm `agents/domain-reviewer.md` needs no change, and that no shipped profile
  updated `agents/` when it added reviewers. Covers: AC-010, FR-015.
- [x] T006 - Baseline: run `bash scripts/check-consistency.sh` on the clean tree and record exit 0.
  Covers: AC-011.

## Phase 2: Implementation

- [x] T007 - Write `skills/python-reviewer/SKILL.md` — typing, module structure, function size,
  logic/IO/config separation, exceptions and silent failure, logging, `pathlib`, dataclasses,
  pydantic where already used, context managers, import-time side effects, configuration,
  dependencies. Contract: `primary_agent: domain-reviewer`,
  `secondary_agents: [security-reviewer]`. Covers: AC-002, AC-003, AC-004, AC-005, FR-002, FR-007,
  FR-008, FR-010.
- [x] T008 - Write `skills/sql-query-reviewer/SKILL.md` — fan-out and duplicates, `NULL` semantics,
  outer joins collapsed by `WHERE`, filters and date boundaries, `GROUP BY`/`HAVING`, window
  functions, CTEs, subqueries, readability that affects correctness, parameterization versus
  interpolation. Contract: `secondary_agents: [security-reviewer]`. Covers: AC-002..005, FR-003,
  FR-007, FR-008, FR-010, D003.
- [x] T009 - Write `skills/database-performance-reviewer/SKILL.md` — N+1, result set size,
  pagination, index coverage, the write cost of a new index, cardinality, locks and transactions,
  batch size, materialized views, connections. Contract: `secondary_agents: []`. Covers: AC-002,
  AC-003, AC-004, FR-004, FR-007, FR-010, D004.
- [x] T010 - Write `skills/data-pipeline-reviewer/SKILL.md` — idempotency, partial failure,
  retries, duplicates, incremental watermarks and late-arriving rows, timestamps and timezones,
  input/output contracts, file formats, validation, traceability, reconciliation, sensitive data.
  Contract: `secondary_agents: [security-reviewer]`. Covers: AC-002..005, FR-005, FR-007, FR-008,
  FR-010.
- [x] T011 - Write `skills/python-testing-reviewer/SKILL.md` — assertions that cannot fail,
  determinism, isolation, fixtures, mocks and patch location, parametrization, edge cases, testing
  scripts, testing SQL, test data, suite hygiene. Contract: `secondary_agents: []`. Covers:
  AC-002, AC-003, AC-004, FR-006, FR-007, FR-010.
- [x] T012 - Add the `python-sql-data` profile object to `profiles.json` before
  `blockchain-crypto`: description, `default: false`, five skills, `agentRouting` under
  `domain-reviewer` with the secondary-consumption note, empty hooks/templates, and a scope `note`.
  Covers: AC-001, AC-002, FR-001, FR-009, D002.
- [x] T013 - Run `bash scripts/check-consistency.sh` and confirm the only failures are README
  counts — any routing or contract failure here means the previous tasks are wrong. Covers: AC-009.

## Phase 3: Documentation

- [x] T014 - Write `docs/PYTHON_SQL_PROFILE.md`: purpose, what it reviews, agent routing, what it
  does not replace, recommended workflow, example review questions. Covers: AC-006, FR-011.
- [x] T015 - Add the profile row to the README profile table, a row to the current-support table,
  and the profile name to the totals row. Keep it brief. Covers: AC-007, FR-012.
- [x] T016 - Add the `[Unreleased] / Added` CHANGELOG entries: profile, five skills, and the
  scope/non-replacement statement. Covers: AC-008, FR-013.
- [x] T017 - Add the not-ported row to `adapters/codex/PARITY.md` and correct the six stale
  hardcoded "65 skills" claims. Covers: D008, D009.
- [x] T018 - Run `bash scripts/check-consistency.sh --fix` to update README count markers and
  shields badges. Covers: AC-007.

## Phase 4: Review

- [x] T019 - Run `bash scripts/check-consistency.sh` → exit 0. Covers: AC-009, AC-011.
- [x] T020 - Run `python3 -m json.tool profiles.json` → exit 0. Covers: AC-001, AC-011.
- [x] T021 - Run `bash scripts/check-consistency.test.sh` → the existing suite passes unchanged
  (regression signal that no shipped profile broke). Covers: AC-011.
- [x] T022 - Run the exaggerated-claim grep over `README.md`, `docs/`, `skills/`, `profiles.json`,
  `CHANGELOG.md` and this spec folder; classify every hit as real issue, safe documentation or
  false positive. Covers: NFR (honesty).
- [x] T023 - Confirm `git status` shows nothing new or modified under `agents/`. Covers: AC-010,
  FR-015.
- [x] T023b - Run `bash install.sh --profile python-sql-data --dry-run` and confirm the profile
  resolves and all five skills are reported. Covers: OQ-1 (partially — dry-run only, macOS only).
- [x] T024 - Report: summary, profile, skills, routing, docs, validation, risks, suggested commit
  message. No commit, no push, no staging.

## Deferred (not this feature)

- [x] T025 - **Verified 2026-08-23.** macOS: real install into a temp central dir, exit 0,
  all five skills present and byte-identical to the repo, profile recorded in the manifest,
  re-run byte-identical. Windows: covered by CI, not by a spot-check — `scripts/install.test.ps1`
  installs `-Profile python-sql-data` on the `windows-latest` runner on every PR (spec 034 D005).
  Original text: Writing install verification: `./install.sh --profile python-sql-data` (without
  `--dry-run`) on macOS, and `install.ps1 -Profile python-sql-data` on Windows. Covers: OQ-1.
  **The Windows half requires a human on a Windows machine; not closable from this session.**
- [ ] T026 - Calibration pass: run all five skills against a real Python + SQL diff and adjust the
  **DEFERRED at close (2026-08-23) → DEBT-004.** Calibration needs a real Python + SQL
  diff from live work; no acceptance criterion depends on it. Tracked in
  `docs/KNOWN_DEBT.md` rather than holding a conformant spec open indefinitely.
  checklists from what they actually caught and missed. Covers: OQ-2.
- [ ] T027 - Guard the hardcoded skill counts in `adapters/` and `docs/` that
  **SKIPPED at close (2026-08-23) → DEBT-005.** Its own text says "Framework-wide change,
  deliberately out of scope here". Skipped for this spec, not dropped: tracked as debt.
  `check-consistency.sh` does not cover today, or record them in `docs/KNOWN_DEBT.md`. Covers:
  D009 consequences. **Framework-wide change, deliberately out of scope here.**
