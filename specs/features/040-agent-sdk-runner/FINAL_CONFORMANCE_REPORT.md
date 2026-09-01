# Final Conformance Report: agent-sdk-runner (spec 040)

**Date:** 2026-09-01 · **Verdict: PASS on 040's corrected scope (T033).**

> **T033 verdict, 2026-09-01: PASS on the corrected scope.** All 19 acceptance criteria are met
> against observed evidence; T028…T032 are closed; AUDIT-1, 5, 6, 7 and 9 are closed in 040;
> AUDIT-2 is resolved by narrowing FR-005; AUDIT-3, 4 and 8 are out of scope and carried to the
> follow-up provider spec. **239 tests**, green. `git diff --check` clean. `check-consistency.sh`
> exit 0. `check-consistency.test.sh` 42/42, `install.test.sh` 33/33, `install.test.ps1` 28/28 —
> the exact counts AC-010 names.
>
> **What PASS means here, and what it does not.** It means the corrected scope — a deterministic
> core driven by one supported backend, `stub` — is fully evidenced. It does **not** mean the
> runner has ever spoken to a provider. `claude` and `codex` are outside the supported surface and
> unobserved; no parity is claimed. The classification stays **EXPERIMENTAL** for that reason: the
> verdict is about scope conformance, the classification is about maturity, and they are not the
> same statement.
>
> **The known weakness of this verdict, stated rather than buried.** T033 asked for an
> *independent* review. This one was performed by the same session that wrote the code, because
> this session is configured not to spawn review agents unless asked. What "independent" bought
> here is narrower: the review was run against **evidence rather than against the previous
> reports** — every count re-executed, every audit closure re-checked against the code, the
> `git diff main` scope enumerated by hand. That found F-4 below, which no prior report contains.
> It does not remove the structural risk R12/F-3 names. A reviewer who wants the stronger form
> should re-run this section with the `final-conformance-reviewer` agent.

## Current D034–D038 disposition

| Area | Current status |
|---|---|
| AUDIT-2 / FR-005 | **Resolved in the contract:** shared readable schema, same-executor re-entry, safe foreign-writer refusal. |
| AUDIT-1 / AC-015 | **CLOSED (T028):** all four cases asserted through the CLI subprocess; only a green, non-mutating baseline exits `0`. |
| AUDIT-5 / AC-016 | **CLOSED (T029):** real-path containment against the spec trail, refused before any artifact, proven with complete feature folders at every external target. |
| AUDIT-6 / AC-011, AC-017 | **CLOSED (T030, D044/D045):** atomic whole-document publication, proven by a two-phase barrier at the claim — one owner, one exit `15`, one dispatch, no exit `16`. |
| AUDIT-7 / AC-018 | **CLOSED (T031):** a committing reviewer aborts and a committing worker stales the earlier approval, both after the reviewable tree is asserted pristine. Provider attribution/policy moves to follow-up. |
| AUDIT-9 / AC-019 | **CLOSED (T032, D046):** a converged run records `CORE-COMPLETE` and stops. No lifecycle dispatch, no closure delta, no `PR_DESCRIPTION.md`; restoring either dispatch breaks the boundary tests. |
| AUDIT-3, AUDIT-4, AUDIT-8 | **Moved to follow-up:** provider routing/format retry and writer scope. Claude source was hardened by D035 (explicit tools, async deadline, declared AnyIO) but remains unobserved and out of 040 conformance. |
| T018, T022 | **Moved to follow-up:** must not run as 040 evidence. |

The earlier PASS is still withdrawn. The matrix below is retained as historical evidence for the
old acceptance surface; it is not a verdict on D034's criteria.

**Earlier verdict, superseded: PASS on the criteria as written — with two of them written
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

## Historical acceptance-criteria evidence matrix (superseded by D034)

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

## Historical traceability

For the pre-D034 contract, SPEC → PLAN → TASKS → DIFF → TESTS held. Every old AC mapped to a task; every task carried a
`Covers:` and a `Verify:`; 22 tasks are closed against their criterion and 3 are marked
not-observed with the environment evidence recorded. 29 decisions are on record, including four
that reopen or narrow earlier claims rather than papering over them.

## Historical claims, retained for audit

The earlier report claimed that the runner's protocol handling was correct against a deterministic
stub — **232 tests at that revision** — and that the command-line entry point converges end to end
in a real subprocess with stdin closed. The fail-closed parser, the counter arithmetic, the hard
budget, idempotent re-entry, the repair cycle, the freeze and the closure delta each had tests that
fail when the control is removed. Two of those items have since moved: the **closure delta** is no
longer computed by this runner (D046), and the test counts in this section are historical. The
current count is in the header.

**Not claimed**, and not to be implied anywhere:

1. That the Claude Agent SDK works. It is not installed here; no `agents/*.md` prompt has reached a
   real provider.
2. That Codex works. The backend is implemented and **gated shut**; DEBT-001 and DEBT-002 remain
   open and are now load-bearing for this feature too. Codex parity is not claimed.
3. That the owning lifecycle skills behave as assumed. **Superseded by D046:** they are no longer
   delegated at all. A converged run stops at `CORE-COMPLETE`, so this is no longer an unobserved
   claim — it is absent by contract. `PR_DESCRIPTION.md` is never produced.
4. That the two executors agree. R1 is **partially mitigated**: no test compares the runner and
   `sdd-orchestrate` on the same input, because there is no injection point for one (D008).
5. In the historical run, that 031's second DONE condition was met when `--baseline` was absent;
   it was only recorded as unobserved. D036 blocks that path and T028 observed all four CLI cases,
   so AC-015 is now met as amended by D040.

## Findings from this pass

- **F-1 (blocking `Done`, not `In Review`) — resolved by narrowing, D034/D046.** Two of DEBT-009's
  four items — a lifecycle skill executing and `PR_DESCRIPTION.md` on disk — are no longer things
  040 needs and failed to show. They left the spec. The other two (a prompt reaching a real
  provider, a real `codex exec`) left with the provider surface. Nothing here waits on them.
- **F-2 (process).** Twice a `Verify:` clause narrower than its own `Covers:` closed a task with
  work still inside it — T013 (D015) and T011 (D025), the second hiding a credential leak. This is
  a defect in how tasks are written, not in this feature, and it belongs in the `Verify:` guidance
  of `specs/_templates/TASKS.md`, which spec 033 owns. **Not changed here.**
- **F-3 (independence) — still true, and true of T033 too.** Three review gates in a row — T020,
  T021, T024 — were performed by the implementing session rather than by the agents that exist for
  them, and so was this one. The findings are real and the fixes are tested, but "the author
  reviewed the author" remains the weakest evidence in this report. It is the reason the
  maintainer's own nine-finding audit found what four green gates had not.
- **F-4 (AC-014 scope, found by T033) — Low, non-blocking.** AC-014's enforceable half holds and was
  re-verified: `git diff main --name-only` over `install.sh`, `install.ps1`, `install-all.sh`,
  `install-all.ps1`, `profiles.json` and `settings.template.json` prints nothing. Its second
  sentence does not hold literally. Six files outside `runner/`, `specs/features/040-*/` and the
  test suites changed: `.gitignore` (bytecode plus `run.jsonl`, infrastructure the package needs),
  `docs/KNOWN_DEBT.md`, `docs/SDD-ORCHESTRATION.md`, `CHANGELOG.md`, `CONTRIBUTING.md` — and four
  **protocol contracts**: `agents/domain-reviewer.md`, `agents/final-conformance-reviewer.md`,
  `skills/sdd-orchestrate/SKILL.md` and `specs/features/031-*/SPEC.md`.

  All four protocol edits are D011's closed-severity-enum clarification, additive, and load-bearing:
  `test_transcription.ObservedDivergence.test_the_protocol_documents_the_closed_enum` fails without
  them. So this is a criterion written narrower than the work legitimately required, not a scope
  breach — the same failure mode F-2 describes, one level up. **Recorded, not silently
  reinterpreted, and AC-014's text is left as written:** amending it is a contract change and
  belongs to whoever opens the follow-up spec.

## Current recommendation

Close spec 040 on its corrected scope. `In Review` → `Done` via `/spec-close`; classification stays
**EXPERIMENTAL**. Open the follow-up provider spec before any real provider run: it inherits
AUDIT-3 (provider routing of auto-resolvable escalations and the canonical format re-request),
AUDIT-4 (enforceable writer `path_scope`), AUDIT-8 (Claude permissions and observed SDK behaviour),
the provider half of AUDIT-7 (attribution for a real writing session's history mutations), the
`Finalizer` that begins at the `_finalize` seam, and the former T018/T022 scenarios. Codex execution
stays gated on DEBT-001/DEBT-002.

Two things the follow-up should carry as process input, not as code:

- **F-2/F-4 are the same defect at two altitudes.** A `Verify:` narrower than its `Covers:` closed
  two tasks with work still inside them; an AC narrower than the work it authorised produced F-4.
  Both belong to the `Verify:` and acceptance-criteria guidance in `specs/_templates/`, which
  spec 033 owns. Not changed here.
- **F-3 is unresolved by construction.** Five gates in this feature, including its final
  conformance, were run by the session that wrote the code. The nine-finding audit that reset the
  whole spec came from the maintainer afterwards. Whatever the follow-up does about review
  independence, it should not inherit this arrangement unexamined.
