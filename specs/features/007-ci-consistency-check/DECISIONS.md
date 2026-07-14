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

### D005 - Auto-fix only for README count markers

**Date:** 2026-07-14

**Status:** Accepted

**Context:** Many drift classes detected by the checker could theoretically be auto-fixed (e.g., missing `.ps1` for a hook, or promoting a planned item to shipped in `profiles.json`). FR-012 adds a `--fix` flag, but scoping it narrowly reduces risk and decision-making burden.

**Decision:** The `--fix` flag auto-corrects only README count markers (updating the number between `<!-- count:<key> -->` markers). All other violations (orphans, missing shipped artifacts, planned items with files, incomplete hook pairs, settings wiring errors) are reported but not auto-fixed; if any non-auto-fixable violations exist, the script exits 1 and does not modify README.

**Reasoning:** README count updates are deterministic (read computed value, overwrite marker) and low-risk (one file, reversible by git). Deciding whether an orphan should be deleted or added to profiles, whether a .ps1 should be created with what template, or whether a planned item is ready to ship requires human judgment and potentially affects profiles.json (repo manifest). `--fix` is a convenience for the maintainer's local workflow, not a substitute for careful review.

**Consequences:** The maintainer still reviews and approves all non-cosmetic changes manually. The `--fix` flag saves time on README maintenance during development but does not change merge review requirements.

### D006 - Spec updated: add auto-fix for README count markers

**Date:** 2026-07-14

**Status:** Accepted

**Context:**

After the initial spec was created (FR-001 through FR-011), stakeholder feedback requested a `--fix` mode to auto-correct safe violations, reducing maintainer friction during local development.

**Decision:**

Added FR-012 (auto-fix capability) and AC-010 (acceptance criteria for --fix) to SPEC.md. The implementation scope remains read-only for non-fixable violations; only README count markers (deterministic, low-risk) are auto-corrected. Updated PLAN.md and TASKS.md to reflect the new requirement. D005 documents the design rationale for limiting auto-fix to README counts.

**Reasoning:**

The `--fix` flag provides genuine value (saves maintainer time on repetitive marker updates) without introducing risk (marker updates are deterministic and reversible). Scoping to README counts avoids complex decision-making around artifacts (delete or add to profiles?) while still delivering the core benefit.

**Consequences:**

T005 and T006 marked `[NEEDS REVIEW]` and now cover AC-010. Test strategy in PLAN.md updated to include --fix test scenarios. Implementation is incomplete until T005/T006 are re-implemented to support the `--fix` flag and write capabilities.
