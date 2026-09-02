# Decisions: autonomous-adopt-in-flight-feature

## Decision log

### D001 - Codex is covered on the same footing as the parent mode; its smoke run gates `Done`

**Date:** 2026-09-02

**Status:** Accepted

**Context:** OQ-1 asked whether 041 ships Claude-Code-only, consistent with `sdd-orchestrate`
being `provider_specific: true`. Two facts settle it. The maintainer's standing rule since
2026-08-06 is that every framework feature covers Codex on the same footing, gating the *close* on
verification rather than the *coverage* on someone remembering. And the parent mode already did
exactly that: 031 FR-012 documented autonomous mode's sequential degradation in
`adapters/codex/PARITY.md`, and 031 AC-013 required behavioral evidence on both providers before
closure, recording an unexecutable provider as an explicit blocker.

**Decision:** 041 mirrors 031. The Codex adapter documents `--adopt` under the same
sequential-degradation contract (FR-012, T007), the Codex `sdd-spec-implement` prompt gets the same
hand-off line as the Claude skill (T006), and a Codex smoke run of the adopt entry is required
before `/spec-close` (FR-013, AC-014, T013). A provider whose run cannot execute is recorded as an
explicit closure blocker, never as a pass and never omitted.

**Reasoning:** The protocol's state lives in files and is provider-neutral by design; adoption adds
header fields and a review step, nothing provider-specific. Documenting it for Codex costs one
section; not documenting it creates parity debt nobody schedules. This reasoning assumed the Codex
CLI was not installed on the maintainer's Mac, so that T013 would most likely end as a blocker — the
rule's intended outcome, gating `Done` and not `Ready`.

**Superseded 2026-09-02 (T013):** that assumption was false. `codex-cli 0.152.1` is installed, and
T013 **passed**: two recorded `codex exec` runs produced the correct gate refusal and, under
`--adopt`, a state file whose adoption shas match git exactly plus a valid `REJECT` verdict block.
The decision itself is unchanged and was vindicated rather than weakened — covering Codex was right,
and the coverage turned out to be verifiable instead of deferred.

**Consequences:** `adapters/codex/` is in scope. `Done` may be blocked by a missing CLI; the
blocker is visible in `CALIBRATION.md`. No claim of permission-isolation parity is made for Codex,
exactly as the parent mode states.

---

### D002 - Adoption is only from `In Progress`; `In Review` stays excluded

**Date:** 2026-09-02

**Status:** Accepted

**Context:** OQ-2 asked whether `--adopt` should also enter from `In Review` for the "run the
remaining reviews for me" case.

**Decision:** Excluded. `In Review` means every task is checked and `/spec-review` passed; what
remains is `/qa-review`, the specialized reviews and `/spec-close`, each with an owning skill. The
adoption gate names those as the remediation.

**Reasoning:** Adoption exists to pay the review debt of *implementation* done outside the loop.
At `In Review` there is no implementation left to loop over, and having the autonomous mode run
QA-stage skills would give it a lifecycle role 031 deliberately did not grant it. The all-checked
`In Progress` case (spec edge cases, AC-006) already covers "no tasks left but nothing reviewed".

**Consequences:** A feature at `In Review` is finished by hand or by the QA/closure skills. If the
need is real, it is a narrow follow-up entry, not a widening of this one.

---

### D003 - No `--base <ref>`; an unresolvable diff base refuses with a remediation

**Date:** 2026-09-02

**Status:** Accepted

**Context:** OQ-3 asked whether `--adopt` should accept an explicit base ref for repositories
without `origin/HEAD` or with a non-standard integration branch.

**Decision:** No flag. The diff base is `merge-base(default-branch, HEAD)` with the default branch
resolved from git metadata; when it cannot be resolved, the gate refuses as *Inherited diff
undetermined* and tells the maintainer to set `origin/HEAD` (or the equivalent metadata).

**Reasoning:** A user-supplied base is a second place provenance can be wrong, and the whole design
of adoption is that provenance comes from git, not from arguments. The existing *Isolated git
location* rule already refuses to assume a default-branch name; this is the same stance. Setting
`origin/HEAD` is a one-line, reversible fix on the maintainer's side.

**Consequences:** Repositories with unusual integration branches must express that in git
metadata before adopting. If that proves common, a follow-up can add the flag with its own
provenance recording.

---

### D004 - Adoption requires a fully clean tree; nothing pre-existing is ever attributed

**Date:** 2026-09-02

**Status:** Accepted

**Context:** 031's condition 5 allows dirty paths on *re-entry* when attributable to the recorded
run. The 040 runner's gate, on *first* entry, tolerates dirty paths inside the feature folder. The
originating case had ~3,000 uncommitted lines. Something had to be decided for adoption.

**Decision:** Under `--adopt`, `git status --porcelain` must be empty. The maintainer commits the
pre-adoption work on the feature branch first; that commit is the adoption baseline and the run's
trusted baseline. Stash is acceptable only to *exclude* work from the feature. The runner's
inside-feature-folder tolerance is removed in both entry modes (T008, T010).

**Reasoning:** On adoption no run exists yet, so "attributable to the run" has no referent; the
only honest attribution is a commit whose author is the maintainer. 031's rule is "never guess
provenance", and a tolerance keyed on folder location is a guess. Requiring the commit also makes
the later fingerprint, recovery and closure-delta rules work unchanged, because they all start
from a committed baseline.

**Consequences:** One extra manual step (commit) before adopting. The runner's pinned test for the
old tolerance is rewritten deliberately, not left to fail. The runner stops being looser than the
skill, which 040 D007 already declared the wrong direction.

**Clarified 2026-09-02 (T019/T026, from review finding NEW-1/R3-04):** "removed in both entry modes"
is true of *first entry*, which is what this decision is about, and was wrongly applied to re-entry
as well. 031 condition 5 allows the paths the recorded run claims to be dirty on re-entry, and the
runner writes four files itself while running, so a live run could not resume over its own
`ORCHESTRATION.md`. The rule is now guarded by `first_entry`: first entry refuses any dirty path in
both modes, re-entry tolerates `gate.RUN_ARTIFACTS` plus whatever a caller passes as `attributed`
(see D010). D004's own subject is unchanged.

---

### D005 - Inherited work is reviewed before any new task; a `Critical` finding gates new work

**Date:** 2026-09-02

**Status:** Accepted

**Context:** Tasks checked before adoption carry a maintainer's tick but no structured reviewer
verdict. The loop could trust them, ignore them, or review them.

**Decision:** Review them. Before the first implementation delegation, `domain-reviewer` (and
`security-reviewer` under the existing Level-3 triggers) run on `diff-base..baseline`. Findings
enter the registry and become `(from <finding-id>)` tasks under the existing rules. While an
inherited-diff finding of severity `Critical` is open, no new spec task is delegated; lower
severities interleave normally. An empty inherited diff skips the review. Checked tasks are never
re-implemented; the `Inherited` table records that their `Verify:` was not observed by this run,
and final conformance says so.

**Reasoning:** The repo's own calibration history (spec 033, CONF findings) established that a
self-report is worth nothing; a checkbox is provenance, not evidence. Reviewing first also means
new work is built on a diff the loop has judged, so a later REJECT is attributable to the right
change. Gating only on `Critical` keeps the run moving on real but non-blocking debt.

**Consequences:** Adoption costs one or two delegations up front and can surface findings the
maintainer did not expect on their own work. The delegation budget formula is unchanged; its
`max(25, …)` floor absorbs the extra calls.

---

### D006 - Runner parity is gate-level only

**Date:** 2026-09-02

**Status:** Accepted

**Context:** The 040 runner is `EXPERIMENTAL`, `stub`-only, and stops at `CORE-COMPLETE`; its
D034 reserved real providers and lifecycle delegation for a follow-up. 040 D007 says the runner
transcribes the skill and is wrong where they disagree.

**Decision:** The runner gains the `--adopt` flag, the status × adopt matrix, the clean-tree rule,
the inherited record and its `--dry-run` printout (T008–T010). It does not dispatch the
inherited-diff review or any other new delegation.

**Reasoning:** Gate parity is cheap, testable with the stdlib suite, and removes an existing
disagreement. Execution parity would need a backend that can run a reviewer, which 040 certifies
none of. Doing half of it here would widen 040's follow-up under 041's name.

**Consequences:** A runner `--adopt` run that passes the gate still behaves as the experimental
core does today. The follow-up that gives the runner a real provider inherits the inherited-diff
review as a requirement.

**Clarified 2026-09-02 (T017, from review finding CONF-041-03):** "gate-level" bounds what the
runner *dispatches*, not what it *records*. Its first version wrote only an `entry` field, so a
runner-written adopted document could not say what it had inherited and would authenticate as a
`ready` entry under D007. FR-010 asks the runner to record the baseline and diff base, and the
Observability NFR asks for every adoption fact before the first delegation, so the state document
now carries `adoption baseline commit`, `adoption diff base` and an `Inherited` table. No new
delegation, so the decision itself stands.

---

### D007 - `Entry` header defaults to `ready` on existing state files

**Date:** 2026-09-02

**Status:** Accepted

**Context:** `ORCHESTRATION.md` gains an `Entry` header line. Runs started before this feature have
none, and re-entry authentication must not break them.

**Decision:** `Ready` entries write `Entry: ready`; on re-entry a missing `Entry` line is read as
`ready`. Only `Entry: adopt` carries the adoption fields and the `Inherited` section.

**Reasoning:** Backward compatibility for state files in flight costs one sentence in the
re-entry rule and one unit test; refusing them as malformed would strand active runs for no gain.

**Consequences:** T004 and T010 pin it. A state file with `Entry: adopt` read by a pre-041 skill
after a rollback fails authentication and must be preserved under a timestamped name, as the
existing recovery rule already requires.

---

### D008 - The canonical `ORCHESTRATION.md` scaffold moves to `templates/ORCHESTRATION.md`

**Date:** 2026-09-02

**Status:** Accepted

**Context:** T002–T005 add about 70 lines of protocol to `skills/sdd-orchestrate/SKILL.md`, which
was at 567 lines on `main`. `scripts/check-consistency.sh` caps a skill body at 600 lines
(`skill-form`, "move heavy reference into linked sibling files") and refused at 636. AC-011 requires
that gate green. Trimming the new protocol text to fit would have cut the rules the feature exists
to state.

**Decision:** The 72-line canonical scaffold fence moves verbatim, with the 041 additions, to
`skills/sdd-orchestrate/templates/ORCHESTRATION.md`. `SKILL.md` keeps a pointer that names the
scaffold's sections in order and states that every rule about its fields stays in the skill. This
follows the existing `skills/sdd-guardrails/templates/` precedent.

**Reasoning:** The scaffold is shape, not rule: nothing in the runner, the conformance test or the
docs parses it out of `SKILL.md` (checked: `runner/tests/conformance/test_transcription.py` only
asserts the closed-enum phrase; `PROTOCOL_TRANSCRIPTION.md` cites sections by name). `install.sh`
copies skill folders whole, so the sibling file ships with no installer or manifest change and
AC-011 still holds.

**Consequences:** `SKILL.md` is at 562 lines. T004's `Verify:` clause now points at the template
file for the header lines and the `Inherited` table; the re-entry sentence it also checks stays in
`SKILL.md`. Rollback reverts the move with the rest of the skill edits. Adopters who read the
installed skill find the scaffold one folder down, at the path the pointer names.

---

### D009 - A pre-existing resume crash on an empty Attempts table is fixed as adjacent-necessary

**Date:** 2026-09-02

**Status:** Accepted

**Context:** T010's entry-default test authenticates a fresh state document through the public
`resume.inspect` seam. That call crashed: `_load_attempts` returned three values on an empty
`Attempts` table and four otherwise, and `inspect` unpacks four. Not introduced by 041 — any
runner run interrupted after the gate and before its first attempt row could not be resumed;
it raised `ValueError` instead of a named refusal.

**Decision:** Change the early return to four values (`set(), set(), set(), 0`) — one token —
and leave everything else in `resume.py` untouched. The entry-default test covers the empty-table
path from then on.

**Reasoning:** The test cannot be written honestly around the bug (seeding a fake attempt row
would test a document no fresh run produces), and the fix cannot be smaller. Reporting it
without fixing would leave 041's own test red on a defect one line away.

**Consequences:** Resume on a zero-attempt document now yields an empty `ResumeState` instead of a
crash. No behavior change for documents with attempts. Recorded here so the diff line is
traceable to a decision, not folded into the feature silently.

---

### D010 - `attributed` ships unwired, and the resumability limit is stated rather than hidden

**Date:** 2026-09-02

**Status:** Accepted

**Context:** T019 gave `gate.check` an `attributed` parameter so it can express 031 condition 5 on
re-entry: only the paths the recorded run claims may be dirty. Review finding R3-03 observed that no
production caller passes it, and that nothing in the runner records such a list — attempt rows store
the repo root as their scope, and fingerprints are digests, not paths. So in practice the CLI
tolerates only the four files the runner writes itself.

**Decision:** Leave it unwired and say so. The parameter stays, documented in the gate docstring and
in `runner/README.md`, and the test that exercises it says in its own docstring that it pins a
capability the CLI does not yet use. Recording real attributed paths would mean changing what every
attempt persists, which is dispatch-side work D006 puts outside this feature.

**Reasoning:** The alternative to stating the limit is hiding it. Wiring it properly is a bigger
change than the finding warrants and lands squarely in the follow-up D006 reserves; deleting the
parameter would leave the gate unable to express the rule it is required to mirror, and the next
person would re-derive it. What must not happen is a test that proves a capability while the prose
claims a behavior, which is the pattern two earlier rounds already caught here.

**Consequences, stated plainly:** with `--backend stub` nothing writes to the tree, so re-entry is
unaffected. With a real backend — `claude` is the CLI default — an interrupted run whose worker
touched source files leaves those files dirty, no list attributes them, and the run **cannot be
resumed through the runner CLI**: the gate refuses `unattributed dirty tree` and the operator must
reconcile by hand. That is consistent with 040's `EXPERIMENTAL` classification, where `stub` is the
only supported backend, and it is the first thing the follow-up must fix if it gives the runner a
real provider.

---

### D011 - Two things round 5 caught: how a performed task with a dead criterion closes, and one condition the runner owns alone

**Date:** 2026-09-02

**Status:** Accepted

**Context:** Two findings from the fifth review, both about things this feature did without recording
them.

The first: T014 was performed — the replay ran against the live repository — but its `Verify:` clause
became unsatisfiable for a reason unrelated to what the replay found (`030` moved to `In Review`,
which D002 excludes). It was closed with an invented marker, `PERFORMED`, in a file whose own header
fixes three markers and says they are not interchangeable.

The second: T029 added `status unreadable`, a user-visible refusal condition, under a comment saying
these names are mirrored from `skills/sdd-orchestrate/SKILL.md`. It is in no skill, no document and
no requirement. It is also a deliberate divergence: the skill is model-mediated and reads any SPEC
dialect, so it needs no such condition, while the runner's parser does.

**Decision:** No fourth closure marker. A task that was performed keeps a plain tick — the template
already says a tick with no marker means performed — and when its criterion turns out mis-stated or
dead, the repo's existing `[VERIFY AMENDED]` note says so and names the criterion actually met.
Anything still owed becomes a DEBT id; for T014 that is [[DEBT-010]], the adopted loop never having
reached a human-gated `PAUSED` outside a fixture. And `status unreadable` is recorded as a
runner-only condition: documented in `runner/README.md` and in this SPEC's interface list, with the
gate's comment corrected to stop claiming a mirror that does not exist.

**Reasoning:** Inventing a marker inside one feature's task list leaves the repo with a fourth
closure keyword defined nowhere, which is the drift `specs/_templates/TASKS.md` exists to prevent —
and that template is not this feature's to edit. On the second point, 040 D007 says the runner is
wrong where it and the skill disagree; the exception is a divergence that is *recorded*, and this one
is defensible on the merits: a regex parser and a model do not have the same job. Undocumented, it
would be indistinguishable from the accidental drift this feature was written to remove.

**Consequences:** T014 carries a plain tick, a `[VERIFY AMENDED]` note and a DEBT id. `status
unreadable` is documented where an operator hitting exit 10 will look. Nothing in the framework's
template changes, and a later feature that wants a "performed but the criterion died" marker has to
amend the template deliberately rather than inherit one from here.

**Amended 2026-09-02 by [[#D012]]:** this decision originally made [[DEBT-010]] a gate on `Done`.
The maintainer lifted that gate. DEBT-010 remains open and tracked; it no longer blocks closure. The
rest of D011 — the closure-marker rule and the recorded runner/skill divergence — is unchanged.

---

### D012 - Spec updated: DEBT-010 is known debt, not a `Done` gate

**Date:** 2026-09-02

**Status:** Accepted

**Context:** D011 made [[DEBT-010]] block `/spec-close`: the adopted loop had never reached a
human-gated `PAUSED` outside a fixture, and T014's replay could not supply that observation because
the originating feature had moved past adoption's window. Holding closure open for it would mean
waiting for the next real in-flight feature — an unbounded wait for evidence about a path that is
already exercised end to end.

**Decision:** DEBT-010 stops gating `Done`. It stays open in `docs/KNOWN_DEBT.md` with its closing
condition unchanged, and is now carried as known debt. Nothing else moves: no code, no task, no
acceptance criterion, and D011's other two rulings stand.

**Reasoning:** The maintainer's, and it holds. Three things make the residual small. The
human-gated path is proven end to end by T028 — a real worker returned `BLOCKED` with its question
verbatim, the classifier called it human-gated, the independent task continued, and the run ended
`PAUSED` with its remediation — so what is missing is *observation on a real feature*, not the
mechanism. The escalation and `PAUSED` code is spec 031's and this feature did not touch it. And the
tool is experimental and local: `stub` is the only supported backend (040's classification), so a
failure here would surface as a run that aborts where it should pause — visible and recoverable, not
a silent wrong answer.

**Consequences:** `/spec-close` may run. No task is impacted, none is over-implemented, and no
acceptance criterion changes — AC-014's evidence never depended on DEBT-010. The debt keeps its
entry and its closing condition, so the next feature adopted by hand still pays it off; what changed
is that this feature no longer waits for that. If the path does misbehave against a real feature, the
cost is one aborted run and this entry to point at.
