# Decisions: incremental-update

## Decision log

### D001 - Manifest is a hidden dotfile in the central dir (resolves OQ-003)

**Date:** 2026-07-17

**Status:** Accepted

**Context:** The install manifest is framework-owned state. It could live per-project, be a visible file, or sit inside the central dir.

**Decision:** `<central-dir>/.sdd-install.json`, hidden, with `schemaVersion: 1`, overwritten by each install run, profiles accumulated across runs.

**Reasoning:** Projects are symlinked views of the central dir, so central state is the single source of truth; a dotfile signals "state, not documentation"; `schemaVersion` lets the format evolve without bricking older updates (corrupt/unknown manifests already degrade to unknown-version mode by spec).

**Consequences:** `update` has exactly one place to look. Adopters who delete it lose only report quality, never correctness.

**Amendment (T001):** the manifest also records `installedCommit` (hash always, even when a tag resolves) and a sticky `linkUserClaude` boolean — FR-007 needs the latter for agents-refresh detection, and the former disambiguates `git describe` output. A corrupt manifest is discarded and rebuilt from the current run (accumulated profiles from before the corruption are lost — acceptable, state is best-effort).

### D002 - `update` orchestrates the installer; it never reimplements copy logic

**Date:** 2026-07-17

**Status:** Accepted

**Context:** The update step could copy files itself or invoke `install.sh`/`install.ps1`.

**Decision:** Invoke the installer with pass-through flags; parse its `[ok]`/`[skip]` output for the report counts.

**Reasoning:** Skip/force/backup semantics exist once and are already tested by use; duplicating them guarantees drift. The cost — coupling to installer log prefixes — is contained by parsing stable prefixes only and asserting counts in `update.test.sh` so CI catches wording changes.

**Consequences:** Installer log prefixes (`[ok]`, `[skip]`) become a de-facto interface; changing them requires touching the update parser and its tests.

### D003 - `--ff-only` pull and dirty-tree refusal; no stash, no merge fallback

**Date:** 2026-07-17

**Status:** Accepted

**Context:** The adopter's clone may have local commits or uncommitted changes at update time.

**Decision:** Refuse a dirty tree (exit 1, name the files); pull with `--ff-only`; a non-fast-forward is a hard error with guidance.

**Reasoning:** Any automatic stash/merge/reset can destroy adopter work — the exact thing this feature promises never to do. Divergence is an adopter decision point, not something a script resolves silently.

**Consequences:** Adopters who fork the repo must merge upstream themselves before running `update`. The error message carries that guidance.

### D004 - Remind-only for wire-hooks; no reverse drift reporting (resolves OQ-001, OQ-002)

**Date:** 2026-07-17

**Status:** Accepted

**Context:** `update` could auto-run `wire-hooks` on `--project-dir` targets when new hook families ship, and the CLAUDE.md drift check could also flag adopter-added sections absent from the example.

**Decision:** Remind only for wire-hooks (it edits a project's `settings.json` — an explicit adopter action). Drift is reported in the example→target direction only.

**Reasoning:** Both defaults follow the same principle: `update` never modifies adopter-owned files and never flags legitimate adopter customization as a problem.

**Consequences:** New hook families require one manual command per project; the report says exactly which. Adopter-authored CLAUDE.md sections stay invisible to the check by design.

### D005 - Test harness uses real local git repos with tags, not git-less copies

**Date:** 2026-07-17

**Status:** Accepted

**Context:** `check-consistency.test.sh` copies the repo and strips `.git` — its subject is filesystem consistency. `update`'s contract is inherently git-dependent (pull, tags, describe, dirty detection).

**Decision:** `update.test.sh` builds throwaway bare "origin" repos with two tagged releases and `file://` working clones per case; no network, deterministic.

**Reasoning:** Faking git behavior would test the mock. Local bare repos give the real semantics (ff-only, tags, dirty tree) hermetically in CI.

**Consequences:** Slightly slower suite (git init/clone per case); zero flakiness risk from network or credentials.

### D007 - update.ps1 verified statically on the dev machine; execution deferred to CI + Windows spot-check (T008)

**Date:** 2026-07-17

**Status:** Accepted

**Context:** The dev machine has no `pwsh`, so `update.ps1` could not be executed or even PSParser-tokenized locally. The bash `update.sh` is fully executed and tested.

**Decision:** Port `update.ps1` as a faithful mirror and verify what is verifiable without pwsh: flag parity, report-string parity, and compatibility of the argument binding to `install.ps1` (its `-Profile` splits comma-separated values at line 146, so the single comma-joined string this script passes is correct). The `New-TemporaryFile` handle is resolved to `.FullName` to avoid FileInfo-vs-string coercion. Execution verification is left to the CI PowerShell parse gate (syntax) and the T012 Windows functional spot-check (behavior), which the task already requires and instructs not to skip silently.

**Reasoning:** Porting a moving target twice is wasteful (bash settled first); claiming execution I did not perform would violate the verifier discipline. The two existing gates are the honest verification path.

**Consequences:** If the CI parse gate or the Windows spot-check surfaces a defect, it is fixed as a follow-up under this spec, not a new one. Until the Windows spot-check runs, `update.ps1` behavior is asserted by parity of construction, not by observation.

### D006 - Manifest lands in the installers as its own slice, before `update` exists

**Date:** 2026-07-17

**Status:** Accepted

**Context:** The manifest write (T001–T002) and the update scripts (T003+) could ship as one unit.

**Decision:** Manifest first, independently useful.

**Reasoning:** Every install that runs between this feature landing and an adopter's first `update` records state that makes that first update's report accurate. Shipping it first also keeps T001–T002 trivially revertible on their own.

**Consequences:** Adopters who reinstall after this slice but before `update` ships already have a manifest; `update`'s unknown-version mode remains for everyone else.
