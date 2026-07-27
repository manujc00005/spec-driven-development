# Codex adapter — capability & parity matrix

This is the honest, per-concept statement of what the Codex adapter implements relative to the
primary Claude Code adapter. **No parity is claimed.** Read this before relying on any behavior.

## Verification status

- **Prompt-based, unverified against a live Codex CLI in this environment.** The `codex` CLI is not
  installed here (`which codex` → not found), so nothing below was executed against a real Codex
  session. The adapter is built on **documented Codex conventions** (project-root `AGENTS.md`,
  custom prompts under `~/.codex/prompts/`, config at `~/.codex/config.toml`).
- Promotion to "verified" is a tracked follow-up (SPEC OQ-1 in
  `specs/features/019-provider-aware-codex-adapter/`): install Codex, run the lifecycle prompts,
  then update this file and `../README.md`.

## What carries over

| SDD Core concept | Claude adapter | Codex adapter | Status |
|---|---|---|---|
| SPEC / PLAN / TASKS / DECISIONS | shared `specs/_templates/` | **same** templates, verbatim | ✅ identical |
| Skill contracts (`## SDD Contract`) | on all 61 skills | reused as provider-neutral metadata | ✅ shared |
| Lifecycle steps (create→…→close) | `skills/*/SKILL.md` | `prompts/*.md` (spine) | ⚠️ prompt-based |
| Consistency gate | `/spec-analyze`, `/sdd-guardrails` | `prompts/sdd-spec-analyze.md`, `sdd-guardrails.md` | ⚠️ prompt-based |
| Generic review gate | `/spec-review`, `/qa-review` | `prompts/sdd-spec-review.md` (inline risk list) | ⚠️ prompt-based |
| Agent responsibility model | `agents/*.md` subagents (`tools:` grant) | roles in `AGENTS.md` | ⚠️ described as personas |
| Bounded context (Graphify optional) | optional, graceful | same doctrine | ✅ shared (external tool) |
| Token economy (`## Context budget`) | PLAN template + `/spec-analyze` check | shared PLAN template + mirrored check in `prompts/sdd-spec-analyze.md` | ⚠️ template shared, check prompt-based |
| PR-ready delivery / traceability | `/pr-description` + evidence chain | described in `AGENTS.md` | ⚠️ discipline, no PR tooling |

## What does NOT carry over (honest gaps)

| SDD Core concept | Claude adapter | Codex adapter | Status |
|---|---|---|---|
| **Deterministic guardrails** | `hooks/*.{sh,ps1}` block `git push`, gate on spec status, etc., at tool-call level via `.claude/settings.json` | **conventions in `AGENTS.md` only — NOT enforced** | ❌ no hook parity |
| **Native subagents** | 8 agents with restricted `tools:` grants (structural read-only enforcement) | roles the single session adopts; no enforced permission isolation | ❌ no native subagent grant |
| **Full skill catalogue** | 61 skills | 7-prompt lifecycle spine only | ❌ curated subset (DECISIONS D004) |
| **Stack-specific reviewers** | Java/Spring, payments, event-driven, Next/Prisma, SEO/GEO reviewer skills | not ported; folded into the generic review prompt's risk list | ❌ not ported in v1 |
| **Mindset manuals** | 9 skills flagged `provider_specific: true` | not ported (Claude-specific behavioral guidance) | ❌ intentionally excluded |
| **Profile-aware install** | `profiles.json` + `install.sh`/`install.ps1` filter by stack | copy-only installer, no profile filtering | ❌ no profile parity |
| **Central-config / project linking** | central dir + `~/.claude` + `.claude/` linking | `AGENTS.md` at project root; prompts in `~/.codex/prompts/` | ❌ different model |

## The biggest gap, stated plainly

On the Claude adapter, a `git push` is **mechanically blocked** by the `git-guardrails` hook and an
implementation against a `Draft` spec is refused by `sdd-spec-guard`. **On Codex none of that is
enforced** — the guardrails live only as instructions the model is asked to follow. Do not assume
any Codex action is blocked. If deterministic enforcement matters for your workflow, use the Claude
adapter, or add provider-side enforcement yourself and contribute it back as a tracked change.
