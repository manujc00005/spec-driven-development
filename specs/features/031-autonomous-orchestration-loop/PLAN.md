# Implementation Plan: autonomous-orchestration-loop

## Summary

Add an autonomous mode to `sdd-orchestrate` by shipping three things, all markdown
contracts (no executable code): (1) a new autonomous-mode section in the skill defining
the entry gate, loop protocol, recoverable attempts, escalation rule, monotonic caps,
current-tree review invalidation, findings registry, closure boundary, termination, and re-entry — plus
the verdict/completion block schemas as the single source of truth; (2) mandatory
structured output blocks in the five delegated-agent contracts; and (3) Codex adapter
parity documentation for the degraded
sequential mode. Verified by `check-consistency.sh` plus a seeded calibration run on a
disposable demo feature (spec 029 style).

## Related spec

[SPEC.md](SPEC.md)

## Impacted areas

- `skills/sdd-orchestrate/SKILL.md` — autonomous-mode section, block schemas, SDD
  Contract `outputs` gains `ORCHESTRATION.md`.
- `agents/security-reviewer.md`, `agents/domain-reviewer.md`,
  `agents/final-conformance-reviewer.md` — verdict block in Outputs.
- `agents/implementer.md`, `agents/fast-worker.md` — completion block in Outputs.
- `adapters/codex/PARITY.md` — degraded-mode documentation. The current Codex prompts do
  not name `sdd-orchestrate`, so they are outside the change boundary.
- `docs/SDD-ORCHESTRATION.md` — user-facing autonomous-mode section, and `CHANGELOG.md` — feature
  entry (both added by D018; the original plan omitted them, which is why no review caught them).
- No changes to installers, `profiles.json`, hooks, or scripts.

## Context budget

### Reading list

- `specs/features/031-autonomous-orchestration-loop/` (all files)
- `skills/sdd-orchestrate/SKILL.md`
- `agents/security-reviewer.md`, `agents/domain-reviewer.md`,
  `agents/final-conformance-reviewer.md`, `agents/implementer.md`,
  `agents/fast-worker.md`
- `skills/sdd-guardrails/SKILL.md` (section 11 only — status ownership)
- `adapters/codex/PARITY.md`, `adapters/codex/AGENTS.md`,
  `adapters/codex/prompts/` (listing; read only files naming orchestrate)
- `scripts/check-consistency.sh` (read-only — what it validates; do not modify)

No whole-repo scans. Nothing under `evals/`, `docs/`, or other features is needed.

### Model routing

- Contract/schema writing (T002–T004) and calibration runs (T008–T014): main
  orchestrator session — the autonomous protocol is the artifact under test, and the
  calibration runs exercise this very session's skill.
- Mechanical agent-file edits (T005–T007): fast-worker — the schema is already decided;
  the edits are bounded per file.
- deep-reasoner: not planned. Only if the escalation-rule wording produces a genuine
  design contradiction during review.

## Proposed approach

1. **Schema first, single source.** Write the autonomous-mode section in
   `sdd-orchestrate/SKILL.md`: six-precondition entry gate, loop protocol with reviewer
   selection reusing existing Level-3 triggers, the escalation rule (auto vs human), caps
   (3 per reviewer / 25 delegations, monotonically increasable on authenticated re-entry),
   recoverable attempt lifecycle, all-stale-review invalidation, termination and abort contracts,
   re-entry from `ORCHESTRATION.md` with diff fingerprints, findings registry, and the explicit
   post-approval closure boundary. Define the verdict block and completion block schemas here —
   agent files will reference, never redefine (D004).
2. **Propagate to agent contracts.** Append the mandatory block to each agent's Outputs
   section with a one-line pointer to the skill schema. Prose stays; control flow keys
   only on the block (D003).
3. **Persist from the skill contract.** The autonomous section contains the canonical
   `ORCHESTRATION.md` scaffold (State / Attempts / Findings / Delegation log / Escalations /
   Cap changes / Closure delta / Run result) and
   creates it inside the active feature on first entry. Do not add a shared template:
   templates are installable artifacts registered in `profiles.json`, which the SPEC
   explicitly excludes from scope (D008).
4. **Codex parity.** Document the degraded sequential mode in `adapters/codex/PARITY.md`:
   same blocks, same file schema, same escalation rule, no subagent fan-out. Runtime
   smoke test stays gated on a Codex CLI existing (gates `Done`, not `Ready`).
5. **Calibrate.** Build a disposable demo feature in a throwaway worktree (never a
   numbered folder under `specs/features/`), seed one reviewer-findable defect, one
   technical blocker, one human-gated blocker, cross-review invalidation, an interrupted write,
   repeated finding IDs, cap resumption, a mutating baseline, and expected/unexpected closure
   deltas; run the AC-001..AC-010 matrix; record evidence in `CALIBRATION.md` inside this feature
   folder.

## Alternatives considered

- **Peer-to-peer agent messaging** instead of hub + file blackboard: rejected — not
  auditable, no ordering guarantees, duplicates context, and Codex has no equivalent, so
  it would violate the provider-parity rule.
- **A verdict parser script in `scripts/`**: rejected for phase 1 — the orchestrator LLM
  parses a fenced yaml block reliably, `check-consistency.sh` already validates
  contracts, and the phase-2 SDK runner will be the first consumer that genuinely needs
  programmatic parsing of the same schema.
- **JSON state file instead of `ORCHESTRATION.md`**: rejected — SDD artifacts are
  human-readable markdown first; the audit-log NFR requires a maintainer to read the
  run's history without tooling.
- **Checkpoint commits per task**: rejected in clarification (OQ-1/D002) — contradicts
  the agents' own forbidden-actions contracts; deferred to the phase-2 runner.

## Dependencies

- None at runtime — markdown only.
- Claude Code 2.1.235 is available for the primary calibration run.
- Codex CLI 0.147.0-alpha.6.6 is available in this environment, so the degraded-mode
  smoke test is required before `Done`, not deferred.

## Risks

- **LLM verdict-parsing reliability**: a reviewer may emit a malformed block. Mitigated
  in-spec (one re-request, then REJECT; never APPROVE by default) and exercised in
  calibration (AC-006 path).
- **Calibration cost**: the E2E matrix runs real delegations. Bounded by the same caps
  the feature introduces; the demo feature is deliberately tiny.
- **Contract drift**: an agent file could later diverge from the skill schema.
  Mitigated by single-source + reference (D004) and `check-consistency.sh` (AC-003).
- **Provider CLI behavior**: Codex autonomous mode is prompt-based and sequential, so a
  smoke test can prove this version's behavior but not deterministic enforcement.
  `PARITY.md` must keep that limitation explicit.
- **Autonomy overreach**: the escalation rule mis-classifying a product decision as
  technical is the worst failure mode. The human-gated list is deliberately over-broad
  (any one trigger suffices) and AC-004 seeds exactly this case.
- **Split-snapshot review**: one reviewer may remain approved on a fingerprint older than another
  reviewer's fix. Mitigated by invalidating every non-matching approval after any implementation
  change (D015) and the two-reviewer AC-008 calibration.
- **Interrupted side effects**: a worker may edit files before its response is persisted. Mitigated
  by pre-call attempt records, allowed-path attribution, fingerprint reconciliation, and fail-closed
  handling for unexplained paths (D014/AC-005).
- **Self-invalidating close**: lifecycle skills legitimately change SDD metadata after approval.
  Mitigated by freezing the reviewed implementation and separately auditing a narrow closure delta
  (D015/AC-010); requirement or implementation changes are never allowed through that boundary.
- **Demo-fixture leakage**: a disposable feature accidentally committed under
  `specs/features/` would collide with real numbering. Mitigated: fixture lives in a
  throwaway worktree only.
- **Cap semantics regressing to workload counting**: the D017 model only works if clean
  re-approvals stay exempt from both counters. A future edit that "simplifies" this back into one
  invocation counter silently restores the abort-at-task-4 bug. AC-011(a) is the regression guard.
- **Untested budget factor**: the `6 ×` delegation-budget default is an estimate. If the AC-011 run
  exhausts it on a converging feature, the factor — not the non-convergence caps — is what to
  raise; conflating the two is how the original bug happened.
- **Fixtures too small to detect protocol bugs**: the three-step demo could not surface the cap
  defect. Calibration fixtures must be sized against the thresholds they exercise.

## Test strategy

- **Unit**: none — no executable code ships.
- **Baseline and integration suite**: `bash scripts/check-consistency.sh` and
  `bash scripts/check-consistency.test.sh`. These are the PLAN-mandated entry/exit suite;
  there is no application build, typecheck, or lint target for this markdown-only diff.
- **E2E**: seeded calibration matrix on the disposable demo feature — happy path
  (AC-001), entry-gate refusals including a mutating green baseline (AC-002/AC-010), escalation fork
  (AC-004), kill-after-write recovery and out-of-scope refusal (AC-005), forced-REJECT cap abort plus
  monotonic-cap resume (AC-006), safety invariants (AC-007), cross-review invalidation (AC-008),
  finding deduplication (AC-009), closure-delta invalidation (AC-010), and the four cap-semantics
  behaviors on a longer-than-`max-iterations` fixture (AC-011). Evidence in `CALIBRATION.md`.
- **Manual**: one real small feature run end-to-end by the maintainer before
  `/spec-close`; Claude Code and Codex smoke runs per AC-013, each recorded as a pass or as an
  explicit closure blocker.
- **Regression**: non-autonomous `sdd-orchestrate` invocations and standalone agent
  invocations must behave as today — verified by inspection of the diffs (additive
  sections only) plus the check-consistency run.

## Rollback strategy

Pure documentation change: `git revert` of the feature commits restores every contract.
No installer, profile, schema, or state migration. Adopters are unaffected until they run
`update.sh`; reverting before a release tag removes the feature entirely. A published
`ORCHESTRATION.md` in some adopter's feature folder is inert without the skill section.

## PLAN verification checklist

- [x] The plan covers all acceptance criteria (AC-001..AC-013).
- [x] The plan avoids behavior outside the spec.
- [x] The Context budget section is filled (reading list + model routing), not left as placeholder.
- [x] Risks are documented.
- [x] Test strategy is documented.
- [x] Rollback strategy is documented.
- [x] SPEC.md status has been updated to `Ready`.
