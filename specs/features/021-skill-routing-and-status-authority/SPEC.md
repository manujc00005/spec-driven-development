# Feature Spec: Skill routing disambiguation and spec-status authority

## Status

Done

## Problem

Two routing/governance gaps, both observed in real sessions and both confirmed by the
Azure Skills plugin's handling of the same problems
(`/Users/manu/Proyectos/example/azure-skills`, analysed 2026-07-25):

1. **No declared authority over `SPEC.md` status.** Four skills perform the four status
   transitions today — `spec-plan` (Draft → Ready), `spec-implement` (Ready → In Progress),
   `spec-review` (→ In Review, on a Pass verdict only), `spec-close` (In Review → Done) —
   but **no document states that these are exclusive**. Nothing forbids another skill, an
   agent, or an ad-hoc editor from promoting a spec directly. This is not theoretical: while
   building specs 019 and 020 in this repository, the status of both was promoted to
   `In Review` by a direct scripted edit, bypassing `/spec-review` entirely. The gate exists
   (`spec-close` refuses a spec that is not `In Review`) but it can be satisfied by simply
   writing the string, which makes the whole lifecycle gate bypassable by accident.
   Azure's plugin closes the equivalent hole explicitly: only `azure-validate` may set a plan
   to `Validated`, and every other skill is told it is forbidden to do so.

2. **Skill descriptions carry only positive triggers.** All 61 skills describe when to use
   them; none describe when *not* to, or which sibling to use instead. Several pairs are
   genuinely confusable at routing time (`spec-create` vs `spec-clarify` vs `spec-update`,
   `spec-plan` vs `spec-analyze`, `spec-review` vs `qa-review` vs `review-all`, `debugger`
   vs `root-causer`, `security-review` vs `threat-modeler`, `test-engineer` vs `qa-review`,
   `context-manager` vs `graphify-context`, `sdd` vs `sdd-orchestrate`). Two skills already
   hint at this informally (`sdd-medium`/`sdd-full` say "Consider using /sdd instead"),
   which shows the need without a convention behind it.

## Goal

- Make the spec-status state machine **authoritative and auditable**: one table naming the
  sole owner of each transition, an explicit prohibition on any other promoter (including
  manual edits), and matching text in the owning and non-owning skills.
- Give the confusable skills **negative triggers** — a terse "not for X, use /y" clause — so
  routing failures are prevented at selection time rather than corrected afterwards.

## Non-goals

- **No hook enforcement of status authority.** A `PreToolUse` hook can see that a `Status`
  line changed but cannot know which skill is driving the edit, so it can only warn, never
  authorize (DECISIONS D001). No new hook family is added.
- No change to `profiles.json`, installers, settings templates, or any hook script.
- No new skills, no new agents, no skill deleted or renamed.
- **Not all 61 skills.** Negative triggers are applied only to documented confusion pairs
  (D003) — a blanket rollout would cost session context for no routing benefit.
- No ALL-CAPS "MANDATORY COMPLIANCE" tone; this framework enforces with gates and calm
  prose, not shouting (D002).

## Users / Actors

- Any model selecting a skill at routing time (the negative-trigger consumer).
- The four transition-owning skills; every other lifecycle skill and the
  `solution-architect` agent (the status-authority consumers).
- The engineer reading `sdd-guardrails` to understand the lifecycle in one place.

## Current behavior

- The four transitions happen in four skills; the rule lives nowhere. `spec-update` says
  "Do not change the spec status unless the user instructs it" and `spec-review` says not to
  change status on a Partial/Fail verdict — two partial negatives, no whole.
- `sdd-guardrails` documents the **Decision** state machine (section 1) but not the **Spec
  status** one.
- Skill descriptions are positive-only.

## Desired behavior

- `sdd-guardrails` carries a **Spec Status Authority** section: the transition→owner table,
  the exclusivity rule, and the "a status string written by hand is not a passed gate" rule.
- Each owning skill states it is the sole authorized promoter of its transition; each
  non-owning lifecycle skill states it must not promote.
- `agents/solution-architect.md` (the agent that writes SDD documents) carries the same rule.
- Confusable skills carry a terse negative-trigger clause in their description.

## Functional requirements

- **FR-001:** `skills/sdd-guardrails/SKILL.md` gains a **Spec Status Authority** section
  containing: the four transitions with their sole owner, the precondition each owner must
  verify before promoting, an explicit statement that no other skill/agent/manual edit may
  promote, and the rule that writing the status string does not satisfy the gate the string
  represents. It must also cover the two non-forward moves the lifecycle allows —
  **`Archived`** and **demotion** — naming their owner and their recording requirement, so no
  documented state is left without one (added during QA — see D006).
- **FR-002:** Each of `spec-plan`, `spec-implement`, `spec-review`, `spec-close` states that
  it is the **only** authorized performer of its transition.
- **FR-003:** `spec-create`, `spec-clarify`, `spec-analyze`, `sdd-orchestrate`, and
  `spec-update` state that they must not promote status, and name the skill that may.
  (`spec-update` added during QA — its pre-existing line was weaker than the new rule.)
- **FR-004:** **Every agent able to write files** carries the same prohibition, scoped to what
  it legitimately owns — `solution-architect`, `implementer` (may perform only
  `Ready` → `In Progress`), and `fast-worker` (may perform none). Agent/skill parity is the
  spec-020 lesson: prose must match across both layers, and applying it to one of three
  write-capable agents leaves the gap open (widened during QA — see D006).
- **FR-005:** Negative-trigger clauses are added to the descriptions of the documented
  confusion pairs listed in PLAN's *Confusion pairs* table.
- **FR-006:** Negative triggers use **one terse sentence** appended to the existing
  description, opening with a negation from the family `Not for …` / `Not a …` / `Not the …` /
  `Not needed …`, and naming the correct sibling as a slash-command. No ALL-CAPS, no
  multi-line blocks, no restructuring of existing description text. (Widened from a single
  literal template during review — see D005.)
- **FR-007:** `scripts/check-consistency.sh` exits 0, and `profiles.json`, `hooks/`,
  `install*.{sh,ps1}`, and `settings.template*.json` are untouched.

## Non-functional requirements

- **Context economy:** every skill description loads at session start, so added text is a
  standing per-session cost. Clauses stay to one sentence; the bounded pair list keeps the
  total addition under roughly 400 words across the repository.
- **Backward compatibility:** frontmatter keys and every `## SDD Contract` block are
  unchanged; `check-consistency.sh` does not validate descriptions, so no harness rule moves.
- **Honesty:** the status rule is documented as a convention enforced by skill text, not as
  a mechanically enforced guarantee (see D001).

## API / Interface changes

None. Markdown prose only: 1 guardrails section, ~8 skill bodies, ~15 skill descriptions,
1 agent file.

## Data model changes

None.

## Edge cases

- **User explicitly instructs a status change.** The owner rule binds skills, not the human;
  an explicit user instruction remains valid and is called out in the guardrails text
  (matching `spec-update`'s existing "unless the user instructs it").
- **`spec-review` returns Partial/Fail.** No promotion — the existing rule is preserved and
  folded into the authority table rather than replaced.
- **A skill in the confusion list gains a new sibling later.** The clause names the sibling
  by slash-command, so a rename shows up as a stale reference; acceptable, and cheaper than a
  machine-validated cross-reference table (not added — see Non-goals).

## Acceptance criteria

- **AC-001:** `skills/sdd-guardrails/SKILL.md` contains a Spec Status Authority section with
  all four forward transitions plus `Archived` and demotion, their owners, and the
  no-manual-promotion rule — every state in the documented lifecycle has an owner. (FR-001)
- **AC-002:** Each of the four owning skills contains an explicit sole-authority sentence for
  its own transition. (FR-002)
- **AC-003:** `spec-create`, `spec-clarify`, `spec-analyze`, `sdd-orchestrate`, and
  `spec-update` each contain an explicit must-not-promote sentence naming the authorized
  skill. (FR-003)
- **AC-004:** Every write-capable agent (`solution-architect`, `implementer`, `fast-worker`)
  forbids promoting spec status outside what it legitimately owns. (FR-004)
- **AC-005:** Every skill named in PLAN's *Confusion pairs* table has a negative-trigger clause
  in its frontmatter `description` — one sentence, opening with a `Not for/a/the/needed …`
  negation, naming the correct sibling as a slash-command, no ALL-CAPS — and PLAN's table text
  matches the shipped text verbatim. (FR-005, FR-006)
- **AC-006:** `bash scripts/check-consistency.sh` exits 0 and `git status --porcelain` shows
  no modification to `profiles.json`, `hooks/`, `install*.sh`, `install*.ps1`, or
  `settings.template*.json`. (FR-007)

## Test scenarios

- **Unit:** N/A (no executable code).
- **Integration:** `scripts/check-consistency.sh` (AC-006); a grep asserting every pair-table
  skill has a `Not for` clause (AC-005).
- **Manual:** read the guardrails section and the four owning skills against AC-001..003.

## Assumptions

- Skill `description` is the field a host uses for routing/auto-selection, so negative
  triggers belong there rather than only in the body.
- The Azure plugin's structure was read as a design reference only; nothing is copied from
  it, and its telemetry hook pattern is explicitly rejected (this framework's hooks never
  call the network).

## Open questions

- **OQ-1 — Deferred.** Whether a non-blocking `spec-status-reminder` hook (warn when a
  `SPEC.md` Status line is edited, without claiming to authorize) is worth a future spec.
  Unchanged at close: the reasoning in D001 still holds — a hook cannot attribute an edit to a
  skill, so it could only warn. Track alongside the CI-validation gap below rather than as part
  of this feature.
- **OQ-2 — Deferred (raised at close).** Neither the negative-trigger clauses nor the section-11
  rules are machine-validated: `check-consistency.sh` does not inspect skill descriptions or
  agent prose, so a new confusable skill without a clause, or a new write-capable agent without
  a status rule, would pass CI unnoticed. Accepted for this feature (D003/D005/D006) and worth
  its own small spec.

## Contracted services

`specs/SERVICES.md` is absent → all billable add-ons treated as NOT contracted. This feature
touches none.
