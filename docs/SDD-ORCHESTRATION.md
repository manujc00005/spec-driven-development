# SDD multi-model orchestration

Multi-model delegation layer for the SDD workflow: the main session orchestrates, an
Opus agent reasons, a Sonnet agent implements. Shipped by this repo since profiles.json
`0.4.0` (feature `specs/features/004-multimodel-orchestration/`).

**Not to be confused with:** the six *lifecycle* agents (`codebase-researcher`,
`solution-architect`, `implementer`, `security-reviewer`, `domain-reviewer`,
`final-conformance-reviewer`) documented in
[`docs/AGENTIC_ROUTING.md`](AGENTIC_ROUTING.md). Those are split by *lifecycle role*
(research/architecture/implementation/review); `deep-reasoner`/`fast-worker` below are
split by *model tier* (Opus/Sonnet cost-awareness). The two systems are independent — use
either, both, or neither.

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

### Autonomous mode

The invocations above report back to you between phases. Autonomous mode instead runs the whole
implement → review → fix circuit on an already-approved feature and only comes back when it is
finished or genuinely stuck:

```
/sdd-orchestrate --autonomous specs/features/<nnn>-<name> [--max-iterations N] [--max-delegations N]
```

It starts only if six conditions hold: the spec is `Ready` (or the run is a validated resume), no
open decision blocks a task, `TASKS.md` has runnable work, you are **not** on the default branch,
the working tree is clean, and the PLAN's verification suite passes at baseline without dirtying
the tree. A refusal names the exact condition and the command that fixes it, so an unmet gate is a
one-line fix rather than a mystery.

Inside the loop, workers and reviewers communicate through structured blocks rather than prose, and
every decision, delegation, verdict, and escalation is written to `ORCHESTRATION.md` in the feature
folder. That file — not the conversation — is the source of truth, which is what lets a compacted
or killed session resume exactly where it stopped.

**What it decides alone vs. what it escalates.** A blocker is resolved autonomously only when it is
purely technical, reversible, inside the approved spec, and outside every human-gated domain; the
resolution is recorded in `DECISIONS.md` as orchestrator-decided, so you can audit or reverse it.
Anything touching product or UX behavior the spec does not settle, money, personal data, a public
contract, a destructive operation, or evidence that contradicts the spec waits for you. Independent
tasks keep running while a question is pending, and the run pauses only when nothing else can
progress.

**What the caps mean.** They bound disagreement, not effort. A reviewer can review as many times as
the work requires; what is capped is a reviewer rejecting repeatedly without resolving anything
(`max-iterations` consecutive no-progress rejections) and a single finding being rejected more than
`max-iterations` times overall. The delegation budget, which defaults to `max(25, 6 × unchecked
tasks)`, is the global ceiling on total cost.

**Resuming.** A `PAUSED` run resumes once you record the answer in `DECISIONS.md` and re-invoke the
same command. A recoverable `ABORTED` run resumes after its stated remediation; if it stopped on an
exhausted cap you must raise that cap explicitly, since counters never reset. A run that aborted on
ambiguous provenance is deliberately non-resumable and hands control back to you.

The loop never commits, pushes, merges, or sets a spec status by hand — it invokes the owning
lifecycle skills and leaves you a reviewed working tree plus a PR description.

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

## Phase 2 — the runner (`runner/`, spec 040)

Everything above runs inside an interactive Claude Code session: the loop is a
prompt, and a person has to be there for it to exist. **Phase 2 is the same
protocol executed as code** — a Python package under `runner/` that reads
`TASKS.md`, dispatches one provider session per task or review, parses the
verdict blocks programmatically, enforces the caps and the budget arithmetically,
and interrupts a human only on an escalation or a non-success exit.

Spec 031 named this feature in its own Non-goals and designed the verdict-block
schema for both consumers. Where the runner and `sdd-orchestrate` disagree about
semantics, **the runner is wrong** — specs 031 and 032 are normative.

### What it is not

The runner is **maintainer tooling of this repository**. It is not installed by
`install.sh` or `install.ps1`, is not listed in `profiles.json` or the install
manifest, and no adopter project depends on it. A machine with neither the Agent
SDK nor the Codex CLI keeps using this framework exactly as before; deleting
`runner/` removes the feature completely.

### Invocation

```bash
PYTHONPATH=runner python3 -m sdd_runner --feature specs/features/<nnn>-<name> --dry-run
```

No TTY is required, stdin is never read, and nothing is ever prompted — which is
the whole point: `cron`, CI and overnight runs work.

| Flag | Meaning |
|---|---|
| `--feature` | the feature folder to run |
| `--backend` | `stub`, `claude`, or `codex` (default `claude`) |
| `--max-iterations` | non-convergence cap (default 3) |
| `--max-delegations` | hard budget (default `max(25, 6 × unchecked tasks)`) |
| `--baseline` | PLAN-mandated verification command; see *Finalization* below |
| `--notify` | command run without a shell, event delivered as JSON on stdin |
| `--allow-unverified-backend` | opt-in required by the gated Codex backend |
| `--stub-script` | JSON responses for `--backend stub` — the only way to exercise a full run without a provider |
| `--dry-run` | entry gate, plan and budget; dispatches nothing, and needs no usable backend |

### Exit codes

A scheduler branches on the code alone.

| Code | Meaning |
|---|---|
| `0` | converged and closed |
| `10` | entry gate refused (status, open questions, missing `TASKS.md`, default branch, dirty tree, red baseline) |
| `11` | human-gated escalation — a person must answer |
| `12` | cap abort — a reviewer or a finding failed to converge |
| `13` | delegation budget exhausted |
| `14` | backend precondition unmet (missing SDK, missing CLI, missing credential, gated backend) |
| `15` | a concurrent run already owns the feature folder |
| `16` | the persisted state cannot be resumed (corrupt, foreign, or self-contradicting) |
| `17` | every task processed, but the run did not converge |
| `18` | closure could not be proven (unexpected closure delta, or a lifecycle skill refused) |
| `70` | internal error |

### Backends

- **`stub`** — always present, scripted, deterministic. The entire test suite runs
  on it with no provider call and no cost.
- **`claude`** — the Claude Agent SDK, imported lazily. Optional dependency:
  `python3 -m pip install claude-agent-sdk`. Credentials come from the
  environment only. **It has never been exercised against a real provider from
  this repository** — no SDK is installed on the maintainer's machine, so the
  end-to-end scenarios are recorded as *not observed* rather than as passing.
- **`codex`** — *Codex backend implementation is present but gated.* Codex
  execution requires local CLI verification. **Codex parity is not claimed.** It
  refuses to run without `--allow-unverified-backend` because the isolation flag
  set it depends on is enforced but never exercised against a real CLI — see
  [`KNOWN_DEBT.md`](KNOWN_DEBT.md), **DEBT-001** and **DEBT-002**.

### Re-entry

Re-running against an existing `ORCHESTRATION.md` resumes it: completed tasks are
not re-delegated, findings are not duplicated, and counters and the budget carry
over without resetting. The runner refuses rather than guesses — code `16` covers
a document written by another executor, a corrupt table, a budget that disagrees
with itself, and a `State` section that contradicts the `Attempts` table.

`ACTIVE` alone does not prove a runner is alive: after a SIGTERM it says the same
thing. The document records the writer's pid and host, so an `ACTIVE` run whose
pid is dead **on this host** is an interrupted run and resumes; one whose pid is
alive is refused as concurrent (`15`); and one recorded on a different host blocks
(`16`), because guessing that a remote pid is dead is how two runners end up in
the same worktree.

### Finalization, freeze and closure delta

A converged task list is not a closed run. Before saying `DONE` the runner
re-checks 031's conditions — no unconverged task, no open finding, no waiting
escalation, a coherent budget, every `TASKS.md` item checked — then re-reviews any
approval a later task's change staled, runs `final-conformance-reviewer` once, and
only then **freezes**: it records the approved implementation fingerprint together
with a per-path content map of the tree.

After the freeze it delegates the owning lifecycle skills (`/spec-review`,
`/spec-close`, `/pr-description`) and requires each one's APPROVE. **It never
writes a spec `Status` itself** — the loop may invoke the owning skills, and that
is not a direct transition. Finally it compares the tree against the frozen map:
generated artifacts, a `SPEC.md` change confined to its `## Status` section and
`TASKS.md` checkbox bookkeeping are allowed; anything else is unexpected and
returns the run to REVIEW with the paths named.

`--baseline` is 031's second DONE condition. Declared, it must pass and must not
mutate the tree. **Undeclared, that condition is recorded as unobserved** — in the
closure record and in the run's reason line — rather than assumed.

### What has and has not been observed

The runner is proven against a deterministic stub backend: 186 tests covering the
fail-closed parser, the counter arithmetic, the budget, re-entry, the repair
cycle, finalization, and — through `--stub-script` — the command-line entry point
converging end to end in a real subprocess with stdin closed. What that does
**not** prove, and what nobody has yet seen work:

- an `agents/*.md` prompt reaching a real provider;
- an owning lifecycle skill actually executing;
- `PR_DESCRIPTION.md` appearing on disk;
- a real `codex exec` invocation.

Those are spec 040's T018 and T022, blocked on an environment this machine does
not have. The runner may not be promoted to `Done` until they are observed.

### Artifacts

Each run writes `ORCHESTRATION.md` (031's schema, human-readable, shared with the
phase-1 executor) and `run.jsonl` (one JSON object per event) into the feature
folder. Every decision the runner makes is reconstructible from `run.jsonl` alone.
Both writers strip known credential values, so a secret an agent echoes does not
survive into either file.

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
