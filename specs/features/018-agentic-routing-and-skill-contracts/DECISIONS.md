<!-- See skills/sdd-guardrails/SKILL.md, section 1, for the full decision state machine (Proposed / Accepted / Superseded / Rejected / Deferred). -->

# Decisions: Agentic Routing and Skill Contracts (Phase 2)

## Decision log

### D001 - Skills remain reusable capabilities

**Date:** 2026-07-24

**Status:** Accepted

**Context:** Phase 1 found 61 healthy skills with no orphans and no broken references. The
temptation in an agentic redesign is to promote skills to agents.

**Decision:** Skills stay skills — reusable capabilities/checklists/procedures — and are not
converted into agents.

**Reasoning:** Skills are composable and profile-scoped; agents are accountable actors. Converting
them would fragment behavior across process boundaries and lose reuse.

**Consequences:** No skill is deleted or moved. The agent layer is additive.

### D002 - Agents are accountable actors that consume skills

**Date:** 2026-07-24

**Status:** Accepted

**Context:** No layer currently owns responsibility for research, architecture, implementation,
security, domain review, or conformance.

**Decision:** Agents are the accountable actors. Each has one responsibility, produces a defined
output, and consumes one or more skills.

**Reasoning:** Separates "capability" (skill) from "accountability" (agent), which is the missing
routing semantic identified in Phase 1.

**Consequences:** Every skill gains a documented `primary_agent`; agents carry allowed/forbidden
action lists.

### D003 - Phase 2 ships exactly 6 agents

**Date:** 2026-07-24

**Status:** Accepted

**Context:** Phase 1 proposed 6–7 agents; the maintainer chose the leaner set.

**Decision:** Ship exactly six: `codebase-researcher`, `solution-architect`, `implementer`,
`security-reviewer`, `domain-reviewer`, `final-conformance-reviewer`.

**Reasoning:** Minimal, professional coverage of the SDD lifecycle without swarm complexity or an
agent-per-technology explosion.

**Consequences:** No test-engineer agent (see D004); testing responsibility is split (D005).

### D004 - No dedicated test-engineer agent in Phase 2

**Date:** 2026-07-24

**Status:** Accepted

**Context:** A standalone test-engineer agent was considered and rejected in favor of the 6-agent set.

**Decision:** Do not create a `test-engineer` agent in Phase 2. The `test-engineer` skill remains.

**Reasoning:** Testing concerns are already covered by three existing agents at different lifecycle
points; a fourth reviewer would overlap.

**Consequences:** Testing ownership is distributed per D005.

### D005 - Testing ownership is split across four agents

**Date:** 2026-07-24

**Status:** Accepted

**Context:** With no test agent, testing responsibility must be explicitly assigned.

**Decision:**
- Pre-implementation test strategy → `solution-architect` (via the `test-engineer` skill).
- Domain-specific test expectations → `domain-reviewer`.
- Final coverage/evidence validation → `final-conformance-reviewer` (via `qa-review`).
- `implementer` adds tests only when a task in TASKS.md explicitly requires it.

**Reasoning:** Places each testing concern where the accountable knowledge already lives.

**Consequences:** No single agent owns "testing" end-to-end; the split is documented in the agent
contracts and the SPEC Test strategy section.

### D006 - domain-reviewer replaces external java-spring/api-design subagent coupling

**Date:** 2026-07-24

**Status:** Accepted

**Context:** `java-spring-reviewer`, `spring-boot-api-reviewer`, and `event-driven-reviewer`
declare routing to `java-spring` / `api-design` subagents that this repo does not ship.

**Decision:** Reroute those references to the `domain-reviewer` agent. The reviewer skill bodies
are unchanged; only the routing target changes.

**Reasoning:** Removes the framework's dependence on uncontrolled, environment-provided agents and
makes the framework self-contained.

**Consequences:** `domain-reviewer` becomes the owner of stack/domain reviewer skills. CHANGELOG
notes the behavior source change for downstream users.

### D007 - Graphify research belongs to codebase-researcher

**Date:** 2026-07-24

**Status:** Accepted

**Context:** `graphify` / `graphify-context` are context providers with no clear agent owner, and
Phase 1 warned against making Graphify mandatory.

**Decision:** `codebase-researcher` owns Graphify-based research. Graphify remains optional and
degrades gracefully when absent.

**Reasoning:** Research is a bounded, read-only responsibility; Graphify is an accelerator, never a
source of truth.

**Consequences:** No hook or gate forces Graphify. `context-manager` remains the no-graph fallback
under the same agent.

### D008 - Security gets a dedicated security-reviewer

**Date:** 2026-07-24

**Status:** Accepted

**Context:** Auth, payments, and secrets carry disproportionate risk and are currently reviewed by
whatever generic reviewer happens to run.

**Decision:** Create a dedicated `security-reviewer` agent, separate from `domain-reviewer`.

**Reasoning:** Isolated security responsibility ensures secrets/auth/payments always get a focused,
severity-based review rather than being folded into domain review.

**Consequences:** Payments are reviewed by `security-reviewer` (money-safety) and `domain-reviewer`
(processor idioms); the boundary is documented to avoid overlap.

### D009 - deep-reasoner and fast-worker remain unchanged

**Date:** 2026-07-24

**Status:** Accepted

**Context:** Two agents already exist for the `sdd-orchestrate` multi-model workflow.

**Decision:** Leave `deep-reasoner` and `fast-worker` untouched.

**Reasoning:** They serve a different, working purpose (model-tiered orchestration). The six new
agents are lifecycle-role agents, orthogonal to the two model-tier agents.

**Consequences:** The repo will ship 8 agents total; the two existing ones are out of scope for
edits in this phase.

### D010 - sdd-orchestrate remains orchestration skill/context, not a dispatched agent

**Date:** 2026-07-24

**Status:** Accepted

**Context:** `sdd-orchestrate` and `review-all` look agent-shaped but dispatch other agents.

**Decision:** `sdd-orchestrate` (and `review-all`, `sdd`, `sdd-medium`, `sdd-full`) remain
orchestration skills/context. Their `primary_agent` is the orchestration context, not one of the six.

**Reasoning:** An orchestrator that is itself a dispatched subagent cannot cleanly spawn siblings;
the dispatcher must sit above the six agents.

**Consequences:** The skill contract model includes an `orchestration-context` value for
`primary_agent`, distinct from the six agents.

### D011 - Skill contract carrier is a `## SDD Contract` YAML block inside SKILL.md

**Date:** 2026-07-24

**Status:** Accepted

**Context:** The SPEC left the contract carrier open (frontmatter keys vs a standard section) and
PLAN leaned toward frontmatter for machine-readability. This resolves SPEC Open Question 1.

**Decision:** Carry the skill contract as a fenced YAML block under a standard `## SDD Contract`
section inside each SKILL.md, rather than adding extra provider-specific keys to the existing
frontmatter.

**Reasoning:** Keeps the existing skill frontmatter (`name`/`description`/`triggers`/etc.) clean
and provider-neutral, avoids colliding with Claude Code's frontmatter contract, and a fenced YAML
block is still fully machine-parseable by `check-consistency`. Supersedes PLAN's earlier
frontmatter leaning.

**Consequences:** `check-consistency` parses the YAML under `## SDD Contract`. T002 becomes
"apply and validate the `## SDD Contract` block" rather than "decide the carrier"; T003 defines the
schema for that block; T010 populates it across all 61 skills. The `provider_specific` field lives
inside this block, keeping provider coupling out of frontmatter.

### D012 - profiles.json expresses routing via an additive `agentRouting` map

**Date:** 2026-07-24

**Status:** Accepted

**Context:** The SPEC deferred the exact JSON shape of the per-profile routing map to PLAN. This
resolves SPEC Open Question 2.

**Decision:** Add an additive `agentRouting` object per profile in `profiles.json`, mapping agent
names to the skills they consume for that profile — e.g. `"agentRouting": { "domain-reviewer":
["java-spring-reviewer", "spring-boot-api-reviewer", ...], "security-reviewer": [...] }`. Existing
`skills` / `plannedSkills` / `agents` arrays are unchanged.

**Reasoning:** A single, generic `agentRouting` map covers all six agents (not just
`domain-reviewer`), is additive so older installers ignore the unknown key without breaking, and
gives `check-consistency` one place to validate agent→skill routing.

**Consequences:** `agentRouting` is validated by `check-consistency` (T014): every agent key must
resolve to a real agent (or `plannedAgents`) and every listed skill must exist on disk. T012
populates `agentRouting`. This generalizes the SPEC's "which reviewers domain-reviewer loads" into
a routing map for every agent.

### D013 - Formal `## SDD Contract` schema: enums, `all` sentinel, side-effect precedence, provider_specific as boolean

**Date:** 2026-07-24

**Status:** Accepted

**Context:** T003 required formalizing the informal field table from SPEC's "Skill contract
model" into a schema `check-consistency` can validate, using the six T002 samples as the test
set. Several forks needed resolving that the SPEC/PLAN left implicit: the full `primary_agent`
enum, how `secondary_agents: all` is represented, whether `side_effects` can capture a skill with
more than one true effect (it can't, as a single enum, without a rule), and whether
`provider_specific` is a boolean or a provider name/list. Full schema recorded in
`CONTRACT_SCHEMA.md`.

**Decision:**
- `primary_agent` enum extends beyond the six agents with three sentinels:
  `orchestration-context` (dispatchers, D010), `any` (no single owner — `spec-status`/
  `spec-resume`), `human` (manual-only skills — `handoff`).
- `secondary_agents: all` is a reserved token, valid only as the list's sole entry, expanding to
  the six lifecycle agents (never the three sentinels above). Cannot mix with named agents.
- `side_effects` stays a single enum (`none`/`writes-specs`/`writes-code`/`writes-scratch`) but is
  resolved by **precedence** against the three booleans when a skill has more than one true
  effect: `writes_code` wins over `writes_specs`, which wins over `none`/`writes-scratch`. Tested
  against `sdd-orchestrate` (writes both code and specs → `writes-code` wins).
- `profile_scope` is `all` or a list validated against `profiles.profiles` keys in `profiles.json`.
- `provider_specific` stays a plain boolean, not a provider name/list.

**Reasoning:** Each fork was resolvable without new capability — they formalize distinctions
already implicit in the Phase 1 matrix (INVENTORY.md) and the six samples, rather than inventing
new behavior. The boolean choice for `provider_specific` follows the Non-goals' rejection of
over-engineering (YAGNI until a second provider is actually integrated); the precedence rule for
`side_effects` avoids widening it to a list, which would have been a bigger schema change for a
label that's advisory, not authoritative (the three booleans remain authoritative).

**Consequences:** `CONTRACT_SCHEMA.md` is the authoritative schema going forward, superseding the
informal table in SPEC's "Skill contract model" section (SPEC not edited in this pass — no
contradiction, just a more detailed downstream document). Validation rules VR1–VR15 defined
there; VR1–VR13 are hard failures, VR14–VR15 are non-blocking warnings — VR14 specifically
decouples contract population (T003/T010) from agent-file creation (T004–T009), so either can
proceed first without failing validation. T010's mass rollout must follow this schema exactly.

### D014 - agentRouting covers profile-level agent consumption

**Date:** 2026-07-24

**Status:** Accepted

**Context:** T012 populated `profiles.json`'s `agentRouting` only for skills judged
cross-cutting or ambiguous between two agents (e.g. payment reviewers consumed by both
`domain-reviewer` and `security-reviewer`). This left two `next-prisma-web` skills —
`frontend-review` and `privacy-compliance-review` — shipped in the profile's `skills` array
but absent from `agentRouting`, even though each already has an unambiguous
`primary_agent` in its own `## SDD Contract` (`domain-reviewer` and `security-reviewer`
respectively, from T010). This under-specified what "coverage" means for `agentRouting`
going forward and would have left `check-consistency` (T014, rule 7) without a clear bar to
enforce.

**Decision:** `agentRouting` is an explicit per-profile routing map for **all** profile
skills that should be consumed by lifecycle agents — not only ambiguous or cross-cutting
skills. Skill contracts (`## SDD Contract`) remain the source of truth for a skill's
*default* ownership; `agentRouting` makes profile-level agent activation explicit and
auditable, independent of whether a skill's routing is contested or obvious.

**Reasoning:** A coverage rule scoped to "ambiguous skills only" is not machine-checkable —
"ambiguous" is a judgment call, not a property `check-consistency` can test. A rule scoped to
"every non-core profile skill" is a concrete, verifiable invariant: for each non-core
profile, every skill in its `skills` array appears under some agent in `agentRouting`
(unless explicitly exempted). This closes the exact gap that produced this decision and
gives T014 rule 7 a precise definition instead of an implicit one.

**Consequences:** `profiles.json`'s `next-prisma-web.agentRouting` gains
`frontend-review` → `domain-reviewer` and `privacy-compliance-review` → `security-reviewer`,
matching each skill's existing `primary_agent`. `core` remains exempt (its 41 skills are not
stack-specific reviewer routing and were out of scope for the original routing rules); this
exemption is explicit, not silent. `blockchain-crypto` remains exempt as a disabled
placeholder profile. `check-consistency` (T014) enforces this coverage rule for the five
non-core, non-disabled profiles (`java-spring-backend`, `messaging-event-driven`,
`payments-fintech`, `next-prisma-web`, `seo-geo-addon`) going forward.

**Addendum (same day, discovered by running the T014 `check-consistency` extension):** the
coverage rule applies to **every** skill a non-core profile ships — including the *generic
quality-review base skills* a profile ships alongside its stack-specific reviewers, not only
the stack-specific reviewers themselves. Running the extended checker against the live repo
found three more uncovered skills that D014's rule already covers by its original wording,
just not yet applied: `java-spring-backend` shipped `api-review`, `backend-review`, and
`database-review` without routing entries; `next-prisma-web` shipped `database-review`
without one. All four already had an unambiguous `primary_agent: domain-reviewer` in their
own `## SDD Contract` from T010. `profiles.json` is updated accordingly:
`java-spring-backend.agentRouting.domain-reviewer.skills` gains `api-review`,
`backend-review`, `database-review`; `next-prisma-web.agentRouting.domain-reviewer.skills`
gains `database-review`. No change to D014's original decision text was needed — this is
the rule being applied completely, not a new decision.
