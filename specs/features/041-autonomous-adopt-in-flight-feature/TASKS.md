# Tasks: autonomous-adopt-in-flight-feature

<!-- Verify clauses follow specs/_templates/TASKS.md: an executable command, or a human check that
     names who checks and against what. Nothing executes these; they are the criterion a human or
     an agent acts on to call the task done. A task closed without being performed keeps the tick
     and states DEFERRED/SKIPPED/RESOLVED on the line below, per the template. -->

## Phase 1: Preparation

- [x] T001 - Build the adoption fixture: a scratch-repo builder (in `runner/tests/support.py` or a
  new module under `runner/tests/fixtures/`) that creates a git repo with a default branch resolvable
  through `origin/HEAD`, a feature branch, a feature folder whose `SPEC.md` is `In Progress`, a
  `TASKS.md` with two checked tasks (with `Verify:` clauses) and two unchecked ones, the checked
  tasks' diff committed on the feature branch with one seeded, reviewable defect, and a clean tree.
  Add a shape test for it. Covers: AC-001, AC-005, AC-009.
  Verify: `PYTHONPATH=runner python3 -m unittest discover -s runner/tests -t runner` exits 0 and
  its output lists the new fixture shape test (`git log --oneline` inside the fixture shows the
  baseline commit on a non-default branch; `grep -c '^- \[x\]' TASKS.md` in it prints 2).

## Phase 2: Implementation — skill protocol

- [x] T002 - In `skills/sdd-orchestrate/SKILL.md`, add `--adopt` to the ARGUMENTS block and to the
  flag-validation paragraph: accepted only with `--autonomous`, rejected when duplicated, rejected
  before any feature-state read/write, refused as *Already adopted or entered* when a valid
  `ORCHESTRATION.md` for the feature exists, and refused on any re-entry. Covers: AC-002, AC-007.
  Verify: `grep -c -- '--adopt' skills/sdd-orchestrate/SKILL.md` is at least 4, the ARGUMENTS
  fence shows the flag, the validation paragraph names all four rejections, and
  `bash scripts/check-consistency.sh` exits 0.

- [x] T003 - In the *Autonomous mode — entry gate* section, define the adoption gate: condition 1
  under `--adopt` requires exactly `In Progress` and names the owning action for every other status
  (`Ready` → *Adoption not needed*); condition 5 under `--adopt` requires an empty
  `git status --porcelain` with the commit command as remediation and stash listed only for
  exclusion; new condition 7 *Inherited record is computable* (baseline commit = `HEAD`, merge-base
  with the default branch resolved from git metadata, checked-task set) refusing as *Inherited diff
  undetermined*; and the remediation order "branch first, commit second" when conditions 4 and 5
  fail together. Covers: AC-002, AC-003, AC-004.
  Verify: each of the strings `Adoption not needed`, `Already adopted or entered`, `Inherited diff
  undetermined` occurs in `skills/sdd-orchestrate/SKILL.md`; the gate section states that under
  `--adopt` the porcelain output must be empty; a reader following the section with the T001 fixture
  on `main` plus one uncommitted file obtains two refusals in the order branch, then tree.

- [x] T004 - Extend the *durable state contract* scaffold and rules: header lines `Entry`,
  `Adopted at`, `Adoption baseline commit`, `Adoption diff base (against <default-branch>)`; the
  `## Inherited` table (`Task | Checked before adoption | Verify clause | Verification observed by
  this run`) with one row per task checked at adoption, all `no`; `Entry: ready` written by `Ready`
  entries and a missing `Entry` line read as `ready` on re-entry; the budget note "unchecked tasks at
  adoption"; the adoption baseline commit named as the run's trusted baseline for the existing
  recovery rule. Covers: AC-001, AC-007.
  Verify: the scaffold fence in `skills/sdd-orchestrate/SKILL.md` contains the four header lines and
  the `## Inherited` table header verbatim, and the re-entry paragraph contains the sentence that a
  missing `Entry` line is read as `ready`.

  **[VERIFY AMENDED 2026-09-02 — D008]** The scaffold fence now lives in
  `skills/sdd-orchestrate/templates/ORCHESTRATION.md` (the 600-line skill cap refused the inline
  version). The clause is checked there for the four header lines and the `## Inherited` header;
  the re-entry sentence is still checked in `SKILL.md`, which also carries the pointer to the
  template.

- [x] T005 - Extend the *implement/review/fix circuit* and *termination* sections: before the first
  implementation delegation of an adopted run, compute the fingerprint and run `domain-reviewer`
  (plus `security-reviewer` under the existing Level-3 triggers) on `diff-base..baseline`, counting
  both against the budget, parsing verdicts through the existing rules; while an inherited-diff
  finding of severity `Critical` is open, no new spec task is delegated; an empty inherited diff skips
  the review; the `final-conformance-reviewer` brief includes the `Inherited` table and its report
  labels unobserved `Verify:` clauses as *inherited, verification not observed*. Covers: AC-005,
  AC-006, AC-008, AC-012.
  Verify: the circuit section contains a step, numbered before the existing step 1, that names
  `diff-base..baseline` and the `Critical` rule; the termination section names the `Inherited` table
  in the final-conformance brief; the existing every-exit assertion paragraph is unchanged
  (`git diff main -- skills/sdd-orchestrate/SKILL.md` shows no deletion inside it).

## Phase 2: Implementation — manual chain, docs, adapter

- [x] T006 - Add the adoption hand-off line to `skills/spec-implement/SKILL.md` (*Recommended next
  command*, when unchecked tasks remain), to step 4 of both workflows in `skills/sdd/SKILL.md`, and
  to the closing recommendation of `adapters/codex/prompts/sdd-spec-implement.md`; each line states
  the commit-on-a-feature-branch precondition. Covers: AC-010, AC-013.
  Verify: `grep -l -- '--adopt' skills/spec-implement/SKILL.md skills/sdd/SKILL.md
  adapters/codex/prompts/sdd-spec-implement.md` lists all three files, and
  `git diff --numstat main -- <those three files>` shows 0 deletions for each.

- [x] T007 - Document the entry: `docs/SDD-ORCHESTRATION.md` *Autonomous mode* gains the `--adopt`
  invocation, the three new refusal conditions, the remediation order and the inherited-diff review;
  its runner flag table and exit-code 10 line list adoption. `adapters/codex/PARITY.md` *Autonomous
  orchestration — sequential degradation* gains the adoption gate, inherited record and
  inherited-diff review under the same sequential contract, keeping the "documented, not closure
  evidence until the smoke run passes" stance. Covers: AC-013.
  Verify: `grep -c -- '--adopt' docs/SDD-ORCHESTRATION.md` is at least 3 and
  `grep -c -i 'inherited' adapters/codex/PARITY.md` is at least 2; the PARITY section names all
  three of: adoption gate, inherited record, inherited-diff review.

## Phase 2: Implementation — runner parity

- [x] T008 - `runner/sdd_runner/gate.py`: add `adopt=False` to `check(...)`; without adopt, first
  entry accepts `Ready` only; with adopt, `In Progress` only, refusing `Ready` as *Adoption not
  needed*; remove `In Review` from first-entry acceptance; refuse any dirty path in both modes
  (drop the inside-feature-folder tolerance); under adopt compute the inherited record (baseline
  sha, merge-base against the resolved default branch, checked-task ids) and refuse as *Inherited
  diff undetermined* when the merge-base cannot be resolved; refuse adopt when a state file already
  exists as *Already adopted or entered*. Mirror the skill's condition names in `Refusal.condition`.
  Covers: AC-009.
  Verify: `grep -n 'READY_STATUSES' runner/sdd_runner/gate.py` shows a tuple without
  `"In Review"`, and the T010 suite passes.

- [x] T009 - `runner/sdd_runner/__main__.py`: add `--adopt` (store_true), pass it to the gate, and
  make `--dry-run` print the inherited record (one line per inherited task plus baseline and diff
  base). Update the flag table and the exit-code 10 description in `runner/README.md`.
  Covers: AC-009, AC-013.
  Verify: on the T001 fixture, `PYTHONPATH=runner python3 -m sdd_runner --feature <fixture>
  --repo <fixture-repo> --dry-run --adopt` exits 0 and prints two inherited rows and
  `max delegations: 25`; the same command without `--adopt` exits 10 and prints `lifecycle status`;
  `grep -- '--adopt' runner/README.md` matches.

  **[OBSERVED 2026-09-02]** The label printed is the pre-existing `max-delegations: 25`, not
  `max delegations: 25` as the clause spelled it; the value and the two inherited rows matched.

## Phase 3: Tests

- [x] T010 - Extend `runner/tests/unit/test_gate.py` with the status × adopt matrix (`Ready`,
  `In Progress`, `In Review`, `Draft`, `Done` in both modes), dirty path inside the feature folder
  refusing in both modes, missing `origin/HEAD` under adopt refusing as *Inherited diff
  undetermined*, existing state file under adopt refusing, and the inherited record shape; add a
  state/resume test that a header without an `Entry` line authenticates as `ready`. Rewrite
  `test_unattributed_dirty_tree` explicitly for the new rule. Covers: AC-009.
  Verify: `PYTHONPATH=runner python3 -m unittest discover -s runner/tests -t runner` exits 0 and
  reports more than 239 tests.

- [x] T011 - Containment check after all edits. Covers: AC-011.
  Verify: `bash scripts/check-consistency.sh` exits 0 and `git diff --name-only main -- install.sh
  install.ps1 install-all.sh install-all.ps1 profiles.json settings.template.json
  settings.template.sh.json` prints nothing.

## Phase 4: Calibration and review

- [x] T012 - Claude Code calibration run over the T001 fixture, recorded in this feature's
  `CALIBRATION.md` with the command and an output excerpt per criterion: refusal matrix (`In
  Progress` without `--adopt`; `Ready` with `--adopt`; existing state file with `--adopt`; one
  uncommitted path; default branch plus uncommitted path, checking order), happy path (state header
  and `Inherited` rows; `domain-reviewer` first in the delegation log; the seeded defect becomes a
  `(from <finding-id>)` task and blocks new spec tasks until APPROVE; run ends `DONE` with
  `PR_DESCRIPTION.md`), all-checked entry ending in final conformance without implementation
  delegations, re-entry with and without `--adopt`, final-conformance report labeling inherited
  tasks, and the every-exit no-commit/no-push/no-status-write assertion. Covers: AC-001, AC-002,
  AC-003, AC-004, AC-005, AC-006, AC-007, AC-008, AC-012, AC-014.
  Verify: `CALIBRATION.md` has one row per listed criterion with a command and an output excerpt,
  the fixture's `ORCHESTRATION.md` ends with `Status: DONE`, `git log` in the fixture shows no
  commit after the baseline, and `SPEC.md` status there was written only by `/spec-review` and
  `/spec-close` (their entries appear in the closure delta).

  **[OBSERVED 2026-09-02]** Evidence copied to `evidence/` because the fixture lives in the session
  scratchpad: `ORCHESTRATION-adopted-run.md` (`Run result: DONE`, HEAD `2ed6adc` unchanged, SPEC status
  written only by the owning skills), `ORCHESTRATION-allchecked-run.md` (AC-006), `PR_DESCRIPTION-adopted-run.md`.

- [x] T013 - Codex smoke run of the adopt entry (refusal without `--adopt`, happy path to at least
  the inherited-diff review verdict), recorded in `CALIBRATION.md` as pass with evidence or as an
  explicit closure blocker. Covers: AC-014.
  Verify: the maintainer confirms that `CALIBRATION.md` carries a Codex row that is either a pass
  with command and output excerpt, or the literal blocker "Codex CLI not available on this machine"
  marked as blocking `/spec-close`; it is never absent and never marked pass without an excerpt.

  **[OBSERVED 2026-09-02] PASS.** The Codex CLI *is* installed here (`codex-cli 0.152.1`); the
  earlier "not available" assumption was wrong. Two runs recorded in `CALIBRATION.md` with commands
  and output excerpts: the refusal without `--adopt` (condition `Lifecycle status`, reached by
  inspecting the real repo) and the adopt path through state initialization to a valid `REJECT`
  verdict block naming the seeded defect. Caveat recorded there: condition 6 was assumed, not run.

- [x] T014 - Manual replay of the originating case on a copy of `proyecto-cumbre` feature 030:
  branch off `main`, commit the pending work, run `--autonomous <path> --adopt`, and observe that
  the two human-only tasks (visual review, real-world run) surface as human-gated escalations and
  the run ends `PAUSED` with the answers needed, not as a loop failure. Covers: AC-001, AC-014.
  Verify: the maintainer checks the copy's `ORCHESTRATION.md` shows two `human-gated` escalations
  in `waiting` status and `Run result: PAUSED`, and records the observation in `CALIBRATION.md`.

  **[VERIFY AMENDED 2026-09-02 — D011; residual tracked as DEBT-010]** The replay was **performed**,
  against the live repository the maintainer supplied at
  `/Users/manu/Proyectos/lead-platform-workspace/proycto-cumbre`, on a copy-on-write copy; the
  original was never touched and was confirmed afterwards still on `main` with its 21 dirty paths.
  The branch-then-commit remediation worked exactly as documented, clearing the `default branch` and
  `unattributed dirty tree` refusals. The run then stopped on two runner defects, which are this
  task's deliverable and are fixed by T029 and T030.

  The clause above cannot be met by this feature, and not because of those defects:
  `030-join-us-landing-aditiva` has since moved to `In Review`, which D002 excludes from adoption on
  purpose. The originating case is past the window adoption serves, so the criterion is
  unsatisfiable, not merely unmet. **The criterion actually met** is the one this task could still
  serve: the adopt entry was exercised end to end against a real adopter repository, and what it
  found is recorded in `CALIBRATION.md`.

  What remains owed is **not** this replay: it is that the adopted loop has never reached a
  human-gated `PAUSED` outside a fixture. That is [[DEBT-010]]. T028 observes the mechanism on a
  fixture and is not a substitute for the originating case.

  An earlier note here said this task was blocked because only encrypted archives of the repository
  were visible. The maintainer then supplied the live path; that note is superseded and removed
  rather than left to contradict the tick.

## Phase 5: Review findings (from /spec-review 2026-09-02)

- [x] T015 - Fix the CLI re-entry regression: `runner/sdd_runner/__main__.py` calls `gate.check(...)`
  without `first_entry`, so it is always `True`; with `READY_STATUSES` narrowed to `Ready` by T008 an
  adopted (`In Progress`) run can no longer be resumed through the CLI at all. Derive `first_entry`
  from the presence of `ORCHESTRATION.md` in the feature folder and pin CLI re-entry with a test
  (from CONF-041-01). Covers: AC-007, AC-009.
  Verify: on the `make_adopted_repo` fixture carrying an `ORCHESTRATION.md`, `python3 -m sdd_runner
  --dry-run` (no `--adopt`) exits 0 instead of refusing `lifecycle status`, and a new test in
  `runner/tests/` fails against the pre-fix `__main__.py`.

- [x] T016 - Add the missing executable evidence for AC-009's dry-run clause: a test that invokes the
  CLI with `--dry-run --adopt` on the adoption fixture and asserts the printed inherited record
  (both inherited task rows, `adoption baseline commit`, `adoption diff base`, `max-delegations: 25`)
  (from CONF-041-02). Covers: AC-009.
  Verify: `PYTHONPATH=runner python3 -m unittest discover -s runner/tests -t runner` exits 0 and its
  output includes the new dry-run test; deleting the printing block in `__main__.py` makes it fail.

- [x] T017 - Persist the adoption facts in the runner's own state document: header `entry`,
  `adoption baseline commit`, `adoption diff base` and an `Inherited` section, so a runner-written
  adopted document can reconstruct what was inherited instead of authenticating as a `ready` entry
  (from CONF-041-03). Covers: AC-009, and FR-010's "records the adoption baseline and diff base".
  Verify: a test asserts that a document created for an adopted run carries the three fields and one
  `Inherited` row per checked task, and that a `ready` run writes none of them.

  **[VERIFY AMENDED 2026-09-02 — from NEW-5]** "a `ready` run writes none of them" was wrong: the
  skill mandates, and the code writes, `n/a` in the three adoption fields plus an empty `Inherited`
  table (`SKILL.md` durable-state section; `state.py`). The corrected criterion is that a `ready`
  document carries `n/a` in both adoption fields and an `Inherited` table with zero rows, which is
  what `test_entry_default.py::AdoptionFactsArePersisted` asserts.

- [x] T018 - Add `runner/sdd_runner/loop.py`, `state.py` and `resume.py` to PLAN.md's *Impacted
  areas*; they are modified by D007 and D009 but listed only in the reading list (from CONF-041-04).
  Covers: AC-011.
  Verify: `grep -c "sdd_runner/\(loop\|state\|resume\).py" specs/features/041-autonomous-adopt-in-flight-feature/PLAN.md`
  counts them inside the *Impacted areas* section, and `bash scripts/check-consistency.sh` exits 0.

## Phase 6: Review findings, round 2 (from /spec-review 2026-09-02, second pass)

- [x] T019 - Guard the empty-tree rule with `first_entry` in `runner/sdd_runner/gate.py`: T008 removed
  the feature-folder tolerance for first entry, which is right (D004), but the rule is applied on
  re-entry too, so a live run cannot resume over its own uncommitted `ORCHESTRATION.md`. Restore 031's
  re-entry rule — only paths attributable to the recorded run may be dirty — and keep first entry
  strict in both modes (from NEW-1). Covers: AC-003, AC-007, AC-009.
  Verify: re-entering the `make_adopted_repo` fixture with an UNCOMMITTED `ORCHESTRATION.md` exits 0
  instead of refusing `unattributed dirty tree`, a path outside the run's attributable set still
  refuses on re-entry, first entry still refuses any dirty path in both modes, and the new test fails
  against the unguarded rule.

- [x] T020 - Authenticate the state document at the CLI entry, not only inside `Loop`: `--dry-run`
  returns before `Loop` is built, so it reports a pass for a state file that `resume.inspect` would
  reject, and `first_entry` is currently decided by file existence alone. Validate it where
  `first_entry` is derived and exit with the existing `state-unresumable` / `concurrent-run` codes
  (from NEW-2). Covers: AC-007, AC-009.
  Verify: `--dry-run` on a feature whose `ORCHESTRATION.md` lacks `max-delegations` exits 16 naming
  the field, a live-pid ACTIVE document exits 15, and a valid document still exits 0.

- [x] T021 - Three defects introduced by T017, fixed together because they are one edit each:
  remove the dead `self.inherited` attribute and its false comment (`loop.py`); move the
  `if __name__ == "__main__"` guard in `runner/tests/unit/test_entry_default.py` to the end of the
  file so running it directly does not silently skip the T017 class; make `_inherited_record` raise
  instead of returning `None` when the gate refuses, so an adopted document can never be written with
  `n/a` adoption fields (from NEW-3, NEW-4, NEW-6). Covers: AC-009.
  Verify: `grep -c "self.inherited" runner/sdd_runner/loop.py` prints 0;
  `PYTHONPATH=runner python3 runner/tests/unit/test_entry_default.py` reports 4 tests, not 2; and a
  test asserts `_inherited_record` raises when `origin/HEAD` is unset for an adopt entry.

  **[OBSERVED 2026-09-02]** The direct run reports **5** tests, not the 4 the clause predicted: the
  NEW-6 test the same task adds is the fifth. Before the guard move it reported 2.

- [x] T022 - Annotate T017's stale `Verify:` clause with the repo's `[VERIFY AMENDED]` convention: it
  says a `ready` run "writes none of them", while the skill mandates and the code writes `n/a` in the
  three fields plus an empty `Inherited` table (from NEW-5). Covers: AC-011.
  Verify: T017's task item carries a `[VERIFY AMENDED 2026-09-02]` note naming the corrected
  criterion, and `bash scripts/check-consistency.sh` exits 0.

## Phase 7: Review findings, round 3 (from /spec-review 2026-09-02, third pass)

- [x] T023 - Move the `if __name__ == "__main__"` guard in
  `runner/tests/integration/test_adopt_cli.py` to the end of the file: it sits before
  `StateIsAuthenticatedAtTheGate`, so a direct run silently skips the four tests that are T020's
  only evidence. This is NEW-4 reintroduced one file over (from R3-01). Covers: AC-009.
  Verify: `PYTHONPATH=runner python3 runner/tests/integration/test_adopt_cli.py` reports 9 tests,
  the same count `unittest discover` collects for that module; it reported 5 before.

  **[OBSERVED 2026-09-02 — from R4-02]** The direct run reports **13**, not the 9 this clause
  predicted: T024 added four tests to the same file later in the same round. The invariant the
  clause asserts — direct run equals discovery — holds at 13/13, and holds for all four test
  modules this feature touches.

- [x] T024 - Settle the refusal precedence T020 changed: authenticating the state document before
  the gate made *Already adopted or entered* unreachable for any document that is not a valid
  runner-written one, so a stale or skill-written file exits 16 where `SPEC.md`'s edge case,
  `runner/README.md`, `docs/SDD-ORCHESTRATION.md` and two `CALIBRATION.md` rows all say 10. Decide
  the order, make code and documents agree, and cover the path by test (from R3-02).
  Covers: AC-002, AC-007, AC-013.
  Verify: a CLI test asserts the exit code and condition for `--adopt` over a skill-written
  document and over a terminal one; `grep -n "already adopted or entered"` in README, docs and
  CALIBRATION matches what the code does.

- [x] T025 - Resolve `attributed`: no production caller passes it and the runner records no
  attributed paths, so on re-entry the CLI tolerates only the four run artifacts and a real-backend
  run whose worker touched source files cannot resume. Either wire it or record it as a deliberately
  unwired extension point with the resulting limitation stated where D006 bounds runner parity
  (from R3-03). Covers: AC-007, AC-009.
  Verify: a DECISIONS entry states the choice and the limitation, `runner/README.md` names it, and
  the test that exercises `attributed` says in its docstring that it pins a capability the CLI does
  not yet use.

- [x] T026 - Three one-line corrections (from R3-04, R3-05, R3-06): clarify D004, which says the
  feature-folder tolerance is removed in both modes while T019 restored a four-path tolerance on
  re-entry; reword the "one list, so the gate and the fingerprint agree" comment, since the
  fingerprint matches by `endswith` and the gate by exact relative path, and note the POSIX
  separator assumption; and guard the early `Orchestration.load` in `__main__.py` so an unreadable
  state file exits with a code instead of a traceback. Covers: AC-009, AC-011.
  Verify: D004 carries a `Clarified` note; the comment no longer claims rule parity; and a CLI run
  against an undecodable `ORCHESTRATION.md` exits 16 or 70, never 1 with a traceback.

## Phase 8: Review findings, round 4 (from /spec-review 2026-09-02, fourth pass)

- [x] T027 - Three documentation corrections, combined because each is one edit from one review and
  none changes behavior (from R4-01, R4-02, R4-03): (a) `gate.RUN_ARTIFACTS` and
  `runner/README.md` both describe the four names as "the files the runner writes itself", which
  contradicts the same README thirteen lines down and the code — the runner never writes
  `PR_DESCRIPTION.md`, so the gate tolerates a dirty one nobody produced; reword both, and keep the
  tuple as it is because `Loop._fingerprint` has excluded that name since before this feature and
  changing it would change behavior nobody asked to change. (b) Annotate T023, whose `Verify:` says
  9 tests while the file now has 13, because T024 added four to it in the same round. (c) Name the
  fixture document in the round-2 transcript in `CALIBRATION.md`: its `exit 0` is only correct
  because the state file was a valid resumable document, and a reader cannot tell.
  Covers: AC-009, AC-011, AC-013.
  Verify: `runner/README.md` no longer claims the runner writes `PR_DESCRIPTION.md` and its two
  statements about that file agree; T023 carries an `[OBSERVED 2026-09-02]` note giving 13; the
  round-2 transcript names the document body it ran against; the suite stays green at 270 and
  `bash scripts/check-consistency.sh` exits 0.

## Phase 9: Escalation-path evidence

- [x] T028 - Observe the human-gated escalation path on an adopted run. Round 3's review noted that
  deferring T014 leaves this path unobserved in the whole feature: the calibration run ended `DONE`
  with zero escalations, so "a human-only task surfaces as a human-gated escalation and the run ends
  `PAUSED`, not as a loop failure" rests on 031's unchanged code, not on evidence. Run an adopted
  fixture whose queue holds one human-only task and one independent task, with a genuine worker
  delegation, and record it. This does NOT replace T014: it covers the mechanism, not the
  originating case. Covers: AC-001, AC-012.
  Verify: the fixture's `ORCHESTRATION.md` ends `Run result: PAUSED` with one `human-gated`
  escalation in `waiting` status carrying the worker's verbatim question, the independent task is
  checked and the human-only one is not, and no `git commit`/`push`/`stash` was made by the loop.

  **[OBSERVED 2026-09-02]** All four clauses hold; state file copied to
  `evidence/ORCHESTRATION-escalation-run.md`. `Run result: PAUSED`, `ESC-001` human-gated and
  `waiting`, T004 checked and T003 not, HEAD unchanged and equal to `origin/feat/adopted`.

## Phase 10: Honest refusals over dialect parsing (from the T014 replay)

- [x] T029 - Say "I could not read a status" instead of quoting whatever the first line happened to
  be. `gate._status_line` returns the first non-empty, non-quote line under `## Status`, so a spec
  that writes its status inside a fenced block yields the fence and the refusal reads
  `Status is '```'`. Recognize an unreadable status and refuse under its own condition naming the
  form the gate expects. Do NOT parse adopter dialects: that surface is unbounded, the runner is
  experimental, and the skill path reads them fine because a model reads them (from the T014
  replay). Covers: AC-002, AC-009.
  Verify: on a SPEC whose status sits in a fenced block, the refusal names condition
  `status unreadable`, quotes no fence, and its remediation states the expected form; a normal SPEC
  is unaffected.

  **[VERIFY AMENDED 2026-09-02 — from R5-04]** "quotes no fence" was the wrong criterion. The detail
  does quote the offending line — `is '```', which states no lifecycle status` — and that is better:
  showing the maintainer the line the gate could not read is more useful than hiding it. What the
  clause meant, and what is pinned by `test_a_fenced_status_refuses_as_unreadable_not_as_a_quoted_fence`,
  is that the refusal names its own condition instead of masquerading as `lifecycle status`.

- [x] T030 - Make the open-questions refusal admit what it cannot judge. Gate condition 2 forbids an
  unresolved question **that blocks an unchecked task**; the parser counts every bullet that is not
  struck through or marked Resolved, so it refuses on questions a spec deliberately carries as
  non-blocking. Keep the count and the fail-closed refusal, but say in the message that the gate
  cannot tell blocking from non-blocking and name the questions so the maintainer can. Do not parse
  non-blocking markers, for the same reason as T029 (from the T014 replay). Covers: AC-002, AC-009.
  Verify: the refusal names the questions it counted and states that it cannot judge whether they
  block; a spec with no open questions is unaffected.

## Phase 11: Review findings, round 5

- [x] T031 - Repair the round-5 findings, all prose, all from one review (R5-01…R5-06): put T014's
  closure notes under T014 instead of under T028 and T030, where appending to the end of the file had
  left them, and remove the stale text that said T014 still blocks `/spec-close` while it was ticked;
  restate that closure with the repo's own `[VERIFY AMENDED]` convention plus a DEBT id for the real
  residual, instead of the invented `PERFORMED` marker; document the `status unreadable` condition in
  `runner/README.md` and in SPEC's interface list and correct the `gate.py` comment that claimed it
  was mirrored from the skill; record D011 for the closure-marker decision and the deliberate
  runner/skill divergence; annotate T029's clause; and add `docs/KNOWN_DEBT.md` to PLAN's impacted
  areas. Covers: AC-011, AC-013.
  Verify: every `[VERIFY AMENDED]`/`[OBSERVED]` note sits under the task it describes; `grep -c
  "blocks .spec-close" TASKS.md` returns 0; `status unreadable` appears in `runner/README.md` and
  `SPEC.md`; D011 and DEBT-010 exist; `bash scripts/check-consistency.sh` exits 0 and the suite stays
  at 275.
