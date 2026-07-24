# Implementation Plan: Agentic Routing and Skill Contracts (Phase 2)

## Summary

Add a minimal agent layer (6 lifecycle agents) on top of the existing 61 skills, give every
skill a lightweight input/output contract, reroute the three externally-coupled reviewer skills
to the new `domain-reviewer` agent, express agent routing in `profiles.json` non-breakingly, and
extend `check-consistency` to validate the new references. Documentation-and-metadata heavy; no
skill behavior changes.

## Related spec

`specs/features/018-agentic-routing-and-skill-contracts/SPEC.md`

## Impacted areas

- `agents/` — six new agent Markdown files (added only when implementation begins).
- `agents/README.md` — document the six lifecycle agents alongside the two model-tier agents.
- `skills/*/SKILL.md` — add a contract block (frontmatter keys or `## Contract` section) to all 61.
- `skills/java-spring-reviewer/`, `skills/spring-boot-api-reviewer/`,
  `skills/event-driven-reviewer/` — reroute external-subagent references to `domain-reviewer`.
- `profiles.json` — per-profile `agents` / routing map (additive).
- `scripts/` (`check-consistency`) — validate skill contracts, `primary_agent`, profile agents,
  and routed reviewers.
- `install.ps1` / `install.sh` — confirm the six new agents copy per-file (mechanism already exists).
- `docs/` — a skills-vs-agents explainer and the routing model.
- `CHANGELOG.md` — record the reviewer routing source change and the new agent layer.

## Proposed approach

**Step 1 — Persist Phase 1 inventory.** Commit the Phase 1 findings/matrix into this feature folder
(e.g. an `INVENTORY.md` or a section here) so the agent contracts have a durable source.

**Step 2 — Decide the contract carrier.** Sample 5–6 representative SKILL.md files across
categories; choose frontmatter keys (preferred, machine-readable) vs a `## Contract` section.
Record the choice in DECISIONS as a follow-up (D011) if it deviates from the SPEC's leaning.

**Step 3 — Author the six agent contracts** as `agents/*.md` using Claude agent frontmatter
(`name`/`description`/`model`/`tools`) plus a body with responsibility, inputs, outputs, skills
consumed, allowed actions, forbidden actions, when-to-run. Model choice: reviewers read-only
(Read/Grep/Glob), `implementer` gets Edit/Write/Bash, `codebase-researcher` read-only + Graphify.

**Step 4 — Add skill contracts** to all 61 SKILL.md files in one mechanical pass, values derived
from the Phase 1 Skill→Agent matrix. Reviewers → `domain-reviewer`; security reviewers →
`security-reviewer`; lifecycle → `solution-architect` / `implementer` / `final-conformance-reviewer`;
mindset → all agents (secondary); orchestration → `orchestration-context`.

**Step 5 — Reroute the three externally-coupled reviewers** — change only the routing target text
from `java-spring` / `api-design` subagent to `domain-reviewer`; leave the review logic intact.

**Step 6 — Express routing in profiles.json** — populate per-profile `agents` (core = all six;
overlays add their reviewers to `domain-reviewer`'s scope) and an additive routing map. Keep
`skills` arrays unchanged.

**Step 7 — Extend check-consistency** — add validation that: every `primary_agent` resolves;
every profile agent exists on disk or in `plannedAgents`; every routed reviewer exists; every skill
contract parses against the schema.

**Step 8 — Documentation** — write the skills-vs-agents explainer; update `agents/README.md` and
`CHANGELOG.md`.

**Step 9 — Validation** — run `check-consistency`, installer dry-runs per profile, and the manual
agent-boundary walkthrough from the SPEC Test strategy.

## Alternatives considered

- **Convert candidate skills to agents** (`graphify`, `review-all`, etc.) — rejected (D001/D010):
  they are fan-out/orchestration/procedure capabilities, not accountable actors.
- **One reviewer agent per stack** — rejected (Non-goals): agent-per-technology explosion; the
  single `domain-reviewer` selects reviewers by profile instead.
- **A `## Contract` section over frontmatter** — deferred to Step 2; frontmatter preferred for
  machine-readability by `check-consistency`.
- **Ship agents immediately** — rejected: SPEC requires agents added under `agents/` only when
  implementation begins (AC-002).

## Dependencies

- Existing `check-consistency` script (specs 007/012) — must be extensible.
- `profiles.json` 0.4.0 `agents`/`plannedAgents` slots.
- Installer per-file agent copy mechanism (already shipped for `deep-reasoner`/`fast-worker`).
- No external services, providers, or libraries.

## Risks

- **R-1 (High):** Reviewer reroute changes review behavior for downstream users — mitigate by
  preserving skill bodies and documenting in CHANGELOG.
- **R-2 (Medium):** Contract frontmatter schema errors break skill parsing — mitigate with a CI
  schema check before merge.
- **R-3 (Medium):** profiles.json routing breaks older installers — mitigate with additive-only,
  ignorable keys.
- **R-4 (Low):** security/domain overlap on payments — mitigate with explicit boundaries.
- **R-5 (Low):** provider-agnostic language drifts Claude-specific — mitigate with the
  `provider_specific` flag.

## Test strategy

- **Schema/unit:** `check-consistency` validates all 61 contracts parse and every
  `primary_agent`/profile-agent/routed-reviewer resolves.
- **Integration:** installer dry-run per profile confirms the six agents copy and skills still link.
- **Regression:** pre-existing skill↔profile consistency checks still pass.
- **Manual:** dispatch each of the six agents on a sample feature; confirm reviewers make no code
  edits and `implementer` stops on a missing decision.
- Testing ownership across agents follows D005 (no dedicated test agent).

## Rollback strategy

All changes additive: revert the six `agents/*.md`, the `profiles.json` routing additions, the
SKILL.md contract blocks, and the `check-consistency` extension via `git revert` of the feature
branch. `deep-reasoner`/`fast-worker` and every skill body remain untouched, so rollback cannot
regress the existing orchestration path. No data, runtime state, or downstream migration involved.

## PLAN verification checklist

- [x] The plan covers all acceptance criteria.
- [x] The plan avoids behavior outside the spec.
- [x] Risks are documented.
- [x] Test strategy is documented.
- [x] Rollback strategy is documented.
- [x] SPEC.md status has been updated to `Ready`.
