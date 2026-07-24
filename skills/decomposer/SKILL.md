---
name: decomposer
description: Mindset manual for planning judgment — decompose before coding, find the one decision that's expensive to reverse, and skip planning entirely when the task is trivial. Use before starting a non-trivial task, and to decide whether a task even needs a plan.
---

## SDD Contract

```yaml
category: mindset
inputs: [current-task]
outputs: [behavioral-constraint]
side_effects: none
writes_code: false
writes_specs: false
analysis_only: true
primary_agent: solution-architect
secondary_agents: [implementer]
profile_scope: all
provider_specific: true
```

# The Decomposer

**Planning is not writing down what you'll touch — it's finding what could invalidate the work before you've done it.** Most of the budget belongs to the one decision you can't cheaply undo; the rest is just doing.

This governs the *judgment* around planning; `spec-plan` owns the *artifact*. When a task is already inside the SDD lifecycle, the written PLAN belongs to `spec-plan` — this manual only decides whether to think a plan up at all, how deep, and in what order. It never produces a competing plan document.

## Triggers

- Before touching code on any non-trivial task — decide the shape before the first edit.
- When a task feels big or uncertain: stop and find the expensive-to-reverse decision inside it.
- When a task feels small: decide, honestly, whether it needs a plan at all.

## Rules

- **Decompose, then find the irreversible decision.** Write the step list, then identify the *one* decision that is expensive to reverse (a schema shape, an API contract, a data migration, a public interface). That decision gets the thinking; the reversible steps don't need it.
- **Skip planning when the task is one obvious edit.** A plan for a rename or a one-line fix is noise. Recognizing that a task needs no plan — and saying so — is part of the skill, not a shortcut around it.
- **Validate the riskiest assumption first.** Order the work so the thing most likely to be wrong is tested before you build on top of it. Don't do the easy, satisfying 80% and meet the hard 20% at the end when it's expensive to change course.
- **Plan in decisions, not filenames.** A list of files you'll touch is inventory, not a plan. A plan states the choices and the one that's hard to undo — the things a reviewer would want to challenge before you start.
- **Right-size the depth to the risk.** A high-uncertainty, hard-to-reverse task earns real up-front thought; a low-risk task earns a sentence. Match the ceremony to the stakes, in both directions.

## Anti-patterns

- **Planning ceremony for a trivial task.** — Bad: a four-phase plan to rename a variable. Good: "This is a rename — no plan needed," then do it.
- **Easy-first ordering.** — Bad: building the whole UI, then discovering at the end the API can't supply the data. Good: confirm the API can supply it first, then build the UI.
- **Filename plan.** — Bad: "I'll edit `service.ts`, `controller.ts`, `dto.ts`." Good: "The one hard-to-reverse call is the DTO shape — it's the public contract; here's the shape and why."
- **Flat weighting.** — Bad: treating "add a log line" and "choose the retry semantics" as equal steps. Good: spend the thought on the retry semantics; the log line is trivia.
- **No irreversible decision named.** — Bad: a plan that never says what's expensive to change. Good: the plan's headline is the one decision worth getting right.

## Contrast

A generic model plans by enumerating what it will touch — a tidy list of files and steps that looks thorough and treats every item as equal weight. This manual plans by hunting for what could make the work wrong: the one decision that's costly to reverse, the assumption most likely to be false, the order that surfaces risk early. It also knows when *not* to plan — a generic model applies the same ceremony to a rename and a migration; this one spends thought in proportion to what's at stake.

## Closing checklist

- [ ] For a non-trivial task, did I name the one expensive-to-reverse decision?
- [ ] For a trivial task, did I skip planning instead of manufacturing it?
- [ ] Is the work ordered so the riskiest assumption is validated first?
- [ ] Is the plan about decisions, not just a list of files?
- [ ] Does the depth of planning match the actual risk?
- [ ] If inside the SDD lifecycle, did I leave the PLAN artifact to `spec-plan`?
