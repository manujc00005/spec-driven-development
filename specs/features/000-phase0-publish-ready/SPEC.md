# Feature Spec: Phase 0 — Publish-ready baseline

## Status

Done

> Closed 2026-07-13 during Phase 5 (`005-framework-hardening-and-cross-platform-polish`).
> Every AC verified against on-disk evidence — see the Verification section in the
> (backfilled) `TASKS.md`. One honesty note: the `.sh` executable bit required by AC-003
> was missing from the git index until the Phase 5 fix (005/D007).

## Problem

The repo is public on GitHub but legally unusable (no LICENSE), has stale README sections that
contradict existing files, lacks cross-platform parity for the most critical safety hook
(`git-guardrails`), and has no output templates for PR descriptions or review reports.

## Goal

Make the repo publishable, legally reusable (MIT), internally coherent, and cross-platform complete
for the safety-critical hook — without touching skills, context layer, or live config.

## Non-goals

- Adding new skills (Phase 2+).
- Graphify integration (Phase 1).
- Installing anything into `C:\ProgramData\ClaudeConfig`.
- Enabling blocking hooks.
- Committing (author reviews and commits manually).

## Functional requirements

- FR-001: Add MIT LICENSE at repo root.
- FR-002: Fix README contradictions re: `docs/INSTALL.md` existence and profile strategy.
- FR-003: Create `hooks/git-guardrails.sh` with parity to `git-guardrails.ps1`.
- FR-004: Create `specs/_templates/PR_DESCRIPTION.md`.
- FR-005: Create `specs/_templates/REVIEW_REPORT_TEMPLATE.md` (common review output format).
- FR-006: Create `profiles.json` manifest declaring all profiles and their skill/hook/template membership.

## Acceptance criteria

- AC-001: `LICENSE` is valid MIT with current year and author name.
- AC-002: README no longer says "Installation guide" is missing; mentions Maven as default build tool for Java profile; Graphify stays `Planned`; blockchain stays `optional disabled`.
- AC-003: `git-guardrails.sh` blocks the same destructive patterns as the `.ps1` variant, exits 0 on safe commands, and is executable (`chmod +x`).
- AC-004: `PR_DESCRIPTION.md` template has Summary, Changes, Tests, Migrations, Risks sections.
- AC-005: `REVIEW_REPORT_TEMPLATE.md` has Verdict, Findings (severity/file:line), Evidence, Actions.
- AC-006: `profiles.json` declares `core`, `java-spring-backend` (default), `messaging-event-driven`, `payments-fintech`, `next-prisma-web`, `blockchain-crypto` (disabled). Maven is primary build tool.
- AC-007: No secrets, PII, or hardcoded local paths in any new/modified file.
