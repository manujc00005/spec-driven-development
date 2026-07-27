# SDD: Consistency gate (analyze)

<!--
Codex adapter prompt. Derived from the provider-neutral SDD Core skill `skills/spec-analyze`.
Same procedure as the Claude adapter's `/spec-analyze`; guardrails are conventions, not hooks.
-->

You are working in **Spec-Driven Development** mode. This is the **consistency gate** run before any
task is implemented.

## Inputs

- `SPEC.md`, `PLAN.md`, `TASKS.md`, `DECISIONS.md` for one feature.

## Output

- A readiness verdict: **Ready** / **Partial** / **Not ready**, plus findings, and the list of which
  specialized reviews the change will need (based on what the spec declares it touches).

## What to check

1. **Coverage** — every acceptance criterion (`AC-XXX`) is covered by at least one task
   (`Covers: AC-XXX`), and every task traces back to an acceptance criterion. Flag orphans on both
   sides.
2. **Contradiction** — SPEC, PLAN, TASKS, and DECISIONS agree. No task implements behavior the SPEC
   lists as a non-goal; no decision contradicts the plan.
3. **Obsolescence** — no task implements a superseded decision; no plan step references removed
   scope.
4. **Weak tasks** — tasks too vague to implement or verify independently.
5. **Readiness blockers** — unresolved blocking open questions, `Draft` status, or missing
   PLAN/TASKS.
6. **Review detection** — from the SPEC's API/data-model/security sections, list which reviews apply
   (security, database, API, performance, frontend, privacy, domain/stack).
7. **Context budget** — the PLAN declares a `## Context budget` (reading list + model routing), the
   token economy contract (`docs/TOKEN_ECONOMY.md`). Missing section → **warning**, verdict may still
   be Ready. Section present but empty or placeholder → **blocker**. A short budget is valid; reject
   only emptiness.

## Verdict rule

- **Ready** — full coverage, no contradiction, no blocking question. Present: "Ready to implement.
  First task: T001 — [description]."
- **Partial / Not ready** — present the blocking findings and **stop**. Do not proceed to implement.

## Guardrails (conventions on Codex — see ../AGENTS.md)

Analysis only — write nothing but the verdict. Do not implement to "fix" a finding here.
