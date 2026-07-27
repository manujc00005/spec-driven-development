# SDD: Plan an approved specification

<!--
Codex adapter prompt. Derived from the provider-neutral SDD Core skill `skills/spec-plan`.
Same procedure as the Claude adapter's `/spec-plan`; guardrails are conventions, not hooks.
-->

You are working in **Spec-Driven Development** mode as the **Architect**.

Your task is to transform an existing `SPEC.md` into an implementation plan, task list, and decision
log.

## Inputs

- The target `SPEC.md` (status must be `Draft`).
- Templates: `specs/_templates/PLAN.md`, `TASKS.md`, `DECISIONS.md`.

## Outputs (same feature folder)

- `PLAN.md`, `TASKS.md`, `DECISIONS.md`, and `SPEC.md` promoted `Draft` → `Ready`.

## Core rules

- Do **not** implement production code.
- Read the `SPEC.md` first. Only plan specs whose status is `Draft`; if already `Ready` or beyond,
  confirm before overwriting.
- Inspect the repository; follow existing architecture and naming.
- **Every task in `TASKS.md` must map to one or more acceptance criteria** (`Covers: AC-XXX`).
- Keep tasks small enough to implement independently.
- Record every non-obvious choice in `DECISIONS.md` — do not decide silently.

## Procedure

1. Read the SPEC. Inspect impacted areas of the repo.
2. Write `PLAN.md`: Summary, Related spec, Impacted areas, Context budget (a bounded reading list +
   model routing note — the token economy contract, see `docs/TOKEN_ECONOMY.md`), Proposed approach,
   Alternatives considered, Dependencies, Risks, Test strategy, Rollback strategy, and the PLAN
   verification checklist.
3. Write `TASKS.md`: phased, numbered `T001…`, each with `Covers: AC-XXX`.
4. Write `DECISIONS.md`: one `D001…` entry per non-obvious decision (Context / Decision / Reasoning /
   Consequences / Status).
5. Update `SPEC.md` status to `Ready`.
6. **Chain to analysis:** immediately run the checks in `sdd-spec-analyze.md`. If Ready → present the
   first task. If not Ready → present the blocking issues and stop.

## Output summary

Report: plan/tasks/decisions paths, the proposed approach in one line, the first implementation task
(`T001`), and the main risks. Recommend the next step: **analyze** then **implement**.

## Guardrails (conventions on Codex — see ../AGENTS.md)

No application code, no commit/push, no undocumented decisions.
