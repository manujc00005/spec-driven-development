# Tasks: CI Consistency Check

## Phase 1: Preparation

- [x] T001 - Create `scripts/` directory and the python3 inventory extractor inside `check-consistency.sh`: parse `profiles.json`, emit flat inventory (category, item, profile, shipped|planned) and computed de-duplicated counts; fail cleanly on invalid JSON. Covers: AC-009 (partial groundwork for all others).

## Phase 2: Implementation

- [x] T002 - Shipped-item existence checks: skills (`skills/<name>/SKILL.md`), hooks (both `.sh` + `.ps1`), templates (`specs/_templates/` then `docs/_templates/`), agents (`agents/<name>.md`). Covers: AC-002.
- [x] T003 - Reverse checks: orphan detection for skills/hook families/templates/agents (with `lib/` and `README.md` exclusions), planned-item-exists-on-disk detection, shipped∩planned overlap, hook `.sh`/`.ps1` parity for all families, disabled-profile-ships-nothing. Covers: AC-003, AC-004, AC-007.
- [x] T004 - Settings wiring checks: extract hook paths from `settings.template.json` and `settings.template.sh.json`, verify each resolves into `hooks/`, enforce `maven-compile` ⊕ `java-build-test-guard` exclusion per file. Covers: AC-005.
- [x] T005 - README count markers: add `<!-- count:<key> -->N<!-- /count -->` markers to the headline counts and profile-table counts in `README.md`; implement marker parsing + comparison + required-marker enforcement in the checker; add a short CI section to README. Covers: AC-006, AC-001 (partial).
- [x] T006 - Report format and exit codes: one line per violation, summary line, exit 0/1/2 semantics; run checker against the real repo and fix any true drift it finds until it exits 0. Covers: AC-001.

## Phase 3: Tests

- [x] T007 - `scripts/check-consistency.test.sh`: temp-copy mutation harness with one case per drift class (missing shipped item ×4 categories, orphan ×4, planned-on-disk, bad settings wiring, forbidden hook pair, wrong marker count, missing hook variant, corrupt JSON), asserting exit codes and message content. Covers: AC-002..007, AC-009.

## Phase 4: Review

- [x] T008 - `.github/workflows/consistency.yml`: push/PR to `main`, ubuntu-latest, `contents: read`, run checker then self-test; verify the first run on the Actions tab after push. Covers: AC-008. (Workflow authored and locally validated; the live Actions-tab verification requires an actual push — pending, see implementation summary.)
