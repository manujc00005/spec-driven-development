# graphify — --watch, git commit hook, CLAUDE.md integration, agent-stats

> Reference for the `graphify` skill. Loaded on demand from
> [`../SKILL.md`](../SKILL.md); not read unless this operation is in play.

## For --watch

Start a background watcher that monitors a folder and auto-updates the graph when files change.

```bash
npx graphify watch INPUT_PATH --debounce 3
```

Replace INPUT_PATH with the folder to watch. Behavior depends on what changed:

- **Code files only (.py, .ts, .go, etc.):** re-runs AST extraction + rebuild + cluster immediately, no LLM needed. `graph.json` and `GRAPH_REPORT.md` are updated automatically.
- **Docs, papers, or images:** writes a `.graphify/needs_update` flag and prints a notification to run `/graphify --update` (LLM semantic re-extraction required).

Debounce (default 3s): waits until file activity stops before triggering, so a wave of parallel agent writes doesn't trigger a rebuild per file.

Press Ctrl+C to stop.

For agentic workflows: run `--watch` in a background terminal. Code changes from agent waves are picked up automatically between waves. If agents are also writing docs or notes, you'll need a manual `/graphify --update` after those waves.

---

## For git commit hook

Install a post-commit hook that auto-rebuilds the graph after every commit. No background process needed - triggers once per commit, works with any editor.

```bash
graphify hook install    # install
graphify hook uninstall  # remove
graphify hook status     # check
```

After every `git commit`, the hook detects which code files changed (via `git diff HEAD~1`), re-runs AST extraction on those files, and rebuilds `graph.json` and `GRAPH_REPORT.md`. Doc/image changes are ignored by the hook - run `/graphify --update` manually for those.

If a post-commit hook already exists, graphify appends to it rather than replacing it.

---

## For native CLAUDE.md integration

Run once per project to make graphify always-on in Claude Code sessions:

```bash
graphify claude install
```

This writes a `## graphify` section to the local `CLAUDE.md` that instructs Claude to check the graph before answering codebase questions and rebuild it after code changes. No manual `/graphify` needed in future sessions.

```bash
graphify claude uninstall  # remove the section
```

---

## For /graphify agent-stats

Attribute branches, commits, and work-packages to the agentic-CLI **session** that produced them, by indexing conversation transcripts already on disk (Claude `~/.claude/projects/`, Codex `~/.codex/sessions/`, agy/Antigravity `~/.gemini/`). Use it when git authorship is uniform/uninformative (e.g. every commit is the same human author with no agent trailer) and you need to know which agent did what. Attribution is ranked evidence (commit-sha printed in tool output > Codex thread-ids > h2a registry > worktree×branch×time-window > PR-merge), never the git author. Citation excerpts are anonymized before they leave the store.

```bash
graphify agent-stats                       # per-agent summary table (--format text|json|md)
graphify agent-stats report [--agent <id>] # per-agent detail with anonymized evidence citations
graphify agent-stats sync [--full]         # parse/refresh transcripts into .graphify/agents/facts.jsonl
graphify agent-stats sessions [--agent <id>] [--branch <b>] [--since <date>] [--json]
graphify agent-stats wp <trackItemId> [--no-pr] [--json]   # conductor view: sessions joined to a Track work-package
graphify agent-stats project-graph [--config <id.json>] [--out <graph.json>] [--studio]   # rename-aware project/conversation graph.json
```

The store (`.graphify/agents/facts.jsonl` + byte-offset cursors) is fully re-derivable; `sync` is incremental. The reports emit stable `graphify.agent-stats/v1` (summary/report) and `graphify.agent-stats.sessions/v1` (sessions) schemas. `wp` optionally uses `gh` to add PR-merge attribution (`--no-pr` to skip).

`project-graph` turns those session facts into a graphify `graph.json` the studio can render (nodes: project / repo / agent / session / branch / commit; edges: `belongs-to`, `rename-lineage`, `worked-in`, `conducted-by`, `touched-branch`, `produced`, `derived-from`). Its point is **rename reconciliation**: agent-stats keys repo identity off the cwd *path*, so a renamed/moved project fragments into several path identities; a `ProjectIdentity` (canonical id + ordered path/remote aliases) collapses them into ONE project node and chains the incarnations with `rename-lineage` edges. `--config` supplies the identity (defaults to the sentropic→graphify lineage); `--studio` also exports a renderable static studio. Stable schema `graphify.agent-stats.project-graph/v1`.

---

