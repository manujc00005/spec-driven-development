<!-- See skills/sdd-guardrails/SKILL.md, section 1, for the full decision state machine. -->

# Decisions: multi-profile-routing-and-installation

## Decision log

### D001 - "Enabled" means "not `disabled: true`", and `--all-profiles` expands inside the existing resolver

**Date:** 2026-09-02

**Status:** Accepted

**Context:** The spec says `--all-profiles` installs "every enabled profile", but `profiles.json`
has no `enabled` key. Verified on disk: profiles are enabled implicitly, and `blockchain-crypto`
alone carries `disabled: true`. "Enabled" therefore has to be defined before it can be implemented.

**Decision:** An enabled profile is one whose object does not carry `disabled: true`.
`--all-profiles` / `-AllProfiles` sets a flag passed into the existing python resolver in
`install.sh` (L175–300) and its PowerShell counterpart, which expands it to those keys minus the
billable ones (D002). `core` continues to be prepended by the existing dedupe loop, unchanged.

**Reasoning:** Introducing an explicit `enabled: true` key on eight profiles to express what their
silence already expresses would be a manifest migration in a feature whose NFR is backward
compatibility. Expanding inside the resolver rather than in the bash arg loop keeps one place that
knows what a profile is, and inherits the unknown-name and disabled-name errors for free.

**Consequences:** A future profile is included in `--all-profiles` by default — silence means
enabled. That is the same default `install.sh` already applies to an explicitly named profile, so
it introduces no new asymmetry, but it does mean adding a profile has a blanket-install consequence
the author must think about. Noted in `docs/INSTALL.md` (T018).

---

### D002 - `billable: true` in `profiles.json`, and a manifest version bump to 0.5.0

**Date:** 2026-09-02

**Status:** Accepted

**Context:** FR-010 requires a blanket install not to turn on `seo-geo-addon`. The spec resolved
OQ-2 in favour of an explicit key and left the version bump to planning.

**Decision:** Add `billable: true` to `seo-geo-addon` only, and bump `profiles.json` `version` from
`0.4.0` to `0.5.0`.

**Reasoning:** The bump follows the repository's own precedent — `0.4.0` marked the additive,
optional `agents`/`plannedAgents` keys, and this is the same shape of change. A version that does
not move when the schema grows makes the field decorative. The key stays absent rather than
`false` on the other eight profiles: absent is what an older installer sees, and encoding the
default explicitly on every profile invites drift.

**Consequences:** An installer built before this change reads the key as unknown and ignores it,
which is the correct behaviour — it has no `--all-profiles` to misapply it to. `check-consistency.sh`
needs no new rule for the key; it validates named categories, not the whole object.

---

### D003 - The new-profile report ships in `update.ps1` as well as `update.sh`

**Date:** 2026-09-02

**Status:** Accepted

**Context:** FR-011, FR-012 and AC-009/AC-010 name `update.sh` only, while FR-008 names both
installers. `scripts/update.ps1` mirrors `update.sh` closely, including the manifest-read block the
report attaches to.

**Decision:** Implement the report in both. This extends the literal AC text and is recorded here
rather than done silently.

**Reasoning:** The asymmetry reads as an omission, not an intent: nothing in the Non-goals excludes
PowerShell, the installer half is explicitly dual, and a Windows adopter would be the one adopter
who never learns a profile exists — the exact defect (3) this feature was written to fix. Shipping
half a fix and calling the AC satisfied would meet the letter of the criterion and miss its point.

**Consequences:** T015 exists, and the PowerShell half carries the same unverified-on-Windows
caveat as the rest of the repository's `.ps1` surface. AC-009/AC-010 are still evaluated against
`update.sh`, which is where the automated tests run.

---

### D004 - The "active profile" sweep covers `security-reviewer` too, beyond AC-014's three files

**Date:** 2026-09-02

**Status:** Accepted

**Context:** AC-014 enumerates three artifacts: `agents/domain-reviewer.md`, `agents/README.md`,
`docs/AGENTIC_ROUTING.md`. A grep during planning found the same singular instruction in two more
shipped artifacts: `agents/security-reviewer.md:28` ("The active profile (to know which
stack-specific security skills apply)") and `:62`, and `skills/security-review/SKILL.md:37`.

**Decision:** Include those two artifacts in the sweep (T017).

**Reasoning:** FR-015 does not say "in three files" — it says *"'active profile' is removed as a
review-time concept and nothing replaces it."* Leaving `security-reviewer` instructing an agent to
determine the active profile would leave the framework contradicting itself one file away from the
fix, and would leave a second agent stopping to ask the question this feature exists to abolish.
AC-014's list under-enumerates its own requirement.

**Consequences:** The diff is larger than AC-014 implies, in a feature whose NFR asks for
minimalism. The extension is bounded to three lines of prose in two files and adds no rule, no key
and no code. `/spec-review` should read this decision before flagging the extra files as scope
creep.

---

### D005 - The AC-011 baseline is captured pre-change at a fixed path, and lives outside the repository

**Date:** 2026-09-02

**Status:** Accepted

**Context:** AC-011 asks for a byte-identical comparison of `install.sh --profile
java-spring-backend --dry-run` before and after the change. Dry-run output embeds the
`--central-dir` path on most of its 420 lines, so the comparison is only meaningful at a fixed path.
Determinism was verified during planning: two runs at the same path produced byte-identical output.

**Decision:** T001 captures the baseline **before any implementation edit**, using an explicit
`--central-dir` under the session scratchpad, and stores it there. It is not committed. T021 re-runs
the same command at the same path and diffs. The capture's commit SHA is recorded in T021's
verification note so a reviewer can confirm the baseline predates the change.

**Reasoning:** A baseline captured after an edit lands produces a green diff that proves nothing —
the failure mode is silent and total. Committing 420 lines of machine-specific paths into `specs/`
would be noise that rots on the first path change; the SHA plus the re-runnable command is the
durable half.

**Consequences:** If the baseline is lost before T021 runs, it cannot be recreated from the changed
tree — it must be re-captured from the pre-change commit via `git stash`-free worktree checkout or
`git show`. T021 states this rather than assuming the file survives.

---

### D006 - FR-004b edits the generic base descriptions, under a hard 400-character cap

**Date:** 2026-09-02

**Status:** Accepted

**Context:** FR-004b requires every reviewer description to name the artifact it applies to, because
`description` becomes the routing signal. Audited during planning across the 26 skills routed to
`domain-reviewer`: the stack-specific ones already comply, but the generic bases (`api-review`,
`backend-review`, `frontend-review`, `database-review`) and `release-readiness` /
`microservices-patterns-reviewer` name concerns rather than artifacts. Descriptions carry a
400-character cap from spec 022; the longest today is 381.

**Decision:** Edit those descriptions to name a file type or artifact, trading words rather than
appending them, and assert the cap mechanically after editing (T008).

**Reasoning:** A routing signal that does not name what it routes on is not a signal. The generic
bases are the ones most likely to over-fire under a description-driven rule precisely because they
claim everything, which makes them the highest-value edits rather than the marginal ones.

**Consequences:** Six descriptions change text that adopters may have grown used to. Nothing depends
on their exact wording mechanically; `check-consistency.sh` validates form, not prose.

---

### D007 - FR-016's "reviewers applied" line is required of `domain-reviewer` only

**Date:** 2026-09-02

**Status:** Accepted — resolves OQ-5 (non-blocking)

**Context:** OQ-5 asked whether FR-016's output requirement belongs on `domain-reviewer` alone or on
every review skill's output format.

**Decision:** `domain-reviewer` alone.

**Reasoning:** FR-016 exists because *selection* became invisible — a reviewer that silently did not
fire. Only `domain-reviewer` selects; every other review skill is invoked directly and its absence
is visible at the call site. Imposing an output-format clause on ~26 skills would be the "additional
validation" the maintainability NFR rules out, for a problem those skills do not have.

**Consequences:** OQ-5 closes. If a second selecting agent ever appears, the requirement travels
with the selection behaviour, not with the skill catalogue.

---

### D008 - No checker rule for FR-004b

**Date:** 2026-09-02

**Status:** Accepted — resolves OQ-8 (non-blocking)

**Context:** OQ-8 asked whether `check-consistency.sh` should verify that every reviewer description
names an artifact.

**Decision:** No. AC-016 is verified by the one-off audit in T002/T022, not by a permanent rule.

**Reasoning:** The maintainability NFR caps this feature at exactly one new rule, and FR-006 spends
it. Any automated check here is a prose proxy — "does this sentence name a file type?" — which is
the false-positive class spec 022 D006 already documented. A rule that fires on good descriptions
teaches maintainers to route around the checker, which costs more than the gap it closes.

**Consequences:** FR-004b is a convention defended by review, not by tooling. A new reviewer skill
can ship with a concern-only description and nothing will complain. Named as a known limitation in
the feature's closing summary rather than left implied.

---

### D009 - Routing and installation stay in one spec

**Date:** 2026-09-02

**Status:** Accepted

**Context:** The spec's Assumptions section explicitly permits a split: *"If planning shows the two
halves do not share artifacts, splitting into two specs is a reasonable outcome rather than a
failure."* Planning shows they largely **do not** — the routing half touches agents, docs, skill
descriptions and `check-consistency.sh`; the installation half touches `install.*`, `update.*` and
`docs/INSTALL.md`. They share `profiles.json` and the AC-013 suite run, and nothing else.

**Decision:** Keep one spec. Phase the tasks so the two halves are independently committable, and
land them as separate commits.

**Reasoning:** The split is viable and was rejected on cost, not principle. A new spec number is not
free in this repository — spec numbers have collided across machines three times — and the two
halves share the user story that justifies both: the polyglot adopter who is both under-reviewed and
unable to install what they need. Splitting would give two specs that each read as half a
motivation. Independent commits capture most of the bisect benefit a split would have bought.

**Consequences:** The feature's diff spans two areas, and `/spec-review` sees a wider change than
usual. R6 in `PLAN.md` records the residual risk. If implementation stalls on one half, the other
can still close — the phases do not interlock except at T023's suite run.
