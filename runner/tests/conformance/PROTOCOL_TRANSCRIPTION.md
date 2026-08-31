# Protocol transcription table

This file is the documented manual comparison spec 040 D008 requires after T017's
original form was found unviable. It maps every rule the runner encodes to the
clause of spec 031 (as rendered in `skills/sdd-orchestrate/SKILL.md`) it comes
from, and to the test that pins it.

`test_transcription.py` asserts that this table stays honest: every module listed
here must exist, and every test named here must be collected by the suite.

| 031 clause (SKILL.md) | Runner module | Test |
|---|---|---|
| Verdict block: `verdict: APPROVE\|REJECT`, `findings` required | `blocks.parse_reviewer` | `test_blocks.ReviewerParsing.test_valid_approve` / `test_valid_reject` |
| "`APPROVE` requires `findings: []`; an approval carrying findings is malformed" | `blocks.parse_reviewer` | `test_blocks.ReviewerParsing.test_fail_closed_cases_never_approve` |
| Finding fields: id, severity, evidence, summary, required_action | `blocks.FINDING_KEYS` | `test_blocks.ReviewerParsing.test_fail_closed_cases_never_approve` |
| "require a path and at least one line, not exactly one line" | `blocks._LOCATOR` | `test_blocks.ReviewerParsing.test_multi_location_evidence_is_accepted` |
| Synthetic fail-closed reviewer result, never APPROVE | `blocks._synthetic` | `test_blocks.ReviewerParsing.test_fail_closed_cases_never_approve` |
| Worker block: `DONE` with decisions, or `BLOCKED` without, is malformed | `blocks.parse_worker` | `test_blocks.WorkerParsing.test_fail_closed_cases_never_done` |
| No-progress streak: increments only on a REJECT resolving nothing | `counters.CounterState.record_reject` | `test_counters.NoProgressStreak.*` |
| Streak resets on APPROVE and on a progress-carrying REJECT | `counters.CounterState` | `test_counters.NoProgressStreak.test_reject_resolving_a_prior_finding_resets_even_while_raising_new_ones` |
| Total invocations are audit only and never gate | `counters.ReviewerCounters.total_invocations` | `test_counters.TotalInvocations.test_approvals_count_for_audit_but_never_gate` |
| Per-finding total counts FAILED REPAIRS, not re-reports | `counters.CounterState.record_repair_done` | `test_counters.PerFindingTotal.*` |
| "A BLOCKED attempt is not a failed repair" | `counters.CounterState` | `test_counters.PerFindingTotal.test_blocked_repair_is_not_a_failed_repair` |
| Per-finding counter catches a flip-flop a streak would miss | `counters.CounterState.breached` | `test_counters.PerFindingTotal.test_flip_flop_is_caught_though_the_streak_keeps_resetting` |
| "an over-cap call is never made or counted" | `counters.CounterState.would_exceed` | `test_counters.CapBreach.test_pre_check_refuses_an_over_cap_call` |
| Budget `max(25, 6 x unchecked tasks)`, computed once | `budget.default_cap` | `test_budget.DefaultCap` |
| Budget proven BEFORE allocating the attempt | `budget.Budget.can_dispatch` | `test_loop.BudgetRefusal` |
| Re-entry may only increase a cap, never reset a counter | `budget.Budget.raise_cap` | `test_budget.Spending.test_cap_may_only_increase` |
| Retries consume the delegation budget | `retry.call_with_retry` | `test_loop.BudgetRefusal` |
| Escalation: auto only when technical, reversible, in-scope, ungated | `escalation.classify` | `test_escalation.AutoResolvable` |
| Six human-gated domains, any one suffices | `escalation.HUMAN_GATED` | `test_escalation.HumanGated.test_each_category_gates` |
| An unclassifiable question is human-gated | `escalation.classify` | `test_escalation.HumanGated.test_unclassifiable_is_gated` |
| Entry gate: status, open questions, TASKS.md, branch, dirty tree, baseline | `gate.check` | `test_gate.py` |
| State written atomically before proceeding past a transition | `state.Orchestration.save` | `test_state.AtomicSave` |
| `ORCHESTRATION.md` shared with the phase-1 executor | `state.Orchestration` | `test_state.RoundTrip.test_real_phase_one_artifacts_round_trip_byte_identically` |
| Task item is the detection unit; `Covers:`/`Verify:` clauses | `tasks.parse` | `test_tasks.Parsing` |
| Finding task titled `(from <finding-id>)` | `tasks.append_finding_task` | `test_tasks.Parsing.test_finding_task_carries_traceability_to_its_finding` |
| Never commit, push, merge | `loop.Loop` (no git write paths) | `test_loop.Converge.test_two_tasks_converge_and_leave_no_commit` |
| REJECT findings become `TASKS.md` items `(from <finding-id>)` | `tasks.append_finding_task` | `test_repair.RejectRegistersWork` |
| Re-reporting updates the row, never allocates a second task | `tasks.task_for_finding` | `test_repair.ResumeAcrossTheCycle.test_no_duplicate_repair_on_resume` |
| Only an APPROVE resolves a finding; a worker DONE does not | `counters.CounterState.record_approve` | `test_repair.RejectThenRepairThenApprove` |
| After any change, EVERY stale required reviewer is re-scheduled | `loop.Loop._process_task` | `test_repair.FlipFlop` |
| A clean re-approval consumes budget and gates nothing | `counters.ReviewerCounters.clean_reapprovals` | `test_counters.TotalInvocations` |
| DONE requires all six conditions simultaneously | `loop.Loop._state_preconditions` | `test_finalization.BlockingConditions` |
| Freeze the fully approved fingerprint before any lifecycle skill | `loop.Loop._freeze` | `test_finalization.StaleApprovals.test_no_freeze_is_recorded_when_finalization_blocks` |
| Narrow closure allowlist; unexpected changes return to REVIEW | `closure.classify` | `test_finalization.ClosureDeltaRecord` |
| Allowed closure deltas are audited but do not stale approvals | `closure.observe` | `test_finalization.ClosureDeltaRecord.test_closure_delta_persisted` |
| Lifecycle skills are invoked, never their status written | `loop.Loop._lifecycle_step` | `test_finalization.LifecycleGate` |
| A refusing owning skill leaves the run PAUSED with its reason | `loop.Loop._lifecycle_step` | `test_finalization.LifecycleGate` |
| Each attempt records an allowed-path scope; an out-of-scope write fails closed | `loop.Loop._scope_for` | `test_loop.ReadOnlyAgentsMayNotWrite` |

## Resolved divergence — severity vocabulary (D011, 2026-08-31)

**Status: closed.** Raised by this guard on its first run, resolved by the maintainer the same day.

**What was found.** The canonical schema fixes severity to `Critical | High | Medium | Low`, but
`specs/features/033-task-verification-criterion/ORCHESTRATION.md` carries `blocker`, `major` and
`minor` on its `final-conformance:CONF-*` rows.

**The rule now, stated in the protocol itself.** The verdict block's `severity` is a **closed
enum** — `Critical | High | Medium | Low`. Report vocabulary (`blocker`, `major`, `minor`, …) is
legitimate in human narrative: prose above the block, rendered reports, summaries, and the
human-readable Findings-registry rows. It is **not** valid inside the machine-parsed block. There
are no aliases and no implicit normalization; a block carrying a non-canonical severity is
malformed and fails closed.

**Where it is written:** `skills/sdd-orchestrate/SKILL.md` (canonical schema),
`agents/domain-reviewer.md` and `agents/final-conformance-reviewer.md` (the two contracts that
previously omitted it — the root cause), and spec 031's FR-003 as a dated clarification.

**The runner did not change.** Its strictness was already correct. What changed is that the
protocol now says so.

**The 033 artifact was not edited.** It records a run that happened; rewriting it to match a rule
written afterwards would falsify history. Under the rule as now stated, its rows are registry
narrative and legitimate where they sit.

| Boundary | Behaviour | Test |
|---|---|---|
| `Critical`/`High`/`Medium`/`Low` inside the block | accepted | `ObservedDivergence.test_the_canonical_severities_are_accepted` |
| `blocker`/`major`/`minor` inside the block | malformed, synthetic REJECT | `ObservedDivergence.test_the_runner_rejects_a_non_canonical_severity_by_design` |
| the same words in prose *outside* the block | ignored, block parses normally | `ObservedDivergence.test_report_vocabulary_outside_the_block_is_ignored` |
| the enum itself | fixed at four values | `ObservedDivergence.test_the_canonical_vocabulary_is_unchanged` |
| the protocol states the rule | enum named in schema + both contracts | `ObservedDivergence.test_the_protocol_documents_the_closed_enum` |

**This does not close R1.** Removing one known divergence is not the same as being able to detect
the next one. Nothing in this suite compares the runner and `sdd-orchestrate` on the same input.
R1 stays **partially mitigated**.
