# Workspace onboarding (Codex prompt)

Derived from [`../../../skills/sdd-workspace-onboarding/SKILL.md`](../../../skills/sdd-workspace-onboarding/SKILL.md).
The procedure is identical; only the packaging differs — this is a prompt you paste or invoke, not
a native agent.

> **No native-agent claim.** This adapter has no subagent isolation and no enforced tool grant. The
> boundaries below are prose you are expected to follow, not a sandbox that prevents you from
> crossing them. See [`../PARITY.md`](../PARITY.md).
>
> **No global configuration.** Nothing here changes Codex settings, installs anything, or touches
> a machine-wide config file.

---

## Role

You are onboarding a **workspace** — a folder containing several related projects — into Workspace
SDD. You produce a bounded, evidence-backed map of how those projects depend on each other.

> Graphify maps code-level dependencies. Workspace SDD maps project-level dependencies.

Full doctrine: [`../../../docs/WORKSPACE_SDD.md`](../../../docs/WORKSPACE_SDD.md).
Output templates: [`../../../docs/_templates/workspace/`](../../../docs/_templates/workspace/).

## Inputs — confirm before starting

1. **Workspace root** — defaults to the current directory.
2. **Include / exclude list** — optional; defaults to every detected project.
3. **May Graphify be run?** — **defaults to no.** Without an explicit yes, only *propose* commands.
4. **May anything be written inside a child project?** — **defaults to no.**

If 3 or 4 were not stated, ask before step 2 and wait for the answer.

## Procedure

### 1. Detect candidate projects

Search one and two levels deep for manifests — `package.json`, `pom.xml`, `build.gradle*`,
`pyproject.toml`, `go.mod`, `Cargo.toml`, `composer.json`, `*.csproj`, `Gemfile` — and monorepo
markers (`pnpm-workspace.yaml`, `turbo.json`, `lerna.json`, a root `workspaces` field).

Detect by manifest and structure, **not** by `.git`: a folder of clones and a monorepo are both
valid. Always exclude `node_modules/`, `vendor/`, `.venv/`, `dist/`, `build/`, `target/`, `.git/`.

**Present the list and stop.** Get inclusions and exclusions confirmed before reading further.

### 2. Summarise each project from bounded sources

Per project, in order, stopping once the four questions below are answered:

1. `<project>/.graphify/GRAPH_REPORT.md` (canonical) or a legacy root `GRAPH_REPORT.md`.
2. The manifest — name, version, dependencies, published package name.
3. `README`, first ~60 lines.
4. API descriptors — `openapi.yaml`/`.json`, `*.proto`, `schema.graphql`.
5. `docs/ARCHITECTURE.md` if the project was already SDD-onboarded.

Four questions: **type/stack**, **what it owns**, **what it publishes**, **what it consumes**.

**Graphify is optional.**

- Report present → use it; if older than the newest source, mark it stale and still use it for
  orientation.
- Report missing → fallback mode for that project; say so. If a Graphify run was approved, propose
  `scripts/setup-graphify.sh --project-dir <path>` and wait. Never run it unprompted.
- `graph.json` present but no report → still "report missing". **Never read `graph.json`.**
- Graphify absent entirely → whole run is fallback; record **Context completeness: partial**.

### 3. Derive relationships, with evidence

Cross-project edges come from manifests, descriptors and configuration — Graphify never crosses a
project boundary. Look for: a published package name in another project's dependencies; a route
from one descriptor in another's client or config; matching event/topic names; env vars naming
another project's origin or key.

Each edge records `From / To / Reason / Contract / Evidence / Confidence / Risk`, with `Confidence`
from a closed vocabulary: `Confirmed`, `Inferred - requires confirmation`,
`Unknown - requires confirmation`.

**Never write an edge without evidence.** Sharing a parent folder is not evidence.

### 4–7. Write the workspace layer

At the workspace root, from the templates:

- `.sdd-workspace/PROJECTS.md` — `Project | Path | Type | Stack | Owns | Public contracts |
  Graphify status`, plus detection evidence and excluded paths.
- `.sdd-workspace/DEPENDENCY_GRAPH.md` — the relationship blocks, a Mermaid overview (solid =
  Confirmed, dashed = Inferred/Unknown), ownership collisions, cycles.
- `.sdd-workspace/INTEGRATION_CONTRACTS.md` — REST APIs, events, webhooks, shared packages,
  environment variables, auth boundaries, data ownership. Config **names** only, never values.
- `.sdd-workspace/WORKSPACE_CONTEXT.md` — purpose, included projects, workflow rules, context
  strategy, Graphify status, ownership, unknowns, owner notes.
- `.sdd-workspace/SHARED_DECISIONS.md` — seeded with the D001–D010 baseline.
- `.sdd-workspace/guardrails/WORKSPACE_GUARDRAILS.md` and `.sdd-workspace/specs/README.md`.

If `.sdd-workspace/` exists, update in place and show a diff before touching any human-authored
section.

### 8. Report unknowns

Close on what could not be determined — fallback-mode projects, `Inferred` edges, unknown
ownership, undocumented contracts — each with the next step that would resolve it. Do not close
with a summary implying completeness.

## Token rules

Reading ladder, each rung only when the one above is insufficient:

1. Existing `.sdd-workspace/` documents.
2. Per-project `GRAPH_REPORT.md`, only for projects the previous rung named.
3. Manifests, README, API descriptors.
4. A bounded reading list, written down first.
5. Concrete implementation files — only those on the list.

Never read every file in a project or every project; never load `.graphify/graph.json`; never grep
across every project without a hypothesis; defer implementation files to a feature's
`IMPACT_MAP.md`.

## Stop conditions

- Unknown project ownership.
- An unclear dependency the next step depends on.
- A missing contract definition.
- Graphify unavailable **and** the fallback context insufficient for a question the map needs.
- Project modifications not approved by the user.
- Two projects claiming the same data.

## Forbidden

- No implementation — no application code, config or dependency change, in any project.
- No writes outside `.sdd-workspace/`, except a user-approved Graphify refresh.
- No `git add .`, no commit, no push.
- No secrets read, copied, printed or written.
- No wholesale `graph.json` load.
- No broad grep across every project.
- No invented dependencies.
- No Graphify install or run without explicit approval.
- No global Codex configuration change.

## Output

```markdown
# Workspace onboarding: <workspace root>

## Projects detected
## Graphify coverage        (X of N; Context completeness: Complete | Partial)
## Relationships found      (N Confirmed, M Inferred, K Unknown)
## Files written
## Unknowns requiring confirmation
## Suggested next steps
```

## Next

Cross-project features go in `.sdd-workspace/specs/features/<slug>/` and start with an approved
`IMPACT_MAP.md`. No project may be modified unless that map lists it as affected.
