# Provider adapters: SDD Core vs. provider packaging

Spec-Driven Development is a **workflow**, not a tool. This document defines the boundary between the
portable workflow (**SDD Core**) and the tool-specific packaging that makes it runnable inside a
particular AI coding agent (**a provider adapter**), and states the principle that keeps the split
honest.

> **Spec-Driven Development should not depend on one AI tool.** Claude Code is the primary shipped
> adapter. Other providers are additional adapters over the same core — added honestly and
> incrementally, never by overclaiming parity.

## The two layers

```
SDD Core  (provider-neutral — the portable workflow)
├── specs/                     SPEC · PLAN · TASKS · DECISIONS lifecycle + templates
├── review gates               risk-triggered, evidence-based review model
├── skill contracts            the ## SDD Contract metadata each skill carries
├── agent responsibility model research / architecture / implementation / review roles
├── deterministic guardrails   the rules (block push, gate on spec status, …) — as intent
├── bounded context            Graphify-optional, never-load-graph.json-wholesale doctrine
└── PR-ready delivery          traceability from acceptance criterion to diff to evidence

provider adapters/  (how a specific tool runs the core)
├── claude/   →  the repository root (skills/, agents/, hooks/, installers, settings templates)
└── codex/    →  adapters/codex/ (AGENTS.md operating guide + lifecycle prompts + installer)
```

### SDD Core — the portable part

These concepts do not depend on any AI tool. They are the same whether a human, Claude Code, or
Codex drives them:

- **SPEC / PLAN / TASKS / DECISIONS** — durable artifacts under `specs/`, from shared templates in
  `specs/_templates/`.
- **Review gates** — what gets reviewed is a function of what the change touches, not of the tool.
- **Skill contracts** — every skill declares a provider-neutral `## SDD Contract`
  (`category`, `primary_agent`, `writes_code`/`writes_specs`/`analysis_only`, `side_effects`,
  `profile_scope`, and a `provider_specific` flag). See
  `specs/features/018-agentic-routing-and-skill-contracts/CONTRACT_SCHEMA.md`.
- **Agent responsibility model** — the six lifecycle responsibilities (research, architecture,
  implementation, security review, domain review, final conformance) are role definitions, not a
  Claude mechanism. See [`AGENTIC_ROUTING.md`](AGENTIC_ROUTING.md).
- **Deterministic guardrails** — the *intent* (never push silently, do not implement against a
  `Draft` spec, do not load `graph.json` wholesale) is portable; the *enforcement mechanism* is
  provider-specific (see below).
- **Bounded context** — Graphify is an optional accelerator, never a source of truth, and its raw
  graph is never loaded wholesale.
- **PR-ready delivery** — an acceptance criterion maps to a task maps to a diff maps to evidence,
  regardless of tool.

### Provider adapter — the tool-specific part

An adapter packages the core so a specific agent can run it. What is provider-specific:

| Core concept | Provider-specific packaging |
|---|---|
| Lifecycle steps | Claude: `skills/*/SKILL.md` slash commands. Codex: prompts under `~/.codex/prompts/`. |
| Agent roles | Claude: `agents/*.md` subagents with a `tools:` grant. Codex: roles described in `AGENTS.md` (no native subagent grant). |
| Guardrail enforcement | Claude: `hooks/*.{sh,ps1}` wired into `.claude/settings.json` (tool-call level). Codex: conventions stated in `AGENTS.md` (**not** enforced). |
| Profile-aware install | Claude: `profiles.json` + `install.sh`/`install.ps1`. Codex: a self-contained copy script; no profile filtering. |
| Plugin install (spec 044) | Both hosts: the repository root is the `sdd` plugin (`.claude-plugin/`, `.codex-plugin/`), whole content, no profile filtering; hooks travel only to Claude Code via `hooks/hooks.json`. |
| Project linking | Claude: `.claude/` linking + central config. Codex: `AGENTS.md` at project root. |

## The honesty principle

Adding a provider is only allowed to state what is **actually implemented and verified**. In
practice:

1. **Never claim a capability another tool lacks.** If Codex has no verified tool-call hook system,
   the adapter says guardrails are conventions, not enforcement — it does not imply `git push` is
   blocked.
2. **Separate "described" from "verified".** An adapter built from documented conventions but not
   run against a live CLI is labeled *prompt-based / unverified* until a real run confirms it — the
   same structural-vs-live distinction this repo already draws for its agents.
3. **No parity by assertion.** "Compatible workflow" ≠ "feature parity." The capability matrix in
   [`../adapters/README.md`](../adapters/README.md) and each adapter's `PARITY.md` state the gaps
   explicitly.
4. **The core is not diluted to fit an adapter.** If a provider cannot express a core concept, the
   gap is documented; the core is not weakened to hide it.

## How to add a new provider adapter

1. Do **not** move or modify the Claude adapter or any shared core file (`specs/_templates/`,
   `profiles.json`, `scripts/`). The core is shared; adapters are additive.
2. Create `adapters/<provider>/` with, at minimum: a `README.md` (purpose + verification status), a
   `PARITY.md` (capability matrix incl. an explicit "does NOT carry over" section), an operating
   guide the provider consumes, and — if installable — a **self-contained, copy-only** installer
   that touches nothing outside the adapter and its target.
3. Map each core concept to a provider mechanism, or record it as a gap. Reuse the shared
   `specs/_templates/` verbatim — the SPEC/PLAN/TASKS/DECISIONS artifacts are the same across
   providers.
4. Add a row to the registry in [`../adapters/README.md`](../adapters/README.md).
5. Label everything unverified until run against the provider's real CLI; then promote status.

## Current adapters

- **Claude Code** — primary, shipped. Lives at the repository root; see
  [`../adapters/claude/README.md`](../adapters/claude/README.md).
- **Codex** — prompt-based; the plugin installs into it (verified on `codex-cli 0.152.1`, spec 044) while its lifecycle prompts remain unverified end-to-end; see
  [`../adapters/codex/README.md`](../adapters/codex/README.md).
