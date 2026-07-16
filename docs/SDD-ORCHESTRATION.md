# SDD multi-model orchestration

Multi-model delegation layer for the SDD workflow: the main session orchestrates, an
Opus agent reasons, a Sonnet agent implements. Shipped by this repo since profiles.json
`0.4.0` (feature `specs/features/004-multimodel-orchestration/`).

## What problem this solves

Without orchestration, one model does everything in one context: expensive models burn
tokens on boilerplate, the main context fills up with file dumps and diffs, and there is
no policy for who decides architecture vs. who types the code. Orchestration keeps the
main session focused on requirements, decisions, and validation, and pushes heavy
reading (analysis) and heavy writing (implementation) into subagents with the right
model for each job.

## Architecture

```
User
  ↓
Main orchestrator (session — Fable when available)
  ├── deep-reasoner → Opus   (analysis, read-only)
  └── fast-worker   → Sonnet (implementation, tests, verifications)
  ↓
Review, validation against acceptance criteria, final synthesis
```

| Role | Model | Responsibility |
|---|---|---|
| Orchestrator | Fable (main session) | Understand the goal, locate SDD docs, classify the task, detect ambiguity, decide delegation, turn analysis into implementable tasks, review every result, run/coordinate verifications, check acceptance criteria, keep TASKS.md and DECISIONS.md in sync. Avoids extensive mechanical work. |
| `deep-reasoner` | Opus | Architecture, system design, complex debugging, root cause, security, concurrency, idempotency, race conditions, data consistency, delicate migrations, algorithm design, distributed systems, risk analysis, SPEC/PLAN review, high-risk implementation review, contradictory requirements. Read-only (`tools: Read, Grep, Glob`); returns a fixed structured report. |
| `fast-worker` | Sonnet | Approved tasks, code changes, tests, mechanical refactors, type fixes, boilerplate, docs, formatting, pre-decided small changes, running verifications. Stops on undocumented architectural decisions. |

## Task classification

| Level | Examples | Flow |
|---|---|---|
| 1 — Trivial | copy, translations, small visual tweaks, formatting, a simple test, no-domain-impact type changes | Orchestrator → fast-worker → validation. **Never Opus.** |
| 2 — Normal | feature with clear SPEC, bounded bug, non-critical business logic | Orchestrator → initial investigation → PLAN/TASKS → fast-worker → tests → final review. deep-reasoner only if ambiguity/risk appears. |
| 3 — High risk | payments/Stripe, webhooks, security, authorization, personal data, migrations, concurrency, distributed systems, idempotency, race conditions, architecture changes, cross-cutting refactors, bugs without clear root cause | Orchestrator → deep-reasoner → PLAN → small TASKS → fast-worker → tests → risk review → final validation. |
| 4 — Investigation/audit | security audit, payments audit, architecture analysis, root-cause hunt, proposal evaluation | Orchestrator → deep-reasoner → report. **No implementation** unless explicitly requested. |

## SDD flow (7 phases)

1. **Discovery** — inspect repo, locate related features/SPEC, classify, decide delegation.
2. **Specify** — create/update `SPEC.md` (existing `/spec-create` conventions).
3. **Plan** — Level 3 delegates analysis to deep-reasoner; the orchestrator reviews it
   critically and writes the final `PLAN.md` itself (never a blind paste).
4. **Tasks** — `TASKS.md` with small, ordered, verifiable tasks (stable IDs T001…), zero
   open architectural decisions.
5. **Implement** — task-by-task delegation to fast-worker with a full brief (objective,
   allowed files, SDD docs, requirements, affected ACs, mandatory tests, restrictions,
   what not to touch, response format). Parallel only when file/contract/migration/state/
   test overlap is impossible.
6. **QA** — real diff review, scope check, per-AC check, tests/typecheck/lint/build,
   regression, no secrets, migrations/config review. deep-reasoner may review high-risk
   changes; the orchestrator decides.
7. **Close** — mark tasks done, update DECISIONS.md, traceability, summary of executed
   and NOT executed validations, pending risks. Never declare success with unresolved
   failures.

## Optional: Architecture Context with Graphify

Projects may optionally use **Graphify** (external tool) to generate dependency graphs for architecture context:

- **When:** Before `/spec-plan` or `/spec-analyze` on medium/large features (optional accelerator).
- **What:** If `.graphify/GRAPH_REPORT.md` exists (legacy fallback: root `GRAPH_REPORT.md`), SDD skills use it to understand module interdependencies and impact.
- **Graph-first (token saving):** when the report exists, `context-manager` and `graphify-context` derive the bounded reading list from the graph — preferring `graphify review-context` / `affected-flows` CLI queries when available — before any repo-wide scan. Heuristic scanning is the fallback, not the default.
- **Graceful degradation:** If Graphify is absent, SDD continues with heuristic analysis. Workflows are unaffected.
- **Setup:** Run `scripts/setup-graphify.sh --project-dir <project>` from the SDD checkout (installs the CLI after confirmation, generates `.graphify/`, scaffolds curated docs).
- **Freshness:** the `graphify-stale-reminder` hook auto-refreshes the graph in the background on `SessionStart` when it is missing/stale and the CLI is installed (`SDD_GRAPHIFY_AUTO=0` disables).
- **Reference:** See `docs/_templates/GRAPHIFY.md` for the full integration guide.

Graphify is a productivity accelerator, not a requirement. SDD works fully without it.

## Cost control

- Fable coordinates/decomposes/synthesizes; Opus only for hard reasoning and high-risk
  review; Sonnet for implementation and mechanical work.
- Never Opus for copy/format/boilerplate/trivial changes.
- Delegate by objective with a bounded brief; never dump the conversation.
- Request summarized, structured responses (both agents have fixed output formats).
- Reuse findings; no redundant investigations; one solid delegation over several
  speculative ones.
- Don't delegate what the main session resolves trivially at lower cost.
- Limit each agent's read/edit scope when viable.

## Model fallback

| Scenario | Configuration |
|---|---|
| Fable available (default) | Fable main · Opus deep-reasoner · Sonnet fast-worker |
| Fable unavailable | Sonnet main (`claude --model sonnet` or `/model`) · Opus deep-reasoner · Sonnet fast-worker in separate contexts |
| Opus unavailable | Sonnet as temporary deep-reasoner (general-purpose subagent + model override); record in DECISIONS.md that the analysis did not use the preferred model |
| Sonnet unavailable | Nearest available model via Agent-tool override; never invent identifiers |
| Agents not installed | General-purpose subagents with explicit `opus`/`sonnet` override + the same brief; re-run the installer |

To change the main model permanently, set it in Claude Code (`/model` in an interactive
session, or `claude --model <alias>`); the agents' models live in their frontmatter
(`agents/*.md`, `model:` key) and use aliases (`opus`, `sonnet`) so they track upgrades.

Verified against Claude Code **2.1.207**: agent frontmatter keys `name`, `description`,
`model`, `tools`; model aliases `opus`, `sonnet`, `haiku`, `fable`.

## Installation

Everything ships from this repo through `profiles.json` (core profile) — there is no
second source of truth.

```powershell
# Windows — into the central dir, then copy agents into your ~/.claude/agents
.\install.ps1
.\install.ps1 -LinkUserClaude
```

```bash
# macOS/Linux
./install.sh
./install.sh --link-user-claude
```

```powershell
# Wire one specific project (junctions skills/hooks, copies agents)
.\link-project.ps1 -ProjectDir C:\code\my-app
```

**Agents are copied per-file, never linked** — `~/.claude/agents` and project
`.claude/agents` commonly contain user/project-authored agents that a directory link
would hide. Consequence: after `git pull`, re-run the installer (and `link-project` where
used) to refresh agents; skills/hooks still update instantly through their links.

Updating an existing setup is the same command — the installers are idempotent and
additive: identical files are no-ops, differing files (your customizations) are skipped
and reported, and overwriting requires `-Force`/`--force` which takes a timestamped
backup first. Preview with `-DryRun`/`--dry-run`.

Finally, merge the block between `<!-- SDD-ORCHESTRATION:START -->` and
`<!-- SDD-ORCHESTRATION:END -->` from `CLAUDE.md.example` into your real `CLAUDE.md`
(user-level or per-project). The installers never write a real `CLAUDE.md` — that is a
deliberate safety invariant — so this merge is a manual (or explicitly prompted) step.
To update the block later, replace only what is between the markers.

## Usage

```
/sdd-orchestrate <free-form goal>
```

**Example 1 — small change**

```
/sdd-orchestrate Increase the secure-payment icon size without changing the layout.
```
Expected: orchestrator → fast-worker → visual/component tests. No Opus, no ceremony.

**Example 2 — complex payment-provider bug**

```
/sdd-orchestrate Investigate why an order shows as cancelled in the admin panel but no
matching event exists in the payment provider. Do not implement until the root cause is found.
```
Expected: orchestrator → deep-reasoner (root cause) → SPEC/PLAN/TASKS → fast-worker → QA.

**Example 3 — audit (no implementation)**

```
/sdd-orchestrate Audit webhook idempotency and deliver prioritized findings.
Do not modify code.
```
Expected: orchestrator → deep-reasoner → prioritized report. Nothing implemented.

### When to use Opus (deep-reasoner)

Architecture, root cause, security, concurrency/idempotency/races, data consistency,
delicate migrations, distributed systems, high-risk review, contradictory requirements.

### When NOT to use Opus

Copy, translations, formatting, boilerplate, simple tests, pre-decided small changes,
anything Level 1–2 without ambiguity — that is fast-worker (or the main session) work.

## Managed vs. customizable

| Managed by this repo (refreshed on install) | Yours to customize (never auto-touched) |
|---|---|
| `<central>/agents/deep-reasoner.md`, `fast-worker.md` | Your real `CLAUDE.md` (any level) |
| `<central>/skills/sdd-orchestrate/` | Copied agents you've edited (installer skips them as "differs") |
| `CLAUDE.md.example` orchestration block (between markers) | Everything outside the markers |
| `docs/SDD-ORCHESTRATION.md` | Project `.claude/settings*.json` (never touched) |

## Verifying the integration

```powershell
# Agents present where Claude Code reads them
Get-ChildItem "$env:USERPROFILE\.claude\agents\deep-reasoner.md", "$env:USERPROFILE\.claude\agents\fast-worker.md"
# Skill present through the junction
Get-ChildItem "$env:USERPROFILE\.claude\skills\sdd-orchestrate"
```

Then start a new Claude Code session: the agents appear in the available-agents list and
`/sdd-orchestrate` autocompletes. (Agent/skill discovery happens at session start.)

The full reproducible live-check procedure — dry-run preview, deploy commands, file
verification, and the four pass/fail criteria (both agents listed with the right models,
the skill autocompleting, and a trivial probe delegation succeeding) — is maintained in
[`specs/features/004-multimodel-orchestration/TASKS.md`](../specs/features/004-multimodel-orchestration/TASKS.md).
It **passed on 2026-07-13** on the reference setup (fresh session recognized both agents
with the correct models and the command). Re-run it after any `git pull` + reinstall;
structural verification alone is never reported as a live PASS.

## Troubleshooting

- **`/sdd-orchestrate` not found** — the skill is read through `~/.claude/skills` (or
  the project's `.claude/skills`); re-run the installer and check the junction/symlink
  (`Get-Item ~\.claude\skills -Force | Select LinkType,Target`). New session required.
- **Agents not offered** — check the files exist in `~/.claude/agents/` (they are
  *copied*, not linked — see above), and that frontmatter starts at line 1 with `---`.
- **`model: opus`/`sonnet` rejected** — your Claude Code version may predate alias
  support; update Claude Code (verified on 2.1.207). Do not substitute invented IDs.
- **deep-reasoner tries to edit** — it has no edit tools; if you customized `tools:`,
  restore `Read, Grep, Glob`.
- **Installer says an agent "differs"** — that copy has local customizations; keep them,
  or `-Force`/`--force` to overwrite (backup taken automatically).

## Disabling / rollback

This integration is additive; removing it restores the previous behavior exactly:

1. Delete `deep-reasoner.md` and `fast-worker.md` from `~/.claude/agents/` and from any
   project `.claude/agents/` they were copied into (they are plain files; deleting them
   affects nothing else).
2. Delete `<central>/agents/` and `<central>/skills/sdd-orchestrate/`.
3. Remove the `<!-- SDD-ORCHESTRATION:START -->`…`<!-- SDD-ORCHESTRATION:END -->` block
   from any `CLAUDE.md` you merged it into.
4. (Repo maintainers) revert the Phase 4 changes via git.

No other state exists — no settings, no hooks, no daemons.
