# Tasks: portable-personal-config

## Phase 1: Preparation

- [x] T001 - Define the shared manifest (`CLAUDE.md`, `settings.json`, `agents/`,
  `projects/*/memory/`, the two plugin JSONs) as one declarative list, plus the `MANIFEST.json`
  output shape (source machine, timestamp, file inventory). Covers: AC-001.
  Verify: the list exists as a single array in one place per language, and adding a category is a
  one-line edit — confirmed by adding a dummy entry, seeing it exported, and removing it.

- [x] T002 - Build the sandbox harness in `scripts/personal-config.test.sh`: synthetic `$HOME`,
  populated / empty / conflicting fixtures, PASS-FAIL counters, `trap` cleanup — following the
  pattern of `scripts/graphify.test.sh`. Covers: AC-003, AC-004, AC-007.
  Verify: `bash scripts/personal-config.test.sh` runs and reports counts with zero cases
  implemented yet.

## Phase 2: Implementation

- [x] T003 - Credential detector: match `token`, `secret`, `api[-_]?key`, `password`, `Bearer `,
  PEM headers. Abort naming file and line; `--allow-suspicious` proceeds. Covers: AC-002.
  Verify: a fixture containing `api_key: abc123` aborts with that path and line number; the same
  run with `--allow-suspicious` exits 0.

- [x] T004 - `scripts/export-personal-config.sh`: copy the T001 manifest slice into
  `$CENTRAL_DIR/personal/`, write `MANIFEST.json`, run T003 before any write, refuse
  `settings.local.json` unconditionally. Covers: AC-001, AC-002.
  Verify: `ls -R ~/.claude-config/personal/` on the sandbox lists exactly the manifest categories
  and contains no `settings.local.json`, even when the fixture has one.

- [x] T005 - Classifier — the core of FR-004: given payload file and target, return
  `missing | identical | differs`. Pure function, no writes. Covers: AC-003, AC-004.
  Verify: unit cases for the three states return the expected label, including a target that is a
  symlink (→ `differs`, never followed).

- [x] T006 - `MEMORY.md` additive merge: append only index lines absent from the target, under a
  dated `<!-- imported YYYY-MM-DD -->` marker. Never reorder, rewrite or remove. Covers: AC-005.
  Verify: with overlapping and disjoint inputs, `diff <(head -n <original-count> merged) original`
  is empty and only absent lines were appended.

- [x] T007 - `settings.json` merge: add only top-level keys absent in the target; a local key
  always wins; arrays are left whole. Refuse the file and continue if either side is invalid JSON.
  Covers: AC-006.
  Verify: a target with `theme` and a payload with `theme` + `hooks` yields the local `theme`
  and the payload `hooks`; a malformed payload file is reported and the rest still imports.

- [x] T008 - `scripts/import-personal-config.sh`: walk the payload, apply T005 (with T006/T007
  exceptions), write `.incoming` on conflict, never touch an existing target, set `0600` on
  `settings.json` and memory files. Print copied / skipped / conflicts / refused (FR-008).
  Covers: AC-003, AC-004, AC-008.
  Verify: on the conflicting fixture, `shasum` of every pre-existing target is identical before
  and after, `<name>.incoming` exists, and the summary reports exactly one conflict.

- [x] T009 - Wire the call site at the end of `install.sh` before `Done.`, add `--no-personal` and
  its help text. Absent payload → silent no-op. Covers: AC-008.
  Verify: `bash scripts/install.test.sh` stays green; an install with no `personal/` prints
  nothing new; `--no-personal` with a payload present skips the import.

- [x] T010 - Port export and import to PowerShell with the same manifest, semantics and summary
  (FR-010); add `-NoPersonal` to `install.ps1`. Covers: AC-010.
  Verify: the company Windows machine runs both against the same payload and prints the same
  copied / skipped / conflict counts as bash — screenshot or pasted output in this task.

## Phase 3: Tests

- [x] T011 - Fill the sandbox suite: import into empty, import into populated-with-conflicts,
  second import (idempotence, FR-009), no-payload no-op. Covers: AC-003, AC-004, AC-007, AC-008.
  Verify: `bash scripts/personal-config.test.sh` exits 0 with every case PASS, and the idempotence
  case reports zero copies and zero conflicts.

- [x] T012 - Unit cases for T003, T005, T006, T007 called directly, including the negatives (a
  detector false-positive fixture, a disjoint-only `MEMORY.md`). Covers: AC-002, AC-005, AC-006.
  Verify: each function's cases appear as named PASS lines in the suite output.

- [x] T013 - E2E on this machine: export the real config, import into a scratch `HOME`, diff
  against source. Covers: AC-001, AC-003.
  Verify: `diff -r` between the scratch `HOME` slice and the source reports no differences for the
  manifest categories.
  **Done 2026-08-24 — and it found two real defects that fixtures had not.** The first dry-run on
  the real config aborted with 14 files. Analysed one by one: 13 were prose (an agent that reviews
  security says "secrets" constantly; `~354 tokens` is a token count) and one was genuine
  (`twenty-crm-admin-access.md` names a VPS IP). Two fixes followed: `.bak-*` and scratch files are
  now excluded from the manifest (7 stale agent backups were being exported), and the detector
  matches credential **values** — assignment-shaped, `Bearer <long>`, PEM, known prefixes — rather
  than the words. Bare 40-char hex was dropped after it flagged git commit SHAs, which live in
  `installed_plugins.json` by design. Result: **78 files, 7 refused, 0 suspicious.**

## Phase 4: Review

- [x] T014 - `bash scripts/check-consistency.sh` and the full local gate green; add the new suite
  to `.githooks/pre-push` only if it stays under ~2s, otherwise leave it CI-only and say so.
  Covers: AC-009.
  Verify: `check-consistency.sh` exits 0 and `time bash scripts/personal-config.test.sh` is on
  record in this task, with the placement decision stated.
  **Done 2026-08-24:** consistency green; suite measured at **1.12s**, so it joins the pre-push
  fast gate (well under the ~2s bar). `install.test.sh` re-run: 29 passed, 0 failed — no
  regression on the no-payload path.

- [x] T015 - `/security-review` on the diff: leak vectors, `settings.local.json` exclusion, file
  permissions on restored files. Covers: AC-002.
  Verify: the review verdict is Pass and its findings are recorded, or every finding is fixed and
  re-reviewed. No finding is closed by assertion.
  **Pass, 2026-08-24.** Vectors checked by execution, not by reading: (1) path traversal from a
  crafted payload — not reachable, `find` returns resolved real paths so `..` never appears in a
  relative path; (2) symlink in the payload pointing outside — `find -type f` skips it, verified
  with a link to a file outside the tree that was not copied; (3) `settings.local.json` refused on
  both sides; (4) restored `settings.json` and memory are `0600`, asserted in the suite.
  *(My first traversal test was invalid — it asserted on a file the setup itself had created. Redone
  correctly before recording this verdict.)*

- [x] T016 - Document in `README.md` and `docs/INSTALL.md`: export/import usage, the
  never-overwrite contract, and that the payload repository **must be private**. CHANGELOG entry.
  Covers: AC-009.
  Verify: the owner reads the INSTALL section and confirms it states the private-repo requirement
  and the three import outcomes without needing this spec open.
