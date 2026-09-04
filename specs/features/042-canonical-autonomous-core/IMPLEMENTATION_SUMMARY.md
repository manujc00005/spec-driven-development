# Implementation Summary: canonical-autonomous-core

## Overview

Spec 042 makes `runner/sdd_runner/` the executable, provider-neutral authority for the autonomous
SDD protocol behind the stable `run(RunRequest) -> RunOutcome` interface. The CLI is now a thin
public-interface consumer, while prose surfaces are contract-tested projections of the core.

**Status:** Complete — 2026-09-04

## What was built

- A centralized `policy` module for protocol vocabulary, limits, states, results, triggers and exit
  codes, with guards against duplicate executable definitions.
- A small frozen public interface and a protocol module that owns entry, resume, gate, budget,
  backend resolution, execution outcome and freeze semantics.
- Versioned `ORCHESTRATION.md` state with backward-compatible version-1 reads and fail-closed handling
  of malformed or unsupported versions.
- A CLI adapter that parses arguments, invokes only the public interface and renders outcomes without
  reimplementing protocol decisions.
- Fail-closed audit logging, repair-task identity resolution and structured refusal when the baseline
  suite cannot launch.
- Contract, integration, golden, retrospective-baseline and mutation evidence covering every gate
  condition and each authorized observable difference.

## Authorized observable differences

FR-009 is the canonical structured list:

- `DIFF-001` / D003 — additive `Protocol version` state header.
- `DIFF-002` / D015 — an unavailable durable audit transcript becomes a stable exit-70 failure.
- `DIFF-003` / D018 — a baseline suite that cannot launch becomes a structured exit-10 refusal.

All other recorded CLI behavior remains byte-identical to `main`.

## Verification

- 494 unit/contract/integration tests: OK.
- 30/30 golden CLI scenarios stable.
- 10/10 retrospective `main` baselines stable; nine byte-identical and one matching `DIFF-003`.
- 15/15 terminal gate conditions mapped to real CLI scenarios.
- 18/18 contract mutations caught; final suite green after all reverts.
- `compileall`, `check-consistency.sh`, installer parity and `git diff --check`: clean.
- T025 final conformance: AC-001…AC-013 PASS on the complete 97-path reviewed tree.
- T026 spec review and QA review: Pass.

## Deferred work

- DEBT-011 — dry-run validation of backend-exclusive options.
- DEBT-012 — tamper evidence for `run.jsonl`.
- DEBT-013 — four non-blocking record/test hygiene items.
- Real provider enablement, autonomous entry/default routing and lifecycle finalization remain future
  features by design.
