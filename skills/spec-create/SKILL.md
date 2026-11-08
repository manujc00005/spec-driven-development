---
name: spec-create
description: Create a structured feature specification before implementation. Use this when the user wants to add, change, or refactor a feature. Not for strengthening an existing spec (use /spec-clarify) or changing one mid-implementation (use /spec-update).
---

## SDD Contract

```yaml
category: lifecycle
inputs: [feature-description]
outputs: [SPEC.md]
side_effects: writes-specs
writes_code: false
writes_specs: true
analysis_only: false
primary_agent: solution-architect
secondary_agents: []
profile_scope: all
provider_specific: false
```

You are working in Spec-Driven Development mode.

Your task is to create or update a feature specification.

## Status lifecycle

Specs follow this lifecycle:

```
Draft → Ready → In Progress → In Review → Done | Archived
```

- `Draft`: spec created, not yet plannable.
- `Ready`: plan and tasks exist, implementation can start.
- `In Progress`: at least one task has been implemented.
- `In Review`: all tasks complete and spec-review passed — QA and specialized reviews pending.
- `Done`: all reviews complete and spec-close run — ready for PR.
- `Archived`: spec abandoned or superseded.

This skill always sets status to **Draft**, and it is the only status it may write. Promoting a spec beyond `Draft` belongs to `/spec-plan` (→ `Ready`), `/spec-implement` (→ `In Progress`), `/spec-review` (→ `In Review`), and `/spec-close` (→ `Done`). See `sdd-guardrails` section 11.

## Core rules

- Do not implement production code.
- Do not modify files outside `specs/features/` unless explicitly requested.
- Determine and reserve the next folder number with the procedure below before creating (never from the local folder alone).
- Prefer existing project terminology and architecture.
- Ask for clarification only if the missing information blocks the spec.
- If something is uncertain but not blocking, write it as an assumption.
- Add unresolved doubts to `Open questions`.
- Read `specs/SERVICES.md` before finalizing the spec and stamp its declared services into the `Contracted services` section (conservative-default note if the file is absent).

## Folder naming

Create a new folder under:

`specs/features/`

Use this format:

`<number>-<short-kebab-case-feature-name>`

Example:

`001-user-login`

**IMPORTANT — determining and reserving the next number:**
Parallel sessions work in other worktrees and branches; a number taken there is invisible in
your local `specs/features/`. Taking `max(local) + 1` is how duplicates happen (e.g. two `088-*`
folders, a 116 renumbered to 118). Never rely on Glob for this either — it can silently return
nothing. Run, from inside the repository:

```bash
git fetch --quiet origin 2>/dev/null || true
claims="$(git rev-parse --git-common-dir)/spec-claims"; mkdir -p "$claims"
taken() {   # every number visible from this clone
  git ls-tree -d --name-only origin/HEAD:specs/features/ 2>/dev/null
  ls specs/features/ 2>/dev/null
  git for-each-ref --format='%(refname:lstrip=-1)' refs/heads refs/remotes
  git worktree list --porcelain | sed -n 's/^worktree //p' | while read -r w; do ls "$w/specs/features" 2>/dev/null; done
  ls "$claims"
}
max=$(taken | grep -oE '^[0-9]{3}' | sort -n | tail -1); n=$(( 10#${max:-0} + 1 ))
until mkdir "$claims/$(printf '%03d' "$n")" 2>/dev/null; do n=$((n + 1)); done   # atomic claim
NNN=$(printf '%03d' "$n"); printf '%s %s\n' "$(date -u +%FT%TZ)" "$(pwd)" > "$claims/$NNN/owner"
echo "$NNN"
```

```powershell
git fetch --quiet origin 2>$null
$claims = Join-Path (git rev-parse --git-common-dir) "spec-claims"; New-Item -ItemType Directory -Force $claims | Out-Null
$taken = @(git ls-tree -d --name-only origin/HEAD:specs/features/ 2>$null) + @(Get-ChildItem specs/features -Name -EA SilentlyContinue) +
         @(git for-each-ref --format='%(refname:lstrip=-1)' refs/heads refs/remotes) + @(Get-ChildItem $claims -Name) +
         @(git worktree list --porcelain | Select-String '^worktree (.+)$' | ForEach-Object { Get-ChildItem (Join-Path $_.Matches[0].Groups[1].Value specs/features) -Name -EA SilentlyContinue })
$n = 1 + [int](($taken | Select-String '^\d{3}' | ForEach-Object { [int]$_.Matches[0].Value } | Measure-Object -Maximum).Maximum)
while ($true) { $NNN = '{0:D3}' -f $n; try { New-Item -ItemType Directory (Join-Path $claims $NNN) -EA Stop | Out-Null; break } catch { $n++ } }
"$(Get-Date -AsUTC -Format s)Z $PWD" | Set-Content (Join-Path $claims "$NNN/owner"); $NNN
```

The claim is a directory in the clone's shared git dir, so every worktree of this clone sees it,
and `mkdir` succeeds for exactly one session. Use `$NNN` for the folder.

**Abandoned claims.** A claim whose number never became a folder or a branch anywhere above
(the session died) may be released after 7 days: `rmdir "$claims/<NNN>"` once `taken` shows no
`<NNN>-*` folder or branch and `owner` is older than that. Never release a claim younger than 7 days.

**Limits — say them when relevant.** Claims coordinate the worktrees of ONE clone on ONE machine.
Another machine or another clone only sees what is on `origin`: push the spec branch early
(`<type>/<NNN>-<slug>`) so its number becomes visible there. Until then, a collision across
machines is still possible.

## Required file

Create:

`SPEC.md`

## SPEC.md template

# Feature Spec: <feature-name>

## Status

Draft

## Problem

Describe the problem this feature solves.

## Goal

Describe the desired outcome.

## Non-goals

List what is explicitly out of scope.

## Users / Actors

List who interacts with this feature.

## Current behavior

Describe the current system behavior.

## Desired behavior

Describe the expected behavior after the change.

## Functional requirements

- FR-001:
- FR-002:
- FR-003:

## Non-functional requirements

- Performance:
- Security:
- Observability:
- Maintainability:

## API / Interface changes

Describe endpoints, DTOs, events, UI props, commands, screens, or public interfaces.

## Data model changes

Describe tables, entities, migrations, indexes, schemas, or persistence changes.

## Edge cases

- 
- 

## Acceptance criteria

- AC-001:
- AC-002:
- AC-003:

## Test scenarios

- Unit:
- Integration:
- E2E:
- Manual:

## Assumptions

- 

## Open questions

- 

## Contracted services

Read `specs/SERVICES.md`. If it exists, list the services marked contracted. If it does not exist, write: "Contracted services not declared → all billable add-ons treated as NOT contracted (conservative default). Run `/project-init` to declare them."

## Auto-clarify pass

After creating the spec, automatically apply a lightweight clarification pass:

1. Strengthen weak or untestable acceptance criteria.
2. Add missing edge cases that are obvious from the requirements.
3. Document implicit assumptions in the `Assumptions` section.
4. Identify blocking questions (things that change the design) and add to `Open questions`.

Do not ask the user before making improvements that do not require input.
If blocking questions exist, list them and wait for answers before recommending `/spec-plan`.

## Output

After creating and auto-clarifying the spec, summarize:

- Spec path
- Spec status: Draft
- Main requirements
- Improvements made (if any)
- Assumptions added (if any)
- Blocking questions (if any)

## Recommended next command

Logic:
- If blocking questions exist: answer them, then re-run `/spec-clarify <path>` for a deeper pass
- If no blocking questions: `/spec-plan <path>`

## Context economy

- Read only the files needed for the current task.
- Prefer the active feature folder over scanning the whole repository.
- Do not inspect unrelated specs.
- Do not inspect archived specs unless explicitly asked.
- Do not paste full file contents unless explicitly requested.
- Keep the response short and actionable.
- Always suggest the next command when useful.
