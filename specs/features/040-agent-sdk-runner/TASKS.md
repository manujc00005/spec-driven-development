# Tasks: agent-sdk-runner

<!-- Verify clauses follow specs/_templates/TASKS.md: an executable command, or a human check that
     names who checks and against what. Nothing executes these; they are the criterion a human or
     an agent acts on to call the task done. -->

## Phase 1: Preparation

- [x] T001 - Create the `runner/` package skeleton at the repository root with its own dependency
  manifest declaring `claude-agent-sdk` and the Python floor, plus an empty `runner/tests/` tree.
  Confirm `scripts/check-consistency.sh` has no rule that a new top-level folder violates.
  Covers: AC-014. Verify: `bash scripts/check-consistency.sh` exits 0 and
  `git diff --name-only main -- install.sh install.ps1 install-all.sh install-all.ps1
  profiles.json settings.template.json` prints nothing.

- [x] T002 - Build the fixture corpus: agent responses (valid APPROVE, valid REJECT with findings,
  valid DONE, valid BLOCKED, missing block, malformed YAML, unknown verdict value, two competing
  blocks, truncated mid-block, and an adversarial response whose *prose* contains a fake verdict
  block) plus a minimal fixture feature folder with a `SPEC.md`, a two-task `TASKS.md`, and a
  `DECISIONS.md`. Covers: AC-004, AC-005. Verify: `ls runner/tests/fixtures/responses/` lists all ten
  named cases, and the fixture feature folder satisfies every 031 FR-002 precondition when checked
  by hand against that FR's list — no dependency on unwritten code.

- [x] T003 - Implement `blocks.py`: a pure fail-closed parser over the fenced YAML block only.
  A missing, unparseable, schema-invalid, duplicated, or unknown-valued block yields a synthetic
  REJECT (reviewer) or BLOCKED (worker), retaining the raw response. Never matches prose.
  Covers: AC-004. Verify: `python3 -m unittest tests.unit.test_blocks` passes with every
  T002 fixture asserted, including the adversarial one resolving to a synthetic REJECT.

## Phase 2: Implementation

- [x] T004 - Implement `state.py`: read and write `ORCHESTRATION.md` in spec 031's schema (State,
  Attempts, Findings, Delegation log, Escalations, Cap changes, Closure delta, Run result) with no
  added or renamed sections. Covers: AC-001, AC-007. Verify:
  `python3 -m unittest tests.unit.test_state` passes a round-trip against both real
  phase-1 artifacts in this repo — `specs/features/032-autonomous-loop-residual-calibration/ORCHESTRATION.md`
  and `specs/features/033-task-verification-criterion/ORCHESTRATION.md` — byte-identical after
  read-then-write.

- [x] T005 - Implement `counters.py` and `budget.py` with spec 031 FR-009 semantics exactly: the
  per-reviewer consecutive no-progress REJECT counter, the per-finding-identity total REJECT
  counter, and the strictly monotonic delegation budget defaulting to
  `max(25, 6 × unchecked tasks at first entry)`. Retries and re-approvals consume budget;
  deterministic local commands do not. Covers: AC-005, AC-006. Verify:
  `python3 -m unittest tests.unit.test_counters` passes against the hand-computed table in
  the test file, whose expected values are derived line by line from 031 FR-009 and cited as such.

- [x] T006 - Implement `escalation.py`: classify an escalation as auto-resolvable or human-gated per
  031 FR-005. Any human-gated category (product/UX, money, personal data, public contracts,
  destructive operations, SPEC contradiction) wins, and an unclassifiable escalation is human-gated.
  Covers: AC-008. Verify: `python3 -m unittest tests.unit.test_escalation` passes one case
  per category plus an unclassifiable case that must resolve to human-gated.

- [x] T007 - Define the `Backend` protocol (system prompt, task prompt, path scope, timeout → raw
  text plus transport metadata) and implement the always-present `stub` backend that replays
  scripted responses deterministically. Covers: AC-004, AC-005, AC-006. Verify:
  `python3 -m unittest tests.unit.test_backends` passes, and the stub records an
  invocation count that a test can assert on.

- [x] T008 - Implement the `claude` backend over the Claude Agent SDK, importing the SDK lazily so
  its absence breaks nothing else. System prompts are read from `agents/*.md` at run time and never
  paraphrased. Covers: AC-001, AC-010. Verify: with the SDK uninstalled,
  `python3 -m unittest discover -s runner/tests -t runner` passes in full and `python3 -m sdd_runner --backend claude
  --feature <fixture>` exits with the backend-precondition code naming the missing dependency.

- [x] T009 - Implement the `codex` backend as a real `codex exec` subprocess call using the flag set
  `scripts/skill-eval.sh` enforces, gated shut by default: without `--allow-unverified-backend` it
  refuses before spawning anything, naming DEBT-001 and DEBT-002. Covers: AC-013. Verify:
  `python3 -m sdd_runner --backend codex --feature <fixture>` exits with the backend-precondition
  code, its message names both debts, and `grep -ri "multi-backend\|paridad\|parity" README.md
  CHANGELOG.md docs/` returns no claim that Codex is verified.

- [x] T010 - Implement `retry.py`: bounded attempts, exponential backoff, per-attempt timeout, every
  retry charged to the delegation budget, exhausted retries failing the delegation closed.
  Covers: AC-006. Verify: `python3 -m unittest tests.unit.test_retry` asserts that N
  retries decrement the budget by N and that exhaustion produces a failed-closed delegation.

- [x] T011 - Implement `log.py`: append-only `run.jsonl` with one JSON object per event, and
  redaction applied at the writer so no call site can bypass it. Covers: AC-012. Verify:
  `python3 -m unittest tests.unit.test_log` writes events containing a sentinel secret and
  asserts the sentinel is absent from the resulting file.

- [x] T012 - Implement `__main__.py`: the CLI of FR-001, the entry gate of FR-002 enforcing every
  031 precondition, the exit-code mapping of FR-013, and the `--notify` sink executed without a
  shell with the event as JSON on stdin. Covers: AC-003, AC-008. Verify: a script violating each
  precondition in turn shows every run exiting with the gate code, naming that condition and its
  remediation, with `git status --porcelain` byte-identical before and after each.

- [x] T013 - Implement `loop.py`: the driver composing core, backends and infrastructure — entry
  gate, plan, dispatch, parse, reviewers, findings-to-tasks, re-review, converge or abort — writing
  state before proceeding past any transition, resuming idempotently per 031 FR-011, and refusing
  to start when an ACTIVE run is recorded. Covers: AC-001, AC-007, AC-011. Verify:
  `python3 -m unittest tests.integration.test_loop tests.integration.test_resume` passes the
  converge, resume and concurrent-refusal cases against the stub backend — 37 integration tests,
  including resume-after-completed-task, resume-after-blocked-task, resume-with-exhausted-budget,
  eleven corrupt-state blocks, and the ACTIVE-but-dead-pid recovery.

- [ ] T014 - Implement finalization: freeze the approved fingerprint, invoke the owning lifecycle
  skills for closure, verify the closure delta against the allowlist per 031 FR-013, and guarantee
  the runner never commits, pushes, merges, or edits a spec `Status` line. Covers: AC-001.
  Verify: after an integration converge run, `git log --oneline main..HEAD` is empty, the feature's
  `SPEC.md` `Status` line is unchanged by the runner, and `PR_DESCRIPTION.md` exists.

## Phase 3: Tests

- [x] T015 - Complete the unit suite: parser corpus, counter table, budget accounting, escalation
  categories, exit-code mapping, redaction, state round-trip. Covers: AC-004, AC-005, AC-012.
  Verify: `python3 -m unittest discover -s runner/tests/unit -t runner` passes with every T002 fixture exercised and the
  run reports zero skipped tests.

- [ ] T016 - Complete the integration suite against the stub: converge, reject-then-fix, flip-flop
  on one finding ID, per-reviewer cap abort, per-finding cap abort, budget refusal, SIGTERM-and-
  resume, concurrent-run refusal, human-gated escalation invoking `--notify`, and the Codex gate
  refusal. Covers: AC-003, AC-006, AC-007, AC-008, AC-011, AC-013. Verify:
  `python3 -m unittest discover -s runner/tests/integration -t runner` passes all ten scenarios, and the budget case
  asserts the stub's invocation counter equals N with the N+1st never dispatched.

  **[PARTIAL 2026-08-31]** Seven of the ten scenarios are green (converge, reject-then-fix, malformed review, malformed worker, budget refusal, reviewer cap abort, human escalation with `--notify`, technical escalation, concurrent refusal, Codex gate). **Missing: the flip-flop scenario at loop level, the per-finding cap abort at loop level, and SIGTERM-and-resume**. T013 unblocked the last of these and
  `runner/tests/integration/test_resume.py` now covers it; the two cap scenarios remain.

- [x] T017 - **[REPLACED 2026-08-31 — D008]** The original two-executor conformance test is not
  viable: `sdd-orchestrate` delegates through the Agent tool with no injection point for scripted
  responses, spec 032's PLAN already ruled scripted reviewers inadmissible as evidence, and
  `skill-eval.sh` is single-turn. Delivered instead: a protocol transcription guard —
  `runner/tests/conformance/PROTOCOL_TRANSCRIPTION.md` (clause → module → test) plus
  `test_transcription.py`, which fails when the table names a module or test that does not exist,
  and checks the runner's model against the real recorded phase-1 artifacts of specs 032 and 033.
  Covers: AC-009. Verify: `python3 -m unittest discover -s runner/tests/conformance -t runner`
  passes; the guard demonstrably bites — it failed on first run for a missing `test_gate.py`, which
  was then written. **R1 is partially mitigated, not eliminated** (D008).

- [ ] T018 - Run the two E2E scenarios against a real provider on the fixture feature: once from a
  non-interactive shell with no TTY, once launched from `cron`. Covers: AC-001, AC-002. Verify:
  `python3 -m sdd_runner --feature <fixture> </dev/null` exits 0 leaving an unstaged tree on a
  non-default branch with `ORCHESTRATION.md`, `run.jsonl` and `PR_DESCRIPTION.md` present and no
  runner-created commit; and the `cron`-captured exit code is 0.

- [x] T019 - Prove containment on a machine with neither the Agent SDK nor the Codex CLI installed.
  Covers: AC-010, AC-014. Verify: `bash scripts/check-consistency.sh` exits 0,
  `bash scripts/check-consistency.test.sh` reports 42/42, `bash scripts/install.test.sh` 33/33,
  `pwsh scripts/install.test.ps1` 28/28, and `git diff --stat main` shows no installer or manifest
  file changed.

## Phase 4: Review

- [ ] T020 - Security review of the runner: credential handling, `run.jsonl` redaction, `--notify`
  command execution, agent responses as untrusted input, permission posture, worktree isolation,
  and the concurrency lock. Covers: AC-012. Verify: `/security-review` returns a verdict of
  APPROVE, or every Critical and High finding it raises is fixed and re-reviewed to APPROVE.

- [ ] T021 - Python-specific review with `/python-reviewer` and `/python-testing-reviewer`: typing,
  module boundaries, exception handling, silent failures, logging, and test quality.
  Covers: AC-009. Verify: both reviews return APPROVE, or each Critical and High finding is fixed and
  re-reviewed to APPROVE.

- [ ] T022 - Run one overnight unattended run on a real `Ready` spec of this repository, then read
  `ORCHESTRATION.md` and `run.jsonl` start to finish. Covers: AC-001, AC-002. Verify: the
  maintainer confirms by hand that every decision the runner made is reconstructible from
  `run.jsonl` alone, without the provider transcript, and records the confirmation in DECISIONS.md.

- [ ] T023 - Document the runner in `docs/SDD-ORCHESTRATION.md` (invocation, exit codes, backends,
  notification, resume, the phase-1/phase-2 boundary), add the `CHANGELOG.md` entry, and correct
  the `CONTRIBUTING.md` dependency line. Covers: AC-013. Verify: the docs state the Codex backend
  is unverified and name DEBT-001/DEBT-002, and `bash scripts/check-consistency.sh` exits 0.

- [ ] T024 - Final conformance review: SPEC → PLAN → TASKS → DIFF → TESTS → REVIEW traceability for
  every AC, plus the draft PR description. Covers: AC-001 through AC-014. Verify:
  `/spec-review` and the final-conformance-reviewer both return APPROVE with each AC mapped to
  observed evidence, and any AC-013 Codex clause not observed is reported as unobserved rather than
  assumed.
