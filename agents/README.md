# Agents

Subagent definitions shipped by this repo for the **multi-model orchestrated SDD workflow**
(see `docs/SDD-ORCHESTRATION.md` and the `/sdd-orchestrate` skill).

| Agent | Model | Tools | Role |
|---|---|---|---|
| `deep-reasoner` | `opus` | Read, Grep, Glob (read-only) | Architecture, complex debugging, root-cause, security, concurrency, migrations, high-risk review. Analyzes; never edits. |
| `fast-worker` | `sonnet` | Read, Grep, Glob, Edit, Write, Bash | Implements approved, well-delimited tasks; runs verifications. Stops on undocumented architectural decisions. |

Model fields use **aliases** (`opus`, `sonnet`) so the agents track the account's current
model per tier instead of pinning a dated snapshot.

## How these are installed — copy, not link

Unlike `skills/` and `hooks/` (which are junctioned/symlinked from the central config),
agent files are **copied file-by-file, additively**:

- `install.ps1 -LinkUserClaude` / `install.sh --link-user-claude` → copies them into
  `~/.claude/agents/`.
- `link-project.ps1` / `link-project.sh` → copies them into `<project>/.claude/agents/`.

Reason: `~/.claude/agents` and project `.claude/agents` directories commonly contain
**user- or project-authored agents**. A junction would replace the whole directory and
hide them. Per-file copy adds only these agents and never touches anything else; a
same-name file that differs is skipped unless `-Force`/`--force` (which backs it up first).

Consequence: agent updates do **not** propagate automatically through the link like skills
do — re-run the installer (or link-project) after `git pull` to refresh them.

## Customizing per project

A project may freely edit its copied `.claude/agents/deep-reasoner.md` /
`fast-worker.md` (e.g., narrow `tools:`, add stack context). The installer will then
report the file as "differs" and skip it on future runs, preserving the customization
unless you explicitly pass `-Force`/`--force`.
