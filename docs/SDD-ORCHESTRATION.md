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
/sdd-orchestrate --autonomous specs/features/<nnn>-<name> [--adopt] [--max-iterations N] [--max-delegations N]
```

It starts only if six conditions hold: the spec is `Ready` (or the run is a validated resume), no
open decision blocks a task, `TASKS.md` has runnable work, you are **not** on the default branch,
the working tree is clean, and the PLAN's verification suite passes at baseline without dirtying
the tree. A refusal names the exact condition and the command that fixes it, so an unmet gate is a
one-line fix rather than a mystery.

**Adopting a feature you started by hand.** A feature that is already `In Progress` through the
manual chain (`/spec-implement` task by task) is refused by the gate above, because it is not
`Ready` and has no state file. `--adopt` is the explicit way in (spec 041): commit the work so far
on a feature branch, then run `/sdd-orchestrate --autonomous <path> --adopt`. The gate then
requires exactly `In Progress`, a fully clean tree (nothing pre-existing is ever attributed to the
run — your commit is the attribution), and a computable inherited record: the baseline commit, the
merge-base with the default branch as resolved from git metadata, and the tasks already checked.
Three refusals are specific to adoption: *Adoption not needed* (the spec is `Ready`; run without
the flag), *Already adopted or entered* (a state file exists; re-enter without the flag — a run is
resumed, never re-adopted), and *Inherited diff undetermined* (no default-branch metadata; set
`origin/HEAD`). When you are on the default branch with uncommitted work, both refusals are listed
branch first, tree second, so following them in order lands the commit on the feature branch.
Before touching any new task, the loop reviews the inherited diff with `domain-reviewer` (and
`security-reviewer` on the usual triggers); a `Critical` finding there is fixed before new work
starts. Checked tasks are never re-implemented; `ORCHESTRATION.md` records them in an `Inherited`
table as *verification not observed by this run*, and the final conformance report says so.

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
semantics, **the skill is wrong** — spec 042 made `runner/sdd_runner/` the
protocol's executable authority, and contract tests hold nine prose surfaces
(this document among them) to it. Specs 031 and 032 remain normative for what the
protocol *says*; changing it is still a `/spec-update` against 031, and the core
is where the change has to land for the suite to go green.

### Classification: experimental, stub-only

Spec 040 is **EXPERIMENTAL** and its final conformance verdict is **PARTIAL**. What
that means concretely, because the word on its own means nothing:

- **One supported backend: `stub`.** Every guarantee below — caps, budget,
  fail-closed parsing, re-entry, the repair cycle, the freeze — is proven against
  it and only against it.
- **`claude` and `codex` are outside the supported surface.** They remain in the
  tree as optional/lazy and gated-shut adapters respectively. Neither has been
  executed against a real provider from this repository, and no parity between
  them is claimed. A follow-up provider spec owns them.
- **The run stops at the `_finalize` hand-off.** The runner proves the core is
  converged and freezes; it does not close the feature lifecycle. See
  [Finalization and the hand-off](#finalization-and-the-hand-off).

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
| `--adopt` | first entry on an `In Progress` feature; prints the inherited record under `--dry-run` (spec 041) |

### Exit codes

A scheduler branches on the code alone.

| Code | Meaning |
|---|---|
| `0` | converged and closed |
| `10` | entry gate refused (status, open questions, missing `TASKS.md`, default branch, dirty tree, red baseline; under `--adopt` also adoption not needed, already adopted or entered, inherited diff undetermined; and status unreadable in either mode, when the line under `## Status` names no lifecycle status) |
| `11` | human-gated escalation — a person must answer |
| `12` | cap abort — a reviewer or a finding failed to converge |
| `13` | delegation budget exhausted |
| `14` | backend precondition unmet (missing SDK, missing CLI, missing credential, gated backend) |
| `15` | a concurrent run already owns the feature folder |
| `16` | the persisted state cannot be resumed (corrupt, foreign, or self-contradicting) |
| `17` | every task processed, but the run did not converge |
| `18` | core completion could not be proven (no `--baseline` declared, or the freeze was voided by a change to the tree after it) |
| `70` | internal error |

### Backends

- **`stub`** — always present, scripted, deterministic. The entire test suite runs
  on it with no provider call and no cost.
- **`claude`** — *outside spec 040's supported surface.* The Claude Agent SDK,
  imported lazily; optional dependency `python3 -m pip install claude-agent-sdk`,
  credentials from the environment only. **It has never been exercised against a
  real provider from this repository** — no SDK is installed on the maintainer's
  machine, so the end-to-end scenarios are recorded as *not observed* rather than
  as passing.
- **`codex`** — *outside spec 040's supported surface.* Implemented but **gated
  shut**: it refuses to run without `--allow-unverified-backend`, because the
  isolation flag set it depends on is enforced in code and never exercised against
  a real CLI. **Codex parity is not claimed.** See
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

### Finalization and the hand-off

A converged task list is not a closed run. Before saying `DONE` the runner
re-checks 031's conditions — no unconverged task, no open finding, no waiting
escalation, a coherent budget, every `TASKS.md` item checked — then re-reviews any
approval a later task's change staled, runs `final-conformance-reviewer` once, and
only then **freezes**: it records the approved implementation fingerprint together
with a per-path content map of the tree.

**The freeze is where spec 040 stops.** The run records `CORE-COMPLETE`, the
frozen fingerprint, the verification outcome and the frozen tree map, and exits
`0`. It does **not** dispatch the owning lifecycle skills (`/spec-review`,
`/spec-close`, `/pr-description`), does not compute a closure delta over what
those skills would have changed, and does not produce `PR_DESCRIPTION.md`. It has
never written a spec `Status` and still does not.

That boundary is deliberate. Closing a feature lifecycle means a provider that can
actually execute a skill, and 040 certifies no such provider — a stub answering
`APPROVE` on `/spec-close`'s behalf proved only that the stub was asked. The
frozen tree map is persisted as the hand-off datum for the follow-up `Finalizer`
spec, which owns lifecycle delegation, the closure delta and PR-description
evidence, and begins exactly at this seam.

`--baseline` is 031's second DONE condition, and it is **required to close**.
Declared, it must exit 0 and leave the tree unchanged. Undeclared, the run blocks
with exit `18` rather than closing over a condition nobody checked: a runner that
cannot verify may still do the work, but it may not call it finished. Everything
else — the entry gate, the task loop, `--dry-run` — works without it.

### What has and has not been observed

The runner is proven against a deterministic stub backend: 239 tests covering the
fail-closed parser, the counter arithmetic, the budget, re-entry, the repair
cycle, finalization, and — through `--stub-script` — the command-line entry point
converging end to end in a real subprocess with stdin closed. What that does
**not** prove, and what nobody has yet seen work:

- an `agents/*.md` prompt reaching a real provider;
- a real `codex exec` invocation.

Neither is a spec 040 task any more. Both moved to the follow-up provider spec
along with lifecycle delegation, the closure delta and `PR_DESCRIPTION.md` — which
are not *unobserved* here so much as *absent by contract*. 040 remains
EXPERIMENTAL/PARTIAL, and that is what its scope now honestly is rather than a
promise of provider work it never did.

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
