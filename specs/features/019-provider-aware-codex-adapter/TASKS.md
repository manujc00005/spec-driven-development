# Tasks: Provider-aware architecture and Codex adapter

## Phase 1: Core architecture documentation

- [x] T001 - Write `docs/PROVIDER_ADAPTERS.md`: SDD Core vs adapters, honesty principle, how a
  provider maps on. Covers: AC-001.
- [x] T002 - Write `adapters/README.md`: adapter registry + capability/honesty matrix. Covers: AC-002.
- [x] T003 - Write `adapters/claude/README.md`: pointer to the shipped root, no files moved. Covers:
  AC-003.

## Phase 2: Codex adapter

- [x] T004 - Write `adapters/codex/AGENTS.md`: provider-neutral SDD operating guide (lifecycle,
  gates, agent roles, guardrails as conventions). Covers: AC-004, AC-005.
- [x] T005 - Write `adapters/codex/prompts/` lifecycle spine (create/plan/analyze/implement/review/
  close/guardrails) + `prompts/README.md` index, each derived from its core skill. Covers: AC-004.
- [x] T006 - Write `adapters/codex/PARITY.md`: Codex capability matrix incl. explicit "does NOT carry
  over" section. Covers: AC-005.
- [x] T007 - Write `adapters/codex/config.example.toml` (labeled example) and
  `adapters/codex/README.md` (purpose, verification status, install/use, limitations). Covers:
  AC-004, AC-005.
- [x] T008 - Write `adapters/codex/install-codex.sh` + `install-codex.ps1`: copy-only, dry-run,
  idempotent, backups, adapter-scoped. Covers: AC-004, AC-006.

## Phase 3: Repository integration (additive)

- [x] T009 - Add honest "Provider adapters" coverage to `README.md` (Current-support row, dedicated
  subsection, architecture tree, quickstart, installation table, shipped list, roadmap) and a
  dedicated "Provider adapters" section to `docs/INSTALL.md`; change no `<!-- count:* -->` marker or
  badge. Covers: AC-009.

- [x] T012 - Add root-level `install-all.sh` + `install-all.ps1`: thin wrapper calling both
  installers in order, flag passthrough, `--skip-*`, fail-fast on Claude error. No change to
  `install.sh`/`install.ps1`. Covers: AC-010. **Verified:** dry-run both wrote nothing;
  `--skip-claude`/`--skip-codex` isolate each side; unknown flag → exit 1; syntax check clean.

- [x] T013 - Harden `AGENTS.md` targeting (D007): install only with explicit `--target`/`-Target`,
  refuse the framework repo root, skip-with-message otherwise; wrapper mirrors it; docs updated
  (codex README, `docs/INSTALL.md`, main README). Remove the stray committed root `AGENTS.md`.
  Covers: AC-011. **Verified:** no-target skips (repo clean); framework-root refused; explicit
  project target installs; `install-all` no-`--codex-target` writes no `AGENTS.md`.

## Phase 4: Verification

- [x] T010 - Run `adapters/codex/install-codex.sh --dry-run` and a real+repeat run into a temp dir;
  assert no-write dry-run, idempotent re-run, backup-on-overwrite. Covers: AC-006. **Verified:**
  dry-run wrote nothing; real run copied AGENTS.md + 8 prompt files; re-run all `[skip] identical`;
  differing file skipped without `--force`, backed up to `.bak-<ts>` and overwritten with `--force`.
- [x] T011 - Run `bash scripts/check-consistency.sh` (exit 0) and audit `git status` against AC-007
  (no Claude installer/manifest/skill/agent/hook file touched). Covers: AC-007, AC-008. **Verified:**
  consistency check exit 0; only `README.md` modified (additive); `profiles.json`, installers,
  wire-hooks, settings templates, and all `skills/`/`agents/`/`hooks/` files untouched.
