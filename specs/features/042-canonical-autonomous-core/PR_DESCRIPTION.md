## Summary

- Establishes `sdd_runner` as the executable authority for the autonomous SDD protocol through the
  stable `run(RunRequest) -> RunOutcome` API.
- Moves protocol decisions out of the CLI, centralizes policy and adds versioned, fail-closed state,
  audit and gate behavior.
- Adds executable conformance evidence for public API boundaries, every gate refusal and all
  authorized differences from `main`.

## Related spec

- Spec: `specs/features/042-canonical-autonomous-core/`
- Status: `Done`

## Acceptance criteria coverage

- AC-001 — centralized executable policy and duplicate-definition guard: Covered.
- AC-002 — frozen public request/outcome interface without internal-object leakage: Covered.
- AC-003 — CLI consumes only `run` and `RunRequest`; prose projections contract-tested: Covered.
- AC-004 — versioned state plus backward-compatible reads and fail-closed versions: Covered.
- AC-005 — suite floor and assertion-preservation evidence: Covered.
- AC-006 — all enumerated protocol surfaces protected by contract mutations: Covered.
- AC-007 — start, pause, abort, resume and core-complete through the public API: Covered.
- AC-008 — golden behavior identity outside FR-009's structured differences: Covered.
- AC-009 — packaging, stdlib-only runtime and installer/manifest parity: Covered.
- AC-010 — future ownership seams declared without implementation: Covered.
- AC-011 — bounded public surface with no CLI import outside it: Covered.
- AC-012 — executable-authority inversion recorded and guarded: Covered.
- AC-013 — preserved autonomous-feature prompt remains byte-identical and untracked: Covered.

## Changes

| Area | Files | What changed |
|---|---|---|
| Protocol | `runner/sdd_runner/policy.py`, `protocol.py`, `seams.py` | Canonical policy, public execution API and future ownership seams. |
| Runtime | `gate.py`, `loop.py`, `state.py`, `resume.py`, `tasks.py`, `log.py` | Centralized gates, convergence, persistence, repair identity and fail-closed audit behavior. |
| Adapter | `runner/sdd_runner/__main__.py` | Thin CLI over `run`/`RunRequest`, retaining stable rendering and notification behavior. |
| Projections | `runner/README.md`, `docs/SDD-ORCHESTRATION.md`, orchestration skill/template | Authority and protocol values aligned with the executable core. |
| Evidence | `runner/tests/`, feature `evidence/` | Contract tests, 30 golden scenarios, 10 `main` baselines and an 18-row mutation harness. |

## Decisions made

- Kept the `sdd_runner` package name and exposed depth through a small `__all__` (D001).
- Made the executable core authoritative while retaining the spec-update process (D004).
- Kept contract surfaces enumerated rather than repository-searched (D005).
- Preserved local-only maintainer packaging (D006).
- Recorded three intentional observable differences in FR-009 through D003, D015 and D018.
- Kept one finding identity mapped to one canonical repair task (D016/D017).
- Rejected and reverted dry-run backend-option validation within this refactor (D011).

## Tests

- [x] Unit, contract and integration suite: 494 tests, OK.
- [x] Golden CLI replay: 30/30 stable.
- [x] Retrospective `main` baseline capture: 10/10 stable.
- [x] Gate-condition matrix: 15/15 covered.
- [x] Contract mutation harness: 18/18 CAUGHT; final suite green.
- [x] Compile, repository consistency, installer parity and diff checks pass.
- [x] Domain, security, standards, final-conformance, spec and QA reviews complete.

## Migrations / Schema

None.

## Deployment notes

No deployment or installer change. The runner remains experimental maintainer tooling and no real
provider is enabled by this feature.

## Risks

- `run.jsonl` detects failed writes but is not tamper-evident (DEBT-012).
- Dry runs intentionally retain `main`'s backend-option validation asymmetry (DEBT-011).
- Real Claude/Codex provider operation remains unverified and gated.

## Follow-up work

- Make `/sdd` autonomous by default and add autonomous free-form entry in later specs.
- Design tamper evidence for the durable audit log.
- Decide whether dry-run should validate backend-exclusive options.
- Resolve the remaining non-blocking hygiene items in DEBT-013.

## Checklist

- [x] Implementation matches all acceptance criteria in the spec.
- [x] Observable differences are explicitly authorized and evidenced.
- [x] Tests were added or updated for changed behavior.
- [x] All decisions are documented in `DECISIONS.md`.
- [x] SPEC status is `Done`.
- [x] Security-sensitive behavior was reviewed.
- [x] No database, migration or performance-sensitive change was introduced.
- [x] Unrelated preserved file remains untracked and unchanged.
