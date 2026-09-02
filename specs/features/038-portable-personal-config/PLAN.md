# Implementation Plan: portable-personal-config

## Summary

Two script pairs (`export-personal-config`, `import-personal-config`) plus a call site at the end
of both installers. The export collects a manifest-defined slice of `~/.claude` into
`~/.claude-config/personal/`; the import restores it **additively** — missing files are copied,
identical ones skipped, differing ones left untouched with a `.incoming` sibling and a reported
conflict.

No production code, no schema, no network. The hard part is not copying: it is the merge
semantics, and those live in three small pure functions that get unit-tested in isolation.

## Related spec

[`SPEC.md`](SPEC.md)

## Impacted areas

| Area | Change |
|---|---|
| `scripts/export-personal-config.sh` / `.ps1` | New |
| `scripts/import-personal-config.sh` / `.ps1` | New |
| `scripts/personal-config.test.sh` | New — sandbox suite |
| `install.sh` / `install.ps1` | Call site before `Done.`; `--no-personal` / `-NoPersonal` flag; help text |
| `.githooks/pre-push` | Add the new suite to the fast gate if it stays under ~2s |
| `README.md`, `docs/INSTALL.md` | Document export/import and the private-payload rule |
| `CHANGELOG.md` | Unreleased entry |

**Untouched:** `profiles.json` (no new skill/hook/template/agent, so no manifest counts change),
`skills/`, `agents/`, `hooks/`.

## Context budget

### Reading list

- `specs/features/038-portable-personal-config/*` — the active folder.
- `install.sh` — flag parsing block, and the tail from `write_install_manifest` to `Done.`
- `install.ps1` — the equivalent two regions, for parity.
- `hooks/lib/claude-json.sh` — the existing dependency-free JSON helper; reuse or extend, do not
  reinvent.
- `scripts/graphify.test.sh` — the sandbox test pattern this suite must follow.
- `docs/INSTALL.md` — the section that documents installer flags.

**Not read:** any other skill, spec or hook. Nothing in `~/.claude` is read during
implementation — the tests build a synthetic `HOME`.

### Model routing

- **Deep reasoning:** the three merge functions and the credential detector. Every branch is a
  data-loss or data-leak decision, and the failure mode is silent.
- **Mechanical:** flag plumbing, help text, docs, CHANGELOG, the PowerShell port once the bash
  version is settled and tested.

## Proposed approach

**1. Manifest first.** A single declarative list, mirrored in both languages, of what qualifies:
`CLAUDE.md`, `settings.json`, `agents/`, `projects/*/memory/`, the two plugin JSONs. Anything
absent from the list is never exported (FR-001) — a new file appearing in `~/.claude` cannot leak
by default.

**2. Export = collect + scan + refuse.** Copy the manifest slice into
`~/.claude-config/personal/`, writing `MANIFEST.json` with source machine, timestamp and file
inventory. Before writing anything, scan every candidate for credential-shaped content and
**abort with file and line** on a hit (FR-007). `settings.local.json` is refused even if named
(FR-002) — this restates a rule `install.sh` already holds constitutionally.

**3. Import = classify, then act.** For each payload file, compute one of three states and act:

```
target missing      → copy                        (the only write)
target identical    → skip
target differs      → write <name>.incoming, count conflict, DO NOT TOUCH target
```

Two exceptions, both narrow and both additive-only:

- `MEMORY.md` — index lines absent from the target are appended under a dated marker (FR-005).
- `settings.json` — top-level keys absent from the target are added; a key present locally always
  wins; arrays are never merged element-wise (FR-006).

**4. Wire the call site.** At the end of `install.sh`, before `Done.`: if
`$CENTRAL_DIR/personal/` exists and `--no-personal` was not passed, run the import and print its
summary. Absent payload → silent no-op, so a fresh clone installs exactly as today (FR-003,
AC-008).

**5. Port to PowerShell** only after the bash suite is green, so parity is measured against tested
behaviour rather than against intent.

## Alternatives considered

**Ship the payload in this repository.** Rejected: it is public, and the memory references client
names, infrastructure and a VPS address. This is the decision that shapes everything else — the
repo ships the tool, never the data (D001).

**Backup-and-overwrite, as `--force` already does for framework files.** Rejected for the personal
layer: framework files have an authoritative source in the repo, so overwriting is recoverable.
A `MEMORY.md` written on the other machine has no upstream — overwriting it destroys the only
copy (D002).

**Three-way merge of `CLAUDE.md`.** Rejected: reconciling personal instructions requires reading
both versions and deciding. A script guessing produces a document nobody wrote and everybody
trusts.

**A `sync` command with two-way reconciliation.** Rejected as scope: it needs conflict resolution,
ordering and a merge base. The problem posed is moving to a new machine, and export/import at
install time solves it without inventing a distributed-state problem.

**Symlinking `~/.claude/projects/*/memory` into the payload repo.** Rejected: it makes the memory
directory disappear if the repo is not cloned, and couples the working setup to a checkout being
present.

## Dependencies

- `python3` for JSON in bash — **already an install.sh dependency**, so this adds none.
- PowerShell 5.1+ `ConvertFrom-Json` / `ConvertTo-Json` for the Windows side.
- No network, no external service, no npm package.

## Risks

| Risk | Mitigation |
|---|---|
| **Silent data loss** — an overwrite nobody notices | FR-004 makes the no-touch path the default; AC-004 verifies by checksum before and after, not by "it didn't error" |
| **Credential leak into the payload repo** | FR-007 scans and aborts with file and line; `settings.local.json` refused unconditionally; the payload repo must be private (documented, not enforceable by script) |
| **Project slug mismatch between machines** | Reported as a conflict, never guessed. Named as a known limitation in `SPEC.md` OQ-2 |
| **PowerShell parity drifts** | AC-010 compares summary counts on the same payload; the port comes after the bash suite is green |
| **`MEMORY.md` append corrupts an index** | Append-only under a dated marker, existing lines byte-identical (AC-005); unit-tested with overlapping and disjoint inputs |
| **The new suite slows the pre-push gate** | Added only if it stays under ~2s; otherwise CI-only, as `check-consistency.test.sh` already is |

## Test strategy

- **Unit** — the three merge functions and the credential detector, called directly with crafted
  inputs. Missing / identical / different; `MEMORY.md` overlapping and disjoint; `settings.json`
  key collision; detector positives and negatives.
- **Integration** — `scripts/personal-config.test.sh` over a synthetic `HOME`: export → import into
  empty → import into populated-with-conflicts → second import (idempotence). Follows the sandbox
  pattern of `scripts/graphify.test.sh`.
- **E2E** — export on this machine, import into a scratch `HOME`, diff against source.
- **Manual** — the company Windows machine; this is also the AC-010 parity evidence.
- **Regression** — `bash scripts/install.test.sh` must stay green: the no-payload path must behave
  exactly as today.

## Rollback strategy

Both scripts are additive and standalone. Reverting means deleting the two script pairs and the
call site — nothing in the framework depends on them.

For an import already run: every write is either a new file or a `.incoming` sibling, both listed
in the summary. Nothing existing was modified except `MEMORY.md` appends, which are delimited by a
dated marker and removable by hand. `--no-personal` disables the behaviour without uninstalling.

## PLAN verification checklist

- [x] The plan covers all acceptance criteria.
- [x] The plan avoids behavior outside the spec.
- [x] The Context budget section is filled (reading list + model routing), not left as placeholder.
- [x] Risks are documented.
- [x] Test strategy is documented.
- [x] Rollback strategy is documented.
- [x] SPEC.md status has been updated to `Ready`.
