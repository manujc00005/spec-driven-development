# Hooks

Nine hook families (18 scripts — all ship as a `.ps1`/`.sh` pair). Each hook is a small, single-purpose script invoked by Claude Code at a specific lifecycle point, configured in `.claude/settings.json` (see [`settings.template.json`](../settings.template.json) at the repo root).

None of these hooks call out to the network. All of them read local files or shell input and either allow, block, or annotate an action.

## Reference table

| Hook | Trigger (event / matcher) | Read-only or can modify files? | Opt-in or wired by default in the template? | Risk it prevents |
|---|---|---|---|---|
| `git-guardrails` | `PreToolUse` on `Bash` | Read-only — inspects the command string, never executes or edits anything itself | Wired by default | Destructive git operations run unattended: `push --force`, `reset --hard`, `clean -f`/`-fd`, `branch -D`, `checkout .`, `restore .` |
| `sdd-spec-guard` | `PreToolUse` on `Write`/`Edit` | Read-only — inspects the target file path and the feature specs, blocks the call, doesn't edit anything | **Opt-in** — ships as a script but is **not** referenced in `settings.template.json`. Add it yourself to a `PreToolUse` matcher on `Write\|Edit` if you want it enforced | Code getting written or edited with no `Ready`/`In Progress` spec behind it — the workflow being silently skipped under time pressure |
| `sdd-status-banner` | `Stop` (end of turn) | Read-only | Wired by default | Losing track of which features are `Draft`/`Ready`/`In Progress`/etc. across sessions |
| `project-init-check` | `SessionStart` | Read-only | Wired by default | Starting spec/review work in a project with no `specs/CONSTITUTION.md`, or one still full of `TODO:` placeholders |
| `ts-check` | `PostToolUse` on `Write`/`Edit` (`.ts`/`.tsx` only) | Runs `tsc --noEmit` — does not modify the file, only reports errors | Wired by default | Type errors surviving an edit unnoticed |
| `eslint-fix` | `PostToolUse` on `Write`/`Edit` (`.ts`/`.tsx`/`.js`/`.jsx`) | **Modifies the file** — runs `eslint --fix` in place | Wired by default | Lint violations and auto-fixable style drift accumulating silently |
| `prettier-format` | `PostToolUse` on `Write`/`Edit` (`.ts`/`.tsx`/`.css`/`.json`/`.js`/`.jsx`) | **Modifies the file** — runs `prettier --write` in place | Wired by default | Inconsistent formatting across AI-generated and human-written code |
| `maven-compile` | `PostToolUse` on `Write`/`Edit` (`.java`) | Read-only — runs `mvnw compile`, does not edit source | Wired by default | A Java change that doesn't compile going unnoticed until the next manual build |
| `graphify-stale-reminder` | `SessionStart` | Read-only — checks `GRAPH_REPORT.md` existence and mtime | **Opt-in** | Relying on a stale or missing architecture map for impact analysis. Warns if `GRAPH_REPORT.md` is absent or >7 days older than the newest source file. **Never blocks** — reminder only (exit 0) |

## How each hook decides whether to run

Every hook is defensive about scope — they exit immediately (exit code `0`, no effect) when they don't apply:

- The format/lint/type/build hooks (`ts-check`, `eslint-fix`, `prettier-format`, `maven-compile`) check the file extension **and** the presence of the relevant config file (`tsconfig.json`, `.eslintrc*`/`eslint.config*`, `.prettierrc*`/`prettier.config*`, `mvnw`) before doing anything. In a project that doesn't use TypeScript/ESLint/Prettier/Maven, these hooks are a no-op.
- `git-guardrails` only inspects `Bash` tool calls and only blocks a fixed list of destructive patterns — every other git command passes through untouched.
- `sdd-spec-guard` always allows edits under `specs/` and `.claude/`, and allows root-level `.md` files outside `specs/features/`. It only blocks edits to application code, and only when `specs/features/` exists but has no spec in `Ready` or `In Progress` status.
- `project-init-check` and `sdd-status-banner` both exit silently if the project has no `specs/` directory at all — they assume nothing about non-SDD projects.
- `graphify-stale-reminder` exits silently (exit 0, no output) when `GRAPH_REPORT.md` exists and is fresh. If it doesn't exist, it prints a reminder suggesting the user run Graphify. If it exists but is stale (>7 days older than the newest source file), it prints a staleness warning. It never blocks.

## How to activate them

1. Copy the hook scripts you want into your project (or reference this repo's `hooks/` directory directly if you keep it checked out alongside your projects).
2. Wire the ones you want in your project's `.claude/settings.json` — start from [`settings.template.json`](../settings.template.json) at the repo root and adjust paths.
3. On Windows, hooks run through `powershell -NoProfile -File <path-to-.ps1>`. On macOS/Linux, run the `.sh` counterpart directly (make sure it's executable: `chmod +x hooks/*.sh`).
4. To enable `sdd-spec-guard` (opt-in), add a `PreToolUse` entry matching `Write|Edit` that calls it. It is not included in `settings.template.json` by default — add it yourself:

   ```json
   {
     "matcher": "Write|Edit",
     "hooks": [
       {
         "type": "command",
         "command": "powershell -NoProfile -File ${CLAUDE_PROJECT_DIR}/hooks/sdd-spec-guard.ps1",
         "timeout": 5,
         "statusMessage": "Spec guard check..."
       }
     ]
   }
   ```

   On macOS/Linux, replace the `command` with `bash ${CLAUDE_PROJECT_DIR}/hooks/sdd-spec-guard.sh`.

## Cross-platform coverage

All 9 hook families ship as both `.ps1` (Windows/PowerShell) and `.sh` (macOS/Linux/bash) variants.

## Cross-platform note on `settings.template.json`

The root [`settings.template.json`](../settings.template.json) is written for **Windows + PowerShell** (`powershell -NoProfile -File ...`), matching the author's original setup. On macOS/Linux:

- Replace each `powershell -NoProfile -File ${CLAUDE_PROJECT_DIR}/hooks/<name>.ps1` command with `bash ${CLAUDE_PROJECT_DIR}/hooks/<name>.sh`.
- Make the shell scripts executable once: `chmod +x hooks/*.sh`.
- `jq` must be installed — the `.sh` hooks use it to parse the tool-call JSON passed on stdin.

`${CLAUDE_PROJECT_DIR}` is used throughout so the template works from any project without hardcoding an absolute path. Confirm this variable is supported by the Claude Code version you're running before relying on it — if it isn't, replace it with a literal relative or absolute path for your setup.

