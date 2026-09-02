# Implementation Plan: autonomous-adopt-in-flight-feature

## Summary

Add an explicit `--adopt` entry to `/sdd-orchestrate --autonomous` so a feature that is already
`In Progress` — started by hand through `/spec-implement` — can be handed to the 031 loop. The
entry keeps every fail-closed rule of the existing gate (clean tree, non-default branch, green
baseline), records what it inherits in `ORCHESTRATION.md`, reviews the inherited diff through the
structured reviewers before delegating any new task, and then runs the unchanged circuit. The 040
runner's entry gate is reconciled with the skill in the same direction, the manual chain learns to
point at adoption, and the Codex adapter documents the entry under the same sequential-degradation
contract as the parent mode. Behavioral evidence on both providers gates `Done`.

## Related spec

[SPEC.md](SPEC.md)

## Impacted areas

- `skills/sdd-orchestrate/SKILL.md` — ARGUMENTS block, flag validation, entry gate (conditions 1,
  5, new 7, three new refusal names), state scaffold (`Entry`, adoption header fields,
  `## Inherited`), circuit (inherited-diff review step and blocker gating), termination
  (final-conformance brief carries the `Inherited` table).
- `skills/spec-implement/SKILL.md` — one line in *Recommended next command*.
- `skills/sdd/SKILL.md` — one alternative in step 4 of both workflows.
- `adapters/codex/prompts/sdd-spec-implement.md` — the same hand-off line in its closing
  recommendation.
- `adapters/codex/PARITY.md` — *Autonomous orchestration — sequential degradation* gains the
  adoption gate, inherited record and inherited-diff review.
- `docs/SDD-ORCHESTRATION.md` — *Autonomous mode* subsection documents `--adopt`, its refusal
  conditions and remediation order; the runner flag table and exit-code 10 line list adoption.
- `runner/sdd_runner/gate.py`, `runner/sdd_runner/__main__.py`, `runner/README.md` — `--adopt`,
  status matrix, dirty-path rule, inherited record in `--dry-run`, and the first-entry/re-entry
  distinction the CLI never passed (T015).
- `runner/sdd_runner/loop.py`, `runner/sdd_runner/state.py`, `runner/sdd_runner/resume.py` — the
  `entry` field and the persisted adoption facts (D007, T017), plus the empty-attempts arity fix
  (D009). Added 2026-09-02 by T018: they were modified from T009 onward but listed only in the
  reading list below, which is a different claim.
- `runner/tests/unit/test_gate.py`, a new fixture builder under `runner/tests/fixtures/` or
  `runner/tests/support.py`, a state/resume test for the `Entry` default, and a CLI-level test for
  the adopt entry and its re-entry (`runner/tests/integration/test_adopt_cli.py`, T015/T016).
- `specs/features/041-autonomous-adopt-in-flight-feature/CALIBRATION.md` — provider evidence
  (created during Phase 4, not before).
- `docs/KNOWN_DEBT.md` — added 2026-09-02: DEBT-001 and DEBT-002 rest on the premise that no Codex
  CLI exists on this machine, which T013 disproved, and T014's residual is registered as DEBT-010.

Not touched: `install.sh`, `install.ps1`, `install-all.*`, `profiles.json`,
`settings.template*.json`, agents, hooks. AC-011 makes this checkable.

## Context budget

### Reading list

- The feature folder: `SPEC.md`, this plan, `TASKS.md`, `DECISIONS.md`.
- `skills/sdd-orchestrate/SKILL.md` in full — it is the protocol being extended.
- `skills/spec-implement/SKILL.md` and `skills/sdd/SKILL.md`: only the *Recommended next
  command* / workflow-step sections.
- `adapters/codex/PARITY.md`: the *Autonomous orchestration — sequential degradation* section.
- `adapters/codex/prompts/sdd-spec-implement.md`: the closing recommendation paragraph.
- `docs/SDD-ORCHESTRATION.md`: *Autonomous mode* (around line 180) and the runner tables (around
  lines 320–345).
- `runner/sdd_runner/gate.py`, `runner/sdd_runner/__main__.py`, `runner/sdd_runner/state.py`
  (header parsing only), `runner/sdd_runner/resume.py` (entry authentication only),
  `runner/tests/unit/test_gate.py`, `runner/tests/support.py`, `runner/README.md` (flag table and
  exit codes).
- `specs/features/031-autonomous-orchestration-loop/SPEC.md` FR-012/AC-013 and
  `specs/features/031-autonomous-orchestration-loop/CALIBRATION.md` as the evidence format to
  mirror. Nothing else from 031/032/035/040.
- `docs/KNOWN_DEBT.md`: only if a task is deferred (next free id is DEBT-010).

Do not read: other specs, `evals/`, hooks, agents, installers, `graph.json`.

### Model routing

- **Deep-reasoning model** (deep-reasoner / Opus): T003, T004 and T005 — they rewrite protocol
  prose that every later run obeys literally, and a wrong word there is a wrong gate. Also the
  design review of T008's status matrix before it is coded.
- **Cheap/mechanical model** (fast-worker / Sonnet): T001, T002, T006, T007, T009, T010, T011 —
  bounded edits with an executable `Verify:`.
- **Orchestrator itself**: T012 and T013 (calibration runs) — they exercise the skill and must be
  observed, not delegated as text edits. T014 is the maintainer's.

## Proposed approach

1. **Fixture first (T001).** A scratch-repo builder that produces an `In Progress` feature with two
   checked tasks whose diff is committed on a feature branch, one seeded reviewable defect in that
   diff, and two unchecked tasks. Runner unit tests, the dry-run integration check and the
   calibration run all use it, so refusal matrices and happy paths are reproducible.
2. **Skill protocol (T002–T005).** Extend `SKILL.md` in the order the run reads it: flag parsing →
   gate → state scaffold → circuit → termination. `--adopt` is explicit and first-entry-only. The
   gate under `--adopt` rewrites conditions 1 (status `In Progress` only) and 5 (fully clean tree,
   no attribution) and adds condition 7 (computable inherited record: baseline commit, merge-base
   with the default branch, checked-task set). Three stable refusal names are added. The scaffold
   gains `Entry`, `Adopted at`, `Adoption baseline commit`, `Adoption diff base` and an
   `## Inherited` table; a state file without an `Entry` line reads as `ready` so existing runs
   keep authenticating. The circuit gains a step before the first delegation: `domain-reviewer`
   (and `security-reviewer` on Level-3 triggers) on `diff-base..baseline`; a `Critical` finding on
   that diff blocks new spec tasks until a later APPROVE. The final-conformance brief carries the
   `Inherited` table and labels unobserved `Verify:` clauses.
3. **Manual chain and docs (T006–T007).** One additive line in `/spec-implement`, `/sdd` and the
   Codex `sdd-spec-implement` prompt. `docs/SDD-ORCHESTRATION.md` and `adapters/codex/PARITY.md`
   document the entry; PARITY keeps the "documented, not closure evidence until the smoke run
   passes" stance the parent mode already uses.
4. **Runner parity (T008–T010).** `gate.check(..., adopt=False)`: without adopt, first entry is
   `Ready` only; with adopt, `In Progress` only; `In Review` leaves first-entry acceptance in both
   modes; any dirty path refuses in both modes (the inside-feature-folder tolerance goes away, per
   D004); with adopt the gate computes and returns the inherited record and `--dry-run` prints it.
   `Refusal.condition` strings mirror the skill's names. Tests pin the whole matrix.
5. **Containment (T011)** and **evidence (T012–T014).** Consistency and manifests unchanged; a
   Claude Code calibration run over the fixture covering every AC that is observable in a run; a
   Codex smoke run recorded as pass or as an explicit `/spec-close` blocker; the maintainer's
   replay on a `proyecto-cumbre` copy.

## Alternatives considered

- **`--all` / `--until-review` on `/spec-implement`.** Rejected in the originating ADR and by the
  spec's Non-goals: a loop without verdict blocks, caps and durable state reintroduces the
  model-interpreted gate 031 removed.
- **Implicit adoption** (accept `In Progress` without a flag when no state file exists). Rejected:
  it turns a fail-closed refusal into a silent branch of behavior, and a stale or foreign
  `ORCHESTRATION.md` would become ambiguous. The runner currently does this by accident; D004 and
  D006 close it.
- **Tolerating dirty paths inside the feature folder on adoption** (the runner's current rule).
  Rejected (D004): no run exists yet to attribute them to, and 031's provenance rule says never
  guess. The maintainer's commit is the attribution.
- **Trusting inherited checked tasks without review.** Rejected (D005): "a self-report is worth
  nothing" is the repo's own lesson; the reviewers judge the diff, the checkbox is only provenance.
- **Full runner parity including dispatching the inherited-diff review.** Rejected (D006): the
  runner is `stub`-only and experimental; execution-level parity is the follow-up 040 D034 already
  reserves.

## Dependencies

- Git metadata for the default branch (`origin/HEAD` or equivalent) in the target repo; the gate
  refuses rather than assuming `main` (D003).
- Codex CLI for T013. **Corrected 2026-09-02:** this plan assumed it was not installed on the
  maintainer's Mac and wrote T013 so its absence would be an explicit blocker rather than a silent
  pass. The assumption was wrong — `codex-cli 0.152.1` is installed at `~/.local/bin/codex` — and
  T013 passed against it. The fail-closed shape of the task is what let the correction be a pass
  instead of a surprise.
- Python 3 stdlib for the runner suite (`unittest`, no pytest).
- `scripts/check-consistency.sh` green before any skill edit is committed.

## Risks

- **Protocol prose drift.** Five sections of `SKILL.md` change; a mismatch between the gate text
  and the scaffold text would be obeyed literally by the next run. Mitigation: deep-reasoning
  routing for T003–T005, and the calibration run (T012) reads the real text.
- **Runner tightening breaks a pinned behavior.** `test_unattributed_dirty_tree` currently asserts
  the inside-feature-folder tolerance; removing it is intended (D004) but must be an explicit test
  change, not a silent failure.
- **Inherited-diff review on a large inherited diff.** The reviewers get the whole
  `diff-base..baseline`; for a feature adopted late this is the biggest review of the run.
  Accepted: it is exactly the review debt adoption exists to pay; the delegation budget scales
  with unchecked tasks, so `max(25, …)` leaves room for two reviewers plus fixes.
- ~~**Codex evidence unavailable.** T013 may end as a `/spec-close` blocker on this Mac.~~
  **Did not materialize (2026-09-02):** the CLI is installed and T013 passed with two recorded runs.
  The risk was correctly framed — D001's rule gates `Done`, not `Ready` — it simply did not fire.
- ~~**Maintainer's replay (T014) depends on a repo not on this machine.** If not performed it is
  DEFERRED with a DEBT id, never ticked.~~
  **Materialized differently (2026-09-02):** the maintainer supplied the live path and the replay was
  performed. It did not pass — it found two runner defects, fixed as T029/T030 — and its criterion
  then turned out unsatisfiable because `030` had moved to `In Review`. Closed on its result under
  D011, with the residual as [[DEBT-010]] rather than as a deferral of the replay itself.

## Test strategy

- **Unit** (`runner/tests/unit/test_gate.py`, plus a state/resume test): status × adopt matrix;
  dirty path inside the feature folder refuses in both modes; missing `origin/HEAD` under adopt
  refuses with *Inherited diff undetermined*; inherited record shape (baseline sha, diff base,
  checked tasks); `Entry` header defaults to `ready` when absent.
- **Integration**: `--dry-run --adopt` on the T001 fixture prints two inherited rows and budget
  25; `--dry-run` without adopt on the same fixture exits 10 naming *lifecycle status*.
- **E2E / calibration** (T012, Claude Code): gate refusal matrix (AC-002, AC-003, AC-004), happy
  path with the seeded defect (AC-005), all-checked entry (AC-006), re-entry with and without
  `--adopt` (AC-007), final-conformance labeling (AC-008), exit assertion (AC-012), recorded in
  `CALIBRATION.md` with command and output excerpt per AC.
- **Provider parity** (T013, Codex): gate refusal and happy path, recorded as pass or explicit
  blocker (AC-014).
- **Manual** (T014): replay on a `proyecto-cumbre` copy; the two human-only tasks must surface as
  human-gated escalations.
- **Regression**: full runner suite green above its current count (239); `check-consistency.sh`
  exit 0; installers and manifests byte-identical to `main` (AC-011).

## Rollback strategy

- Skill and docs: revert the commits touching `skills/sdd-orchestrate/SKILL.md`,
  `skills/spec-implement/SKILL.md`, `skills/sdd/SKILL.md`, `adapters/codex/`,
  `docs/SDD-ORCHESTRATION.md`. Runs entered at `Ready` never wrote `Entry`, so old state files are
  unaffected; a state file written with `Entry: adopt` after a revert fails re-entry authentication
  (unknown header field) and must be preserved under a timestamped name, as the existing recovery
  rule already requires.
- Runner: revert `gate.py`, `__main__.py`, `README.md` and the tests together; the package has no
  callers inside the framework.
- No installer, manifest or profile change exists to roll back.

## PLAN verification checklist

- [x] The plan covers all acceptance criteria.
- [x] The plan avoids behavior outside the spec.
- [x] The Context budget section is filled (reading list + model routing), not left as placeholder.
- [x] Risks are documented.
- [x] Test strategy is documented.
- [x] Rollback strategy is documented.
- [x] SPEC.md status has been updated to `Ready`.
