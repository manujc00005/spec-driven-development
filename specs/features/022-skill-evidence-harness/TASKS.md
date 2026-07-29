# Tasks: Skill evidence harness

Every task states the files it may touch. `profiles.json`, `hooks/`, `install*.{sh,ps1}`,
`settings.template*.json`, `agents/` and `.github/workflows/consistency.yml` are out of bounds
for all of them (FR-010).

## Phase 1: Preparation

- [x] **T001** — Re-measure, against the current post-021 tree, every skill's `description` length
  and `SKILL.md` line count. Confirm the 400/600 thresholds bind exactly the known violations and
  nothing else. If a spec-021 negative-trigger clause cannot survive at 400, raise the threshold
  and record it in DECISIONS rather than deleting the clause.
  *Files: none (measurement only; DECISIONS.md if a threshold moves).* Covers: AC-002.
  **Done 2026-07-28:** five violations, not four — `event-driven-reviewer` (418) was uncounted in
  FR-002. Measured `sdd-guardrails` 522, `sdd-orchestrate` 490, `event-driven-reviewer` 418,
  `graphify` arrow chain, `graphify` 1.559 lines. **Thresholds unchanged** — the one over-cap
  description carrying a spec-021 clause (`sdd-orchestrate`) reaches ≤ 400 with the clause intact.
  See D007, D008.

- [ ] **T002** — Create the `evals/` layout: `evals/scenarios/`, `evals/results/`, and
  `evals/README.md` documenting the directory contract, the scenario file format (failure under
  test, system-prompt context, user message, observable criterion), the mandatory control arm and
  its 2-of-5 rule, the `NO-BASELINE-FAILURE` / `INCONCLUSIVE` verdicts, the runner shim contract,
  and the ~90-call cost of a full mindset sweep.
  *Files: `evals/README.md`, `evals/scenarios/.gitkeep`, `evals/results/.gitkeep`.*
  Covers: AC-004, AC-005.

## Phase 2: Implementation

- [ ] **T003** — Add the `skill-form` check class to `scripts/check-consistency.sh`, inside the
  existing `python3` block and reusing the `disk_skills` iteration that already reads each
  `SKILL.md` for the SDD-contract rule. Three assertions per skill: frontmatter `description`
  ≤ 400 chars; description free of arrow chains (`→`, `->`), enumerated step sequences
  (`1.` … `2.`) and three-or-more `then`-chained clauses; body ≤ 600 lines. Report via the
  existing `err()` helper with category `skill-form` (lowercase — D002); exit 1 on any violation.
  **State the line-counting convention explicitly** and use the same one in the tests: `wc -l`
  reports 1.559 for `graphify` where a `split("\n")` count reports 1.560, and at the 600 boundary
  that off-by-one decides a verdict (D007). Reuse the frontmatter parse approach validated in
  T001 — a first-line `awk` misreads quoted and multi-line YAML values.
  *Files: `scripts/check-consistency.sh`.* Covers: AC-001.

- [ ] **T004** — Bring the four description violations into compliance: shorten
  `sdd-guardrails` (522), `sdd-orchestrate` (490) and `event-driven-reviewer` (418) to ≤ 400
  chars, and remove the arrow chain from `graphify`'s description. Preserve every spec-021
  negative-trigger clause — `sdd-orchestrate`'s in particular, whose cut comes from its workflow
  summary (D007). Per D008, `event-driven-reviewer` is trimmed for **context economy**, not as a
  workflow summary — do not describe it as one. Verify with the T003 lint, not by eye.
  *Files: `skills/sdd-guardrails/SKILL.md`, `skills/sdd-orchestrate/SKILL.md`,
  `skills/event-driven-reviewer/SKILL.md`, `skills/graphify/SKILL.md` (frontmatter only).*
  Covers: AC-002.

- [ ] **T005** — Extract `graphify`'s per-command sections (`## For …`, currently lines ~93–1505)
  into `skills/graphify/references/<command>.md`, one file per command group, linked from a table
  in `SKILL.md`. Keep the SDD Contract, Usage, Input scope policy, What graphify is for, Honesty
  Rules, Configured Project Profiles, Ontology Lifecycle Patches and Lifecycle State sections
  inline. Body must end ≤ 600 lines with no content lost — account for it by line count before
  and after, and confirm every extracted file is reachable from `SKILL.md`.
  *Files: `skills/graphify/SKILL.md`, `skills/graphify/references/*.md`.* Covers: AC-002.

- [ ] **T006** — Write `scripts/skill-eval.sh SKILL [--reps N] [--out FILE]`. Resolves the skill's
  scenario from `evals/scenarios/<skill>.md`; runs a control arm (scenario only) and a treatment
  arm (scenario + full `SKILL.md`); default 5 reps per arm; invokes `$SKILL_EVAL_RUNNER`
  (stdin → stdout), and when unset prints the two arm prompts plus instructions instead of
  failing silently; writes every raw response, per-arm tallies, the model identifier, and a verdict
  line to one result file; emits `NO-BASELINE-FAILURE` when the control exhibits the failure in
  fewer than 2 of 5 reps, and `INCONCLUSIVE` on a split treatment result; prints the call count and
  cost estimate before running. Must never write anything under `skills/`.
  *Files: `scripts/skill-eval.sh`.* Covers: AC-003, AC-005.

- [ ] **T007** — Write one scenario per skill whose `## SDD Contract` declares
  `category: mindset` — resolved by parsing the contract, not from a hardcoded list (currently 9:
  `communicator`, `decomposer`, `honest-advisor`, `root-causer`, `scope-keeper`, `scout`,
  `stopper`, `threat-modeler`, `verifier`). Each states the failure under test, the
  system-prompt context, the user message, and the observable criterion. A scenario whose failure
  is only reachable across multiple turns must say so explicitly instead of substituting a weaker
  single-turn proxy.
  *Files: `evals/scenarios/*.md`.* Covers: AC-004.

- [ ] **T008** — Add the eval-evidence gate to `CONTRIBUTING.md`: a PR changing the content of a
  discipline or mindset skill must include an `evals/results/` file produced after the change.
  *Files: `CONTRIBUTING.md`.* Covers: AC-007.

## Phase 3: Tests

- [ ] **T009** — Add three mutation cases to `scripts/check-consistency.test.sh` using the existing
  `fresh_copy` + `assert_case` helpers: an over-long description, an arrow-chained description, and
  an over-long body — each asserting exit 1 and a `skill-form` match. Read thresholds dynamically
  where practical, per the suite's stale-hardcode note.
  *Files: `scripts/check-consistency.test.sh`.* Covers: AC-001, AC-008.

- [ ] **T010** — Run the sweep: every `category: mindset` skill, both arms, 5 reps. Read every
  flagged match by hand and mark it as manually read — automated counts are not the verdict.
  Commit each result to `evals/results/<skill>-<YYYY-MM-DD>.md`. Report how many came back
  `NO-BASELINE-FAILURE` and how many `INCONCLUSIVE`.
  *Files: `evals/results/*.md`.* Covers: AC-003, AC-005.

- [ ] **T011** — Rewrite at least one mindset skill in response to its T010 result — change its
  form, remove guidance, or record that it should be retired — then re-run its eval and commit the
  second result. Both results and the change must be traceable to each other. **If T010 produced no
  rewrite candidate, the scenarios were too weak: strengthen them and re-run rather than weakening
  this task.**
  *Files: one `skills/*/SKILL.md`, `evals/results/*.md`, `evals/scenarios/*.md` if strengthened.*
  Covers: AC-006.

## Phase 4: Review

- [ ] **T012** — Full verification: `bash scripts/check-consistency.sh` exits 0 with zero
  `skill-form` findings; `bash scripts/check-consistency.test.sh` passes; `graphify.test.sh` and
  `update.test.sh` pass; `git status --porcelain` shows no modification to `profiles.json`,
  `hooks/`, `install*.sh`, `install*.ps1`, `settings.template*.json` or `agents/`; and
  `git diff --name-only` under `skills/` lists only `sdd-guardrails`, `sdd-orchestrate`,
  `graphify` and the one skill rewritten in T011.
  *Files: none (verification only).* Covers: AC-002, AC-008.

- [ ] **T013** — Run `/spec-review`, then `/qa-review`, then the specialized reviews the diff
  triggers. Record residual risks and any deferred findings.
  *Files: none (review only).* Covers: all.
