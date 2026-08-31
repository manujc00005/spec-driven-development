# Feature Spec: agent-sdk-runner

## Status

In Review

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
gaps. Both are `Done`. But the loop exists **only as a prompt**: `skills/sdd-orchestrate/SKILL.md`
instructs an orchestrator LLM, inside an interactive Claude Code session, to run it. Four
consequences follow, and none of them are fixable inside phase 1's chosen mechanism.

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

## Goal

A Python runner that executes **the protocol spec 031 already defines** as code rather than as
instructions: it reads `TASKS.md`, opens one provider session per task or review carrying the
corresponding agent's system prompt, parses the verdict and completion blocks programmatically,
enforces caps and budget arithmetically, persists the same `ORCHESTRATION.md` state, retries
transport failures under a bounded policy, emits a machine-readable run log, and interrupts the
human only on a human-gated escalation or a non-success exit.

The success criterion, stated so it can be checked rather than admired: **one `Ready` feature goes
from unchecked tasks in `TASKS.md` to a PR-ready branch with no interactive session, driven by
`cron` or a CI job, producing the same `ORCHESTRATION.md` a phase-1 run would produce — and it
aborts on an exhausted budget instead of spending the account.**

One protocol, two executors. Where the runner and `sdd-orchestrate` disagree about semantics, the
runner is wrong by definition; that is a defect, never a feature.

**v1 boundary (decided 2026-08-31, resolving OQ-1 and OQ-2).** v1 is **maintainer tooling of this
repository**, not a shipped artifact: it does not enter the installers, `profiles.json`, or the
install manifest, and no adopter project inherits a pip dependency because of it. Its first real
workload is this repo's own specs. Downstream distribution is a later phase, gated on this runner
having an observed track record — the same reasoning that keeps checkpoint commits out of v1.

## Non-goals

- **No new loop semantics.** Specs 031 and 032 own the protocol: the entry gate, the escalation
  split, the two non-convergence counters, the finding registry, fingerprint invalidation, the
  closure freeze. This feature re-implements them faithfully. Any semantic change needs
  `/spec-update` against 031, not a quiet divergence here.
- **No replacement of `/sdd-orchestrate`.** The interactive skill stays, unchanged in behavior, and
  remains the recommended path for attended work.
- **No auto-commit of the feature work, no push, no merge, no spec-Status promotion** outside the
  owning lifecycle skills. Every phase-1 prohibition survives.
- **No checkpoint commits in this spec**, despite 031 parking them here. Giving the first
  unattended executor the power to write git history on its very first release multiplies the blast
  radius of every other defect in it. This is a deliberate deferral, recorded so it is not lost:
  it belongs in a follow-up once the runner has an observed track record. See Open questions OQ-3.
- **No distribution to adopter projects in v1.** The runner is not installed by `install.sh` or
  `install.ps1`, is not listed in `profiles.json` or the install manifest, and is not assumed to
  exist in any downstream project. A machine with neither the Agent SDK nor the Codex CLI installed
  must keep using this framework exactly as it does today — that is a hard requirement (FR-014),
  not an aspiration.
- **No day-job workload in v1.** The Python/SQL/Jira flows are not the v1 fixture and not the v1
  target. They bring a database, large JSON payloads, external permissions, and sensitive data;
  mixing that risk surface into the runner's own design is how both end up unclear. That case comes
  once the runner is stable.
- **No shipped CI workflow for adopter projects.** The runner must be *invocable* non-interactively
  and must exit with meaningful codes; one reference invocation is documented. A supported,
  maintained GitHub Actions/GitLab pipeline for arbitrary repos is a separate product surface.
- **No new agents and no new reviewers.** The runner drives the existing seven.
- **No dashboard, TUI, or web UI.** Output is a state file, a JSONL log, and exit codes.
- **No parallel fan-out beyond the parallelism rule phase 1 already allows.** Determinism first;
  concurrency is a separate risk budget.

## Users / Actors

- **Maintainer** — approves the spec, answers human-gated escalations, reviews the resulting PR,
  and owns the credentials the runner uses.
- **Scheduler** (`cron`, CI job, `launchd`, manual `nohup`) — starts the runner non-interactively
  and consumes its exit code.
- **Runner process** — owns the loop: dispatch, parse, decide, persist, retry, abort, notify.
- **Backend adapter** — Claude Agent SDK (Python) or `codex exec` subprocess. Interchangeable
  behind one interface.
- **Delegated agents** — the seven existing agents under `agents/`, whose markdown files are the
  system prompts the runner sends. They remain the single source of truth for agent behavior.

## Current behavior

- `sdd-orchestrate --autonomous <feature-path>` runs the loop inside an interactive Claude Code
  session. It requires the Agent tool, and therefore Claude Code.
- Verdict blocks (`verdict: APPROVE | REJECT` + `findings`) and completion blocks
  (`status: DONE | BLOCKED`) are emitted by the agents as fenced YAML and read by the orchestrator
  LLM. No code parses them anywhere in the repo.
- Loop state lives in `specs/features/<nnn>-<name>/ORCHESTRATION.md`, written by the orchestrator.
- Caps and the delegation budget are counted by the orchestrator, following prose rules.
- The Codex path is documented as a sequential degradation (031 FR-012) and has never been run.
- The repo contains no Python package: `python3` is used only as inline stdlib heredocs inside Bash
  scripts (`check-consistency.sh`, `export-personal-config.sh`, tests). There is no
  `requirements.txt`, no virtualenv, and no third-party Python dependency anywhere.
  `CONTRIBUTING.md:124` states the dependency budget as "`bash`, `python3` (installer/harness), and
  optionally `pwsh`".

## Desired behavior

1. **Invocation.** The maintainer or a scheduler runs the runner with a feature path, optionally a
   backend, caps, and a dry-run flag. No TTY is required and no prompt is ever shown.
2. **Entry gate.** The runner re-checks every phase-1 precondition. On any unmet condition it exits
   non-zero, naming the condition and its remediation, having changed nothing.
3. **Plan.** It parses `TASKS.md`, determines the unchecked tasks, computes the task-relative
   delegation budget once (031 FR-009), and writes the run header into `ORCHESTRATION.md`. If a
   prior run's state exists, it resumes from it instead: completed tasks are not re-delegated, open
   findings are not duplicated, and approvals survive only while their fingerprint matches.
4. **Loop.** Per task: dispatch to the worker, parse the completion block, dispatch the required
   reviewers, parse the verdict blocks, convert REJECT findings into tasks with traceable IDs,
   update the registry, and re-review. Every transition is persisted before the runner proceeds.
5. **Decide.** Auto-resolvable escalations go to the deep-reasoner and are recorded in
   `DECISIONS.md` before re-delegation. Human-gated escalations stop the run, are written to
   `ORCHESTRATION.md`, and notify.
6. **Bound.** Counters and budget are enforced arithmetically. An exhausted cap produces a
   recoverable abort naming what failed to converge; an exhausted budget refuses the next dispatch
   rather than making it.
7. **Finalize.** On convergence the runner freezes the approved fingerprint, invokes the owning
   lifecycle skills for closure, verifies the closure delta against the allowlist, and exits 0 with
   an unstaged working tree on a dedicated branch plus `PR_DESCRIPTION.md`.
8. **Report.** In every case the run leaves `ORCHESTRATION.md` (human-readable) and `run.jsonl`
   (machine-readable), and the exit code says which of the seven outcomes occurred.

## Functional requirements

- FR-001: The runner is invocable non-interactively as
  `python3 -m sdd_runner --feature specs/features/<nnn>-<name> [--backend claude|codex]
  [--max-iterations N] [--max-delegations N] [--dry-run] [--notify <command>]`.
  It requires no TTY, reads no stdin, and never prompts. `--dry-run` performs the entry gate,
  parses `TASKS.md`, prints the plan and the computed budget, and dispatches nothing.
- FR-002: The entry gate enforces every precondition of 031 FR-002 (lifecycle status, zero open
  questions, `TASKS.md` present, not the default branch, no unattributed dirty tree, green
  non-mutating baseline suite) in code. Each refusal names the unmet condition and its remediation
  and exits with the gate exit code, leaving the tree untouched.
- FR-003: Verdict and completion blocks are parsed by a pure function over the fenced YAML block
  only — never by matching prose. A block that is missing, unparseable, schema-invalid, or carries
  an unknown `verdict`/`status` value **fails closed**: a reviewer response becomes a synthetic
  REJECT and a worker response becomes BLOCKED, both recorded as such with the raw response
  retained for audit.
- FR-004: Caps and budget are enforced arithmetically with exactly 031 FR-009's semantics: a
  per-reviewer consecutive no-progress REJECT counter, a per-finding-identity total REJECT counter,
  and a strictly monotonic total delegation budget defaulting to
  `max(25, 6 × unchecked tasks at first entry)`. Re-approvals, deep-reasoner calls, and
  structured-output retries consume the budget; deterministic local commands do not. The runner
  refuses to dispatch once the budget is exhausted rather than dispatching and then noticing.
- FR-005: `ORCHESTRATION.md` is written and re-read in the schema 031 defines, with no added or
  renamed sections, and is updated before the runner proceeds past any transition. A run started
  by the runner must be resumable by an interactive `sdd-orchestrate` session and vice versa.
- FR-006: The escalation rule of 031 FR-005 is implemented as an explicit classification step.
  Human-gated categories (product/UX behavior, money, personal data, public contracts, destructive
  operations, anything contradicting the SPEC) halt the run; the runner never reclassifies a
  human-gated escalation as auto-resolvable, and an unclassifiable escalation is treated as
  human-gated.
- FR-007: Notification is pluggable and service-agnostic. The default sink writes the escalation or
  abort to `ORCHESTRATION.md` and to stderr; `--notify <command>` additionally executes a
  user-supplied command with the event as JSON on stdin. The runner notifies on human-gated
  escalation, on abort, and on completion — never per task, and never mid-loop for progress.
- FR-008: One backend interface, two implementations. `claude` uses the Claude Agent SDK for
  Python; `codex` shells out to `codex exec` with the isolation flag set the repo already enforces
  in `scripts/skill-eval.sh` (`--ignore-user-config`, `--ephemeral`, `--model`), and is gated per
  FR-017. A third implementation, `stub`, is always present (FR-016). A backend whose preconditions
  are unmet (missing SDK, missing CLI, missing credentials, unaccepted flags, or an unverified
  backend without its opt-in) fails at startup with a named cause, never mid-run.
- FR-009: Agent system prompts are read from `agents/*.md` at run time. The runner does not embed,
  duplicate, or paraphrase agent instructions; those files stay the single source of truth.
- FR-010: Transport and transient provider failures are retried under a bounded policy (finite
  attempts, exponential backoff, per-attempt timeout). Every retry consumes the delegation budget
  and is recorded. Exhausted retries fail the delegation closed, not silently.
- FR-011: The runner emits `run.jsonl` next to `ORCHESTRATION.md`: one JSON object per event
  (dispatch, response, parse result, verdict, counter change, escalation, retry, abort,
  finalization) with timestamps and the attempt ID. Credentials, API keys, and environment secrets
  are never written to it or to `ORCHESTRATION.md`.
- FR-012: The runner never runs `git commit`, `git push`, or `git merge`, never edits a spec
  `Status` line directly, and never writes outside the feature folder and the paths the delegated
  agents are scoped to.
- FR-013: Exit codes are distinct and documented, so a scheduler can branch on the code alone:
  `0` converged; `10` gate refusal; `11` human-gated escalation; `12` cap non-convergence abort;
  `13` budget exhaustion; `14` backend precondition failure; `15` a concurrent run already owns
  the feature folder; `16` the persisted state cannot be resumed (corrupt, written by another
  executor, or contradicting itself); `17` every task was processed but the run did not converge;
  `18` closure could not be proven (an unexpected closure delta, or an owning lifecycle skill that
  refused); `70` internal error.

  > **Amended 2026-08-31 (D023).** The original clause named six non-zero codes. Four more were
  > added during implementation — 15 by T013, 16 and 17 by T013/T014, 18 by T014 — because each
  > names an outcome a scheduler must be able to tell apart from the others, and folding any of
  > them into an existing code would have made a corrupt state file indistinguishable from a
  > product question. The list above is now the contract.
- FR-014: The runner is fully contained. `install.sh`, `install.ps1`, `profiles.json`, the install
  manifest, and `check-consistency.sh`'s rules are **not modified by this feature**; the runner
  declares its own dependencies in its own manifest under `runner/`. On a machine with neither the
  Agent SDK nor the Codex CLI installed, every existing suite passes at its current count and the
  framework installs and behaves exactly as before. Invoking the runner there fails with a named
  missing dependency and an install hint — it never degrades silently.
- FR-015: A conformance test proves the runner and `sdd-orchestrate` agree on the protocol: the
  same fixture responses drive both to the same verdicts, the same counter values, and the same
  `ORCHESTRATION.md` state transitions.
- FR-016: A **stub backend is a first-class, always-present implementation**, not test scaffolding:
  it replays scripted responses deterministically and is what the entire test suite drives. Every
  loop guarantee — caps, budget, resume, fail-closed parsing — is provable without a single
  provider call.
- FR-017: The Codex backend ships **implemented but gated**. It is a real implementation of the
  backend interface (so the abstraction carries two loads, not one plus a comment), and it refuses
  to run by default, naming `DEBT-001`/`DEBT-002` and the fact that its flag set has never been
  exercised against a real CLI. An explicit `--allow-unverified-backend` opt-in is required to
  invoke it — the precedent `scripts/skill-eval.sh` already set with `--allow-unisolated`. Codex is
  therefore an architectural target of v1 and not a functional requirement of it: multi-backend
  parity **must not be claimed anywhere** — docs, CHANGELOG, or README — until a real `codex exec`
  run records the accepted flag spellings. If the CLI becomes available during implementation, that
  run is performed and the debts are closed; if it does not, v1 ships with the gate shut and says
  so.
- FR-018: `docs/SDD-ORCHESTRATION.md` documents the runner — invocation, exit codes, backends,
  notification, resume, and the phase-1/phase-2 boundary — and `CHANGELOG.md` records the feature.

## Non-functional requirements

- **Performance:** wall-clock is dominated by provider latency and is not a target. The controlled
  quantity is spend: the delegation budget is a hard ceiling enforced before dispatch, and an
  unattended overnight run must not be able to exceed it under any code path, including retries.
- **Security:** credentials come from the environment only — never a config file in the repo, never
  a CLI argument, never a log line. The runner executes in a dedicated branch or worktree with a
  permission posture it states explicitly rather than inherits. Agent responses are untrusted
  input: a response that contains instructions to the runner is data, and only the verdict block is
  ever acted on. `--notify` executes a user-supplied command and must not interpolate agent output
  into a shell string.
- **Observability:** every decision the runner makes is reconstructible after the fact from
  `run.jsonl` alone, without the provider transcript. `ORCHESTRATION.md` stays human-first.
- **Maintainability:** protocol semantics exist once. Where the runner must encode a rule from 031,
  it cites the FR it implements, so a future change to 031 has a findable set of call sites.

## API / Interface changes

- **New CLI:** `python3 -m sdd_runner …` as in FR-001, with documented exit codes (FR-013).
- **New internal interface:** a backend protocol with one operation — run a session given a system
  prompt, a task prompt, a path scope, and a timeout; return raw text plus transport metadata.
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

`ORCHESTRATION.md` keeps 031's schema verbatim.

## Edge cases

- The provider returns prose with no fenced block, or two blocks, or a block whose YAML parses but
  whose fields are wrong — fail closed per FR-003, with the raw text retained.
- The provider truncates mid-block, or the session hits a context limit.
- The run is killed (SIGTERM from a CI timeout, machine sleep, `cron` overlap) between dispatch and
  the state write — the next run must find a durable attempt row and re-enter per 031 FR-008
  rather than blindly re-delegating.
- Two runners start on the same feature folder concurrently, from an overlapping `cron` schedule.
- The working tree changed between runs, from a human edit rather than an attempt.
- A reviewer approves, then a later fix moves the fingerprint, invalidating that approval.
- A reviewer flip-flops on the same finding ID across rounds.
- The delegation budget is exhausted exactly at a re-review that would have converged.
- Credentials expire mid-run; the provider rate-limits; the network drops.
- The Agent SDK is installed but at an incompatible version; the Codex CLI rejects a flag spelling.
- `TASKS.md` is edited by a human while the run is in flight.
- `--notify` command exits non-zero, hangs, or does not exist.
- The feature folder is on a filesystem where the append to `run.jsonl` fails (full disk).
- A delegated agent writes outside its allowed path scope.

## Acceptance criteria

- AC-001: A `Ready` fixture feature with at least two unchecked tasks runs from a non-interactive
  shell with no TTY (`</dev/null`) to exit `0`, leaving an unstaged tree on a non-default branch,
  an `ORCHESTRATION.md` whose sections match 031's schema and a `run.jsonl`. No commit exists that
  the runner created.

  > **Downgraded 2026-08-31 (D030, [[DEBT-009]]).** Two clauses were removed because no evidence
  > for them can be produced on this machine: *"With the Claude backend"* and *"and a
  > `PR_DESCRIPTION.md`"*. What remains is observed against the deterministic stub backend
  > (`test_finalization.HappyPath`). The provider half and the generated PR description move to
  > DEBT-009 and gate `Done`.
- AC-002: The runner is invocable with no controlling terminal and no inherited interactive
  session: it requires no TTY, never reads stdin, never prompts, and returns an exit code a
  scheduler can branch on.

  > **Downgraded 2026-08-31 (D030, [[DEBT-009]]).** The original criterion required an actual
  > `cron`-launched run reaching exit `0`, and **it had no evidence at all** — its only coverage
  > was T018 and T022, both blocked on a provider this machine does not have. What remains is the
  > property the code can demonstrate here: the CLI's non-interactive contract, exercised with
  > `</dev/null` and asserted through the exit-code mapping. **Nobody has watched this runner start
  > from `cron`**, and that sentence is the debt, not a footnote to it.
- AC-003: Each entry-gate precondition is violated in turn; each run exits with the gate exit code,
  names that specific condition and its remediation, and leaves `git status` byte-identical.
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
- AC-008: A human-gated escalation (a fixture BLOCKED response naming a product decision) halts the
  run, writes the escalation verbatim to `ORCHESTRATION.md`, invokes the `--notify` command once
  with valid JSON on stdin, and exits with the escalation exit code.
- AC-009: FR-015's conformance test passes: identical fixture responses produce identical verdicts
  and identical counter values through both executors.
- AC-010: On a machine with neither the Agent SDK nor the Codex CLI installed,
  `check-consistency.sh` exits 0 and `check-consistency.test.sh`, `install.test.sh`, and
  `install.test.ps1` all pass at their current counts (42/42, 33/33, 28/28 as of spec 039), and
  invoking the runner fails with a named missing dependency and an install hint.
- AC-014: `git diff main --stat` for this feature touches no installer and no manifest:
  `install.sh`, `install.ps1`, `install-all.sh`, `install-all.ps1`, `profiles.json`,
  `settings.template.json`, and the install manifest are byte-identical to `main`. Documentation
  and `CHANGELOG.md` are the only files outside `runner/`, `specs/features/040-agent-sdk-runner/`,
  and the test suites that this feature may change.
- AC-011: A second runner started against a feature folder with an ACTIVE run refuses to start,
  naming the in-flight run, and makes no provider call.
- AC-012: `grep` over `run.jsonl` and `ORCHESTRATION.md` from a run performed with a sentinel value
  in `ANTHROPIC_API_KEY` finds no occurrence of that sentinel. **Met 2026-08-31**, both halves:
  redaction is applied at the `run.jsonl` writer and at the `ORCHESTRATION.md` writer. It was not
  met until then — the state file carried a secret an agent echoed, verbatim, on the human-gated
  escalation path — and the gap was found by review, not by the suite. See D025.
- AC-013: Invoking `--backend codex` without `--allow-unverified-backend` refuses before any
  subprocess is spawned, names `DEBT-001`/`DEBT-002`, and exits with the backend-precondition code.
  A `grep` over `README.md`, `CHANGELOG.md`, and `docs/` finds no claim of verified multi-backend
  support. **If** a Codex CLI is available during implementation, one real `codex exec` delegation
  completes, the accepted flag spellings are recorded, and `DEBT-001`/`DEBT-002` are updated —
  otherwise this clause is explicitly reported as not observed rather than assumed.

## Test scenarios

- **Unit:** the block parser against a fixture corpus (valid, missing, malformed, adversarial,
  double-block, truncated); the counter arithmetic against the FR-009 table; budget accounting
  including retries; escalation classification; exit-code mapping; secret redaction.
- **Integration:** the full loop against a stub backend that replays scripted responses — the
  converge path, the reject-then-fix path, the flip-flop path, the cap-abort path, the
  budget-abort path, the SIGTERM-and-resume path, the concurrent-run refusal.
- **E2E:** AC-001 and AC-002 against a real provider on a small fixture feature, once per backend.
- **Manual:** an overnight unattended run on a real feature of this repo, with the resulting
  `ORCHESTRATION.md` and `run.jsonl` read start to finish by the maintainer; and the AC-013 Codex
  invocation on a machine where the CLI is installed.

## Assumptions

- Agent system prompts are the existing `agents/*.md` files, read at run time. If that turns out to
  be insufficient — because the SDK needs a different prompt shape than the Claude Code agent
  frontmatter provides — that is a design finding for `/spec-plan`, not a licence to fork the
  prompts.
- `python3` is already a declared dependency of this repo (`CONTRIBUTING.md:124`), so the
  *language* is not new. The Agent SDK as a third-party pip package **is** new: this repo has never
  had a non-stdlib Python dependency. FR-014 exists to keep that contained.
- The framework's rule that no feature may be Claude-Code-only is honored by *implementing* the
  Codex backend in v1 rather than by describing it (FR-017). What v1 does not do is *claim* it
  works. This is a deliberate narrowing of the usual "provider verification gates `Done`"
  convention, taken because the CLI is absent from this machine and the alternative — shipping a
  prose-only Codex path — is precisely how `DEBT-002` came to exist. See D004.
- The verdict/completion block schema of 031 is sufficient to parse without a version field. The
  runner will fail closed on anything it does not recognize, which is the safe behavior with or
  without versioning.
- The runner runs on the maintainer's machine or in CI with the repo checked out and a working
  `git`; it does not need to provision anything.
- Structured-output enforcement, if the SDK offers it, is an implementation choice for the plan —
  the spec requires only that a non-conforming response fail closed.

## Open questions

- ~~**OQ-1**: is the runner repo tooling or a shipped artifact?~~ **Resolved 2026-08-31 — repo
  tooling in v1, no installer or manifest changes.** See D001 and FR-014.
- ~~**OQ-2**: what is the first real workload?~~ **Resolved 2026-08-31 — this repo's own specs.
  The day-job Python/SQL/Jira flows are explicitly out of v1.** See D003.
- ~~**OQ-3**: checkpoint commits.~~ **Resolved 2026-08-31 — out of v1, confirmed by the
  maintainer.** An unsupervised runner does not write git history in its first version. Recorded as
  a follow-up owned by the phase that ships downstream distribution. See D005.
- **OQ-4 (non-blocking):** should the verdict block gain an explicit schema version? It would make
  the machine contract self-describing, but it is a change to 031's shipped agent contracts and
  therefore a `/spec-update` against 031, not a change this spec may make unilaterally.
- **OQ-5 (non-blocking):** notification transport beyond `--notify`. A command hook covers every
  case a maintainer can script; anything richer needs a named requirement.

## Contracted services

`specs/SERVICES.md` does not exist → all billable add-ons treated as NOT contracted (conservative
default). Run `/project-init` to declare them.
