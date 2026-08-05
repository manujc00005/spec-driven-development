# Feature Spec: Skill evidence harness

## Status

Done

## Problem

This framework's product is behaviour-shaping prose: 61 skills, ~8.900 lines of `SKILL.md`,
plus 9 agent contracts. Every one of them asserts that reading it changes what a model does.
**None of that has ever been measured**, and nothing in the repository could detect it if a
skill were neutral or actively harmful.

Three concrete gaps:

1. **No behavioural evidence at all.** `scripts/check-consistency.sh` validates structure —
   that `profiles.json`, the on-disk artifacts, the hook wiring and the README counts agree.
   It says nothing about effect. A skill that is ignored, or one that makes output worse,
   passes CI identically to one that works.

2. **Two failure modes are documented empirically elsewhere and both apply here.** Both come
   from the superpowers project (`/Users/manu/Proyectos/example/superpowers`, analysed
   2026-07-28), which tests its skills against agent behaviour:
   - **A `description` that summarises the workflow gets followed *instead of* the skill
     body.** Their recorded case: a description saying "code review between tasks" produced
     one review, though the skill's own flowchart mandated two; removing the summary fixed
     it. Our longest descriptions do exactly this — `sdd-orchestrate` (492 chars) narrates
     its seven phases, `sdd-guardrails` (524 chars) enumerates its detections.
   - **Prohibition-form guidance applied to an output-*shaping* failure backfires.** In their
     head-to-head wording tests the prohibition arm produced clearly more of the unwanted
     content than the recipe arm, and trended worse than the **no-guidance control**. Our 9
     mindset skills (`communicator`, `decomposer`, `honest-advisor`, `root-causer`,
     `scope-keeper`, `scout`, `stopper`, `threat-modeler`, `verifier`) are written largely as
     anti-pattern lists — the exact form implicated — and several target shaping failures
     rather than discipline failures.

3. **Spec 021 already recorded this hole and deferred it.** Its OQ-2, raised at close: *"neither
   the negative-trigger clauses nor the section-11 rules are machine-validated:
   `check-consistency.sh` does not inspect skill descriptions or agent prose, so a new
   confusable skill without a clause … would pass CI unnoticed. Accepted for this feature and
   worth its own small spec."* This is that spec, widened from "validate the clause exists" to
   "validate the form, and measure the effect".

The practical consequence today is that every new behaviour-shaping change — spec 021's
negative triggers, spec 020's security-agent prose, every mindset skill — ships on the author's
judgement alone, and each one is a standing per-session context cost whether or not it works.

## Goal

- Give the repository a **cheap deterministic gate** on the skill-authoring failures that are
  statically detectable (description form and length, `SKILL.md` body size), wired into the
  existing consistency checker so it runs in CI.
- Give it an **on-demand behavioural harness** that measures a skill against a **no-guidance
  control**, so a skill's effect can be demonstrated rather than asserted.
- Prove the deterministic half end-to-end by fixing every form violation the repository actually
  has, and prove the behavioural half's *contract* with a stub-runner suite that needs no model.
- *(Narrowed 2026-07-29 — D011.)* Demonstrating **measured effect** — running the instrument
  against real models and rewriting a skill because the evidence said so — is **spec 023's** goal,
  not this one's. This feature ends with a working, tested, documented instrument and zero
  behavioural evidence, which is the honest state and is recorded as a risk in D011.

## Non-goals

- **No live sweep, and no evidence-driven skill rewrite** (narrowed 2026-07-29 — D011). This
  feature delivers the **instrument**: the static lint, the harness, its two test suites, the
  documented method and the contribution gate. *Running* it against real models to produce
  committed evidence, and rewriting a skill from that evidence, are spec 023. Two sweeps were run
  and both were discarded (D009, D010); a third cannot start until the scenario form is settled,
  and the instrument should not stay unclosed waiting on it.
- **Not all 61 skills.** The scenario corpus targets the 9 mindset skills. The ~40 stack/domain
  reviewer skills are reference-shaped, have weak incentive to be bypassed, and are deliberately
  out of scope.
- **No behavioural test in CI.** Model calls are non-deterministic, token-costly and
  network-dependent; gating `main` on them would make the build flaky and expensive. Only the
  static lint runs in CI; the harness is run by hand, and when it is run for real (spec 023) its
  results are committed as dated evidence. `scripts/skill-eval.test.sh` is deterministic and
  model-free but is **also** not in CI — `.github/` is out of scope by FR-010, so it stays a
  local gate listed in `CONTRIBUTING.md` until a follow-up wires it in.
- **No mass rewrite to a `Use when …` description convention.** All 61 descriptions currently
  use this repo's imperative style; superpowers' `Use when` prefix is a house convention with no
  evidence attached, unlike the no-workflow-summary rule, which has a recorded failure case. Only
  the latter is adopted.
- **No separate evals repository and no tmux/CLI-driving harness.** Superpowers offloads that to
  a second repo driving real terminal sessions with an LLM judge. Single-turn subagent calls are
  sufficient to test wording and are affordable; multi-turn evals are a later question (OQ-2).
- No new skills, no new agents, no skill renamed or deleted, no change to `profiles.json`,
  installers, settings templates or hook scripts.
- **No judgement-based check in CI.** "Does this description summarise the workflow?" is not
  reliably decidable by regex; the lint catches only mechanical proxies and the judgement call
  stays a manual review item (see D-candidates in Open questions).

## Users / Actors

- **The skill author** (maintainer or contributor) changing any discipline- or
  mindset-shaping skill — the consumer of both the lint and the harness.
- **CI** (`.github/workflows/consistency.yml`) — runs the static lint on every push to `main`
  and every PR.
- **The reviewer of a PR** touching skill prose — reads the committed eval results instead of
  taking the author's word. *This role only becomes real once spec 023 delivers a valid corpus;
  until then the contribution gate can be satisfied but the evidence it produces is not
  trustworthy — see T025.*
- Indirectly, every model that loads these skills at session start.

## Current behavior

- `scripts/check-consistency.sh` enforces FR-001..FR-012 of spec 007 (profiles/artifacts/hook
  wiring/README counts). It never opens a `SKILL.md` frontmatter `description`, and never
  measures a `SKILL.md` body.
- Description lengths range from 86 to 522 characters with no cap; **three** exceed 400 —
  `sdd-guardrails` (522), `sdd-orchestrate` (490) and `event-driven-reviewer` (418). *(Figures
  re-measured in T001 with a real frontmatter parser; the drafting estimates of "two, 524/492"
  came from a first-line `awk` that did not strip YAML quotes — D007.)*
- `SKILL.md` bodies range from 60 to **1.559 lines** (`graphify`), with no cap and no rule
  pushing heavy reference into sibling files — despite that pattern already existing in the repo
  (`docs/_templates/`, `adapters/codex/prompts/`).
- There is no eval harness, no scenario corpus, no control-arm concept, and no place where a
  skill's measured effect is recorded.
- `CONTRIBUTING.md` asks for consistency-checker output on a PR; it asks for nothing when the
  change is purely behaviour-shaping prose.

## Desired behavior

- `scripts/check-consistency.sh` gains a **skill-form** class of checks; drift in description
  length/shape or `SKILL.md` size fails CI with the same `[CATEGORY] item — message` output the
  checker already uses.
- `scripts/skill-eval.sh <skill> [--reps N]` runs a scenario from a committed corpus through two
  arms — **with** the skill and a **no-guidance control** — N times each, and writes a dated
  result file. A run where the control does not exhibit the failure is reported as
  **"nothing to fix"**, not as a pass.
- The scenario **format** is defined and documented in `evals/README.md`, including the
  self-contained rule D010 established, and the 9 mindset skills have format-conformant scenario
  files on disk — marked superseded, as spec 023's starting point rather than as evidence.
- The harness's contract — result-file shape, all three refusals, all five cascade verdicts, and
  leaving `skills/` untouched — is verified by `scripts/skill-eval.test.sh` against a stub runner,
  with no model call.
- *(Moved to spec 023 — D011.)* Committed baseline results for the 9 skills, and at least one
  skill rewritten because its measured result demanded it.
- `CONTRIBUTING.md` requires eval evidence for changes to discipline/mindset skill content.

## Functional requirements

- **FR-001:** `scripts/check-consistency.sh` gains a `[SKILL-FORM]` check class covering every
  `skills/*/SKILL.md`: (a) frontmatter `description` at most **400 characters**; (b) description
  free of mechanical workflow-summary markers — an arrow chain (`→`, `->`), an enumerated step
  sequence (`1.` … `2.`), or three or more clauses chained by `then`; (c) `SKILL.md` body at most
  **600 lines**. Violations are reported per skill and exit 1.
- **FR-002:** Every current violation is brought into compliance, and there are exactly **five**
  (re-measured 2026-07-28 against the post-021 tree in T001, correcting this requirement's
  original count of four — see D007): the **three** descriptions over 400 characters
  (`sdd-guardrails`, 522; `sdd-orchestrate`, 490; `event-driven-reviewer`, 418), the one
  description carrying an arrow chain (`graphify` — `… -> knowledge graph -> clustered
  communities -> …`), and the one body over 600 lines (`graphify`, 1.559 by `wc -l`).
  Descriptions are reduced to triggering conditions only, preserving every spec-021
  negative-trigger clause; `graphify`'s heavy reference is extracted to sibling files under
  `skills/graphify/` and linked, with no content lost. No other skill is edited by this
  requirement.
- **FR-003:** `scripts/skill-eval.sh SKILL [--reps N] [--out FILE]` exists and: runs the skill's
  committed scenario in a **control arm** (scenario only) and a **treatment arm** (scenario +
  the skill's full `SKILL.md`); defaults to **5 reps per arm**; writes every raw response and a
  per-arm tally to a single result file; never mutates any file under `skills/`.
- **FR-004:** *(Moved to spec 023 — D011.)* The scenario corpus's **format** is defined here and
  documented in `evals/README.md`: each `evals/scenarios/<skill>.md` states the failure being
  tested, the system-prompt context, the user message, the observable criterion, and the detection
  pattern. Producing a **valid** corpus for the 9 mindset skills is spec 023's requirement — the
  nine files on disk are format-conformant but substantively invalid (D010) and are 023's starting
  point, not this feature's deliverable.
- **FR-005:** The harness enforces the control-arm rule: if the control arm does not exhibit the
  failure in at least **2 of 5** reps, the result file is marked `NO-BASELINE-FAILURE` and the
  finding is that the skill has no demonstrated problem to solve — the treatment arm result must
  not be reported as success.
- **FR-006:** The harness writes results to `evals/results/<skill>-<YYYY-MM-DD>.md` containing the
  model identifier, rep count, both arms' tallies, and a one-line verdict, and refuses to run at
  all when no model identifier can be determined. Every flagged match is marked as manually read
  or not — automated counts alone are not accepted as the verdict. *(The file **contract** is this
  feature's requirement and is verified by `scripts/skill-eval.test.sh`. Committing real results
  from a live sweep moves to spec 023 — D011.)*
- **FR-007:** *(Moved to spec 023 — D011.)* Rewriting at least one mindset skill as a consequence
  of its measured result requires a valid sweep, which requires the scenario rewrite D010
  specifies. It cannot be satisfied by anything in this feature's scope.
- **FR-008:** `CONTRIBUTING.md` states that a PR changing the content of a discipline or mindset
  skill must include an `evals/results/` file produced after the change.
- **FR-009:** `.github/workflows/consistency.yml` runs the extended checker unchanged in
  invocation (the new class is inside `check-consistency.sh`); `scripts/check-consistency.test.sh`
  gains cases for the new `[SKILL-FORM]` class, matching the existing self-test pattern.
- **FR-010:** `profiles.json`, `hooks/`, `install*.{sh,ps1}`, `settings.template*.json` and
  `agents/` are untouched.

## Non-functional requirements

- **Performance:** the `[SKILL-FORM]` checks are pure file reads in the existing `python3` block —
  no measurable addition to CI runtime. The behavioural harness is never on the CI path.
- **Security:** the harness reads local files and calls whatever model runner the maintainer
  configures; it must not transmit repository contents anywhere else, and must not be wired into
  any hook (this framework's hooks never call the network — spec 021 assumption, preserved).
- **Observability:** every eval run produces a committed, dated artifact naming the model used.
  A result without a model identifier is not evidence.
- **Maintainability:** the scenario corpus and result files live outside `skills/`, so nothing in
  `evals/` is installed into a user's project or counted by `profiles.json`.
- **Honesty:** results are dated observations against one named model, not guarantees. The
  harness must not present a passing treatment arm as proof the skill "works" in production
  sessions, and the documentation must say so.
- **Cost:** each skill's default run is 10 model calls (2 arms × 5 reps). The full mindset sweep
  is ~90 calls; the spec must state this before anyone runs it in a loop.

## API / Interface changes

- New CLI: `scripts/skill-eval.sh SKILL [--reps N] [--out FILE]`.
- New directory contract: `evals/scenarios/<skill>.md`, `evals/results/<skill>-<date>.md`.
- Extended output vocabulary in `check-consistency.sh`: a `[SKILL-FORM]` category alongside the
  existing ones.

## Data model changes

None. Markdown and shell only.

## Edge cases

- **Control arm shows no failure.** The skill is solving a problem the model does not have.
  Reported as `NO-BASELINE-FAILURE` (FR-005), and the honest follow-up is retirement, not a
  rewrite — retirement itself stays out of scope here (Non-goals) and becomes a follow-up spec.
- **Non-deterministic split result** (e.g. control 3/5, treatment 2/5). Treated as *not binding*:
  variance is itself the metric — when guidance lands, reps converge. Such a result is recorded as
  `INCONCLUSIVE`, never rounded up to a pass. The implemented cascade resolves the neighbouring
  cases explicitly, in this order (T016/T018): treatment **above** control is `HARMFUL` — reported
  first, even with no baseline, because a skill making things worse is the most important thing
  the harness can surface; then a control below the 2-of-5 floor is `NO-BASELINE-FAILURE`; then
  treatment at zero is `EFFECTIVE`; then treatment **equal to** control is `INEFFECTIVE`; and only
  treatment strictly between zero and control is `INCONCLUSIVE`.
- **A skill whose failure only appears across multiple turns** (`stopper`, `communicator` may
  qualify). Single-turn scenarios cannot reach it; the scenario file must say so explicitly rather
  than substituting a weaker single-turn proxy and calling it covered.
- **`provider_specific: true` skills** (most mindset skills carry this flag). Results are valid
  only for the model actually named in the result file; the harness must not generalise across
  providers.
- **`graphify` extraction changes its shipped file set.** *Confirmed at planning (D004):*
  `install.sh:438` calls `copy_tree_safely` on the whole skill **directory**, and `profiles.json`
  lists skill names rather than files, so sibling files ride along with no installer change —
  satisfying FR-010. A future installer that enumerates files individually would break this.
- **A description legitimately needs more than 400 characters.** Spec 021 deliberately appended
  negative triggers to descriptions; the cap must be checked against the post-021 text before
  being fixed, and raised rather than forcing removal of a clause 021 justified.

## Acceptance criteria

- **AC-001:** `bash scripts/check-consistency.sh` reports `[SKILL-FORM]` violations for a
  deliberately over-long description, a deliberately arrow-chained description, and a
  deliberately over-long body, and exits 1 in each case. (FR-001)
- **AC-002:** On the real repository after FR-002, `bash scripts/check-consistency.sh` exits 0
  with no `[SKILL-FORM]` findings; `skills/graphify/SKILL.md` is at most 600 lines, its
  description carries no arrow chain, and every section removed from it is reachable from a
  linked sibling file. `git diff --name-only` under `skills/` lists exactly four skills —
  `sdd-guardrails`, `sdd-orchestrate`, `event-driven-reviewer` and `graphify` — and no others.
  Every spec-021 negative-trigger clause present before the change is still present after it.
  (FR-001, FR-002)
- **AC-003:** `bash scripts/skill-eval.test.sh` passes, demonstrating with a stub runner that the
  harness produces a result file carrying both arms, the requested reps, the model identifier and a
  verdict line; that it refuses to run without a model identifier, without a scenario, or with an
  output path resolving inside `skills/`; and that a run leaves `skills/` byte-identical.
  *(Restated by D011: the original wording required one live `claude -p` run, whose artifact was
  discarded as invalid. A stub suite verifies the same contract deterministically, in CI-able time,
  and without a model.)* (FR-003, FR-006)
- **AC-004:** *(Moved to spec 023 — D011.)* A valid scenario corpus for the 9 mindset skills. The
  format is defined and documented here; the corpus is 023's deliverable.
- **AC-005:** `scripts/skill-eval.test.sh` pins all five verdicts of the implemented cascade,
  including that a control arm below the 2-of-5 floor yields `NO-BASELINE-FAILURE` and that
  `HARMFUL` outranks it when treatment exceeds control. (FR-005)
- **AC-006:** *(Moved to spec 023 — D011.)* At least one mindset skill rewritten in response to a
  measured result, with before and after results committed. Unreachable here: it requires a valid
  sweep, which requires D010's scenario rewrite.
- **AC-007:** `CONTRIBUTING.md` contains the eval-evidence requirement for discipline/mindset
  skill changes. (FR-008)
- **AC-008:** `bash scripts/check-consistency.test.sh` passes and covers the new class; `git
  status --porcelain` shows no modification to `profiles.json`, `hooks/`, `install*.sh`,
  `install*.ps1`, `settings.template*.json`, or `agents/`. (FR-009, FR-010)

## Test scenarios

- **Unit:** `scripts/check-consistency.test.sh` cases for each `[SKILL-FORM]` rule, mutating a
  temp copy of the repo (the harness already supports an explicit `repo_root` argument).
- **Integration:** full `check-consistency.sh` run on the real tree (AC-002);
  `scripts/skill-eval.test.sh` driving the harness end-to-end against a stub runner (AC-003,
  AC-005).
- **E2E:** N/A — no runtime product.
- **Manual:** read the extracted `graphify` siblings to confirm no content was lost. *(Reading
  every flagged match in a result file remains the rule FR-006 states, but there are no live
  results to read in this feature's scope — that manual pass belongs to spec 023's sweep.)*

## Assumptions

- The frontmatter `description` is what a host uses for routing/auto-selection (carried over from
  spec 021), so its form has behavioural consequences worth gating.
- Single-turn subagent calls with a fresh context are a valid proxy for testing *wording*.
  Superpowers states this explicitly and equally explicitly says micro-tests do **not** replace
  multi-turn pressure scenarios for discipline skills — so this feature buys the cheaper half
  knowingly.
- The maintainer runs the harness manually and can afford ~90 model calls for a full mindset
  sweep.
- 400 characters and 600 lines are starting thresholds chosen to bind exactly the known outliers
  (2 descriptions, 1 body) without forcing unrelated churn; they are conventions, not findings,
  and PLAN may adjust them once the post-021 description lengths are re-measured.

## Open questions

- **OQ-1 — Resolved at planning (D001).** A pluggable runner shim: `skill-eval.sh` calls
  `$SKILL_EVAL_RUNNER` (stdin → stdout), defaulting to the Claude Code CLI headless
  (`claude -p --model <id>`, verified present at 2.1.220). No vendored SDK, no API key required by
  the repo, no network code in repository code. The Codex runner ships as documentation only and
  is explicitly not claimed to work — `codex` is not installed here and no one has run it.
- **OQ-2 — Deferred, transferred to spec 023 (D012).** Are multi-turn pressure scenarios
  (superpowers' `drill`-style harness) worth a later spec, given that `stopper` and `communicator`
  may not be reachable single-turn? Its trigger — how many skills come back `INCONCLUSIVE` — is
  produced by 023's sweep, so it cannot be answered here.
- **OQ-3 — Deferred, transferred to spec 023 (D012).** If a skill returns `NO-BASELINE-FAILURE`,
  retiring it changes `profiles.json` and the README counts. Should a follow-up "skill retirement"
  spec be opened pre-emptively, or only if a sweep actually produces one? Same reason: the trigger
  is a sweep result.
- **OQ-4 — Deferred, not transferred.** Should `agents/*.md` contracts be covered by the same lint
  and harness? Excluded here to keep scope bounded (FR-010); left for a future spec to pick up
  since it needs its own scoping, not spec 023's (023 is about the sweep, not the lint's reach).

## Contracted services

`specs/SERVICES.md` is absent → all billable add-ons treated as NOT contracted (conservative
default). This feature touches none.
