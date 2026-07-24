---
name: decision-mapping
description: Turn a loose idea into a sequenced map of investigation tickets, then drive them to resolution one at a time.
disable-model-invocation: true
---

## SDD Contract

```yaml
category: lifecycle
inputs: [loose-idea]
outputs: [investigation-tickets]
side_effects: writes-scratch
writes_code: false
writes_specs: false
analysis_only: false
primary_agent: solution-architect
secondary_agents: []
profile_scope: all
provider_specific: false
```

This skill is invoked when a loose idea requires more than one agent session to turn into a plan. It creates a stateful decision map in a markdown file, and drives the user through a sequence of tickets to resolve the open questions — which may require prototyping, research, or discussion.

## The Decision Map

The decision map is a single compact Markdown file, one per planning effort, git-tracked alongside the project. It is the canonical artifact — the **whole map is loaded as context into every session**, so it must stay compact.

Assets created during tickets should be linked to from the map, not duplicated within it.

### Structure

```markdown
## #1: Relational Or Non-Relational Database?

Blocked by: #<ticket-number>, #<ticket-number>
Type: Research | Prototype | Discuss

### Question

<question-here>

### Answer

<answer-here>
```

Each ticket must be sized to one 100K token agent session.

## Ticket Types

- **Research**: Reading documentation, third-party APIs, or local resources like knowledge bases. Creates a markdown summary as an asset. Use when knowledge outside the current working directory is required.
- **Prototype**: Writing UI or logic code to test a hypothesis, or to explore a design space. Uses `/prototype`. Creates a prototype as an asset. Use when "how should it look" or "how should it behave" is the key question.
- **Discuss**: Conversation with the agent. The default case.

## Fog of war

The map is _deliberately_ incomplete beyond the frontier. Your job is to investigate the frontier, and to resolve tickets in order to push it forward. At some point, the fog of war should have been pushed back far enough that the path to the finish line is clear — at that point, no more tickets are required and the decision map is done.

## Invocation

### Bootstrap

User invokes with a loose idea.

1. Run a discussion session to surface the open decisions.
2. Write a new decision map — mostly fog, frontier identified, trivially-decidable entries resolved inline.
3. Stop. Map-building is one session's work; do not also resolve tickets.

### Resume

User invokes with a path to an existing map and a ticket number.

1. Load the **whole map** as context.
2. Run a session to resolve the ticket, invoking skills as needed.
3. Record what the session resolved in the ticket's body.
4. Add newly-discovered tickets (with correct `blocked_by` edges).
5. Stop.

If the decisions made invalidate other parts of the map, update or delete those nodes.

## Parallelism

The user may choose to run tickets in parallel — expect other agents to make changes to the map.

## Skipping the Decision Map

Many times, the initial discussion will result in no fog of war — no unresolved tickets. In those situations, offer the user the chance to skip the decision map, since it is only needed for multi-session decisions. If they skip it, recommend implementing directly or using `/spec-create`.

## SDD integration

- The decision map lives at `specs/features/<feature>/DECISION-MAP.md` inside each project's feature folder — not in the centralised Claude config.
- The map feeds the spec: once all blocking questions are resolved, the decisions flow into `SPEC.md`, `PLAN.md`, and `DECISIONS.md`.
- Do not start `/spec-plan` until the decision map's frontier is clear.

## Recommended next command

- To bootstrap a new map → `/decision-mapping <loose idea>`.
- If a ticket is resolved and the frontier is clear → `/spec-create <feature>` to start the formal spec.
- If questions remain → continue with the next unblocked ticket in the decision map.
