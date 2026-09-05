# Feature Spec: install-manifest-coherence

## Status

Done

## Problem

`<central-dir>/.sdd-install.json` is the framework's only record of what an adopter has
installed. `scripts/update.sh` trusts it completely — it replays exactly the profile list it
finds there ([update.sh:163-168](../../../scripts/update.sh:163)). That trust is misplaced in
three independent ways, all of the same shape: **the manifest asserts a state the disk does not
hold, and nothing detects the gap.**

### Defect 1 — one commit stamp for a set of profiles that were installed at different commits

`write_install_manifest` ([install.sh:684-733](../../../install.sh:684)) unions the recorded
profiles with this run's active ones:

```
merged = list(dict.fromkeys(existing_profiles + profiles))   # install.sh:711
```

The union is deliberate and documented — it is what makes `--profile x` additive across runs.
But the manifest then stores a **single top-level `installedCommit`/`installedVersion` for the
whole merged set**, while the run only copied files for the **active** profiles. Every recorded
profile that was not active in that run keeps its old files and inherits a commit stamp it never
reached.

Observed on 2026-08-21, and reproducible from git history on both sides:

- `./install.sh --force --link-user-claude` ran at 17:08:22 +0200 with no `--profile`, so the
  active set was `core` + `java-spring-backend` (the `defaults.profile`).
- The manifest recorded **all 8 profiles** at `e28501d`
  (`"installedVersion": "v0.5.0-58-ge28501d"`), including the 6 that were not refreshed.
- `skills/python-reviewer/SKILL.md` — owned by the inactive `python-sql-data` profile — was
  still at its pre-`1f18894` content, missing 45 lines (the shell-embedded mode and
  formatted-text control-flow sections added on 2026-08-18).
- Nothing in the install output, the manifest, or a subsequent `update.sh` mentioned it. It was
  caught only by a hand-run `diff -rq skills ~/.claude-config/skills`, and corrected by a manual
  full-profile re-install (`~/.claude-config` commit `b7b3515`, +46/-1 across 2 files).

The failure is silent and self-concealing: `update.sh` reads `installedCommit`, computes the
delta from that commit, and reports "you are up to date" for profiles whose files are older than
the commit it just read.

### Defect 2 — a profile can never be removed

The union at `install.sh:711` is **one-way**. There is no `--remove-profile`, no prune path, and
no way to edit the recorded set other than hand-editing framework-owned JSON. Verified absent:
`grep -rn 'remove-profile\|RemoveProfile\|prune' install.sh install.ps1 scripts/update.sh
scripts/update.ps1` returns nothing.

Because `update.sh` re-installs whatever the manifest records, **a profile adopted once is
permanent** — every future update re-delivers it. This is the mechanism behind the recurring
"`install.sh` restores the 7 Java/messaging reviewers I deliberately pruned" complaint: manual
deletion from the central dir is not a supported operation, it is a change the next update
silently reverts.

### Defect 3 — `agents/README.md` and `hooks/README.md` are write-once, so `--force` never refreshes them

Found while gathering evidence for defect 1, and the same coherence failure in a different place:

```sh
if [ ! -e "$dest" ]; then                      # install.sh:500 and install.sh:566
  ... cp "$REPO_ROOT/agents/README.md" "$dest"; log "agents/README.md  (new)"
fi
```

Both READMEs are copied **only when absent**. `--force` does not reach them, no backup is taken,
and no drift is reported. Confirmed live: `agents/README.md` in the central dir is still the
pre-lifecycle-agents version (it describes only the orchestrated workflow and lacks the entire
"Lifecycle agents" section), despite the manifest claiming `e28501d`. `install.ps1:475` and
`install.ps1:559` carry the identical guard.

These are shipped documentation files that `installedCommit` implicitly vouches for. They are
frozen at whatever commit first created them.

## Goal

The manifest tells the truth about the disk, and the set of installed profiles is editable in
both directions.

Concretely: every recorded profile carries the commit its files were actually installed at; a run
that leaves recorded profiles untouched says so, by name, with the command to fix it; and an
adopter can remove a profile as explicitly and as safely as they added one.

## Non-goals

- **No automatic refresh of inactive profiles.** A run that names `--profile java-spring-backend`
  must not silently start installing `python-sql-data` files. Reporting the staleness is in
  scope; deciding for the adopter is not — that is the same reasoning spec 030 applied to
  newly-added profiles.
- **No automatic profile removal**, and no inference of "you probably don't want this anymore"
  from usage. Removal is always explicit and named.
- **No change to which skills, agents, or hooks any profile ships**, and no change to
  `profiles.json` beyond what a requirement below genuinely needs.
- **No new profile.**
- **No re-install requirement for existing adopters.** A `schemaVersion: 1` manifest must keep
  working (see FR-003); nobody is forced to reinstall to get the fix.
- **No protection for hand-edits made directly inside the central dir.** Out of scope, but see
  Open questions — it is a real adjacent hazard this feature makes *more* likely to bite, and
  FR-009 exists because of it.
- **No Codex adapter counterpart.** `adapters/codex/install-codex.sh` has **no profile concept
  at all** (verified: zero occurrences of `profile`) and writes no manifest, so there is nothing
  to mirror. Recorded as an honest gap, same treatment as spec 030 and spec 029 D008.
- **Not spec 030's requirement.** Spec 030 FR asks `update.sh` to report profiles present in
  `profiles.json` but *absent* from the manifest (profiles you have never installed). This spec
  covers profiles that *are* in the manifest but stale, and removal. Adjacent, disjoint; see
  Assumptions for the ordering constraint.

## Users / Actors

- **Adopter running `install.sh` / `install.ps1`** with a subset of their recorded profiles.
- **Adopter running `scripts/update.sh` / `update.ps1`**, whose delta report is only as honest as
  the manifest.
- **Adopter who wants a profile gone** — the pruned-reviewers case.
- **`scripts/install.test.sh` and `scripts/update.test.sh`**, which must gain the coverage this
  area currently lacks: `install.test.sh` contains **zero** manifest assertions today.

## Current behavior

- The manifest is a flat record: `schemaVersion: 1`, one `installedVersion`, one
  `installedCommit`, one `installedAt`, a flat `profiles` string array, `linkUserClaude`,
  `sourceClone`.
- `installedAt` is preserved when re-installing the same commit, so a no-op update leaves the
  file byte-identical (spec 015 AC-003). That idempotence property must survive this change.
- A corrupt or absent manifest is discarded silently and rebuilt — framework-owned state, never
  adopter content. That treatment must survive too.
- Profiles accumulate; nothing removes them.
- `update.sh` logs `Recorded install: version <v>, profiles: <list>` and re-installs that list.
- `agents/README.md` and `hooks/README.md` are created once and never updated.
- `install.ps1:702-704` and `update.ps1:142-145` mirror the Bash behavior exactly, including both
  defects and the write-once README guard.

## Desired behavior

- The manifest records **per-profile** install state. Reading it answers "at what commit was
  `python-sql-data` last written?" without guessing.
- At the end of a successful run, `install.sh` names every recorded profile it did **not**
  refresh, shows the commit each is stuck at, and prints the exact command that refreshes them.
  A run whose active set covers every recorded profile prints nothing extra.
- `update.sh` uses the per-profile state, so its "what's new since your version" report is
  computed from the oldest recorded profile rather than the newest, and cannot claim freshness it
  has not verified.
- `install.sh --remove-profile <name>` drops the profile from the manifest and deletes the files
  that only it owned, after backing them up. `update.sh` then stops re-delivering them.
- `core` cannot be removed.
- `agents/README.md` and `hooks/README.md` are refreshed like every other shipped file, so
  `installedCommit` is honest about them.
- A `schemaVersion: 1` manifest is migrated in place on the next run, with no adopter action.

## Functional requirements

### Per-profile freshness (defect 1)

- FR-001: The manifest gains a per-profile record keyed by profile name, each carrying at minimum
  the `commit`, `version`, and `installedAt` at which that profile's files were last written.
  `schemaVersion` bumps to `2`.
- FR-002: A run updates the per-profile record **only for the profiles active in that run**. The
  merged `profiles` list keeps accumulating exactly as today — FR-001 changes what is recorded
  about each entry, not which entries exist.
- FR-003: Readers (`install.sh`, `install.ps1`, `update.sh`, `update.ps1`) accept
  `schemaVersion: 1` and migrate it by attributing the single top-level `installedCommit` to every
  recorded profile. This is knowingly optimistic — it is the assertion the old format already
  made — and the first post-migration run corrects the active profiles. The migration must not
  require a re-install and must not fail on a manifest missing the new keys.
- FR-004: After a successful non-dry-run install, `install.sh` warns when the merged profile set
  is larger than the active set, listing each unrefreshed profile with its recorded commit and
  the exact refresh command. The warning is informational — it never changes the exit code.
- FR-005: Top-level `installedVersion`/`installedCommit` are retained for backward compatibility
  and mean "the newest commit any profile was installed at". `update.sh` must compute its delta
  from the **oldest** per-profile commit, not this value.
- FR-006: The spec-015 idempotence property holds: re-running the same commit with the same
  active profiles leaves the manifest byte-identical, including per-profile `installedAt`.

### Profile removal (defect 2)

- FR-007: `install.sh --remove-profile <name>` (and `install.ps1 -RemoveProfile`) removes `<name>`
  from the manifest's profile list and its per-profile record. Repeatable and combinable.
- FR-008: Removal deletes only items **exclusively owned** by that profile — an item also shipped
  by any still-recorded profile, or by `core`, is retained. Ownership is computed from
  `profiles.json`, never from the filesystem.
- FR-009: Every file removal backs the file up to `<central-dir>/_install-backups/<timestamp>/`
  first, reusing the existing backup mechanism. Removal must never be the one destructive path
  that skips it.
- FR-010: `core` is refusable — `--remove-profile core` exits non-zero with an explanatory
  message and changes nothing.
- FR-011: Removing a profile that is not recorded is a no-op with a clear message, not an error.
- FR-012: `--remove-profile` honors `--dry-run`, reporting every file it would delete and every
  file it retains because another profile still owns it.
- FR-013: `--remove-profile` and `--profile` naming the same profile in one invocation is a usage
  error, rejected before any file is touched.
- FR-014: `update.sh` / `update.ps1` replay the pruned list — a consequence of FR-007 requiring no
  change to their replay logic, to be asserted by test rather than assumed.

### Shipped-README freshness (defect 3)

- FR-015: `agents/README.md` and `hooks/README.md` are copied through the same
  `copy_file_safely` path as every other shipped file — refreshed under `--force`, backed up
  before overwrite, and reported as `(updated)` rather than only `(new)`. The `[ ! -e "$dest" ]`
  guards at `install.sh:500`, `install.sh:566`, `install.ps1:475`, and `install.ps1:559` are
  removed.

### Parity

- FR-016: `install.ps1` and `scripts/update.ps1` implement FR-001..FR-015 with identical
  semantics, messages, and exit codes.
- FR-017: The Codex adapter is explicitly out of scope and the gap is recorded in the spec's
  Assumptions and in `DECISIONS.md` at plan time — not left as an unstated omission.

## Non-functional requirements

- **Performance**: negligible. The manifest is a small JSON file read and written once per run;
  removal touches only the files it deletes.
- **Security**: `--remove-profile` deletes files. It must never accept a path-like or traversing
  profile name, must resolve every deletion inside `<central-dir>`, and must refuse to delete
  anything it did not compute from `profiles.json`. A profile name that does not appear in
  `profiles.json` is rejected before any deletion.
- **Observability**: the unrefreshed-profile warning (FR-004) and the dry-run removal report
  (FR-012) are the two signals this feature exists to produce; both name profiles and commits
  explicitly rather than emitting counts. The `~/.claude-config` git repo (first commit
  `081455a`) is the reference way to observe what any run actually changed.
- **Maintainability**: the manifest read/write logic is duplicated across four scripts in two
  languages. This change must not deepen that duplication — the schema and its migration rule are
  stated once in the spec and mirrored, and every new behavior is covered by
  `scripts/install.test.sh` / `scripts/update.test.sh` so the Bash side is defended in CI.

## API / Interface changes

**New CLI flags** (`install.sh` / `install.ps1`):

| Flag | Meaning |
|---|---|
| `--remove-profile <name>` / `-RemoveProfile <name>` | Drop a profile from the manifest and delete its exclusively-owned files (backed up first). Repeatable. Refuses `core`. |

**Changed output**: `install.sh` gains an end-of-run warning block when recorded profiles were not
active; `agents/README.md` and `hooks/README.md` may now log `(updated)`.

**No changes** to `update.sh` / `update.ps1` CLI surface.

## Data model changes

`.sdd-install.json` moves to `schemaVersion: 2`. Illustrative shape — the plan owns the final
key names:

```json
{
  "schemaVersion": 2,
  "installedVersion": "v0.5.0-58-ge28501d",
  "installedCommit": "e28501d…",
  "installedAt": "2026-08-21T15:08:22+00:00",
  "profiles": ["core", "java-spring-backend", "python-sql-data"],
  "profileState": {
    "core":                { "commit": "e28501d…", "version": "v0.5.0-58-ge28501d", "installedAt": "2026-08-21T15:08:22+00:00" },
    "java-spring-backend": { "commit": "e28501d…", "version": "v0.5.0-58-ge28501d", "installedAt": "2026-08-21T15:08:22+00:00" },
    "python-sql-data":     { "commit": "1f18894…", "version": "v0.5.0-41-g1f18894", "installedAt": "2026-08-18T06:11:44+00:00" }
  },
  "linkUserClaude": true,
  "sourceClone": "~/Proyectos/spec-driven-development"
}
```

`profiles` is retained as the ordered list of record (it is what `update.sh` replays);
`profileState` is keyed by the same names. The two must not be allowed to disagree — a name in
one and not the other is a corrupt manifest, handled by the existing discard-and-rebuild rule.

## Edge cases

- **`schemaVersion: 1` manifest** → migrated per FR-003, no adopter action, no re-install.
- **`schemaVersion` from the future (3+)** → treat as unreadable: fall back to the existing
  unknown-version mode and rebuild, rather than misreading keys.
- **`profiles` and `profileState` disagree** → corrupt; discard and rebuild (existing rule).
- **Manifest absent or corrupt** → unchanged behavior: unknown-version mode, rebuilt by this run.
- **Removing the only non-core profile** → leaves `["core"]`; `update.sh` then re-installs with
  the installer's default profile, which would silently re-add `java-spring-backend`. The plan
  must decide whether the pruned list is authoritative over `defaults.profile` — this is the
  removal path's real failure mode, not the file deletion.
- **Removing a profile whose files were never installed** (recorded but stale-empty) → no-op per
  file, still removed from the manifest.
- **Removal plus install in one run** → FR-013 rejects the same name in both; different names in
  one run must apply removal before install so ownership is computed against the final set. "Final
  set" includes profiles **arriving in this run**, not merely those already recorded: an item both
  the departing and the incoming profile ship must be kept, never deleted and re-copied. (Caught in
  `/spec-review`; regression-tested in both suites.)
- **A shipped item is missing from the repo** while computing exclusive ownership → the existing
  `MISSING_SHIPPED` error path already fails the run; removal must not bypass it.
- **`--dry-run` with `--remove-profile`** → nothing deleted, nothing written to the manifest.
- **Adopter hand-edited a file that removal would delete** → backed up per FR-009; the backup is
  the only recovery path and the message must say where it went.
- **`--force` now overwrites a hand-edited `agents/README.md`** (FR-015) → backed up like any
  other overwrite, which is precisely the behavior the write-once guard was avoiding and the
  reason the file went stale.

## Acceptance criteria

- AC-001: Given a manifest recording 8 profiles at commit A, when `install.sh --force` runs with
  an active set of `core` + `java-spring-backend` at commit B, then `profileState` shows B for
  exactly those two and A for the other six, and the run's output names all six as unrefreshed
  with the command to refresh them. Exit code is unchanged (0).
- AC-002: Given the same run, when `update.sh` next computes its delta, then the delta is computed
  from commit A (the oldest per-profile commit), not commit B.
- AC-003: Given a `schemaVersion: 1` manifest, when any of the four scripts reads it, then it is
  migrated to `schemaVersion: 2` with every recorded profile attributed the old top-level commit,
  no error is raised, and no re-install is required.
- AC-004: Given the same commit and the same active profiles, when `install.sh` runs twice, then
  the manifest is byte-identical after both runs (spec 015 AC-003 preserved under the new schema).
- AC-005: Given `python-sql-data` is recorded, when `install.sh --remove-profile python-sql-data`
  runs, then it is absent from both `profiles` and `profileState`, every file it exclusively owned
  is gone from the central dir, a copy of each is present under
  `_install-backups/<timestamp>/`, and no file shared with a still-recorded profile was deleted.
- AC-006: Given AC-005 has run, when `update.sh` runs, then `python-sql-data` is not re-installed
  and its files stay absent.
- AC-007: `install.sh --remove-profile core` exits non-zero, prints an explanatory message, and
  leaves the manifest and central dir unchanged.
- AC-008: `install.sh --dry-run --remove-profile <name>` writes nothing and deletes nothing, and
  its report lists both the files it would delete and the files it retains due to shared
  ownership.
- AC-009: `install.sh --profile x --remove-profile x` exits non-zero before touching any file.
- AC-010: `install.sh --remove-profile ../../etc` (and any name absent from `profiles.json`) is
  rejected before any deletion.
- AC-011: Given a central dir whose `agents/README.md` differs from the repo's, when
  `install.sh --force` runs, then the central copy matches the repo byte-for-byte and the previous
  content is in `_install-backups/`. Same for `hooks/README.md`.
- AC-012: After a full-profile `install.sh --force`, `diff -rq agents ~/.claude-config/agents` and
  `diff -rq hooks ~/.claude-config/hooks` report no differences attributable to shipped files.
- AC-013: `install.ps1` and `update.ps1` satisfy AC-001..AC-012 with identical messages and exit
  codes, proven by `scripts/install.test.ps1` and `scripts/update.test.ps1` running on the
  `windows-latest` CI runner (D005) — not by a manual spot-check.
- AC-014: `scripts/check-consistency.sh` stays green, and `scripts/install.test.sh` /
  `scripts/update.test.sh` cover AC-001..AC-012 and run in CI.

## Test scenarios

- **Unit**: n/a (shell + PowerShell) — covered by the harnesses below.
- **Integration**: `scripts/install.test.sh` gains its first manifest coverage — it currently
  contains zero manifest assertions. Temp central dir + temp clone with two commits; assert
  per-profile stamping (AC-001), v1 migration (AC-003), byte-identical idempotence (AC-004), the
  full removal matrix (AC-005, AC-007..AC-010), and README refresh (AC-011).
  `scripts/update.test.sh` extends its existing AC-007 manifest test to cover oldest-commit delta
  (AC-002) and post-removal replay (AC-006).
- **E2E**: on the maintainer's real central dir, using the `~/.claude-config` git repo as the
  observation mechanism — run `install.sh --force` with a partial profile set, confirm
  `git -C ~/.claude-config diff` shows changes only for active profiles and that the warning names
  the rest; then a full refresh and confirm the tree goes clean.
- **Manual**: Windows spot-check of `install.ps1 -RemoveProfile` and the migration path (AC-013).
  This is the same class of task that has left specs 015 and 016 open — see Open questions.

## Assumptions

- The central dir is framework-owned state. Deleting files there on an explicit
  `--remove-profile` is legitimate provided FR-009's backup holds.
- `profiles.json` is the sole authority for which items a profile owns; exclusive ownership is
  computed from it, never inferred from the filesystem.
- The optimistic v1 migration (FR-003) is acceptable because it preserves exactly the claim the v1
  format already made — it makes no new assertion, it just stops making a *single* one for a set.
- Spec 030 is still `Draft` (SPEC.md only, no PLAN). This spec does not depend on it and does not
  block it, but both touch `update.sh`'s reporting and `install.sh`'s profile handling. Whichever
  implements second reconciles; recorded so the second one does not silently overwrite the first.
- Spec 015 owns the manifest contract; this spec amends it rather than replacing it, and spec
  015's AC-003 idempotence is carried forward as FR-006.
- The Codex adapter has no profile or manifest concept, so "parity" here means Bash + PowerShell
  only.

## Open questions

Three of the four below were settled during `/spec-plan`. The fourth is out of scope for this
feature, remains open at close, and is carried forward as a deferred item.

- ~~**BLOCKING** — does a pruned profile list override `defaults.profile`?~~ **Resolved by
  [D001](./DECISIONS.md)** (2026-08-21): the manifest is authoritative. `update.sh` replays the
  recorded list verbatim *including* `core`, so `defaults.profile` applies only to a direct
  `install.sh` invocation with no `--profile`. This needs no new flag — `--profile core` already
  resolves correctly — and leaves behavior unchanged for every existing adopter. Asserted by
  AC-006.
- ~~Non-blocking: should `update.sh` refresh stale recorded profiles automatically?~~ **Resolved
  by [D007](./DECISIONS.md)**: report only, consistent with spec 030's stance on new profiles. A
  future `--refresh-all` would be additive and would supersede D007 without rework.
- **DEFERRED — local hand-edits in the central dir are silently clobbered by the next `--force`.**
  Confirmed live: `~/.claude-config/skills/scope-keeper/SKILL.md` carries a "Dead code you created
  is yours" bullet that exists on **no branch of this repo**, and the next full-force run will
  overwrite it with no warning (backups are taken, but nothing tells the adopter a local change was
  lost). Deliberately out of scope here and **still open at close** — FR-015 widened its blast
  radius from adopter-edited skills to the two shipped READMEs. Needs its own spec; the immediate
  mitigation is to port that bullet into `skills/scope-keeper/SKILL.md` before the next
  `--force` run.
- ~~Non-blocking: is the Windows spot-check (AC-013) a `Done` gate or a deferred verification?~~
  **Resolved by [D005](./DECISIONS.md)**: neither — it stops being a manual task. A new
  `scripts/install.test.ps1` runs on the `windows-latest` runner already present in
  `consistency.yml`, so AC-013 is a CI gate. This is a deliberate break from the pattern that left
  specs 015 and 016 stuck on spot-checks nobody performed.

## Contracted services

Contracted services not declared → all billable add-ons treated as NOT contracted (conservative
default). Run `/project-init` to declare them.

`specs/SERVICES.md` is absent from this repository, which is expected: this is the SDD framework
repo itself, not an adopter project with billable services. No billable add-on service
(`seo-geo-addon` and siblings) is touched by this feature.
