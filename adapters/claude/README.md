# Claude Code adapter

**The Claude Code adapter is the repository root.** It is the primary, shipped adapter, and no
files were moved into this directory. This page is a **pointer**, not a copy.

## Why the files are not here

Moving `skills/`, `agents/`, `hooks/`, and the installers under `adapters/claude/` would rename
paths that are hardcoded in `install.sh`, `install.ps1`, `link-project.*`, `scripts/wire-hooks.*`,
`scripts/check-consistency.sh`, and `profiles.json` — and, critically, in **every downstream project
that already installed from this repo**. The provider/adapter boundary this framework needs is a
**conceptual and documentation** boundary, and it is expressed that way (see
[`../../docs/PROVIDER_ADAPTERS.md`](../../docs/PROVIDER_ADAPTERS.md)) rather than by a breaking
filesystem reorganization.

See `specs/features/019-provider-aware-codex-adapter/DECISIONS.md` D001 for the full rationale.

## Where each piece of the Claude adapter lives

| Adapter piece | Location | Notes |
|---|---|---|
| Plugin manifests | [`../../.claude-plugin/`](../../.claude-plugin/) | `plugin.json` + `marketplace.json`: the repository root is the `sdd` plugin and its own marketplace (spec 044). No skill or agent is named; directories load by convention. |
| Plugin hook wiring | [`../../hooks/hooks.json`](../../hooks/hooks.json) | Same default set as `settings.template.sh.json`, `${CLAUDE_PLUGIN_ROOT}` paths; equivalence enforced by `scripts/check-consistency.sh`. |
| Lifecycle & review skills | [`../../skills/`](../../skills/) | 72 skills, one folder per slash command, each with a `## SDD Contract`. |
| Lifecycle & model-tier agents | [`../../agents/`](../../agents/) | 6 lifecycle agents + `deep-reasoner`/`fast-worker`. |
| Guardrail hooks | [`../../hooks/`](../../hooks/) | 13 families × `.sh` + `.ps1`; wired via `hooks/hooks.json` (plugin) or the settings templates (installer). |
| Profile manifest | [`../../profiles.json`](../../profiles.json) | The installer's source of truth for profile → skills/hooks/templates/agents. |
| Installers | [`../../install.sh`](../../install.sh) · [`../../install.ps1`](../../install.ps1) | Profile-aware, central-config + opt-in `~/.claude` linking. |
| Project linking | [`../../link-project.sh`](../../link-project.sh) · [`../../link-project.ps1`](../../link-project.ps1) | Links one project's `.claude/` to the central dir. |
| Hook wiring | [`../../scripts/wire-hooks.sh`](../../scripts/wire-hooks.sh) · [`wire-hooks.ps1`](../../scripts/wire-hooks.ps1) | Additive merge into `.claude/settings.json`. |
| Settings templates | [`../../settings.template.json`](../../settings.template.json) · [`../../settings.template.sh.json`](../../settings.template.sh.json) | Hook wiring templates (Windows / macOS-Linux). |
| Shared SDD templates (core) | [`../../specs/_templates/`](../../specs/_templates/) | Provider-neutral — reused by every adapter, including Codex. |

## Install

The primary path is the plugin (spec 044):

```bash
claude plugin marketplace add manujc00005/spec-driven-development   # or a local clone path
claude plugin install sdd@spec-driven-development
```

The profile-aware installer remains the alternative, exactly as documented in the main
[`README.md`](../../README.md) and [`docs/INSTALL.md`](../../docs/INSTALL.md):

```bash
./install.sh                    # core + default profile into the central config dir
./install.sh --link-user-claude # opt-in: link ~/.claude + copy agents
```

Nothing about the Claude adapter's files changed when the adapter layer was introduced, nor when the
plugin manifests were added — the manifests point at the directories that were already there.
