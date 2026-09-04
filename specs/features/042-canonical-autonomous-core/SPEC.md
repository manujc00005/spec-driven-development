# Feature Spec: canonical-autonomous-core

## Status

Done

## Problem

The autonomous orchestration protocol has **three overlapping authorities** and no single
executable definition:

1. `skills/sdd/SKILL.md` (138 lines) — routes a feature into the lifecycle and stops before
   implementation. It names the loop (`/sdd-orchestrate --autonomous <path> --adopt`) but knows
   nothing about its contract.
2. `skills/sdd-orchestrate/SKILL.md` (565 lines) — carries the protocol **in prose**: the six/seven
   entry conditions, the verdict and completion block schemas, the three convergence counters, the
   escalation classifier, the durable state contract, the termination/abort contract.
3. `runner/sdd_runner/` (3 957 lines, 276 tests) — implements a **part** of the same protocol as
   code, while declaring itself subordinate: "Where this runner and `skills/sdd-orchestrate/SKILL.md`
   disagree, **this runner is wrong**" (spec 040 D007). It stops at `CORE-COMPLETE`.

Three consequences, all observable today:

- **The prose is the authority and the prose cannot be executed.** A rule can only be checked
  against the runner by a hand-written mapping table
  (`runner/tests/conformance/PROTOCOL_TRANSCRIPTION.md`, 44 rows) plus a guard that asserts the
  table has not rotted. That guard is explicitly weaker than a real comparison: spec 040 D008
  records R1 as "PARTIALLY mitigated, not eliminated", because there is **no injection point** for
  driving the skill's Agent-tool delegations from a fixture.
- **Protocol rules are duplicated into the CLI.** `runner/sdd_runner/__main__.py:130-175` decides
  first-entry versus re-entry, orders resume authentication against the gate, and computes the
  delegation budget (`default_cap`) — all of them normative rules of spec 031, living in an
  argument-parsing module. `__main__.py:184-199` re-renders the dry-run plan from protocol values.
  A second adapter (a skill, an in-process caller) must either re-derive those rules or diverge.
- **Divergences are found late and by accident.** D011 (severity vocabulary) was found by the
  transcription guard on its first run — after `specs/features/033-.../ORCHESTRATION.md` had already
  recorded `blocker`/`major`/`minor` rows against a closed enum. `loop.Loop._lifecycle_step`
  survived in the mapping table for a day after the method was deleted (D046).

The naming layer is contradictory too. `docs/PROVIDER_ADAPTERS.md` already defines **"SDD Core"** as
the provider-neutral *workflow* layer (specs lifecycle, review gates, skill contracts, agent roles)
and **"adapter"** as *provider packaging* (`adapters/claude`, `adapters/codex`). The protocol
executor is neither of those things and currently has no name at all.

## Goal

One **executable, provider-neutral module** that is the single authority for the autonomous
protocol — gates, states, persistence, resume, budgets, convergence and freeze — reachable through a
small public interface:

```python
run(RunRequest) -> RunOutcome
```

Everything that runs the protocol becomes a caller of that interface or a **projection** of its
contract: the CLI, `/sdd`, `/sdd-orchestrate`, and the `stub`/`claude`/`codex` backends.
`ORCHESTRATION.md` stays the durable authority for an individual run, and gains a
`protocol_version` so a future contract change is detectable rather than silent.

**Observable behaviour does not change**, apart from the exceptions FR-009 enumerates. This is an
architectural refactor: the same exit codes, the same refusal condition names, the same gate
ordering, the same loop outcomes, apart from the `authorised-observable-differences` block FR-009
carries — the single place any of them is listed or counted.

## Non-goals

Explicitly out of scope, and no task in this feature may touch them:

- Making `/sdd` autonomous by default, or changing which workflow `/sdd` recommends.
- Creating git worktrees automatically. Worktree and permission-mode setup remain caller concerns.
- Driving the flow from a free-form request through to implementation (autonomous entry).
- Enabling a real provider. `claude` stays optional/lazy, `codex` stays gated behind
  `--allow-unverified-backend` and [[DEBT-001]] / [[DEBT-002]].
- QA, lifecycle closure, the closure delta over lifecycle-skill writes, or `PR_DESCRIPTION.md` —
  the Finalizer's scope (spec 040 D034 §1, §6).
- Changing any gate, cap, trigger list or safety rule, **except** where a contradiction between the
  three authorities is demonstrated in writing and resolved by a recorded decision.
- Deleting `/sdd-orchestrate --autonomous`, the `python3 -m sdd_runner` invocation, any CLI flag, or
  any current exit code.
- **The autonomous runner does not create commits, push, merge, or open pull requests**, and
  this feature adds no code that does. Also out of scope: real migrations and any change to
  secrets.

  **Clarified 2026-09-04 (`conformance:CONF-008`).** The line read *"`git commit`, `git push`,
  `git merge`, real migrations, or any change to secrets"* under a heading saying no task may
  touch them, which reads as a blanket ban on the maintainer committing at all — and D010 was
  written on that reading, recording the branch's own history as an unauthorised deviation.
  The Non-goal is about **what the runner does**, not about how the maintainer manages their
  own branch: the maintainer's ordinary commits, outside the runner's behaviour, were never in
  scope here. D010 stays on the record unamended — it is the honest account of what was
  believed at the time, and D013's rule is that the history stays legible.
- Modifying `docs/AUTONOMOUS_SDD_FEATURE_PROMPT.md` (untracked working-tree file, preserved as-is).
- **Making `--dry-run` validate backend-exclusive options.** A dry run resolves no backend, so it
  accepts combinations the real run refuses (`--dry-run --backend claude --stub-script <path>` exits
  `0` with a plan; the same request without `--dry-run` exits `14`). That asymmetry is `main`'s
  behaviour and AC-008 requires it to survive. It was briefly changed during review repair and
  reverted; the decision recording the attempt is D011 (**Superseded**). A follow-up feature may
  make the dry run answer exactly as the real run does — it needs its own transcripts and its own
  acceptance criterion, because it changes observable output on purpose.

## Users / Actors

| Actor | Interaction |
|---|---|
| **Maintainer** | Runs `python3 -m sdd_runner --feature ... --backend stub`, reads refusals and `ORCHESTRATION.md`, answers escalations. |
| **Orchestrating session** (Claude or Codex reading `/sdd-orchestrate`) | Follows the protocol as prose; must not contradict the core. |
| **`/sdd`** | Routes a feature into the lifecycle and names the loop's entry command. |
| **CLI adapter** (`sdd_runner.__main__`) | Parses argv, calls the core once, renders the outcome, returns an exit code. |
| **Backend adapters** (`stub`, `claude`, `codex`) | Execute one agent session; never interpret protocol rules. |
| **Contract tests** | The mechanical reader of every normative rule across core, CLI, skill and docs. |
| **Future features** (autonomous entry, real providers, Finalizer) | Consume the declared seams; not implemented here. |

## Current behavior

- `python3 -m sdd_runner` resolves the feature path, decides `first_entry` from the existence of
  `ORCHESTRATION.md`, authenticates a re-entry via `resume.inspect`, calls `gate.check`, computes
  `default_cap(len(pending))`, resolves a backend, constructs `Loop`, and calls `Loop.run()`, which
  returns a `loop.Outcome(code, result, reason, resumable, escalations, remediation)`.
- Protocol constants are spread across modules: `exits.OK…INTERNAL_ERROR` and `exits.NAMES`;
  `state.RUN_RESULTS`, `state.LIFECYCLE`, the four `*_COLUMNS` lists; `gate.READY_STATUSES`,
  `ADOPT_STATUSES`, `REENTRY_STATUSES`, `KNOWN_STATUS_WORDS`, `RUN_ARTIFACTS`, the refusal-name
  constants; `loop.REVIEWERS`, `READ_ONLY_AGENTS`, `CORE_COMPLETE`, `AGENT_FILES`,
  `SECURITY_TRIGGERS`; `blocks.SEVERITIES`, `blocks.FINDING_KEYS`; `escalation.HUMAN_GATED`;
  `budget.default_cap`.
- A caller wanting a run must import from at least six modules (`gate`, `resume`, `state`, `budget`,
  `tasks`, `backends`, `log`, `loop`) and reproduce the CLI's ordering to get the same answers.
- `ORCHESTRATION.md` carries no version field. Its shape is defined by
  `skills/sdd-orchestrate/templates/ORCHESTRATION.md` and enforced by `state.Orchestration`.
- The suite is 276 tests, `unittest` only, no third-party dependency, ~91 s on the maintainer's
  machine. `scripts/check-consistency.sh` exits 0. The runner is **not installed** by
  `install.sh`/`install.ps1`, is absent from `profiles.json` and from `check-consistency.sh`
  (spec 040 D001, AC-014).

## Desired behavior

A caller — CLI today, another adapter later — does this and nothing else:

```python
from <canonical-module> import run, RunRequest

outcome = run(RunRequest(
    repo=..., feature="specs/features/042-...", backend="stub",
    entry="adopt", max_iterations=3, max_delegations=None,
    baseline=[...], dry_run=False, notify=..., stub_script=...,
))
# outcome.exit_code, outcome.result, outcome.reason, outcome.remediation,
# outcome.resumable, outcome.escalations, outcome.gate, outcome.plan,
# outcome.protocol_version
```

The core owns, in one place: request validation, feature-path containment, first-entry versus
re-entry, resume authentication ordering, the entry gate, budget computation, backend resolution,
the loop, freeze, and the terminal result. The CLI owns argv, stdout/stderr formatting, and the
process exit code — nothing else.

**A dry run resolves no backend, and therefore validates no backend-exclusive option.**
`--dry-run` dispatches nothing, so it never reaches backend resolution; options that only mean
something to a particular backend — `--stub-script` against `--backend claude` is the live example —
are validated where the backend is resolved, on the real run. This is the behaviour on `main` and
this feature preserves it. It is stated here because it looks like an omission and is not: a dry
run has no backend to contradict, and making it refuse anyway would widen observable behaviour for
a request that was never going to dispatch. Tightening that validation so a dry run answers exactly
as a real run would is a **follow-up, out of scope here** — see Non-goals.

Every normative rule (state names, gate conditions, caps, severities, escalation domains, reviewer
triggers, fingerprint inclusion, run artifacts, exit codes) is a typed value in **one** policy
module, and the contract tests read that module to check the skill, the CLI, the templates and the
docs against it.

`ORCHESTRATION.md` gains one header line, `Protocol version`, written by the core. A file without
it reads as version `1` — the same read-compatibility rule spec 041 D007 already established for a
missing `Entry` line.

## Functional requirements

**Module and interface**

- **FR-001:** A single Python package is the executable authority for the autonomous protocol. Every
  state name, gate condition, cap rule, escalation domain, reviewer trigger, verdict/severity
  vocabulary, fingerprint inclusion rule, run artifact name, run result and exit code is defined
  **exactly once**, inside it. No duplicate definition may exist in the CLI, in a backend, or in a
  test fixture.
- **FR-002:** The package exposes `run(RunRequest) -> RunOutcome` as its entry point. A caller
  needing to start, resume, adopt or dry-run a feature imports only the package's public names.
- **FR-003:** `RunRequest` is a validated value type covering every input the CLI accepts today:
  repository root, feature path, backend name and its options, entry mode (`ready` | `adopt`), cap
  overrides, baseline command, notification sink, dry-run flag, unverified-backend flag. Validation
  — including feature-path containment inside `specs/features/` through resolved real paths — is
  performed by the core, not by the caller.
- **FR-004:** `RunOutcome` is a value type carrying the run result, exit code, reason, remediation,
  resumability, open escalations, the `GateResult`, the dry-run plan when requested, the protocol
  version, any `Diagnostic`s, and **`loop_completed`**. It **leaks no internal object**: no `Loop`,
  no `Orchestration`, no `Backend`, no `CounterState`, no open file handle.
- **FR-004a — disposition and diagnostics are independent facts, and both are stated.**
  `loop_completed` says whether `Loop.run()` returned normally with a reportable terminal result.
  `diagnostics` say something went wrong alongside the invocation. **Neither may be derived from the
  other**, and no adapter may infer one from the other. A caller decides whether to report a
  terminal result from `loop_completed` alone.

  This is a contract change, made because the alternative had already failed: the disposition was
  *inferred* as "terminal result and no diagnostics", which held only while diagnostics accompanied
  refusals. The moment a converged run carried one — its `run.jsonl` writer losing events — a
  `DONE`/exit-0 run stopped printing its result and stopped emitting `run-finished`, leaving a
  scheduler waiting on an event that never arrived (D012, `maintainer:MNT-001`).

  `loop_completed` is `False` for preflight refusals, containment failures, `--dry-run`, and the
  internal-error path. **It is not `execution_started`**: an exception may be raised after the loop
  begins, and the baseline prints no terminal result and sends no `run-finished` in that case.
- **FR-005:** `GateResult` is a structured, fail-closed value: a boolean pass, plus the ordered
  refusals, each with its stable condition name, observed evidence and remediation. Every refusal
  reported by the gate today keeps its condition name and its position in the ordering.
- **FR-006:** The rules currently living in `runner/sdd_runner/__main__.py` move into the core:
  first-entry-versus-re-entry determination, resume authentication and its ordering relative to the
  gate, delegation-budget computation, and backend resolution. After this feature the CLI module
  contains argument parsing, output rendering and the exit call, and no protocol decision.
- **FR-007:** A dry run is computed by the core and returned as data on `RunOutcome`; the CLI only
  renders it. The rendered text stays byte-identical to today's output.

**Policies as data**

- **FR-008:** Caps, escalation classification inputs, reviewer trigger lists, fingerprint inclusion
  and exclusion rules, run-artifact names, lifecycle values, run results, severities and exit codes
  are typed values in one policy module, importable without importing the loop.
- **FR-009:** `ORCHESTRATION.md` gains a `Protocol version: <n>` header field, written by the core
  on create and preserved on save. It is the first of the intentional changes to observable output
  in this feature. **The block below is the complete list**: every one is enumerated here with a
  stable identifier and the decision that authorised it, and nothing outside this list may differ
  from `main`. The count is the length of the list, and is stated nowhere else.

  ```yaml
  authorised-observable-differences:
    - id: DIFF-001
      decision: D003
      surface: ORCHESTRATION.md
      change: the additive Protocol version header line
    - id: DIFF-002
      decision: D015
      surface: CLI exit code and both streams
      change: a failure to persist run.jsonl becomes exit 70 with a stable redacted diagnostic
    - id: DIFF-003
      decision: D018
      surface: CLI exit code and both streams
      change: a baseline suite that cannot launch becomes exit 10 with a BASELINE_UNAVAILABLE refusal
  ```

  This block is the record, and the contract tests read it **structurally, by identifier**:
  `test_golden_cli.TheSpecAndTheseConstantsAgree` fails if its own constants and this list disagree,
  and `test_main_baselines` fails if a listed difference has no recorded `main` side, if an
  unlisted difference appears, or if a listed one is not the difference the record describes.
  Adding a further difference means adding an entry here first.

  **Two entries were added to this list after the fact, and the history is kept on purpose.**
  The requirement said "only" while the tree already shipped `DIFF-002` — authorised by D015 and
  pinned by the `audit-unavailable` transcript pair, but never written back here; that is the
  unrepaired half of `domain:DOM-023`, re-reported in round 5 as `security:SEC-013`. It then said
  **"exactly two"** while the tree already shipped `DIFF-003` — the `BASELINE_UNAVAILABLE` refusal
  introduced by `security:SEC-006`'s repair and reclassified by `security:SEC-012`, neither of which
  was asked to decide whether the departure from `main` was authorised. Nothing detected it, because
  the ten gate-refusal scenarios CONF-003 added had **no `main` side to be compared against** until
  CONF-006 captured one. Authorised retroactively by D018.
- **FR-010:** A state file **without** `Protocol version` is read as version `1` and remains fully
  resumable. A file whose version the core does not understand refuses fail-closed as unresumable,
  naming the version it read and the version it supports — it is never guessed into shape.
- **FR-011:** The `stub` backend remains the deterministic adapter and stays scripted from JSON. It
  must be sufficient to drive start, pause, abort, resume and core-complete **through the public
  interface alone**.

**Contract tests and documentation**

- **FR-012:** Contract tests fail when the core and any **protocol surface** disagree about a
  normative rule. The protocol surfaces are enumerated exactly — there are nine, found by grepping
  the repository for the constants themselves:

  | Surface | Normative content it states |
  |---|---|
  | `runner/sdd_runner/__main__.py` | flag set, exit codes, dry-run rendering |
  | `skills/sdd-orchestrate/SKILL.md` | the whole protocol in prose |
  | `skills/sdd-orchestrate/templates/ORCHESTRATION.md` | section order, header fields, table columns |
  | `runner/README.md` | flags, exit codes, budget formula, `CORE-COMPLETE` boundary |
  | `docs/SDD-ORCHESTRATION.md` | invocation, flags, budget formula, `Inherited` table |
  | `agents/domain-reviewer.md` | the closed severity enum |
  | `agents/final-conformance-reviewer.md` | the closed severity enum |
  | `adapters/codex/PARITY.md` | `ORCHESTRATION.md` blackboard, `Inherited` table, adoption header fields |
  | `evals/scenarios/orchestrate-per-finding-counter.md` | `max-delegations` default, counter semantics |

  Coverage is at minimum: exit-code names and values, gate condition names and their order, run
  results, lifecycle values, the severity enum, the human-gated escalation domains, the security
  trigger list, the reviewer set, the budget formula, `ORCHESTRATION.md` section order and header
  fields, and the CLI flag set.
- **FR-012a — the contract tests must not over-reach.** Twelve unrelated review skills
  (`security-review`, `qa-review`, `api-review`, `database-review`, `frontend-review`,
  `performance-review`, `privacy-compliance-review`, `review-all`, and the four SEO/GEO/AEO/AI
  skills) contain the string `Critical | High | Medium | Low` as ordinary **report** vocabulary.
  They are *not* protocol surfaces. A contract test that greps the repository for a constant
  instead of reading the enumerated surface list would fail on all twelve and would then be
  weakened or deleted — the exact failure mode this feature exists to prevent. Every contract test
  reads the FR-012 surface list; none discovers surfaces by search.
- **FR-013:** The existing `PROTOCOL_TRANSCRIPTION.md` guard survives the refactor: every row still
  names a module attribute that exists and a test file the suite collects, with references updated
  to the new locations. Its scope note (three Finalizer clauses excluded) stays true.
- **FR-014:** Normative documentation is **validated against** the executable contract, not
  generated from it. The skill and the README stay human-authored and human-readable; a contract
  test asserts the values they state match the core.

**Seams**

- **FR-015:** Exactly three seams are declared, in one place, each with the feature that will fill
  it and no implementation here: **autonomous entry** (a caller that turns a request into a
  `RunRequest`), **real providers** (`Backend` implementations beyond `stub`), and **Finalizer**
  (what happens after `CORE-COMPLETE`). No other abstraction is introduced without a second real
  implementation existing today.

**Compatibility**

- **FR-016:** `python3 -m sdd_runner` keeps every flag, every exit code, and every refusal message
  shape it has today. `/sdd-orchestrate --autonomous [--adopt]` remains the documented skill-side
  interface for the duration of the migration.
- **FR-017:** No installer, `profiles.json` entry, install manifest or `check-consistency.sh` rule
  changes (spec 040 D001 / AC-014, upheld by A-012). "Installable" is satisfied by local packaging:
  a `pyproject` declaring the package, zero non-stdlib runtime dependencies, no import reaching
  outside the package, and `python3 -m …` working from a plain checkout.

## Non-functional requirements

- **Performance:** the suite stays on stdlib `unittest` with no third-party dependency and no
  network. Total wall time must not exceed ~1.5× the current ~91 s; a contract test that walks the
  repository must be bounded to the files it names.
- **Security:** every control result stays structured and **fail-closed**. Preserved without
  weakening: feature-path containment through `os.path.realpath` + `commonpath`; `--notify` executed
  without a shell with a fixed argv and JSON on stdin; no agent-authored text reaching a shell
  string; exclusive-create ownership of `ORCHESTRATION.md`; the gate's refusal of a dirty tree,
  default branch and detached HEAD; the read-only agents' inability to write.
- **Observability:** `run.jsonl` keeps its event stream; the protocol version appears in the run log
  and in `ORCHESTRATION.md`; a refusal always names the condition, the evidence and a remediation.
- **Maintainability:** the public surface is small enough to list in one screen — the target is
  ≤ 12 exported names — and everything else is internal. Where a caller previously imported six
  modules to start a run, it imports one. No module may re-export the loop's internals to dodge the
  cap.

## API / Interface changes

**New public interface** (names indicative; the PLAN fixes the final spelling):

| Name | Kind | Purpose |
|---|---|---|
| `run(request)` | function | The only way to execute the protocol. |
| `RunRequest` | dataclass | Validated inputs, replacing the CLI's ad-hoc argument handling. |
| `RunOutcome` | dataclass | Result, exit code, reason, remediation, resumable, escalations, gate, plan, protocol version. |
| `GateResult` | dataclass | Pass/fail plus ordered structured refusals. |
| `Refusal` | dataclass | Condition, observed, remediation (today `gate.Refusal`). |
| `RunPlan` | dataclass | The dry-run projection: feature, entry, unchecked tasks, caps, inherited record. |
| `PROTOCOL_VERSION` | constant | The version stamped into `ORCHESTRATION.md`. |
| policy values | constants | States, gates, caps, severities, triggers, artifacts, exit codes. |
| `Backend`, `Response`, `BackendPrecondition` | interface | Unchanged shape; the provider seam. |

**Unchanged, public, and load-bearing:** every `python3 -m sdd_runner` flag; every exit code value
and name; every gate refusal condition name; `ORCHESTRATION.md`'s section order.

**Skills:** `/sdd-orchestrate` keeps its prose, and stops being the final authority — a stated
change of ownership recorded in the skill itself and in `runner/README.md`, which today says the
opposite (spec 040 D007). `/sdd` is touched only if a contract test proves it states a value that
disagrees with the core.

## Data model changes

No database. The persisted artifacts:

- `ORCHESTRATION.md` — **additive**: one `Protocol version` header line. Section order, table
  columns and every existing field are unchanged. Files written before this feature (including
  `specs/features/032-.../ORCHESTRATION.md` and `033-.../ORCHESTRATION.md`, which the conformance
  suite reads as real artifacts) must keep round-tripping byte-identically when untouched.
- `skills/sdd-orchestrate/templates/ORCHESTRATION.md` — the scaffold gains the same line.
- `run.jsonl` — additive event fields only; no existing field renamed or removed.

## Edge cases

- A state file with **no** `Protocol version` line → read as version 1, resumable (FR-010).
- A state file with a version **higher** than the core's → fail-closed unresumable refusal naming
  both versions; never a traceback, never a guess.
- A state file with a **malformed** version value (`abc`, empty, negative) → same fail-closed path as
  an unknown version.
- Two adapters disagreeing about a value that the contract test does not yet cover → the test suite
  must fail on an **uncovered** normative constant, so adding a policy value without a contract test
  is itself a failure.
- The refactor moves a module named in `PROTOCOL_TRANSCRIPTION.md` → the guard must fail loudly, not
  silently skip the row. Today a module absent from the guard's `MODULES` map makes its rows
  **unchecked**, which is exactly how a deleted method survived in the table for a day (D046).
- `--dry-run` with no usable backend → still returns a plan and exit 0 (a dry run resolves no
  backend today; the move into the core must not change that).
- `--dry-run --adopt` → still prints the inherited record; the record is now computed by the core.
- A run interrupted mid-freeze → the freeze record and `CORE-COMPLETE` semantics are unchanged; the
  core still exits 18 when core completion is not proven.
- A caller passing a `RunRequest` with contradictory fields (`entry="adopt"` with an existing valid
  state file; `stub_script` with `backend="claude"`) → rejected by the core with the same condition
  names the CLI produces today, **on the path that resolves a backend**. A dry run resolves none, so
  it accepts the `stub_script`/backend pair and returns its plan — `main`'s behaviour, preserved by
  AC-008 and now stated rather than implied. An earlier draft of this bullet read as an unqualified
  requirement, which is what led a review repair to change the dry run and break FR-009.
- A contract test greps for a protocol constant instead of reading the FR-012 surface list → it
  fails on twelve unrelated review skills that use the same words as report vocabulary (FR-012a).
- A protocol constant is added to the policy module but to no surface list → the "uncovered
  constant" test of AC-001 must fail; a value nobody states anywhere is still a value nobody can
  check.
- `closure.classify`, `closure.observe` and `closure.unexpected` have **no callers** — the
  Finalizer's pre-written half, already flagged in `PROTOCOL_TRANSCRIPTION.md`'s scope note. The
  refactor moves them unchanged and leaves them uncalled (A-010); a "no dead code" cleanup that
  deletes them would silently discard the Finalizer seam's existing work.
- The maintainer's untracked `docs/AUTONOMOUS_SDD_FEATURE_PROMPT.md` is present in the working tree
  during implementation → no task may add, move, edit or delete it, and no gate change may be made
  to accommodate it.

## Acceptance criteria

- **AC-001:** There is exactly one executable definition of workflow states, gate conditions, caps,
  severities, escalation domains, reviewer triggers, run results and exit codes. A test enumerates
  the policy module's values and fails if the same constant is defined a second time anywhere under
  `runner/`.
- **AC-002:** `run(RunRequest) -> RunOutcome` starts, resumes, adopts and dry-runs a feature, and a
  test asserts that `RunOutcome` and `GateResult` expose no internal type (no `Loop`,
  `Orchestration`, `Backend`, `CounterState`, file handle or mutable shared reference).
- **AC-003:** Every **executable** adapter consumes the core and reimplements none of its rules:
  `runner/sdd_runner/__main__.py` contains no protocol decision, and a test asserts it imports no
  protocol module other than the public interface. Every **prose** adapter — `/sdd`,
  `/sdd-orchestrate`, `runner/README.md`, the `ORCHESTRATION.md` template — is a projection whose
  normative values a contract test checks against the core. (Restated from the original AC-003: a
  Markdown skill cannot import Python, and spec 040 D008 already established there is no injection
  point into a skill's delegations; "consumes the core" is only satisfiable for code.)
- **AC-004:** A newly written `ORCHESTRATION.md` records `Protocol version`. Both real phase-1
  artifacts (specs 032 and 033) still round-trip byte-identically through `state.Orchestration`, and
  a state file without the field resumes as version 1.
- **AC-005:** The suite reports **at least 276 tests, all passing**, on a machine with neither the
  Agent SDK nor the Codex CLI installed. Test files may be edited for import paths and module
  locations only; no assertion may be weakened, deleted or made conditional to keep the count. A
  reviewer must be able to see the assertion-level diff is import-only.
- **AC-006:** New contract tests fail when a normative rule is stated differently by the core and
  any of the nine surfaces enumerated in FR-012. Each of the nine is demonstrated failing at least
  once by a deliberate, reverted mutation recorded as evidence. A tenth test asserts the suite stays
  green against the twelve review skills of FR-012a — proving the guard reads the surface list and
  does not search.
- **AC-007:** A scripted `stub` run demonstrates **start, pause, abort, resume and core-complete**
  through the public interface only — the test imports `run` and `RunRequest` and nothing else from
  the package.
- **AC-008:** External behaviour is unchanged and proved so: for the recorded scenario corpus under
  `evidence/golden/` — at minimum clean first entry, each gate refusal, dry run, dry-run adopt,
  concurrent run, re-entry after a completed run, unresumable state, cap abort, budget exhaustion,
  human escalation, core-complete, backend precondition, the dry-run/backend-option asymmetry, and
  the internal-error path, and the audit-unavailable path — the CLI's exit code and stdout/stderr are
  byte-identical before and after, **apart from the differences FR-009's
  `authorised-observable-differences` block enumerates, and nothing else.** This criterion states no
  count of its own: the list is the authority, and it is read by identifier. A further difference
  would need its own entry in that list and its own decision — a repair that widened dry-run
  validation tried to become one and was reverted (D011, Superseded). No real provider becomes
  usable.

  This criterion twice named a number the tree had already passed. It read *"That is the only
  permitted difference and it stays the only one"* while `DIFF-002` was in the tree
  (`domain:DOM-023` / `security:SEC-013`), and then *"apart from the two differences… and nothing
  else"* while `DIFF-003` was in the tree (`conformance:CONF-006`, authorised by D018). Both times a
  criterion gating this feature was false against it, which is the failure this feature exists to
  end; both times the repair was to record the difference, never to relax the criterion. The count
  now lives only in the list, so the criterion cannot go stale again by arithmetic.
- **AC-009:** `scripts/check-consistency.sh` exits 0, and `install.sh`, `install.ps1`,
  `profiles.json` and the install manifest are **byte-identical to `main`** (`git diff --stat main --
  install.sh install.ps1 profiles.json` is empty). The canonical package imports nothing outside
  itself and nothing outside the stdlib, and `python3 -m sdd_runner --help` works from a plain
  checkout with neither the Agent SDK nor the Codex CLI installed.
- **AC-010:** The three seams of FR-015 are declared in one place, each naming its future owner, and
  a test asserts that none of them has an implementation in this feature: no second `Backend` is
  reachable without an explicit unverified flag, no autonomous entry point exists, and no lifecycle
  skill is dispatched after `CORE-COMPLETE`.
- **AC-011:** The public surface is ≤ 12 exported names, asserted by a test reading the package's
  `__all__`; nothing outside that list is imported by the CLI.
- **AC-012:** The authority inversion is recorded where it is currently stated backwards:
  `runner/README.md` and `sdd_runner/__init__.py` no longer say the runner is wrong when it
  disagrees with the skill, and `skills/sdd-orchestrate/SKILL.md` states that the executable
  contract is the source of truth. A contract test asserts no surviving text asserts the old
  ownership.
- **AC-013:** `docs/AUTONOMOUS_SDD_FEATURE_PROMPT.md` is unmodified and remains untracked at the end
  of the feature (`git status --porcelain` shows it as `??`, same bytes).

## Test scenarios

- **Unit**
  - Policy module: every constant has exactly one definition; the severity enum, run results,
    lifecycle values, exit-code map and human-gated domains match their current values exactly.
  - `RunRequest` validation: path containment (including the symlink and `features-old` cases the
    CLI already covers), contradictory fields, cap overrides, unknown backend.
  - `RunOutcome`/`GateResult`: no internal type escapes; refusal ordering preserved.
  - Protocol version: absent → 1; unknown → fail-closed; malformed → fail-closed.
- **Integration**
  - Every existing integration test (`test_loop`, `test_repair`, `test_resume`, `test_race`,
    `test_finalization`, `test_gate`, `test_cli_e2e`, `test_adopt_cli`) passes unchanged in
    assertions, rewired to the new imports.
  - Full scripted `stub` run through `run(RunRequest)` for each of start, pause, abort, resume,
    core-complete (AC-007).
- **Conformance / contract**
  - `PROTOCOL_TRANSCRIPTION.md` guard, updated references, still enforcing table honesty.
  - New cross-surface contract tests (FR-012), each demonstrated failing under a deliberate mutation
    of the core, the CLI, the skill, the template and the README.
  - Golden CLI comparison for AC-008: recorded stdout/stderr/exit code per scenario.
  - Over-reach guard: the contract suite is green while the twelve review skills of FR-012a are
    untouched, and stays green if one of them changes its report vocabulary.
- **Manual**
  - `python3 -m sdd_runner --feature specs/features/042-... --dry-run` on this repository.
  - `bash scripts/check-consistency.sh` → exit 0.
  - `git status --porcelain` before and after → `docs/AUTONOMOUS_SDD_FEATURE_PROMPT.md` unchanged.
  - `git diff --stat main -- install.sh install.ps1 profiles.json` → empty (unless OQ-1 says
    otherwise).

## Assumptions

- **A-001 — Canonical name and location.** The module is named for what it is: the **protocol
  authority**, not "core" and not "adapter". `sdd_core` is rejected because `docs/PROVIDER_ADAPTERS.md`
  already binds **"SDD Core"** to the provider-neutral *workflow* layer (specs lifecycle, review
  gates, skill contracts, agent roles) and **"adapter"** to *provider packaging*
  (`adapters/claude`, `adapters/codex`); reusing either word for a Python package would create a
  third meaning for a term the framework already defines twice.

  This assumption recommended `runner/sdd_protocol/`; **planning superseded that spelling — see
  D001.** The inventory found 21 test files importing `sdd_runner` submodules, so a rename would
  bury AC-005's import-only signal under mechanical churn. The package stays `runner/sdd_runner/`
  and depth comes from `__init__.__all__` plus `policy.py`/`protocol.py`/`seams.py`. What survives
  from this assumption is its *rejection* of `sdd_core` and `adapter`, which D001 upholds: the
  framework already binds both words, and prose in the README, the `__init__` docstring and
  SKILL.md carries the ownership a package name cannot (D004). `runner/` remains the location
  (spec 040 D002); A-012 confirms nothing is distributed.
- **A-002 — Rules that become data versus rules that stay code.** Data: closed vocabularies and
  fixed values (states, lifecycle, run results, severities, exit codes, human-gated domains,
  security triggers, reviewer set, run artifacts, the budget formula's constants, the gate condition
  names and their order). Code: anything requiring the tree, git, or the run's history — fingerprint
  computation, resume reconciliation, counter transitions, freeze, and the escalation *classifier*
  (its input domains are data; its judgement is not). A rule becomes data only when a contract test
  can compare it against another surface.
- **A-003 — Documentation is validated, not generated.** Generating normative prose from Python
  would make `/sdd-orchestrate` unreadable to the humans and agents that consume it, and there is
  already a working precedent for validation (`test_transcription.py`'s
  `test_the_protocol_documents_the_closed_enum`, which asserts four documents state the closed
  enum). FR-012 generalises that precedent rather than inventing a generator.
- **A-004 — Real adapters today.** Exactly two seams have a second real implementation and therefore
  justify existing: **caller** (CLI today; autonomous entry later) and **backend** (`stub` today;
  `claude`/`codex` present but not enabled). "Skill versus CLI" is *not* a code seam — a skill cannot
  call Python — so it is served by contract tests, not by an interface.
- **A-005 — Versioning strategy.** `protocol_version` is a single monotonic integer starting at `1`,
  describing the *protocol contract*, not the package version. Absent means 1 (mirroring spec 041
  D007's "a state file with no `Entry` line is read as `ready`"). It is bumped only by a spec that
  changes a normative rule, never by a refactor — so this feature stamps `1` and does not bump.
- **A-006 — The 276 count.** Verified on 2026-09-03: `Ran 276 tests … OK`, stdlib `unittest`,
  ~91 s. "Preserving the behaviour the 276 tests demonstrate" permits editing their import lines and
  file locations; it forbids touching their assertions.
- **A-007 — Contracted services.** No `specs/SERVICES.md` exists at the repository root (only
  `specs/_templates/SERVICES.md`), so the conservative default applies; nothing in this feature is
  billable in any case.
- **A-008 — Branch.** Implementation happens on a dedicated feature branch, never on `main` — which
  the runner's own entry gate enforces for any run pointed at this feature.
- **A-009 — This repository has no `specs/CONSTITUTION.md`.** It is the SDD framework itself, not an
  adopter project, so `specs/` holds only `_templates/` and `features/`. No constitution rule
  constrains this feature, and none is created by it — `/project-init` is out of scope.
- **A-010 — Found dead code is reported, not removed.** `closure.classify`, `closure.observe` and
  `closure.unexpected` have no callers today and are the Finalizer's pre-written half. They move
  with their module and stay uncalled. Deleting them belongs to the Finalizer spec, which either
  uses them or removes them with a reason.
- **A-012 — OQ-1, answered 2026-09-03: not distributed yet.** The maintainer's words: *"No se
  distribuye todavía. 'Instalable' significa empaquetado y ejecutable localmente dentro del
  repositorio, no incluido en los instaladores para adoptantes. La activación y distribución por
  defecto quedan fuera de la spec 042."* So **"installable" is read as packaged and locally
  runnable**: a clean `pyproject`, a stdlib-only dependency set, no import reaching outside the
  package, and `python3 -m …` working from a checkout. It is **not** read as entering
  `install.sh`/`install.ps1`, `profiles.json`, the install manifest or `check-consistency.sh`.
  Spec 040 D001 stands unamended, AC-009 and FR-017 stand as written, and both activation and
  downstream distribution are explicitly a later feature's scope.
- **A-011 — Codex has a real protocol surface.** `adapters/codex/PARITY.md` states
  `ORCHESTRATION.md` structure, the `Inherited` table and the adoption header fields, so it is
  covered by FR-012 like any other surface. This resolves the former OQ-3 in favour of covering it:
  scoping the contract tests to Claude-only surfaces would leave the one adapter whose autonomous
  evidence is, by its own account, mostly Codex-only, unguarded. What Codex does **not** get here is
  a code seam — it has no Python surface to check.

## Open questions

**None blocking.** OQ-1 was answered by the maintainer on 2026-09-03; see A-012.

**All resolved during planning. Kept for provenance:**

- ~~**OQ-2**~~ — **Resolved by D001.** There is no second package: `sdd_runner` keeps its name and
  the CLI stays inside it as `__main__.py`. `python3 -m sdd_runner` is therefore unchanged and needs
  no shim, so the invocation strings in `runner/README.md`, `skills/sdd-orchestrate/SKILL.md` and
  `docs/SDD-ORCHESTRATION.md` stay as they are.
- ~~**OQ-3**~~ — **Resolved during clarification.** The grep was run: `adapters/codex/PARITY.md`
  does state protocol values (`ORCHESTRATION.md` blackboard, `Inherited` table, adoption header
  fields), so it is a protocol surface and FR-012 covers it. See A-011.
- ~~**OQ-4**~~ — **Resolved by D002.** Both survive: the table alone carries clause→module→test
  provenance, the contract tests alone carry cross-surface value agreement. T018 updates the table's
  references without widening the `MODULES` hole that D002 names as its known weakness.

## Contracted services

`specs/SERVICES.md` does not exist at the repository root (only the template at
`specs/_templates/SERVICES.md`). Contracted services not declared → all billable add-ons treated as
NOT contracted (conservative default). Run `/project-init` to declare them.

This feature requires no billable service: it is a local refactor of maintainer tooling with a
stdlib-only test suite, no network access and no provider execution.
