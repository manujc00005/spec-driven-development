<!-- Extracted from skills/spec-plan/SKILL.md — kept in sync with that skill's template. -->
<!-- See skills/sdd-guardrails/SKILL.md, section 1, for the full decision state machine (Proposed / Accepted / Superseded / Rejected / Deferred). -->

# Decisions: Phase 2 — Java/Spring backend profile

## Decision log

### D001 - Split profiles.json into shipped vs. planned arrays

**Date:** 2026-07-12

**Status:** Accepted

**Context:** The original `profiles.json` mixed items that exist in the repo with items that were only roadmap placeholders inside the same `skills`/`hooks`/`templates` arrays (e.g. `contract-testing-reviewer` next to `java-spring-reviewer`). Both installers treated any missing item — real typo or genuine roadmap gap — identically: a silent `[skip]` line. This made it impossible to distinguish "this doesn't exist yet by design" from "someone mistyped a name and a real feature silently didn't install."

**Decision:** Every profile now declares three shipped arrays (`skills`, `hooks`, `templates` — must exist on disk) and three parallel planned arrays (`plannedSkills`, `plannedHooks`, `plannedTemplates` — roadmap-only, may not exist). The installers validate shipped items against the filesystem and hard-fail (`[ERROR]`, non-zero exit) if one is missing; planned items are always reported as `[planned] ... not installed` and never cause an error.

**Reasoning:** A QA pass on the profile-driven installer surfaced that "missing = skip" silently hides both real typos and genuine repo/manifest drift. Separating declared intent (shipped vs. planned) up front removes the ambiguity instead of trying to infer it at install time.

**Consequences:** `profiles.json` bumped to `version: 0.2.0`. Any future addition to a profile must go in the correct array — an item added to `skills` before its `SKILL.md` exists will now fail the install instead of silently skipping.

### D002 - install.sh resolves profiles.json via python3, not jq

**Date:** 2026-07-12

**Status:** Accepted

**Context:** The original `install.sh` used `jq` to parse `profiles.json`, with a fallback of "jq not found → install everything, no filtering" if `jq` was absent. During this QA pass `jq` was unavailable in the reference test environment (Git Bash on Windows, and the `docker-desktop` WSL distro), which would have silently exercised the old fallback and hidden the new shipped/planned logic entirely. The fallback itself was also identified as unacceptable under the hardening goal: "never install everything unfiltered, never silently drop filtering."

**Decision:** `install.sh` now resolves `profiles.json` via an embedded `python3` script (stdlib `json` only). If `python3` is missing, or exists as a non-functional stub (see D003), the script fails immediately with: `python3 is required to resolve profiles.json on macOS/Linux. Install Python 3 or use the Windows installer.` There is no `jq` fallback and no "install everything" fallback — a missing/invalid `profiles.json`, an unresolvable interpreter, or a JSON parse failure all abort with a non-zero exit before any files are touched.

**Reasoning:** `python3` is present by default on virtually every modern macOS/Linux system (unlike `jq`, which is a separate install almost everywhere), and the resolution logic only needs the stdlib `json` module — no external dependency to install. This also unifies behavior with `install.ps1`, which already used PowerShell's built-in `ConvertFrom-Json` with no external tool.

**Consequences:** `hooks/README.md`'s existing note that "`jq` must be installed" for the **hook scripts themselves** (git-guardrails.sh, spring-config-guard.sh, etc. — which parse Claude Code's tool-call JSON from stdin) is unrelated and still accurate; that is a separate, unaffected use of `jq`. Only `install.sh`'s own profile-resolution logic dropped its `jq` dependency.

### D003 - python3 availability is checked functionally, not just by `command -v`

**Date:** 2026-07-12

**Status:** Accepted

**Context:** While testing D002's implementation, `command -v python3` succeeded in the reference environment but the resolved binary was the Windows Store's app-execution-alias stub, which prints an installation prompt and exits non-zero when actually invoked — i.e. `python3` "exists" in `PATH` but does not run any Python code.

**Decision:** `install.sh` checks python3 availability by actually running it (`python3 -c "import sys"`) and inspecting the exit code, not merely checking `command -v python3`.

**Reasoning:** A presence-only check would have falsely reported `python3` as available on any machine with this common Windows shim active, then failed later with a confusing raw error instead of the intended, actionable error message.

**Consequences:** None beyond one extra subprocess call during profile resolution; negligible cost.

### D004 - Explicitly requesting a disabled profile is a hard error, not a silent skip

**Date:** 2026-07-12

**Status:** Accepted

**Context:** The original installers silently dropped a requested profile with `disabled: true` (e.g. `blockchain-crypto`) from the active set and continued installing core + whatever else was valid, printing only a `[warn]`. `profiles.json`'s own note claimed the profile could be "explicitly enabled with -Profile blockchain-crypto," which directly contradicted the code (which always dropped it regardless).

**Decision:** Requesting a disabled profile explicitly now aborts the install with `[ERROR] Profile '<name>' is disabled by design ... and cannot be installed via --profile/-Profile. This is intentional, not a bug.` and a non-zero exit, before any files are touched. `profiles.json`'s note for `blockchain-crypto` was corrected to match: there is no flag to force-enable it.

**Reasoning:** Silently continuing with a subset of what the user asked for (installing core while dropping their explicit profile request) is a worse failure mode than stopping and telling them clearly why nothing further happened. It also resolves the doc/code contradiction outright instead of leaving a misleading note in place.

**Consequences:** If a disabled profile is ever meant to become force-enablable in the future, that requires an explicit code change plus a new spec entry — not just flipping a JSON field.

### D005 - Missing shipped item is a deferred hard-fail, not an immediate abort

**Date:** 2026-07-12

**Status:** Accepted

**Context:** Unlike an unknown/disabled profile name (which can be validated before touching any files), a missing shipped item is only discoverable after resolving the active profile's full item list.

**Decision:** When one or more shipped items are missing from disk, the installer prints every missing item as `[ERROR]`, continues through the rest of its normal dry-run/real-run reporting (so the user sees the complete picture of what *would* install), and only exits non-zero at the very end of the script.

**Reasoning:** Aborting immediately on the first missing item would hide how many other items are also missing and would prevent a `--dry-run` from showing the full preview in one pass. Deferring the exit while still surfacing every `[ERROR]` line balances "fail loudly" with "don't make the user run the command five times to find all the problems."

**Consequences:** A run with a missing shipped item still exits non-zero and installs nothing that depends on this being a "real" install (in dry-run this is moot; in a real run, the copy loops for shipped items still individually skip anything not found, so no partial/corrupt copy of a missing item is attempted — the final non-zero exit is a signal, not a rollback mechanism).
