# Plan: Phase 0 — Publish-ready baseline

## Approach

Six independent deliverables, all additive (new files or safe edits to README). No deletions, no
moves, no dependency installs. Order doesn't matter — implemented in one pass.

## Files to CREATE

| File | Purpose | AC |
|---|---|---|
| `LICENSE` | MIT license | AC-001 |
| `hooks/git-guardrails.sh` | Cross-platform parity for destructive-git blocking | AC-003 |
| `specs/_templates/PR_DESCRIPTION.md` | Template for PR descriptions | AC-004 |
| `specs/_templates/REVIEW_REPORT_TEMPLATE.md` | Common review output format | AC-005 |
| `profiles.json` | Manifest mapping profiles → skills/hooks/templates | AC-006 |

## Files to MODIFY

| File | Change | AC |
|---|---|---|
| `README.md` | Fix stale "not yet" for INSTALL.md; add profile/build-tool note; keep Graphify planned; note blockchain disabled | AC-002 |

## Files NOT touched

- `C:\ProgramData\ClaudeConfig\*`
- `settings.local.json` (any location)
- Any existing skill `SKILL.md`
- `install.ps1` / `install.sh` / `link-project.*` (profile flag comes in Phase 2)
- `settings.template.json`

## Risks

- README edit must not break existing Mermaid diagrams or link anchors.
- `git-guardrails.sh` must handle stdin JSON from Claude Code the same way as `.ps1` (pipe → parse → match → exit code).
- `profiles.json` is declarative only at this phase — installer doesn't consume it yet (Phase 2).

## Verification

- `bash -n hooks/git-guardrails.sh` (syntax check).
- `grep` for secrets/PII across all new/modified files.
- `git status` + `git diff` for author review before commit.
