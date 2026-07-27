# Tasks: Security agent hardening and self-contained routing

## Phase 1: Agent

- [x] T001 - Rewrite `agents/security-reviewer.md`: vulnerability taxonomy, attack-anticipation
  method, RGPD/LOPDGDD/AEPD ownership via `privacy-compliance-review`; tools and read-only
  boundaries unchanged. Covers: AC-003.

## Phase 2: Skill routing

- [x] T002 - `skills/security-review/SKILL.md`: delegation section targets `security-reviewer`
  (RGPD trigger list → same agent applies `privacy-compliance-review`); fallback checklist kept
  with honest availability note. Covers: AC-001, AC-002.
- [x] T003 - `skills/privacy-compliance-review/SKILL.md`: delegation section targets
  `security-reviewer`; fallback kept. Covers: AC-001, AC-002.

## Phase 3: Unification (D004)

- [x] T006 - Absorb the stopgap `software-security-review`'s unique disciplines into the agent
  (source-to-sink Confirmed/Potential, structural verification, plausibility filter, public-token
  rule, third-party minimization, erasure propagation, paid-downstream rate limiting); then retire
  the stopgap from `~/.claude-config/skills/` via timestamped backup move. Covers: AC-005.

## Phase 4: Docs

- [x] T004 - CHANGELOG Unreleased entry (spec 020). Covers: AC-001..003 (documentation).

## Phase 5: Verification

- [x] T005 - `grep -rn "gdpr-spain" skills/` empty; no bare `security` agent delegation remains;
  `bash scripts/check-consistency.sh` exit 0. Covers: AC-001, AC-004.
