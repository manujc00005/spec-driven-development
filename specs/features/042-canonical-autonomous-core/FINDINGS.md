# Findings registry — spec 042

Identity is `<reviewer>:<finding-id>` and maps to exactly one repair task. Re-reporting updates the
row; it never allocates a second task.

| Reviewer:finding | Severity | Repair task | Status | Required action |
|---|---|---|---|---|
| security:SEC-001 | Medium | T028 | open | Template and core must state `Protocol version` where the core can read it; replace the substring guard with one that parses the template through `state.Orchestration.loads(...).protocol_version()`. |
| security:SEC-002 | Medium | T029 | open | `_refuse` must pass `resumable=False` on both `UnresumableState` paths and the internal-error path, so exit 16 reports the same resumability whichever route produced it. |
| security:SEC-003 | Low | T030 | open | Add an integration test planting a valid feature folder at `specs/features-old/900-fixture`; it must fail if containment is rewritten as `startswith`. |
| security:SEC-004 | Low | T031 | open | Redact the internal-error diagnostic with the log's secrets set before it reaches stderr; guard the `log.emit` call so a failing write cannot turn exit 70 into a traceback; reconcile `RunLog.emit` with its docstring. |
| security:(adjacent) | — | T032 | open | Raised outside the security lane: `REFUSED`/`PLANNED` are defined in `protocol.py` while AC-001 claims every result value is defined once in `policy`. |

## Verdicts

| Round | Reviewer | Verdict | Fingerprint |
|---|---|---|---|
| 1 | security-reviewer | REJECT (4 findings) | pre-repair tree |

## Note on SEC-001

The sharpest of the four, and it invalidates a claim this feature made about itself.
`evidence/CONTRACT_MUTATIONS.md` records the template guard as **CAUGHT**. That is true of the
mutation that was tried — `Protocol version: \`1\`` → `\`2\``, which changes the substring — and false
of the divergence actually present: the guard is
`assertIn("Protocol version: \`1\`", template_text)`, satisfied by the field existing **anywhere, in
any spelling the core cannot parse**. `parse_fields` (`state.py:214`) is case-sensitive and does not
strip backticks, and the template states the field in the preamble rather than in `## State`, so the
core reads a template-shaped document as version 1 regardless of what it declares.

A mutation test proves a guard catches *the mutation you thought of*. It does not prove the guard
checks the property. That is worth more than the fix.
