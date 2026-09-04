<!-- Canonical ORCHESTRATION.md scaffold for `/sdd-orchestrate --autonomous` (spec 031, extended by
     spec 041). Extracted from skills/sdd-orchestrate/SKILL.md, which remains the protocol's home and
     defines every rule about these fields; this file is the ready-to-paste shape. Replace every
     angle-bracket value; do not leave them. -->

# Orchestration: <feature-name>

- Feature: `<feature-path>`
- Protocol version: `1`
- Mode: `autonomous`
- Entry: `ready | adopt`
- Adopted at: `<ISO-8601 | n/a>`
- Adoption baseline commit: `<sha | n/a>`
- Adoption diff base: `<merge-base sha | n/a>` (against `<default-branch>`)
- Started at: `<ISO-8601>`
- Updated at: `<ISO-8601>`
- Effective max iterations (no-progress streak and per-finding rejects): `<N>`
- Effective max delegations: `<N>` (`max(25, 6 × <unchecked tasks at first entry or at adoption>)` unless overridden)

## State

- Phase: `ENTRY | IMPLEMENT | REVIEW | FIX | FINAL | PAUSED | TERMINAL`
- Current task: `<TNNN | none>`
- Current attempt: `<A-NNN | none>`
- Current attempt state: `<PLANNED | DISPATCHED | RESPONDED | VERIFIED | RECOVERED | FAILED | none>`
- Current task verification: `<Verify: criterion and the result of checking it, or none>`
- Delegations used: `<N>`
- Attributed dirty paths: `<sorted paths or none>`
- Baseline verification: `<commands and PASS evidence>`
- No-progress streaks (gating): `security=<N>, domain=<N>, final-conformance=<N>`
- Total invocations (audit only): `security=<N>, domain=<N>, final-conformance=<N>`
- Approvals: `<reviewer=fingerprint or none>`
- Frozen implementation fingerprint: `<fingerprint or none>`

## Attempts

| ID | Timestamp | Agent | Task/objective | State | Allowed paths | Pre fingerprint | Post fingerprint | Outcome |
|---|---|---|---|---|---|---|---|---|

For a task closed on its `Verify:` clause, the `Outcome` cell and the state block's "Current task
verification" field both record the criterion and the result of checking it, not merely the
checked box. Checking never means the loop executing the clause itself (FR-010).

## Inherited

| Task | Checked before adoption | Verify clause | Verification observed by this run |
|---|---|---|---|

## Findings

| Reviewer:finding | Task | Severity | Required action | Status | REJECTs | First seen | Last seen | Resolving verdict/fingerprint |
|---|---|---|---|---|---|---|---|---|

## Delegation log

| Timestamp | Agent | Objective | Outcome | Evidence |
|---|---|---|---|---|

## Escalations

| ID | Classification | Status | Question | Affected tasks | Resolution |
|---|---|---|---|---|---|

## Cap changes

| Timestamp | Invocation | Cap | Old | New | Reason |
|---|---|---|---|---|---|

## Closure delta

- Frozen fingerprint: `<fingerprint or none>`
- Allowed lifecycle/evidence changes: `<exact paths and lifecycle-only fields or none>`
- Observed changes: `<exact paths/fields or none>`
- Unexpected changes: `<exact paths/fields or none>`

## Run result

- Status: `ACTIVE | PAUSED | DONE | ABORTED`
- Resumable: `yes | no`
- Reason: `<reason or next action>`
- Required remediation: `<command/action or none>`
