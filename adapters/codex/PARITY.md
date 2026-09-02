# Codex adapter — capability & parity matrix

This is the honest, per-concept statement of what the Codex adapter implements relative to the
primary Claude Code adapter. **No parity is claimed.** Read this before relying on any behavior.

## Verification status

- **Prompt-based; autonomous-mode smoke verification pending.** `codex-cli
  0.147.0-alpha.6.6` is available in this environment. The adapter remains based on **documented
  Codex conventions** (project-root `AGENTS.md`, custom prompts under `~/.codex/prompts/`, config at
  `~/.codex/config.toml`); presence of the binary does not make its instructions deterministic.
- Promotion to "verified" is a tracked follow-up (SPEC OQ-1 in
  `specs/features/019-provider-aware-codex-adapter/`): install Codex, run the lifecycle prompts,
  then update this file and `../README.md`.

## What carries over

| SDD Core concept | Claude adapter | Codex adapter | Status |
|---|---|---|---|
| SPEC / PLAN / TASKS / DECISIONS | shared `specs/_templates/` | **same** templates, verbatim | ✅ identical |
| Skill contracts (`## SDD Contract`) | on all 71 skills | reused as provider-neutral metadata | ✅ shared |
| Lifecycle steps (create→…→close) | `skills/*/SKILL.md` | `prompts/*.md` (spine) | ⚠️ prompt-based |
| Consistency gate | `/spec-analyze`, `/sdd-guardrails` | `prompts/sdd-spec-analyze.md`, `sdd-guardrails.md` | ⚠️ prompt-based |
| Generic review gate | `/spec-review`, `/qa-review` | `prompts/sdd-spec-review.md` (inline risk list) | ⚠️ prompt-based |
| Agent responsibility model | `agents/*.md` subagents (`tools:` grant) | roles in `AGENTS.md` | ⚠️ described as personas |
| Bounded context (Graphify optional) | optional, graceful | same doctrine | ✅ shared (external tool) |
| Token economy (`## Context budget`) | PLAN template + `/spec-analyze` check | shared PLAN template + mirrored check in `prompts/sdd-spec-analyze.md` | ⚠️ template shared, check prompt-based |
| PR-ready delivery / traceability | `/pr-description` + evidence chain | described in `AGENTS.md` | ⚠️ discipline, no PR tooling |
| Autonomous orchestration protocol | native delegated roles + file blackboard | one session, sequential roles + the same file blackboard | ⚠️ protocol-equivalent, no fan-out |

## What does NOT carry over (honest gaps)

| SDD Core concept | Claude adapter | Codex adapter | Status |
|---|---|---|---|
| **Deterministic guardrails** | `hooks/*.{sh,ps1}` block `git push`, gate on spec status, etc., at tool-call level via `.claude/settings.json` | **conventions in `AGENTS.md` only — NOT enforced** | ❌ no hook parity |
| **Native subagents** | 8 agents with restricted `tools:` grants (structural read-only enforcement) | roles the single session adopts; no enforced permission isolation | ❌ no native subagent grant |
| **Full skill catalogue** | 71 skills | 7-prompt lifecycle spine only | ❌ curated subset (DECISIONS D004) |
| **Stack-specific reviewers** | Java/Spring, payments, event-driven, Next/Prisma, SEO/GEO reviewer skills | not ported; folded into the generic review prompt's risk list | ❌ not ported in v1 |
| **Python/SQL/data reviewers** | `python-reviewer`, `sql-query-reviewer`, `database-performance-reviewer`, `data-pipeline-reviewer`, `python-testing-reviewer` (`python-sql-data` profile, spec 029) | not ported | ❌ not ported — same reason as the rest of the reviewer catalogue |
| **Delivery/operations reviewers** | `deployment-review`, `container-review`, `pipeline-review`, `release-readiness` (`delivery-operations` profile, spec 024) | not ported | ❌ not ported — deferred, see below |
| **Mindset manuals** | 9 skills flagged `provider_specific: true` | not ported (Claude-specific behavioral guidance) | ❌ intentionally excluded |
| **Profile-aware install** | `profiles.json` + `install.sh`/`install.ps1` filter by stack | copy-only installer, no profile filtering | ❌ no profile parity |
| **Central-config / project linking** | central dir + `~/.claude` + `.claude/` linking | `AGENTS.md` at project root; prompts in `~/.codex/prompts/` | ❌ different model |

## Delivery/operations profile — deferred, not overlooked

Spec 024 added a `delivery-operations` profile (deploy procedure, containers, CI/CD, release
gating) to the Claude adapter. It is **not** ported here, for the same reason the other
stack-specific reviewers are not, plus one more: the `codex` CLI is not installed in this
environment, so any prompt written for it would ship unverified against a real provider CLI. An
honest gap row is worth more than an unverifiable prompt. Porting remains a tracked follow-up
alongside the rest of the reviewer catalogue.

## Autonomous orchestration — sequential degradation

`sdd-orchestrate --autonomous <feature-path>` is a shared protocol, not a claim that Codex has the
Claude adapter's Agent tool. On Codex, one session adopts each role sequentially and must obey the
same contract in `skills/sdd-orchestrate/SKILL.md`:

- the same six-condition entry gate, including default-branch, unattributed-dirty-tree, and
  green-but-mutating-baseline refusals;
- the same final YAML reviewer verdict and worker completion blocks;
- the same per-feature `ORCHESTRATION.md` blackboard, durable attempt lifecycle, findings registry,
  counters, append-only logs, and diff-fingerprinted approvals;
- the same conservative technical-versus-human escalation classifier;
- the same all-stale-reviewer invalidation after a changed fingerprint;
- the same monotonic iteration/delegation caps, recoverable/non-resumable abort distinction,
  fail-closed malformed-output behavior, and DONE/PAUSED/ABORTED conditions;
- the same frozen implementation fingerprint and separately audited lifecycle/PR closure delta;
- the same prohibition on commit, push, merge, secrets, real migrations, and direct SPEC status
  edits;
- the same `--adopt` entry for a feature already `In Progress` (spec 041): the same adoption gate
  (`In Progress` only, fully clean tree, non-default branch, green baseline, and a computable
  inherited record — baseline commit, merge-base with the default branch, checked tasks), the same
  `Inherited` table and adoption header fields in `ORCHESTRATION.md`, and the same inherited-diff
  review by `domain-reviewer` (and `security-reviewer` on the usual triggers) before any new task,
  run sequentially in the one context like every other role.

**Where the autonomous evidence actually comes from.** Unusually for this adapter, most of the
autonomous-mode behavioral evidence is **Codex-only**: the happy path, the entry-gate matrix, the
agent-contract conformance, the escalation classifier and the finding dedup were all observed on
Codex and never re-run on Claude Code. Claude Code carries the non-convergence abort, the
malformed-block recovery and the cap-semantics runs. Both providers therefore have real evidence,
but neither has all of it. This asymmetry is accepted, not pending: the protocol's state lives in
files and is deliberately provider-neutral, so re-running those five on the other provider would
spend real runs proving something the design already makes provider-independent. It is recorded
here so nobody later mistakes "verified" for "verified on both".

There is no parallel fan-out, isolated context, or enforced tool grant. Role switches happen inside
one context, so persisted file state—not conversation memory—is authoritative after compaction or
resume. A Codex run may preserve protocol behavior, but it cannot claim permission-isolation parity.
The live smoke result belongs in the active feature's `CALIBRATION.md`; until it passes, autonomous
Codex support is documented but not closure evidence. The adoption entry is held to the same
standard: spec 041 documents it here and records its Codex smoke run as a pass or as an explicit
closure blocker, never as an assumed parity.

## The biggest gap, stated plainly

On the Claude adapter, a `git push` is **mechanically blocked** by the `git-guardrails` hook and an
implementation against a `Draft` spec is refused by `sdd-spec-guard`. **On Codex none of that is
enforced** — the guardrails live only as instructions the model is asked to follow. Do not assume
any Codex action is blocked. If deterministic enforcement matters for your workflow, use the Claude
adapter, or add provider-side enforcement yourself and contribute it back as a tracked change.
