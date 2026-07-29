# Implementation Plan: Skill evidence harness

## Summary

Two deliverables, deliberately split by determinism.

**A static `skill-form` check class** inside `scripts/check-consistency.sh`, reusing the pass
that already iterates `disk_skills` for the `## SDD Contract` block: description ≤ 400 chars,
description free of mechanical workflow-summary markers, `SKILL.md` body ≤ 600 lines. It runs in
CI on every push to `main` and every PR, and it fails the build like any other drift class.

**An on-demand behavioural harness** (`scripts/skill-eval.sh`) that runs a committed scenario
through two arms — treatment (scenario + full `SKILL.md`) and a mandatory no-guidance control —
N times each, and writes a dated result file naming the model. It never runs in CI, never writes
under `skills/`, and reports `NO-BASELINE-FAILURE` when the control does not exhibit the failure.

The feature then applies both: it fixes the four current lint violations, writes scenarios for
the 9 `category: mindset` skills, runs the sweep, and ships at least one skill rewritten because
the evidence demanded it.

## Related spec

`specs/features/022-skill-evidence-harness/SPEC.md`

## Impacted areas

| Area | Change |
|---|---|
| `scripts/check-consistency.sh` | new `skill-form` check class (~40 lines in the existing `python3` block) |
| `scripts/check-consistency.test.sh` | 3 new mutation cases, following the `fresh_copy` + `assert_case` pattern |
| `scripts/skill-eval.sh` | **new** — harness CLI |
| `evals/scenarios/*.md` | **new** — 9 scenario files |
| `evals/results/*.md` | **new** — dated result artifacts |
| `evals/README.md` | **new** — directory contract, control-arm rule, cost per sweep |
| `skills/sdd-guardrails/SKILL.md` | description 522 → ≤ 400 chars |
| `skills/sdd-orchestrate/SKILL.md` | description 490 → ≤ 400 chars (keeping its spec-021 clause) |
| `skills/event-driven-reviewer/SKILL.md` | description 418 → ≤ 400 chars (found by T001 — D007) |
| `skills/graphify/SKILL.md` | description de-arrowed; body 1.559 → ≤ 600 lines |
| `skills/graphify/references/*.md` | **new** — extracted per-command reference |
| `CONTRIBUTING.md` | eval-evidence gate for discipline/mindset skill changes |
| ≥1 mindset `SKILL.md` | rewritten per its measured result (which one is an outcome, not a choice) |

Explicitly untouched (FR-010): `profiles.json`, `hooks/`, `install*.{sh,ps1}`,
`settings.template*.json`, `agents/`, `.github/workflows/consistency.yml`.

## Proposed approach

**The lint rides the existing skills pass.** `check-consistency.sh` already builds `disk_skills`
and, in the SDD-contract rule, opens each `skills/<name>/SKILL.md` and reads its text. The new
class adds a frontmatter `description` extractor and three assertions over the same text, emitting
through the existing `err(category, item, message)` helper with category `skill-form` (lowercase,
matching `shipped-skill` / `planned-drift` / `hook-parity` — see D002). No new file I/O, no
measurable CI cost.

The workflow-summary detection is **three mechanical proxies only** — an arrow chain (`→`/`->`),
an enumerated step sequence (`1.` … `2.`), three-or-more `then`-chained clauses. It is not a
judgement engine and the plan does not pretend otherwise (D006); the judgement call stays a manual
review item.

**The harness is a shim, not a client.** `skill-eval.sh` shells out to a runner command from
`$SKILL_EVAL_RUNNER`, which takes a prompt on stdin and returns text on stdout. The repo vendors
no SDK, requires no API key of its own, and contains no network code — consistent with the
zero-dependency install and the never-call-the-network hook rule. The documented default is the
Claude Code CLI in headless mode (`claude -p --model <id>`), verified present on this machine at
2.1.220 with both flags. `codex` is not installed here, so the Codex path ships as documentation
only and is not claimed to work (D001).

**The mindset set is derived, not listed.** `CATEGORY_ENUM` already contains `mindset`, and each
skill declares its category in its `## SDD Contract`. Both the sweep and the CONTRIBUTING gate
resolve the set by parsing that field, so a tenth mindset skill is covered the day it lands (D003).

**graphify is split along its existing seams.** Lines 93–1505 are per-command sections
(`## For /graphify query`, `## For --update`, …) — each becomes
`skills/graphify/references/<command>.md`, linked from a table in `SKILL.md`. The contract,
usage, scope policy, honesty rules and lifecycle sections stay inline. The installer copies whole
skill directories, so the siblings ship without touching the installer (D004).

**Sequencing.** The lint lands before the fixes so the fixes are verified by the thing that will
police them. The harness lands before the scenarios so scenarios are written against a real
runner. The sweep runs last, because one of its outcomes — a rewrite — is itself a deliverable.

## Alternatives considered

**Direct API calls from the harness** (`curl` + `ANTHROPIC_API_KEY`). Rejected: adds a key
requirement and network code to a zero-dependency repo, and hard-binds the harness to one
provider in a project that ships a provider-adapter layer. The shim reaches the same models
through a CLI the maintainer already has.

**Prompt-generator only** — script emits the two arm prompts to files, a human runs them, the
script tallies. Rejected as the primary design: it makes a 90-call sweep unrunnable in practice.
Retained as the documented fallback when `$SKILL_EVAL_RUNNER` is unset, which is also what makes
the harness honest on a machine with no CLI installed.

**Gating CI on behavioural results.** Rejected in the SPEC's non-goals and unchanged here:
non-deterministic, token-costly, network-dependent. A flaky `main` would be a worse outcome than
no evals.

**A separate evals repository with a multi-turn tmux harness** (superpowers' model). Rejected for
scope: single-turn calls test *wording*, which is what the two documented failure modes are about.
The multi-turn gap is acknowledged, not papered over — scenarios that need it must say so (SPEC
edge case), and OQ-2 carries it forward.

**Hardcoding the 9 mindset skills.** Rejected: the contract field already encodes it, and spec 021
was widened mid-flight precisely because a hardcoded set left a gap.

## Dependencies

- `python3` — already required by `check-consistency.sh`.
- `bash` + `git` — already required.
- A model runner for the harness only: `claude` CLI (verified: 2.1.220, `-p/--print`, `--model`),
  or any command satisfying the stdin→stdout contract. **Not** required to run CI or the lint.
- Model access and token budget for the sweep: ~90 calls (9 skills × 2 arms × 5 reps).

## Risks

| Risk | Severity | Mitigation |
|---|---|---|
| **AC-006 depends on an empirical outcome.** If all 9 skills pass first time, no rewrite exists and the feature cannot close. | High | This is by design (the SPEC states a clean sweep means the harness measured nothing). The correct response is to strengthen the scenarios — more pressure, closer to the real failure — not to weaken the AC. Budget a second scenario round. |
| Eval non-determinism produces `INCONCLUSIVE` across most skills. | Medium | Variance is treated as a metric, not noise. Record and report; do not round up. If most come back inconclusive, that is a finding about scenario quality, and feeds OQ-2. |
| The lint's proxies miss real workflow summaries (false negatives certain). | Medium | Stated as a limitation in `evals/README.md` and D006; manual review retains the judgement call. The proxies bind the known outliers, which is the claim being made. |
| graphify extraction loses content. | Medium | Line-count accounting before/after, plus a link check that every extracted file is reachable from `SKILL.md`. Verified by reading, not by diff size. |
| Shortening two descriptions collides with spec 021's negative-trigger clauses. | Low | SPEC edge case: re-measure post-021 text first (T001); if a 021-justified clause cannot survive at 400, raise the threshold rather than delete the clause. |
| `evals/` counted as an orphan artifact by the checker. | Low | The checker's orphan classes cover `skills/`, `hooks/`, `specs/_templates/`, `docs/_templates/`, `agents/` only; `evals/` is outside all of them. Confirmed by T012's full run. |
| Sweep cost surprises the maintainer. | Low | Cost stated in `evals/README.md` and printed by the script before a multi-skill run. |

## Test strategy

- **Unit:** `check-consistency.test.sh` gains three mutation cases — over-long description,
  arrow-chained description, over-long body — each asserting exit 1 and a `skill-form` match,
  using the existing `fresh_copy` + `assert_case` helpers on a temp copy.
- **Integration:** full `bash scripts/check-consistency.sh` on the real tree, expecting exit 0 and
  zero `skill-form` findings after T004/T005; one real `skill-eval.sh` run against `verifier`.
- **E2E:** N/A — no runtime product.
- **Manual (load-bearing here):** every flagged match in every result file is read by hand — FR-006
  forbids accepting automated counts as the verdict; and the extracted graphify siblings are read
  to confirm nothing was lost.
- **Regression:** `check-consistency.sh`, `check-consistency.test.sh`, `graphify.test.sh` and
  `update.test.sh` all green, i.e. the four suites CI already runs.

## Rollback strategy

Three independent, individually revertible layers:

1. **Lint** — revert the `skill-form` block in `check-consistency.sh` and its three test cases.
   Nothing else depends on it.
2. **Harness** — delete `scripts/skill-eval.sh` and `evals/`. Nothing imports them; CI never
   invokes them; `profiles.json` never lists them, so no installed project is affected.
3. **Skill edits** — `git revert` the description shortenings, the graphify extraction, and the
   evidence-driven rewrite independently; each is a separate commit touching disjoint files.

No migration, no state, no deployed artifact. A user who already installed the framework is
unaffected until they run `scripts/update.sh`.

## PLAN verification checklist

- [x] The plan covers all acceptance criteria. (AC-001→T003/T009; AC-002→T001/T004/T005;
      AC-003→T006/T010; AC-004→T007; AC-005→T006/T010; AC-006→T011; AC-007→T008; AC-008→T009/T012)
- [x] The plan avoids behavior outside the spec. (FR-010 untouched-file list asserted in T012)
- [x] Risks are documented.
- [x] Test strategy is documented.
- [x] Rollback strategy is documented.
- [x] SPEC.md status has been updated to `Ready`.
