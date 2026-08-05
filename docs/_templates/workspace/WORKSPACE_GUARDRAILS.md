# Workspace Guardrails

> Template for `.sdd-workspace/guardrails/WORKSPACE_GUARDRAILS.md`. The hard rules for any agent or
> human working across this workspace. See [`../../../WORKSPACE_SDD.md`](../../../WORKSPACE_SDD.md).

These are not style preferences. Each one exists because breaking it has a known cost: an
unbounded blast radius, a context bill that makes the workspace layer pointless, or a contract that
changed under a consumer without warning.

## Prohibitions

**Scope**

- **No broad edits.** No change touching many projects "while we're in there". One project at a
  time, in the order `IMPACT_MAP.md` states.
- **No implementation before the impact map.** The map is written and approved first — always.
- **No project outside the impact map.** If a project is not listed as *affected*, it is not
  edited. Not a config file, not a README, not a version bump.
- **No scope widening mid-feature.** Discovering another project is needed is a stop condition,
  not a reason to continue.

**Contracts**

- **No silent contract changes.** A REST shape, event schema, webhook payload, shared-package API
  or cross-project env var changes in `INTEGRATION_CONTRACTS.md` **before** any dependent project
  implements against it.
- **No invented dependencies.** No edge in `DEPENDENCY_GRAPH.md` without evidence and a confidence
  marker. Inference is labelled as inference.
- **No confidence upgrades without a human.** `Inferred` becomes `Confirmed` only when someone
  confirms it.

**Context**

- **No full-repository reads** across the workspace. Never "read all the projects".
- **No wholesale `.graphify/graph.json` load.** Use `GRAPH_REPORT.md` or Graphify's scoped
  read-only queries.
- **No broad grep across every project without a hypothesis.** A cross-project search needs a named
  symbol, route or package and a reason to expect it somewhere specific.

**Safety**

- **No secrets.** No reading, copying, printing or writing `.env` files, tokens, keys or
  credentials — in any project. Config *names* may be recorded; values never.
- **No `git add .`.** Staging is explicit, per file, and the user's decision.
- **No `git commit`. No `git push`.** Not in the workspace root, not in any child project.
- **No dependency installs or upgrades** in a child project unless a task explicitly requires it.
- **No Graphify install or run without approval.** Proposing `scripts/setup-graphify.sh` is
  allowed; running it unprompted is not.

## Stop conditions

Halt and ask. Do not proceed on a best guess.

| Condition | Why it stops the work |
|---|---|
| A needed project is not in `IMPACT_MAP.md` | The approved boundary no longer matches reality — amend and re-approve |
| Project ownership is unknown | Nobody can approve a change to something with no owner |
| A dependency is unclear or only `Inferred`, and the next step depends on it being real | Building on an unconfirmed edge propagates the guess into code |
| A contract the change relies on is undocumented | The change would define the contract by accident |
| Graphify is unavailable **and** the fallback context cannot answer the question | Partial context is fine for a map; it is not fine for an edit |
| The user has not approved modifying a given project | Approval is per project, per feature |
| Two projects claim ownership of the same data | The collision has to be decided before either is changed |

## What "affected" means

A project is **affected** — and therefore editable — only if `IMPACT_MAP.md` lists it under
affected projects for the feature currently being implemented. Everything else, including projects
listed as *unaffected* and projects excluded in `WORKSPACE_CONTEXT.md`, is read-only.

Reading a non-affected project to understand a contract is allowed and expected. Writing to one is
not.

## Escalation

When a stop condition fires:

1. Stop at the current file. Do not start the next task.
2. State which condition fired and what evidence triggered it.
3. Propose the smallest amendment that would unblock — usually an added project in the impact map
   or a contract entry.
4. Wait for approval. Resume only after the amended map or contract is written down.
