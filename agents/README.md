# Agents

This repo ships two families of agents. They are independent of each other — neither
supersedes the other, and a project can use one, both, or neither. This file is the
concise reference; [`docs/AGENTIC_ROUTING.md`](../docs/AGENTIC_ROUTING.md) is the full
explainer (per-agent skills consumed/when-to-run detail, the routing model, testing
responsibility, and provider positioning).

## Lifecycle agents

Six role-based agents covering the SDD lifecycle end to end: research, architecture,
implementation, and three flavors of review. Any project using the `core` profile gets all
six. They consume the repo's **skills** (see "Skills vs. agents" below) rather than
duplicating their logic.

| Agent | Tools | Role |
|---|---|---|
| `codebase-researcher` | Read, Grep, Glob | Understands the affected code area; uses Graphify when available; produces a bounded reading list. Read-only, never edits. |
| `solution-architect` | Read, Grep, Glob, Edit, Write | Reviews/authors SPEC, PLAN, TASKS, DECISIONS; surfaces architectural decisions; owns the pre-implementation test strategy. Writes SDD documents only, never application code. |
| `implementer` | Read, Grep, Glob, Edit, Write, Bash | Executes approved TASKS within explicit file boundaries; stops on any undocumented decision. The only lifecycle agent that edits application code. |
| `security-reviewer` | Read, Grep, Glob | Reviews secrets, auth, payments, permissions, and sensitive-data handling; produces severity-ranked findings. Read-only, never edits. |
| `domain-reviewer` | Read, Grep, Glob | Loads the stack/domain reviewer skills the active profile ships (Java/Spring, event-driven, payments idioms, Next.js/Prisma, SEO/GEO); owns stack-specific review. Read-only, never edits. |
| `final-conformance-reviewer` | Read, Grep, Glob | Verifies SPEC → PLAN → TASKS → DIFF → TESTS → REVIEW and validates evidence before a feature can close. Read-only, never edits. |

## Model-tier agents

Two agents for the separate **multi-model orchestrated SDD workflow**
(see `docs/SDD-ORCHESTRATION.md` and the `/sdd-orchestrate` skill), tiered by model cost
rather than by lifecycle role.

| Agent | Model | Tools | Role |
|---|---|---|---|
| `deep-reasoner` | `opus` | Read, Grep, Glob (read-only) | Architecture, complex debugging, root-cause, security, concurrency, migrations, high-risk review. Analyzes; never edits. |
| `fast-worker` | `sonnet` | Read, Grep, Glob, Edit, Write, Bash | Implements approved, well-delimited tasks; runs verifications. Stops on undocumented architectural decisions. |

Model fields use **aliases** (`opus`, `sonnet`) so the agents track the account's current
model per tier instead of pinning a dated snapshot. The six lifecycle agents above
deliberately have no `model:` field — they inherit whatever model the invoking session
uses, since they are not part of the opus/sonnet cost-tiering scheme.

## Skills vs. agents

A **skill** is a reusable capability — a checklist, a procedure, a document template. An
**agent** is an accountable actor with a single responsibility, allowed/forbidden actions,
and a defined output; it consumes one or more skills to do its job. Skills do not become
agents just because they are well-scoped: most of this repo's 60+ skills stay skills,
consumed by whichever lifecycle agent owns that concern.

Profiles route skills to agents. Each profile in `profiles.json` (java-spring-backend,
messaging-event-driven, payments-fintech, next-prisma-web, seo-geo-addon) declares an
additive `agentRouting` map naming which reviewer skills `domain-reviewer` and
`security-reviewer` load for that stack — see `profiles.json` for the exact mapping.
`domain-reviewer` owns stack/domain reviewers (Java/Spring idioms, event-driven patterns,
payment processor conventions, Next.js/Prisma, SEO/GEO); `security-reviewer` owns
auth/secrets/payments *risk* review (a payment reviewer can appear under both, per its own
skill's primary/secondary agent split). `final-conformance-reviewer` is the last step: it
validates the full SPEC → PLAN → TASKS → DIFF → TESTS → REVIEW chain before a feature closes.
Testing has no dedicated agent — it's split across `solution-architect` (pre-implementation
strategy), `domain-reviewer` (domain-specific expectations), `final-conformance-reviewer`
(final coverage/evidence), and `implementer` (adds tests only when a task requires it); see
`docs/AGENTIC_ROUTING.md` for the full reasoning.

## Hard boundaries (all lifecycle agents)

- Reviewers (`codebase-researcher`, `security-reviewer`, `domain-reviewer`,
  `final-conformance-reviewer`) are **read-only** — Read/Grep/Glob only, no Edit/Write/Bash.
- `implementer` is the **only** lifecycle agent permitted to edit application code, and only
  within a task's explicit file boundary.
- **No agent may** run `git commit`, `git push`, or `git add .`; edit secrets, `.env` files,
  or `settings.local.json`; or bypass SPEC/PLAN/TASKS/DECISIONS to make an undocumented
  decision.
- Graphify is optional, never a source of truth, and belongs to `codebase-researcher` —
  no other agent invokes it, and its absence must degrade gracefully rather than block work.

## How these are installed — copy, not link

Unlike `skills/` and `hooks/` (which are junctioned/symlinked from the central config),
agent files are **copied file-by-file, additively**:

- `install.ps1 -LinkUserClaude` / `install.sh --link-user-claude` → copies them into
  `~/.claude/agents/`.
- `link-project.ps1` / `link-project.sh` → copies them into `<project>/.claude/agents/`.

Reason: `~/.claude/agents` and project `.claude/agents` directories commonly contain
**user- or project-authored agents**. A junction would replace the whole directory and
hide them. Per-file copy adds only these agents and never touches anything else; a
same-name file that differs is skipped unless `-Force`/`--force` (which backs it up first).

Consequence: agent updates do **not** propagate automatically through the link like skills
do — re-run the installer (or link-project) after `git pull` to refresh them.

## Customizing per project

A project may freely edit its copied `.claude/agents/deep-reasoner.md` /
`fast-worker.md` (e.g., narrow `tools:`, add stack context). The installer will then
report the file as "differs" and skip it on future runs, preserving the customization
unless you explicitly pass `-Force`/`--force`.
