# Feature Spec: portable-personal-config

## Status

Merged

> `Merged` 2026-08-24 — 16/16 tasks, all gates green: 33 new tests, `install.test.sh` 29 passed
> (no regression on the no-payload path), `check-consistency.sh` exit 0, PowerShell parity verified
> by execution on this machine (`copied: 0 identical: 4` matching bash on the same payload).
>
> **Not `Live`:** nobody has yet run export on one machine and import on another. That is the
> company Windows box, and it is the only evidence that promotes this.

## Problem

Setting up a new machine restores the *framework* in one command and the *person* in none.
`install.sh` rebuilds skills, hooks, agents and templates from the repo — but everything that makes
the setup **yours** is left behind:

- `~/.claude-config/CLAUDE.md` — personal global instructions (54 lines).
- `~/.claude/settings.json` — hooks wiring, enabled plugins, marketplaces, theme.
- `~/.claude/agents/` — custom agents (112 K).
- `~/.claude/projects/*/memory/` — **63 files, 276 K, across 12 projects**. Accumulated
  understanding: what a project is, what was tried, what failed, why a decision was made.
- `~/.claude/plugins/installed_plugins.json` + `known_marketplaces.json` — the *list* of what to
  reinstall, not the 35 MB of plugin code.

The whole payload is **under 1 MB**, sitting inside 700 MB of disposable session transcripts,
telemetry and caches. Today it moves only by hand-written `tar` — which means in practice it does
not move, and the memory is the part that cannot be regenerated at all.

Two constraints make this harder than "copy some files", and both have already caused problems in
this workspace:

1. **This repository is public.** Personal instructions and memory reference client names,
   infrastructure and at least one VPS address. They cannot travel in it.
2. **The user works the same projects on two machines** (personal Mac, company Windows). A restore
   that overwrites is not a restore: it is data loss on whichever machine ran second.

## Goal

`install.sh` / `install.ps1` restore the personal layer alongside the framework, from a payload the
user controls, **adding only what is missing and never overwriting anything that exists**. Export
is one command; import needs no command at all.

## Non-goals

- **Shipping the payload inside this repository.** It is public. The repo ships the *tool*; the
  data lives elsewhere.
- **Exporting `settings.local.json`.** Machine-scoped by name and convention, and the current one
  holds at least one credential-shaped rule.
- **Syncing session transcripts, telemetry, caches, `file-history`, `shell-snapshots` or plugin
  code.** Disposable and regenerated; 700 MB of noise around 1 MB of signal.
- **Merging prose automatically.** Two versions of `CLAUDE.md` are reconciled by a human reading
  both, never by a script guessing.
- **Continuous two-way sync.** This is export/import at install time, not a daemon.
- **Secret management.** No credential is ever exported. Detection is best-effort and refuses on
  suspicion (FR-007).

## Users / Actors

- **The owner** — runs export on the old machine, install on the new one, and resolves any
  conflicts the import reports.
- **`install.sh` / `install.ps1`** — detect an available payload and import it after the framework
  is in place.
- **The payload repository** (`~/.claude-config`, private) — carries the personal layer between
  machines. Already a git repo; today it has no remote.

## Current behavior

- `install.sh --force --link-user-claude` installs skills/hooks/templates/agents into
  `~/.claude-config` and symlinks `~/.claude/{skills,hooks,CLAUDE.md}` to it.
- `~/.claude-config` is a git repository **with no remote** — it exists on exactly one disk.
- Nothing reads or writes `~/.claude/projects/*/memory/`.
- `~/.claude/settings.json` and `~/.claude/agents/` are never touched by the installer.
- A new machine gets a complete framework and an empty person.

## Desired behavior

**Export** (`scripts/export-personal-config.sh|ps1`) collects the payload into
`~/.claude-config/personal/`, from a manifest of what qualifies — never a wildcard sweep. The user
commits and pushes that private repo.

**Import** runs automatically at the end of `install.sh` when a payload is present, and reports
every decision it made. Per file, exactly three outcomes:

| Situation | Action |
|---|---|
| Target missing | **Copy it.** The only case that writes |
| Target exists, byte-identical | Skip silently |
| Target exists, differs | **Never touch it.** Write `<name>.incoming` beside it and report the conflict |

`MEMORY.md` is the one exception, and only in the additive direction: index lines present in the
payload and absent in the target are **appended**; nothing is reordered, rewritten or removed
(FR-005).

## Functional requirements

- **FR-001** — Export writes to `~/.claude-config/personal/` from an explicit manifest:
  `CLAUDE.md`, `settings.json`, `agents/`, `projects/*/memory/`, and the two plugin manifests.
  Anything not on the manifest is not exported, so a new file in `~/.claude` cannot leak by default.
- **FR-002** — Export **refuses** to write `settings.local.json` even if named explicitly.
- **FR-003** — Import runs at the end of `install.sh` when `~/.claude-config/personal/` exists.
  It requires no flag; `--no-personal` skips it.
- **FR-004** — Import never overwrites. Missing → copy. Identical → skip. Different → leave the
  target untouched, write `<name>.incoming`, count it as a conflict.
- **FR-005** — `MEMORY.md` merges additively: absent index lines are appended under a dated
  `<!-- imported YYYY-MM-DD -->` marker. Existing lines are never rewritten or removed. Memory
  files themselves follow FR-004 (a memory file is never overwritten, never deleted).
- **FR-006** — `settings.json` merges **top-level keys only**, and only keys absent in the target.
  A key present locally always wins. Arrays are not merged element-wise: an existing array is left
  alone.
- **FR-007** — Export scans every file for credential-shaped content (`token`, `secret`,
  `api[-_]?key`, `password`, `Bearer `, PEM headers). On a hit it **aborts** naming the file and
  the line number. `--allow-suspicious` proceeds after the user has looked.
- **FR-008** — Both commands print a summary: copied, skipped-identical, conflicts (with paths),
  and refused. Import exits 0 even with conflicts — a conflict is information, not a failure.
- **FR-009** — Import is idempotent: a second run with no changes copies nothing and reports
  everything as identical.
- **FR-010** — `install.ps1` reaches feature parity with the same manifest, semantics and summary.

## Non-functional requirements

- **Performance:** payload under 1 MB; import must not add perceptible time to install.
- **Security:** the payload never enters this public repository. Export refuses on credential
  suspicion. Imported files keep restrictive permissions (`0600` for `settings.json` and memory).
- **Observability:** every write and every conflict is named on stdout. No silent action.
- **Maintainability:** the manifest is one declarative list, shared by both platforms. Adding a
  category is editing that list, not the copy logic.

## API / Interface changes

- New: `scripts/export-personal-config.sh` and `.ps1`.
- New: `scripts/import-personal-config.sh` and `.ps1` (also callable standalone).
- `install.sh` / `install.ps1` gain `--no-personal` / `-NoPersonal`.
- New: `.claude-config/personal/MANIFEST.json` — what was exported, when, from which machine.
- **Installer flags are a contract** (spec 034): the new flag is additive and defaults to current
  behaviour when no payload exists.

## Data model changes

None. No database, no schema. `MANIFEST.json` is a flat inventory, not state to maintain.

## Edge cases

- `~/.claude-config/personal/` absent → import is a silent no-op. A fresh clone must install
  cleanly.
- `~/.claude/projects/<slug>/` does not exist on the new machine (project not cloned yet) → the
  directory is created and memory copied. Memory arriving before the project is correct.
- Project slugs differ between machines (different paths → different slug) → **cannot be resolved
  automatically**; report as conflict, never guess a mapping.
- `MEMORY.md` exists but its `.md` targets do not → append the index lines anyway; a link to a
  missing memory is a visible gap, silence is not.
- `settings.json` is invalid JSON on either side → refuse to merge that file, report it, continue
  with the rest.
- `agents/` holds a file with the same name and different content → FR-004 conflict.
- Payload from a newer framework version → import does not care; it carries no framework files.
- Symlink where a real file is expected → do not follow, do not overwrite; report.
- Export run twice → overwrites `~/.claude-config/personal/` wholesale. That directory is
  export output, not a merge target.

## Acceptance criteria

- **AC-001** — Export on a populated machine produces `personal/` containing exactly the manifest
  categories, and **no** `settings.local.json`. Verified by listing the output.
- **AC-002** — Export aborts with file and line number when a credential-shaped string is present,
  and proceeds with `--allow-suspicious`.
- **AC-003** — Import into an empty `~/.claude` copies everything and reports counts matching the
  payload.
- **AC-004** — Import into a populated machine where one file differs leaves the original
  **byte-identical**, creates `<name>.incoming`, and reports one conflict. Verified by checksum
  before and after.
- **AC-005** — `MEMORY.md` merge appends only absent index lines under the dated marker; existing
  lines are byte-identical afterwards.
- **AC-006** — `settings.json` merge adds only absent top-level keys; a key present on both keeps
  the local value.
- **AC-007** — Second import run reports zero copies and zero conflicts.
- **AC-008** — `install.sh` with no payload behaves exactly as today; `--no-personal` skips import
  even when a payload exists.
- **AC-009** — `bash scripts/check-consistency.sh` exits 0, and any new script is covered by a test
  under `scripts/*.test.sh`. *(Spec 037 shipped with this gate red because its criterion only
  checked that templates parsed — this one names the gate explicitly.)*
- **AC-010** — `install.ps1` produces the same summary counts as `install.sh` on the same payload.

## Test scenarios

- **Unit:** merge functions in isolation — missing / identical / different; `MEMORY.md` append with
  overlapping and disjoint lines; `settings.json` key merge; credential detector against known
  positives and negatives.
- **Integration:** `scripts/personal-config.test.sh` over a synthetic `HOME` — export, import into
  empty, import into populated-with-conflicts, second import (idempotence).
- **E2E:** export on this Mac, import into a scratch `HOME`, diff against the source.
- **Manual:** the real second machine (company Windows), which is also the AC-010 evidence.

## Assumptions

- The payload lives in `~/.claude-config`, which the owner gives a **private** remote. The
  mechanism only requires the directory to be present — how it travels (git, USB, `scp`) is the
  owner's choice.
- Session transcripts, telemetry and caches are disposable. Verified: 667 MB of `projects/` against
  276 K of memory inside it.
- `~/.claude/skills`, `hooks` and `CLAUDE.md` are symlinks into `~/.claude-config`, so restoring
  the central directory restores them. Verified on this machine.
- Memory files are Markdown with a `MEMORY.md` index — the format this framework's memory
  convention already writes.
- The company Windows machine is the second machine and therefore the parity test.

## Open questions

- **OQ-1 (non-blocking)** — should `export` optionally include `~/.claude/plans/`? Not on the
  manifest today; add only if it proves useful in practice.
- **OQ-2 (non-blocking)** — slug mismatch between machines is reported, not solved. If it turns out
  to be the common case rather than the exception, a mapping file becomes its own spec.
- **OQ-3 (non-blocking)** — whether `import` should offer `--adopt-incoming <file>` to promote a
  `.incoming` after review. Deliberately out of scope: reviewing a diff is a human act, and the
  first version should not automate the resolution it exists to surface.

## Contracted services

`specs/SERVICES.md` does not exist → all billable add-ons treated as **NOT contracted**
(conservative default). Run `/project-init` to declare them. No billable service is involved in
this feature.
