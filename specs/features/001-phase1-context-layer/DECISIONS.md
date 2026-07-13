# Decisions: Phase 1 — Context layer + Graphify integration

> **Backfill note (2026-07-13, Phase 5).** Reconstructed after the fact (005/D006); this
> feature shipped before the repo enforced its full SDD document set.

## Decision log

### D001 — Graphify as optional accelerator, never a dependency (reconstructed)

**Date:** 2026 (Phase 1) · **Status:** Accepted

**Decision:** Every Graphify-aware artifact (3 skills, 1 hook) must degrade gracefully when
`GRAPH_REPORT.md` is absent; nothing fails or blocks because the external tool wasn't run.

**Reasoning (evident):** The tool is external and not shipped here; a hard dependency would
make the whole context layer unusable for adopters without it. This invariant is restated in
`docs/INSTALL.md` (Graphify section) and the README.

### D002 — Onboarding never touches application code (reconstructed)

**Date:** 2026 (Phase 1) · **Status:** Accepted

**Decision:** `sdd-onboard` may only create/update context documents under `docs/`; it must
never modify application source.

**Reasoning (evident):** Onboarding an existing project must be a zero-risk operation, or
nobody will run it on a codebase they care about.

### D003 — Staleness threshold of 7 days for the architecture map (reconstructed)

**Date:** 2026 (Phase 1) · **Status:** Accepted

**Decision:** `graphify-stale-reminder` warns when `GRAPH_REPORT.md` is more than 7 days
older than the newest source file; reminder-only (exit 0), never blocking.

**Reasoning (evident):** A stale map silently trusted is worse than no map; 7 days balances
noise vs. drift for typical development pace.
