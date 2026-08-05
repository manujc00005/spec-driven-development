# Tasks: Skill evidence harness

> **Scope narrowed 2026-07-29 (D011).** T007, T010 and T011 moved to spec 023: this feature
> delivers the instrument, not the evidence. `[>]` marks a moved task.

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

- [x] **T002** — Create the `evals/` layout: `evals/scenarios/`, `evals/results/`, and
  `evals/README.md` documenting the directory contract, the scenario file format (failure under
  test, system-prompt context, user message, observable criterion), the mandatory control arm and
  its 2-of-5 rule, the `NO-BASELINE-FAILURE` / `INCONCLUSIVE` verdicts, the runner shim contract,
  and the ~90-call cost of a full mindset sweep.
  *Files: `evals/README.md`, `evals/scenarios/.gitkeep`, `evals/results/.gitkeep`.*
  Covers: AC-004, AC-005.
  **Done 2026-07-28.** `evals/README.md`, `evals/scenarios/`, `evals/results/`.

## Phase 2: Implementation

- [x] **T003** — Add the `skill-form` check class to `scripts/check-consistency.sh`, inside the
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
  **Done 2026-07-28.** Verified RED first: the new class flagged exactly the five T001 violations, then GREEN after T004/T005. `wc -l` convention stated in the code.

- [x] **T004** — Bring the four description violations into compliance: shorten
  `sdd-guardrails` (522), `sdd-orchestrate` (490) and `event-driven-reviewer` (418) to ≤ 400
  chars, and remove the arrow chain from `graphify`'s description. Preserve every spec-021
  negative-trigger clause — `sdd-orchestrate`'s in particular, whose cut comes from its workflow
  summary (D007). Per D008, `event-driven-reviewer` is trimmed for **context economy**, not as a
  workflow summary — do not describe it as one. Verify with the T003 lint, not by eye.
  *Files: `skills/sdd-guardrails/SKILL.md`, `skills/sdd-orchestrate/SKILL.md`,
  `skills/event-driven-reviewer/SKILL.md`, `skills/graphify/SKILL.md` (frontmatter only).*
  Covers: AC-002.
  **Done 2026-07-28.** `sdd-guardrails` 522→<400, `sdd-orchestrate` 490→393 (spec-021 clause intact), `event-driven-reviewer` 418→<400, `graphify` de-arrowed.

- [x] **T005** — Extract `graphify`'s per-command sections (`## For …`, currently lines ~93–1505)
  into `skills/graphify/references/<command>.md`, one file per command group, linked from a table
  in `SKILL.md`. Keep the SDD Contract, Usage, Input scope policy, What graphify is for, Honesty
  Rules, Configured Project Profiles, Ontology Lifecycle Patches and Lifecycle State sections
  inline. Body must end ≤ 600 lines with no content lost — account for it by line count before
  and after, and confirm every extracted file is reachable from `SKILL.md`.
  *Files: `skills/graphify/SKILL.md`, `skills/graphify/references/*.md`.* Covers: AC-002.
  **Done 2026-07-28.** 1.559→164 lines; 1.413 lines moved to 8 files under `references/`. Content preservation proven by diff against `git show HEAD:` — byte-identical. All 8 linked.

- [x] **T006** — Write `scripts/skill-eval.sh SKILL [--reps N] [--out FILE]`. Resolves the skill's
  scenario from `evals/scenarios/<skill>.md`; runs a control arm (scenario only) and a treatment
  arm (scenario + full `SKILL.md`); default 5 reps per arm; invokes `$SKILL_EVAL_RUNNER`
  (stdin → stdout), and when unset prints the two arm prompts plus instructions instead of
  failing silently; writes every raw response, per-arm tallies, the model identifier, and a verdict
  line to one result file; emits `NO-BASELINE-FAILURE` when the control exhibits the failure in
  fewer than 2 of 5 reps, and `INCONCLUSIVE` on a split treatment result; prints the call count and
  cost estimate before running. Must never write anything under `skills/`.
  *Files: `scripts/skill-eval.sh`.* Covers: AC-003, AC-005.
  **Done 2026-07-28, amended 2026-07-29 (D009).** shellcheck-clean; runner now executes in an empty sandbox.

- [>] **T007 — MOVED to spec 023 (D011)** — Write one scenario per skill whose `## SDD Contract` declares
  `category: mindset` — resolved by parsing the contract, not from a hardcoded list (currently 9:
  `communicator`, `decomposer`, `honest-advisor`, `root-causer`, `scope-keeper`, `scout`,
  `stopper`, `threat-modeler`, `verifier`). Each states the failure under test, the
  system-prompt context, the user message, and the observable criterion. A scenario whose failure
  is only reachable across multiple turns must say so explicitly instead of substituting a weaker
  single-turn proxy.
  *Files: `evals/scenarios/*.md`.* Covers: AC-004.
  **Written 2026-07-28, SUPERSEDED 2026-07-29 by D010.** All 9 scenarios exist, but they describe
  repo state the model cannot see, so an agent runner answers about the mismatch instead of the
  scenario. They need rewriting as self-contained prompts before T010 can produce evidence.

- [x] **T008** — Add the eval-evidence gate to `CONTRIBUTING.md`: a PR changing the content of a
  discipline or mindset skill must include an `evals/results/` file produced after the change.
  *Files: `CONTRIBUTING.md`.* Covers: AC-007.
  **Done 2026-07-28.** Gate added under 'The merge gate'.

## Phase 3: Tests

- [x] **T009** — Add three mutation cases to `scripts/check-consistency.test.sh` using the existing
  `fresh_copy` + `assert_case` helpers: an over-long description, an arrow-chained description, and
  an over-long body — each asserting exit 1 and a `skill-form` match. Read thresholds dynamically
  where practical, per the suite's stale-hardcode note.
  *Files: `scripts/check-consistency.test.sh`.* Covers: AC-001, AC-008.
  **Done 2026-07-28; extended by T015 on 2026-07-29.** 6 cases: three mutations, a positive
  step-sequence case, a version-string negative case, and a clean-tree guard; suite 30/30.

- [>] **T010 — MOVED to spec 023 (D011)** — Run the sweep: every `category: mindset` skill, both arms, 5 reps. Read every
  flagged match by hand and mark it as manually read — automated counts are not the verdict.
  Commit each result to `evals/results/<skill>-<YYYY-MM-DD>.md`. Report how many came back
  `NO-BASELINE-FAILURE` and how many `INCONCLUSIVE`.
  *Files: `evals/results/*.md`.* Covers: AC-003, AC-005.
  **Two sweeps run (~170 calls), both invalidated.** Sweep 1 was never committed; three of
  sweep 2's results were committed in `1e9dab9` and deleted afterwards (D010, corrected by T019).
  Sweep 1: runner
  inherited the repo (D009). Sweep 2: scenarios reference unreachable files (D010). Every
  manually-read 'hit' in both sweeps was an artifact. Blocked until the scenario form is settled.

- [>] **T011 — MOVED to spec 023 (D011)** — Rewrite at least one mindset skill in response to its T010 result — change its
  form, remove guidance, or record that it should be retired — then re-run its eval and commit the
  second result. Both results and the change must be traceable to each other. **If T010 produced no
  rewrite candidate, the scenarios were too weak: strengthen them and re-run rather than weakening
  this task.**
  *Files: one `skills/*/SKILL.md`, `evals/results/*.md`, `evals/scenarios/*.md` if strengthened.*
  Covers: AC-006.

- [x] **T025** — Fix the live contradiction the D013 sweep found in shipped documentation:
  `CONTRIBUTING.md` requires a PR changing a mindset skill to attach an `evals/results/` file, but
  every scenario is marked superseded (D010/D011), so a contributor complying today produces
  evidence that is not trustworthy. State in the gate that it takes full effect when spec 023
  lands a valid corpus, and that until then a result file must use a scenario meeting the
  self-contained rule in `evals/README.md`.
  *Files: `CONTRIBUTING.md`.* Covers: AC-007 (wording only — the gate itself already exists).
  **Done 2026-07-29.** The gate now states it is not fully in force until spec 023 lands a
  valid corpus, and requires any result attached today to come from a self-contained
  scenario — with an explicit instruction to say so in the PR rather than attach a
  non-evidence result. **No test seam:** prose in a documentation file; recorded in D013
  rather than skipped silently.

## Phase 4: Review

- [x] **T012** — Full verification: `bash scripts/check-consistency.sh` exits 0 with zero
  `skill-form` findings; `bash scripts/check-consistency.test.sh` passes; `graphify.test.sh` and
  `update.test.sh` pass; `git status --porcelain` shows no modification to `profiles.json`,
  `hooks/`, `install*.sh`, `install*.ps1`, `settings.template*.json` or `agents/`; and
  `git diff --name-only` under `skills/` lists only `sdd-guardrails`, `sdd-orchestrate`,
  `graphify` and the one skill rewritten in T011.
  *Files: none (verification only).* Covers: AC-002, AC-008.
  **Done 2026-07-29 (D012).** Unblocked by D011: with T011 moved to spec 023, the expected `skills/` diff is exactly the
  four skills T004/T005 touched — no rewritten skill is pending. Verified 2026-07-29: consistency
  0 findings; self-test 30/30; harness 20/20; graphify 66/0; update 7/0; shellcheck clean;
  FR-010 forbidden paths untouched.

- [x] **T013** — Run `/spec-review`, then `/qa-review`, then the specialized reviews the diff
  triggers. Record residual risks and any deferred findings.
  *Files: none (review only).* Covers: all.
  **Done 2026-07-29.** `/spec-review` → **Pass** on the eight live ACs, all verified by
  command against baseline `06f15b3`; status promoted to `In Review`. `/qa-review` → every
  shipped script has a suite; every SPEC edge case is pinned by a named test; no diff
  outside the declared surface; rollback intact across three independent layers.
  Specialized reviews: none triggered — the diff touches no API, schema, auth, UI or
  money-movement code (bash + markdown only).

## Phase 5: Review remediation
Raised by `/spec-review` on 2026-07-29. All six are unblocked — none depends on D010.

- [x] **T014** — Add `scripts/skill-eval.test.sh`: a stub-runner suite for the harness, following
  `check-consistency.test.sh`'s `fresh_copy` + temp-repo pattern. Cover the unset-runner path, the
  missing-model refusal, the missing-scenario refusal, the refusal to write under `skills/`, and
  the three verdicts reachable without a live model (`NO-BASELINE-FAILURE`, `HARMFUL`,
  `EFFECTIVE`). The harness is 230 lines in `scripts/` with no coverage while every sibling script
  has a suite.
  *Files: `scripts/skill-eval.test.sh`.* Covers: AC-003, AC-005.
  **Done 2026-07-29.** `scripts/skill-eval.test.sh`, 18 assertions, shellcheck clean. Two bugs in the test harness itself were found and fixed first (`local a="$1" b="$a"` expands before assigning; `env` needs `-u` before assignments).

- [x] **T015** — Fix the step-sequence proxy's confirmed false positive: `\b1\..*\b2\.` matches
  `see 1.2.3 for details`, so a description mentioning a semantic version is reported as a workflow
  summary. Require whitespace after the digit-dot. Add a case pinning `1.2.3` as clean **before**
  changing the regex. A false positive blocks CI, which is worse than the false negatives D006
  already accepts.
  *Files: `scripts/check-consistency.sh`, `scripts/check-consistency.test.sh`.* Covers: AC-001.
  **Done 2026-07-29.** RED confirmed (`1.2.3` was flagged), narrowed to `\b1\.\s.*\b2\.\s`, GREEN. Added a positive step-sequence case too — the narrowing had no coverage in the detecting direction.

- [x] **T016** — Reorder the verdict cascade so `HARMFUL` is evaluated before
  `NO-BASELINE-FAILURE`, or make the latter carry the treatment-vs-control delta. `verifier`'s
  control 0/5 against treatment 3/5 was reported only as a missing baseline — the treatment arm
  looking worse is the signal this feature exists to surface.
  *Files: `scripts/skill-eval.sh`.* Covers: AC-005.
  **Done 2026-07-29.** `HARMFUL` now outranks `NO-BASELINE-FAILURE`, and carries the missing-baseline caveat in its note. Pinned by `harmful-outranks-no-baseline`.

- [x] **T017** — Remove the dead `$WORK/$arm.hits` write (`skill-eval.sh:147`, never read) and
  grep each response once per rep instead of twice, so the printed status and the tally cannot
  diverge.
  *Files: `scripts/skill-eval.sh`.* Covers: AC-003.
  **Done 2026-07-29.** Dead `.hits` write removed; one grep per rep.

- [x] **T018** — Align FR-005's `INCONCLUSIVE` wording with the implemented cascade. FR-005 says
  "a split treatment result"; the code emits it only when treatment falls strictly between zero and
  control, reporting an equal split as `INEFFECTIVE`.
  *Files: `SPEC.md`.* Covers: AC-005.
  **Done 2026-07-29.** Corrected in SPEC *Edge cases*, not FR-005 — the review misattributed the location. Full cascade order now written out.

- [x] **T019** — Harden the `--out` guard: the current `case "$OUT" in "$REPO_ROOT"/skills/*)`
  is a string-prefix test, so a relative path such as `../skills/foo.md` slips past FR-003's
  "never mutates a skill". Resolve the path before comparing. Also correct D010's consequence
  line, which claims the invalid results were "deleted, not committed" — they were committed in
  `1e9dab9` and removed afterwards.
  *Files: `scripts/skill-eval.sh`, `DECISIONS.md`.* Covers: AC-003.

  **Done 2026-07-29.** RED reproduced live: `--out evals/../skills/pwned.md` wrote inside `skills/`. Now resolved via nearest-existing-ancestor + `pwd -P` before guarding. D010's consequence line corrected.

- [x] **T020** — Make `resolve_path` fail **closed**. It is called as
  `OUT="$(resolve_path "$OUT")"`, so its `die` exits the command substitution's subshell, not the
  script; with `set -uo pipefail` (no `-e`) execution would continue with `OUT` empty. The `-d`
  arm is currently unreachable — the dirname chain always ends at `/` or `.` — so replace it with
  the reachable failure it should have been testing: `cd "$dir" && pwd -P` failing on a directory
  that cannot be entered. Return non-zero and check the status at the call site.
  *Files: `scripts/skill-eval.sh`.* Covers: AC-003.
  **Done 2026-07-29.** RED was worse than predicted: the script exited **0** while writing nowhere (`OUT` resolved to `/sub/r.md`). Now returns non-zero and the call site stops. Pinned by `unresolvable output directory fails closed` (skipped as root).

- [x] **T021** — Close three gaps in `skill-eval.test.sh`: (a) `no-skill-mutation` checksums
  `skills/` around a run whose output goes to `evals/results/` by default, so it would pass with
  no guard at all — point its `--out` at `skills/` and assert both the refusal and the unchanged
  checksums; (b) `unknown skill is refused` runs against the live repo instead of a `fresh_copy`,
  breaking the isolation invariant every other case holds; (c) no case pins `INCONCLUSIVE`, the
  verdict the SPEC discusses most — the stub answers per arm, so it must be extended to vary per
  rep before treatment-strictly-between-zero-and-control can be expressed.
  *Files: `scripts/skill-eval.test.sh`.* Covers: AC-003, AC-005.
  **Done 2026-07-29.** Stub rewritten to count reps per arm, so all five verdicts are pinnable; `INCONCLUSIVE` (control 5, treatment 2) now covered. `no-skill-mutation` runs with `--out` aimed at a real `SKILL.md`; `unknown skill` moved onto a `fresh_copy`. Suite 20/20.

- [x] **T022** — Record the false negative the T015 narrowing introduced: `step 1. foo step 2.`,
  a sequence whose last marker ends the string, is no longer detected. Defensible under D006's
  stated tolerance, but currently undocumented — add it to D006's consequences so the tolerance is
  recorded rather than rediscovered.
  *Files: `DECISIONS.md`.* Covers: AC-001.
  **Done 2026-07-29.** D006 now carries a 'Known false negatives' list covering both the prose-shaped summary and the trailing `step 2.` case, with the positive/negative trade stated.

- [x] **T023** — Update `evals/README.md` for three behaviour changes it never tracked: the
  verdict **cascade order** (HARMFUL first, and why) after T016; the **sandbox** and its residual
  user-config caveat, making D009's claim that this is "stated in evals/README.md" true rather
  than false; and D010's **self-contained scenario rule**, which until now lived only in a decision
  record and so reached no scenario author. Also documents the `Detection pattern` field, which
  the harness has always required but the format section never listed.
  *Files: `evals/README.md`, `DECISIONS.md`.* Covers: none new — corrects false documentation.
  **Done 2026-07-29.** D009's consequence now notes it was only made true in T023.

- [x] **T024** — Restore permissions in the test's cleanup path so an abort between `chmod 000`
  and `chmod 755` cannot leave a tree `rm -rf` refuses to descend into.
  *Files: `scripts/skill-eval.test.sh`.* Covers: none new.
  **Done 2026-07-29.** Handled in the `EXIT` trap rather than inline, so it covers any future case.
