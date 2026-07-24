# Codex adapter

A first, **honest, prompt-based** adapter that runs the provider-neutral **SDD Core** workflow on
OpenAI Codex. It is additive: it introduces nothing into, and changes nothing about, the Claude Code
adapter.

> **Status: prompt-based, unverified against a live Codex CLI in this environment.** The `codex` CLI
> is not installed here, so the adapter is built on documented Codex conventions and has not been run
> against a real Codex session. See [`PARITY.md`](PARITY.md) for the full capability matrix and the
> explicit list of what does **not** carry over from the Claude adapter.

## What's in here

| File | Purpose |
|---|---|
| [`AGENTS.md`](AGENTS.md) | The SDD operating guide a Codex user drops into their project root. Workflow, roles, and guardrails-as-conventions. |
| [`prompts/`](prompts/) | The lifecycle-spine prompts (create → plan → analyze → implement → review → close + guardrails), each derived from its core skill. |
| [`PARITY.md`](PARITY.md) | Capability matrix and the honest "does NOT carry over" section. |
| [`config.example.toml`](config.example.toml) | An illustrative, unverified example config. The installer never edits your real config. |
| [`install-codex.sh`](install-codex.sh) · [`install-codex.ps1`](install-codex.ps1) | Self-contained, copy-only installer (dry-run, idempotent, backups). |

## What it uses from SDD Core (shared, not copied)

- The SPEC/PLAN/TASKS/DECISIONS templates in [`../../specs/_templates/`](../../specs/_templates/) —
  **the same** provider-neutral templates the Claude adapter uses.
- The workflow, review model, and guardrail *intent* documented in
  [`../../docs/PROVIDER_ADAPTERS.md`](../../docs/PROVIDER_ADAPTERS.md).

## Install

The installer is **copy-only** — it never runs the Codex CLI, never touches secrets or your existing
`~/.codex/config.toml`, and backs up any file it would overwrite. Preview first:

```bash
# from the repository root
./adapters/codex/install-codex.sh --dry-run          # writes nothing; prints planned actions
```

Then install. Prompts go to `~/.codex/prompts/` by default; **`AGENTS.md` is per-project and is
installed only when you pass `--target`** (it is never written to the current directory by default,
and never into the framework repo itself):

```bash
./adapters/codex/install-codex.sh --target /path/to/your/project
```

Flags:

- `--target DIR` — project root that receives `AGENTS.md`. **Required to install `AGENTS.md`**;
  without it, `AGENTS.md` is skipped (prompts still install). Refuses the framework repo root.
- `--codex-home DIR` — where prompts go (default: `~/.codex`; prompts land in `<codex-home>/prompts`).
- `--prompts-only` / `--agents-only` — copy just one part.
- `--dry-run` — preview; writes nothing.
- `--force` — overwrite a differing file (after a timestamped `.bak-<ts>` backup).

Windows: use `install-codex.ps1` with the PowerShell-equivalent flags (`-Target`, `-CodexHome`,
`-DryRun`, `-Force`, `-PromptsOnly`, `-AgentsOnly`).

> If your Codex release reads custom prompts from a different directory, pass `--codex-home` (or copy
> the `prompts/*.md` files there by hand) — they are plain markdown with no version-specific syntax.

## Use

1. Confirm `AGENTS.md` is at your project root and the prompts are where your Codex install reads
   them.
2. Drive the workflow prompt by prompt: create → plan → analyze → implement → review → close, running
   the guardrails pass before plan/implement/close.
3. **Uphold the guardrails yourself.** On Codex they are conventions, not enforced hooks — see
   [`PARITY.md`](PARITY.md). Nothing blocks a `git push` or a `Draft`-spec implementation for you.

## Honest limitations

- No enforced guardrails (no hook parity), no native subagents with `tools:` grants, no
  profile-filtered install, and only the lifecycle spine of skills — not the full 61-skill catalogue
  or the stack-specific reviewers. All of this is intentional and documented in
  [`PARITY.md`](PARITY.md); none of it is claimed to work and silently missing.
- Everything is **unverified against a live Codex CLI** until the follow-up in SPEC OQ-1 is done.
