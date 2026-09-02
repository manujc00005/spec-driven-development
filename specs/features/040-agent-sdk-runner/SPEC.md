# Feature Spec: agent-sdk-runner

## Status

Done

## Classification

**EXPERIMENTAL** (2026-08-31, D033; retained by D034).

This runner is a deterministic core with a stub backend, and that is what it should be trusted as.
It is **not** a supported way to run unattended work against a real provider. D034 accepts the
architecture review's option A: 040 owns the core controls through the `_finalize` seam; a
follow-up owns real providers, writer-scope enforcement, lifecycle delegation and closure. D035–D038
record partial implementation progress and its reconciliation, but T028…T032 remain open against
their current Verify clauses, so final conformance remains **PARTIAL**, not PASS.

The lifecycle `Status` above stays `In Review` because only `/spec-review` may move it, and this
update is not that gate. A re-run of `/spec-review` against the findings below would not return
`Pass`.

> **Historical lifecycle record; the 2026-08-31 Pass is superseded by D033/D034.**
>
> `Done` 2026-09-01 — `/spec-close`. `/spec-review` returned **Pass** on the corrected scope the
> same day. All 33 tasks resolved: 31 closed against their `Verify:` clause, 2 (T018, T022) moved
> out of the spec by D034 and marked `[~]`. All 19 acceptance criteria met against observed
> evidence. **239 tests**, green; `check-consistency.sh` exit 0; `check-consistency.test.sh` 42/42,
> `install.test.sh` 33/33, `install.test.ps1` 28/28; installers and manifests byte-identical to
> `main`.
>
> **Closed as EXPERIMENTAL, and the word is load-bearing.** `stub` is the only supported backend.
> `claude` and `codex` are outside the supported surface and have never spoken to a provider; no
> parity is claimed. A converged run stops at `CORE-COMPLETE` and closes no feature lifecycle.
> `Done` here means *this scope is finished and evidenced*, not *the runner is ready to drive
> anything unattended against a real provider*.
>
> `In Review` 2026-08-31 — `/spec-review` **Pass**. All 14 acceptance criteria are met **as
> written**, which for AC-001 and AC-002 means as downgraded by D030 and observed by D031's
> subprocess suite. 24 tasks closed, 2 recorded `NOT OBSERVED` against [[DEBT-009]]. 186 tests;
> `check-consistency.sh` exit 0; installers and manifests byte-identical to `main`.
>
> **`Done` is blocked** and this promotion does not weaken that: DEBT-009 holds four things nobody
> has seen work — a prompt reaching a real provider, a lifecycle skill executing,
> `PR_DESCRIPTION.md` on disk, and a real `codex exec`.
>
> `In Progress` 2026-08-31 — 19 of 25 tasks closed, one deferred as not observable on this
> machine (T018, D026). The status had been left at `Ready` while implementation ran; corrected
> here by its owning skill.
>
> `Ready` 2026-08-31 — PLAN.md, TASKS.md and DECISIONS.md exist; OQ-1, OQ-2 and OQ-3 resolved by
> the maintainer and recorded as D001, D003 and D005; every acceptance criterion AC-001…AC-014 is
> covered by at least one task.
>
> Phase 2 of the autonomy line. Spec 031 named this feature in its own Non-goals —
> "**No Agent SDK runner, no CI/cron integration.** That is phase 2 — a separate feature"
> ([031/SPEC.md:57](../031-autonomous-orchestration-loop/SPEC.md:57)) — and designed the
> verdict-block schema for both consumers: "the SDK runner in phase 2 will parse the same
> blocks programmatically" ([031/SPEC.md:402](../031-autonomous-orchestration-loop/SPEC.md:402)).
> This spec picks up that reservation. Number **040**: 039 is the highest slot on `main`
> and no remote branch claims 040.

## Problem

Spec 031 shipped an autonomous implement→review→fix loop, and spec 032 calibrated its residual
gaps. Both are `Done`. At spec 040's inception that loop existed **only as a prompt**:
`skills/sdd-orchestrate/SKILL.md` instructed an orchestrator LLM, inside an interactive Claude Code
session, to run it. Four consequences motivated the runner; the audit later showed they should not
all be solved inside one feature.

1. **It cannot run unattended.** There is no way to start the loop from CI, from `cron`, or
   overnight. Every autonomous run still begins with a human typing into a session and ends when
   that session ends. The feature is called autonomous and requires a person present to exist.

2. **The control flow is model-mediated, so the guarantees are only as good as the model's
   attention.** The caps of FR-009, the monotonic delegation budget, the fingerprint invalidation
   of FR-011, the closure freeze of FR-013 — all of it is prose the orchestrator must re-read and
   apply correctly at every transition. 031 knew this: FR-008 persists `ORCHESTRATION.md` precisely
   because "a long autonomous run will hit context compression". The state file makes the loop
   *recoverable*; it does not make the arithmetic *deterministic*. A hard budget that a model can
   miscount is not a hard budget.

3. **Retries and transport failures have no owner.** An API error, a truncated response, a
   malformed verdict block: today these land on the orchestrator's judgment mid-run. There is no
   bounded retry policy, no backoff, and no rule that says a retry consumes budget — except as a
   sentence in FR-009 that nothing enforces.

4. **Checkpointing was parked here on purpose.** 031 deferred audit/bisect/crash-recovery commits
   to phase 2 "where the SDK runner — not an agent — could own them"
   ([031/SPEC.md:64](../031-autonomous-orchestration-loop/SPEC.md:64)), because the agents'
   contracts forbid committing and phase 1 refused to carve an exception.

There is a fifth problem, and it is the one that most justifies choosing a runner over a better
prompt. **The framework's rule is that nothing may be Claude-Code-only.** Phase 1 honors that rule
on paper: FR-012 documents that the Codex adapter degrades to a sequential single-context loop
because Codex has no Agent tool. That degradation is real and it is a ceiling — a Claude Code skill
cannot invoke `codex exec`. A runner can: it is the only place in this framework where both
providers can be driven through *one* implementation of the protocol rather than two prose
descriptions of it that drift.

That argument comes with a debt attached, and this spec must not inherit it silently.
**The Codex CLI is not installed on the maintainer's machine** (`which codex` → not found, verified
2026-08-31), which contradicts spec 031's own closing assumption that "a Codex CLI is present in
this environment". `DEBT-001` and `DEBT-002` are both open for the same root cause: the Codex
isolation flags are enforced but never exercised, and the adapter is advertised as
prompt-based/unverified ([KNOWN_DEBT.md](../../../docs/KNOWN_DEBT.md)). A second backend that has
never been executed is not a second backend.

The first 040 implementation attempted the full answer — deterministic engine, providers and
lifecycle closure — and D033 found nine architectural defects. D034 therefore preserves the part
that can be proved locally and moves the external boundary to a separately observable feature.

## Goal

A Python runner that executes the **deterministic core** of the protocol defined by spec 031 as
code rather than as instructions: it reads `TASKS.md`, drives a scripted backend through one
backend interface, parses verdict and completion blocks programmatically, enforces caps and budget
arithmetically, persists `ORCHESTRATION.md`, emits a machine-readable run log and fails closed on
ambiguous state.

The success criterion is deliberately smaller than the original one: **a `Ready` fixture feature
converges through the stub backend without an interactive session; exit `0` is impossible unless a
declared non-mutating baseline passes; a foreign executor's state is readable but refused for
re-entry; feature paths, concurrent ownership and repository fingerprints are enforced rather
than merely recorded.**

One state format, executor-owned re-entry. Spec 040 preserves the shared protocol vocabulary and
file shape, but it no longer claims that two independently evolving executors can safely continue
each other's in-memory lifecycle. Real provider sessions and full phase-1 parity are follow-up
work.

**v1 boundary (decided 2026-08-31, resolving OQ-1 and OQ-2).** v1 is **maintainer tooling of this
repository**, not a shipped artifact: it does not enter the installers, `profiles.json`, or the
install manifest, and no adopter project inherits a pip dependency because of it. Its first real
workload is this repo's own specs. Downstream distribution is a later phase, gated on this runner
having an observed track record — the same reasoning that keeps checkpoint commits out of v1.

## Non-goals

- **No new core-loop semantics.** Specs 031 and 032 still own the parser, escalation categories,
  non-convergence counters, finding registry and fingerprint invalidation retained here. D034
  explicitly removes provider routing and the closure freeze from 040 rather than quietly
  diverging from them.
- **No replacement of `/sdd-orchestrate`.** The interactive skill stays, unchanged in behavior, and
  remains the recommended path for attended work.
- **No auto-commit of feature work, push, merge or spec-Status promotion.** Spec 040 invokes no
  owning lifecycle skill; all phase-1 prohibitions survive on the core side of the seam.
- **No checkpoint commits in this spec**, despite 031 parking them here. Giving the first
  unattended executor the power to write git history on its very first release multiplies the blast
  radius of every other defect in it. This is a deliberate deferral, recorded so it is not lost:
  it belongs in a follow-up once the runner has an observed track record. See Open questions OQ-3.
- **No distribution to adopter projects in v1.** The runner is not installed by `install.sh` or
  `install.ps1`, is not listed in `profiles.json` or the install manifest, and is not assumed to
  exist in any downstream project. A machine with neither the Agent SDK nor the Codex CLI installed
  must keep using this framework exactly as it does today — that is a hard requirement (FR-014),
  not an aspiration.
- **No real-provider execution, writer-scope enforcement, lifecycle delegation or closure
  automation** (moved out 2026-08-31, D034, AUDIT-3/AUDIT-4/AUDIT-8/AUDIT-9). Spec 040 keeps the
  deterministic core and the stub. Driving a real provider, performing the canonical format retry,
  routing to `deep-reasoner`, policing a writing provider session, attributing its path/history
  mutations, delegating lifecycle skills and automating closure are one follow-up feature. Its code
  seam begins at `Loop._finalize`; it owns a `Finalizer` and the provider-specific half of the
  backend contract.
- **No day-job workload in v1.** The Python/SQL/Jira flows are not the v1 fixture and not the v1
  target. They bring a database, large JSON payloads, external permissions, and sensitive data;
  mixing that risk surface into the runner's own design is how both end up unclear. That case comes
  once the runner is stable.
- **No shipped CI workflow for adopter projects.** The runner must be *invocable* non-interactively
  and must exit with meaningful codes; one reference invocation is documented. A supported,
  maintained GitHub Actions/GitLab pipeline for arbitrary repos is a separate product surface.
- **No new agents and no new reviewers.** Stub fixtures represent the existing roles; the
  follow-up provider path may drive only the existing seven unless its own spec says otherwise.
- **No dashboard, TUI, or web UI.** Output is a state file, a JSONL log, and exit codes.
- **No parallel fan-out beyond the parallelism rule phase 1 already allows.** Determinism first;
  concurrency is a separate risk budget.

## Users / Actors

- **Maintainer** — approves the spec, answers human-gated escalations and reviews the core run
  evidence. Provider credentials are outside 040.
- **Scheduler or shell** — starts the runner non-interactively and consumes its exit code. Spec 040
  proves the process contract with a local subprocess; it does not certify a deployed scheduler.
- **Runner process** — owns parsing, deterministic state transitions, persistence, caps, budget,
  baseline gating, repository fingerprinting and abort/notify behavior.
- **Backend interface** — an internal seam whose supported 040 implementation is the scripted
  stub. The lazy Claude adapter and gated Codex adapter remain experimental source artifacts; their
  execution contract belongs to the follow-up.

## Current behavior

*(Updated 2026-09-01, after T028…T032.)*

- `runner/` exists and its deterministic stub path is covered by a **239-test** suite, including
  parser, counters, budget, state persistence, repair, finalization and subprocess invocation.
- The runner writes the shared `ORCHESTRATION.md` sections but refuses safe re-entry when the
  recorded writer is not `sdd_runner` (AUDIT-2, resolved in the contract by D037).
- A run cannot reach `DONE` without a declared baseline that exits 0 and leaves the tree unchanged.
  All four cases — omitted, non-zero, tree-mutating, green — are observed through the CLI
  subprocess (AUDIT-1, T028; AC-015 as amended by D040).
- `--feature` is resolved through symlinks and contained against the `specs/features/` trail with
  `commonpath`, before any write (AUDIT-5, T029).
- The initial state document is published whole or not at all — fsync to a temporary name, then
  `os.link` — and every fingerprint hashes `git rev-parse HEAD`, so a delegated commit cannot hide
  behind a clean status and diff (AUDIT-6/7, T030/T031).
- `_finalize` stops on 040's side of the seam: a converged run records `CORE-COMPLETE` and exits
  `0`, dispatching no lifecycle skill, computing no closure delta and creating no
  `PR_DESCRIPTION.md` (AUDIT-9, T032/D046).
- Claude and Codex adapter source exists. Claude is lazy and unobserved; Codex is gated shut and
  unobserved. **Neither is a supported 040 backend**, and AUDIT-8 belongs to the follow-up spec.

## Desired behavior

1. **Invocation.** The maintainer or a scheduler runs the runner with a feature path, the supported
   stub backend, caps, a baseline command and optionally a dry-run flag. No TTY is required and no
   prompt is ever shown.
2. **Entry gate.** The runner resolves the repository and feature paths, refuses any lexical or
   symlink escape from `specs/features/`, then re-checks every applicable phase-1 precondition. On
   refusal it exits non-zero, names the condition and remediation, and changes nothing.
3. **Plan.** It parses `TASKS.md`, determines the unchecked tasks, computes the task-relative
   delegation budget once (031 FR-009), and writes the run header into `ORCHESTRATION.md`. If a
   prior run's state exists, it resumes from it instead: completed tasks are not re-delegated, open
   findings are not duplicated, and approvals survive only while their fingerprint matches.
4. **Loop.** Per task: dispatch to the worker, parse the completion block, dispatch the required
   reviewers, parse the verdict blocks, convert REJECT findings into tasks with traceable IDs,
   update the registry, and re-review. Every transition is persisted before the runner proceeds.
5. **Decide.** Escalations are classified explicitly. Human-gated and unclassifiable cases stop,
   are written to `ORCHESTRATION.md`, and notify. Auto-resolvable cases are recorded distinctly
   and pause for the follow-up provider orchestrator; 040 does not dispatch `deep-reasoner`.
6. **Bound.** Counters and budget are enforced arithmetically. An exhausted cap produces a
   recoverable abort naming what failed to converge; an exhausted budget refuses the next dispatch
   rather than making it.
7. **Core completion.** On convergence the runner verifies that a declared baseline passes without
   mutating the tree. The approved fingerprint includes the current `HEAD` object ID. Only then may
   the deterministic core record run result `DONE` and exit `0`. That run result means **core
   complete**, not lifecycle `Status: Done`. The core performs no lifecycle delegation, spec
   transition, `PR_DESCRIPTION.md` generation or closure-delta automation.
8. **Report.** In every case the run leaves `ORCHESTRATION.md` (human-readable) and `run.jsonl`
   (machine-readable), and the exit code names the core outcome.

## Functional requirements

- FR-001: The runner is invocable non-interactively as
  `python3 -m sdd_runner --feature specs/features/<nnn>-<name> --backend stub
  [--stub-script FILE] [--baseline <command>] [--max-iterations N]
  [--max-delegations N] [--dry-run] [--notify <command>]`.
  It requires no TTY, reads no stdin, and never prompts. `--dry-run` performs the entry gate,
  parses `TASKS.md`, prints the plan and the computed budget, and dispatches nothing.
- FR-002: The entry gate enforces every precondition of 031 FR-002 (lifecycle status, zero open
  questions, `TASKS.md` present, not the default branch, no unattributed dirty tree) in code. It
  also proves that the resolved feature directory is contained under the current repository's
  `specs/features/` directory, including through symlinks. Each refusal names the unmet condition
  and remediation and exits with the gate code, leaving the tree untouched. A baseline may be
  omitted while work is in progress, but FR-013 forbids exit `0` without one.
- FR-003: Verdict and completion blocks are parsed by a pure function over the fenced YAML block
  only — never by matching prose. A block that is missing, unparseable, schema-invalid, or carries
  an unknown `verdict`/`status` value **fails closed**: a reviewer response becomes a synthetic
  REJECT and a worker response becomes BLOCKED, both recorded as such with the raw response
  retained for audit.
- FR-004: Caps and budget are enforced arithmetically with exactly 031 FR-009's semantics: a
  per-reviewer consecutive no-progress REJECT counter, a per-finding-identity total REJECT counter,
  and a strictly monotonic total delegation budget defaulting to
  `max(25, 6 × unchecked tasks at first entry)`. Every backend invocation and re-approval consumes
  the budget; deterministic local commands do not. If the follow-up introduces deep-reasoner calls
  or format retries, they consume its same monotonic budget. The runner refuses to dispatch once
  the budget is exhausted rather than dispatching and then noticing.
- FR-005: `ORCHESTRATION.md` is written and read in the shared section schema defined by 031, with
  no added or renamed sections, and is updated before the runner proceeds past any transition.
  Both executors must be able to identify and render the other's document. **Re-entry is
  executor-owned:** the runner resumes only state whose `writer` is `sdd_runner`; a foreign writer
  is refused safely with exit `16`, the writer and remediation named, and no state mutation. An
  interactive executor applies the reciprocal rule unless a future compatibility spec defines a
  versioned hand-off.

  > **Narrowed 2026-08-31 (D034, AUDIT-2).** Bidirectional continuation was an unsafe promise, not
  > an implementation gap. Shared readability is retained; cross-executor reconstruction is not.
- FR-006: The escalation rule of 031 FR-005 is implemented as an explicit classification step.
  Human-gated categories (product/UX behavior, money, personal data, public contracts, destructive
  operations, anything contradicting the SPEC) halt the run; the runner never reclassifies a
  human-gated escalation as auto-resolvable, and an unclassifiable escalation is treated as
  human-gated. The core records an auto-resolvable classification but does not dispatch a provider
  to resolve it. Provider routing and the canonical one-time format re-request are owned by the
  follow-up spec (D034); their absence is not a 040 conformance failure.
- FR-007: Notification is pluggable and service-agnostic. The default sink writes the escalation or
  abort to `ORCHESTRATION.md` and to stderr; `--notify <command>` additionally executes a
  user-supplied command with the event as JSON on stdin. The runner notifies on human-gated
  escalation, on abort, and on completion — never per task, and never mid-loop for progress.
- FR-008: One backend interface, one supported implementation in 040. `stub` is always present and
  deterministic (FR-016). Existing `claude` and `codex` modules may remain in the tree as
  experimental adapters, but they are outside 040's supported and conformance-tested surface:
  Claude stays optional and lazily imported; Codex stays gated shut by default per FR-017.
- FR-009: The backend interface accepts a system prompt, task prompt, path scope and timeout as
  data. Provider-specific interpretation of `agents/*.md`, tool permissions and writer scope is
  not executed or certified by 040; the follow-up must keep those files as the single source of
  truth and define an enforceable writer-scope contract.
- FR-010: Transport retry, provider timeout and the canonical one-time format re-request are
  follow-up responsibilities. The deterministic core still charges every backend invocation to the
  monotonic budget and fails closed on any failure value returned through the interface.
- FR-011: The runner emits `run.jsonl` next to `ORCHESTRATION.md`: one JSON object per event
  (dispatch, response, parse result, verdict, counter change, escalation, abort, core completion)
  with timestamps and the attempt ID. Credentials, API keys, and environment secrets are never
  written to it or to `ORCHESTRATION.md`.
- FR-012: The runner never runs `git commit`, `git push`, or `git merge`, never edits a spec
  `Status` line directly, and never writes its own artifacts outside the contained feature folder.
  Its repository fingerprint includes both the dirty-tree material and `git rev-parse HEAD`, so a
  delegated commit is observable. Enforcement of paths written by real provider sessions belongs
  to the follow-up provider contract.
- FR-013: Exit codes are distinct and documented, so a scheduler can branch on the code alone:
  `0` core converged **and a declared baseline passed without mutating the tree**; `10` gate
  refusal; `11` classified escalation; `12` cap non-convergence abort;
  `13` budget exhaustion; `14` backend precondition failure; `15` a concurrent run already owns
  the feature folder; `16` the persisted state cannot be resumed (corrupt, written by another
  executor, or contradicting itself); `17` every task was processed but the run did not converge;
  `18` completion evidence could not be proven (the baseline is absent, fails, or mutates the
  tree); `70` internal error. `--baseline` is optional for dry-run, inspection and resumable work,
  but mandatory for exit `0`; `NOT DECLARED` is a gate outcome, never an observation that permits
  run result `DONE`. In 040 that result means deterministic-core completion only and never promotes
  the feature's lifecycle `Status`.

  > **Amended 2026-08-31 (D023).** The original clause named six non-zero codes. Four more were
  > added during implementation — 15 by T013, 16 and 17 by T013/T014, 18 by T014 — because each
  > names an outcome a scheduler must be able to tell apart from the others, and folding any of
  > them into an existing code would have made a corrupt state file indistinguishable from a
  > product question. The list above is now the contract.

  > **Reassigned 2026-08-31 (D034).** Exit `18` now means core completion evidence was not proven,
  > including a missing baseline. Lifecycle/closure refusal leaves with `Finalizer` and may define
  > its own exit contract in the follow-up.
- FR-014: The runner is fully contained. `install.sh`, `install.ps1`, `profiles.json`, the install
  manifest, and `check-consistency.sh`'s rules are **not modified by this feature**; the runner
  declares its own dependencies in its own manifest under `runner/`. On a machine with neither the
  Agent SDK nor the Codex CLI installed, every existing suite passes at its current count and the
  framework installs and behaves exactly as before. The stub runner works there; selecting an
  unavailable experimental provider adapter fails with a named cause and never degrades silently.
- FR-015: A protocol-transcription guard maps each retained 031 core rule to the module and test
  that encode it, validates that mapping against recorded phase-1 artifacts, and fails when a named
  module or test disappears. It does **not** claim behavioral equivalence between two executors;
  D008 proved that comparison has no admissible injection point.
- FR-016: A **stub backend is a first-class, always-present implementation**, not test scaffolding:
  it replays scripted responses deterministically and is what the entire test suite drives. Every
  loop guarantee — caps, budget, resume, fail-closed parsing — is provable without a single
  provider call.
- FR-017: The Codex adapter remains **implemented but gated** and refuses by default, naming
  `DEBT-001`/`DEBT-002`. This preserves the architectural target without making it a 040 functional
  requirement. No document may claim Codex or multi-backend parity. The follow-up provider spec
  owns any opt-in execution and debt closure.
- FR-018: `docs/SDD-ORCHESTRATION.md` documents the runner's experimental classification, the
  stub-only supported boundary, exit codes, notification, same-executor resume and the `_finalize`
  hand-off; `CHANGELOG.md` records the corrected scope.

## Non-functional requirements

- **Performance:** wall-clock is not a target. The controlled quantity is delegation count: the
  budget is a hard ceiling enforced before every stub dispatch. Provider spend and retry behavior
  belong to the follow-up.
- **Security:** the feature path is contained after real-path resolution; ownership is acquired
  atomically; the fingerprint includes `HEAD`; credentials are never written to a config file, CLI
  argument or log. Scripted responses are untrusted input: only the verdict block is acted on.
  `--notify` executes without interpolating response text into a shell string. Real provider
  permissions, allowed tools and writer scope belong to the follow-up.
- **Observability:** every decision the runner makes is reconstructible after the fact from
  `run.jsonl` alone, without the provider transcript. `ORCHESTRATION.md` stays human-first.
- **Maintainability:** protocol semantics exist once. Where the runner must encode a rule from 031,
  it cites the FR it implements, so a future change to 031 has a findable set of call sites.

## API / Interface changes

- **New CLI:** `python3 -m sdd_runner …` as in FR-001, with documented exit codes (FR-013).
- **New internal interface:** a backend protocol with one operation — accept a system prompt, task
  prompt, path scope and timeout; return raw text plus transport metadata. In 040 only the stub's
  behavior is normative.
- **New artifact:** `run.jsonl` per feature folder.
- **Contract promotion, not change:** the verdict and completion blocks defined by 031 FR-003 and
  FR-004 become a machine-parsed contract. Their schema is unchanged by this spec; what changes is
  that a malformed block now has a defined, enforced consequence instead of a reader's judgment.
- **No change** to any skill's invocation, to `profiles.json`, or to the installed skill surface.

## Data model changes

No database, no schema files. New files only:

- `runner/` at the repository root, containing the Python package, its dependency manifest, and
  its tests. Root rather than `scripts/runner/` because `scripts/` is today exclusively executable
  Bash and PowerShell plus `scripts/lib`; a pip package with its own manifest does not belong
  there, and a top-level folder is trivially excludable from the installers (D002).
- `specs/features/<nnn>-<name>/run.jsonl`, append-only, one JSON object per event.

`ORCHESTRATION.md` keeps 031's section schema. Writer-specific fields may differ and are the reason
foreign documents are readable but not resumable by the runner.

## Edge cases

- The stub returns prose with no fenced block, or two blocks, or a block whose YAML parses but
  whose fields are wrong — fail closed per FR-003, with the raw text retained.
- The run is killed (SIGTERM from a CI timeout, machine sleep, `cron` overlap) between dispatch and
  the state write — the next run must find a durable attempt row and re-enter per 031 FR-008
  rather than blindly re-delegating.
- Two runners start on the same feature folder concurrently, from an overlapping `cron` schedule.
- The working tree changed between runs, from a human edit rather than an attempt.
- A reviewer approves, then a later fix moves the fingerprint, invalidating that approval.
- A reviewer flip-flops on the same finding ID across rounds.
- The delegation budget is exhausted exactly at a re-review that would have converged.
- `TASKS.md` is edited by a human while the run is in flight.
- `--notify` command exits non-zero, hangs, or does not exist.
- The feature folder is on a filesystem where the append to `run.jsonl` fails (full disk).
- `--feature` uses `..`, an absolute path outside the repository, or a symlink that escapes
  `specs/features/`.
- Two processes race before either has persisted `ACTIVE`; exactly one acquires ownership.
- A delegation creates a commit and leaves a clean worktree; the changed `HEAD` still invalidates
  the previous fingerprint.

## Acceptance criteria

- AC-001: A contained `Ready` fixture with at least two unchecked tasks and a declared green,
  non-mutating baseline runs through the stub backend from a non-interactive shell with no TTY
  (`</dev/null`) to exit `0`. It leaves `ORCHESTRATION.md` in the shared section schema and a
  `run.jsonl`; it creates no commit, invokes no lifecycle skill and does not create
  `PR_DESCRIPTION.md`.
- AC-002: The runner is invocable with no controlling terminal and no inherited interactive
  session: it requires no TTY, never reads stdin, never prompts, and returns an exit code a
  scheduler can branch on.

  > **Historical narrowing (D030), retained by D034.** The original criterion required an actual
  > `cron`-launched provider run. The locally provable process contract remains in 040; deployed
  > scheduler/provider evidence and former tasks T018/T022 move to the follow-up.
- AC-003: Each entry-gate precondition is violated in turn; each run exits with the gate exit code,
  names that specific condition and remediation, and leaves `git status` byte-identical.
- AC-004: Fixture responses covering a missing block, malformed YAML, an unknown verdict value, and
  two competing blocks each produce the fail-closed outcome of FR-003, recorded with the raw text.
- AC-005: A scripted sequence of REJECT verdicts drives the per-reviewer and per-finding counters to
  values asserted against a hand-computed table derived from 031 FR-009, including the cases that
  must *not* increment (an APPROVE, a REJECT that closes a prior finding, a re-review forced by
  another reviewer's fingerprint move).
- AC-006: With `--max-delegations` set to N, exactly N delegations are dispatched and the N+1st is
  refused before any provider call is made. Observed by a stub backend counting invocations.
- AC-007: A run interrupted mid-delegation, then restarted, re-enters without re-delegating a
  completed task, without duplicating a finding, and without resetting any counter. **Observed
  against the state an interruption leaves behind** — an `ACTIVE` record whose writing process is
  gone — rather than by delivering a real signal to a live run. The distinction is recorded in
  D024: the state is faithful, the path to it is simulated.
- AC-008: A human-gated escalation halts, is recorded verbatim, notifies once with valid JSON on
  stdin and exits `11`. An auto-resolvable fixture is recorded with that classification and also
  pauses without a `deep-reasoner` dispatch; the follow-up owns resolution.
- AC-009: FR-015's protocol-transcription guard passes against the named modules, tests and real
  phase-1 artifacts, while making no claim of cross-executor behavioral equivalence.
- AC-010: On a machine with neither the Agent SDK nor the Codex CLI installed,
  `check-consistency.sh` exits 0 and `check-consistency.test.sh`, `install.test.sh`, and
  `install.test.ps1` all pass at their current counts (42/42, 33/33, 28/28 as of spec 039). The
  stub runner works without either dependency; explicitly selecting an unavailable experimental
  adapter fails with a named cause.
- AC-011: Two runner processes released simultaneously against a feature with no state yield one
  owner and one exit `15`; the loser names the in-flight run and makes no backend call. A later
  process against an already ACTIVE state is refused by the same rule.
- AC-012: `grep` over `run.jsonl` and `ORCHESTRATION.md` from a run performed with a sentinel value
  in `ANTHROPIC_API_KEY` finds no occurrence of that sentinel. **Met 2026-08-31**, both halves:
  redaction is applied at the `run.jsonl` writer and at the `ORCHESTRATION.md` writer. It was not
  met until then — the state file carried a secret an agent echoed, verbatim, on the human-gated
  escalation path — and the gap was found by review, not by the suite. See D025.
- AC-013: Invoking `--backend codex` without `--allow-unverified-backend` refuses before any
  subprocess is spawned, names `DEBT-001`/`DEBT-002`, and exits with the backend-precondition code.
  A `grep` over `README.md`, `CHANGELOG.md`, and `docs/` finds no claim of verified multi-backend
  support. No real `codex exec` delegation is part of 040.
- AC-014: `git diff main --stat` for this feature touches no installer and no manifest:
  `install.sh`, `install.ps1`, `install-all.sh`, `install-all.ps1`, `profiles.json`,
  `settings.template.json`, and the install manifest are byte-identical to `main`. Outside
  `runner/`, `specs/features/040-agent-sdk-runner/` and the test suites, this feature may change
  only documentation, `CHANGELOG.md`, and the **six files named below**.
  > **Amended 2026-09-01 (D047, [[F-4]]).** The original second sentence allowed documentation and
  > `CHANGELOG.md` only, and the delivered work exceeds it: D011's closed-severity-enum
  > clarification had to land in four **protocol contracts**, and the `runner/` package needs two
  > `.gitignore` rules. The criterion was written narrower than the work it authorised. It is
  > widened by **enumeration, not by category** — a category ("contracts", "config") would license
  > the next change nobody vetted. The exception is exactly these six paths and nothing else:
  > `agents/domain-reviewer.md`, `agents/final-conformance-reviewer.md`,
  > `skills/sdd-orchestrate/SKILL.md`, `specs/features/031-autonomous-orchestration-loop/SPEC.md`,
  > `.gitignore`, and `CONTRIBUTING.md`. All four protocol edits are additive and load-bearing:
  > `tests/conformance/test_transcription.ObservedDivergence.test_the_protocol_documents_the_closed_enum`
  > fails without them. **What is unchanged is the property that matters: no installer, no manifest,
  > and no adopter-visible behaviour moves.**
- AC-015: With an otherwise converged stub script, **no baseline outcome other than green and
  non-mutating permits exit `0`**, and each failure is refused at the earliest gate that can see
  it: omitting `--baseline` returns `18` from the closure gate; a non-zero or tree-mutating
  baseline returns `10` from the entry gate, before any delegation. A green non-mutating baseline
  permits exit `0` and records `DONE`. Every one of the four results is asserted from the CLI —
  exit code and persisted run result — not from a verification string the runner wrote about
  itself.

  > **Amended 2026-08-31 (D040, [[AUDIT-1]]).** The original required `18` for all three failures.
  > Two of them cannot reach the closure gate: **031 FR-002 makes a red or tree-mutating baseline
  > an entry-gate refusal**, so the run stops at `10` having done nothing. The two requirements
  > could not both hold and 031's is the more protective, so the criterion now describes the
  > earliest-gate behaviour rather than a single code. What is unchanged is the property that
  > matters: **only a green, non-mutating baseline closes a run.**
- AC-016: `--feature` refuses an absolute external path, a `..` escape and a symlink escape before
  creating `ORCHESTRATION.md` or `run.jsonl`; a real contained feature path is accepted.
- AC-017: The concurrent-start test opens the race before either process writes state and proves
  atomic exclusion: exactly one process acquires the lock and only that process can dispatch.
- AC-018: A test backend that commits during a delegation changes the repository fingerprint even
  when `git status --porcelain -uall` and `git diff HEAD` are both empty; the run fails closed and
  the previous approval cannot survive.
- AC-019: A converged stub run stops at the core side of the `_finalize` seam. The dispatch log
  contains no `lifecycle:*` event, no closure delta is required, and no `PR_DESCRIPTION.md` is
  created. Provider/lifecycle finalization is therefore absent from 040 evidence rather than
  merely unobserved.

## Test scenarios

- **Unit:** the block parser against a fixture corpus (valid, missing, malformed, adversarial,
  double-block, truncated); the counter arithmetic against the FR-009 table; budget accounting
  including retries; escalation classification; exit-code mapping; secret redaction.
- **Integration:** the full loop against a stub backend that replays scripted responses — the
  converge path, the reject-then-fix path, the flip-flop path, the cap-abort path, the
  budget-abort path, same-executor resume, foreign-writer refusal, atomic concurrent start,
  baseline refusal/pass, external-feature refusal, committed-HEAD mutation and the `_finalize`
  boundary.
- **CLI E2E (local, deterministic):** AC-001 and AC-002 through a real subprocess with stdin closed,
  a stub script and a declared baseline. No real provider or lifecycle session is run by 040.

## Audit findings (architecture review, 2026-08-31)

Nine defects, each verified against the code rather than inferred. They are the reason this spec is
classified EXPERIMENTAL and its conformance verdict is PARTIAL. D034 assigns every finding to
either 040 or a follow-up; D035–D038 record later implementation and reconciliation without treating
narrower tests as closure.

| ID | Finding | Severity | Current disposition |
|---|---|---|---|
| AUDIT-1 | **CLOSED 2026-08-31 (D036/D040, T028).** The four verification outcomes are named constants, only a green non-mutating baseline permits `DONE`, and the four cases are asserted through the real CLI. AC-015 was amended to expect the earliest gate that can see each failure, since 031 FR-002 refuses a red or mutating baseline at entry. Original finding:** The original defect was that `DONE` remained reachable with no declared baseline. The runner now blocks that path with exit `18` and only a named green, non-mutating result can close. | **High** | **CLOSED in 040.** The four cases — omitted, non-zero, tree-mutating and green — are asserted through the CLI subprocess; only the green one exits `0` and records `DONE`. |
| AUDIT-2 | **RESOLVED 2026-08-31 (D037) — by narrowing the requirement, not the code.** FR-005 no longer promises bidirectional continuation: shared readability is kept, cross-executor reconstruction is not. The refusal was always the safe behaviour; the requirement was the thing that was wrong. Original finding: **a phase-1 `ORCHESTRATION.md` cannot be resumed.** `resume.inspect` refuses a document whose `writer` is not `sdd_runner`. | **High** under the old FR-005 | **Resolved in the contract.** FR-005 now requires shared readability and same-executor re-entry; foreign writers are refused safely. No runner patch is required. |
| AUDIT-3 | **Auto-resolvable escalation and the canonical format retry are not implemented.** The runner pauses instead of routing to `deep-reasoner`, and fails closed on the first malformed block. | **Medium** | **Follow-up.** Classification remains in 040; provider routing and format re-request leave with the provider path. |
| AUDIT-4 | **`path_scope` is not enforced for writing agents.** Only read-only agents are checked; workers and lifecycle sessions carry repository scope. | **Medium** | **Follow-up.** 040 contains its own writes; enforceable writer scope is a provider-session contract. |
| AUDIT-5 | **CLOSED 2026-09-01 (D042, T029).** Repository root, `specs/features/` root and the requested path are resolved through symlinks and compared with `commonpath`, anchored on the spec trail rather than the repository, before any write. Original finding: **`--feature` was not contained.** D035 adds `abspath`/`commonpath` against the repo, blocking absolute and `..` escapes. | **Medium** | **CLOSED in 040.** Containment is resolved through symlinks against the spec trail and refuses before any artifact exists; the external targets in the test are complete feature folders, so nothing else can produce the refusal. |
| AUDIT-6 | **CLOSED 2026-09-01 (D044/D045).** The exclusion held all along — the reported two-owner failure was sequential resume misread (D044). The real defect was the partial-publication window: the claim made an empty file visible before writing the document, so a contender loaded a truncated state and exited `16`. The initial document is now published whole or not at all. Original finding: **concurrent-start exclusion was not atomic.** D035 adds `O_CREAT|O_EXCL` on the state path. | **Medium** | **CLOSED in 040.** A two-phase barrier at the claim itself observes one owner, one exit `15`, one worker dispatch and no exit `16`, repeatedly and without sleep ordering. |
| AUDIT-7 | **CLOSED 2026-09-01 (T031).** `HEAD` is hashed, and both a committing reviewer and a committing worker are caught after asserting the reviewable tree is pristine — so the detection provably comes from `HEAD` alone. Original finding: **a delegated commit was invisible to the fingerprint.** D035 includes the `HEAD` object ID; direct fingerprint tests now distinguish clean, dirty and committed states. | **High** | **CLOSED in 040.** A committing reviewer aborts out-of-scope and a committing worker stales the earlier approval, both after the reviewable tree is asserted pristine. Provider attribution remains follow-up scope. |
| AUDIT-8 | **The Claude adapter had inherited tools and an inert timeout.** D035 declares tool lists, moves `fail_after` inside the async run, and declares direct `anyio>=4` use. | **High** | **Follow-up — HARDENED, UNOBSERVED.** This out-of-scope change is not 040 evidence; permissions, role wiring and timeout still require a real-provider spec and observation. |
| AUDIT-9 | **CLOSED in 040 on 2026-09-01 (T032, D046).** The cut is made and enforced: a converged run records `CORE-COMPLETE` and stops. Original finding: **scope split** — real providers, lifecycle-skill delegation and closure automation carry a different risk profile from the deterministic core. | — | **CLOSED in 040.** `Loop._close` dispatches no lifecycle skill, computes no closure delta and creates no `PR_DESCRIPTION.md`; restoring either dispatch breaks the boundary tests. The follow-up owns `Finalizer`, lifecycle sessions and closure evidence. |

**What stays in spec 040:** the fail-closed parser, counters, budget, contained entry gate, state
I/O, same-executor resume, repair cycle, atomic ownership, `HEAD`-aware fingerprints, mandatory
completion baseline, run log and stub backend. Claude stays optional/lazy and non-conforming;
Codex stays gated shut.

**What leaves:** AUDIT-3's provider actions, AUDIT-4, AUDIT-8 and AUDIT-9. T018 and T022 are no
longer 040 tasks and must not be run as 040 evidence. The architecture decision is now approved;
the block is architectural rather than temporary: real-token evidence belongs to the follow-up.

## Assumptions

- Provider system prompts remain the existing `agents/*.md` files. How an SDK consumes them is a
  follow-up design question, not a licence for 040 to fork the prompts.
- `python3` is already a declared dependency of this repo (`CONTRIBUTING.md:124`), so the
  *language* is not new. The Agent SDK as a third-party pip package **is** new: this repo has never
  had a non-stdlib Python dependency. FR-014 exists to keep that contained.
- The existing Codex adapter remains gated and the Claude adapter remains lazy, but neither is
  evidence for 040. The optional Claude extra now declares both `claude-agent-sdk` and the directly
  imported `anyio>=4` (D035). The follow-up must observe both providers before claiming parity.
- The verdict/completion block schema of 031 is sufficient to parse without a version field. The
  runner will fail closed on anything it does not recognize, which is the safe behavior with or
  without versioning.
- The runner runs on the maintainer's machine or in CI with the repo checked out and a working
  `git`; it does not need to provision anything.
- Structured-output enforcement and format retry are follow-up provider concerns. The 040 parser
  continues to fail closed on a non-conforming scripted response.

## Open questions

- ~~**OQ-1**: is the runner repo tooling or a shipped artifact?~~ **Resolved 2026-08-31 — repo
  tooling in v1, no installer or manifest changes.** See D001 and FR-014.
- ~~**OQ-2**: what is the first real workload?~~ **Resolved 2026-08-31 — this repo's own specs.
  The day-job Python/SQL/Jira flows are explicitly out of v1.** See D003.
- ~~**OQ-3**: checkpoint commits.~~ **Resolved 2026-08-31 — out of v1, confirmed by the
  maintainer.** An unsupervised runner does not write git history in its first version. Recorded as
  a follow-up owned by the phase that ships downstream distribution. See D005.
- **OQ-4 (non-blocking): DEFERRED at close, 2026-09-01.** Should the verdict block gain an explicit
  schema version? It would make the machine contract self-describing, but it is a change to 031's
  shipped agent contracts and therefore a `/spec-update` against 031, not a change this spec may
  make unilaterally. D011 touched those same four contracts for the severity enum and shows the
  route; nothing in 040 depends on the answer. **Owner: a `/spec-update` against spec 031.**
- **OQ-5 (non-blocking): DEFERRED at close, 2026-09-01.** Notification transport beyond `--notify`.
  A command hook covers every case a maintainer can script; anything richer needs a named
  requirement, and no workload has produced one. **Owner: the follow-up provider spec, if a real
  provider run generates the requirement.**

## Contracted services

`specs/SERVICES.md` does not exist → all billable add-ons treated as NOT contracted (conservative
default). Run `/project-init` to declare them.
