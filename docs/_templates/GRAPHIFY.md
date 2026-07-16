# Graphify — Optional Architecture Context Provider

> Graphify is an **optional external tool** for generating and analyzing project dependency graphs.
> The SDD framework works fully without it. This template guides projects that choose to use Graphify.

## What is Graphify?

Graphify generates a dependency graph of your codebase and produces a human-readable report:

- `.graphify/graph.json` — Complete dependency graph (nodes, edges, communities, metrics)
- `.graphify/GRAPH_REPORT.md` — Markdown summary of the graph

Graphify is useful for:
- Understanding module/service architecture before making changes
- Analyzing impact of changes (which modules affected?)
- Identifying critical modules (high connectivity, "god nodes")
- Debugging complex dependency issues
- Code review context generation

## Status: Optional, Non-Mandatory

- ✅ Install Graphify yourself (external tool, not shipped by SDD)
- ✅ Use Graphify output for architecture context
- ✅ SDD recognizes and uses Graphify if available
- ❌ SDD does NOT require Graphify
- ❌ SDD does NOT auto-install Graphify
- ❌ SDD does NOT fail if Graphify is absent

If Graphify is not installed, SDD continues to work normally with heuristic analysis.

## Installation

**One-step adoption (recommended):** from the SDD framework checkout, run

```bash
scripts/setup-graphify.sh --project-dir <your project>   # add --yes for non-interactive
# Windows: scripts/setup-graphify.ps1 -ProjectDir <your project> [-Yes]
```

The script installs `@sentropic/graphify` (after confirmation), runs the detect
and update commands below, gitignores `.graphify/`, and scaffolds this file plus
`docs/PROJECT_GRAPH.md` into the project. It is idempotent — safe to re-run.

**Manual alternative:**

```bash
npm install -g @sentropic/graphify
# or equivalent for your platform/package manager
```

Then, in your project root:

```bash
graphify detect . --scope committed
graphify update . --no-description --no-label
```

This generates `.graphify/graph.json` and `.graphify/GRAPH_REPORT.md`.

> **Scope values vary by version.** `--scope committed` worked historically, but
> 0.17.x documents `auto` / `tracked` / `all` (where `auto` = committed files +
> `.graphify/memory/*`). If `committed` is rejected, use `--scope auto` — the
> `setup-graphify` script already tries both automatically.

## Automatic freshness

The `graphify-stale-reminder` hook (wired on `SessionStart` by the SDD settings
templates) keeps the graph fresh: when `.graphify/GRAPH_REPORT.md` is missing or
more than 7 days older than the newest source file and the `graphify` CLI is on
PATH, it re-runs `graphify update . --no-description --no-label` in a detached
background process guarded by `.graphify/.update.lock`. It never blocks the
session. Set `SDD_GRAPHIFY_AUTO=0` to disable auto-refresh (reminder-only).

## Common Commands

### Generate / Update the Graph

```bash
# Full update with LLM descriptions (requires API key)
graphify update .

# Quick update (no descriptions)
graphify update . --no-description --no-label

# Force refresh
graphify update . --force
```

### Explore the Graph

```bash
# Show all nodes related to <node-name>
graphify tree <node-name>

# Limit depth
graphify tree <node-name> --depth 2

# Find shortest path between two nodes
graphify path <from-node> <to-node>

# Get context for a file or module
graphify review-context <file-or-module>

# Show all flows affected by a change
graphify affected-flows <file>

# Minimal context for a changeset
graphify minimal-context <directory>
```

## When to Use Graphify in SDD

### ✅ Recommended

- **Before `/spec-plan` on medium/large features** — Use `/graphify-context` (if available) to understand architectural impact before writing a plan
- **Before `/spec-analyze`** — Graphify can enrich the reading list and highlight boundary crossings
- **During `/code-review`** — Use `graphify review-context <files>` to provide architectural context to reviewers
- **When debugging** — `graphify path` and `graphify tree` help trace execution paths and dependencies

### ❌ Not Necessary

- Typo fixes or small isolated changes
- Documentation-only changes
- Changes that clearly don't cross architectural boundaries
- When you understand the impact without needing the graph

## When to Refresh the Graph

### Update the graph:
- After merging a major feature branch
- After refactoring > 5 files
- Before/after deleting files or renaming packages
- When architecture visibly changes

### Don't update:
- After every commit (too slow)
- After only test changes
- After typo fixes
- If graph is < 1 week old

## Shell Aliases (Optional)

Copy these into your shell profile (`.bashrc`, `.zshrc`, or PowerShell `$PROFILE`):

### PowerShell

```powershell
Set-Alias -Name gg -Value "graphify"
function gtree { graphify tree $args }
function gpath { graphify path $args[0] $args[1] }
function gcontext { graphify review-context $args }
function gflows { graphify affected-flows $args }
function gupdate { graphify update . --no-description --no-label }
```

### Bash / Zsh

```bash
alias gg="graphify"
alias gtree="graphify tree"
alias gpath="graphify path"
alias gcontext="graphify review-context"
alias gflows="graphify affected-flows"
alias gupdate="graphify update . --no-description --no-label"
```

## Using Graphify with Claude Code

### Before asking Claude for help:

1. Run `graphify update .` to refresh (if needed)
2. Run a command relevant to your question:
   ```bash
   graphify tree <component-you-are-touching>
   graphify affected-flows <file-you-changed>
   graphify review-context <directory>
   ```
3. Copy the output → paste into Claude Code
4. Ask: "Here's the graph. Where does this change impact?"

Claude can then see the dependency structure and provide better-scoped advice.

### Example:

```bash
# Terminal
graphify affected-flows lib/auth/authentication.ts

# Terminal output
# → [list of affected modules and flows]

# In Claude Code
"I need to add a feature to lib/auth/authentication.ts.
Graphify shows this module affects: [paste output]
Which of these need updates?"
```

Claude then understands the scope without needing to re-derive it.

## Using Graphify within SDD Workflow

### For `/spec-plan`

If you have a spec and want to plan the implementation:

```bash
graphify review-context <files-you-plan-to-modify>
```

Paste the output into `PLAN.md` under a "## Architecture Impact" section.
This shows reviewers which modules are involved and why the plan makes sense.

### For `/spec-analyze`

Before running `/spec-analyze`, optionally check:

```bash
graphify affected-flows <entry-point-file>
```

This can help identify if your plan is complete (did you account for all callers/consumers?).

### For `/context-manager`

The `/context-manager` skill automatically uses `.graphify/GRAPH_REPORT.md` if present.
It will narrow the reading list to the most impacted modules.
If Graphify is absent, it falls back to heuristic analysis (still works fine).

## Troubleshooting

### False coupling between routes with the same basename (known bug, 0.17.1)

**Symptom:** the report shows a coupling that does not exist in the code between
two files whose paths end in the same basename (e.g. `payments/checkout` and
`bonos/checkout` both mapped to a single `checkout_route_post` node).

**Cause:** Graphify 0.17.1 derives node IDs from the basename, colliding equal
basenames across directories. Re-check against the actual code (the graph is an
accelerator, never a source of truth) and verify whether versions newer than
0.17.1 fix the collision before trusting such edges.

### Graph is stale (older than code changes)

**Symptom:** Graphify output seems out of sync with recent code changes.

**Solution:**
```bash
graphify update . --no-description --no-label
# or full update if you have API keys:
graphify update .
```

### Graph is absent (.graphify/ not found)

**Symptom:** You want to use Graphify but it's not initialized.

**Solution:**
```bash
graphify detect . --scope committed
graphify update . --no-description --no-label
```

### Command not found: graphify

**Symptom:** `graphify` is not recognized.

**Solution:**
- Confirm installation: `npm list -g @sentropic/graphify`
- If missing, install: `npm install -g @sentropic/graphify`
- If installed, reload your shell: `source ~/.bashrc` (bash) or restart PowerShell

### Graph reports wrong dependencies

**Symptom:** Graphify shows modules connected that shouldn't be connected, or misses actual connections.

**Solution:**
- This is rare but can happen if Graphify's heuristic is confused
- Check the official Graphify docs or report to Graphify maintainers
- SDD skills will still work (they have graceful fallbacks)

### Want to reset the graph

**Solution:** Rename or back up the directory, then re-generate:

```bash
# Backup (safe)
mv .graphify .graphify.backup

# Regenerate
graphify detect . --scope committed
graphify update . --no-description --no-label

# If the new graph looks good, remove the backup
rm -rf .graphify.backup
```

## Further Reading

- **Graphify Official Docs:** https://github.com/sentropic/graphify (or official source)
- **SDD Onboarding:** See `docs/PROJECT_CONTEXT.md` and `docs/ARCHITECTURE.md` in your project
- **SDD Workflow:** See `docs/SDD-ORCHESTRATION.md` for where Graphify fits in the development process

---

**Key Takeaway:** Graphify is a productivity accelerator, not a requirement. Use it if it helps. Skip it if it doesn't.
The SDD framework works either way.
