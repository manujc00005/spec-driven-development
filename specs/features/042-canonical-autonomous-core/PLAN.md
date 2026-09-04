# Implementation Plan: canonical-autonomous-core

## Summary

Turn the existing `runner/sdd_runner/` package into the **single executable authority** for the
autonomous protocol, reachable through `run(RunRequest) -> RunOutcome`, without changing observable
behaviour.

Three moves, in order:

1. **Collect the vocabulary.** Every protocol constant scattered across nine modules becomes a typed
   value in one `policy` module; the modules that own behaviour import it instead of defining it.
2. **Raise the interface.** A new `protocol` module absorbs the protocol decisions currently living
   in `__main__.py` — first-entry determination, resume-authentication ordering, budget computation,
   backend resolution — and exposes one function plus five value types. `__init__.__all__` becomes
   the public surface; everything else is internal.
3. **Nail it down.** Contract tests check the core against the nine surfaces that state protocol
   values in prose, and golden CLI transcripts prove byte-identical behaviour across the refactor.

The package is **not renamed** (D001), so the 276 tests keep their imports and the diff a reviewer
must read is the refactor itself rather than 21 files of import churn.

## Related spec

[`specs/features/042-canonical-autonomous-core/SPEC.md`](SPEC.md)

## Impacted areas

| Area | Change |
|---|---|
| `runner/sdd_runner/__init__.py` | Gains `__all__` (the public surface) and the corrected authority statement |
| `runner/sdd_runner/policy.py` | **New.** Every protocol constant, typed, defined once |
| `runner/sdd_runner/protocol.py` | **New.** `run`, `RunRequest`, `RunOutcome`, `GateResult`, `RunPlan` |
| `runner/sdd_runner/seams.py` | **New.** The three declared seams, no implementation |
| `runner/sdd_runner/__main__.py` | Reduced to argv → `RunRequest` → `run` → render → exit |
| `exits`, `state`, `gate`, `loop`, `blocks`, `escalation`, `budget`, `resume` | Constants re-homed to `policy`; behaviour untouched |
| `runner/sdd_runner/state.py` | `Protocol version` header: write, read, version refusal |
| `runner/tests/contract/` | **New.** Nine surface tests + the over-reach guard + golden CLI |
| `runner/tests/conformance/PROTOCOL_TRANSCRIPTION.md` | Module references updated to survive the move |
| `skills/sdd-orchestrate/SKILL.md` + `templates/ORCHESTRATION.md` | Authority statement; `Protocol version` line |
| `runner/README.md`, `runner/pyproject.toml` | Authority statement; package declaration |
| `install.sh`, `install.ps1`, `profiles.json`, `check-consistency.sh` | **Untouched** (D006) |
| `docs/AUTONOMOUS_SDD_FEATURE_PROMPT.md` | **Untouched**, sha256 recorded in `evidence/` |

## Context budget

### Reading list

Bounded to what the refactor touches. No whole-repo scan; no unrelated spec.

- `specs/features/042-canonical-autonomous-core/*` — the active feature folder.
- `runner/sdd_runner/*.py`, `runner/sdd_runner/backends/*.py` — 3 957 lines, all of it in scope.
- `runner/tests/**` — read on demand, per test file being rewired; never all 21 at once.
- `runner/tests/conformance/PROTOCOL_TRANSCRIPTION.md`, `runner/README.md`, `runner/pyproject.toml`.
- The nine FR-012 surfaces, **only the lines stating a protocol constant** — located by grep, not by
  reading each file whole: `skills/sdd-orchestrate/SKILL.md`,
  `skills/sdd-orchestrate/templates/ORCHESTRATION.md`, `docs/SDD-ORCHESTRATION.md`,
  `agents/domain-reviewer.md`, `agents/final-conformance-reviewer.md`, `adapters/codex/PARITY.md`,
  `evals/scenarios/orchestrate-per-finding-counter.md`.
- **Read-only, never edited:** `specs/features/031|032|033|040|041/**` — consulted for a decision's
  provenance and nothing else. The 032 and 033 `ORCHESTRATION.md` files are test fixtures; a change
  to either is a defect.

Explicitly **out** of the reading list: the twelve review skills of FR-012a (their severity strings
are report vocabulary, not protocol), `skills/` at large, `hooks/`, `evals/` beyond the one scenario
named above, and every spec folder not listed.

### Model routing

| Phase | Model | Justification |
|---|---|---|
| Constant inventory (T002) | cheap/mechanical | Grep and tabulate. No judgement. |
| `policy` extraction (T003) | cheap/mechanical | Moving constants; the compiler and 276 tests are the oracle. |
| Interface design (T006–T010) | **deep-reasoning** | Where the seam falls decides whether the module is deep or merely split. Getting `RunOutcome`'s boundary wrong leaks internals and fails AC-002. |
| Version compatibility (T004–T005) | **deep-reasoning** | Fail-closed semantics on a durable artifact; a wrong default silently strands a resumable run. |
| CLI reduction (T008) | cheap/mechanical once the interface exists | Deleting code that moved. |
| Contract tests (T015–T019) | cheap/mechanical | Comparisons against an enumerated list. |
| Review gates | per trigger | See Test strategy. |

No Graphify report is needed: the impacted surface is one 3 957-line package the plan already
enumerates file by file.

## Proposed approach

**Step 0 — freeze the observable behaviour before touching it (T001).** Record, for ten scenarios,
the exit code and the exact stdout/stderr of `python3 -m sdd_runner` as it behaves *today*. These
transcripts are the oracle for AC-008: any later difference is a regression until a decision says
otherwise. Nothing can be refactored safely before this exists, so it is the first task.

**Step 1 — one vocabulary (T002–T003).** Inventory every protocol constant and its current single
definition site, then move them into `policy`. The existing modules import from `policy` and define
none of their own, so "defined exactly once" (AC-001) becomes structurally true rather than
asserted. A test enumerates `policy`'s names and fails if any is re-defined under `runner/`.

**Step 2 — the durable version (T004–T005).** `PROTOCOL_VERSION = 1` is stamped into
`ORCHESTRATION.md` on create and preserved on save. Absent reads as 1; unknown or malformed refuses
fail-closed naming both the version read and the version supported. The two real phase-1 artifacts
must still round-trip byte-identically, which pins the write path to *additive only*.

**Step 3 — the interface (T006–T011).** `RunRequest` takes over validation from the CLI, `GateResult`
and `RunPlan` become value types, and `run()` absorbs the four protocol decisions currently in
`__main__.py`. `__main__.py` is then reduced until it holds argv parsing, rendering and the exit
call — and a test asserts it imports nothing but the public names. This is the step where the module
becomes deep: the complexity does not move, it goes *behind* a face of ≤ 12 names.

**Step 4 — say who is in charge (T012–T014).** `runner/README.md` and `sdd_runner/__init__.py`
currently state the inverse of this feature's premise — *"Where this runner and
`skills/sdd-orchestrate/SKILL.md` disagree, THIS RUNNER IS WRONG"*. That sentence is corrected in
both places and in the skill, and a test asserts no surviving text reasserts the old ownership.
The three seams are declared in one module with no implementation.

**Step 5 — make divergence impossible to add (T015–T020).** Nine contract tests, one per surface,
each reading the enumerated surface list rather than searching the repository (FR-012a). Each is
demonstrated failing under a deliberate mutation, and the mutation is reverted and recorded.

**Order matters and is not negotiable:** golden transcripts before any refactor (or AC-008 has no
oracle); `policy` before `protocol` (or the interface re-imports scattered constants and the
duplication survives behind a nicer face); contract tests last (or they pin the pre-refactor shape).

## Alternatives considered

**A rename to `sdd_protocol`, with `sdd_runner` reduced to a CLI adapter** — the spelling SPEC A-001
recommended. **Rejected (D001).** The inventory found 21 test files importing `sdd_runner`
submodules across 18 distinct import lines. A rename makes every one of them change, and AC-005's
protection — *"a reviewer must be able to see the assertion-level diff is import-only"* — becomes
unreviewable in exactly the diff where it matters most. Depth is produced by `__all__` and by what
the interface hides, not by the package's name. The better word is not worth the one criterion that
guards the 276 tests.

**Generating the normative prose from the executable contract.** Rejected in SPEC A-003 and
unchanged here: it would make `/sdd-orchestrate` unreadable to its actual consumers (humans and
agents), and validation already has a working precedent in `test_transcription.py`.

**A `Protocol` abstract base class with `stub`/`claude`/`codex` implementations behind it.**
Rejected: `Backend` already is that seam and already has three implementations. A second abstraction
over it would be the hypothetical abstraction the SPEC forbids.

**Deleting `closure.classify/observe/unexpected` as dead code.** Rejected (SPEC A-010): found dead
code, not created. It is the Finalizer's pre-written half; removing it belongs to that spec.

**Skipping the golden transcripts and relying on the 276 tests for AC-008.** Rejected: the suite
tests the loop's behaviour, not the CLI's *rendering*. FR-007 requires byte-identical dry-run output,
and no current test asserts a byte of it.

## Dependencies

None new. Python ≥ 3.11 stdlib only; `unittest`, no `pytest`, no network, no provider. The Agent SDK
stays optional and lazily imported; the Codex CLI stays gated. Every task must pass on a machine with
neither installed.

## Risks

| ID | Risk | Mitigation |
|---|---|---|
| R1 | A "no behaviour change" refactor changes behaviour nobody was asserting | T001's golden transcripts, captured before the first edit, over the whole recorded corpus — including one scenario per terminal condition `gate.check` can emit, verified by a matrix derived from the gate's own AST (`test_gate_refusal_coverage`). *The original mitigation said "ten scenarios including every refusal path"; the corpus has grown and it never covered every refusal path — **five of fifteen conditions, carried by four scenarios** (`refusal-adopt-not-needed` reaches two) — until CONF-003 was repaired. The figure read "four of fifteen conditions", which was the scenario count wearing the condition label (CONF-007).* |
| R2 | Constants get *copied* into `policy` instead of *moved*, leaving two definitions | T003's test enumerates `policy` and greps `runner/` for a second definition of each name |
| R3 | Contract tests written by grep instead of by list, so they fail on the twelve review skills and get weakened | FR-012a is its own task (T016) with its own criterion; the guard asserts the tests read the list |
| R4 | Rewiring 21 test files quietly weakens an assertion to keep the count | AC-005 forbids it; T020 verifies the test diff is import-only, and the count is a floor (≥ 276), not a target |
| R5 | The `Protocol version` line breaks byte-identical round-trip of the 032/033 fixtures | T004's criterion is the round-trip itself; the write path is additive-only by construction |
| R6 | The interface leaks an internal, so "deep module" is cosmetic | T010 walks `RunOutcome`/`GateResult` recursively and fails on any internal type |
| R7 | Scope creep: the refactor "improves" a gate, cap or safety rule in passing | Every such change is forbidden by SPEC Non-goals unless a contradiction is demonstrated in writing and recorded as a decision |
| R8 | The preserved untracked file is moved or edited by a mechanical pass | Its sha256 is recorded in `evidence/PRESERVED_FILE_BASELINE.txt` and re-checked in T022 |

## Test strategy

- **Unit** — `policy` single-definition; `RunRequest` validation (path containment including the
  symlink and `features-old` cases, contradictory fields, cap overrides, unknown backend);
  `RunOutcome`/`GateResult` leak-freedom; protocol-version absent/unknown/malformed.
- **Integration** — the eight existing integration modules, assertions untouched; a full scripted
  `stub` run through `run(RunRequest)` for start, pause, abort, resume and core-complete.
- **Contract** — nine surface tests, the over-reach guard, the updated
  `PROTOCOL_TRANSCRIPTION.md` guard, and the golden CLI comparison.
- **Regression** — the whole suite, `Ran N tests` with N ≥ 276 and `OK`, on a machine with neither
  the Agent SDK nor the Codex CLI.
- **Manual** — `python3 -m sdd_runner --feature specs/features/042-… --dry-run`;
  `bash scripts/check-consistency.sh` exit 0; `git diff --stat main -- install.sh install.ps1
  profiles.json` empty; `git status --porcelain` shows the preserved file still `??` at its recorded
  sha.
- **Review gates.** `domain-reviewer` on every implemented diff. `security-reviewer` is evaluated
  against the Level-3 trigger list and, on the evidence available at planning time, **is expected to
  trigger**: the feature touches path containment, the `--notify` argv boundary, secret redaction in
  `log.py`, and fail-closed control results. T024 records the evaluation rather than assuming it.
  Then `final-conformance-reviewer`, `/spec-review`, `/qa-review`, `/spec-close`, `/pr-description`.

## Rollback strategy

> **This section contradicted the SPEC and has been rewritten. See D010.** Its earlier form
> mandated "every task is a separate commit", which `SPEC.md`'s Non-goals forbid: *"`git commit`,
> `git push`, `git merge`, real migrations, or any change to secrets."* The contradiction was
> written into the PLAN, missed by the `/spec-analyze` pass, and then acted on. What follows is the
> rollback that is actually consistent with the SPEC; the commits that were nonetheless made are
> recorded as a deviation in D010, not retroactively authorised here.

Two layers, cheapest first:

1. **Working tree.** Every change this feature makes is confined to `runner/`, the four protocol
   surfaces it corrects, and its own feature folder. Discarding the working tree restores the
   previous state; no build artefact, cache or generated file has to be cleaned up first.
2. **The branch.** `main` is never written to. Deleting `feature/042-canonical-autonomous-core`
   removes the feature entirely, and AC-009's byte-identity check means nothing downstream can have
   drifted in the meantime.

**The durable artifact.** The only persisted change is the additive `Protocol version` line. A
reverted core reads a file carrying it and ignores an unknown field; a file without it reads as
version 1 by FR-010. Rollback therefore strands no resumable run in either direction.

No migration, no data, no deployment, no feature flag needed.

## PLAN verification checklist

- [x] The plan covers all acceptance criteria. AC-001…AC-013 each have explicit coverage: the
      Coverage map in TASKS.md maps every criterion to the implementation tasks that satisfy it,
      and every repair task added since carries its own `Covers:` clause, so coverage is stated
      per task rather than by a range. **No range is claimed here**: an earlier version of this
      item said the map "spans T001…T045", which was false in both halves — the map's highest id
      is T026 and the task list runs past it (`domain:DOM-026`).
- [x] The plan avoids behavior outside the spec. (Non-goals restated as R7; no gate/cap/safety
      change; the Rollback section no longer orders commits.) **This item read `NO` while the
      Rollback section still mandated per-task commits. That section was rewritten, so the
      checklist now describes the plan as it stands — the commits that were made under the old
      wording remain recorded as a deviation in D010, which is not amended.**
- [x] The Context budget section is filled (reading list + model routing), not left as placeholder.
- [x] Risks are documented. (R1…R8, each with a mitigation owned by a task)
- [x] Test strategy is documented.
- [x] Rollback strategy is documented.
- [x] SPEC.md status has been updated to `Ready`.
