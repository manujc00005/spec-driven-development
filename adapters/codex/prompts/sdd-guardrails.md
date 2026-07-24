# SDD: Guardrails / consistency check

<!--
Codex adapter prompt. Derived from the provider-neutral SDD Core skill `skills/sdd-guardrails`.
Same checks as the Claude adapter's `/sdd-guardrails`. IMPORTANT: on the Claude adapter, some
guardrails are ALSO enforced deterministically by tool-call hooks. On Codex there are no hooks —
this prompt is the ONLY line of defense, so run it deliberately. See ../PARITY.md.
-->

You are working in **Spec-Driven Development** mode. This is the **consistency guardrail** pass. Run
it before planning, before implementing, and before closing — whenever a feature has more than one
decision on record, or touches money/units, schema, or deployment.

## Inputs

- `SPEC.md`, `PLAN.md`, `TASKS.md`, `DECISIONS.md` for the active feature.

## What to detect

1. **Contradictions between documents** — a task or plan step that conflicts with the SPEC (e.g.
   implements a non-goal), or two decisions that cannot both hold.
2. **Obsolete plan being implemented** — a task that carries out a decision now `Superseded` or
   `Rejected`, or a plan step for scope the SPEC removed.
3. **Decisions used after being superseded** — a later step relying on a decision that a newer
   decision replaced.
4. **Ambiguous naming reused across versions** — the same identifier meaning different things in
   different documents (a common source of money/unit and schema bugs).
5. **Status-machine violations** — implementing a `Draft` spec; closing a spec not `In Review`.

## Decision state machine (reference)

`Proposed → Accepted → (Superseded | Rejected | Deferred)`. Only `Accepted` decisions are
authoritative; a `Superseded` decision must name its successor.

## Output

- A verdict: **Clear** / **Issues found**. For each issue: the two documents/lines in conflict, why
  it is a conflict, and the minimal fix. If issues are found, **stop the workflow** until they are
  resolved — do not plan/implement/close over a contradiction.

## Guardrails (conventions on Codex — see ../AGENTS.md)

This is analysis only. And remember: on Codex, the behavioral guardrails in `../AGENTS.md`
(no silent `git push`, no undocumented decisions, no `graph.json` wholesale, no `Draft`-spec
implementation) are **not** mechanically enforced — you are responsible for upholding them.
