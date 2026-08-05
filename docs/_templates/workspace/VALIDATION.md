# Validation: `<feature name>`

> Template for `.sdd-workspace/specs/features/<slug>/VALIDATION.md`. Evidence, not intentions.
> See [`../../WORKSPACE_SDD.md`](../../WORKSPACE_SDD.md).

**Feature:** `<NNN>-<slug>`
**Last updated:** `YYYY-MM-DD`

**Rule:** a row is filled in only after the check has **run**. "Will be covered by the existing
suite" is not evidence. A check that was written but never executed is recorded as
`Written but not run` — which never counts as satisfied.

## Per-project validation

| Project | Check | Command | Run on | Result | Evidence |
|---|---|---|---|---|---|
| `backend-api` | Unit + integration | `./mvnw verify` | `YYYY-MM-DD` | Pass (142 tests) | `<CI run or local output ref>` |
| `shared-sdk` | Unit | `npm test` | `YYYY-MM-DD` | Pass (58 tests) | `<ref>` |
| `<project>` | `<what it proves>` | `<command>` | `YYYY-MM-DD` | `Pass` / `Fail` / `Written but not run` / `Not run` | `<ref>` |

## Cross-project validation

The paths that only break when the projects are combined. This is the section a per-project suite
cannot cover.

| Path exercised | Projects | How it was run | Run on | Result | Evidence |
|---|---|---|---|---|---|
| Widget submits a lead with consent → API persists → CRM receives event | `widget`, `backend-api`, `crm-platform` | `<manual against staging / e2e suite / script>` | `YYYY-MM-DD` | `Pass` / `Fail` | `<ref>` |
| `<path>` | `<projects>` | `<how>` | `YYYY-MM-DD` | `<result>` | `<ref>` |

**Environment:** `<local / staging / which>` — and which project versions were deployed together.

## Contract validation

One row per contract in `IMPACT_MAP.md`. Verifies the contract as written, not the implementation
that happens to satisfy it.

| Contract | Verified how | Both sides checked? | Backward compatible? | Run on | Result |
|---|---|---|---|---|---|
| `POST /v1/leads` | OpenAPI schema check + consumer contract test | Producer + `sdk` | Yes — field optional | `YYYY-MM-DD` | Pass |
| `<contract>` | `<schema check / contract test / manual>` | `<producer + which consumers>` | `Yes` / `No` | `YYYY-MM-DD` | `<result>` |

**Old-consumer check:** `<was a consumer running the previous version verified against the new
producer? If not, say so — that is the compatibility claim's weakest point.>`

## Negative checks

What must still fail or be rejected after the change.

| Expectation | Verified how | Run on | Result |
|---|---|---|---|
| Request without consent still succeeds (field optional) | `<test>` | `YYYY-MM-DD` | Pass |
| `<expectation>` | `<how>` | `YYYY-MM-DD` | `<result>` |

## Gaps

Everything the validation above does **not** cover. Being explicit here is what makes the rest
trustworthy.

- `<what is untested, and the risk that leaves>`
- `Not run` — `<check that was planned but skipped, and why>`

## Rollback notes

| Project | Rollback step | Reversible? | Rehearsed? |
|---|---|---|---|
| `<project>` | `<revert deploy / redeploy previous tag / down-migration>` | `Yes` / `No — point of no return` | `Yes YYYY-MM-DD` / `No` |

- **Rollback order:** `<usually the reverse of the implementation order — state it explicitly>`
- **Point of no return:** `<the first step that cannot be undone — typically a destructive
  migration or a published package version. If there is none, say "none".>`
- **Data implications:** `<what happens to rows written under the new behaviour if the code is
  rolled back>`
- **Contract implications:** `<does rolling back one project break a consumer already on the new
  contract?>`

> A rollback that has never been executed is `Written but not run`. Say so rather than implying it
> works.
