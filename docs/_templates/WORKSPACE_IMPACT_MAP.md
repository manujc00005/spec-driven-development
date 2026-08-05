# Impact Map: `<feature name>`

> Template for `.sdd-workspace/specs/features/<slug>/IMPACT_MAP.md`.
> See [`../WORKSPACE_SDD.md`](../WORKSPACE_SDD.md).

**Feature:** `<NNN>-<slug>`
**Date:** `YYYY-MM-DD`
**Approved by:** `<name>` on `YYYY-MM-DD` — *`Not yet approved` until this line is filled in*

> **This document is the boundary.** No project may be modified unless it is listed under
> *Affected projects* below, and no implementation starts before this map is approved. Discovering
> that another project is needed is a **stop condition**: halt, amend this map, get re-approval,
> resume.

## Affected projects

Projects that will be **modified**. Each needs a reason and an owner sign-off.

| Project | Why it must change | Owner | Approved |
|---|---|---|---|
| `<project>` | `<the specific change — not "related">` | `<owner>` | `Yes` / `Pending` |
| `<project>` | `<...>` | `<owner>` | `Yes` / `Pending` |

## Unaffected projects

Every other project in the workspace, and why it stays out. **Read-only for this feature.**

| Project | Why it is out of scope | Read-only reason to open it |
|---|---|---|
| `<project>` | Consumes the endpoint but not the changed field | Understand the response shape |
| `<project>` | No dependency on anything this feature touches | None |

> If a project appears in neither table, this map is incomplete. Every project in `PROJECTS.md`
> belongs in one of the two.

## Contracts touched

Every cross-project contract this feature changes, adds or deprecates. Cross-reference
`INTEGRATION_CONTRACTS.md`.

| Contract | Owner project | Consumers | Change | Breaking? | Contract file updated |
|---|---|---|---|---|---|
| `POST /v1/leads` | `backend-api` | `widget`, `sdk` | adds optional `consent` | No | `Pending` / `YYYY-MM-DD` |
| `<contract>` | `<project>` | `<projects>` | `<add / change / remove>` | `Yes` / `No` | `<date>` |

> A contract row must reach "updated" **before** any consumer implements against it (D009).

## Risks

| Risk | Projects | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| Consumer deploys before producer | `<a>`, `<b>` | Medium | Runtime 4xx on a field the API rejects | Implementation order below; feature-flag or tolerate-absent |
| `<risk>` | `<projects>` | `<L/M/H>` | `<what breaks and how it surfaces>` | `<mitigation>` |

## Implementation order

One project at a time. Contract-owning projects go first, so consumers never build against an
undocumented shape.

| # | Project | What lands | Gate before the next step |
|---|---|---|---|
| 1 | `<contract owner>` | `<change>` | Contract written into `INTEGRATION_CONTRACTS.md`; tests green |
| 2 | `<consumer>` | `<change>` | Integration verified against step 1 |
| 3 | `<consumer>` | `<change>` | `<gate>` |

**Rollback order is the reverse**, unless the contract change is backward-compatible — say which
here.

## Validation plan

What will prove this works. Evidence goes in `VALIDATION.md`; this is the plan.

- **Per project:** `<the command or suite per affected project>`
- **Cross-project:** `<the end-to-end path exercised, and where it runs>`
- **Contract:** `<contract tests, schema checks, or the manual verification and who does it>`
- **Negative:** `<what must still fail / be rejected after the change>`

## Bounded reading list

The **only** files to be opened for this feature. Built from graph reports and contracts, not from
a repository sweep. Extending this list mid-feature requires stating why.

| Project | File | Why |
|---|---|---|
| `<project>` | `<path>` | `<what it answers>` |
| `<project>` | `<path>` | `<...>` |

**Source of this list:** `<which GRAPH_REPORT.md sections, contracts, and manifests it came from>`

## Unknowns

- `Unknown - requires confirmation` — `<what is unresolved and who can resolve it>`
- `Inferred - requires confirmation` — `<what was assumed to build this map>`

> Any unknown that the implementation depends on is a stop condition, not a caveat.
