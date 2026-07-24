# Spec-Driven Development — operating guide (Codex adapter)

> **Provider-neutral SDD workflow, packaged for OpenAI Codex.** This file is the Codex adapter's
> operating guide. It encodes the same **SDD Core** workflow the Claude Code adapter runs — see
> [`../../docs/PROVIDER_ADAPTERS.md`](../../docs/PROVIDER_ADAPTERS.md) — expressed as instructions a
> Codex session follows, plus a set of lifecycle prompts under [`prompts/`](prompts/).
>
> **Status: prompt-based, unverified against a live Codex CLI in this environment.** See
> [`PARITY.md`](PARITY.md) for exactly what does and does not carry over from the Claude adapter.

## How to use this file

Copy this file to your **project root as `AGENTS.md`** (the convention Codex reads for repo
instructions), or merge its rules into your existing `AGENTS.md`. Install the lifecycle prompts with
[`install-codex.sh`](install-codex.sh) / [`install-codex.ps1`](install-codex.ps1) so they are
available as prompts in your Codex session. Then drive the workflow prompt by prompt.

Nothing here executes automatically. **These are conventions the model must follow, not enforced
guardrails** — Codex has no verified tool-call hook mechanism in this environment, so unlike the
Claude adapter, none of the rules below are mechanically enforced. Treat them as a discipline you
and the model both uphold.

## The workflow

Spec-Driven Development sits between "having an idea" and "opening a pull request":

```
Requirement → SPEC → PLAN → TASKS → DECISIONS → scoped implementation → layered review → evidence → PR
```

Each step produces a durable artifact under `specs/features/<NNN-feature-name>/`, using the shared,
provider-neutral templates in [`../../specs/_templates/`](../../specs/_templates/) (the **same**
templates the Claude adapter uses — they are SDD Core, not Claude-specific).

| Step | Prompt | Output | Gate |
|---|---|---|---|
| Specify | `prompts/sdd-spec-create.md` | `SPEC.md` (status `Draft`) | — |
| Plan | `prompts/sdd-spec-plan.md` | `PLAN.md`, `TASKS.md`, `DECISIONS.md`; SPEC → `Ready` | — |
| Analyze | `prompts/sdd-spec-analyze.md` | consistency verdict | **Must be Ready before implementing** |
| Implement | `prompts/sdd-spec-implement.md` | code + tests, one task at a time; SPEC → `In Progress` | Refuse if SPEC is `Draft` |
| Review | `prompts/sdd-spec-review.md` | review verdict + risk-triggered reviews | — |
| Close | `prompts/sdd-spec-close.md` | implementation summary; SPEC → `Done` | Refuse unless `In Review` |
| Guardrails | `prompts/sdd-guardrails.md` | contradiction/obsolescence check across the four docs | Run before plan/implement/close |

## Roles (agent responsibility model)

The Claude adapter ships these as native subagents with a restricted `tools:` grant. **Codex has no
verified equivalent here**, so on this adapter they are *roles the single session adopts* — a lens
for the current step, not an isolated actor with enforced permissions:

- **Researcher** — understand the affected code area; produce a bounded reading list, not a full-repo
  dump. Read-only in spirit.
- **Architect** — author/curate SPEC/PLAN/TASKS/DECISIONS; surface every non-obvious decision into
  `DECISIONS.md`. Writes specs, not application code.
- **Implementer** — execute one approved task at a time, strictly within its file boundary; stop the
  moment a needed decision is not already recorded.
- **Security reviewer** — auth, secrets, payments, permissions, sensitive-data handling;
  severity-ranked findings with evidence.
- **Domain reviewer** — stack-specific correctness (idioms, migrations, contracts).
- **Final-conformance reviewer** — verify SPEC → PLAN → TASKS → DIFF → TESTS → REVIEW before close.

When you switch steps, state which role you are adopting. Because the roles are not mechanically
isolated on Codex, be *more* deliberate about honoring their boundaries (e.g. do not let the
Implementer role invent an architectural decision).

## Guardrails (conventions — NOT enforced on Codex)

The Claude adapter enforces these with hooks. On Codex they are rules you must follow by hand:

- **Never** run `git push`, `git commit`, or `git add .` on the user's behalf without explicit
  instruction. Committing and pushing are deliberate human actions.
- **Do not** implement against a `Draft` spec — plan it to `Ready` first.
- **Do not** close a feature that is not `In Review`.
- **Do not** edit secrets, `.env`, or local settings files.
- **Do not** load a Graphify `graph.json` wholesale into context — use a scoped query or the
  `GRAPH_REPORT.md` summary if present; Graphify is optional and never a source of truth.
- **Do not** make an architectural decision that is not written down in `DECISIONS.md`.
- Keep changes scoped: one bounded task at a time, minimal diff, code that reads like its neighbors.

## Bounded context

- Read only what the current task needs. Prefer the active feature folder over scanning the repo.
- Graphify is an **optional** accelerator. If `.graphify/GRAPH_REPORT.md` exists and is fresh, use it
  for impact analysis; otherwise fall back to targeted search. Never make it mandatory.

## What this adapter does NOT provide

Read [`PARITY.md`](PARITY.md) before relying on parity. In short, relative to the Claude adapter,
the Codex adapter does **not** ship: enforced tool-call hooks, native subagents with `tools:` grants,
the full 61-skill catalogue (only the lifecycle spine), profile-filtered install, or stack-specific
reviewers. These are honest gaps, not oversights.
