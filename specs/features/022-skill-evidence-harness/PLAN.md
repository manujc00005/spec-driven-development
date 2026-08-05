# Implementation Plan: Skill evidence harness

> **Regenerated 2026-07-29** from the post-D013 `SPEC.md`, replacing a plan that had been
> spot-edited twice and still described the pre-D011 feature. `TASKS.md` and `DECISIONS.md` are
> **not** regenerated — they carry the executed task history and thirteen decisions, which are
> record, not restatement.

## Summary

Deliver the **instrument** for measuring whether this framework's behaviour-shaping skills change
what a model does — not the measurements themselves.

**A static `skill-form` check class** inside `scripts/check-consistency.sh`, riding the pass that
already iterates `disk_skills` for the `## SDD Contract` block: description ≤ 400 chars,
description free of mechanical workflow-summary markers, `SKILL.md` body ≤ 600 lines (`wc -l`
semantics). Runs in CI, fails the build like any other drift class.

**An on-demand harness** (`scripts/skill-eval.sh`) that runs a scenario through two arms —
treatment (scenario + full `SKILL.md`) and a mandatory no-guidance control — N times each, in an
empty sandbox, via a pluggable runner shim, and writes a dated result file naming the model.

**Both are then applied to the repository itself**: every form violation the tree actually has is
fixed, and the harness's whole contract is pinned by a stub-runner suite that needs no model.

Running the harness against real models to produce committed evidence, and rewriting a skill
because that evidence demanded it, are **spec 023** (D011).

## Related spec

`specs/features/022-skill-evidence-harness/SPEC.md`

## Impacted areas

| Area | Change |
|---|---|
| `scripts/check-consistency.sh` | new `skill-form` check class inside the existing `python3` block |
| `scripts/check-consistency.test.sh` | 6 skill-form cases: 3 mutations, a positive step-sequence case, a version-string negative, a clean-tree guard |
| `scripts/skill-eval.sh` | **new** — harness CLI, sandboxed runner, five-verdict cascade |
| `scripts/skill-eval.test.sh` | **new** — 20 assertions against a stub runner; local-only, not in CI (FR-010 bars `.github/`) |
| `evals/README.md` | **new** — method: what the checks prove, the mandatory control arm, the verdict cascade, the sandbox and its residual caveat, the self-contained scenario rule, cost |
| `evals/scenarios/*.md` | **new** — 9 format-conformant scenario files, marked superseded (D010) |
| `evals/scenarios/README.md` | **new** — marks the corpus superseded so no one sweeps against it |
| `skills/sdd-guardrails/SKILL.md` | description 522 → ≤ 400 |
| `skills/sdd-orchestrate/SKILL.md` | description 490 → 393, spec-021 negative-trigger clause preserved |
| `skills/event-driven-reviewer/SKILL.md` | description 418 → ≤ 400 (context economy, not a workflow summary — D008) |
| `skills/graphify/SKILL.md` | description de-arrowed; body 1.559 → 164 lines |
| `skills/graphify/references/*.md` | **new** — 8 files, 1.413 lines moved verbatim |
| `CONTRIBUTING.md` | eval-evidence gate, its not-yet-in-force caveat, and the local-only note for the harness suite |

Explicitly untouched (FR-010): `profiles.json`, `hooks/`, `install*.{sh,ps1}`,
`settings.template*.json`, `agents/`, `.github/workflows/consistency.yml`.

## Proposed approach

**The lint rides the existing skills pass.** No new file I/O: the SDD-contract rule already opens
every `skills/<name>/SKILL.md`. The new class adds a frontmatter parser — one that handles quoted,
folded and multi-line YAML, because a first-line `awk` misreads several shipped skills (T001) —
and three assertions, reported through the existing `err()` helper with category `skill-form`
(lowercase, matching house convention — D002).

**Two rules, two purposes, deliberately not merged (D008).** The length caps enforce *context
economy* and apply to every skill whatever its text is doing. The shape proxies target the
*workflow-summary* failure and are three mechanical shapes, not a judgement engine (D006). Neither
subsumes the other: `sdd-orchestrate`'s description was a textbook workflow summary that no proxy
detected, and `event-driven-reviewer` was over budget without being a summary at all.

**The harness is a shim, not a client.** `$SKILL_EVAL_RUNNER` takes a prompt on stdin and returns
text on stdout; the repo vendors no SDK, needs no API key, contains no network code (D001). It runs
in an empty sandbox, never the working tree — a runner inherits its cwd, and one that reads this
repo answers about *this repo* instead of the scenario (D009). Guards fail closed: the output path
is resolved before it is checked, and the resolver returns non-zero rather than exiting a subshell
(T019, T020).

**Verification is deterministic.** Every harness behaviour is pinned by a stub runner that counts
reps per arm, so all five cascade verdicts — including `INCONCLUSIVE` — are expressible without a
model call. This is what makes AC-003 and AC-005 checkable in CI-able time.

**Sequencing that was actually used.** The lint landed before the fixes, so the fixes were verified
by the thing that polices them (RED confirmed on exactly five violations, GREEN after). The harness
landed before its suite. Every code fix in review remediation was preceded by a failing test.

## Alternatives considered

*(Preserved from the original plan — all four still hold.)*

**Direct API calls from the harness** (`curl` + `ANTHROPIC_API_KEY`). Rejected: adds a key
requirement and network code to a zero-dependency repo, and hard-binds the harness to one provider
in a project that ships a provider-adapter layer.

**Prompt-generator only** — the script emits both arm prompts, a human runs them, the script
tallies. Rejected as the primary design (a 90-call sweep becomes unrunnable), retained as the
fallback when `$SKILL_EVAL_RUNNER` is unset, which is what keeps the harness honest on a machine
with no CLI.

**Gating CI on behavioural results.** Rejected: non-deterministic, token-costly, network-dependent.
A flaky `main` is worse than no evals.

**A separate evals repository with a multi-turn tmux harness.** Rejected for scope: single-turn
calls test *wording*, which is what the two documented failure modes are about. The multi-turn gap
is acknowledged, not papered over — carried to spec 023 as OQ-2.

**Hardcoding the 9 mindset skills.** Rejected: `category: mindset` in the SDD Contract already
encodes the set, and spec 021 was widened mid-flight precisely because a hardcoded list left a gap
(D003).

## Dependencies

- `python3` — already required by `check-consistency.sh`.
- `bash` + `git` — already required.
- **Nothing else.** The lint and both test suites run with no model, no network and no API key.
  A model runner is required only to *use* the harness for real, which is spec 023's dependency,
  not this plan's.

## Risks

| Risk | Severity | Mitigation |
|---|---|---|
| **022 closes having produced no behavioural evidence.** The feature's own premise — that skills should be measured, not asserted — stays unproven for this repo until 023 runs. | High | Accepted and recorded (D011). The instrument is independently useful; holding it unclosed behind an unsettled scenario form trades delivered value for tidiness. Stated in the SPEC's Goal rather than hidden behind a green checklist. |
| The shape proxies miss real workflow summaries. | Medium | Certain, and documented with two named false negatives (D006/T022). The length cap catches the case the proxies missed; the behavioural half exists for the rest. |
| `skill-eval.test.sh` is not in CI, so harness regressions land silently. | Medium | `.github/` is barred by FR-010. Listed in `CONTRIBUTING.md`'s merge gate as a local requirement, and disclosed there rather than assumed. Wiring it in is a follow-up. |
| The superseded scenario corpus is mistaken for usable. | Medium | `evals/scenarios/README.md` marks it, `evals/README.md` states the rule it violates, and the CONTRIBUTING gate carries a not-yet-in-force caveat (T025). |
| graphify extraction loses content. | Low → closed | Proven byte-identical by diffing the reassembled references against `git show HEAD:` — 1.413 lines, exact. All 8 files reachable from `SKILL.md`. |
| Threshold values (400/600) are conventions, not findings. | Low | Stated as such (D005), re-measured before being fixed (T001), and chosen to bind exactly the violations the tree had. |

## Test strategy

- **Unit:** `check-consistency.test.sh` — six `skill-form` cases on mutated temp copies, pinning
  detection in both directions (a real step sequence is caught; `1.2.3` is not).
- **Integration:** `check-consistency.sh` on the real tree, expecting exit 0 with zero
  `skill-form` findings; `skill-eval.test.sh` driving the harness end-to-end against a stub runner
  — result-file contract, three refusals, five verdicts, `skills/` byte-identical after a run.
- **E2E:** N/A — no runtime product.
- **Manual:** read the extracted `graphify` siblings to confirm nothing was lost, and read the
  rendered `CONTRIBUTING.md` gate. *(Reading flagged matches in live result files is the rule
  FR-006 states, but there are no live results in this scope — that pass belongs to spec 023.)*
- **Regression:** the four suites CI already runs — `check-consistency.sh`,
  `check-consistency.test.sh`, `graphify.test.sh`, `update.test.sh` — plus shellcheck `-S error`.

## Rollback strategy

*(Preserved from the original plan — still accurate.)* Three independent layers:

1. **Lint** — revert the `skill-form` block in `check-consistency.sh` and its six test cases.
   Nothing depends on it.
2. **Harness** — delete `scripts/skill-eval.sh`, `scripts/skill-eval.test.sh` and `evals/`.
   Nothing imports them, CI never invokes them, `profiles.json` never lists them, so no installed
   project is affected.
3. **Skill edits** — revert the three description shortenings, the graphify extraction, and the
   documentation changes independently; each touches disjoint files.

No migration, no state, no deployed artifact. A user who already installed the framework is
unaffected until they run `scripts/update.sh`.

## PLAN verification checklist

- [x] The plan covers all acceptance criteria. Map against the **eight live** criteria:
      AC-001→T003/T009/T015 · AC-002→T001/T004/T005/T012 · AC-003→T006/T014/T019/T020/T021 ·
      AC-005→T006/T014/T016/T021 · AC-007→T008/T025 · AC-008→T009/T012.
      **AC-004 and AC-006 are not mapped — they moved to spec 023 (D011).**
- [x] The plan avoids behavior outside the spec. FR-010's untouched-file list asserted in T012 and
      re-verified against baseline `06f15b3`.
- [x] Risks are documented, including the one that survives closure.
- [x] Test strategy is documented.
- [x] Rollback strategy is documented.
- [x] **Status handling:** `SPEC.md` is `In Progress` and this regeneration does **not** change it.
      The template's "updated to `Ready`" step applies to planning a `Draft` spec; this spec is
      already implemented, and `Ready` would be a demotion. Per `sdd-guardrails` section 11, only
      `/spec-review` may move it to `In Review`.
