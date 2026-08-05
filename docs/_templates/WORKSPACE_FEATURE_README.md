# Cross-project features

> Template for `.sdd-workspace/specs/README.md`. Explains the structure every cross-project feature
> follows. See [`../WORKSPACE_SDD.md`](../WORKSPACE_SDD.md).

## When a feature belongs here

The rule is mechanical:

- **More than one project in the impact set** → a workspace feature, in this folder.
- **One project** → that project's own `specs/features/**`. Nothing changes for it.

If you are unsure, sketch the impact map first. If it names one project, the feature was never a
workspace feature.

## Folder structure

```
.sdd-workspace/specs/features/<feature-slug>/
├── SPEC.md              # problem, goal, non-goals, acceptance criteria — workspace-wide
├── PLAN.md              # approach, alternatives, risks, rollback
├── TASKS.md             # tasks grouped BY PROJECT, in implementation order
├── DECISIONS.md         # decisions made during this feature
├── IMPACT_MAP.md        # affected + unaffected projects — the boundary. Required before implementing
├── PROJECT_CHANGES.md   # what actually changed, per project
└── VALIDATION.md        # per-project, cross-project and contract validation evidence
```

The first four are the standard SDD documents, scoped to the workspace instead of one repository.
The last three are what workspace work adds.

## The three workspace-specific documents

| Document | Answers | Written |
|---|---|---|
| `IMPACT_MAP.md` | Which projects may be touched, in what order, and what may **not** be touched | **Before** implementation. Approved before any edit |
| `PROJECT_CHANGES.md` | What actually changed in each project, and whether it moved a contract | During and after implementation |
| `VALIDATION.md` | What was run, where, and what it proved — per project, across projects, and per contract | As evidence accumulates; never pre-filled with intentions |

## Workflow

1. **Read `.sdd-workspace/`** — context, projects, dependency graph, contracts, guardrails. Nothing
   else yet.
2. **Write `SPEC.md`** — the problem across projects, not per project.
3. **Write `IMPACT_MAP.md`** — affected, unaffected, contracts touched, risks, order, validation
   plan, bounded reading list.
4. **Get the affected list approved.** No file is opened for editing before this.
5. **Write `PLAN.md` and `TASKS.md`** — tasks grouped by project, ordered so contract-owning
   projects come first.
6. **Implement one project at a time**, strictly within the approved boundary.
7. **Update `INTEGRATION_CONTRACTS.md`** *before* the dependent project implements against a
   changed contract.
8. **Fill `PROJECT_CHANGES.md` and `VALIDATION.md`** from what actually ran.

## Rules that apply to every feature here

- No project outside `IMPACT_MAP.md` may be modified.
- Contract changes land in `INTEGRATION_CONTRACTS.md` before dependent implementation.
- No `git add .`, no commit, no push.
- No secrets read, copied or written.
- No full-repository reads; no `graph.json` load; no hypothesis-free cross-project grep.
- Stop conditions live in `../guardrails/WORKSPACE_GUARDRAILS.md` and are not overridable by a task.

## Naming

`<NNN>-<short-slug>`, e.g. `001-lead-consent-capture`. Numbers are workspace-scoped and independent
of any project's own spec numbering.

## Index

| Feature | Status | Projects affected |
|---|---|---|
| `<NNN>-<slug>` | `Draft` / `Ready` / `In progress` / `Done` | `<a>`, `<b>` |
