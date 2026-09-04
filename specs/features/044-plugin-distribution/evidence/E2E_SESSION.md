# T014 — E2E in a disposable project (no .claude/hooks)

Date: 2026-09-04T19:49:55Z · 2.1.259 (Claude Code) · dir: /tmp/sdd-e2e-x5x1

```
$ claude plugin install sdd@spec-driven-development --scope project
Installing plugin "sdd@spec-driven-development"...✔ Successfully installed plugin: sdd@spec-driven-development (scope: project)
[exit 0]
```

```
$ ls -a /tmp/sdd-e2e-x5x1 ; ls -a /tmp/sdd-e2e-x5x1/.claude
.
..
.claude
.git
.
..
settings.json
(no .claude/hooks directory — hooks come from the plugin)
```

(First attempt used GNU `timeout`, absent on macOS — exit 127, not a plugin failure. Re-run below without it.)

```
$ claude -p 'Run /sdd and stop after listing what it would do. Do not create files.' --max-turns 3
Warning: no stdin data received in 3s, proceeding without it. If piping from a slow command, redirect stdin explicitly: < /dev/null to skip, or wait longer.
# SDD

Stopped at the bootstrap check. No files were created.

**What /sdd would do in this project**

1. **Bootstrap check** fails: there is no `specs/` directory, so the constitution file is missing. The skill stops here and recommends running `/project-init` first. It does not proceed to complexity detection in an uninitialized project.
2. **After initialization**, the skill would ask for a feature description, since none was given.
3. **Complexity detection** would classify the feature as Medium or Full based on whether it touches auth, user data, schema changes, external integrations, uploads, secrets, or significant ambiguity.
4. **Review detection** would list the specialized reviews likely needed, such as database, security, performance, API, backend, frontend, and any installed stack reviewers.
5. **Workflow chain** would then run in one response: spec-create with the auto-clarify pass, then spec-plan producing PLAN, TASKS and DECISIONS, then spec-analyze. It would stop only on blocking questions or a Partial/Not-ready analysis result, and would never write production code.

**Current project state**

- The repo contains only `.claude/settings.json`, a `.git` directory, and a `.graphify` directory.
- No commits exist yet, and no `specs/` or `docs/` structure is present.

**First command to run**

`/project-init`
[exit 0]
```

```
$ claude -p 'Run /spec-create for a throwaway feature named demo-echo and stop after naming the folder it would create. Do not write any file.' --max-turns 3
Warning: no stdin data received in 3s, proceeding without it. If piping from a slow command, redirect stdin explicitly: < /dev/null to skip, or wait longer.
The `specs/features/` directory does not exist, so the skill's rule applies: numbering starts at 001.

The folder `/spec-create` would create for demo-echo is:

```
specs/features/001-demo-echo/
```

It would hold a single `SPEC.md` with status Draft. Nothing was written. Stopping here as requested.
[exit 0]
```

```
$ ls -a /tmp/sdd-e2e-x5x1 /tmp/sdd-e2e-x5x1/.claude   # after the sessions
.
..
.claude
.git
.graphify
.
..
settings.json
```

## Hook attribution run (after `mkdir specs`)

`hooks/project-init-check.sh` exits silently when the project has no `specs/` directory (its first
guard), so the two sessions above could not show its message by design. With an empty `specs/` the
hook applies. Plain `claude -p` prints only the assistant text; the hook output is visible as
`hook_response` events in `--output-format stream-json --verbose`, and the loading in `--debug-file`.

```
$ mkdir specs && claude -p 'Reply with the single word ok.' --max-turns 1 --output-format stream-json --verbose --debug-file <log> < /dev/null
[exit 0]
SessionStart hook_response exit 0 stdout: {"systemMessage":"[SDD] specs/CONSTITUTION.md not found. Agents will work without project rules. Run /project-init to set up your project constitution."}
SessionStart hook_response exit 0 stdout: {}
SessionStart hook_response exit 0 stdout: 
SessionStart hook_response exit 0 stdout: 
SessionStart hook_response exit 0 stdout: 
```

The five `SessionStart` responses are: the plugin's `project-init-check` (the `[SDD]` message), one
user-level hook from `~/.claude/settings.json` (the `{}` reply), the plugin's
`graphify-stale-reminder` and two other plugins' hooks (empty). No user-level or project-level wiring
on this machine runs `project-init-check`, so the message is the plugin's.

Debug log lines proving the harness loaded the plugin's wiring and ran the hook — note the plugin
root is the checkout itself for a directory-sourced marketplace, not `~/.claude/plugins/cache/`:

```
2026-09-04T19:54:01.135Z [DEBUG] Read hooks.json for plugin sdd (enabled=true): /Users/manu/Proyectos/spec-driven-development/hooks/hooks.json
2026-09-04T19:54:01.169Z [DEBUG] Loading hooks from plugin: sdd
2026-09-04T19:54:01.336Z [DEBUG] "Hook SessionStart:startup (SessionStart) success:\n{\"systemMessage\":\"[SDD] specs/CONSTITUTION.md not found. Agents will work without project rules. Run /project-init to set up your project constitution.\"}"
2026-09-04T19:54:01.356Z [DEBUG] "Hook SessionStart:startup (SessionStart) success:\n{}"
```

`ls -a /tmp/sdd-e2e-x5x1/.claude` still shows only `settings.json`: no `.claude/hooks/` was ever
created in the project.
