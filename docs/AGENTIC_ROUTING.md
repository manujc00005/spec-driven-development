# Agentic routing: skills, agents, and how profiles connect them

The six-agent lifecycle layer for the SDD workflow: how a **skill** (a reusable capability)
differs from an **agent** (an accountable actor that consumes skills), and how
`profiles.json` routes one to the other. Shipped by this repo since
`specs/features/018-agentic-routing-and-skill-contracts/`.

This is a **separate system** from [`docs/SDD-ORCHESTRATION.md`](SDD-ORCHESTRATION.md)'s
multi-model orchestration (`deep-reasoner`/`fast-worker`) — see "Relationship to the
model-tier agents" below for exactly how the two fit together.

## Skills vs. agents

> **Skills define how to do something. Agents are responsible for producing an outcome.**

**Skills** are reusable capabilities:

- Checklists, procedures, review lenses, workflows, or mindset manuals.
- Can be consumed by more than one agent (a payment reviewer skill, for example, is read by
  both `domain-reviewer` and `security-reviewer`, for different concerns).
- Remain profile-scoped — a skill ships only where `profiles.json` says it ships.
- Do **not** imply responsibility by themselves. A skill existing doesn't mean anyone owns
  running it; that's what an agent's `primary_agent` assignment is for.

**Agents** are accountable actors:

- Own one lifecycle responsibility (research, architecture, implementation, or one of three
  review flavors).
- Consume one or more skills to do their job — they don't reimplement what a skill already
  checks.
- Produce a defined output (a reading list, a SPEC/PLAN/DECISIONS update, a diff, a
  findings report, a verdict).
- Have an explicit allowed/forbidden action list, enforced both by their Claude Code `tools:`
  grant (structural) and by prose rules in their contract (behavioral).
- Can be routed by profile — which reviewer skills `domain-reviewer` or `security-reviewer`
  load for a given stack is a `profiles.json` decision, not hardcoded in the agent.

Do not convert every skill into an agent. Most of this repo's 61 skills stay skills,
consumed by whichever agent owns that concern — see each skill's own `## SDD Contract`
block for its `primary_agent`.

## The six lifecycle agents

All six live in [`agents/`](../agents/) as standard Claude Code subagent files
(`name`/`description`/`tools:` frontmatter, no `model:` — they inherit whatever model the
invoking session uses, since they are not part of a cost-tiering scheme). Full contracts
are in each agent's own file; this is the summary.

### `codebase-researcher`

- **Responsibility:** understand the code area affected by a feature; prefer
  Graphify-derived impact analysis when a fresh graph report exists, fall back to direct
  `Grep`/`Glob` inspection when it doesn't; produce a bounded reading list, not a full-repo
  dump.
- **Key skills consumed:** `graphify`, `graphify-context`, `context-manager`, `scout`.
- **Allowed actions:** Read, Grep, Glob; request that the orchestrating session run
  `graphify` when a fresh graph would help.
- **Forbidden actions:** modifying any file (it has no Edit/Write/Bash tool at all);
  making architectural or implementation decisions; treating a stale/absent graph as
  authoritative.
- **When it runs:** first, before planning or review, on any medium-or-larger feature.

### `solution-architect`

- **Responsibility:** review/author `SPEC.md`/`PLAN.md`/`TASKS.md`; surface architectural
  decisions into `DECISIONS.md` rather than deciding silently; own the pre-implementation
  test strategy.
- **Key skills consumed:** `spec-create`, `spec-clarify`, `spec-plan`, `spec-analyze`,
  `sdd-guardrails`, `architect-review`, `test-engineer` (strategy use).
- **Allowed actions:** Read, Grep, Glob, Edit, Write — but Edit/Write are confined by its
  own contract to `specs/features/**` (and `specs/CONSTITUTION.md` when scaffolding a
  project).
- **Forbidden actions:** writing or editing application code, tests, or configuration
  outside `specs/`; marking a spec `Ready` while `sdd-guardrails` reports a contradiction;
  `git commit`/`git push`/`git add .` (no Bash tool exists to run them anyway).
- **When it runs:** after `codebase-researcher`, before any implementation task begins.

### `implementer`

- **Responsibility:** execute approved `TASKS.md` items, one at a time, strictly within the
  boundaries the task and `PLAN.md` define; stop the moment a needed decision isn't already
  recorded in `DECISIONS.md`.
- **Key skills consumed:** `spec-implement`, `refactor-review`, `scope-keeper`, `scout`,
  `stopper`, `verifier`, `debugger`.
- **Allowed actions:** Read, Grep, Glob, Edit, Write, Bash — the only lifecycle agent with a
  Bash tool, and the only one permitted to edit application code, strictly within a task's
  explicit file boundary.
- **Forbidden actions:** editing any file outside that boundary; making an architectural
  decision not already in `DECISIONS.md`; `git commit`/`git push`/`git add .`; touching
  secrets, `.env` files, or `settings.local.json`; marking a task complete when
  implementation is partial.
- **When it runs:** after `solution-architect` has produced an approved `TASKS.md` with no
  open blocking questions, one task at a time.

### `security-reviewer`

- **Responsibility:** review secrets, authentication, authorization, payments, permissions,
  and other sensitive-data handling in a diff; produce severity-ranked findings with
  concrete evidence.
- **Key skills consumed:** `security-review`, `spring-security-reviewer`,
  `nextjs-server-actions-reviewer`, `privacy-compliance-review`, `threat-modeler`, and the
  payment reviewers (`stripe-payments-reviewer`, `payment-idempotency-reviewer`) whenever
  the diff moves money.
- **Allowed actions:** Read, Grep, Glob.
- **Forbidden actions:** modifying code, tests, or configuration; silently downgrading a
  finding; reporting a finding without evidence.
- **When it runs:** on any diff touching auth, user data, tenant isolation, public APIs,
  file uploads, tokens, secrets, or payment/money-movement flows.

### `domain-reviewer`

- **Responsibility:** load and apply the stack/domain reviewer skills the active profile
  ships (Java/Spring, event-driven/microservices, payment processor idioms, Next.js/Prisma,
  SEO/GEO); own domain-specific test expectations; the single owner of record for domain
  reviewer skills, replacing any ad-hoc or externally-coupled subagent routing those skills
  used to name.
- **Key skills consumed:** `java-spring-reviewer`, `spring-boot-api-reviewer`,
  `event-driven-reviewer`, `microservices-patterns-reviewer`, `stripe-payments-reviewer`,
  `payment-idempotency-reviewer`, `prisma-migration-reviewer`, the SEO/GEO/AEO/AI-visibility
  family, plus the generic bases (`api-review`, `backend-review`, `database-review`, etc.)
  when used for domain-level review.
- **Allowed actions:** Read, Grep, Glob; select and apply reviewer skills by active profile.
- **Forbidden actions:** modifying code, tests, or configuration; running a billable-service
  reviewer (SEO/GEO/AEO/AI-visibility) when the service isn't contracted in
  `specs/SERVICES.md`; editing skill files itself to fix any stale routing text it notices.
- **When it runs:** per the active profile, after the generic quality review, on any diff
  touching stack-specific code.

### `final-conformance-reviewer`

- **Responsibility:** verify the full chain SPEC → PLAN → TASKS → DIFF → TESTS → REVIEW;
  validate that test/coverage evidence is real, not just claimed; produce a traceability
  verdict and a draft PR description — the last checkpoint before a feature can close.
- **Key skills consumed:** `spec-review`, `spec-analyze`, `spec-close`, `sdd-guardrails`,
  `qa-review`, `pr-description`.
- **Allowed actions:** Read, Grep, Glob across the repo, the diff, and all SDD documents.
- **Forbidden actions:** modifying code, tests, or configuration; declaring conformance
  while an acceptance criterion has no covering task (or vice versa); closing over an
  unresolved contradiction; accepting a test as passing without evidence it actually ran.
  It does not write its own verdict or PR description to a file — that's the orchestrating
  session's or `solution-architect`'s job to persist.
- **When it runs:** last, after `implementer` finishes and `domain-reviewer`/
  `security-reviewer` have reported, before the maintainer opens a PR.

## Relationship to the model-tier agents

`deep-reasoner` and `fast-worker` (documented fully in
[`docs/SDD-ORCHESTRATION.md`](SDD-ORCHESTRATION.md)) remain unchanged and separate. They are
**model-tier** agents: the axis that distinguishes them is cost/capability (Opus for hard
reasoning, Sonnet for mechanical work), used specifically by the `/sdd-orchestrate` workflow.
The six agents above are **lifecycle-role** agents: the axis that distinguishes them is *which
part of the SDD lifecycle they own* (research, architecture, implementation, or one of three
review flavors), independent of which model runs them.

The two systems can be used independently or together — nothing about the lifecycle agents
requires `/sdd-orchestrate`, and nothing about `/sdd-orchestrate` requires the six lifecycle
agents. `agents/README.md` documents both families side by side.

## Routing model

- **Profiles activate skills** — `profiles.json`'s per-profile `skills` array, unchanged by
  this work.
- **Profiles activate agents** — `profiles.json`'s per-profile `agents` array. `core` (always
  installed) activates all six lifecycle agents alongside `deep-reasoner`/`fast-worker`.
- **`agentRouting` maps profile skills to lifecycle agents** — an additive, per-profile map
  in `profiles.json` naming which agent owns which of that profile's skills, e.g.:
  ```json
  "agentRouting": {
    "domain-reviewer": { "skills": ["java-spring-reviewer", "spring-boot-api-reviewer"] },
    "security-reviewer": { "skills": ["spring-security-reviewer"] }
  }
  ```
  Every non-core, non-disabled profile's skills are expected to be covered by its
  `agentRouting` (an optional `agentRoutingExempt` array can name a deliberate exception);
  `scripts/check-consistency.sh` enforces this.
- **`domain-reviewer` owns stack/domain reviewer skills** — Java/Spring idioms, event-driven
  patterns, payment processor conventions, Next.js/Prisma, SEO/GEO.
- **`security-reviewer` owns auth/secrets/payments/sensitive-data *risk* review** — a
  distinct concern from domain idioms even on the same skill (e.g. Stripe idempotency-key
  safety is `security-reviewer`'s job; Stripe SDK call conventions are `domain-reviewer`'s).
- **`codebase-researcher` owns Graphify/context-first research** — see Boundaries below.
- **`final-conformance-reviewer` owns traceability and final evidence validation** — the
  only agent that looks at the *entire* SPEC-to-review chain at once.

## Boundaries

Hard rules that hold across all six lifecycle agents:

- **Reviewers are read-only.** `codebase-researcher`, `security-reviewer`,
  `domain-reviewer`, and `final-conformance-reviewer` all declare `tools: Read, Grep, Glob`
  only — there is no Edit/Write/Bash tool to misuse, so this is enforced structurally, not
  just by instruction.
- **`implementer` is the only lifecycle agent allowed to edit application code**, and only
  within a task's explicit file boundary.
- **`solution-architect` may write specs/decisions but not application code** — it has
  Edit/Write, but its own Forbidden-actions text confines both to `specs/`.
- **No agent may** run `git commit`, `git push`, or `git add .`; edit secrets, `.env` files,
  or `settings.local.json`; or bypass `SPEC.md`/`PLAN.md`/`TASKS.md` to make an undocumented
  decision.
- **Graphify is optional, never mandatory.** `codebase-researcher` prefers a fresh graph
  report when one exists and degrades gracefully — falling back to direct `Grep`/`Glob`
  exploration — when it doesn't. No agent requires Graphify to function.
- **`graph.json` should not be loaded wholesale into context.** Graphify's own scoped query
  commands (`graphify query`, `graphify path`, `graphify explain`, or a cached
  `GRAPH_REPORT.md` summary) return a bounded subgraph; reading the raw `graph.json` file in
  full defeats the token-saving purpose Graphify exists for.

## Testing responsibility

There is no dedicated `test-engineer` agent in Phase 2 (`specs/features/018-.../DECISIONS.md`
D004). Testing concerns are split across the four agents that already have the relevant
context, rather than centralized in a fifth:

- **`solution-architect` owns the pre-implementation test strategy** — what must be proven,
  at what level, before a feature can be called done (via the `test-engineer` *skill*, used
  for strategy design, not as an agent).
- **`domain-reviewer` owns domain-specific test expectations** — what a correct
  implementation in a given stack must be tested for (e.g. idempotent-consumer tests for a
  Kafka listener).
- **`final-conformance-reviewer` owns final coverage/evidence validation** — confirming
  claimed test runs actually happened and passed, as part of its traceability verdict.
- **`implementer` adds tests only when a task in `TASKS.md` explicitly requires it** — it
  does not invent test coverage beyond what was asked.

## Provider positioning

Claude Code is the current shipped agent file format (`name`/`description`/`tools:`
frontmatter, read by `~/.claude/agents/` or a project's `.claude/agents/`). The six lifecycle
agents' *responsibilities* — research, architecture, implementation, security review, domain
review, final conformance — are conceptually provider-agnostic: the accountability split
they encode doesn't depend on any Claude-specific mechanism. That said, this repo does not
claim or implement parity with any other agent runtime (e.g. Codex) today; if and when
another provider is actually integrated, that will be its own tracked decision, not an
assumption made here. Each skill's `## SDD Contract` carries a `provider_specific` flag for
exactly this reason — mindset-manual-style skills that encode Claude-specific behavioral
guidance are flagged `true`; generic lifecycle/review skills are flagged `false`.
