# Provider adapters

This directory is the **adapter layer** of the framework. It separates the portable workflow
(**SDD Core**) from the tool-specific packaging that runs it inside a particular AI coding agent.
For the full model, read [`../docs/PROVIDER_ADAPTERS.md`](../docs/PROVIDER_ADAPTERS.md).

> **SDD Core is provider-neutral. Adapters are how a specific tool runs it.** Claude Code is the
> primary shipped adapter; Codex is an additional, prompt-based adapter added honestly and
> incrementally.

## Adapter registry

| Adapter | Location | Status | Installer |
|---|---|---|---|
| **Claude Code** | repository root (`skills/`, `agents/`, `hooks/`, installers, settings templates) — see [`claude/README.md`](claude/README.md) | **Primary, shipped.** Live-verified for `deep-reasoner`/`fast-worker`; lifecycle agents schema/dry-run validated. | `install.sh` / `install.ps1` (profile-aware) |
| **Codex** | [`codex/`](codex/) | **Prompt-based. Unverified against a live Codex CLI in this environment** (`which codex` → not found). No parity claimed. | `codex/install-codex.sh` / `.ps1` (copy-only) |

> The Claude adapter is **not** stored under `adapters/claude/` — it *is* the repository root, and
> no file was moved there. `adapters/claude/README.md` is a pointer. This keeps `install.sh`,
> `install.ps1`, `profiles.json`, and every existing downstream install working unchanged. See
> `specs/features/019-provider-aware-codex-adapter/DECISIONS.md` D001.

## Capability / honesty matrix

What each adapter actually implements, per SDD Core concept. `✅` implemented · `⚠️` partial /
prompt-based · `❌` not implemented (honest gap).

| SDD Core concept | Claude Code | Codex | Notes |
|---|---|---|---|
| SPEC / PLAN / TASKS / DECISIONS lifecycle | ✅ shared `specs/_templates/` | ✅ **same** templates | Identical artifacts; the templates are provider-neutral. |
| Lifecycle steps (create→plan→analyze→implement→review→close) | ✅ `skills/*/SKILL.md` slash commands | ⚠️ prompts in `codex/prompts/` (lifecycle spine only) | Codex prompts derived from the same skill procedures; curated spine, not all 61 skills. |
| Consistency / guardrails gate | ✅ `/sdd-guardrails` skill | ⚠️ `codex/prompts/sdd-guardrails.md` | Same checks, prompt-driven. |
| Agent responsibility model | ✅ `agents/*.md` subagents (`tools:` grant) | ⚠️ roles described in `codex/AGENTS.md` | Codex has no verified native subagent/`tools:` grant here; roles are personas the model adopts. |
| Deterministic guardrails (block push, gate on spec status) | ✅ `hooks/*.{sh,ps1}` at tool-call level | ❌ **not enforced** — conventions in `AGENTS.md` only | The largest honest gap. Codex adapter does **not** claim hook parity. See `codex/PARITY.md`. |
| Profile-aware routing / install | ✅ `profiles.json` + installers | ❌ no profile filtering | Codex installer is copy-only; no `profiles.json` involvement. |
| Skill contracts (`## SDD Contract`) | ✅ on all 61 skills | ✅ reused as provider-neutral metadata | The `provider_specific` flag already anticipated this split. |
| Review gates (risk-triggered) | ✅ review skills | ⚠️ `codex/prompts/sdd-spec-review.md` (generic gate) | Stack-specific reviewers (Java/Spring, payments, …) not ported to Codex in v1. |
| Bounded context (Graphify optional) | ✅ optional, graceful degradation | ✅ same doctrine (external tool) | Graphify is external to both adapters; never mandatory, never `graph.json` wholesale. |
| PR-ready delivery / traceability | ✅ `/pr-description` + evidence chain | ⚠️ described in `AGENTS.md` | Same discipline; no Codex-native PR tooling claimed. |

## What "prompt-based, unverified" means for Codex

- The adapter is built on **documented Codex conventions** — a project-root `AGENTS.md`, custom
  prompts under `~/.codex/prompts/`, config at `~/.codex/config.toml`.
- The `codex` CLI is **not installed in this development environment**, so none of it was run
  against a live Codex. It is honest, useful, standards-based content — not a verified integration.
- Promotion to "verified" is a tracked follow-up (SPEC OQ-1): install Codex, run the prompts, then
  update this row and `codex/PARITY.md`.

## Adding another adapter

See the "How to add a new provider adapter" section in
[`../docs/PROVIDER_ADAPTERS.md`](../docs/PROVIDER_ADAPTERS.md). In short: additive only, never move
core or Claude files, ship a `PARITY.md` with an explicit gaps section, reuse `specs/_templates/`
verbatim, and label everything unverified until run against the real CLI.
