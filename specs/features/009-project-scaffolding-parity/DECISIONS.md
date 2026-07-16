# Decisions: project-scaffolding-parity

## Decision log

### D001 - Hook wiring stays an explicit opt-in command, outside the installers

**Date:** 2026-07-16

**Status:** Accepted

**Context:** Hooks ship and get linked but never run because nothing registers them in `settings.json`. The obvious fix — installers merging `settings.json` — contradicts the repo's documented safety model.

**Decision:** New `scripts/wire-hooks.sh` / `.ps1` perform the merge as an explicit command; installers only copy both settings templates and print a pointer.

**Reasoning:** Preserves "installers never write settings.json/CLAUDE.md"; the user consciously opts into hook execution per project.

**Consequences:** One extra command in the setup flow, documented in INSTALL.md and printed by install/link-project.

### D002 - Per-project SDD support files become shipped templates scaffolded by /project-init

**Date:** 2026-07-16

**Status:** Accepted

**Context:** `specs/README.md`, `SDD-GUARDRAILS.md` and `CLAUDE-SDD.md` existed only as hand-written files in one project; new projects silently lacked them.

**Decision:** Ship generic templates in `specs/_templates/` (core profile) and make `/project-init` instantiate all of them, filling `CLAUDE-SDD.md` from its interview.

**Reasoning:** `/project-init` is the single entry point for project setup; templates are the repo's existing distribution mechanism for documents.

**Consequences:** Structure parity across projects; the guardrails doctrine is duplicated (skill + template) with a header note accepting that trade-off.

### D003 - Merge granularity: dedupe by command string within each hook event

**Date:** 2026-07-16

**Status:** Accepted

**Context:** Re-running the wiring must not duplicate entries, and users may have hand-added their own hooks.

**Decision:** For each event (`PreToolUse`, `PostToolUse`, …), append only template hook commands not already present anywhere in that event's existing matcher groups; never remove or reorder existing entries.

**Reasoning:** Additive and idempotent; command string is the only stable identity across matcher-group shapes.

**Consequences:** A user who intentionally deleted one shipped hook will get it re-added on re-run — acceptable for an explicit command, documented in the script header.
