# Decisions: audit-closure-and-ci-hardening

## Decision log

### D001 - shellcheck at severity error only

**Date:** 2026-07-17

**Status:** Accepted

**Context:** The codebase has no shellcheck history; full-severity runs produce
style noise that would either block CI or push toward blanket disables.

**Decision:** CI runs `shellcheck -S error`. Verified clean locally (0.11.0,
via ephemeral npx) before wiring. Style-level adoption deferred to roadmap.

**Reasoning:** Error-severity findings are near-certain real bugs; style debates
should not gate an audit-closure commit.

**Consequences:** Some legitimate warnings stay invisible in CI until severity
is raised deliberately.

### D002 - Windows CI job parses, never executes

**Date:** 2026-07-17

**Status:** Accepted

**Context:** sh/ps1 parity was review-only; behavioral hook tests on a bare
runner would need a fake project context and Windows-specific fixtures.

**Decision:** The Windows job runs the PowerShell language parser over every
shipped `.ps1` and fails on parse errors. No hook execution.

**Reasoning:** Parse-gating converts the parity claim from "reviewed" to
"machine-checked" at near-zero cost and zero flakiness; behavioral Windows
tests are a separate, larger investment.

**Consequences:** Windows behavior (vs syntax) remains verified by review.

### D003 - Badges become harness-enforced, reusing the marker fix rule

**Date:** 2026-07-17

**Status:** Accepted

**Context:** Badges drifted once already; they duplicate five counts the
harness already computes.

**Decision:** New `readme-badge` error category for the five total badges,
auto-fixed by `--fix` under the same safety rule as markers (only when no
non-README violations exist).

**Reasoning:** Same source of truth, same mechanism, no new moving parts.

**Consequences:** CI now fails on badge drift (stricter than before — intended).
