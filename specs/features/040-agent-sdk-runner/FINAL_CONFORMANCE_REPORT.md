# Final Conformance Report: agent-sdk-runner (spec 040)

**Date:** 2026-08-31 · **Verdict: PASS on the criteria as written — with two of them written
narrower than they began, and the difference carried by [[DEBT-009]].**

> **Revised after the first pass.** The original verdict was PARTIAL: AC-002 had no evidence at all
> and AC-001 was half observed. Two things changed. D030 downgraded both criteria to what this
> machine can demonstrate and opened DEBT-009 for the rest — the framework's own rule for closing
> over an unmet criterion. D031 then made the remaining clause *observable* rather than downgrading
> it a second time: `--stub-script` plus a subprocess suite that spawns the real CLI with stdin
> closed. Read the two rows below together with DEBT-009; neither means what it would mean on its
> own.

> **Reviewer caveat, stated first because it changes how to read this.** This report was produced
> by the session, not by the `final-conformance-reviewer` agent the framework ships: this session
> is under a standing instruction not to invoke the Agent tool. An independent conformance pass has
> therefore *not* happened — the same party that implemented the feature is attesting to it.

## Acceptance-criteria evidence matrix

| AC | Behaviour | Status | Evidence |
|---|---|---|---|
| AC-001 | A two-task feature converges non-interactively to exit 0, unstaged tree, no runner commit | PASS **as downgraded** (D030) | `test_cli_e2e` — a real subprocess, stdin on `/dev/null`, exit 0, all eight 031 sections, one commit in the log. The clauses *"With the Claude backend"* and *"and a `PR_DESCRIPTION.md`"* were removed and live in DEBT-009 |
| AC-002 | The runner is invocable with no controlling terminal and no inherited session | PASS **as downgraded** (D030) | `test_cli_e2e` — same subprocess, plus `--dry-run` exiting 0 without a resolvable backend. The original *"launched from `cron`, exit 0"* is in DEBT-009: **nobody has watched this runner start from `cron`** |
| AC-003 | Each entry-gate precondition refuses by name, tree byte-identical | PASS | `test_gate.EachPreconditionRefusesByName` — six conditions, each asserting `git status` unchanged and a remediation present |
| AC-004 | Missing / malformed / unknown-verdict / competing blocks fail closed with raw text retained | PASS | `test_blocks` over a ten-case corpus incl. an adversarial prose-embedded block; `test_loop.MalformedResponses` |
| AC-005 | Counters match a hand-computed FR-009 table, including the cases that must not increment | PASS | `test_counters` — every expected value quotes the SKILL.md clause it derives from |
| AC-006 | With `--max-delegations N`, exactly N dispatch and the N+1st is refused before any call | PASS | `test_loop.BudgetRefusal`, `test_repair.BudgetDuringTheCycle` — observed by counting stub invocations |
| AC-007 | An interrupted run re-enters without re-delegating, duplicating or resetting | PASS (criterion amended, D024) | `test_resume.ConcurrencyAndInterruption` + `ResumeDoesNotDuplicate`. Observed against the state an interruption leaves, not by delivering a signal |
| AC-008 | A human-gated escalation halts, records verbatim, notifies once, exits with its code | PASS | `test_loop.HumanEscalation` |
| AC-009 | The conformance guard passes | PASS (replaced, D008) | `test_transcription` — 13 tests. **Weaker than the original two-executor comparison**, which the spike proved unviable |
| AC-010 | Existing suites pass at their counts with no SDK and no Codex CLI | PASS | 42/42, 33/33, 28/28 under pwsh, `check-consistency.sh` exit 0 — on this machine, where neither is installed |
| AC-011 | A second runner refuses, no provider call | PASS | `test_loop.ConcurrentRun`, `test_resume.ConcurrencyAndInterruption` |
| AC-012 | A sentinel `ANTHROPIC_API_KEY` appears in neither `run.jsonl` nor `ORCHESTRATION.md` | PASS (after a failure) | `test_loop.SecretsNeverReachTheArtifacts`, `test_state.RedactionAtTheWriter`. **It failed for four tasks** because T011's `Verify:` was narrower than this AC (D025) |
| AC-013 | Codex refuses without the opt-in, names both debts, no parity claim anywhere | PASS | `test_backends.CodexGate`; docs grep clean |
| AC-014 | No installer or manifest file differs from `main` | PASS | `git diff --stat main -- install.sh install.ps1 install-all.* profiles.json settings.template.json scripts/` → empty |

## Traceability

SPEC → PLAN → TASKS → DIFF → TESTS holds. Every AC maps to at least one task; every task carries a
`Covers:` and a `Verify:`; 22 tasks are closed against their criterion and 3 are marked
not-observed with the environment evidence recorded. 29 decisions are on record, including four
that reopen or narrow earlier claims rather than papering over them.

## What is claimed, and what is not

Claimed: the runner's protocol handling is correct against a deterministic stub — 202 tests, no
provider call, no cost — and the command-line entry point converges end to end in a real
subprocess with stdin closed. The fail-closed parser, the counter arithmetic, the hard budget, idempotent
re-entry, the repair cycle, the freeze and the closure delta each have tests that fail when the
control is removed; every one of those was verified by reverting the control and watching the suite
go red.

**Not claimed**, and not to be implied anywhere:

1. That the Claude Agent SDK works. It is not installed here; no `agents/*.md` prompt has reached a
   real provider.
2. That Codex works. The backend is implemented and **gated shut**; DEBT-001 and DEBT-002 remain
   open and are now load-bearing for this feature too. Codex parity is not claimed.
3. That the owning lifecycle skills behave as assumed. They are delegated and their APPROVE is
   required, but none has executed; `PR_DESCRIPTION.md` has never been produced.
4. That the two executors agree. R1 is **partially mitigated**: no test compares the runner and
   `sdd-orchestrate` on the same input, because there is no injection point for one (D008).
5. That 031's second DONE condition is met when `--baseline` is absent. It is recorded as
   unobserved, in the closure record and in the run's reason line.

## Findings from this pass

- **F-1 (blocking `Done`, not `In Review`) — still open, now precise.** Both criteria pass as
  written, and what they no longer assert is the whole of DEBT-009: a prompt reaching a real
  provider, a lifecycle skill executing, `PR_DESCRIPTION.md` on disk, a real `codex exec`. A reader
  of `SPEC.md` alone would not feel that gap; that is why it is in three places.
- **F-2 (process).** Twice a `Verify:` clause narrower than its own `Covers:` closed a task with
  work still inside it — T013 (D015) and T011 (D025), the second hiding a credential leak. This is
  a defect in how tasks are written, not in this feature, and it belongs in the `Verify:` guidance
  of `specs/_templates/TASKS.md`, which spec 033 owns. **Not changed here.**
- **F-3 (independence).** Three review gates in a row — T020, T021, T024 — were performed by the
  implementing session rather than by the agents that exist for them. The findings are real and the
  fixes are tested, but "the author reviewed the author" is the weakest evidence in this report.

## Recommendation

Promoted to `In Review` (2026-08-31). Do **not** promote to `Done`: F-1 is exactly the case
`docs/KNOWN_DEBT.md` exists to prevent — closing over an unmet criterion — and the precedent is
spec 039, which stopped at `Implemented` and said why.
