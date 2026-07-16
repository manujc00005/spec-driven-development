# Decisions: graphify-first-class-integration

## Decision log

### D001 - Canonical report path with legacy fallback

**Date:** 2026-07-17

**Status:** Accepted

**Context:** Graphify writes `.graphify/GRAPH_REPORT.md`; consumers looked at project root, breaking detection everywhere (hook + 2 skills). SPEC 006 and GRAPHIFY.md already documented `.graphify/`.

**Decision:** Resolution order everywhere: `.graphify/GRAPH_REPORT.md` first, then root `GRAPH_REPORT.md` as legacy fallback. If both exist, `.graphify/` wins.

**Reasoning:** Matches what the CLI actually produces; fallback costs one file check and protects any pre-006 layout.

**Consequences:** Hooks, skills, docs, and harness assertions all state the same order; fallback can be dropped in a future major.

### D002 - Auto-refresh via SessionStart hook with detached background run and lock

**Date:** 2026-07-17

**Status:** Accepted

**Context:** The graph goes stale silently. Candidate triggers: PostToolUse per edit, git post-commit, cron, SessionStart.

**Decision:** Extend the existing SessionStart hook: when the CLI is installed and the graph is missing/stale, spawn `graphify update . --no-description --no-label` detached, guarded by `.graphify/.update.lock` (10-min expiry), opt-out via `SDD_GRAPHIFY_AUTO=0`. Hook always exits 0 in <2s.

**Reasoning:** Staleness threshold is 7 days — per-session granularity is enough. Per-edit regeneration is too hot for a whole-repo graph; git hooks are outside the framework's contract (SDD ships Claude Code hooks only). Detached run keeps session start non-blocking.

**Consequences:** First session after staleness pays a background CPU cost; a killed refresh self-heals via lock expiry; two simultaneous sessions may rarely double-refresh (harmless).

### D003 - Keep the hook name `graphify-stale-reminder`

**Date:** 2026-07-17

**Status:** Accepted

**Context:** The upgraded hook does more than remind; a rename (`graphify-auto-update`) was considered.

**Decision:** Keep the existing name and extend behavior.

**Reasoning:** `profiles.json`, `hooks/README.md`, and installed copies reference the name; renaming breaks references for zero functional gain.

**Consequences:** Name slightly undersells behavior; README documents the auto-refresh clearly.

### D004 - Distribute `setup-graphify` from the framework checkout (wire-hooks precedent)

**Date:** 2026-07-17

**Status:** Accepted

**Context:** `profiles.json` has no `scripts` category; `install.sh` never copies repo scripts into projects; `wire-hooks` runs from the checkout with `--project-dir`.

**Decision:** Ship `scripts/setup-graphify.{sh,ps1}` in the repo, run against target projects via `--project-dir`; reference it from installer guidance, INSTALL.md, GRAPHIFY.md, and the init/onboard skills. No profiles.json schema change.

**Reasoning:** Follows the only existing precedent; avoids rippling schema changes through two installers; checkout-run scripts pick up fixes for free.

**Consequences:** Projects need the framework checkout (or central dir) available to adopt Graphify — same constraint wire-hooks already has.

### D005 - No network installs from hooks; installation only in the user-invoked script

**Date:** 2026-07-17

**Status:** Accepted

**Context:** "New projects always use Graphify" could be read as auto-installing the npm package.

**Decision:** Hooks never install anything. `setup-graphify` installs `@sentropic/graphify` only after explicit confirmation (or `--yes`). Init/onboard skills *recommend and offer* the script (default yes), never run npm silently.

**Reasoning:** Hooks run automatically every session — silent network installs are a security and trust violation; the framework's doctrine is graceful degradation, not hard dependency.

**Consequences:** Adoption requires one explicit user action; "always use" is achieved via defaults and prompts, not force.

### D006 - Graph-first token-saving doctrine in skills

**Date:** 2026-07-17

**Status:** Accepted

**Context:** Skills treated the graph as optional input; Claude routinely fell back to repo-wide scans even when a graph existed.

**Decision:** `context-manager` and `graphify-context` make the graph Step 1: when the report exists, derive the bounded reading list from it; when the CLI is available, prefer `graphify review-context` / `affected-flows` / `tree` / `path` over Glob/Grep sweeps. Heuristic scanning becomes the explicitly-labeled fallback. Documented in SDD-ORCHESTRATION.md, GRAPHIFY.md, CLAUDE.md.example.

**Reasoning:** The graph exists precisely to bound context; making it the default path (not an option) is what saves tokens. Code remains the source of truth — the graph only selects what to read.

**Consequences:** Doctrine is prose, not enforceable code; harness asserts key phrases exist to prevent regression.

### D007 - Version-tolerant scope fallback in setup-graphify (post-close fix)

**Date:** 2026-07-17

**Status:** Accepted

**Context:** After close, verification against the official Graphify 0.17.1 README showed the documented `--scope` values are `auto`/`tracked`/`all` — `committed` (used by GRAPHIFY.md and this integration, and known to have worked historically, e.g. guinda-spa) is not listed, and `detect` is not documented either. Could not be confirmed by execution (CLI not installed on this machine).

**Decision:** `setup-graphify.{sh,ps1}` try `graphify detect . --scope committed` first, fall back to `--scope auto`, and skip `detect` entirely (with a warning) if the subcommand does not exist. The `update` invocation keeps its flags with NO automatic fallback to plain `graphify update .`.

**Reasoning:** The fallback chain works across both known CLI surfaces without guessing the version. A plain `update` may trigger LLM description generation with API costs — never acceptable as a silent automatic fallback (same principle as D005: no un-consented cost). The stale-reminder hook keeps flags-only for the same reason; a failing background refresh is silent and self-heals via lock expiry.

**Consequences:** One extra failed invocation on newer CLIs (harmless); covered by a strict-stub test case that rejects `committed`. Real-CLI verification remains a deferred manual step.
