# Projects

> Template for `.sdd-workspace/PROJECTS.md`. One row per detected project.
> See [`../../WORKSPACE_SDD.md`](../../WORKSPACE_SDD.md).

**Last updated:** `YYYY-MM-DD`
**Detection basis:** manifest and structure markers (not `.git` presence) — monorepo packages and
independent clones are both valid projects.

## Project inventory

| Project | Path | Type | Stack | Owns | Public contracts | Graphify status |
|---|---|---|---|---|---|---|
| `<name>` | `./<dir>` | backend-api | Java 21 / Spring Boot 3 | Lead data model, persistence | `POST /v1/leads`, event `lead.created` | Report `YYYY-MM-DD` |
| `<name>` | `./<dir>` | widget | TypeScript / Vite | Embed markup, consent UI | none (consumer only) | Missing — refresh proposed |
| `<name>` | `./<dir>` | shared-sdk | TypeScript, published npm | HTTP client for the API | npm `@acme/sdk` v2.4 | Report `YYYY-MM-DD` (stale) |
| `<name>` | `./<dir>` | wordpress-plugin | PHP 8.2 | WP admin screen | WP hooks `acme_lead_*` | Not applicable |
| `<name>` | `./<dir>` | frontend-admin | Next.js 15 | Lead listing, export | none (consumer only) | Missing |

**Column meanings**

- **Type** — `backend-api`, `frontend-admin`, `widget`, `shared-sdk`, `wordpress-plugin`,
  `crm-platform`, `worker`, `infra`, `library`, `docs`. Extend as needed; keep it one token.
- **Stack** — language, runtime, primary framework. Enough to know which reviewer skills apply.
- **Owns** — the data, behaviour or surface this project is the authority for. If two projects
  claim the same thing, that is a risk row in [`DEPENDENCY_GRAPH.md`](DEPENDENCY_GRAPH.md), not a
  detail to resolve silently.
- **Public contracts** — what *other* projects may depend on: endpoints, events, webhooks,
  published packages, hooks. `none (consumer only)` is a meaningful answer.
- **Graphify status** — `Report YYYY-MM-DD`, `Report YYYY-MM-DD (stale)`, `Missing`,
  `Missing — refresh proposed`, or `Not applicable`. A project with `graph.json` but no
  `GRAPH_REPORT.md` is **Missing**.

## Excluded paths

| Path | Reason |
|---|---|
| `node_modules/`, `vendor/`, `.venv/`, `dist/`, `build/` | Vendored or generated — not projects |
| `<path>` | `<user-stated reason; out of bounds for every workspace feature>` |

## Detection evidence

How each project was identified — so a later reader can check the inventory rather than trust it.

| Project | Marker |
|---|---|
| `<name>` | `<dir>/pom.xml` |
| `<name>` | `<dir>/package.json` (`"name": "@acme/sdk"`) |
| `<name>` | `<dir>/composer.json` + `<dir>/*.php` plugin header |

## Unknowns

- `Unknown - requires confirmation` — ownership of `<project>`.
- `Unknown - requires confirmation` — whether `<project>` publishes `<contract>` or merely consumes it.
