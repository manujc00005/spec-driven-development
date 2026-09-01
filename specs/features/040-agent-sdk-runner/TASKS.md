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

  **[AC-014 AMENDED 2026-09-01 — D047; this task's `Verify:` is unaffected]** The criterion's
  second sentence was narrower than the delivered work: D011's closed-enum clarification landed in
  four protocol contracts and the package needs two `.gitignore` rules. AC-014 now enumerates those
  six paths as its whole exception. The `Verify:` above tests the installer/manifest half, which
  never moved and still passes — so this task is not reopened.

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

- [x] T004 - **[CONTRACT REALIGNED 2026-08-31 — D034]** AUDIT-2 is resolved by narrowing FR-005:
  both writers share a readable section schema, but only the writer resumes its state. The existing
  foreign-writer refusal is the required fail-closed behavior, not an implementation defect.
  Implement `state.py`: read and write `ORCHESTRATION.md` in spec 031's schema (State,
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

- [x] T008 - **[OUTSIDE 040 CONFORMANCE 2026-08-31 — D034]** AUDIT-8 moves with real-provider
  execution to the follow-up spec. The module remains optional/lazy experimental source; this
  historical task is not evidence that Claude is supported. **D035 hardens the source anyway:**
  explicit tool lists, an async `fail_after` deadline, and a declared `anyio>=4` optional
  dependency. This is potentially over-implemented relative to 040 and remains follow-up evidence.
  Implement the `claude` backend over the Claude Agent SDK, importing the SDK lazily so
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

- [x] T010 - **[PROVIDER POLICY MOVED OUT — D034]** Historical implementation retained; provider
  retries, timeouts and canonical format retry are not 040 conformance evidence. Implement
  `retry.py`: bounded attempts, exponential backoff, per-attempt timeout, every
  retry charged to the delegation budget, exhausted retries failing the delegation closed.
  Covers: AC-006. Verify: `python3 -m unittest tests.unit.test_retry` asserts that N
  retries decrement the budget by N and that exhaustion produces a failed-closed delegation.

- [x] T011 - **[REOPENED then closed 2026-08-31 - D025]** Redaction must cover **every**
  artifact the runner writes, not only `run.jsonl`. Implement it at the `ORCHESTRATION.md` writer
  as well, in the same place and for the same reason: at the writer, so no call site can bypass it.
  Covers: AC-012. Verify: a run whose worker returns a human-gated BLOCKED question containing the
  value of `ANTHROPIC_API_KEY` leaves that value absent from **both** `run.jsonl` and
  `ORCHESTRATION.md`, asserted by a regression test, and `python3 -m unittest tests.unit.test_log`
  still passes.

  **Closed 2026-08-31.** `redact` is now applied in `Orchestration.save()` - the single choke
  point through which every write to `ORCHESTRATION.md` passes - using the same helper and the same
  placement rationale as `log.py`. `dumps()` stays verbatim, so the byte-identical round-trip
  against the real phase-1 artifacts is unaffected. Evidence: five tests, two of them a full-run
  regression asserting the sentinel is absent from **both** files while the escalation question
  itself stays legible; reverting `save()` to write `dumps()` fails them.

  **Why it was closed and should not have been.** The original `Verify:` asserted the sentinel was
  absent from `run.jsonl` alone, while AC-012 requires both files. The narrower criterion passed;
  the acceptance criterion did not. Reproduced 2026-08-31: on the human-gated escalation path the
  worker's question is copied verbatim into the `Escalations` section, which never passes through
  `redact`. This is the second time a `Verify:` clause narrower than its own `Covers:` has closed a
  task with work left inside it - the first was T013 (D015) - and the first time it let a
  credential leak through.

- [x] T012 - **[FOLLOW-UP CORE FIX: T029 — D034]** AUDIT-5 showed this historical Verify did not
  cover feature-path containment.
  Implement `__main__.py`: the CLI of FR-001, the entry gate of FR-002 enforcing every
  031 precondition, the exit-code mapping of FR-013, and the `--notify` sink executed without a
  shell with the event as JSON on stdin. Covers: AC-003, AC-008. Verify: a script violating each
  precondition in turn shows every run exiting with the gate code, naming that condition and its
  remediation, with `git status --porcelain` byte-identical before and after each.

- [x] T013 - **[FOLLOW-UP CORE FIX: T030 — D034]** AUDIT-2 is resolved by FR-005; AUDIT-6 remains
  because the historical concurrent-refusal tests did not open the pre-state creation race.
  Implement `loop.py`: the driver composing core, backends and infrastructure — entry
  gate, plan, dispatch, parse, reviewers, findings-to-tasks, re-review, converge or abort — writing
  state before proceeding past any transition, resuming idempotently per 031 FR-011, and refusing
  to start when an ACTIVE run is recorded. Covers: AC-001, AC-007, AC-011. Verify:
  `python3 -m unittest tests.integration.test_loop tests.integration.test_resume` passes the
  converge, resume and concurrent-refusal cases against the stub backend — 37 integration tests,
  including resume-after-completed-task, resume-after-blocked-task, resume-with-exhausted-budget,
  eleven corrupt-state blocks, and the ACTIVE-but-dead-pid recovery.

- [x] T014 - **[SUPERSEDED AT `_finalize` — D034]** Its provider/lifecycle closure half leaves 040.
  AUDIT-1 and the core half of AUDIT-7 remain as T028 and T031; the boundary cut is T032.
  Implement finalization: freeze the approved fingerprint, invoke the owning lifecycle
  skills for closure, verify the closure delta against the allowlist per 031 FR-013, and guarantee
  the runner never commits, pushes, merges, or edits a spec `Status` line. Covers: AC-001.
  Verify: after an integration converge run, `git log --oneline main..HEAD` is empty, the feature's
  `SPEC.md` `Status` line is unchanged by the runner, and `PR_DESCRIPTION.md` exists.

  **[DONE 2026-08-31]** `python3 -m unittest tests.integration.test_finalization` passes 21 tests
  covering the ten required cases. `HappyPath.test_the_runner_still_creates_no_commit` asserts the
  empty git log; the runner never writes a `Status` line — it delegates `/spec-review` and
  `/spec-close` and requires their APPROVE (D019), and `PR_DESCRIPTION.md` is generated by the
  `/pr-description` step it delegates. **One clause of this Verify is not observed**: with the stub
  backend no lifecycle skill actually writes `PR_DESCRIPTION.md`, so its existence is asserted only
  through the delegation being made and approved, not through the file appearing. That needs a
  real provider (T018) and is recorded as such rather than claimed.

## Phase 3: Tests

- [x] T015 - Complete the unit suite: parser corpus, counter table, budget accounting, escalation
  categories, exit-code mapping, redaction, state round-trip. Covers: AC-004, AC-005, AC-012.
  Verify: `python3 -m unittest discover -s runner/tests/unit -t runner` passes with every T002 fixture exercised and the
  run reports zero skipped tests.

- [x] T016 - Complete the integration suite against the stub: converge, reject-then-fix, flip-flop
  on one finding ID, per-reviewer cap abort, per-finding cap abort, budget refusal, SIGTERM-and-
  resume, concurrent-run refusal, human-gated escalation invoking `--notify`, and the Codex gate
  refusal. Covers: AC-003, AC-006, AC-007, AC-008, AC-011, AC-013. Verify:
  `python3 -m unittest discover -s runner/tests/integration -t runner` passes all ten scenarios, and the budget case
  asserts the stub's invocation counter equals N with the N+1st never dispatched.

  **[DONE 2026-08-31]** All ten scenarios are green across `test_loop.py` (10), `test_resume.py`
  (28) and `test_repair.py` (14) — 52 integration tests. The two that were missing are closed by
  T025's repair cycle: the per-finding cap abort (`FlipFlop.test_flip_flop_detected_at_loop_level`,
  which asserts the abort scope is `finding` and the reviewer streak never reached the cap) and the
  loop-level flip-flop (a reviewer alternating between two findings, so every round makes progress
  and only the per-finding total accumulates). SIGTERM-and-resume was closed by T013. The budget
  cases assert the stub's invocation counter directly, before and after the refused dispatch.

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

- [~] T018 - **[MOVED OUT OF SPEC 040 — D034; DO NOT RUN AS 040 EVIDENCE]** **[NOT OBSERVED - D026,
  D030, DEBT-009]** Run the two E2E scenarios against a real
  provider on the fixture feature: once from a non-interactive shell with no TTY, once launched
  from `cron`. Covers: AC-001, AC-002. Verify: `python3 -m sdd_runner --feature <fixture>
  </dev/null` exits 0 leaving an unstaged tree on a non-default branch with `ORCHESTRATION.md`,
  `run.jsonl` and `PR_DESCRIPTION.md` present and no runner-created commit; and the
  `cron`-captured exit code is 0.

  **D034 supersedes this criterion for 040.** It is retained verbatim as follow-up input, not as an
  unchecked gate on the deterministic core.

  **Not performed, and not performable here.** `import claude_agent_sdk` raises
  `ModuleNotFoundError` and `which codex` finds nothing on this machine, both verified 2026-08-31.
  Historically this task gated promotion to `Done`, not the rest of the work - the precedent is spec 039,
  which stopped at `Implemented` because its symlink ladder could not execute off Windows and said
  so. Three things nobody has seen work remain behind this task: an `agents/*.md` prompt reaching a
  real provider, an owning lifecycle skill actually running, and `PR_DESCRIPTION.md` appearing on
  disk.

- [x] T019 - Prove containment on a machine with neither the Agent SDK nor the Codex CLI installed.
  Covers: AC-010, AC-014. Verify: `bash scripts/check-consistency.sh` exits 0,
  `bash scripts/check-consistency.test.sh` reports 42/42, `bash scripts/install.test.sh` 33/33,
  `pwsh scripts/install.test.ps1` 28/28, and `git diff --stat main` shows no installer or manifest
  file changed.

## Phase 4: Review

- [x] T020 - **[HISTORICAL REVIEW, NOT FINAL EVIDENCE — D034]** AUDIT-5 remains in 040 as T029;
  AUDIT-4 and AUDIT-8 move to the provider follow-up. T033 requires independent conformance after
  the core fixes.
  Security review of the runner: credential handling, `run.jsonl` redaction, `--notify`
  command execution, agent responses as untrusted input, permission posture, worktree isolation,
  and the concurrency lock. Covers: AC-012. Verify: `/security-review` returns a verdict of
  APPROVE, or every Critical and High finding it raises is fixed and re-reviewed to APPROVE.

  **[DONE 2026-08-31 — D028]** First pass: **Partial**, no Critical or High, four findings. Three
  Medium fixed and pinned by nine tests (SEC-001 closure allowlist matched by basename repo-wide;
  SEC-002 the recorded allowed-path scope was never checked; SEC-003 the redaction hint list missed
  `OPENAI_KEY`/`DB_PASS`/`GH_PAT`/`PRIVATE_KEY`). SEC-004 Low — the Codex backend passes the prompt
  in `argv`, readable via `ps` — is documented in `codex.py` and tied to DEBT-001, because the fix
  is stdin and nobody has verified that CLI accepts it. Re-review: **Pass**, with R11 recorded as a
  named residual (writing agents still carry the whole repo as their scope).

  **Reviewer caveat, stated rather than implied:** performed by the session, not by the
  `security-reviewer` agent this framework ships — this session is under a standing instruction not
  to invoke the Agent tool. The agent's abuse-case enumeration was not applied.

- [x] T021 - Python-specific review with `/python-reviewer` and `/python-testing-reviewer`: typing,
  module boundaries, exception handling, silent failures, logging, and test quality.
  Covers: AC-009. Verify: both reviews return APPROVE, or each Critical and High finding is fixed and
  re-reviewed to APPROVE.

- [~] T022 - **[MOVED OUT OF SPEC 040 — D034; DO NOT RUN AS 040 EVIDENCE]** **[NOT OBSERVED - D026,
  D030, DEBT-009; depends on the provider follow-up]** Run one overnight unattended
  run on a real `Ready` spec of this repository, then read
  `ORCHESTRATION.md` and `run.jsonl` start to finish. Covers: AC-001, AC-002. Verify: the
  maintainer confirms by hand that every decision the runner made is reconstructible from
  `run.jsonl` alone, without the provider transcript, and records the confirmation in DECISIONS.md.

  **D034 supersedes this criterion for 040.** The provider/finalizer follow-up may adopt it; 040
  must not run it or use it for conformance.

  **Not performable here.** It needs a real backend, and T018 records why there is none on this
  machine. Before D034 it gated promotion to `Done`, not the rest of the work. What *is* observed is
  the structural half: `test_loop.Converge.test_every_decision_is_reconstructible_from_run_jsonl_alone`
  asserts that a run emits `plan`, `dispatch`, `response`, `completion`, `verdict`, `counters`,
  `finalize-start`, `freeze`, `closure-delta` and `finish` events. What is **not** observed is a
  human reading a real overnight run's log start to finish and confirming it is enough.

- [x] T023 - **[DOCUMENTATION SCOPE SUPERSEDED BY T032 — D034]** Document the runner in
  `docs/SDD-ORCHESTRATION.md` (invocation, the eleven exit codes,
  backends, notification, resume, finalization, the phase-1/phase-2 boundary), add the
  `CHANGELOG.md` entry, correct the `CONTRIBUTING.md` dependency line, record in
  `docs/KNOWN_DEBT.md` that DEBT-001/DEBT-002 are now load-bearing for this feature, and decide
  whether `run.jsonl` belongs in `.gitignore` or is committed evidence. Covers: AC-013.
  Verify: `grep -l sdd_runner docs/SDD-ORCHESTRATION.md CHANGELOG.md CONTRIBUTING.md` lists all
  three, the docs state the Codex backend is unverified and name DEBT-001/DEBT-002, and
  `bash scripts/check-consistency.sh` exits 0.

  **[DONE 2026-08-31]** FR-018 is met. `grep -l sdd_runner docs/SDD-ORCHESTRATION.md CHANGELOG.md
  CONTRIBUTING.md` lists all three; `check-consistency.sh` exits 0. The new phase-2 section
  documents the invocation, all eleven exit codes, the three backends, notification, re-entry,
  finalization/freeze/closure delta, and the phase-1/phase-2 boundary — and carries a
  *"What has and has not been observed"* subsection naming the four things nobody has seen work.
  The Codex backend is described as present but gated, citing DEBT-001 and DEBT-002, with
  "Codex parity is not claimed" in the text. `docs/KNOWN_DEBT.md` now records that both debts are
  load-bearing for spec 040, not only for 019/028. `run.jsonl` is gitignored (D027);
  `ORCHESTRATION.md` stays committed.

- [x] T024 - **[SUPERSEDED BY T033 — D034]** The historical report remains evidence of what was
  checked, but the current verdict is PARTIAL and the acceptance surface changed.
  Final conformance review: SPEC → PLAN → TASKS → DIFF → TESTS → REVIEW traceability for
  every AC, plus the draft PR description. Covers: AC-001 through AC-014. Verify:
  `/spec-review` and the final-conformance-reviewer both return APPROVE with each AC mapped to
  observed evidence, and any AC-013 Codex clause not observed is reported as unobserved rather than
  assumed.

  **[DONE 2026-08-31]** `FINAL_CONFORMANCE_REPORT.md` written: verdict **PARTIAL**. Eleven of
  fourteen ACs PASS with named evidence, AC-001 is half observed, and **AC-002 has none at all** —
  both wait on T018/T022. Three findings recorded, including that this pass and the two review
  gates before it were performed by the implementing session rather than by the agents that exist
  for them. Recommendation: promote to `In Review`, not to `Done`.

## Phase 5: Driver completion (added 2026-08-31)

- [x] T025 - **[CORE SCOPE CONFIRMED — D034]** The deterministic repair cycle remains in 040.
  AUDIT-3's provider actions — `deep-reasoner` routing and the canonical format retry — move to the
  follow-up and are no longer criteria for this historical task.
  Implement the repair / re-review cycle in `loop.py`: a REJECT registers its finding,
  allocates exactly one repair task per new identity per 031 FR-007, delegates the repair through
  the worker path, records the repair, re-reviews every stale required reviewer, and converges,
  or aborts on the per-reviewer cap, the per-finding cap or the budget. Covers: AC-005, AC-006.
  Verify: `python3 -m unittest tests.integration.test_repair` passes 14 tests, including
  reject→repair→approve reaching exit 0 with the finding resolved and its repair task checked off;
  the flip-flop aborting on the `finding` scope with the streak below the cap; and both budget
  cases asserting the stub was never invoked for the refused dispatch.

  **Why this is a separate task, not a re-open of T013.** T013's description named
  "findings-to-tasks, re-review", but the `Verify:` clause it was closed against covered only the
  converge, resume and concurrent-refusal cases. Reopening a task whose stated criterion was
  genuinely met would falsify the record; this names the gap between that description and that
  criterion instead. See [[D015]].

- [x] T026 - Make the end-to-end CLI path observable without a provider: a `--stub-script FILE`
  flag loading scripted responses for `--backend stub`, and an integration suite that spawns
  `python3 -m sdd_runner` in a real subprocess with stdin closed. Covers: AC-001, AC-002.
  Verify: `python3 -m unittest tests.integration.test_cli_e2e` passes 8 tests, including a
  two-task feature converging to exit 0 with no TTY, on a non-default branch, with an unstaged
  tree, an `ORCHESTRATION.md` carrying all eight 031 sections, a `run.jsonl`, and exactly one
  commit in the log — the fixture baseline, none created by the runner.

  **[DONE 2026-08-31 — D031]** AC-001's shell clause had never been executed: the stub could not
  be driven from the CLI, so `--backend stub` exited 14 with "script exhausted after 0 responses"
  and no run ever reached exit 0 through `main()`. This closes that. It also closes the gap that
  let a `--dry-run` regression survive three review passes — every other integration test builds
  `Loop` in process and never touches argument parsing, backend-resolution order or the exit-code
  mapping. The script loader fails closed on all five malformed shapes without starting a run.

- [x] T027 - Close the test gaps `/qa-review` found: direct coverage for the strict YAML subset,
  evidence for the PY-2 error classification, and the `--notify` sink exercised as a real command.
  Covers: AC-004, AC-008, AC-012. Verify: `python3 -m unittest tests.unit.test_miniyaml
  tests.unit.test_backends tests.integration.test_cli_e2e` passes; reverting the PY-2 guard fails
  five of them.

  **[DONE 2026-08-31 — D032]** Three gaps, one of them mine. `_miniyaml` — the module whose whole
  job is rejecting things, and the basis of D010's "unrecognized == rejected" — had **no tests of
  its own**: it was exercised only through `blocks`, which sees the accepted shapes. Nineteen
  rejection cases now cover anchors, aliases, tags, flow mappings, block scalars, document markers,
  tabs, duplicate keys and nesting, plus an assertion that `MiniYamlError` is the *only* way it
  fails. The PY-2 fix from D029 was **claimed and never tested**; it now has evidence, and
  reverting it fails five tests. The `--notify` sink had only ever been a Python callable in
  process — never a real command — so the declared edge case "the notify command exits non-zero,
  hangs, or does not exist" was untested; it now runs as a real script.

## Phase 6: Experimental-core stabilization (added 2026-08-31 — D034)

- [x] T028 - Make a declared baseline mandatory for core completion. Replace the stringly
  `NOT DECLARED` observation with a completion-evidence outcome that prevents `DONE`/exit `0`; a
  missing, failing or tree-mutating baseline returns exit `18`, while a green non-mutating baseline
  permits core run result `DONE` and exit `0` without changing the feature lifecycle `Status`. This
  task must change the decision point, not merely the rendered record.
  Covers: AC-001, AC-015. Verify:
  `python3 -m unittest tests.integration.test_cli_e2e tests.integration.test_finalization` passes
  four subprocess cases — missing, non-zero, mutating and passing baseline — and asserts that only
  the last exits `0` and records `DONE`.

  **[VERIFY MET, AC AMENDED 2026-08-31 — D039/D040]** The `Verify:` clause is now satisfied: four
  subprocess cases through the real CLI — omitted, non-zero, tree-mutating and green — each
  asserting the exit code and the persisted run result, with only the green one exiting `0` and
  recording `DONE`. The D035 → D036 traceability comments are corrected.

  **AC-015 amended 2026-08-31 (D040)** to expect the earliest gate that can see each failure: `18`
  for an omitted baseline, `10` for a non-zero or tree-mutating one, `0` only for green. The
  conflict with 031 FR-002 is resolved in favour of 031's entry gate, which refuses before any
  delegation. **[CLOSED 2026-08-31]** The four cases were re-run rather than taken on this note's
  word: 28 tests across `test_cli_e2e` and `test_finalization`, green. `Covers:` and `Verify:` now
  agree.

  Found while implementing: the CLI never printed `remediation`, so every blocking outcome told the
  operator what was wrong and not what to do. Fixed.

- [x] T029 - Contain `--feature` before any runner write. Resolve the repository root,
  `specs/features/` root and requested feature through symlinks, use a path-aware containment check,
  and refuse an absolute external path, `..` escape or symlink escape with the gate code and a
  remediation. Do not use string-prefix comparison. Covers: AC-003, AC-016. Verify:
  `python3 -m unittest tests.integration.test_gate tests.integration.test_cli_e2e` passes all four
  path cases and asserts that refusals create no `ORCHESTRATION.md`, `run.jsonl` or lock at either
  the requested or resolved external location.

  **[DONE 2026-08-31 — D042]** `_resolve_feature` resolves the repository root, the
  `specs/features/` root and the requested path through symlinks with `os.path.realpath`, then
  compares with `os.path.commonpath` — path-aware, so `specs/features-old` is correctly outside
  `specs/features`. It runs before any write: before the entry gate, before the exclusive claim on
  `ORCHESTRATION.md`, before the log exists. `tests/integration/test_gate.py` covers absolute
  external, `..` escape, symlink escape, in-repo-but-outside-the-trail, the features root itself,
  and the two paths that must still be accepted, asserting no artifact at either the requested or
  the resolved location.

  **The first version of these tests passed against the unfixed code.** The external targets were
  empty directories, so the gate refused them for a missing `SPEC.md` and the containment check was
  never exercised. They now plant a complete, otherwise-valid feature folder at every external
  target and assert the refusal names containment, so nothing else can produce a green.

- [x] T030 - Replace the exists-then-create ownership window with atomic per-feature exclusion
  (`O_CREAT | O_EXCL` or an equivalent single atomic primitive), retaining named stale-owner
  recovery without allowing two contenders to clean up or acquire simultaneously. Covers: AC-011,
  AC-017. Verify: `python3 -m unittest tests.integration.test_race tests.integration.test_resume`
  passes. The race releases two contenders from a two-phase barrier at the claim itself and
  observes exactly one owner, exactly one exit `15`, one worker dispatch in total and no exit `16`,
  repeatedly and without sleep ordering; the focused test proves the atomic primitive.

  **[DONE 2026-09-01 — D044/D045]** Two findings, and the first one was mine.

  **`[14,14]` was never two owners.** The captured trace is
  `plan(resumed=false) → finish(14) → resume → plan(resumed=true) → finish(14)`: the first
  contender claimed, ran, exited 14 leaving `ABORTED / resumable: yes`, and the second — whose
  busy-wait had lost by enough — then legitimately resumed it. Sequential, not simultaneous. The
  earlier barrier released both *before the whole CLI*, so the entry gate's git work separated them
  far beyond the contested window. D043's conclusion was wrong and D044 corrects it without
  deleting it.

  **The real defect was the partial-publication window**, exactly where it was predicted: the claim
  created an empty `ORCHESTRATION.md` with `O_CREAT|O_EXCL` and filled it in with a later
  `doc.save()`. A contender looking in between loaded a truncated document and exited `16`, blaming
  the state instead of the other runner. `state.create_exclusive` now writes and `fsync`s the
  complete document to a temporary name and publishes it with `os.link`, which is atomic
  create-if-absent and never replaces. Nothing is cleaned up by anyone: a stale owner's document is
  resumed, never deleted, so there is no reclaim race to lose.

  The barrier moved to where the race is — a two-phase file barrier around
  `_load_or_create_state`, monkeypatched **in the child process only**, so production carries no
  test hook. Phase 1 holds both until both have reached the claim; phase 2 holds the winner until
  both have attempted, which is what removes the sequential-resume confound that produced the false
  positive. Six rounds per run, stable across four consecutive runs, no sleeps anywhere.

- [x] T031 - Include `git rev-parse HEAD` in every repository fingerprint that protects an
  approval, freeze or read-only delegation. A changed commit object must invalidate the prior
  fingerprint even when status and diff are clean. Covers: AC-018. Verify:
  `python3 -m unittest tests.integration.test_loop tests.integration.test_finalization` includes a
  backend that commits during delegation, asserts `git status --porcelain -uall` and
  `git diff HEAD` are empty afterwards, and still observes fail-closed staleness because `HEAD`
  changed.

  **[DONE 2026-09-01]** Both halves now commit from inside a delegation, and both first assert the
  reviewable tree is pristine afterwards — no status entries, no diff against `HEAD` — so detection
  cannot have come from either and can only have come from `HEAD` being hashed.

  *Read-only half* (`test_loop.CommitsDuringDelegationAreDetected`): a `domain-reviewer` that
  commits is caught as an out-of-scope write — `ABORTED`, exit `16`, `resumable: no` — and its
  recorded pre/post fingerprints differ. *Approval half*
  (`test_finalization.CommittedWorkStalesApprovals`): a worker that commits T002's change stales
  `domain@T001`, the run re-reviews and only then closes.

  Removing the `HEAD` line from the digest fails both (2 failures, 1 error), so the control is the
  thing under test rather than a coincidence.

- [x] T032 - Enforce the D034 boundary at `Loop._finalize`. A converged stub run performs the
  baseline gate, records terminal core evidence and stops; it does not dispatch `/spec-review`,
  `/spec-close` or `/pr-description`, compute a provider/lifecycle closure delta, or require
  `PR_DESCRIPTION.md`. Keep Claude optional/lazy and Codex gated, but label both out of 040's
  supported surface in `docs/SDD-ORCHESTRATION.md`, `CHANGELOG.md` and `CONTRIBUTING.md`. Covers:
  AC-001, AC-019, FR-008, FR-017, FR-018. Verify:
  `python3 -m unittest tests.integration.test_finalization tests.integration.test_cli_e2e` passes
  a converged stub run whose `run.jsonl` contains no `lifecycle:*` dispatch or closure event and
  whose feature contains no `PR_DESCRIPTION.md`; `rg -n "supported|provider|Claude|Codex|closure"
  docs/SDD-ORCHESTRATION.md CHANGELOG.md CONTRIBUTING.md` shows the experimental boundary and no
  provider-parity claim.

  **[DONE 2026-09-01 — D046]** `Loop._close` now records `CORE-COMPLETE`, the frozen fingerprint,
  the verification outcome and the frozen tree map, and finishes `DONE`/exit `0`. Removed with the
  dispatch, because they died with it: `LIFECYCLE_STEPS`, `_lifecycle_step`, `_phase_index` and the
  `lifecycle:` branch of `_system_prompt`.

  The boundary is tested with a script that *would* have satisfied every lifecycle step. If the
  boundary leaks, the run does not fail on a missing scripted response and read like a harness bug:
  it succeeds, and only the assertions catch it. Two negative checks confirm they do — restoring a
  single `/spec-review` dispatch fails 3 tests, restoring the closure-delta computation fails 2.

  The old `LifecycleGate` tests were inverted rather than deleted: the refusing `/spec-close` and
  the unreadable `/spec-review` scripts are still there, and now assert that a run nobody asks
  closes anyway. A leaking boundary would revive exactly those two paths.

  **Found while implementing, reported rather than fixed silently:** `runner/README.md` still
  described the pre-T028 `--baseline` behaviour ("undeclared → the closure record says NOT
  DECLARED") three paragraphs from the text T032 had to rewrite. Corrected, because leaving it
  would have contradicted the code inside the section being rewritten.

  **A judgment call a reviewer should see:** `closure.observe`, `closure.unexpected` and
  `closure.classify` now have no production caller. They are kept, said so in the module docstring,
  and still asserted directly — AUDIT-9 hands the closure delta to the follow-up `Finalizer`, and
  the frozen map this runner persists is what it will compare against. See D046.

- [x] T033 - Run an **independent** final conformance review after T028…T032. Map every current AC
  to observed evidence, verify that AUDIT-1/5/6/7/9 are closed in 040, that AUDIT-2 is resolved by
  D034, and that AUDIT-3/4/8 have not leaked back from the follow-up. Covers: AC-001 through
  AC-019.
  Verify: `/spec-review` plus an independent final-conformance reviewer produce a current report;
  `FINAL_CONFORMANCE_REPORT.md` may change from PARTIAL only if every retained criterion passes.

  **[DONE 2026-09-01 — PASS on the corrected scope]** All 19 criteria mapped to observed evidence.
  AUDIT-1/5/6/7/9 closed in 040; AUDIT-2 resolved by narrowing FR-005; AUDIT-3/4/8 confirmed absent
  from the runner and carried to the follow-up. `stub` is the only backend `backends.resolve`
  treats as supported. No `_lifecycle_step`, `LIFECYCLE_STEPS`, `_phase_index` or
  `closure_mod.observe` call survives in `sdd_runner/`; the only remaining `PR_DESCRIPTION.md`
  mentions are the fingerprint exclusion list and the closure allowlist constant. No duplicate
  `Txxx` or `Dxxx` IDs. `artifacts/` is untracked, untouched and excluded from the commit.

  Re-executed rather than quoted: **239 tests** green, `git diff --check` clean,
  `check-consistency.sh` exit 0, and AC-010's three named suites at exactly their stated counts —
  `check-consistency.test.sh` 42/42, `install.test.sh` 33/33, `install.test.ps1` 28/28.

  **One new finding, F-4 (Low, non-blocking):** AC-014's enforceable half holds — the six installer
  and manifest files are byte-identical to `main` — but its second sentence does not hold literally.
  Four protocol contracts changed (`agents/domain-reviewer.md`,
  `agents/final-conformance-reviewer.md`, `skills/sdd-orchestrate/SKILL.md`,
  `specs/features/031-*/SPEC.md`), all of them D011's additive closed-enum clarification and all
  load-bearing for `test_transcription`. Recorded rather than reinterpreted; the AC text is left as
  written, because amending it is a contract change for the follow-up spec to make.

  **[F-4 RESOLVED 2026-09-01 — D047, second independent review]** Deferring it was the wrong call:
  it left a PASS standing on a criterion that did not literally hold, which is the exact shape of
  the thing this spec has been correcting all along. AC-014 is now amended by enumeration of the
  six paths `f48e62d` actually touched. Widening it by category was rejected.

  **The limit of this verdict:** "independent" here means *against evidence rather than against the
  previous reports*, not *by a different agent*. This session performed it. F-3 stands.

## Follow-up-spec input — not tasks of 040

- AUDIT-3: provider routing of auto-resolvable questions and the canonical one-time format retry.
- AUDIT-4: enforceable `path_scope`, allowed writes and provenance for writing provider sessions.
- AUDIT-7 provider half: attribution and policy for history mutations made by a real writing
  session. Spec 040 only detects the changed `HEAD` and fails closed.
- AUDIT-8: Claude permissions, explicit tool allowlist, timeout inside the async run and observed
  SDK behavior; Codex execution/parity remains gated by DEBT-001/DEBT-002.
- AUDIT-9: a `Finalizer` beginning at the `_finalize` seam, owning lifecycle delegation, closure
  delta, PR-description evidence, real-provider E2E and the former T018/T022 scenarios.
