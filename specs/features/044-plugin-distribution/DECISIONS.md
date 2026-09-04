# Decisions: Plugin distribution

## Decision log

### D001 - One plugin, the repository root, named `sdd`

**Date:** 2026-09-04

**Status:** Accepted

**Context:** The framework could ship as one plugin per profile (nine), as one plugin for the
`core` profile with the stack profiles left to the installer, or as one plugin carrying everything.
`profiles.json` encodes the per-profile selection in 367 lines and spec 030's routing logic; a
plugin manifest is declarative and points at directories, not at lists of skills.

**Decision:** One plugin, `sdd`, whose root is the repository root, in a marketplace named
`spec-driven-development` declared in the same repository with `source: "./"`. No skill or agent is
named in any manifest.

**Reasoning:** The two alternatives each require new machinery: a per-profile split needs either
`skills/` restructured into profile directories (breaking every installer path) or a build step
generating plugin trees from `profiles.json` (a new installer). Both are exactly the over-engineering
this feature exists to stop. The cost of the single plugin is the token footprint of 72 skill
descriptions in every session; `claude plugin details` reports that figure, and AC-005 records it so
the split is decided later on a number rather than assumed now.

**Consequences:** Adding a skill or agent never touches a manifest. Adopters cannot pick profiles
through the plugin yet; the installer still can. The two assumptions this decision rests on
(conventional discovery of `agents/`; nothing outside `skills/`, `agents/`, `hooks/` loaded) are
answered by T001 and recorded below.

**Observed (T001):** _pending — filled by T001 with the inventory lines quoted._

### D002 - `hooks/hooks.json` is a transcription of `settings.template.sh.json`, bash only

**Date:** 2026-09-04

**Status:** Accepted

**Context:** A plugin wires hooks through one `hooks/hooks.json` with commands resolved against
`${CLAUDE_PLUGIN_ROOT}`. The repository already has two wirings, one per shell, in the settings
templates. Every `.sh` hook finds its library through `dirname "${BASH_SOURCE[0]}"`, so the scripts
are location-independent.

**Decision:** `hooks/hooks.json` carries the `hooks` object of `settings.template.sh.json`
unchanged except for the command prefix. Same events, matchers, timeouts, status messages, same
ten commands. `bash` only. Windows parity for plugin-delivered hooks is a Non-goal; Windows users
stay on `install.ps1` and `settings.template.json`.

**Reasoning:** Any difference between the plugin wiring and the template wiring is drift the gate
would have to special-case. Equivalence is the property that keeps three wirings honest (D005).
Committing to `bash` states a real limitation instead of shipping an untested PowerShell branch,
which is what DEBT-007 already is.

**Consequences:** A project that wires hooks manually and also enables the plugin runs every hook
twice; documented, not prevented (FR-015). Windows keeps the installer until a later spec verifies
plugin hooks there.

### D003 - The installer is untouched; retirement is a later spec

**Date:** 2026-09-04

**Status:** Accepted

**Context:** ADR-001 (architect review, 2026-09-04) recommended reaching the plugin through a
hybrid period with an explicit end, and warned that two distribution mechanisms as a permanent state
repeat the runner's two-sources-of-truth failure.

**Decision:** No installer script, `profiles.json`, manifest logic or `runner/` file changes in this
feature (AC-012). The spec that retires the installer is written after this one has recorded
evidence, with the removal of `scripts/update.*` and the install manifest as its acceptance
criteria.

**Reasoning:** The installer is the only Windows path and the only path anyone has used. Removing it
before the plugin has a recorded install, a recorded inventory and a recorded token cost would be a
decision without evidence.

**Consequences:** For a while the repository has two ways to install. `docs/INSTALL.md` puts the
plugin first and names the installer as the alternative, so the direction is visible.

### D004 - What was taken from `everything-claude-code`, and what was not

**Date:** 2026-09-04

**Status:** Accepted

**Context:** The local copy at `/Users/manu/Proyectos/everything-claude-code` (WorldFlowAI fork,
last commit 2026-01-23) was read in full at the skill, agent, command, rule, hook and script level
and compared with this framework's 72 skills, 9 agents and 14 hook families. Manuel asked to adopt
whatever is better and merge it in.

**Decision:** Adopt exactly three reviewer checklist lines, and reject everything else with the
reasons below, so the comparison is closed and never repeated.

Adopted (absent here, confirmed by `grep` across `security-review`, `qa-review`, `code-review`,
`review-all`, `api-review`):

- **Dependency audit and lockfile discipline** → `security-review` (from their
  `security-review/SKILL.md` §10 and `code-reviewer.md`).
- **Licence compatibility of an integrated library** → `security-review` (from
  `code-reviewer.md`, "Licenses of integrated libraries checked").
- **`TODO`/`FIXME` without a ticket** → `qa-review` (from `code-reviewer.md`, "TODO/FIXME without
  tickets").

Rejected, one reason each:

- **Plugin manifests as distribution** — not rejected: it is this whole feature (D001). Listed here
  so the record shows where the idea came from.
- **`memory-persistence` hooks (`session-start`, `session-end`, `pre-compact`)** — `session-end.js`
  writes a Markdown template containing the literal `[Session context goes here]`; the persistence
  is done by the model, not the hook. Our durable state is `SPEC/PLAN/TASKS/DECISIONS` plus
  `/spec-status`, and `TASKS.md` checkboxes survive compaction. Nothing to gain.
- **`PreCompact` event** — the only lifecycle event we do not use, and for the same reason: our
  state is already on disk. Low value; revisit only if a real compaction loss is observed.
- **`strategic-compact`** — a tool-call counter that nags to `/compact` every 25 calls after 50.
  Adds noise to every edit; the SDD phases already give natural compaction points.
- **`/learn` and `continuous-learning`** — `evaluate-session.js` counts user messages and prints
  "evaluate for extractable patterns"; the extraction is the model's. Our memory directory with its
  index does this with a loaded index rather than a model-invoked skill. Covered.
- **`/checkpoint`** — a log of `(name, sha)` lines with test/coverage deltas. `TASKS.md` ticks plus
  git already are the checkpoints; a second ledger drifts.
- **`/verify` and `verification-loop`** — a build/types/lint/tests/console.log report, npm-shaped.
  Our per-edit hooks do the mechanical part, `/verifier` sets the standard, `/qa-review` and the
  prompt maestro's G5 do the report. A fourth verification entry point is the over-engineering the
  user asked to avoid.
- **`rules/` split (coding-style, git-workflow, testing, security, performance, patterns)** — a
  poorer, TypeScript-specific version of `specs/CONSTITUTION.md` plus profile reviewers. Their
  `performance.md` model-selection table is already our deep-reasoner/fast-worker routing;
  `TOKEN_ECONOMY.md` already covers context-window discipline.
- **`contexts/` (dev, research, review)** — mode files; our profiles and skills' `SDD Contract`
  blocks route the same way with less ceremony.
- **`code-reviewer.md` severity taxonomy and Approve/Warning/Block** — already ours: every review
  skill emits a verdict block, and the prompt maestro's G5 requires APPROVE/PASS.
- **`build-error-resolver`** — "minimal diffs, no architecture changes" is `fast-worker` plus
  `/scope-keeper`. Duplicate.
- **`e2e-runner` (Playwright)** — a real gap in the `next-prisma-web` profile, but Manuel's daily
  work is Python and SQL as of 2026-08; a profile addition on its own evidence later, not a copy
  now.
- **`doc-updater` / `update-codemaps`** — Graphify is our codemap, spec 010/027.
- **`clickhouse-io`, `backend-patterns`, `frontend-patterns`, `coding-standards`** — stack content
  for stacks we do not run, or duplicated by our profile reviewers.
- **`eval-harness` (pass@k, capability vs regression evals)** — `evals/` and `skill-eval.sh` (spec
  022) exist; "define evals before coding" is what acceptance criteria and the `Verify:` clause
  (spec 033) already enforce.
- **The hook that blocks creating `.md` files** — would block `SPEC.md`, `PLAN.md`, `TASKS.md`,
  `DECISIONS.md`. Actively hostile to this framework.
- **Their `matcher` expression syntax (`tool == "Bash" && tool_input.command matches ...`)** — not
  verified as valid Claude Code matcher syntax; ours (`"matcher": "Bash"`) is what every official
  plugin on this machine uses. Not adopted.
- **`tmux` enforcement for dev servers, `console.log` audits, PR-URL echo** — stack habits, not
  framework concerns.

**Reasoning:** The repository is famous for breadth, not depth. Where it overlaps ours, ours is
stricter; where it does not, the gap is either not ours to fill now or is filled by a mechanism we
already have. The three adopted lines are the only items that were both absent and stack-agnostic.

**Consequences:** AC-009 and AC-010 are the whole footprint of the comparison. Anyone proposing to
re-adopt an item above must first answer the reason recorded against it.

### D005 - The consistency gate treats `hooks/hooks.json` as a third wiring and checks equivalence

**Date:** 2026-09-04

**Status:** Accepted

**Context:** `check_settings_wiring` in `scripts/check-consistency.sh` verifies, for each settings
template, that every referenced hook exists and the deprecated pair is not wired together. It does
not compare the two templates with each other. With a third wiring, drift between wirings becomes
the most likely failure, and reference-existence alone would not catch a hook silently dropped
from the plugin.

**Decision:** Run `check_settings_wiring("hooks/hooks.json")` for the existing guarantees, and add
a `plugin-wiring` check that parses `hooks/hooks.json` and `settings.template.sh.json` as JSON and
asserts the multiset of `(event, matcher, hook-name, timeout)` is identical, naming the first
differing tuple. Test both directions in `check-consistency.test.sh`: a removed hook fails, the
clean tree passes.

**Reasoning:** Equivalence is the property D002 chose; a check that does not test it would let the
property rot on the first hand edit, which is how spec 034 came to exist.

**Consequences:** Any deliberate change to the default hook set must be made in both files in the
same commit. That is the intended friction.

### D006 - Every acceptance criterion is a recorded observation

**Date:** 2026-09-04

**Status:** Accepted

**Context:** Spec 042's conformance found that four of six rejections were fixes reported but not
made; spec 031's Done still has CONF-014 open against it. This feature's claims ("installs",
"resolves", "fires") are exactly the kind that are easy to state and easy to skip.

**Decision:** Every AC that says something happened points at a file under `evidence/` holding the
command, its exit code, the CLI version and the output. A Codex failure narrows AC-007 through a
written decision (D009, if needed), never through omission. A missing token-cost figure becomes a
debt entry with the CLI version, not a ticked box.

**Reasoning:** An unverified plugin path would recreate DEBT-007 under a new name.

**Consequences:** `evidence/` gains up to six files. The Ralph loop running this feature must not
tick a task whose evidence file is absent.

### D007 - Number 044 while 043 is absent from `main`

**Date:** 2026-09-04

**Status:** Accepted

**Context:** `specs/features/` on `main` ends at 042. Spec 043 exists only on the archived branch
`feature/043-real-provider-execution`. Memory records three spec-number collisions across machines.

**Decision:** This feature is 044. 043 stays reserved by the archived branch.

**Reasoning:** A second 043 with a different name would make `/spec-status` and the archive record
ambiguous the day that branch is checked out next to `main`.

**Consequences:** The numbering on `main` has a visible gap, and the gap is the pointer to the
archive.

### D008 - AC-011 extended at planning time to cover FR-017

**Date:** 2026-09-04

**Status:** Accepted

**Context:** The Draft spec's FR-017 (one `CHANGELOG.md` Unreleased line) had no acceptance
criterion, and `/spec-plan` requires every task to map to one.

**Decision:** AC-011 gains the clauses "`CHANGELOG.md` Unreleased carries one line for this spec"
and "`hooks/README.md` names `hooks/hooks.json` as the plugin wiring". T010 covers both.

**Reasoning:** Smaller than a new AC, and the three edits are one documentation task.

**Consequences:** None beyond the spec text.
