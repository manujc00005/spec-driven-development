# Implementation Summary: project-scaffolding-parity

## Overview

Any project initialized with `/project-init` now gets the full, identical `specs/` structure (CONSTITUTION + README + SDD-GUARDRAILS + CLAUDE-SDD + features/), and hook wiring has a supported one-command path instead of an undocumented manual merge.

**Status:** Complete — 2026-07-16

## What was built

- **Templates** (`specs/_templates/`): `SPECS-README.md`, `SDD-GUARDRAILS.md` (generic instance of the sdd-guardrails doctrine), `CLAUDE-SDD.md` (domain review triggers skeleton). Registered in the `core` profile (12 → 15 core templates).
- **`/project-init`**: scaffolds and fills all four `specs/` support files from its interview; output and description updated.
- **`scripts/wire-hooks.sh` / `wire-hooks.ps1`**: additive, idempotent merge of the platform settings template's `hooks` key into `<project>/.claude/settings.json`; backup before write; `--dry-run`; never touches `settings.local.json`.
- **Installers**: `install.sh`/`install.ps1` now also copy `settings.template.sh.json` (previously never installed); final NOTE points at wire-hooks; `link-project.sh`/`.ps1` print the same hint.
- **`/sdd`**: bootstrap check — uninitialized project (no `specs/CONSTITUTION.md`) → recommend `/project-init` before anything else.
- **`docs/INSTALL.md`**: new "Wiring hooks into a project" section; script table extended.

## Verification

- `wire-hooks.sh` against temp projects: fresh project (settings created with only `hooks`), pre-existing settings with foreign keys and a custom hook (preserved, deduped, no duplicates across 8 wired commands), second run is a no-op, exactly one backup (AC-002, AC-003).
- `install.sh --dry-run` lists `settings.template.sh.json` (AC-004).
- `check-consistency.sh` passes; README markers auto-fixed via `--fix` (templates-total 17 → 20).
- `check-consistency.test.sh`: 22 passed, 0 failed.

## Out-of-scope fixes made along the way (pre-existing bugs found by T008)

The consistency test harness had never passed on macOS and had drifted:

1. `scripts/check-consistency.sh` / `.test.sh` lacked the executable bit (harness invokes the checker directly → exit 126).
2. Seven `sed -i` calls used GNU-only syntax (BSD sed on macOS fails, mutations silently skipped) — replaced with a portable `sed_inplace` helper.
3. `shipped-skill-missing-skillmd` never registered the fake skill in `profiles.json`, so it asserted nothing on any OS.
4. Marker assertions grepped all numbers on multi-marker README lines; `fix-readme-marker` hardcoded a stale hook-families count (12 vs 11).

## Pending / follow-ups

- Windows counterpart `wire-hooks.ps1` written to mirror the `.sh` behavior but only exercised by review, not by an automated test (no Windows environment here).
- Existing projects are not retrofitted automatically; run `/project-init` in them to fill the gaps.
