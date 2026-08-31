# Implementation Plan: agent-sdk-runner

## Summary

Build `runner/`, a self-contained Python package that executes the autonomous SDD loop defined by
spec 031 as **code** rather than as prompt instructions: it reads `TASKS.md`, dispatches one
provider session per task or review carrying the corresponding `agents/*.md` system prompt, parses
verdict and completion blocks with a fail-closed parser, enforces the caps and the delegation
budget arithmetically, persists 031's `ORCHESTRATION.md` schema plus a new `run.jsonl`, retries
transport failures under a bounded policy, and notifies the human only on a human-gated escalation
or a non-success exit.

v1 is **maintainer tooling of this repository**. It ships no installer change, no manifest change,
and no downstream dependency. Its correctness is provable end to end against a stub backend, with
one real-provider E2E on top.

## Related spec

[SPEC.md](SPEC.md) — status `Ready`.

## Impacted areas

**Created:**

- `runner/` — the Python package: CLI, loop driver, parser, state I/O, counters, escalation
  classifier, backends (`stub`, `claude`, `codex`), retry policy, JSONL logging.
- `runner/tests/` — unit, integration and conformance suites plus the fixture corpus.
- `specs/features/040-agent-sdk-runner/fixtures/` — a small fixture feature folder used as the
  loop's target in integration tests.
- `specs/features/<nnn>-<name>/run.jsonl` — new per-feature artifact, written at run time.

**Modified (documentation only):**

- `docs/SDD-ORCHESTRATION.md` — a phase-2 section: invocation, exit codes, backends, notification,
  resume, and the phase-1/phase-2 boundary.
- `CHANGELOG.md` — the feature entry.
- `CONTRIBUTING.md` — one line on the runner's optional dependency, kept honest against the
  existing "no dependencies beyond `bash`, `python3`, optionally `pwsh`" statement at line 124.
- `docs/KNOWN_DEBT.md` — only if the Codex verification of AC-013 actually happens.

**Explicitly not touched** (AC-014 asserts this): `install.sh`, `install.ps1`, `install-all.sh`,
`install-all.ps1`, `profiles.json`, `settings.template.json`, the install manifest,
`scripts/check-consistency.sh`, and every existing skill and agent.

## Context budget

### Reading list

The protocol already exists in writing; the job is to transcribe it faithfully, so the reading list
is dominated by the two specs that define it and by the skill that implements it today.

- `specs/features/040-agent-sdk-runner/SPEC.md` — this feature.
- `specs/features/031-autonomous-orchestration-loop/SPEC.md` — **the normative source** for the
  entry gate (FR-002), verdict/completion blocks (FR-003/FR-004), the escalation rule (FR-005),
  the finding registry (FR-007), attempt lifecycle (FR-008), caps and budget (FR-009), re-entry
  (FR-011), and the closure freeze (FR-013). Read in full, once.
- `specs/features/031-autonomous-orchestration-loop/DECISIONS.md` — for the *why* behind the
  counter semantics, before re-deriving them wrongly.
- `specs/features/032-autonomous-loop-residual-calibration/SPEC.md` + `CALIBRATION.md` — the
  observed-evidence corrections to 031. Where 031 and 032 disagree, 032 wins.
- `skills/sdd-orchestrate/SKILL.md` — the current executor. The conformance test (FR-015) is
  written against its behavior, so its loop section must be read closely.
- `agents/security-reviewer.md`, `agents/domain-reviewer.md`,
  `agents/final-conformance-reviewer.md`, `agents/implementer.md`, `agents/fast-worker.md`,
  `agents/deep-reasoner.md`, `agents/solution-architect.md` — read for their **verdict/completion
  block contract and frontmatter shape only**, not end to end; the runner sends these files as
  system prompts without paraphrasing them.
- `scripts/skill-eval.sh` — the `PROVIDER_TABLE` and the Codex isolation flag set, plus the
  `--allow-unisolated` refusal message, which is the precedent FR-017 copies.
- `docs/KNOWN_DEBT.md` — DEBT-001 and DEBT-002 entries only.
- `scripts/check-consistency.sh` — skimmed once, to confirm a new top-level `runner/` folder is
  outside its rules (T001).

**Out of budget:** every other spec folder, every skill other than `sdd-orchestrate`, the whole of
`install.sh`/`install.ps1` (the plan's claim is that they do not change — confirmed by `git diff`,
not by reading them), `adapters/`, and `evals/`.

### Model routing

| Phase / tasks | Routing | Justification |
|---|---|---|
| T003 parser fail-closed semantics | **deep-reasoning** | This is the security boundary. Agent output is untrusted input, and "fail closed" has to hold for the adversarial fixtures, not just the malformed ones. Getting it wrong turns a rejected review into a silent approval. |
| T005 counters and budget | **deep-reasoning** | 031 FR-009 is the most intricate rule in the protocol: two counters with different reset semantics plus a monotonic budget. It must be derived from the spec text and a hand-computed table, not from intuition. |
| T013 loop driver, resume, concurrency | **deep-reasoning** | Idempotent re-entry (031 FR-011) and the attempt lifecycle (031 FR-008) interact; a wrong resume re-delegates completed work or duplicates findings under a live budget. |
| T014 finalization freeze | **deep-reasoning** | The closure-delta allowlist (031 FR-013) decides whether a run's approvals survive its own closure writes. Off-by-one here silently invalidates conformance. |
| T017 conformance test | **deep-reasoning** | It has to be a real comparison, not a test that passes because both sides are the runner. |
| T020 security review | **deep-reasoning** | Unattended execution, credentials, untrusted responses, `--notify` command execution. |
| T001, T002, T007, T009, T011, T012, T018, T019, T023 | cheap/mechanical | Package skeleton, fixtures, stub backend, subprocess wrapper, JSONL writer, argparse plumbing, running suites, docs. Decided semantics, mechanical execution. |
| T004, T006, T008, T010 | cheap/mechanical, deep-reasoning on review | Markdown I/O against a fixed schema, a documented classification table, an SDK call, a retry decorator — mechanical to write, but each is reviewed against its 031 FR before acceptance. |

## Proposed approach

**One protocol, transcribed once.** Every module that encodes a rule from 031 names the FR it
implements in a module-level docstring, so a future change to 031 has a findable set of call sites
(SPEC NFR: Maintainability). The runner never invents semantics; where 031 is silent, the task
stops and escalates rather than choosing.

**Build order is inside-out, and it is deliberate.** The pure, testable core comes first — parser,
state I/O, counters, classifier — because all of it is provable with zero provider calls. Only then
the backends, then the driver that composes them. The stub backend (T007) lands before any real
backend, so the entire integration suite is written and green before a single token is spent.

Layers:

1. **Core (pure).** `blocks.py` (fail-closed parser), `state.py` (`ORCHESTRATION.md` read/write in
   031's schema), `counters.py` (FR-009 arithmetic), `escalation.py` (FR-005 classification),
   `budget.py`. No I/O beyond the feature folder, no provider knowledge, fully unit-testable.
2. **Backends.** A single `Backend` protocol — run a session given system prompt, task prompt, path
   scope, timeout; return raw text plus transport metadata. Three implementations: `stub`
   (scripted, always present), `claude` (Agent SDK), `codex` (`codex exec` subprocess, gated shut
   by default per FR-017).
3. **Infrastructure.** `retry.py` (bounded attempts, backoff, per-attempt timeout, every retry
   charged to the budget), `log.py` (`run.jsonl`, with redaction applied at the writer so no call
   site can forget it).
4. **Driver.** `loop.py` composes the above: entry gate → plan → per-task dispatch → parse →
   reviewers → findings-to-tasks → re-review → converge or abort. State is persisted *before* the
   driver proceeds past any transition, which is what makes the SIGTERM test meaningful.
5. **CLI.** `__main__.py`: argument parsing, exit-code mapping, notification sink.

**Fail-closed is the house rule, not a feature of one module.** An unparseable reviewer response is
a REJECT. An unparseable worker response is BLOCKED. An unclassifiable escalation is human-gated.
An unverified backend is refused. A second concurrent run is refused. In every ambiguous case the
runner does the boring, visible, recoverable thing.

**Agent responses are untrusted input.** Only the fenced verdict block is ever acted on; prose is
recorded and never interpreted. `--notify` receives its event as JSON on stdin and is executed
without a shell, so no agent-produced text can reach a shell string.

**Codex, honestly.** The backend is written — a real implementation, so the abstraction carries two
loads rather than one plus a comment — and it refuses to run without `--allow-unverified-backend`,
naming DEBT-001/DEBT-002. No document claims multi-backend parity until a real `codex exec` run
records the accepted flags. If the CLI appears during implementation, T009 closes the debts; if it
does not, that is reported as unobserved, not assumed.

## Alternatives considered

- **Extend `sdd-orchestrate` with better prompt discipline instead of writing a runner.** Rejected:
  it cannot address the actual problem. No prompt makes a model's arithmetic deterministic, no
  prompt survives context compression by construction, and no Claude Code skill can invoke
  `codex exec`. Phase 1 already went as far as this mechanism goes.
- **Reimplement the loop semantics "better" while transcribing them.** Rejected explicitly, and
  guarded by FR-015's conformance test. Two executors with two semantics is worse than one
  executor, because every disagreement becomes an unfalsifiable argument about which is right.
- **Ship the runner to adopter projects in v1.** Rejected by the maintainer (D001). It would push a
  pip dependency onto every adopter to validate a loop that has never run unattended even once.
- **TypeScript Agent SDK.** Rejected: Python is already a declared dependency of this repo and the
  maintainer's daily stack; adding a Node toolchain to a Bash/PowerShell/Python repo costs more
  than the SDK difference is worth.
- **Skip the stub backend and test against a real provider.** Rejected: non-deterministic tests for
  a component whose entire value proposition is determinism, at a per-run cost, with no way to
  script a flip-flopping reviewer.
- **Store loop state as JSON instead of reusing `ORCHESTRATION.md`.** Rejected: it would fork the
  state format between the two executors and break the requirement that either can resume the
  other's run (FR-005). `run.jsonl` covers the machine-readable need without splitting the source
  of truth.
- **Give the runner checkpoint commits in v1**, as 031 anticipated. Rejected by the maintainer
  (D005): an unsupervised executor should not write git history in its first release.

## Dependencies

- **`claude-agent-sdk` (Python)** — new, and the first non-stdlib Python dependency this repo has
  ever had. Declared in `runner/`'s own manifest, imported lazily so its absence cannot break
  anything but the `claude` backend.
- **Codex CLI** — **not installed on this machine** (verified 2026-08-31). Gates AC-013's optional
  clause and the closure of DEBT-001/DEBT-002.
- **Provider credentials** — from the environment only, for the E2E tasks.
- **Python 3.14** on this machine; the floor the manifest declares is decided in T001.
- **A scheduler** (`cron` or `launchd`) for AC-002. No CI account or runner is required.
- Existing suites (`check-consistency.test.sh`, `install.test.sh`, `install.test.ps1`) as the
  untouched-baseline evidence for AC-010.

## Risks

| # | Risk | Severity | Mitigation |
|---|---|---|---|
| R1 | **The transcription drifts from 031.** Two executors, two behaviors, and the framework's autonomy story splits in half. | High | **PARTIALLY mitigated only (D008).** The two-executor conformance test proved unviable — no injection point into `sdd-orchestrate`'s Agent-tool delegations. The replacement is a protocol transcription guard: a clause→module→test table plus a test that keeps it honest and checks the runner against real recorded phase-1 artifacts. Nothing compares the two executors on the same input, so drift can still occur. The guard already found one real divergence (D011). |
| R2 | **A parser bug turns a REJECT into an APPROVE.** The failure is silent and it defeats the entire review gate. | High | Fail-closed by construction (T003, deep-reasoning), an adversarial fixture corpus (T002) including a response whose *prose* contains a fake verdict block, and AC-004. |
| R3 | **The budget leaks and an overnight run empties the account.** | High | Budget is checked *before* dispatch, retries are charged, and AC-006 proves the N+1st call is never made — observed by counting stub invocations, not by reading code. |
| R4 | **The SDK dependency escapes containment** into installers or adopter machines. | Medium | FR-014 plus AC-014's `git diff` assertion, plus AC-010 running the existing suites on a machine without the SDK. Lazy imports. |
| R5 | **A resumed run duplicates work or resets a counter**, making caps meaningless across restarts. | High | State written before proceeding past any transition; AC-007's SIGTERM-and-restart test; counters monotonic by construction (T005). |
| R6 | **Codex remains prose forever**, recreating DEBT-002 inside the runner. | Medium | The backend is implemented, not described, and the gate refuses loudly rather than the docs claiming quietly. The refusal message names the debt. |
| R7 | **`--notify` becomes a command-injection surface** carrying agent-authored text. | Mitigated | Executed without a shell, argument vector fixed, event delivered as JSON on stdin. Confirmed by T020's review. |
| R11 | **An agent writes outside the work it was given**, and nothing notices until the run ends. | **Partially mitigated (D028)** | Read-only agents now fail closed on any tree change during their delegation (031 FR-008). Writing agents still carry the whole repo as their scope, so a worker straying into unrelated code is caught only by the closure delta at the end. |
| R8 | **Concurrent `cron` runs corrupt `ORCHESTRATION.md`.** | Medium | A lock with the ACTIVE run recorded in state; second runner refuses before any provider call (AC-011). |
| R9 | **Secrets land in the runner's artifacts** and they become unshareable. | **Materialized, then closed** | Redaction now runs at both writers — `run.jsonl` and `ORCHESTRATION.md` — pinned by a full-run regression. It leaked for four tasks because T011's `Verify:` was narrower than AC-012, and the suite could not have caught it: no test ran a secret through a real escalation. Residual: redaction keys on env-var *names* matching a hint list, so a credential passed some other way is not recognised. |
| R10 | **[[DEBT-009]]** — **the real E2E fails for reasons the stub cannot model** (SDK session semantics, prompt shape of `agents/*.md`, lifecycle skills that never ran, `PR_DESCRIPTION.md` that never appeared). | **Medium — UNTESTED, and now the largest unknown** | T018 is `not observed` (D026), and AC-001/AC-002 were downgraded to match (D030): no SDK and no Codex CLI on this machine. Nothing here is mitigated, only bounded and named. The Assumptions section flags that a prompt-shape mismatch is a finding, not a licence to fork the agent files. |

## Test strategy

The suite runs on stdlib `unittest`, not pytest (D009): requiring an install to prove
containment would contradict the containment.

- **Unit** (`runner/tests/unit/`): the parser against the fixture corpus (valid, missing,
  malformed, unknown verdict, double-block, truncated, adversarial prose-embedded block); counter
  arithmetic against a hand-computed table derived from 031 FR-009, including every case that must
  *not* increment; budget accounting with retries; escalation classification per category; exit-code
  mapping; secret redaction; `ORCHESTRATION.md` round-trip.
- **Integration** (`runner/tests/integration/`): the full loop against the stub backend over the
  fixture feature — converge, reject-then-fix, flip-flop on one finding ID, per-reviewer cap abort,
  per-finding cap abort, budget refusal, SIGTERM-and-resume, concurrent-run refusal, human-gated
  escalation with `--notify`.
- **Conformance** (FR-015, T017 as replaced by D008): a protocol transcription guard —
  `runner/tests/conformance/PROTOCOL_TRANSCRIPTION.md` maps each 031 clause to the module encoding
  it and the test pinning it, and `test_transcription.py` fails when that table names a module
  attribute or test file that does not exist, and checks the runner's model against the real
  recorded `ORCHESTRATION.md` artifacts of specs 032 and 033. Weaker than a two-executor
  comparison, and stated as such.
- **E2E** (T018): AC-001 non-interactive with `</dev/null` and no TTY; AC-002 the same run launched
  from `cron`. Real provider, small fixture feature, one run each.
- **Regression** (T019): `check-consistency.sh` exit 0; `check-consistency.test.sh` 42/42;
  `install.test.sh` 33/33; `install.test.ps1` 28/28 under pwsh — all on a machine without the SDK,
  plus the AC-014 `git diff` assertion.
- **Manual** (T022): one overnight unattended run on a real spec of this repo, with
  `ORCHESTRATION.md` and `run.jsonl` read start to finish by the maintainer.

## Rollback strategy

Trivially reversible, by design. The runner is one new top-level folder with no callers: deleting
`runner/` removes the feature entirely, and nothing in the framework imports it or depends on it.
No installer, manifest, skill, agent, or hook changes, so there is no adopter-visible surface to
revert and no migration to undo. The documentation edits (`docs/SDD-ORCHESTRATION.md`,
`CHANGELOG.md`, `CONTRIBUTING.md`) revert as an ordinary diff. Runtime artifacts (`run.jsonl`) are
per-feature files that can be deleted without affecting `ORCHESTRATION.md`.

Operationally, a misbehaving run is stopped by killing the process: the state file is written
before each transition, so the tree is left in an inspectable state and the run is either resumable
or explicitly not, per 031 FR-011.

## PLAN verification checklist

- [x] The plan covers all acceptance criteria. (AC-001…AC-014 each map to at least one task.)
- [x] The plan avoids behavior outside the spec.
- [x] The Context budget section is filled (reading list + model routing), not left as placeholder.
- [x] Risks are documented.
- [x] Test strategy is documented.
- [x] Rollback strategy is documented.
- [x] SPEC.md status has been updated to `Ready`.
