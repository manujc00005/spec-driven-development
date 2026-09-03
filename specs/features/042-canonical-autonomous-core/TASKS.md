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
  on an unmodified tree reproduces all ten byte-for-byte.
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
  Verify: all ten scenarios match byte for byte except the `Protocol version` line of FR-009, and the
  test names that line as the sole permitted difference.
- [x] T020 - Run the full suite and confirm the test diff is import-only. Covers: AC-005. Verify:
  `Ran N tests` with `N >= 276` and `OK` on a machine with neither the Agent SDK nor the Codex CLI,
  and `git diff main -- runner/tests` shows no changed line inside an `assert*` call.

## Phase 4: Review

- [ ] T021 - Confirm installer and manifest byte-identity. Covers: AC-009. Verify:
  `bash scripts/check-consistency.sh` exits 0 and
  `git diff --stat main -- install.sh install.ps1 profiles.json` is empty.
- [ ] T022 - Confirm the preserved file is untouched. Covers: AC-013. Verify:
  `git status --porcelain docs/AUTONOMOUS_SDD_FEATURE_PROMPT.md` shows `??` and its `shasum -a 256`
  equals the value recorded in `evidence/PRESERVED_FILE_BASELINE.txt`.
- [ ] T023 - `domain-reviewer` on the full implemented diff. Covers: AC-003, AC-006. Verify: an
  APPROVE verdict block for the current fingerprint, or every REJECT finding repaired and re-approved.
- [ ] T024 - Evaluate the Level-3 security triggers against the real diff and record the evaluation;
  run `security-reviewer` if triggered. Covers: AC-002, AC-009. Verify: the evaluation is written
  down naming which triggers matched (the PLAN expects path containment, the `--notify` argv
  boundary, `log.py` redaction and fail-closed control results to match), and an APPROVE verdict
  block exists if it ran.
- [ ] T025 - `final-conformance-reviewer` once over the full evidence chain. Covers: AC-001…AC-013.
  Verify: an APPROVE verdict block citing each acceptance criterion against its task and evidence.
- [ ] T026 - `/spec-review` then `/qa-review`. Covers: AC-005, AC-008. Verify: `/spec-review` returns
  Pass and sets `In Review`; `/qa-review` reports no unaddressed regression.
- [ ] T027 - `/spec-close` then `/pr-description`. Covers: AC-001…AC-013. Verify: `/spec-close` sets
  `Done` and `PR_DESCRIPTION.md` exists with acceptance-criterion-to-evidence traceability.

## Phase 5: Repairs from review

- [ ] T028 - Make `Protocol version` readable by the core wherever a surface states it, and replace
  the substring guard with one that parses (from security:SEC-001). Covers: AC-004, AC-006.
  Verify: `state.Orchestration.loads(<the template's text>).protocol_version()` returns
  `policy.PROTOCOL_VERSION`, and mutating the template's value to `2` fails the guard.
- [ ] T029 - Pass `resumable` explicitly on every pre-loop refusal (from security:SEC-002). Covers:
  AC-002. Verify: a test asserts `RunOutcome.resumable is False` for exit 16 via **both** routes —
  `_authenticate_reentry` and `loop.run` — and for the internal-error path.
- [ ] T030 - Add the sibling-prefix containment test (from security:SEC-003). Covers: AC-002.
  Verify: a feature folder planted at `specs/features-old/900-fixture` is refused, and the test
  fails when `protocol.resolve_feature`'s `commonpath` check is mutated to `startswith`.
- [ ] T031 - Redact the internal-error diagnostic and guard its log write (from security:SEC-004).
  Covers: AC-002. Verify: a test asserts a secret in an exception message reaches neither stderr nor
  `run.jsonl`, and that a failing `log.emit` still exits 70 rather than raising.
- [ ] T032 - Define `REFUSED` and `PLANNED` in `policy` (raised adjacent to security:SEC-002).
  Covers: AC-001. Verify: `test_policy.SingleDefinition` sees them, and `protocol.py` assigns
  neither at module level.

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
