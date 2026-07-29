---
name: graphify
description: "Use when the user asks any question about a codebase, project content, architecture, or file relationships, especially if .graphify/ exists. Builds a persistent knowledge graph from code, docs, papers or images, with god nodes, community detection, BFS/DFS query tools, a static Ontology Studio, JSON, and an audit report."
trigger: /graphify
---

## SDD Contract

```yaml
category: context-research
inputs: [any-input(code/docs/papers/images)]
outputs: [.graphify/knowledge-graph, GRAPHIFY.md, audit-report]
side_effects: writes-scratch
writes_code: false
writes_specs: false
analysis_only: true
primary_agent: codebase-researcher
secondary_agents: []
profile_scope: all
provider_specific: false
```

# /graphify

Turn any folder of files into a navigable knowledge graph with community detection, an honest audit trail, and three outputs: a static Ontology Studio, GraphRAG-ready JSON, and a plain-language GRAPH_REPORT.md.

## Usage

```
/graphify                                             # full pipeline on current directory → Obsidian vault
/graphify <path>                                      # full pipeline on specific path
/graphify https://github.com/<owner>/<repo>           # clone repo locally, then run the full pipeline
/graphify https://github.com/<owner>/<repo> --branch <branch>  # clone a specific branch before graphing
/graphify <path> --scope auto                         # safe default for code/review repos
/graphify <path> --scope tracked                      # include newly staged files too
/graphify <path> --all                                # full recursive folder walk for knowledge bases
/graphify <path> --directed                           # build directed graph (preserves source→target)
/graphify <path> --mode deep                          # thorough extraction, richer INFERRED edges
/graphify <path> --pdf-ocr auto                       # preflight PDFs; OCR scanned/low-text PDFs with mistral-ocr when needed
/graphify <path> --update                             # incremental - re-extract only new/changed files
/graphify <path> --cluster-only                       # rerun clustering on existing graph
graphify studio export .graphify/studio               # build the self-contained static Ontology Studio (open by serving it with any static file server)
/graphify <path> --svg                                # also export graph.svg (embeds in Notion, GitHub)
/graphify <path> --graphml                            # export graph.graphml (Gephi, yEd)
/graphify <path> --neo4j                              # generate .graphify/cypher.txt for Neo4j
/graphify <path> --neo4j-push bolt://localhost:7687   # push directly to Neo4j
/graphify <path> --mcp                                # start MCP stdio server for agent access
/graphify <path> --watch                              # watch folder, auto-rebuild on code changes (no LLM needed)
/graphify <path> --wiki                               # build agent-crawlable wiki (index.md + one article per community)
graphify wiki describe --graph .graphify/graph.json --mode assistant --targets all  # opt-in description sidecars
graphify export wiki --graph .graphify/graph.json --descriptions .graphify/wiki/descriptions.json
graphify export obsidian --graph .graphify/graph.json --descriptions .graphify/wiki/descriptions.json
/graphify <path> --obsidian --obsidian-dir ~/vaults/my-project  # write vault to custom path (e.g. existing vault)
/graphify add <url>                                   # fetch URL, save to ./raw, update graph
/graphify add <url> --author "Name"                   # tag who wrote it
/graphify add <url> --contributor "Name"              # tag who added it to the corpus
/graphify migrate-state --dry-run                    # plan graphify-out -> .graphify migration
/graphify query "<question>"                          # BFS traversal - broad context
/graphify query "<question>" --dfs                    # DFS - trace a specific path
/graphify query "<question>" --budget 1500            # cap answer at N tokens
/graphify summary --graph .graphify/graph.json        # compact first-hop orientation before deep traversal
/graphify minimal-context --task "review PR" --graph .graphify/graph.json  # first review call
/graphify review-delta --files src/auth.ts --graph .graphify/graph.json  # review impact for changed files
/graphify review-analysis --files src/auth.ts --graph .graphify/graph.json  # blast radius + review views
/graphify recommend-commits --files src/auth.ts,src/session.ts --graph .graphify/graph.json  # advisory commit grouping
/graphify scope inspect <path> --scope auto           # inspect the resolved file inventory first
/graphify path "AuthModule" "Database"                # shortest path between two concepts
/graphify explain "SwinTransformer"                   # plain-language explanation of a node
```

## Input scope policy

- Default to `--scope auto` for codebase and review work. In Git repos this means committed files plus `.graphify/memory/*`.
- Use `--scope tracked` when newly staged files must influence the graph before commit.
- Use `--all` only when the user clearly wants a knowledge-base style crawl of docs, notes, papers, screenshots, audio, or video.
- If the repo is dirty or the right scope is unclear, run `graphify scope inspect <path> --scope auto` first and summarize what will be included or excluded.

## What graphify is for

graphify is built around Andrej Karpathy's /raw folder workflow: drop anything into a folder - papers, tweets, screenshots, code, notes - and get a structured knowledge graph that shows you what you didn't know was connected.

Three things it does that Claude alone cannot:
1. **Persistent graph** - relationships are stored in `.graphify/graph.json` and survive across sessions. Ask questions weeks later without re-reading everything.
2. **Honest audit trail** - every edge is tagged EXTRACTED, INFERRED, or AMBIGUOUS. You know what was found vs invented.
3. **Cross-document surprise** - community detection finds connections between concepts in different files that you would never think to ask about directly.

Use it for:
- A codebase you're new to (understand architecture before touching anything)
- A reading list (papers + tweets + notes → one navigable graph)
- A research corpus (citation graph + concept graph in one)
- Your personal /raw folder (drop everything in, let it grow, query it)

## Operations reference

Each operation's full instructions live in a sibling file. **Read only the one you need** —
loading all of them defeats the token economy graphify exists for.

| Operation | Reference |
|---|---|
| Default `/graphify` run (full extraction) | [`references/full-extraction.md`](references/full-extraction.md) |
| `--update` (incremental re-extraction) | [`references/update.md`](references/update.md) |
| `--cluster-only` | [`references/cluster-only.md`](references/cluster-only.md) |
| `/graphify query` | [`references/query.md`](references/query.md) |
| `/graphify path` | [`references/path.md`](references/path.md) |
| `/graphify explain` | [`references/explain.md`](references/explain.md) |
| `/graphify add` | [`references/add.md`](references/add.md) |
| `--watch`, git commit hook, CLAUDE.md integration, `agent-stats` | [`references/integrations.md`](references/integrations.md) |

The rules below bind every operation, whichever reference you load.

## Honesty Rules

- Never invent an edge. If unsure, use AMBIGUOUS.
- Never skip the corpus check warning.
- Always show token cost in the report.
- Never hide cohesion scores behind symbols - show the raw number.
- The static Ontology Studio scales to large graphs (WebGL + pre-computed positions) - export it for graphs of any size; no node-count cap.

## Configured Project Profiles

The profile activation rule is explicit: use this branch only when `graphify.yaml`, `graphify.yml`, `.graphify/config.yaml`, or `.graphify/config.yml` exists, or the invocation includes `--config` or `--profile`. If none is active, fallback to the existing non-profile workflow.

Configured profile workflow:
1. Keep the TypeScript runtime proof in `.graphify/.graphify_runtime.json`; it must contain `"runtime": "typescript"`.
2. Run `project-config` to normalize config/profile artifacts.
3. Run the `configured-dataprep` runtime command to produce `.graphify/profile/profile-state.json`, semantic detection, and registry extraction.
4. Run the `profile-prompt` runtime command and use that prompt for assistant semantic extraction.
5. Run base extraction validation, then the `profile-validate-extraction` runtime command.
6. Merge `.graphify/profile/registry-extraction.json` with AST and semantic extraction, then finalize through the existing build/report/export runtime commands.
7. Run the `profile-report` runtime command to write `.graphify/profile/profile-report.md`.
8. If ontology discovery is requested, run `profile-discovery-sample`, use its prompt to produce `.graphify/ontology/discovery/proposals.json`, then run `profile-discovery-diff`; present the diff/report to the user and wait for approval before any apply step.
9. If `dataprep.image_analysis.enabled` is true, use `image-calibration-samples` and `image-calibration-replay` for calibration. The assistant may propose labels or rule changes, but TypeScript replay owns acceptance.
10. For batch image analysis, use `image-batch-export` and `image-batch-import`. A deep-pass export is allowed only when project-owned routing rules declare `decision: accept_matrix`; do not make production route decisions in the assistant.
11. If the profile declares `outputs.ontology.enabled: true`, run `ontology-output` to compile `.graphify/ontology/` after validated extraction exists.

## Ontology Lifecycle Patches

Use ontology lifecycle commands only when profile artifacts and `.graphify/ontology/` outputs already exist. Review decisions are patches against project-owned sources, not direct graph mutations. Assistants may propose patches, but must validate before dry-run and dry-run before write.

- Validate with `ontology-patch-validate --profile-state .graphify/profile/profile-state.json --patch patch.json`.
- Preview with `ontology-patch-apply --profile-state .graphify/profile/profile-state.json --patch patch.json --dry-run`.
- Write with `ontology-patch-apply --profile-state .graphify/profile/profile-state.json --patch patch.json --write` only after explicit user approval.
- Always warn if the Git worktree is dirty before proposing a write apply.
- Agents must not edit `.graphify/graph.json` or derived `.graphify/ontology/*.json` directly.
- The default MCP server stays read-only; mutation tools require explicit `graphify ontology serve --config graphify.yaml --write`.
- Use the Public Domain Mystery Sagas repo as an external UAT and UI-mock corpus only; do not add its real corpus as Graphify package fixtures.

Do not add embeddings, databases, a resident LLM backend, or a forked OCR/PDF pipeline for this branch.

## Lifecycle State

- Runtime state lives under `.graphify/`; do not create legacy visible state directories.
- If `.graphify/graph.json` is missing but legacy `graphify-out/graph.json` exists, run `graphify migrate-state --dry-run` first. If it reports tracked legacy artifacts, ask before using the recommended `git mv -f graphify-out .graphify` and commit message; do not auto-stage or auto-commit.
- For architecture or codebase questions, when `.graphify/graph.json` exists, first run `graphify query "<question>"` (or `graphify path "<A>" "<B>"` / `graphify explain "<concept>"`); these return a scoped subgraph, usually much smaller than `GRAPH_REPORT.md` or raw grep output.
- Use `.graphify/wiki/index.md` first when present; read `.graphify/GRAPH_REPORT.md` only for broad architecture review or when `query` / `path` / `explain` do not surface enough context.
- If `.graphify/needs_update` exists or `.graphify/branch.json` has `"stale": true`, tell the user the graph is stale and run the platform graphify command with `--update` before relying on semantic results.
- Before proposing or committing `.graphify` artifacts, run `graphify portable-check .graphify`; commit-safe graph artifacts must use repo-relative paths, and never commit `.graphify/branch.json`, `.graphify/worktree.json`, `.graphify/needs_update`, or `.graphify/cache/`. If a repo already tracks any of them, first add them to `.gitignore`, then propose `git rm --cached .graphify/branch.json .graphify/worktree.json .graphify/needs_update` and `git rm -r --cached .graphify/cache`; never mutate git state without asking.
- Git hooks may mark stale state after branch switches, merges, and rewrites. Never delete `.graphify/` automatically; use `graphify state prune` only as a non-destructive cleanup preview.

Commit recommendation workflow: `graphify recommend-commits` is advisory-only. It may suggest groups and commit messages, but the user remains the actor; do not auto-stage, auto-commit, or mutate branches.

CRG review workflow: `graphify minimal-context` is the first review call. Keep graph review context within `<=5 graph tool calls` and `<=800` graph-context tokens. If `.graphify/needs_update` exists or `.graphify/branch.json` has `stale=true`, warn and update before trusting semantic review output. Then follow only the compact route: `graphify detect-changes` for risk, `graphify affected-flows` for flow impact, and `graphify review-context` for snippets or radius detail. If `.graphify/flows.json` is missing and flows are needed, run `graphify flows build` first. Explicit `--files`, `--base`, `--head`, or `--staged` inputs override unrelated dirty worktree noise; mention dirty worktrees as a warning and never mutate git state.

Review analysis workflow: `graphify review-analysis` adds blast radius, bridge nodes, test-gap hints, impacted communities, and multimodal/doc safety. `graphify review-eval` is the deterministic evaluation harness for token savings, impacted-file recall, review summary precision, and multimodal regression safety.
