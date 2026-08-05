# Implementation Plan: Delivery-operations profile

## Summary

Add a `delivery-operations` profile carrying four delivery review skills (`deployment-review`,
`container-review`, `pipeline-review`, `release-readiness`) plus one evidence-gated mindset skill
(`rightsizing-advisor`), a `RUNBOOK.md` context template, `review-all` routing on deployment-artifact
detection, and repair of the `kubernetes-deployment-reviewer` dangling reference. Two candidates
(`iac-review`, `kubernetes-review`) land in `plannedSkills` rather than shipping unproven.

Everything is Markdown and JSON. No executable code, no hook, no agent, no installer change.

## Related spec

[`SPEC.md`](SPEC.md) — status moved `Draft` → `Ready` by this plan.

## Impacted areas

| Area | Change | Requirement |
|---|---|---|
| `skills/deployment-review/`, `container-review/`, `pipeline-review/`, `release-readiness/` | new `SKILL.md` each | FR-002..005 |
| `skills/rightsizing-advisor/` | new `SKILL.md`, conditional on eval | FR-006, FR-011 |
| `skills/review-all/SKILL.md` | Deployment detection type + 4 routing rows | FR-008a |
| `skills/spring-security-reviewer/SKILL.md` | line 119 handoff repointed | FR-008b |
| `profiles.json` | new profile block, `agentRouting`, `agentRoutingExempt` | FR-001, D011 |
| `docs/_templates/RUNBOOK.md` | new template | FR-007 |
| `docs/_templates/DEPLOYMENT.md` | line 5 dangling ref repaired | FR-008b |
| `README.md` | badges, markers, skill tables, profile table, tree comment | FR-009, FR-012 |
| `docs/AGENTIC_ROUTING.md`, `adapters/README.md`, `adapters/claude/README.md`, `adapters/codex/prompts/README.md`, `adapters/codex/PARITY.md` | unguarded count claims | FR-012, FR-013 |
| `evals/scenarios/rightsizing-advisor.md`, `evals/results/` | scenario + result | FR-011 |
| `CHANGELOG.md` | entry | FR-014 |
| **Untouched:** `hooks/`, `agents/`, `settings.template*.json`, `install.sh`, `install.ps1` | — | FR-015 |

## Proposed approach

**Sequencing is dictated by three hard gates discovered while inspecting the checker.** The order
below is not stylistic; reversing steps 2 and 3 fails CI.

1. **Skills first, profile second.** `install.sh` treats a `skills` entry with no directory on disk
   as a hard error, and `check-consistency.sh` enforces the same both ways (orphan skill
   directories also fail). So all `SKILL.md` files land before `profiles.json` names them.

2. **Contract values come from closed enums**, not from judgment (`check-consistency.sh:325-334`):
   - `category` ∈ {lifecycle, context-research, domain-reviewer, quality-review, mindset,
     orchestration}. The three artifact reviewers take `domain-reviewer`; `release-readiness` takes
     `quality-review` (it produces a verdict, not domain findings); `rightsizing-advisor` takes
     `mindset`.
   - `primary_agent` must resolve to one of the six lifecycle agents, `orchestration-context`,
     `any`, or `human`. D007's mapping is valid under this rule; `solution-architect` is a
     lifecycle agent.
   - `profile_scope` entries must be real profile keys — so `[delivery-operations]` is only valid
     *after* step 3, which is why the checker is run once at the end rather than after each skill.

3. **`agentRouting` is mandatory for non-core profile skills** (rule 7, spec 018 D014): every
   non-core profile skill must appear in the profile's `agentRouting`, or in its optional
   `agentRoutingExempt` array. This was not in the SPEC and forces D011 below.

4. **The eval gates the counts.** `rightsizing-advisor`'s verdict decides whether the skill count
   is 66 or 65, so `check-consistency.sh --fix` runs *after* the eval, not before. Running `--fix`
   early would bake in a count the eval may invalidate.

5. **Counts are synced by the tool, not by hand.** `bash scripts/check-consistency.sh --fix`
   rewrites README markers and the five badges. The skill tables, profile table, directory-tree
   comment and the six unguarded prose claims (FR-012) are **not** covered by `--fix` and are
   edited manually — that asymmetry is the whole reason FR-012 exists.

## Alternatives considered

- **Take spec number 023** — rejected (D001): reserved in `CONTRIBUTING.md`, `evals/scenarios/README.md`
  and thirty-two references across spec 022.
- **Ship all seven candidate skills** — rejected (D004, D005): `iac-review` and `kubernetes-review`
  have no evidence base in this feature, and shipping a Kubernetes reviewer in the profile's v1
  signals endorsement through shape regardless of wording.
- **A dedicated `delivery-reviewer` agent** — rejected (D007): an agent here is a tool-grant
  boundary, and nothing about a Dockerfile needs a different grant than a Spring config.
- **Merge `rightsizing-advisor` into `deployment-review` as a section** — rejected (D006): it would
  fire only once the artifacts exist, which is exactly too late.
- **Extend `check-consistency.sh` to guard prose count claims** — rejected for this feature (OQ-5):
  it would mean changing the gate that judges this change.
- **Route `rightsizing-advisor` to `solution-architect` in `agentRouting`** — rejected (D011) in
  favour of `agentRoutingExempt`.

## Dependencies

- **Claude Code CLI** at `/Users/manu/.local/bin/claude` — required for FR-011's eval. Present.
  `SKILL_EVAL_RUNNER` must be exported with an explicit `--model <id>`, or the harness refuses to
  run (`skill-eval.sh:117` — a result without a model identifier is not evidence).
- **`pwsh`** — optional, only to spot-check `install.ps1`. If absent, the PowerShell path is
  recorded as unverified rather than claimed (repo precedent: spec 015).
- **`python3`** — used by `check-consistency.sh` and `install.sh`. Present.
- No network dependency, no external service.

## Risks

| # | Risk | Severity | Mitigation |
|---|---|---|---|
| R-1 | The eval returns `NO-BASELINE-FAILURE` — models may not have the overbuild reflex the skill assumes | **High (likely)** | FR-011's fallback is pre-agreed: skill → `plannedSkills`, count 65, reason in DECISIONS. No renegotiation needed mid-implementation. Result is committed either way. |
| R-2 | `review-all` routing is prompt behaviour with no mechanical test — the profile could ship and simply not fire | High | AC-004a greps the static rules; AC-004b runs two real fixtures. Recorded as one dated observation, not a proof. |
| R-3 | Description cap (400 chars) cannot hold the negative triggers D008 requires, especially for `deployment-review` (three neighbours) | Medium | Precedent from spec 022: challenge the cap rather than drop a clause. If it binds, raise it in a DECISIONS amendment with the measured lengths. |
| R-4 | The four new skills overlap in practice despite D008's boundaries, producing duplicate findings | Medium | Each boundary is written into **both** skills. AC-004b's fixture surfaces duplication if it exists. |
| R-5 | FR-012's six prose claims are fixed by hand and a seventh appears later | Medium | AC-012 greps repo-wide as the check. OQ-5 records the durable fix as a follow-up spec. |
| R-6 | A neutrality violation slips into a skill body — the profile quietly pushes heavier infra | Medium | AC-011 is a mandatory read of all five bodies against the NFR, tracked as its own task (T016). |
| R-7 | `profile_scope: [delivery-operations]` written before the profile exists fails the checker | Low | Sequencing (approach §2): checker runs once, after `profiles.json` lands. |

## Test strategy

- **Unit / structural:** `bash scripts/check-consistency.sh` (profiles ↔ disk ↔ settings ↔ README,
  `[SKILL-FORM]`, SDD Contract enums, agentRouting rules 4-8) and
  `bash scripts/check-consistency.test.sh` (the checker's own 30-case mutation suite).
- **Integration:** a real `bash install.sh --profile delivery-operations --central-dir <scratch>`
  run against a throwaway directory — never `~/.claude` (CONTRIBUTING dev-setup rule). Output
  captured in TASKS.md. `install.ps1` spot-checked if `pwsh` exists, otherwise recorded unverified.
- **E2E / behavioural:** the two `review-all` fixtures (AC-004b), transcripts recorded.
- **Behavioural (skill):** `bash scripts/skill-eval.sh rightsizing-advisor --reps 5` against a new
  self-contained scenario, 10 model calls, every flagged match read before `manually-read: YES`.
- **Regression:** `bash scripts/graphify.test.sh` and `bash scripts/skill-eval.test.sh` — neither
  is touched by this feature, so both must stay green; they are the guard that this change did not
  disturb unrelated machinery.
- **Manual:** read all five skill bodies for the neutrality NFR (AC-011); confirm no shipped file
  presents `kubernetes-deployment-reviewer` as existing (AC-005).

## Rollback strategy

Every change is additive Markdown/JSON in one commit-block per phase. Rollback is `git revert` of
the feature commits. There is no migration, no state, no deployed artifact, and nothing installed
into a user's `~/.claude` by this repository's own CI.

Partial rollback is well-defined at two points:

- **Drop `rightsizing-advisor` only** — remove the skill directory, move it to `plannedSkills`,
  re-run `check-consistency.sh --fix`. This is FR-011's fallback and is expected to be exercised.
- **Drop the whole profile, keep the repairs** — the `kubernetes-deployment-reviewer` fix
  (FR-008b) and the count corrections (FR-012) are independent of the profile and are worth
  keeping even if the profile is reverted. They are sequenced into their own phase (T003) so this
  split is a clean revert boundary rather than a manual untangle.

## PLAN verification checklist

- [x] The plan covers all acceptance criteria. (AC-001..013 mapped in TASKS.md)
- [x] The plan avoids behavior outside the spec. (FR-015's untouched surface is a task, T017)
- [x] Risks are documented. (R-1..R-7, with R-1 rated likely)
- [x] Test strategy is documented.
- [x] Rollback strategy is documented, including the expected partial rollback.
- [x] SPEC.md status has been updated to `Ready`.
