# Implementation Plan: Skill routing disambiguation and spec-status authority

## Summary

Documentation-only change in two independent halves: (A) declare the spec-status state machine
authoritative in `sdd-guardrails` and mirror it into the owning/non-owning skills and the
`solution-architect` agent; (B) append one-sentence negative-trigger clauses to the descriptions
of the confusable skill pairs listed below. No code, no manifest, no hook.

## Related spec

`specs/features/021-skill-routing-and-status-authority/SPEC.md`

## Impacted areas

**A — Status authority (9 files)**

| File | Change |
|---|---|
| `skills/sdd-guardrails/SKILL.md` | New section 11 *Spec Status Authority*; existing *Limitations* renumbered 11 → 12 (D004) |
| `skills/spec-plan/SKILL.md` | Sole-authority sentence: Draft → Ready |
| `skills/spec-implement/SKILL.md` | Sole-authority sentence: Ready → In Progress |
| `skills/spec-review/SKILL.md` | Sole-authority sentence: → In Review (Pass verdict only) |
| `skills/spec-close/SKILL.md` | Sole-authority sentence: In Review → Done |
| `skills/spec-create/SKILL.md` | Must-not-promote sentence (creates as `Draft`) |
| `skills/spec-clarify/SKILL.md` | Must-not-promote sentence |
| `skills/spec-analyze/SKILL.md` | Must-not-promote sentence (verdict only; `spec-plan` promotes) |
| `skills/sdd-orchestrate/SKILL.md` | Must-not-promote sentence (routes to the owner instead) |
| `agents/solution-architect.md` | Forbidden action: promoting spec status outside the owners |

**B — Negative triggers (descriptions only)** — see *Confusion pairs* below.

**Untouched (hard):** `profiles.json`, `hooks/**`, `install*.sh`, `install*.ps1`,
`link-project.*`, `scripts/**`, `settings.template*.json`, every `## SDD Contract` block, all
skill/agent frontmatter keys other than `description`.

## Confusion pairs (the maintained source of truth for FR-005)

| Skill | Confusable with | Clause to append |
|---|---|---|
| `spec-create` | `spec-clarify`, `spec-update` | Not for strengthening an existing spec (use /spec-clarify) or changing one mid-implementation (use /spec-update). |
| `spec-clarify` | `spec-create`, `spec-update` | Not for creating a new spec (use /spec-create) or changing scope after implementation started (use /spec-update). |
| `spec-update` | `spec-clarify` | Not for pre-planning clarification of a Draft spec — use /spec-clarify. |
| `spec-plan` | `spec-analyze`, `architect-review` | Not for validating an existing plan (use /spec-analyze) or exploring architecture before one exists (use /architect-review). |
| `spec-analyze` | `spec-plan`, `sdd-guardrails` | Not for producing PLAN/TASKS/DECISIONS — use /spec-plan. |
| `spec-review` | `qa-review`, `review-all` | Not for behaviour and regression review (use /qa-review) or for running every applicable review at once (use /review-all). |
| `qa-review` | `spec-review`, `test-engineer` | Not for spec-conformance review (use /spec-review) or for designing a test strategy up front (use /test-engineer). |
| `test-engineer` | `qa-review` | Not for the pre-merge acceptance-criteria and regression review — that is /qa-review. (Reworded during implementation: the original draft said "not for verifying an existing implementation", which contradicted this skill's own "or as a standalone audit after implementation".) |
| `review-all` | `spec-review` | Not for a single targeted review — invoke that review directly (e.g. /security-review). |
| `refactor-review` | `scope-keeper` | Not a licence to refactor during implementation — for scope discipline while editing, use /scope-keeper. |
| `debugger` | `root-causer` | Not the mindset manual on debugging stance — that is /root-causer. |
| `root-causer` | `debugger` | Not the step-by-step debugging procedure — that is /debugger. |
| `security-review` | `threat-modeler` | Not for attacker-mindset guidance before code is written — that is /threat-modeler. |
| `threat-modeler` | `security-review` | Not a review of code already written — for that, use /security-review. |
| `verifier` | `qa-review` | Not a test-coverage or acceptance review — that is /qa-review. |
| `scope-keeper` | `refactor-review` | Not a cleanup review of code already written — that is /refactor-review. |
| `context-manager` | `graphify-context` | Not for interpreting an existing Graphify report — that is /graphify-context. |
| `graphify-context` | `context-manager` | Not for building a reading list when no graph exists — that is /context-manager. |
| `sdd` | `sdd-orchestrate` | Not for multi-model delegation across deep-reasoner/fast-worker — that is /sdd-orchestrate. |
| `sdd-orchestrate` | `sdd` | Not needed for single-session work — /sdd covers that without delegation overhead. |
| `architect-review` | `spec-plan` | Not for producing PLAN/TASKS artefacts — that is /spec-plan. |

`sdd-medium` / `sdd-full` already carry an informal redirect to `/sdd` and are left as-is.

## Proposed approach

1. **A1** — Insert *Spec Status Authority* into `sdd-guardrails` (table + exclusivity +
   "a written status string is not a passed gate" + the user-instruction exception); renumber
   *Limitations* to 12.
2. **A2** — Add the sole-authority sentence to the four owning skills, next to their existing
   status instruction so the rule sits where the action happens.
3. **A3** — Add the must-not-promote sentence to the four non-owning skills and the Forbidden
   actions list of `solution-architect`.
4. **B** — Append each clause from the table to that skill's `description`, preserving existing
   wording and frontmatter shape.
5. **Verify** — grep for clause coverage, grep that protected paths are untouched, run
   `check-consistency.sh`.

## Alternatives considered

- **Hook enforcement of status authority** — rejected (D001): a hook cannot attribute an edit
  to a skill, so it could only warn while implying a guarantee.
- **Azure-style ALL-CAPS `DO NOT USE WHEN` blocks** — rejected (D002): tone and per-session
  context cost.
- **Negative triggers on all 61 skills** — rejected (D003): cost without routing benefit.
- **A machine-validated cross-reference table in `check-consistency.sh`** — rejected for this
  spec: it would add a CI rule for prose, and the pair list is small enough to review by eye.
  Revisit only if clauses start drifting.
- **Appending the new guardrails section after *Limitations*** — rejected (D004): leaves the
  closing section stranded mid-document.

## Dependencies

None. Markdown only.

## Risks

- **R-1 (Medium): description bloat.** Every clause is a standing per-session context cost.
  *Mitigation:* one sentence per skill, bounded pair list (D003), explicit NFR budget in SPEC.
- **R-2 (Low): stale slash-command references** if a skill is renamed later. *Mitigation:*
  clauses name commands that exist today; a rename already requires a repo-wide grep by
  CONTRIBUTING's consistency rule.
- **R-3 (Low): the authority rule is convention, not enforcement**, so it can still be
  bypassed. *Mitigation:* stated honestly in SPEC and D001; the reminder-hook option is
  recorded as OQ-1 rather than implied.
- **R-4 (Low): renumbering a guardrails section** could break an external reference.
  *Mitigation:* grep confirmed only *section 1* is referenced outside the file (D004).

## Test strategy

- **Integration:** `bash scripts/check-consistency.sh` → exit 0 (AC-006).
- **Coverage grep:** every skill in the *Confusion pairs* table has a `Not for` clause in its
  description (AC-005); no clause uses ALL-CAPS.
- **Scope guard:** `git status --porcelain` shows no `profiles.json`, `hooks/`, `install*`, or
  `settings.template*` modification (AC-006).
- **Manual:** read the new guardrails section and the eight edited lifecycle skills against
  AC-001..004.

## Rollback strategy

Revert the touched markdown files with git. No installer, manifest, hook, or downstream state is
involved, so rollback is a single `git checkout` of the paths.

## PLAN verification checklist

- [x] The plan covers all acceptance criteria.
- [x] The plan avoids behavior outside the spec.
- [x] Risks are documented.
- [x] Test strategy is documented.
- [x] Rollback strategy is documented.
- [x] SPEC.md status has been updated to `Ready`.
