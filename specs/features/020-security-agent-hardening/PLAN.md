# Implementation Plan: Security agent hardening and self-contained routing

## Summary

Reroute `security-review` and `privacy-compliance-review` delegation prose from the unshipped
`security`/`gdpr-spain` agents to the shipped `security-reviewer`, and upgrade
`agents/security-reviewer.md` with an explicit vulnerability taxonomy, an attack-anticipation
method, and RGPD/LOPDGDD/AEPD ownership. Markdown-only; no manifest, installer, or hook changes.

## Related spec

`specs/features/020-security-agent-hardening/SPEC.md`

## Impacted areas

- `agents/security-reviewer.md` (rewrite: taxonomy + method + RGPD; tools/boundaries unchanged)
- `skills/security-review/SKILL.md` (delegation section only)
- `skills/privacy-compliance-review/SKILL.md` (delegation section only)
- `CHANGELOG.md` (Unreleased entry)
- **Untouched:** `profiles.json`, installers, hooks, all other skills/agents.

## Proposed approach

1. Rewrite the agent file: keep frontmatter shape (`name`/`description`/`tools`), extend the
   description; add Vulnerability taxonomy, Attack anticipation, and RGPD sections; keep
   Allowed/Forbidden, Stop conditions, SDD boundaries, output format.
2. Replace each skill's delegation block: target `security-reviewer`; keep the RGPD trigger list
   (in `security-review`) as the condition for instructing the agent to also apply
   `privacy-compliance-review`; keep the inline checklist fallback with an honest availability
   note (install + new session).
3. CHANGELOG entry under Unreleased.
4. Verify: greps (AC-001/002), agent content (AC-003), `check-consistency.sh` (AC-004).

## Alternatives considered

- Ship `security`/`gdpr-spain` agent files matching the old prose — rejected (D001, 018 D006/D008).
- Move the RGPD checklist into the agent — rejected (D002; skills carry capability).
- Import the user's central-dir `software-security-review` stopgap into the repo — rejected; the
  routing fix removes its reason to exist, and it would duplicate `security-review`.

## Dependencies

None (markdown only).

## Risks

- **R-1 (Low): prose/contract mismatch.** Contracts already say `primary_agent: security-reviewer`;
  after the edit prose and contract agree. Verified by grep + harness.
- **R-2 (Low): overclaiming.** Mitigated by D003 (no scanner/pentest claims) and review of the
  final text.

## Test strategy

Manual read against AC-001..003; `bash scripts/check-consistency.sh` for AC-004; `grep -rn
"gdpr-spain" skills/` must be empty.

## Rollback strategy

Revert the three markdown files (git); no state, no installers involved.

## PLAN verification checklist

- [x] The plan covers all acceptance criteria.
- [x] The plan avoids behavior outside the spec.
- [x] Risks are documented.
- [x] Test strategy is documented.
- [x] Rollback strategy is documented.
- [x] SPEC.md status updated (`Ready` → `In Progress` at implementation start).
