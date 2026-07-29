# Feature Spec: Skill evidence harness

## Status

In Progress

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
- Prove both by applying them to the 9 mindset skills and shipping at least one skill
  **rewritten because the evidence said so**, not because the author preferred it.

## Non-goals

- **Not all 61 skills.** The behavioural harness is applied to the 9 mindset skills in this
  feature. The ~40 stack/domain reviewer skills are reference-shaped, have weak incentive to be
  bypassed, and are deliberately out of scope.
- **No behavioural test in CI.** Model calls are non-deterministic, token-costly and
  network-dependent; gating `main` on them would make the build flaky and expensive. Only the
  static lint runs in CI; the harness is run by hand and its results are committed as dated
  evidence.
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
  taking the author's word.
- Indirectly, every model that loads these skills at session start.

## Current behavior

- `scripts/check-consistency.sh` enforces FR-001..FR-012 of spec 007 (profiles/artifacts/hook
  wiring/README counts). It never opens a `SKILL.md` frontmatter `description`, and never
  measures a `SKILL.md` body.
- Description lengths range from ~60 to 524 characters with no cap; `sdd-guardrails` (524) and
  `sdd-orchestrate` (492) both exceed 400.
- `SKILL.md` bodies range from ~100 to **1.559 lines** (`graphify`), with no cap and no rule
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
- Each of the 9 mindset skills has a committed scenario and a committed baseline result.
- At least one mindset skill is rewritten in this feature because its measured result demanded
  it, with the before/after evidence committed alongside.
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
- **FR-004:** A scenario corpus lives at `evals/scenarios/<skill>.md`, one file per skill,
  each containing: the failure being tested, the system-prompt context, the user message, and the
  observable criterion by which a response counts as exhibiting the failure. Scenarios exist for
  all **9** mindset skills.
- **FR-005:** The harness enforces the control-arm rule: if the control arm does not exhibit the
  failure in at least **2 of 5** reps, the result file is marked `NO-BASELINE-FAILURE` and the
  finding is that the skill has no demonstrated problem to solve — the treatment arm result must
  not be reported as success.
- **FR-006:** Results are committed at `evals/results/<skill>-<YYYY-MM-DD>.md` and include the
  model identifier, rep count, both arms' tallies, and a one-line verdict. Every flagged match is
  marked as manually read or not — automated counts alone are not accepted as the verdict.
- **FR-007:** At least one of the 9 mindset skills is **rewritten as a consequence of its result**
  (form changed, guidance removed, or skill retired), with the before result, the change, and the
  after result all committed.
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
- **Non-deterministic split result** (e.g. 3/5 vs 2/5). Treated as *not binding*: per
  superpowers' finding, variance is itself the metric — when guidance lands, reps converge.
  A split result is recorded as `INCONCLUSIVE`, never rounded up to a pass.
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
  linked sibling file. `git diff --name-only` under `skills/` lists only `sdd-guardrails`,
  `sdd-orchestrate`, `event-driven-reviewer` and `graphify` (plus the one skill rewritten by
  AC-006). Every spec-021 negative-trigger clause present before the change is still present
  after it. (FR-001, FR-002)
- **AC-003:** `bash scripts/skill-eval.sh verifier --reps 5` produces a result file containing
  both arms, 5 reps each, the model identifier, and a verdict line; `git status` shows no
  modification under `skills/`. (FR-003, FR-006)
- **AC-004:** `evals/scenarios/` contains one scenario for each of the 9 mindset skills, and each
  states its failure, its user message, and its observable criterion. (FR-004)
- **AC-005:** A scenario whose control arm passes fewer than 2 of 5 reps yields a result file
  marked `NO-BASELINE-FAILURE`, and the harness does not emit a success verdict for that skill.
  (FR-005)
- **AC-006:** At least one mindset skill has two committed result files — one before and one
  after a change to its content — showing the change was made in response to the first. (FR-007)
- **AC-007:** `CONTRIBUTING.md` contains the eval-evidence requirement for discipline/mindset
  skill changes. (FR-008)
- **AC-008:** `bash scripts/check-consistency.test.sh` passes and covers the new class; `git
  status --porcelain` shows no modification to `profiles.json`, `hooks/`, `install*.sh`,
  `install*.ps1`, `settings.template*.json`, or `agents/`. (FR-009, FR-010)

## Test scenarios

- **Unit:** `scripts/check-consistency.test.sh` cases for each `[SKILL-FORM]` rule, mutating a
  temp copy of the repo (the harness already supports an explicit `repo_root` argument).
- **Integration:** full `check-consistency.sh` run on the real tree (AC-002); one real
  `skill-eval.sh` run against `verifier` (AC-003).
- **E2E:** N/A — no runtime product.
- **Manual:** read every flagged match in each result file (FR-006 forbids accepting automated
  counts as the verdict); read the extracted `graphify` siblings to confirm no content was lost.

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
- **OQ-2:** Are multi-turn pressure scenarios (superpowers' `drill`-style harness) worth a later
  spec, given that `stopper` and `communicator` may not be reachable single-turn? Deferred by
  Non-goals; revisit after the first sweep shows how many skills come back `INCONCLUSIVE`.
- **OQ-3:** If a skill returns `NO-BASELINE-FAILURE`, retiring it changes `profiles.json` and the
  README counts — out of scope here. Should a follow-up "skill retirement" spec be opened
  pre-emptively, or only if the sweep actually produces one?
- **OQ-4:** Should `agents/*.md` contracts be covered by the same lint and harness? They are
  behaviour-shaping prose with the same properties, and spec 021's FR-004 already had to widen to
  all write-capable agents mid-flight. Excluded here to keep scope bounded (FR-010).

## Contracted services

`specs/SERVICES.md` is absent → all billable add-ons treated as NOT contracted (conservative
default). This feature touches none.
