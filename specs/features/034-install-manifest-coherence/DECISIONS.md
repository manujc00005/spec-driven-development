# Decisions: install-manifest-coherence

## Decision log

### D001 - `update.sh` replays the recorded profile list verbatim; `defaults.profile` never applies to a recorded install

**Date:** 2026-08-21

**Status:** Accepted

**Context:**

This resolves the spec's one **blocking** open question. `update.sh` strips `core` from the
recorded list and passes the remainder as `--profile`
([update.sh:163-168](../../../scripts/update.sh:163)). After `--remove-profile` leaves only
`["core"]`, the remainder is empty, `install.sh` receives no `--profile`, and its resolver falls
back to `defaults.profile` — `java-spring-backend` — silently re-adding a profile the adopter
just removed. FR-014/AC-006 would be unachievable in exactly the case removal exists for.

Note this is a **latent bug today**, not one this feature introduces: any manifest recording only
`core` already suffers it. Removal just makes the state reachable on purpose.

Two readings were available:

- **(a) The manifest is authoritative.** A recorded install replays exactly what is recorded, and
  the default-profile fallback is a convenience for direct invocation only.
- **(b) `defaults.profile` still applies.** Removal cannot deliver AC-006 in the general case, and
  the framework keeps a path that contradicts the adopter's recorded choice.

**Decision:**

Reading (a). `update.sh` / `update.ps1` pass the recorded profile list **verbatim, including
`core`**. `defaults.profile` applies only to a direct `install.sh` invocation with no `--profile`.

**Reasoning:**

The manifest's purpose is to record what the adopter chose. A fallback that overrides that record
is not a default, it is a contradiction. Reading (b) would also leave the latent bug in place.

Decisively: `--profile core` **already resolves correctly** — `core` is a valid, non-disabled key
in `profiles.json`, and the resolver prepends `core` to the requested set regardless. So reading
(a) needs **no new flag and no change to `install.sh`'s resolver**; it is a strictly smaller change
than the alternative, and the cheaper option is also the correct one.

**Consequences:**

- For every existing adopter, behavior is **unchanged**: a manifest recording
  `["core", "java-spring-backend"]` produces the same active set either way. The two readings
  differ only when the recorded set is `core`-only.
- `update.sh`'s "Re-installing with recorded profiles" log line now includes `core`, which is
  more accurate than the current output.
- The genuinely-empty case (no manifest at all) keeps the existing unknown-version path and its
  default-profile fallback. Untouched.
- Asserted by AC-006.

---

### D002 - Manifest schema v2: a `profileState` map beside the existing `profiles` list

**Date:** 2026-08-21

**Status:** Accepted

**Context:**

FR-001 needs per-profile commit tracking. `profiles` is a flat string array that `update.sh`
replays directly; changing its element type would break every reader at once.

**Decision:**

`schemaVersion: 2`. `profiles` is retained **unchanged** as the ordered list of record. A sibling
`profileState` object maps each name to `{commit, version, installedAt}`. A run rewrites entries
only for `ACTIVE_PROFILES`. Top-level `installedVersion`/`installedCommit` are retained and
redefined as "the newest commit any profile reached" (FR-005).

**Reasoning:**

Additive-beside rather than change-in-place keeps a v1 reader working against a v2 file — which is
what makes the rollback in PLAN.md safe. Keeping `profiles` as the replay source also means D001
and the removal path need no knowledge of `profileState`.

**Consequences:**

- Two structures can disagree. A name in one and not the other is corrupt state, handled by the
  existing discard-and-rebuild rule (D003); a name in `profiles` missing from `profileState` is
  backfilled from the top-level commit rather than treated as fatal.
- `update.sh` must take its delta from the **oldest** `profileState.commit`, never the top-level
  value — the top-level value is precisely the optimistic number that caused the original defect.
  Asserted by AC-002.

---

### D003 - v1 migrates optimistically; an unknown `schemaVersion` is discarded

**Date:** 2026-08-21

**Status:** Accepted

**Context:**

Existing adopters hold `schemaVersion: 1` manifests. FR-003 forbids requiring a re-install.

**Decision:**

`schemaVersion: 1` → synthesize `profileState` by attributing the single top-level
`installedCommit` to every recorded profile. `schemaVersion` ≥ 3 or unparseable → existing
discard-and-rebuild / unknown-version mode.

**Reasoning:**

The migration is knowingly optimistic — it may record a commit a profile never reached. That is
acceptable because **it asserts nothing new**: it is exactly the claim the v1 format already made
for the whole set. It cannot be worse than the status quo, and the first post-migration run
corrects the active profiles. Any alternative (probing the disk, refusing to migrate) either costs
a tree walk or forces the re-install FR-003 rules out.

Refusing to guess at a *future* schema follows the installer's existing stance — it already refuses
to fall back to installing everything unfiltered rather than guess.

**Consequences:**

- A migrated adopter may see the FR-004 warning name profiles that are in fact current. Acceptable:
  it errs toward reporting staleness, never toward hiding it.
- The optimism is bounded to one run.

---

### D004 - Removal derives ownership from `profiles.json` only, and never deletes without a backup

**Date:** 2026-08-21

**Status:** Accepted

**Context:**

`--remove-profile` is the **only destructive path in the repository**. Everything else copies,
skips, or backs up before overwriting.

**Decision:**

1. Ownership is computed **solely** from `profiles.json`: an item is deletable iff it appears in the
   removed profile's arrays and in no still-recorded profile's arrays. Never inferred from the
   filesystem.
2. The profile name is validated against `profiles.json` keys **before any filesystem call**.
3. `core` is refused outright (FR-010).
4. Every deletion is preceded by a backup into `_install-backups/<timestamp>/`. A backup that fails
   **aborts** the removal — it does not warn and continue.

**Reasoning:**

(1) makes ownership a pure function of a version-controlled file, so it is reviewable and testable
without a populated central dir; filesystem inference would delete whatever happened to be lying
around. (2) is the path-traversal guard (R2) — validating the *name* against a closed set is
stronger than sanitizing a path. (4) inverts the usual warn-and-continue posture because a lost
backup on a delete is unrecoverable, unlike a lost backup on an overwrite where the repo still
holds the source.

**Consequences:**

- An item that a *planned* (not shipped) profile lists is not protected — `plannedSkills` describe
  intent, not installed files. Correct, and worth stating so it is not read as an oversight.
- Items installed by a since-deleted profile definition become unreachable by removal. Out of
  scope; the adopter deletes them by hand, as today.
- Asserted by AC-005, AC-007, AC-008, AC-010.

---

### D005 - Windows parity is a CI gate, not a manual spot-check

**Date:** 2026-08-21

**Status:** Accepted

**Context:**

The spec left this as a non-blocking question. The repo's Windows CI (`consistency.yml`,
`windows-syntax` job) is **parse-only by design** (spec 012 D002) — it proves `.ps1` files parse,
never that they behave. Every behavioral Windows claim to date has rested on a manual spot-check,
and that is precisely what has left specs 015 and 016 unclosed.

**Decision:**

Add `scripts/install.test.ps1` and `scripts/update.test.ps1`, and execute both on the
`windows-latest` runner that already exists in the workflow. `Done` gates on those jobs, not on a
maintainer's manual run.

**Amended 2026-08-21 (during `/spec-review`).** This decision originally scoped the PowerShell
suite to a subset — AC-001, AC-003, AC-005, AC-007, AC-011 — which **contradicted AC-013**, whose
text requires the PowerShell side to satisfy AC-001..AC-012. The review found the contradiction
plus a harder problem behind it: `update.ps1` was rewritten by T015 and had **no** automated
coverage at all. The subset is therefore widened rather than the AC narrowed: `install.test.ps1`
now also covers AC-008 and AC-012, and the new `update.test.ps1` covers AC-002, AC-006 and AC-006b.
AC-013 is satisfied as written.

**Reasoning:**

The runner is already provisioned; the marginal cost is the harness, not the infrastructure. Spec
012 D002's parse-only stance was about **hooks** (executing them in CI is genuinely risky); an
installer writing into a temp directory has no such hazard, so this extends that decision rather
than contradicting it.

The alternative — a manual spot-check — has a measured failure rate of two specs stuck on exactly
this task. Choosing it again would be choosing a known-broken process.

**Consequences:**

- Scope grows by one new file. Deliberately bounded to **this spec's behaviors**; it is not a port
  of `install.test.sh`.
- CI wall-clock grows by one Windows job step.
- Supersedes the spec's non-blocking Windows question. `Done` no longer depends on a user-only task.

---

### D006 - `scripts/install.test.sh` is wired into CI before new assertions are added to it

**Date:** 2026-08-21

**Status:** Accepted

**Context:**

Verified against [`consistency.yml`](../../../.github/workflows/consistency.yml): CI runs
`check-consistency.sh`, `check-consistency.test.sh`, `graphify.test.sh` and `update.test.sh`.
`install.test.sh` **is not run**. Its existing spec-016 assertions have never gated a merge.

**Decision:**

Wire `install.test.sh` into the `check` job as a task in **Phase 1**, before Phase 3 adds
assertions to it.

**Reasoning:**

Writing tests into a harness nobody runs produces coverage that only appears to exist — the same
class of defect this whole feature is about (a record asserting a state that does not hold).
Ordering it first means every assertion added later is live on arrival.

**Consequences:**

- The pre-existing spec-016 assertions start gating merges. If any is already red, that is a real
  regression surfacing, and T003 must stop and report rather than weaken the assertion.
- Asserted by AC-014.

---

### D007 - Stale recorded profiles are reported, never auto-refreshed

**Date:** 2026-08-21

**Status:** Accepted

**Context:**

The spec's second non-blocking question. FR-004 reports unrefreshed profiles; it would be a small
step to refresh them.

**Decision:**

Report only. A run's active set stays exactly what the adopter named.

**Reasoning:**

A run named `--profile java-spring-backend` that silently writes `python-sql-data` files installs
content nobody requested — the same objection spec 030 raised against auto-installing newly-added
profiles, and consistent with the installer's existing refusal to guess. The report carries the
exact refresh command, so the adopter is one paste away from the other behavior.

**Consequences:**

- An adopter who ignores the warning stays stale. Accepted: visible-and-ignored beats silent.
- If this proves wrong in practice, a future `--refresh-all` is additive and supersedes this
  decision without reworking anything here.

---

### D008 - No Codex counterpart; recorded as an honest gap

**Date:** 2026-08-21

**Status:** Accepted

**Context:**

The framework treats Codex as first-class. `adapters/codex/install-codex.sh` has **zero**
occurrences of `profile` (verified) and writes no manifest.

**Decision:**

Bash + PowerShell only. Recorded here so the omission is a decision rather than an oversight.

**Reasoning:**

Parity means matching capability, not adding a manifest to an installer that has no profile concept
to record. Giving the Codex adapter profiles is a separate feature with its own spec.

**Consequences:**

- A Codex-only adopter gets none of this. Correct, since they have no profiles to track or remove.
- Same treatment as spec 030 and spec 029 D008.

---

### D009 - The shipped READMEs route through `copy_file_safely`

**Date:** 2026-08-21

**Status:** Accepted

**Context:**

`agents/README.md` and `hooks/README.md` are copied only when absent
([install.sh:500](../../../install.sh:500), [:566](../../../install.sh:566);
`install.ps1:475`, `:559`), so `--force` never refreshes them.

**Decision:**

Delete the guards; call `copy_file_safely` with a backup path under `_install-backups/$TIMESTAMP/`,
exactly as every other shipped file does.

**Reasoning:**

The helper already implements the required semantics (new → copy, identical → no-op, differs → skip
unless `--force`, differs + `--force` → back up then overwrite). The write-once guard was
presumably protecting adopter edits, but it protects them by **going permanently stale** and
reporting nothing — and `copy_file_safely` protects them properly, via backup. Net diff is smaller
than the code removed.

**Consequences:**

- An adopter who hand-edited a central README loses it to the next `--force`, with a backup taken.
  Documented in the spec's Edge cases.
- Asserted by AC-011, AC-012.

---

### D010 - A removal-only run does not fall back to `defaults.profile`

**Date:** 2026-08-21

**Status:** Accepted

**Context:**

Found by testing during implementation of T009, not at plan time. D001 fixed resurrection through
`update.sh`, but the same hole existed **inside a single direct run**: `install.sh --remove-profile
java-spring-backend` (no `--profile`) resolved its active set from `defaults.profile`, so it deleted
the profile's files and re-installed them in the same pass, then re-recorded the profile in the
manifest. Verified before the fix — `profiles` came back as `['core', 'java-spring-backend']` and
`skills/java-spring-reviewer` was still on disk.

FR-014 and AC-006 were therefore satisfiable through `update.sh` but not through the flag the spec
actually introduces.

**Decision:**

When `--remove-profile` is given and `--profile` is not, the resolver skips the `defaults.profile`
fallback and the active set is `core` alone. With `--profile` also present, nothing changes.

**Reasoning:**

The purpose of such a run is removal; installing an unrequested profile on top of it is a
contradiction, and it is the same class of error as D001. Suppressing the fallback (rather than,
say, replaying the manifest) keeps the run's active set equal to what the adopter named — the
principle D001 and D007 already rest on.

The remaining recorded profiles are then reported as unrefreshed by FR-004, which is honest: this
run genuinely did not refresh them.

**Consequences:**

- `install.sh --remove-profile X` no longer refreshes the surviving profiles as a side effect. The
  FR-004 warning names them and prints the refresh command, so the behaviour is visible rather than
  silent.
- The installer's standing refusal to do a silent core-only install (the `FATAL_ERROR` branch when
  no profile is requested and no default exists) is untouched for ordinary runs — the suppression
  applies only when a removal was explicitly requested.
- Asserted by AC-006 and by the removal cases in T017.

---

### D011 - Two fixes outside spec 034's stated scope, landed here on purpose

**Date:** 2026-08-21

**Status:** Accepted

**Context:**

`/spec-review` flagged two changes in the diff that no FR asks for. Both are real, both are small,
and leaving either undocumented would be exactly the untracked-claim problem this spec exists to
remove.

1. **`Format-ManifestStamp` in `install.ps1`** fixes a **pre-existing spec 015 defect**:
   PowerShell 7's `ConvertFrom-Json` parses ISO-8601 strings into `[datetime]`, and interpolating
   one back rendered it in the current culture (`08/21/2026 16:25:52`). The manifest was therefore
   never byte-identical on a no-op re-run under PowerShell — spec 015 AC-003 held on bash only.
   Confirmed by running the pre-034 `install.ps1` from git before touching it.

2. **`usage()` in `install.sh`** no longer prints a hard-coded `sed -n '2,48p'` line range. Adding
   the `--remove-profile` help text pushed the options list past line 48 and silently truncated
   `--force`, `--dry-run`, `--skip-link` and `--link-user-claude` from `--help`.

**Decision:**

Both stay in this diff. (1) is required to satisfy AC-004 and AC-013, which demand a byte-identical
manifest on *both* platforms — it cannot be deferred without failing an acceptance criterion.
(2) repairs damage caused by this spec's own documentation change, so it belongs to this spec.

**Reasoning:**

Splitting (1) into its own spec would mean shipping 034 with a knowingly failing AC on Windows, or
weakening the AC to match a bug. Deferring (2) would mean shipping a `--help` this spec broke.

Making `usage()` range-independent rather than moving the number to 58 is the smaller long-term
change: the fixed range is the defect, and it would have silently truncated the next person's edit
too.

**Consequences:**

- Spec 015's AC-003 becomes true on PowerShell for the first time. Anyone auditing spec 015 should
  read this entry — its acceptance criterion passed on one platform only until now.
- `--help` output is now derived from the comment block's actual extent, so it cannot drift again.
- Both are covered: the manifest fix by AC-004 in `install.test.ps1`, the `usage()` fix by the
  options-parity check run during implementation (declared flags vs flags shown).
