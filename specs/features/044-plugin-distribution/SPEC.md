# Feature Spec: Plugin distribution

## Status

In Progress

## Problem

The framework has two layers: the content (72 skills, 9 agents, 14 hook families, all text) and
the machinery that puts that content on a machine. The second layer has grown out of proportion
to the first and now sets the pace of the whole repository.

| Surface | Lines |
|---|---|
| `install.sh`, `install.ps1`, `install-all.*`, `link-project.*`, `update.*`, `wire-hooks.*`, personal-config, `profiles.json` | 4 895 |
| Their tests and `check-consistency.sh` | 3 015 |
| **Total spent on copying files to a machine** | **7 910** |

Six specs have gone into that layer (009, 015, 016, 034, 038, 039). Spec 039 is the only open
spec and has been blocked for weeks on a manual Windows 11 check. `DEBT-007` records that
`install.ps1` has never run on a real Windows outside CI. Every hook ships twice, `.sh` and `.ps1`,
and the duplication is permanent. Spec 034 existed only because the installer keeps a manifest
that could disagree with the disk.

Claude Code and Codex both ship a native plugin mechanism that already solves distribution:

- `claude plugin marketplace add <path|url|repo>` and `claude plugin install <plugin>@<marketplace>`
  install from a Git repository or a local directory. `claude plugin details <name>` reports the
  component inventory and the projected token cost.
- `codex plugin marketplace add` and `codex plugin add PLUGIN@MARKETPLACE` do the same for Codex
  (`codex-cli 0.152.1` on the maintainer machine).
- Verified on this machine: official plugins ship `agents/`, `commands/`, `skills/` and
  `hooks/hooks.json` as conventional directories under the plugin root, with hook commands
  resolved through `${CLAUDE_PLUGIN_ROOT}` (`ralph-loop`, `code-simplifier`, `agent-sdk-dev`); a
  marketplace may be a local directory (`i-have-adhd` is registered with
  `{"source": "directory"}`); a `.codex-plugin/plugin.json` variant exists in the wild.

The repository's layout already matches the plugin convention: `skills/`, `agents/` and `hooks/`
sit at the root, and every `.sh` hook locates its shared library relative to its own path
(`source "$(dirname "${BASH_SOURCE[0]}")/lib/claude-json.sh"`), so nothing depends on
`${CLAUDE_PROJECT_DIR}` except the wiring in the settings templates.

A second, smaller problem was found while comparing this framework with
`everything-claude-code` (WorldFlowAI fork, 2026-01-23). Almost all of that repository covers
ground this framework already covers with more rigour, and one of its hooks would be actively
harmful here (it blocks creating `.md` files). Three concrete checks in its reviewer prompts are
absent from ours, confirmed by grep across `skills/security-review`, `skills/qa-review`,
`skills/code-review`, `skills/review-all` and `skills/api-review`: licence of an integrated
library, dependency audit and lockfile discipline, and `TODO`/`FIXME` left without a ticket.

## Goal

Make the framework installable on any machine, for Claude Code and for Codex, with two commands
and no installer of our own: the repository root **is** the plugin, and the repository **is** its
own marketplace. Prove it on this Mac by installing from the local checkout into a disposable
project, observing the skills, agents and hooks all present and one hook firing, and record the
projected token cost so the profile question can be decided on evidence later.

Absorb the three reviewer checks from `everything-claude-code` as one-line additions to the
existing review skills, and record in `DECISIONS.md` what was evaluated and rejected, so the
comparison is never repeated.

The existing installer is **not** removed by this feature. It keeps working unchanged. Its
retirement is a later spec whose acceptance criteria are written once this one has produced
evidence.

## Non-goals

- Removing or modifying `install.sh`, `install.ps1`, `install-all.*`, `link-project.*`,
  `scripts/update.*`, `scripts/wire-hooks.*`, `profiles.json` or the install manifest. They stay
  as they are; a later spec retires them against the evidence this one records.
- Splitting the plugin per profile. This feature ships **one** plugin containing the whole
  repository content. The per-profile split is decided later, on the token-cost figure this feature
  records, not assumed now.
- Windows parity for plugin-delivered hooks. `hooks/hooks.json` carries one command per hook and
  that command is `bash`. Windows users keep `install.ps1` and `settings.template.json` until a
  later spec verifies what a plugin can do there. This is stated in the docs, not hidden.
- Wiring the opt-in hooks (`sdd-spec-guard`, `spring-config-guard`) or the deprecated one
  (`maven-compile`). The plugin wires exactly the set `settings.template.sh.json` wires by default.
- Publishing to any public marketplace, tagging a release, or changing `CHANGELOG.md` release
  structure. Local-directory installation is the proof; GitHub installation follows from it
  without further work and is not claimed here.
- Adopting anything else from `everything-claude-code`: its memory-persistence and
  strategic-compact hooks, `/learn`, `/checkpoint`, `/verify`, its `rules/` and `contexts/`
  layouts, its `build-error-resolver` and `e2e-runner` agents, or its `matcher` expression syntax
  (`tool == "Bash" && ...`), whose validity in Claude Code was not verified. The reasons go in
  `DECISIONS.md`.
- Touching `runner/`. It is frozen (notice at the top of `runner/README.md`) and is not plugin
  content: it is maintainer tooling and must not be exposed to adopters.

## Users / Actors

- **Manuel (maintainer)**, installing the framework on a new machine or a new project, on macOS
  today and Windows later.
- **A consumer project** (`lead-platform`, `guinda-spa`, ...), receiving skills, agents and hooks
  without a copied `.claude/hooks/` tree of its own.
- **Claude Code and Codex**, as the two hosts that load the plugin.
- **`scripts/check-consistency.sh`**, the CI gate that must keep passing with the new files present.

## Current behavior

Installation means cloning this repository and running `install.sh --link-user-claude` or the
PowerShell equivalent, which copies skills, agents and hooks into `~/.claude` and a project's
`.claude/`, writes `.sdd-install.json`, and wires hooks by having the maintainer paste entries from
a settings template into the project's `.claude/settings.json` with `${CLAUDE_PROJECT_DIR}` paths.
Updates run `scripts/update.sh`. Codex receives the same content through `adapters/codex/` and
`install-all.sh --codex-target`. Nothing in the repository declares a plugin manifest; `grep` for
`.claude-plugin`, `marketplace` or `/plugin install` finds only incidental key names in spec 038.

## Desired behavior

From a clean machine with Claude Code installed:

```bash
claude plugin marketplace add /path/to/spec-driven-development   # or the GitHub repo
claude plugin install sdd@spec-driven-development
```

After that, in any project, the SDD skills resolve (`/spec-create`, `/sdd`, `/architect-review`,
...), the nine agents are available for delegation, and the default hook set fires from
`${CLAUDE_PLUGIN_ROOT}` without any file copied into the project. `claude plugin details sdd`
lists the inventory and a projected token cost.

For Codex:

```bash
codex plugin marketplace add /path/to/spec-driven-development
codex plugin add sdd@spec-driven-development
```

The three new reviewer checks appear in the relevant review skills as checklist lines, in the
same voice as the lines around them.

## Functional requirements

Plugin manifest and marketplace

- FR-001: `.claude-plugin/plugin.json` exists at the repository root and declares name `sdd`,
  a version, description, author and repository. It relies on the conventional directories
  (`skills/`, `agents/`, `commands/` if present, `hooks/hooks.json`) rather than listing paths, so
  adding a skill never requires touching the manifest.
- FR-002: `.claude-plugin/marketplace.json` exists at the repository root and declares one
  marketplace named `spec-driven-development` with one plugin entry, `sdd`, whose `source` is `./`.
- FR-003: `.codex-plugin/plugin.json` exists at the repository root with the same identity and a
  `skills` pointer, so the same checkout serves both hosts.
- FR-004: `hooks/hooks.json` exists and wires exactly the hooks `settings.template.sh.json` wires
  by default, with the same events, matchers, timeouts and status messages, and every command
  rewritten from `bash ${CLAUDE_PROJECT_DIR}/.claude/hooks/<name>.sh` to
  `bash "${CLAUDE_PLUGIN_ROOT}/hooks/<name>.sh"`. No hook script is modified.
- FR-005: The plugin excludes non-content directories. `runner/`, `scripts/`, `specs/`, `evals/`,
  `adapters/`, `examples/`, `docs/`, the installers and the tests must not be loaded as plugin
  components. If the plugin system loads only the conventional directories this is satisfied by
  construction; if it needs an explicit exclusion mechanism, the task uses it. Either way the
  `claude plugin details sdd` inventory is the proof.

Local proof

- FR-006: The marketplace is added from the local checkout path and the plugin installed with the
  CLI, non-interactively, and the commands and their output are recorded under
  `specs/features/044-plugin-distribution/evidence/`.
- FR-007: In a disposable project directory outside this repository, a Claude Code session with
  the plugin enabled resolves at least `/spec-create` and `/sdd`, and the `SessionStart` hook
  `project-init-check` emits its message. The observation is recorded, not asserted.
- FR-008: The projected token cost reported by `claude plugin details sdd` is recorded in
  `evidence/` together with the component counts, so the per-profile decision can be taken later
  with a number.
- FR-009: The Codex marketplace is added from the same local path and `codex plugin add
  sdd@spec-driven-development` succeeds; the output is recorded. If Codex rejects the manifest,
  the exact error is recorded and the Codex acceptance criterion is downgraded through a decision,
  not silently dropped.

Consistency gate

- FR-010: `scripts/check-consistency.sh` passes with the new files present. If it inspects hook
  wiring or hook counts, it is extended to know about `hooks/hooks.json` as a third wiring
  alongside the two settings templates, so the three cannot drift apart silently.

Reviewer checks adopted from everything-claude-code

- FR-011: `skills/security-review/SKILL.md` gains a check for dependency audit and lockfile
  discipline: the change runs the ecosystem's audit (`npm audit`, `pip-audit`, `mvn
  dependency-check` or equivalent) when it adds or bumps a dependency, and commits the lockfile.
- FR-012: `skills/security-review/SKILL.md` gains a check that a newly integrated library's licence
  is compatible with the project's distribution.
- FR-013: `skills/qa-review/SKILL.md` gains a check that no `TODO` or `FIXME` is introduced
  without a reference to a spec, task or ticket.
- FR-014: Each addition is one checklist line in the voice of its neighbours, placed in the
  existing section it belongs to. No new section, no new skill, no new agent.

Documentation

- FR-015: `docs/INSTALL.md` gains a "Install as a plugin" section placed **before** the installer
  instructions, giving the four commands above, stating that Windows hooks stay on the installer
  for now, and warning that a project must not wire the same hooks in `.claude/settings.json`
  **and** enable the plugin, or every hook fires twice.
- FR-016: `README.md` install section points to the plugin path first; the installer path stays
  documented as the alternative.
- FR-017: `CHANGELOG.md` Unreleased gains one line for this spec.

## Non-functional requirements

- Performance: the plugin must add no per-tool-call latency beyond what the same hooks add today
  through `settings.json`; the hook set and timeouts are identical by FR-004.
- Security: no hook script changes; `hooks/hooks.json` grants nothing the templates did not. No
  secrets, tokens or machine paths enter the manifests. The marketplace `source` is relative.
- Observability: every claim in the acceptance criteria is backed by a recorded command output
  under `evidence/`, never by a sentence saying it worked.
- Maintainability: the manifests list no skill or agent by name, so the 72 skills and 9 agents
  keep evolving without manifest edits. The only file that duplicates existing knowledge is
  `hooks/hooks.json`, and FR-010 makes the gate watch it.

## API / Interface changes

New public interface: the plugin identity `sdd@spec-driven-development` for Claude Code and Codex.
New files: `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`,
`.codex-plugin/plugin.json`, `hooks/hooks.json`. Renaming the plugin later is a breaking change for
anyone who installed it, so the name is chosen once here.

## Data model changes

None. No manifest of our own is written or read; `.sdd-install.json` is untouched.

## Edge cases

- **A project already wires the hooks through `.claude/settings.json` and also enables the
  plugin.** Every hook runs twice per event. Not prevented by code in this feature; documented in
  FR-015. The throttled hooks (`scope-keeper-reminder`, `graphify-scan-reminder`) self-limit; the
  formatters would run twice and be idempotent; `git-guardrails` would block twice, harmlessly.
- **Plugin enabled in a project with no `specs/CONSTITUTION.md`.** `project-init-check` fires on
  `SessionStart` exactly as it does today when wired manually. That is the hook doing its job, and
  it is also the observable signal FR-007 uses.
- **The plugin system loads everything under the root, not only the conventional directories.**
  Then `runner/`, `scripts/` and `specs/` would appear in the inventory. FR-005 turns this into a
  recorded inventory check with an exclusion task if needed, instead of an assumption.
- **`claude plugin details` reports no token cost or the CLI lacks the subcommand on an older
  version.** Record the version and the actual output; the criterion becomes "inventory recorded"
  and the cost figure moves to open debt with the version noted.
- **`bash` is absent on the host.** The hooks do not fire. Out of scope by Non-goals, stated in the
  docs.
- **The skill listing grows the model's context.** That is precisely the number FR-008 records; this
  feature measures it and does not act on it.
- **Codex accepts the marketplace but not the manifest shape.** FR-009: record the error, downgrade
  the AC through a decision, keep the Claude Code path. Codex is first-class, so this cannot be
  closed as Done while the Codex path is unverified; it can be closed as Done with a recorded,
  narrowed AC only if the failure is on the Codex side and documented.

## Acceptance criteria

- AC-001: `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `.codex-plugin/plugin.json`
  and `hooks/hooks.json` exist at the repository root, are valid JSON, and none of them names an
  individual skill or agent.
- AC-002: `hooks/hooks.json` wires the same ten hook commands as `settings.template.sh.json` with
  identical events, matchers, timeouts and status messages, differing only in the path prefix. A
  script or test asserts this equivalence and is part of FR-010.
- AC-003: `claude plugin marketplace add <local path>` followed by `claude plugin install
  sdd@spec-driven-development` both exit 0 on this Mac; transcripts are under `evidence/`.
- AC-004: `claude plugin details sdd` lists skills, agents and hooks with counts that match the
  repository (skills and agents equal the counts `check-consistency.sh` already asserts), and
  lists nothing from `runner/`, `scripts/`, `specs/`, `evals/`, `adapters/` or `docs/`. Output
  under `evidence/`.
- AC-005: The projected token cost figure from AC-004's output is recorded in
  `evidence/TOKEN_COST.md` with the CLI version.
- AC-006: In a disposable project outside this repository, with the plugin installed and no
  `.claude/hooks/` directory present, `/spec-create` and `/sdd` resolve and `project-init-check`
  emits its `SessionStart` message. Transcript under `evidence/`.
- AC-007: `codex plugin marketplace add <local path>` and `codex plugin add
  sdd@spec-driven-development` exit 0, or their exact failure is recorded and a decision narrows
  this criterion. Transcript under `evidence/`.
- AC-008: `scripts/check-consistency.sh` passes on the final tree and fails when `hooks/hooks.json`
  is deliberately made to differ from `settings.template.sh.json` (one hook removed), then passes
  again when restored. Both runs recorded.
- AC-009: `skills/security-review/SKILL.md` contains one checklist line about dependency audit and
  lockfile, and one about licence compatibility; `skills/qa-review/SKILL.md` contains one about
  `TODO`/`FIXME` without a reference. Each is a single line inside an existing section. `git diff
  --stat` for those two files shows only additions.
- AC-010: `DECISIONS.md` for this feature records, in one decision, the items from
  `everything-claude-code` that were evaluated and rejected, with one reason each, so the
  comparison is closed.
- AC-011: `docs/INSTALL.md` has the plugin section before the installer section, and it contains
  the Windows statement and the double-wiring warning. `README.md` install section links to it.
  `CHANGELOG.md` Unreleased carries one line for this spec, and `hooks/README.md` names
  `hooks/hooks.json` as the plugin wiring (extended at planning time, D008).
- AC-012: `runner/` is untouched (`git diff --stat main -- runner/` is empty) and no installer or
  `profiles.json` line changes (`git diff --stat main -- install.sh install.ps1 install-all.sh
  install-all.ps1 link-project.sh link-project.ps1 scripts/update.sh scripts/update.ps1
  scripts/wire-hooks.sh scripts/wire-hooks.ps1 profiles.json` is empty).

## Test scenarios

- Unit: the FR-010 equivalence check between `hooks/hooks.json` and `settings.template.sh.json`,
  exercised inside `scripts/check-consistency.test.sh` with a passing fixture and a one-hook-removed
  failing fixture (AC-008).
- Integration: local marketplace add and plugin install on both CLIs (AC-003, AC-007); inventory
  and token cost (AC-004, AC-005).
- E2E: the disposable-project session observing skill resolution and one hook firing (AC-006).
- Manual: reading the rendered `docs/INSTALL.md` section and following its four commands from a
  second terminal (AC-011).

## Assumptions

- The plugin loaders of both hosts discover `skills/`, `agents/` and `hooks/hooks.json` by
  convention when `plugin.json` does not list paths. Evidence: `ralph-loop`'s manifest carries no
  component keys yet its `commands/` and `hooks/` load. If this proves false for `agents/`, FR-001
  gains explicit path keys and the assumption is corrected in `DECISIONS.md`; the "no skill named
  individually" rule still holds because the keys point at directories.
- `${CLAUDE_PLUGIN_ROOT}` resolves to the installed plugin root at hook execution time, so
  `hooks/<name>.sh` finds `hooks/lib/claude-json.sh` through `dirname "${BASH_SOURCE[0]}"`.
  Evidence: `ralph-loop` runs `bash "${CLAUDE_PLUGIN_ROOT}/hooks/stop-hook.sh"`.
- A marketplace whose `source` is `./` is accepted for a directory-sourced marketplace. Evidence:
  `everything-claude-code` uses it and is installable per its README; if rejected, the fallback is
  a relative path to a subdirectory and a recorded decision.
- Spec number 044 is used although 043 is not on `main`: 043 is the archived
  `feature/043-real-provider-execution` and its folder name is reserved by that branch.
- The three review additions are stack-agnostic in wording; the audit command examples are
  illustrative and belong in the line itself only as examples, not as requirements.
- `everything-claude-code` at `/Users/manu/Proyectos/everything-claude-code` is the WorldFlowAI
  fork (last commit 2026-01-23); the upstream may have changed since. The comparison is against the
  local copy and says so.

## Open questions

- None blocking. The two uncertainties (conventional-directory discovery for `agents/`, and the
  `./` source) each have a stated fallback and land in `DECISIONS.md` once observed.

## Contracted services

Contracted services not declared → all billable add-ons treated as NOT contracted (conservative
default). Run `/project-init` to declare them.
