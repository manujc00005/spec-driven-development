# Decisions: CI Consistency Check

## Decision log

### D001 - Single bash script, no PowerShell twin

**Date:** 2026-07-14

**Status:** Accepted

**Context:** Shipped hooks in this repo always come as `.sh`/`.ps1` pairs because they run on end-user machines. The consistency checker is repo-maintenance tooling that runs in CI (ubuntu) and occasionally on the maintainer's machine.

**Decision:** Implement `scripts/check-consistency.sh` as bash + embedded python3 only, matching `install.sh`'s existing JSON-parsing approach. No `.ps1` variant.

**Reasoning:** The pair rule exists for installed artifacts, not repo tooling; a twin would double maintenance for a script whose canonical runtime is a Linux CI runner. The maintainer runs it via Git Bash on Windows.

**Consequences:** The checker must stay free of Linux-only assumptions that break Git Bash (no GNU-only flags beyond what Git Bash ships). If repo tooling ever needs first-class Windows support, this decision must be revisited.

### D002 - README counts validated via explicit HTML marker comments

**Date:** 2026-07-14

**Status:** Accepted

**Context:** README contains many numeric claims; some are global totals, some are per-profile subsets, some are informal prose ("3 skills + 1 hook"). Regex-scanning all prose for numbers produces false positives and is unmaintainable.

**Decision:** Only counts wrapped in `<!-- count:<key> -->N<!-- /count -->` markers are validated. The marker wraps only the bare number (no bold/whitespace inside the span). A minimum required marker set (global totals + profile-table counts) is enforced: if a required marker is absent, the check fails.

**Reasoning:** Explicit markers make checked claims auditable and eliminate prose false positives. Requiring the minimum set prevents silently losing coverage if a marker is deleted during a README edit.

**Consequences:** Unmarked prose counts can still drift undetected; contributors adding new count claims should add markers. The marker convention is documented in the README CI section.

### D003 - Checker duplicates (rather than reuses) installer validation logic

**Date:** 2026-07-14

**Status:** Accepted

**Context:** `install.sh` already validates that shipped items exist on disk. Reusing it (e.g. a `--dry-run` mode) would avoid duplication.

**Decision:** The checker is standalone and read-only; it re-implements the shipped→disk direction and adds the other drift classes (orphans, planned-on-disk, settings wiring, README counts, hook parity).

**Reasoning:** The installer validates only one of seven drift classes and entangles validation with install side effects and platform branching. A read-only checker is simpler, faster, and safe to run anywhere. The duplicated semantics (template resolution order) are small and cross-referenced by comment.

**Consequences:** If installer resolution semantics change, the checker must change too — the cross-referencing comments and the self-test are the guard.

### D004 - No specs/CONSTITUTION.md in this repo; proceeding without it

**Date:** 2026-07-14

**Status:** Accepted

**Context:** User-level SDD rules say to create `specs/CONSTITUTION.md` via `/project-init` before any spec. This repo (the SDD framework itself) has shipped features 000–006 without one; its engineering rules live in `profiles.json` comments, `README.md`, and feature DECISIONS.

**Decision:** Follow the established project pattern and proceed without creating a constitution as part of this feature.

**Reasoning:** Creating a constitution is its own scoped piece of work (and arguably a backlog candidate); bundling it here would violate scope control.

**Consequences:** Future features keep relying on distributed conventions until a constitution is written deliberately.
