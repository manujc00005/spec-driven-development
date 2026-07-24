# Feature Spec: Provider-aware architecture and Codex adapter

## Status

In Review

## Problem

The framework markets itself as "provider-aware" (README, `docs/AGENTIC_ROUTING.md` "Provider
positioning", the `provider_specific` flag on every skill contract), but in practice it ships as a
single Claude Code adapter. Everything installable — skills as `SKILL.md`, agents with `tools:`
frontmatter, hooks wired through `.claude/settings.json`, the central-config + `~/.claude` linking
model — is Claude Code mechanism. There is no structural separation between the **provider-neutral
SDD workflow** and the **Claude-specific packaging** of it, and no second adapter demonstrating
that the separation is real.

A user on OpenAI Codex today gets nothing they can install: no operating instructions, no lifecycle
prompts, no honest statement of what does and does not carry over. The conceptual claim
("Spec-Driven Development should not depend on one AI tool") is not backed by an artifact.

## Goal

Introduce an explicit **provider-adapter layer** that separates SDD Core (provider-neutral) from
per-provider packaging, and ship a **first, honest, prompt-based Codex adapter** — without moving
or breaking any existing Claude Code file, installer, or downstream install.

Concretely:

- A documented core-vs-adapter architecture (`docs/PROVIDER_ADAPTERS.md`).
- An `adapters/` directory: `claude/` (a pointer to the shipped root, no files moved) and `codex/`
  (the new adapter).
- A Codex adapter built on documented Codex conventions (an `AGENTS.md` operating guide, a curated
  set of lifecycle prompts, an example config, a self-contained installer).
- A capability matrix that states, per SDD concept, what the Codex adapter implements and — just as
  importantly — what it does **not** (no hooks parity, no native subagents, no skill packaging).

## Non-goals

- **Not** replacing, moving, or renaming any Claude Code adapter file (`skills/`, `agents/`,
  `hooks/`, installers, settings templates stay exactly where they are).
- **Not** modifying `install.sh` / `install.ps1` / `link-project.*` / `wire-hooks.*` — their
  source-layout assumptions are Claude-shaped by design; retrofitting a `--provider` flag is out of
  scope and higher-risk than an additive adapter.
- **Not** claiming Codex feature parity. No claim that Codex has Claude-style skills, subagents, or
  tool-call hooks unless verified against a live Codex CLI.
- **Not** adding a provider dimension to `profiles.json` — it is the Claude installer's profile
  source of truth; overloading it creates an unvalidated drift surface (see DECISIONS D003).
- **Not** touching downstream/consumer projects.
- **Not** making Graphify mandatory, loading `graph.json` wholesale, creating swarms, autonomous
  runtimes, or a model router.

## Users / Actors

- **Codex user** — wants to run the SDD workflow on OpenAI Codex; needs operating instructions and
  lifecycle prompts they can install.
- **Framework maintainer** — needs the core/adapter boundary documented so future providers plug in
  the same way, and needs the honesty matrix to prevent overclaiming.
- **Claude Code user (existing)** — must be entirely unaffected: same files, same installers, same
  behavior.
- **Future-provider integrator** — wants a worked example of what "add an adapter" means.

## Current behavior

- SDD Core concepts (SPEC/PLAN/TASKS/DECISIONS, review gates, skill contracts, agent
  responsibilities, guardrails, bounded context, PR-ready delivery) exist only as Claude Code
  packaging.
- `provider_specific` is a per-skill boolean, but nothing consumes the distinction to produce a
  non-Claude artifact.
- `docs/AGENTIC_ROUTING.md` states, honestly, that no other provider is integrated "today."

## Desired behavior

- The repository has a named **SDD Core** (provider-neutral) and a named **adapter layer**.
- `adapters/codex/` is installable via its own self-contained script and usable by a Codex user.
- Every Codex-adapter artifact carries an explicit verification-status and honesty note.
- The Claude Code adapter is unchanged and remains the primary shipped adapter.
- CI (`scripts/check-consistency.sh`) stays green with no changes required.

## Functional requirements

- **FR-001:** Ship `docs/PROVIDER_ADAPTERS.md` describing SDD Core (the portable part), the adapter
  layer, and how a provider maps onto the core. It names the honesty principle explicitly.
- **FR-002:** Create `adapters/` with a top-level `README.md` that is the authoritative **adapter
  registry** and **capability/honesty matrix** (core concept → Claude mechanism → Codex mechanism →
  status).
- **FR-003:** `adapters/claude/README.md` documents that the shipped Claude adapter **is the repo
  root** (skills/agents/hooks/installers/templates) and that no files were moved; it is a pointer,
  not a copy.
- **FR-004:** `adapters/codex/` ships: `README.md` (what it is + verification status), `PARITY.md`
  (capability matrix specific to Codex), `AGENTS.md` (provider-neutral SDD operating guide for
  Codex), `prompts/` (a curated core-lifecycle prompt set derived from the portable skills),
  `config.example.toml` (clearly-labeled example), and `install-codex.{sh,ps1}`.
- **FR-005:** The Codex prompts cover the portable lifecycle spine — spec-create, spec-plan,
  spec-analyze, spec-implement, spec-review, spec-close, and the guardrails/consistency gate — each
  faithfully derived from the corresponding Claude skill's procedure, with a header noting its
  origin and provider-neutrality.
- **FR-006:** `install-codex.{sh,ps1}` operate **only within the Codex adapter**: they copy
  `AGENTS.md` and `prompts/` into a user-specified target (project dir and/or the documented
  `~/.codex` locations), support `--dry-run`, are idempotent, never delete, and back up before
  overwriting — mirroring the repo's existing installer safety ethos. They carry an explicit
  "unverified against a live Codex CLI in this environment" note.
- **FR-007:** Every Codex-adapter document states honestly what does **not** carry over: no hook
  enforcement, no native subagent/`tools:` grant, no skill packaging, no profile-filtered install.
  Guardrails are described as **conventions the model must follow**, not enforced tool-call hooks.
- **FR-008:** `README.md` gains a short, honest "Provider adapters" pointer and the "Current
  support" Codex row is updated to reference the shipped adapter — without claiming parity and
  without changing any `<!-- count:* -->` marker.
- **FR-009:** No change to `profiles.json`, the Claude installers, the hook scripts, the settings
  templates, or any `skills/**`, `agents/**`, `hooks/**` file.
- **FR-010:** Ship a thin convenience wrapper (`install-all.sh` / `install-all.ps1`) that installs
  both adapters by **calling** the two existing installers in order — never modifying or
  reimplementing them — with `--skip-claude`/`--skip-codex`, `--dry-run`/`--force` (both), and
  passthrough for each installer's own flags (DECISIONS D006).
- **FR-011:** The Codex installer writes `AGENTS.md` **only when an explicit target is given**
  (`--target`/`-Target`, or `--codex-target` via the wrapper); with no target it skips `AGENTS.md`
  and installs only the global prompts. It **refuses** to write `AGENTS.md` into the framework repo
  root (DECISIONS D007). No file is ever silently created in the current directory.

## Non-functional requirements

- **Performance:** N/A (documentation + copy scripts).
- **Security:** The Codex installer must not run networked operations, must not touch secrets or
  `settings.local.json`, and must not execute the Codex CLI. It is copy-only.
- **Observability:** Installer prints per-file actions (`[copy]`, `[skip]`, `[backup]`, `[dry-run]`)
  like the existing installers.
- **Maintainability:** Codex prompts are derived from, and cross-linked to, their core skill so
  drift is visible to a human reviewer. No new machine-validated surface is added that CI does not
  cover (the adapter registry stays human-authoritative — DECISIONS D003).

## API / Interface changes

- New CLI surface (opt-in, self-contained): `adapters/codex/install-codex.sh [--target DIR]
  [--codex-home DIR] [--dry-run] [--force]` and the PowerShell twin. No change to any existing CLI.
- New convention files a Codex user consumes: a project-root `AGENTS.md` and `~/.codex/prompts/*.md`
  (documented Codex conventions; see DECISIONS D002 on verification status).

## Data model changes

None. No schema, no `profiles.json` change.

## Edge cases

- Codex CLI absent from the environment (the case in this dev environment): the installer still
  works (it is copy-only) and every doc flags the unverified status. Verification is a tracked
  follow-up, not a blocker — mirrors how the repo tracked live-vs-structural agent verification.
- `~/.codex` does not exist on the target: installer creates only the subpath it is asked to write,
  after confirming/`--dry-run`, and never assumes the path is correct — it documents the assumption.
- A Codex user also uses Claude Code in the same repo: `AGENTS.md` (Codex) and `CLAUDE.md` (Claude)
  coexist; neither adapter writes the other's files.
- CI orphan/consistency checks: all new files live under `adapters/`, `docs/` (not `docs/_templates/`),
  and `specs/features/019-*` — none of the directories `check-consistency.sh` scans for
  skills/hooks/templates/agents — so no orphan or drift is introduced.

## Acceptance criteria

- **AC-001:** `docs/PROVIDER_ADAPTERS.md` exists and defines SDD Core vs adapters and the honesty
  principle. (FR-001)
- **AC-002:** `adapters/README.md` exists and contains the adapter registry + capability/honesty
  matrix. (FR-002)
- **AC-003:** `adapters/claude/README.md` documents the pointer model with no Claude file moved.
  (FR-003)
- **AC-004:** `adapters/codex/` contains `README.md`, `PARITY.md`, `AGENTS.md`, `config.example.toml`,
  `install-codex.sh`, `install-codex.ps1`, and `prompts/` with the lifecycle spine. (FR-004, FR-005)
- **AC-005:** Every Codex-adapter doc carries an explicit verification-status note and an explicit
  "what does not carry over" statement (no hooks/subagents/skills/profile parity). (FR-006, FR-007)
- **AC-006:** `install-codex.sh --dry-run` writes nothing and prints the planned actions; a real run
  is idempotent and backs up on overwrite. (FR-006)
- **AC-007:** `git status` shows **no** modification to `profiles.json`, `install.sh`, `install.ps1`,
  `link-project.*`, `scripts/wire-hooks.*`, `settings.template*.json`, or any `skills/`, `agents/`,
  `hooks/` file. (FR-009)
- **AC-008:** `bash scripts/check-consistency.sh` exits 0 (no drift) after the change. (FR-008,
  FR-009)
- **AC-009:** `README.md` references the adapter layer honestly, with no `<!-- count:* -->` marker or
  shields badge value changed. (FR-008)
- **AC-010:** `install-all.sh` installs both adapters in order and forwards flags; `--dry-run` writes
  nothing; `--skip-claude`/`--skip-codex` run only the other; an unknown flag exits non-zero; a
  Claude-step failure skips Codex. It does not modify `install.sh`/`install.ps1`. (FR-010)
- **AC-011:** `install-codex.sh` with no `--target` skips `AGENTS.md` (prompts still install) and
  leaves the current directory untouched; with `--target <framework-root>` it refuses; with
  `--target <project>` it installs `AGENTS.md` there. `install-all.sh` with no `--codex-target` never
  writes `AGENTS.md`. (FR-011)

## Test scenarios

- **Unit:** N/A (no application code).
- **Integration:** Run `adapters/codex/install-codex.sh --dry-run --target <tmp>` and a real
  `--target <tmp>` twice; assert dry-run writes nothing, first real run copies, second run is a
  reported no-op, and overwriting a modified file produces a timestamped backup.
- **E2E:** N/A (Codex CLI not present; documented as unverified follow-up).
- **Manual:** Read each adapter doc and confirm the honesty/verification notes are present; confirm
  `git status` matches AC-007; run `check-consistency.sh`.

## Assumptions

- Codex consumes a project-root `AGENTS.md` and custom prompts from `~/.codex/prompts/*.md`, and is
  configured via `~/.codex/config.toml`. These are **documented Codex conventions**, treated as
  unverified in this environment because the `codex` CLI is not installed here (`which codex` →
  not found). Every artifact says so. See DECISIONS D002.
- The AGENTS.md convention is a genuine cross-tool open standard, so the operating guide is useful
  even if a specific Codex prompt path later proves different.

## Open questions

- **OQ-1:** Exact Codex custom-prompt directory and config schema on the current Codex release —
  resolve by verifying against an installed Codex CLI before advertising the adapter as "verified".
  Until then the adapter is labeled prompt-based/unverified.

## Contracted services

Read `specs/SERVICES.md`. Absent in this repo → all billable add-ons treated as NOT contracted
(conservative default). This feature ships no billable service; the `seo-geo-addon` gating is
unaffected.
