# Tasks: canonical-autonomous-core

<!-- Each task carries a `Verify:` clause after `Covers:`: the criterion anyone checks to call it
     done. Nothing in the framework executes it; it is text for a human or an agent to act on. -->

**Ordering is load-bearing.** T001 before every implementation task (D007: without the golden
transcripts AC-008 has no oracle). T003 before T006–T011 (or the interface re-imports scattered
constants and the duplication survives behind a nicer face). T015–T019 last (or the contract tests
pin the pre-refactor shape).

## Phase 1: Preparation

- [x] T001 - Capture golden CLI transcripts for the ten AC-008 scenarios against the **pre-refactor**
  code, into `specs/features/042-canonical-autonomous-core/evidence/golden/`. Covers: AC-008.
  Verify: the directory holds one file per scenario (clean first entry, gate refusal per condition,
  dry run, dry-run adopt, concurrent run, unresumable state, cap abort, budget exhaustion, human
  escalation, core-complete), each recording exit code + stdout + stderr, and re-running the capture
  on an unmodified tree reproduces every one byte-for-byte.
  ~~Superseded clause: "gate refusal per condition ... reproduces all ten byte-for-byte."~~
  **Restated 2026-09-04 (CONF-002, CONF-003; count corrected by CONF-007; total dated by
  CONF-008).** "All ten" was the corpus when this task was written and the corpus has grown well
  past it since — `golden.SCENARIOS` is the authority for how far, and this clause states no figure
  of its own. And "per condition" was a claim the corpus did
  not meet — **five** of the gate's fifteen terminal conditions were recorded, carried by **four**
  `refusal-*` scenarios, because `refusal-adopt-not-needed` reaches two of them ("adoption not
  needed" and "inherited diff undetermined"). ~~"four of the gate's fifteen terminal conditions"~~
  counted scenarios and called them conditions; the two are different numbers and the coverage
  matrix is keyed by condition. The criterion was **not** narrowed: `test_gate_refusal_coverage`
  derives the conditions from `gate.py`'s AST and fails if any lacks a transcript, and the ten
  missing scenarios were added. **Current verification:** every scenario in `golden.SCENARIOS`
  replays byte-for-byte on an unmodified tree, and every condition the gate can emit maps to one.
- [x] T002 - Inventory every protocol constant, its single current definition site and its target
  home, into `evidence/CONSTANT_INVENTORY.md`. Covers: AC-001. Verify: the table lists every constant
  named in `exits`, `state`, `gate`, `loop`, `blocks`, `escalation`, `budget`, `resume`, and every
  constant stated by the nine FR-012 surfaces appears in it with a definition site or is marked
  prose-only.

## Phase 2: Implementation

- [x] T003 - Create `sdd_runner/policy.py` holding every constant from T002 as a typed value; the
  owning modules import from it and define none of their own. Covers: AC-001. Verify:
  `PYTHONPATH=runner python3 -m unittest discover -s runner/tests -t runner` is green **and** a new
  test enumerates `policy`'s public names and fails if any is assigned a second time anywhere under
  `runner/sdd_runner/`.
- [x] T004 - Add `PROTOCOL_VERSION = 1` and the `Protocol version` header field: written on create,
  preserved on save, added to `skills/sdd-orchestrate/templates/ORCHESTRATION.md`. Covers: AC-004.
  Verify: a newly created document contains the line, and
  `specs/features/032-.../ORCHESTRATION.md` and `033-.../ORCHESTRATION.md` still round-trip
  byte-identically through `state.Orchestration` (the existing `test_state.RoundTrip` test stays
  green untouched).
- [x] T005 - Read compatibility: absent version reads as 1 and stays resumable; unknown or malformed
  refuses fail-closed naming both the version read and the version supported. Covers: AC-004.
  Verify: three unit tests — absent → resumes; `99` → exit 16 with both versions in the message;
  `abc` and empty → same path, no traceback.
- [x] T006 - Introduce `RunRequest` in `sdd_runner/protocol.py` and move request validation out of
  `__main__.py`: feature-path containment through resolved real paths, contradictory fields, cap
  overrides, backend options. Covers: AC-002, AC-003. Verify: the existing containment tests
  (symlink, `features-old`, features root) pass with their assertions unchanged, and
  `grep -n "realpath\|commonpath" runner/sdd_runner/__main__.py` returns nothing.
- [x] T007 - Introduce `GateResult`, `Refusal` and `RunPlan` value types; `gate.check` returns a
  `GateResult`. Covers: AC-002, AC-005. Verify: every refusal condition name and the order in which
  refusals are reported match T001's golden transcripts exactly.
- [x] T008 - Implement `run(RunRequest) -> RunOutcome`, absorbing first-entry determination, resume
  authentication and its ordering against the gate, budget computation and backend resolution from
  `__main__.py`. Covers: AC-002, AC-003. Verify: `__main__.py` contains argv parsing, rendering and
  the exit call only, and a test asserts it imports no `sdd_runner` name outside `__all__`.
- [x] T009 - Define `__init__.__all__` as the public surface; stop re-exporting internals. Covers:
  AC-011. Verify: a test reads `__all__`, asserts `len(__all__) <= 12`, and asserts every name the
  CLI imports from the package is in it.
- [x] T010 - Guarantee `RunOutcome` and `GateResult` leak no internal object. Covers: AC-002.
  Verify: a test walks both dataclasses' fields recursively and fails on any `Loop`,
  `Orchestration`, `Backend`, `CounterState`, file handle or mutable shared reference.
- [x] T011 - Move dry-run computation into the core as a `RunPlan`; the CLI only renders it. Covers:
  AC-007, AC-008. Verify: the `dry run` and `dry-run adopt` golden transcripts from T001 match byte
  for byte.
- [x] T012 - Correct the authority statement in `runner/README.md`, `sdd_runner/__init__.py` and
  `skills/sdd-orchestrate/SKILL.md` per D004. Covers: AC-012. Verify: a test asserts no file among
  the nine FR-012 surfaces contains a sentence stating the runner is wrong when it disagrees with
  the skill, and that `SKILL.md` states the executable contract is the source of truth.
- [x] T013 - Declare the three seams in `sdd_runner/seams.py`, each naming its future owner, with no
  implementation. Covers: AC-010. Verify: a test asserts no `Backend` other than `stub` is reachable
  without `--allow-unverified-backend`, no autonomous entry point exists, and no lifecycle skill is
  dispatched after `CORE-COMPLETE`.
- [x] T014 - Local packaging per D006: `pyproject` declares the package, no runtime dependency
  outside the stdlib, no import reaching outside the package. Covers: AC-009. Verify:
  `python3 -m sdd_runner --help` exits 0 on a checkout with neither the Agent SDK nor the Codex CLI,
  and a test asserts every top-level import in the package resolves to the stdlib or to
  `sdd_runner`.

## Phase 3: Tests

- [x] T015 - Write one contract test per FR-012 surface (nine), each reading the enumerated surface
  list. Covers: AC-006. Verify: nine tests exist, each named for its surface; each is demonstrated
  failing under a deliberate mutation of that surface, and the mutation and its revert are recorded
  in `evidence/CONTRACT_MUTATIONS.md`.
- [x] T016 - Add the over-reach guard of FR-012a. Covers: AC-006. Verify: the suite is green while
  the twelve review skills are untouched, and a test asserts each contract test consumes the surface
  list rather than walking the repository.
- [x] T017 - Drive start, pause, abort, resume and core-complete through the public interface alone
  with a scripted `stub`. Covers: AC-007. Verify: the test module imports only `run` and
  `RunRequest` from `sdd_runner`, and asserts the five terminal states with their exit codes.
- [x] T018 - Update `PROTOCOL_TRANSCRIPTION.md` module references to survive the move, without
  widening the `MODULES` hole D002 names. Covers: AC-006. Verify: `test_transcription.py` is green
  and every row's module attribute resolves — checked by temporarily asserting zero rows are skipped.
- [x] T019 - Add the golden CLI comparison test replaying T001's transcripts. Covers: AC-008.
  Verify: every recorded scenario matches byte for byte **outside every difference FR-009's
  `authorised-observable-differences` block currently enumerates**, and inside none of them by
  accident: `test_golden_cli` derives the membership from that block by identifier and fails if its
  own constants and the block disagree. This clause names no difference and no count of its own.
  ~~Superseded clause 1: "all ten scenarios match byte for byte except the `Protocol version` line
  of FR-009, and the test names that line as the sole permitted difference."~~
  ~~Superseded clause 2: "except the two authorised differences, `DIFF-001` and `DIFF-002` … and
  `AUTHORISED_SCENARIO_DIFFERENCES` for the scenario-level one."~~
  **Restated twice; both restatements are recorded, neither is the criterion in force.**
  *2026-09-04 (CONF-002)* replaced clause 1, whose two halves had gone false: the corpus was no
  longer ten and `Protocol version` was no longer the sole permitted difference. *2026-09-04
  (CONF-002, re-reported at T025)* replaced clause 2, which repeated the defect at a smaller scale —
  it swapped one fixed enumeration for another, and D018 falsified it four decisions later by
  authorising `DIFF-003` and giving `AUTHORISED_SCENARIO_DIFFERENCES` a second entry. A criterion
  that copies the list is a second list. Named rather than erased, as T043, T055 and T065 do.
- [x] T020 - Run the full suite and confirm the test diff is import-only. Covers: AC-005. Verify:
  `Ran N tests` with `N >= 276` and `OK` on a machine with neither the Agent SDK nor the Codex CLI,
  and `git diff main -- runner/tests` shows no changed line inside an `assert*` call.

## Phase 4: Review

- [x] T021 - Confirm installer and manifest byte-identity. Covers: AC-009. Verify:
  `bash scripts/check-consistency.sh` exits 0 and
  `git diff --stat main -- install.sh install.ps1 profiles.json` is empty.
- [x] T022 - Confirm the preserved file is untouched. Covers: AC-013. Verify: **all four jointly** —
  `git ls-files --error-unmatch docs/AUTONOMOUS_SDD_FEATURE_PROMPT.md` exits 1;
  `git status --porcelain --untracked-files=all` on it shows `??`; its `shasum -a 256` equals
  `evidence/PRESERVED_FILE_BASELINE.txt`; and `git diff --name-status main...HEAD` on it is empty.
  **The original clause named `git status` alone, and that is why this task was reported met while
  failing** — `git status` is silent about a path that is staged or committed (D010).
- [x] T023 - `domain-reviewer` on the full implemented diff. Covers: AC-003, AC-006. Verify: an
  APPROVE verdict block for the current fingerprint, or every REJECT finding repaired and re-approved.
  **Closed 2026-09-04 on the second limb of that clause.** `domain-reviewer` ran five times over the
  implemented diff and returned REJECT each time; every finding it raised is repaired and
  re-verified. Round-5 delta: `DOM-019`, `DOM-023`, `DOM-028`, `DOM-029` all **CLEARED**, and
  `DOM-019`'s post-verdict continuation re-checked and **CLEARED** again
  (`evidence/SUITE_AND_TEST_DIFF.md:64`). Its four non-blocking observations were deliberately not
  repaired and are recorded as [[DEBT-013]]. No `domain:` identity remains unrepaired: 54 registry
  rows, 54 canonical `task_ref`s, 0 broken.
- [x] T024 - Evaluate the Level-3 security triggers against the real diff and record the evaluation;
  run `security-reviewer` if triggered. Covers: AC-002, AC-009. Verify: the evaluation is written
  down naming which triggers matched, and an APPROVE verdict block exists if it ran.
  **Closed 2026-09-04.** The evaluation is `evidence/SECURITY_TRIGGER_EVALUATION.md`: all ten
  triggers assessed against `policy.SECURITY_TRIGGERS`, three matched — `public api`, `schema`,
  `persistence` — with the evidence for each of the seven that did not, including that `log.py`'s
  redaction was untouched so `secret` does not match. It also records the two security-relevant
  changes **no trigger word names** (path containment moving modules, the pre-existing broad
  `except`), handed to the reviewer as hunting instructions rather than by inventing a second
  trigger list, which the protocol forbids. `security-reviewer` ran five times and returned REJECT
  each time; every finding is repaired and re-verified. Round-5 delta: `SEC-013`, `SEC-014`,
  `SEC-015`, `SEC-016` all **CLEARED**.

  **What changed after security's verdict, and why no re-run is owed.** Three files: the AC-005
  evidence artifact `evidence/SUITE_AND_TEST_DIFF.md`, its guard
  `runner/tests/contract/test_ac005_evidence.py` (extended in place), and `FINDINGS.md`'s DOM-019
  row. **No production file was touched** — nothing under `runner/sdd_runner/` — so no new
  Level-3 trigger matches and the 20/20 golden transcripts still replay byte-identically. The change
  is evidence and its guard, which is the one category a security verdict does not gate.
- [x] T025 - `final-conformance-reviewer` once over the full evidence chain. Covers: AC-001…AC-013.
  Verify: an APPROVE verdict block citing each acceptance criterion against its task and evidence.
  **Provenance of the verification, so no later reader conflates the two (`conformance:CONF-005`):**
  the **first** conformance pass was **documentary** — that session had no shell, and it said so:
  AC-004, AC-005, AC-006, AC-008, AC-009 and two of AC-013's four checks were verified by reading
  in-tree artifacts and guard code, not by observing a run. It returned REJECT with five findings.
  The **independent execution was performed by the runner** and is persisted in
  `evidence/EXECUTED_BATTERY.md` with each command, its own exit code and the tree fingerprint it
  ran against. The retry pass verifies **the resulting artifacts**; it does not claim to have run a
  shell, and must not be read as having done so.
  **APPROVE 2026-09-04.** The final retry reviewed the complete 97-path tree at digest
  `e19066bd78aded16361a86c21e7cdccfa7ac8ca210237a75ee556442f742cada`: Standards reported no
  blocking violation, final conformance marked AC-001…AC-013 PASS, and CONF-002/006/007/008,
  CONF-009…012 and MNT-005…010 were verified against their repairs and executable evidence.
- [x] T026 - `/spec-review` then `/qa-review`. Covers: AC-005, AC-008. Verify: `/spec-review` returns
  Pass and sets `In Review`; `/qa-review` reports no unaddressed regression.
  **Pass 2026-09-04.** Spec review consumed T025's AC-001…AC-013 APPROVE and performed the owning
  `In Progress` → `In Review` transition. QA observed 494 tests, 30/30 golden scenarios, ten stable
  retrospective baselines, 15/15 gate conditions, 18/18 caught mutations, a dependency-free CLI
  help path, installer parity and clean consistency/compile/diff checks. It found no unaddressed
  regression; the explicitly accepted residual risks remain in DEBT-011…013.
- [x] T027 - `/spec-close` then `/pr-description`. Covers: AC-001…AC-013. Verify: `/spec-close` sets
  `Done` and `PR_DESCRIPTION.md` exists with acceptance-criterion-to-evidence traceability.
  **Closed 2026-09-04.** `SPEC.md` is `Done`; every AC is covered below and was PASS at T025;
  `IMPLEMENTATION_SUMMARY.md` records the delivered scope and residual debt; `PR_DESCRIPTION.md`
  traces AC-001…AC-013 to the implementation and executed evidence. No commit, push or PR was made.

## Phase 5: Repairs from review

- [x] T028 - Make `Protocol version` readable by the core wherever a surface states it, and replace
  the substring guard with one that parses (from security:SEC-001). Covers: AC-004, AC-006.
  Verify: `state.Orchestration.loads(<the template's text>).protocol_version()` returns
  `policy.PROTOCOL_VERSION`, and mutating the template's value to `2` fails the guard.
- [x] T029 - Pass `resumable` explicitly on every pre-loop refusal (from security:SEC-002). Covers:
  AC-002. Verify: a test asserts `RunOutcome.resumable is False` for exit 16 via **both** routes —
  `_authenticate_reentry` and `loop.run` — and for the internal-error path.
- [x] T030 - Add the sibling-prefix containment test (from security:SEC-003). Covers: AC-002.
  Verify: a feature folder planted at `specs/features-old/900-fixture` is refused, and the test
  fails when `protocol.resolve_feature`'s `commonpath` check is mutated to `startswith`.
- [x] T031 - Redact the internal-error diagnostic and guard its log write (from security:SEC-004).
  Covers: AC-002. Verify: a test asserts a secret in an exception message reaches neither stderr nor
  `run.jsonl`, and that a failing `log.emit` still exits 70 rather than raising.
- [x] T032 - Define `REFUSED` and `PLANNED` in `policy` (raised adjacent to security:SEC-002).
  Covers: AC-001. Verify: `test_policy.SingleDefinition` sees them, and `protocol.py` assigns
  neither at module level.

- [x] T033 - Correct the surviving pre-042 authority sentence and widen the guard that missed it
  (from domain:DOM-001). Covers: AC-012, AC-006. Verify: `docs/SDD-ORCHESTRATION.md` states the
  inverted authority, `AuthorityIsInverted.OLD` matches `(this|the) runner is wrong`, and a
  core-side mutation restoring the old sentence fails the suite.
- [x] T034 - Restore `budget.__doc__` (from domain:DOM-002). Covers: AC-001. Verify: a test asserts
  every module in the package has a non-`None` `__doc__`, and it fails with the import above it.
- [x] T035 - Resolve the empty-version contradiction (from domain:DOM-004). Covers: AC-004.
  Verify: an empty value takes the same path the SPEC's edge case names, and SPEC and test agree.
- [x] T036 - Stop the CLI importing from `policy` (from domain:DOM-005). Covers: AC-003, AC-011.
  Verify: `test_interface` has no whitelist beyond `__all__`, and `__main__` imports only public names.
- [x] T037 - Add FR-012's missing surface coverage and D005's uncovered-constant test (from
  domain:DOM-007). Covers: AC-006. Verify: `SECURITY_TRIGGERS`, the gate condition names and their
  order, and the exit-code names each have a surface test; a `policy` value consumed by no surface
  test fails the suite.
- [x] T038 - Freeze `gate.Refusal` and generalise the leak walk (from domain:DOM-008). Covers:
  AC-002. Verify: the walk asserts every dataclass reachable from `RunOutcome` is frozen, and fails
  if `Refusal` is unfrozen.
- [x] T039 - Correct the `_state_fields` comment and report the pre-existing field loss (from
  domain:DOM-009). Covers: AC-004. Verify: a test asserts every key `state.new_document` writes
  survives `Loop._persist`, or names the two it does not and why.
- [x] T040 - Carry the read protocol version through resume instead of restamping (from
  domain:DOM-010). Covers: AC-004. Verify: a document read at version N is persisted at N.
- [x] T041 - Delete the incoherent assertion (from domain:DOM-011). Covers: AC-001. Verify:
  `test_policy` no longer contains `assertIsNone(node.module and ...)`.
- [x] T042 - Make the first-entry-status guard read `policy` (from domain:DOM-012). Covers: AC-006.
  Verify: mutating `policy.READY_STATUSES` fails the guard, recorded in `CONTRACT_MUTATIONS.md`.
- [x] T043 - Validate contradictory fields before the dry-run branch (from domain:DOM-013).
  Covers: AC-002. Verify: `docs/KNOWN_DEBT.md` carries a `DEBT-011` row and section describing the
  unvalidated dry-run path, and the tree matches `main` — `--dry-run --backend claude --stub-script
  <path>` exits 0 with a plan, pinned by the `dry-run-contradiction` transcript.
  **DEFERRED (2026-09-03) -> DEBT-011.** The work was implemented and then undone by T049: it
  widened observable behaviour, which AC-008 forbids and D011 (Superseded) records. **This task is
  not presented as executed** — strict validation of backend-exclusive options in a dry run is not
  implemented in this feature. Its `Verify:` clause above is therefore the deferral's criterion, not
  the original one, which the tree now deliberately fails. The earlier `REVERTED` annotation was not
  one of the three markers the TASKS template admits (`DEFERRED`, `SKIPPED`, `RESOLVED`), which is
  the second half of domain:DOM-020. The half that *is* implemented — the real run refuses the
  contradiction — belongs to T049 and to the `stub-script-wrong-backend` transcript.
  **AC-002 does not depend on this task.**
- [x] T044 - Measure the extras on the package, not the process (from domain:DOM-014). Covers:
  AC-009. Verify: the assertion runs in a subprocess or over the AST, and would fail if the package
  imported an extra eagerly.
- [x] T045 - Add the ordering-discrimination fixture (from domain:DOM-015). Covers: AC-002. Verify:
  a re-entry that is both gate-refusing and resume-refusing asserts exit 16, and the test fails when
  the two blocks in `protocol.run` are swapped.

## Phase 6: Repairs from the second review round

- [x] T046 - Make `resumable` keyword-only and required, and replace the tautological guard with an
  AST check (from security:SEC-005 and domain:DOM-018 — the same defect, one task, two identities).
  Covers: AC-002. Verify: `inspect.signature(_refuse).parameters["resumable"].kind` is
  `KEYWORD_ONLY` with no default; flipping one `STATE_UNRESUMABLE` call to `resumable=True` fails
  the suite (demonstrated).
- [x] T047 - Widen the `TASKS.md` handler to `(OSError, UnicodeDecodeError)` (from
  security:SEC-006). Covers: AC-002. Verify: a committed non-UTF-8 `TASKS.md` returns exit 10, not a
  traceback — the escape was reproduced before the fix.
- [x] T048 - Fail closed when a document states two different protocol versions (from
  security:SEC-007). Covers: AC-004. Verify: two disagreeing statements raise
  `UnknownProtocolVersion` naming both; a repeated identical value does not.
- [x] T049 - **Revert** DOM-013's repair and restore `main`'s dry-run behaviour (from
  domain:DOM-017, and superseding D011). Covers: AC-008. Verify: `--dry-run --backend claude
  --stub-script <path>` exits 0 with a plan, matching `main`; the same request without `--dry-run`
  still exits 14; the `dry-run-contradiction` transcript records the baseline; `PERMITTED_DIFFERENCES`
  still holds exactly one entry.
- [x] T050 - Refresh the AC-005 evidence to the measured tree (from domain:DOM-019). Covers: AC-005.
  Verify: `evidence/SUITE_AND_TEST_DIFF.md` states the count the suite currently reports, with the
  superseded figure kept visible and labelled.
- [x] T051 - Reconcile `RunLog.emit` with its docstring at the writer (second-round completion of
  security:SEC-004). Covers: AC-002. Verify: a `RunLog` pointed at an unwritable path returns its
  record, keeps the event in memory, appends to `write_failures`, and raises nothing.

## Phase 7: Repairs from the third review round

- [x] T052 - Guard every read the entry gate performs, not the last one added (from
  security:SEC-006, re-reported). Covers: AC-002. Verify: a committed non-UTF-8 `SPEC.md` returns
  exit 10 with a diagnostic, not a traceback — asserted by
  `test_outcome_and_logging.UnreadableInputsGetACodeNotATraceback`.
- [x] T053 - Give the lost-transcript signal a reader (from security:SEC-008 and domain:DOM-022).
  Covers: AC-002. Verify: a run whose `run.jsonl` cannot be appended to reports a diagnostic naming
  the loss; a run whose transcript is intact reports none.
- [x] T054 - Pin the two branches nothing exercised (from security:SEC-009). Covers: AC-004,
  AC-002. Verify: a document stating two different versions raises naming both, one stating the same
  value twice does not, and a non-UTF-8 `TASKS.md` returns exit 10.
- [x] T055 - Close T043 honestly, without presenting it as executed (from domain:DOM-020).
  Covers: AC-008. Verify: **all four** — T043 carries exactly `DEFERRED (2026-09-03) -> DEBT-011`
  and no other marker; `docs/KNOWN_DEBT.md` has a DEBT-011 row, a DEBT-011 section and a stated
  closing condition; T043's own `Verify:` clause attests the deferral and the preserved baseline
  (`--dry-run --backend claude --stub-script <path>` exits 0, as on `main`) rather than the original
  criterion the tree now deliberately fails; and AC-002 does not depend on the deferred work.
  **This clause replaces a false one.** It read *"T043's clause is struck through and names T049"*,
  which described the first attempt — the one that annotated T043 as `REVERTED`, a marker the TASKS
  template does not admit. The strikethrough is gone and the marker is `DEFERRED`, so the clause
  described a tree that no longer existed while the task stayed checked (`maintainer:MNT-002`).
- [x] T056 - Replace the two exemptions that cited absent coverage with the property that is really
  true (from domain:DOM-021). Covers: AC-006. Verify: `TheColumnDivergenceIsDeliberate` asserts the
  template's Attempts/Findings headers do **not** equal `policy`'s, and `FINDING_KEYS` is asserted
  against the skill's published verdict schema.

## Phase 8: Repair of a defect introduced by the round-3 repairs

- [x] T057 - Replace the inferred outcome disposition with a stated one (from
  `maintainer:MNT-001`, a defect introduced by T053). Covers: AC-002, AC-008. Verify: **all five** —
  `RunOutcome.loop_completed` is `True` only where `protocol.run` holds a `Loop.run()` return value;
  `ran` returns it and its AST contains no reference to `diagnostics`; a converged run whose
  `run.jsonl` cannot be appended to exits 0, prints `run result: DONE`, emits the incomplete-transcript
  diagnostic on stderr and delivers **exactly one** `run-finished` to a real `--notify` sink; an
  internal error still exits 70 with a diagnostic, no terminal report and no `run-finished`; and the
  mutation `loop_completed=True` → `False` turns the suite red.

## Phase 9: Repairs of defects in the record and the guards

- [x] T058 - Make T055's criterion describe the state the tree is actually in (from
  `maintainer:MNT-002`). Covers: AC-008. Verify: T055's four sub-criteria are each checkable against
  the tree today, and the history of the rejected `REVERTED` marker survives in T055, in T043 and in
  the findings registry rather than being edited away.
- [x] T059 - Prove the internal-error path emits no `run-finished`, through the adapter that owns
  the notifier (from `maintainer:MNT-003`). Covers: AC-002, AC-008. Verify: **all five** — a test
  forces `Loop.run()` to raise and executes `__main__.main()` with a real `--notify` sink; exit is
  70; the `[INTERNAL]` diagnostic is on stderr; `run result:` is absent from stdout; the sink
  receives **zero** `run-finished` events, *and* a companion test proves the sink is reachable at
  all by delivering exactly one event through the same code path. Plus a mutation removing
  `outcome.loop_completed` from the CLI's notify condition turns the suite red.

## Phase 10: Repairs from the fourth review round

- [x] T060 - Make an audit failure a fail-closed gate instead of a warning beside a success (from
  domain:DOM-023, with the maintainer's factual correction of its baseline). Covers: AC-002, AC-008.
  Verify: **all eight** — an unwritable `run.jsonl` yields exit 70, `ABORTED`, `loop_completed=False`,
  `resumable=False`, a redacted `[INTERNAL]` diagnostic with no traceback, no `run result:` line and
  zero `run-finished`; the loop stops at the first failed write with no delegation attempted after
  it; and a run with an intact log still converges and notifies.
- [x] T061 - Make the mutation evidence derive its claim from the table and its generator durable
  (from domain:DOM-024 and security:SEC-010 — the same defect, one task, two identities). Covers:
  AC-006. Verify: `evidence/mutation_harness.py` exists and runs from the repository root; the
  generated file states no positional claim; a second run does not restore the old sentence; the
  lessons file's total matches the table.
- [x] T062 - Restore one identity to one canonical repair task, recording the two deviations (from
  domain:DOM-025 and security:SEC-011). Covers: AC-006. Verify: every identity has exactly one row;
  `security:SEC-006` and `security:SEC-004` each name a canonical task and record the other as a
  task created outside the rule; `T051` and `T052` still exist and are not hidden.
- [x] T063 - Refuse a baseline that cannot be launched with a condition that names it (from
  security:SEC-012). Covers: AC-002. Verify: a `--baseline` naming a nonexistent binary returns exit
  10 with condition `baseline suite unavailable`, the observed argv quoted safely, a remediation
  naming the command, and no traceback.
- [x] T064 - Restate the PLAN's coverage item without a false range (from domain:DOM-026). Covers:
  AC-008. Verify: the item claims only that AC-001…AC-013 have explicit coverage and that each
  repair task carries its own `Covers:`, and names no task range.
- [x] T065 - Resolve identity to repair task from the registry, not from prose (from
  maintainer:MNT-004). Covers: AC-006. Verify: `registry_task_refs` parses only the registry's two
  structured columns; every identity in the registry resolves to a task that exists; a registry
  naming a missing task raises `BrokenRepairTaskReference` and the caller refuses without writing;
  a wrapped title, an optional namespace and a shared task all resolve; and three incidental prose
  mentions resolve to nothing.
  **Clause corrected 2026-09-04 (`security:SEC-014`).** It read *"a registry naming a missing task
  returns `None`"* — the contract this task shipped, which `maintainer:MNT-005` then proved unsafe
  and T066 replaced. A checked task must not state a criterion the tree deliberately fails; the
  superseded wording is named here rather than erased.

## Phase 11: Repairs of defects introduced by the round-4 repairs

- [x] T066 - Make a broken repair-task reference fail closed at the caller, not just the resolver
  (from `maintainer:MNT-005`). Covers: AC-006. Verify: a registry naming a task absent from
  `TASKS.md` raises `BrokenRepairTaskReference`; driven through `_schedule_repairs` it creates no
  task, leaves `TASKS.md` byte-identical, emits no `repair-task-created`, and refuses with a code.
- [x] T067 - Make the registry parser fail closed on a duplicate identity and on a multi-task cell
  (from `maintainer:MNT-006`). Covers: AC-006. Verify: two rows for one identity raise; a Repair
  task column naming two tasks raises; the column holds only `T031`/`T047` while `T051`/`T052`
  survive in Required action and D016.
- [x] T068 - Anchor the `(from …)` fallback to the logical header (from `maintainer:MNT-007`).
  Covers: AC-006. Verify: `(from SEC-006)` written inside a `Verify:` clause resolves to `None`.
- [x] T069 - Make the mutation harness fail when a mutation does not happen (from
  `maintainer:MNT-008`). Covers: AC-006. Verify: the harness requires exactly one anchor match per
  mutation and exits non-zero on any row that is not CAUGHT and on a red final suite; the
  regenerated evidence records **every row CAUGHT, 0 SKIPPED, 0 MISSED**; and its suite claim says
  "after all reverts", which is when the suite actually runs.
  ~~Superseded clause: "the regenerated evidence reads 16 CAUGHT, 0 SKIPPED, 0 MISSED".~~
  **Restated 2026-09-04 (`conformance:CONF-008`).** `16` was the row count when the clause was
  written and became false the moment CONF-006 added two mutations — a volatile total pinned inside
  the criterion of the task whose whole subject is a harness that must not report a figure it did
  not derive. The criterion is now the harness's behaviour and the table's internal consistency; the
  live count is `CONTRACT_MUTATIONS.md`, which the harness regenerates and derives.
- [x] T070 - Remove the claims earlier rounds left behind (from `maintainer:MNT-009`). Covers:
  AC-008. Verify: `test_golden_cli`'s docstring and its constants **agree with FR-009's
  `authorised-observable-differences` block**, compared by identifier rather than by count;
  `RunLog.emit`'s comment says the writer records and the loop decides; and the audit-gate test's
  name no longer claims a notification it does not install.
  ~~Superseded clause: "`test_golden_cli` states two authorised differences and its docstring's
  count matches its assertion".~~ **Restated 2026-09-04 (`conformance:CONF-008`).** The clause
  froze the membership at two while D018 was authorising a third, so the criterion for the task that
  removes stale claims had itself gone stale. It now names the structured list as the authority and
  states no number.
- [x] T071 - Keep a normalized retrospective artifact of `main`'s real output (from
  `maintainer:MNT-010`). Covers: AC-008. Verify: `evidence/golden/audit-unavailable.main.txt` holds
  the normalized `main` transcript, and a test asserts the two sides differ exactly as the
  authorised difference says.

## Phase 12: Repairs from the T025 final-conformance gate

- [x] T072 - Supersede D007's single-difference claim (from `conformance:CONF-001`). Covers: AC-008.
  Verify: D007 carries a dated supersession note pointing at D015 and FR-009's fenced block, with
  the original sentence struck and visible; no production change.
  ~~Superseded clause 1: "naming `DIFF-001` and `DIFF-002`".~~ Naming the members made this
  criterion a second copy of the list, and it went stale the moment D018 added `DIFF-003` — the
  defect CONF-001 was raised about, one document over.
  ~~Superseded clause 2: "The note now defers to FR-009's block and states no membership of its
  own".~~ **Restated 2026-09-04 (`conformance:CONF-008`).** That was not what the note does. D007's
  supersession note **keeps the historical provenance visible** — it names the identifiers in force
  at the time it was written, dated as such — and **delegates the binding membership to FR-009's
  `authorised-observable-differences` block**. Those are different claims, and asserting the
  stronger one made this criterion false against the very note it describes. What T077 verifies is
  the delegation, not an absence.
- [x] T073 - Restate the two `Verify:` clauses and the PLAN mitigation that the tree fails (from
  `conformance:CONF-002`). Covers: AC-008. Verify: T001, T019 and PLAN R1 each state a criterion
  checkable against the tree as it stands, with the superseded wording named rather than erased.
- [x] T074 - Cover every terminal condition `gate.check` can emit (from `conformance:CONF-003`).
  Covers: AC-008. Verify: the condition inventory is derived from `gate.py`'s AST, not assumed; every
  condition maps to a CLI transcript in `test_gate_refusal_coverage.COVERAGE`; each transcript
  carries its refusal, a remediation and exit 10, and replays byte-for-byte; no scenario builder
  calls `gate.check` directly; and the guard fails if a condition has no scenario.
- [x] T075 - Widen the AC-001 guard to all of `runner/` (from `conformance:CONF-004`). Covers:
  AC-001. Verify: the walk reaches `runner/tests` and `runner/sdd_runner/backends`, excludes only
  `__pycache__` and `policy.py` itself, and asserts positively that exactly one file defines each
  canonical constant.
- [x] T076 - Execute the battery and persist it (from `conformance:CONF-005`). Covers: AC-004,
  AC-005, AC-006, AC-008, AC-009, AC-013. Verify: `evidence/EXECUTED_BATTERY.md` records each
  command, its exit code, its relevant output and the tree fingerprint it ran against, and T025's
  closure states that the first conformance pass was documentary.
- [x] T077 - Give the ten CONF-003 gate conditions a real `main` side, and register what it found
  (from `conformance:CONF-006`). Covers: AC-008. Verify: the ten scenarios ran through `main`'s real
  CLI from a temporary extraction, with no checkout, reset or change to the working tree; each
  `evidence/golden/<scenario>.main.txt` carries its condition, the `main` commit, the reproducible
  command, the fixture and the normalization applied, and declares itself retrospective;
  `evidence/golden/index.json` records the same provenance structurally and its digests match the
  files on disk; **nine** conditions reproduce `main` byte-for-byte and the tenth differs only as
  `DIFF-003`; `DIFF-003` is an entry in FR-009's block naming D018, and D018 is `Accepted`;
  `test_main_baselines` fails if a side is missing, if the provenance commit moves without a
  regeneration, if one of the nine stops matching, if the tenth differs otherwise, if a fourth
  difference appears, or if `DIFF-003` leaves FR-009 or D018; D007 and `golden.py` state the real
  provenance split of the corpus instead of implying T001 captured all of it; no production change.
- [x] T078 - Say five conditions and four scenarios wherever the two were conflated (from
  `conformance:CONF-007`). Covers: AC-008. Verify: T001's restated clause, PLAN R1,
  `test_gate_refusal_coverage`'s docstring and `test_golden_cli`'s module docstring each state
  **5 of 15 conditions carried by 4 scenarios** and name `refusal-adopt-not-needed` as the scenario
  reaching two; D007's `each gate refusal` clause is struck and annotated rather than left standing;
  `DEBT-013` item 2 is marked resolved against the vocabulary the rows actually use; every superseded
  figure stays visible; no production change.
- [x] T079 - Take the volatile totals and the fixed enumerations out of the `Verify:` clauses that
  own AC-006 and AC-008 (from `conformance:CONF-008`). Covers: AC-006, AC-008. Verify: T019, T069,
  T070 and T072 each state a criterion that **derives** its membership or its total from the
  structured source rather than restating it — T019 and T070 from FR-009's
  `authorised-observable-differences` block by identifier, T069 from the harness's behaviour (every
  row CAUGHT, 0 SKIPPED, 0 MISSED, non-zero exit on any other result) instead of a row count, and
  T072 from what D007's note actually does (keeps the historical provenance, delegates the binding
  membership); T001's restatement dates its corpus figure instead of stating one in the present
  tense; every superseded wording stays struck and visible (D013); and no clause among those that
  cover AC-008 or name a difference, transcript, scenario, condition or mutation verdict pins a
  figure a structured source can move. No production change.

## Phase 13: Repairs from the final T025 retry

- [x] T080 - Authenticate the complete reviewable tree in the executed-battery fingerprint (from
  `conformance:CONF-009`). Covers: AC-005, AC-006. Verify: the documented path set is the union of
  `main...HEAD`, tracked working-tree changes against `HEAD`, and sorted untracked paths; it excludes
  only the self-referential battery artifact, includes production files and tests, and its recorded
  path count and digest reproduce on the current tree.
- [x] T081 - Make the CLI consume the package's public interface (from
  `conformance:CONF-010`). Covers: AC-003, AC-011. Verify: `__main__.py` imports `run` and
  `RunRequest` from the package root, never imports `protocol`, and the no-whitelist AST guard fails
  if any imported name is absent from `sdd_runner.__all__`.
- [x] T082 - Make the public-lifecycle proof use only the two names AC-007 permits (from
  `conformance:CONF-011`). Covers: AC-007. Verify: the module imports exactly `run` and
  `RunRequest` from `sdd_runner`; its protocol-version assertion derives the value from the public
  `RunOutcome` returned by `run`, and the AST guard checks the exact import set.
- [x] T083 - Remove live copies of FR-009's difference count from known debt (from
  `conformance:CONF-012`). Covers: AC-008. Verify: DEBT-011 preserves the dated historical context
  but delegates current authorisation to FR-009, and DEBT-012 names the structured list without
  restating its size.

## Coverage map

| AC | Tasks |
|---|---|
| AC-001 | T002, T003 |
| AC-002 | T006, T007, T008, T010, T024 |
| AC-003 | T006, T008, T023 |
| AC-004 | T004, T005 |
| AC-005 | T007, T020, T026 |
| AC-006 | T015, T016, T018, T023 |
| AC-007 | T011, T017 |
| AC-008 | T001, T011, T019, T026 |
| AC-009 | T014, T021, T024 |
| AC-010 | T013 |
| AC-011 | T009 |
| AC-012 | T012 |
| AC-013 | T022 |
