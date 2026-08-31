# Decisions: agent-sdk-runner

## Decision log

### D001 - v1 is repository tooling, not a shipped framework artifact

**Date:** 2026-08-31

**Status:** Accepted

**Context:** This repo is a framework installed into `~/.claude` and linked into adopter projects.
A runner that ships must enter `install.sh`/`install.ps1`, the install manifest,
`check-consistency.sh`'s coherence rules and `profiles.json` — and every adopter inherits
`claude-agent-sdk`, the first non-stdlib Python dependency this repo would ever have. This was
OQ-1, and it was blocking because the two designs differ in nearly every file they touch.

**Decision:** v1 lives in `runner/` as maintainer tooling. No installer change, no manifest change,
no `profiles.json` change, no downstream assumption. Downstream distribution is a later phase.

**Reasoning:** The maintainer's call, and the reasoning holds up: pushing a pip dependency onto
every adopter to validate a loop that has never once run unattended is paying the integration cost
before earning the confidence. Containment is also cheap here — the runner has no callers inside
the framework, so keeping it out of the installers costs nothing but discipline.

**Consequences:** FR-014 and AC-014 exist to make containment checkable rather than intended: the
installers and manifests must be byte-identical to `main`, and the existing suites must pass at
their current counts on a machine with neither the SDK nor Codex. Rollback becomes deleting one
folder. The cost is that adopter projects get no benefit from phase 2 until a later spec ships it.

---

### D002 - The package lives at `runner/`, not `scripts/runner/`

**Date:** 2026-08-31

**Status:** Accepted

**Context:** The maintainer offered either location. `scripts/` today contains exclusively
executable Bash and PowerShell files plus `scripts/lib`; every `python3` use in the repo is an
inline stdlib heredoc inside a shell script.

**Decision:** `runner/` at the repository root.

**Reasoning:** A pip package with its own dependency manifest and test tree is a different kind of
artifact from the shell scripts in `scripts/`, and mixing them would make `scripts/` mean two
things. A top-level folder is also the cleanest thing to exclude from the installers and the
easiest to delete on rollback.

**Consequences:** One new top-level entry. T001 confirms `check-consistency.sh` has no rule that a
new top-level folder violates, before anything else is built on the assumption.

---

### D003 - The first real workload is this repository's own specs

**Date:** 2026-08-31

**Status:** Accepted

**Context:** OQ-2, blocking: the alternative was the day job's Python/SQL/Jira flows.

**Decision:** v1 targets specs of this repository. The day-job flows are explicitly out of scope,
including as fixtures.

**Reasoning:** This repo has controlled `SPEC.md`/`TASKS.md`/`ORCHESTRATION.md` in a domain the
maintainer knows exactly. The day-job case brings a database, large JSON payloads, external
permissions and sensitive data; putting that risk surface into the runner's first version blurs
which failures belong to the runner and which belong to the environment.

**Consequences:** The fixture feature and both E2E scenarios live inside this repo. The runner may
assume this repo's layout in v1; making it portable to arbitrary projects is a later requirement,
not an implicit one. T022's overnight run is against a real spec here.

---

### D004 - The Codex backend ships implemented but gated

**Date:** 2026-08-31

**Status:** Accepted

**Context:** The maintainer decided Codex is an architectural target of v1, not a functional
requirement, gated until DEBT-001 and DEBT-002 close. The Codex CLI is **not installed on this
machine** (`which codex` → not found, verified 2026-08-31), which also contradicts spec 031's
closing assumption that a Codex CLI was present. That instruction admits two readings: *(a)* write
only the interface and leave Codex unimplemented, or *(b)* write the implementation and ship it
switched off.

**Decision:** Reading **(b)**. The `codex` backend is a real implementation of the `Backend`
protocol and refuses to run without an explicit `--allow-unverified-backend` opt-in, naming
DEBT-001 and DEBT-002 in the refusal. No document — README, CHANGELOG or docs — claims verified
multi-backend support until a real `codex exec` run records the accepted flag spellings.

**Reasoning:** Reading (a) is how DEBT-002 came to exist: a provider path described in prose,
never executed, quietly rotting behind a label. An abstraction with one implementation and a
comment is not an abstraction. Writing the code makes the interface carry two real loads and makes
the remaining gap exactly one thing — an unexecuted CLI — instead of an unknown amount of unwritten
work. The `--allow-unisolated` flag in `scripts/skill-eval.sh` is the precedent for gating an
enforced-but-unverified provider path this way, so this is the repo's existing idiom rather than a
new one.

**Consequences:** This deliberately narrows the framework's usual "provider verification gates
`Done`" convention: v1 may reach `Done` with Codex unverified, because the honest alternative is
blocking the feature on a CLI nobody has installed. AC-013 splits accordingly — the refusal
behavior is mandatory and testable now; the real `codex exec` run is conditional and, if it does
not happen, must be **reported as unobserved rather than assumed**. DEBT-001/DEBT-002 stay open and
are now also load-bearing for this feature.

---

### D005 - No checkpoint commits in v1

**Date:** 2026-08-31

**Status:** Accepted

**Context:** Spec 031 deferred audit/bisect/crash-recovery commits to phase 2 "where the SDK runner
— not an agent — could own them", because the agents' contracts forbid committing. This was OQ-3.

**Decision:** Out of v1, confirmed by the maintainer. Recorded as a follow-up rather than dropped.

**Reasoning:** An unsupervised executor should not write git history in its first release. Every
other defect in the runner becomes harder to recover from once it has been committing along the
way, and the recovery value checkpoints provide is not needed until the runner is trusted enough to
run long unattended stretches.

**Consequences:** Crash recovery in v1 rests entirely on `ORCHESTRATION.md` being written before
each transition (031 FR-008) — which is what AC-007's SIGTERM test proves. FR-012 forbids git
writes outright, so adding checkpoints later is a spec change, not a config flag.

---

### D006 - The verdict block gains no schema version in this feature

**Date:** 2026-08-31

**Status:** Accepted

**Context:** OQ-4. A machine-parsed contract would ordinarily carry a version field.

**Decision:** Do not add one here. The parser fails closed on anything it does not recognize.

**Reasoning:** The block schema is defined by spec 031 FR-003/FR-004 and emitted by seven shipped
agent contracts. Adding a field is a change to *those* artifacts and belongs to a `/spec-update`
against 031, not to a unilateral change from a consumer. Fail-closed parsing is the safe behavior
with or without a version, so nothing in v1 is blocked by its absence.

**Consequences:** OQ-4 stays open as a cross-spec follow-up. If 031 later versions the block, the
runner's parser is the one place that must learn about it.

---

### D007 - Where the runner and `sdd-orchestrate` disagree, the runner is wrong

**Date:** 2026-08-31

**Status:** Accepted

**Context:** Two executors of one protocol invite divergence, and divergence in a review gate is
the failure mode with the worst blast radius: one executor approving what the other rejects.

**Decision:** Specs 031 and 032 are normative. Any behavioral difference is a runner defect, never
a runner feature. Semantic changes go through `/spec-update` against 031.

**Reasoning:** Without a tiebreaker written down, every disagreement becomes an argument about
which side is right, and the framework's autonomy story splits in two. Naming the authority up
front makes the conformance test meaningful rather than decorative.

**Consequences:** FR-015 and T017 exist to make this checkable. Every core module cites the 031 FR
it implements, so a future change to 031 has a findable set of call sites. Where 031 and 032
disagree with each other, 032's observed evidence wins.

---

### D008 - T017 is not viable as specified; the guard is a transcription test instead

**Date:** 2026-08-31

**Status:** Accepted

**Context:** T017 specified the conformance guard as "identical fixture responses driven through
the runner and through `sdd-orchestrate`". The maintainer required a read-only spike before
building on it. The spike found three independent blockers:

1. **No injection point.** `sdd-orchestrate` delegates through Claude Code's Agent tool. There is
   no supported way to feed scripted reviewer responses into those delegations, so the skill side
   of "identical fixture responses" cannot be constructed at all.
2. **The repo has already ruled the workaround inadmissible.** Spec 032's PLAN rejects "Scripted or
   mocked reviewers" because "a mock cannot produce the malformed-block and format-retry paths the
   protocol handles, so it would certify a circuit nobody exercised"
   ([032/PLAN.md:86](../032-autonomous-loop-residual-calibration/PLAN.md:86)). A T017 built on a
   scripted skill side would produce exactly the evidence this repo decided does not count.
3. **The one capture harness cannot do it.** `scripts/skill-eval.sh` runs a skill as a single
   prompt on stdin returning a response on stdout. It cannot drive a multi-turn delegating loop.

**Decision:** Do not force T017 with a test that would pass without proving anything. Replace it
with a **protocol transcription guard**: `runner/tests/conformance/PROTOCOL_TRANSCRIPTION.md`, a
clause-by-clause table mapping each 031 rule to the module that encodes it and the test that pins
it, plus `test_transcription.py`, which asserts the table stays honest (every named module
attribute exists, every named test file is collected) and checks the runner's model against the
**real recorded phase-1 artifacts** in specs 032 and 033.

**Reasoning:** A conformance test whose two sides are both the runner is worse than no conformance
test, because it produces the reassurance without the evidence. The replacement is weaker than a
true two-executor comparison and is stated as such. What it adds over the fallback the maintainer
described is the golden-artifact check: the runner's schema understanding is tested against files
that real subagent runs actually produced, not only against fixtures its own author wrote.

**Consequences:** **Risk R1 (transcription drift) is PARTIALLY mitigated, not eliminated.** Nothing
in the suite compares the two executors' behaviour on the same input; drift can still occur and
would be caught only by the table going stale, which the honesty test detects, or by a human
noticing. PLAN.md's risk table is updated accordingly. This guard also found a real divergence on
its first run — see D011.

---

### D009 - The test suite uses stdlib `unittest`, not pytest

**Date:** 2026-08-31

**Status:** Accepted

**Context:** TASKS.md wrote every `Verify:` clause as `python3 -m pytest ...`. pytest is a
third-party package.

**Decision:** The suite runs on stdlib `unittest`:
`python3 -m unittest discover -s runner/tests -t runner`. The `Verify:` clauses are corrected to
match.

**Reasoning:** AC-010 requires the suite to pass on a machine with nothing installed, and D001
requires the runner to add no mandatory dependency. Requiring pytest to run the runner's own tests
would contradict both — it would mean the containment proof itself needs an install.

**Consequences:** No parametrized fixtures; `subTest` covers the cases that needed them. The suite
runs anywhere `python3` runs, which is the whole point.

---

### D010 - The verdict block is parsed by a strict YAML subset, not a YAML library

**Date:** 2026-08-31

**Status:** Accepted

**Context:** The verdict and completion blocks are fenced YAML. PyYAML is a third-party dependency;
a full YAML parser also accepts anchors, aliases, tags, flow collections, multi-document streams
and implicit type coercion.

**Decision:** `sdd_runner/_miniyaml.py` implements only the grammar spec 031's blocks use and
rejects everything else on sight.

**Reasoning:** Two reasons, and the second matters more. It avoids a dependency (D001); and it
makes "unrecognized" and "rejected" the same thing by construction, which is what FR-003's
fail-closed requirement actually asks for. A permissive parser would silently accept shapes the
protocol never defined, which is the opposite of failing closed.

**Consequences:** A reviewer emitting valid-but-exotic YAML gets a synthetic REJECT and one format
retry. That is the intended trade: the protocol fixes the shape, and the parser enforces exactly
that shape.

---

### D011 - The verdict block's severity enum is closed; report vocabulary stays outside it

**Date:** 2026-08-31 (raised and resolved the same day)

**Status:** Accepted — **closed**

**Context:** Found by the D008 transcription guard on its first run. The canonical schema in
`skills/sdd-orchestrate/SKILL.md` fixes severity to `Critical | High | Medium | Low`, but a real
phase-1 run recorded `blocker`, `major` and `minor` in
[033/ORCHESTRATION.md](../033-task-verification-criterion/ORCHESTRATION.md). Two readings were open:
the registry rows were written in review-report language while the verdict blocks stayed canonical,
or a reviewer emitted a non-canonical severity and the phase-1 orchestrator accepted it.

**Decision (maintainer, 2026-08-31):** The machine-parsed verdict block stays **strict**.

- Canonical severity inside the block: **`Critical | High | Medium | Low`**. Closed enum.
- `blocker`, `major`, `minor` and the rest of the review-report vocabulary may appear in human
  narrative — prose above the block, rendered reports, summaries, and the human-readable
  Findings-registry rows. They are **not valid inside the verdict block**.
- A reviewer emitting one of them inside the block: the runner keeps failing closed.
- **No relaxation of the parser, no silent aliases, no implicit normalization.**

**Reasoning:** A parser that maps `blocker` to `Critical` makes the gate's own vocabulary
unfalsifiable — nobody can afterwards tell whether a reviewer used the schema or was quietly
corrected into it, which is the same class of defect as keying control flow on rendered prose
(commit `36c3b04`). Keeping the enum closed also keeps "unrecognized" and "rejected" the same
thing, which is what D010's strict subset parser is built on.

The root cause turned out to be findable and narrow. `agents/security-reviewer.md` already named
the vocabulary explicitly; `agents/domain-reviewer.md` and `agents/final-conformance-reviewer.md`
only pointed at "the canonical schema". Every non-canonical row in 033 is a
`final-conformance:CONF-*` row — the one reviewer whose contract omitted the enum. That is not
proof of which reading was true, and this decision does not claim it is; the artifact cannot settle
it either way. It is, however, enough to fix the thing that let the ambiguity exist.

**Consequences:**

- `skills/sdd-orchestrate/SKILL.md` now states the closed enum, the narrative/block boundary, and
  the no-aliases rule, and cites the 033 artifact as the reason.
- `agents/domain-reviewer.md` and `agents/final-conformance-reviewer.md` now name the enum. This is
  the behavioural fix: the contracts a reviewer actually reads no longer omit it.
- Spec 031's FR-003 carries a dated clarification. 031 is `Done`, so it is amended in place with a
  note rather than rewritten — the precedent is spec 032 amending 031's evidence matrix.
- `specs/features/033-task-verification-criterion/ORCHESTRATION.md` is **left exactly as it is**.
  It is the record of a run that happened; editing it to match a rule written afterwards would
  falsify history to make a document look consistent. Under the rule as now stated, its rows are
  registry narrative and therefore legitimate where they sit.
- The runner is **unchanged**. Its strictness was already correct; what changed is that the
  protocol now says so out loud.
- Four tests pin the boundary: the canonical four are accepted, the three report words are rejected
  *inside* a block, the same words are ignored *outside* one, and the enum tuple itself is fixed.

**What this does not resolve:** D008's R1. Closing D011 removes one known divergence; it does not
give the suite a way to compare the two executors on the same input. **R1 remains partially
mitigated, not eliminated.**


---

### D012 - `ACTIVE` alone does not mean a runner is alive; the document records pid and host

**Date:** 2026-08-31

**Status:** Accepted

**Context:** T013 has to satisfy two requirements that pull against each other: a concurrent
`ACTIVE` run must be rejected, and an interrupted run must be recoverable. After a SIGTERM the
document says `ACTIVE` in both cases, so nothing in 031's schema as the runner was writing it could
tell them apart. Left unresolved, either the runner refuses forever after any crash, or it walks
into a worktree a live runner already owns.

**Decision:** The State section records the writer's pid and host. Re-entry then resolves:

| Recorded | This runner does |
|---|---|
| `ACTIVE`, same host, pid alive | refuse — concurrent run (exit 15) |
| `ACTIVE`, same host, pid dead | resume — an interrupted run |
| `ACTIVE`, different host | **block** (exit 16) — cannot verify |
| `ACTIVE`, unreadable pid | **block** (exit 16) |

**Reasoning:** A liveness check that only works on one host is honest about its own limit. Guessing
that a remote pid is dead is exactly how two runners end up writing the same `ORCHESTRATION.md`,
and the cost of the conservative answer is one human confirmation. The block message says precisely
what to change (`ABORTED` + `resumable: yes`) so it is not a dead end.

**Consequences:** A machine that loses its hostname between runs blocks and needs a human. That is
the intended trade. The pid/host fields live in State, which 031 already describes as holding the
run's current attempt and counters, so no section was added or renamed.

---

### D013 - A run that processed every task but converged on none is not `DONE`

**Date:** 2026-08-31

**Status:** Accepted

**Context:** Found while building T013's tests, not by design review. The driver ended a run with
`DONE` once it had *processed* every runnable task — including a run where every review returned
`REJECT` and no task ever completed. The bug was invisible until resume existed, because nothing
read the result back.

**Decision:** `DONE` requires convergence: every runnable task must be in the completed set. A run
that processed everything without converging finishes `PAUSED`, `resumable: yes`, exit **17**
(`not-converged`), naming the tasks that did not converge.

**Reasoning:** Two independent reasons, and the second is the dangerous one. Reporting `DONE` after
a rejected review is a false claim on its face. Worse, a later re-entry reads `DONE`, treats the
run as finished and refuses to resume — so the false claim becomes permanent and silently discards
work that never landed.

**Consequences:** A new exit code, 17. The existing converge test still passes because it actually
converges; the reject-then-fix test now ends 17 instead of 0, which is the truthful outcome given
the driver has no fix cycle yet (that is T016's remaining scope).

---

### D014 - Two columns added to the Attempts and Findings tables, and why they are not new state

**Date:** 2026-08-31

**Status:** Accepted

**Context:** 031 FR-011 requires re-entry to rebuild counters without resetting them. The per-finding
counter counts *failed repairs*, which needs `repair_done`; and task completion needs an attempt row
distinguishable from a worker's mere response. Neither was persisted.

**Decision:** The runner writes 031's full documented column set for both tables, plus `Repair done`
in the Findings registry, and marks task completion with an explicit `task complete` attempt row
(lifecycle `VERIFIED`, outcome `DONE`) written only after every required reviewer approved. The
runner recognizes its own documents by these exact headers and blocks on any other.

**Reasoning:** Rule 4 of T013 is "rebuild the counters from persisted state **or block**". Persisting
what the runner already computes is the alternative to blocking on every re-entry. This is not
inventing state; it is writing down state that existed only in memory.

**Consequences:** A document written by the phase-1 executor has different columns and is refused
with a named reason rather than parsed on a guess. The first cut of this had a real bug — the
worker's `RESPONDED` row was indistinguishable from task completion, so resume skipped a task whose
review had rejected. The State-versus-Attempts cross-check caught it, and that cross-check stays:
when the two disagree, the runner blocks instead of choosing.

---

### D015 - The repair cycle is T025, not a re-opened T013

**Date:** 2026-08-31

**Status:** Accepted

**Context:** T013's description named "findings-to-tasks, re-review" among the driver's
responsibilities, but the `Verify:` clause it was closed against covered only the converge, resume
and concurrent-refusal cases. So T013 is genuinely met as written, and a capability its prose
promised is genuinely missing.

**Decision:** Add T025 for the repair / re-review cycle rather than re-open T013, and say in T025
why.

**Reasoning:** Re-opening a task whose stated criterion was met would make the checkbox mean
"someone later wanted more", which destroys the only thing a `Verify:` clause is for. Naming the
gap between a task's description and its criterion is the honest record, and it is also the useful
one: it says the description over-promised, which is a lesson for the next task written.

**Consequences:** T013 stays closed. T025 carries the cycle. The general lesson — a `Verify:`
clause narrower than its description will close a task with work left inside it — belongs in the
`Verify:` guidance of `specs/_templates/TASKS.md`, and is not changed here.

---

### D016 - Approvals are keyed by reviewer AND task

**Date:** 2026-08-31

**Status:** Accepted

**Context:** Found by T016's converge test, which suddenly reported three provider calls where four
were expected. Approvals were keyed by reviewer alone, so `domain`'s APPROVE of T001 satisfied the
freshness check for T002 whenever the tree fingerprint happened not to move between them.

**Decision:** The key is `<reviewer>@<task>`.

**Reasoning:** An APPROVE of T001's diff is not an approval of T002's work. Keying by reviewer
alone made the guard depend on the tree changing between tasks — true for a real worker, false for
any task that changes nothing, and false for the stub. A test suite that only passes because a
worker happens to write files is not testing the rule.

**Consequences:** One task's approvals cannot satisfy another's. Cross-task staleness — a later
task's change invalidating an earlier task's approval — is still NOT handled here; that is the
finalization freeze (031 FR-013, T014). Recorded so it is not mistaken for solved.

---

### D017 - The reviewable fingerprint excludes the loop's own bookkeeping

**Date:** 2026-08-31

**Status:** Accepted

**Context:** 031 FR-007 requires REJECT findings to become `TASKS.md` items, so the runner now
writes `TASKS.md`: a repair row on REJECT, a check-off when the finding resolves. Those writes
moved the reviewable fingerprint, which invalidated the approval the runner had just been given and
forced a re-review of a tree nobody had touched.

**Decision:** `ORCHESTRATION.md`, `run.jsonl`, `PR_DESCRIPTION.md` and `TASKS.md` are excluded from
the fingerprint — from the status walk **and** from `git diff HEAD`, via pathspec exclusions. The
first version excluded them from only the walk, and a tracked `TASKS.md` leaked back in through the
diff.

**Reasoning:** The fingerprint answers "has the implementation changed since this reviewer
approved it". Loop bookkeeping is not implementation, and 031 FR-013 already draws that line for
the closure freeze: lifecycle and evidence writes are audited but do not stale approvals.

**Consequences:** A reviewer finding about `TASKS.md` content does not move the fingerprint. That
matters at closure, not mid-loop, and closure is where 031's closure-delta check reads task content
directly (T014).

---

### D018 - A synthetic malformed-block finding is not repairable by a worker

**Date:** 2026-08-31

**Status:** Accepted

**Context:** A malformed verdict block fails closed to a synthetic `ORCH-MALFORMED-*` REJECT. Once
findings became repair tasks, the loop dutifully allocated a worker repair task for it — asking an
implementer to fix a reviewer's formatting.

**Decision:** Synthetic findings are flagged in the registry (`Synthetic` column) and are never
scheduled for repair. The next round simply re-reviews, and the reviewer's no-progress streak ends
the run if the malformed output persists.

**Reasoning:** No code change satisfies "return a block conforming to the canonical schema". The
required action is on the reviewer, so a repair delegation would burn budget on work that cannot
succeed, and the failed repair would then be counted against the per-finding cap as if the code
were at fault.

**Consequences:** A persistently malformed reviewer aborts on the reviewer streak cap after
`max-iterations` rounds, with the raw responses retained. **031's single format re-request is still
not implemented** — the parser fails closed on the FIRST malformed block instead of re-requesting
once with the schema and the validation error. That is a real divergence from the protocol and it
is recorded as an open gap, not as a decision.

---

### D019 - The runner delegates the owning lifecycle skills and reads their verdict block

**Date:** 2026-08-31

**Status:** Accepted

**Context:** 031's termination contract requires the run to `/spec-review` (require its Pass),
`/spec-close` (require its gate) and `/pr-description` before `DONE`, while forbidding the loop
from writing a spec `Status`: "the loop may invoke the owning lifecycle skills; that is not a
direct transition." A Python process cannot invoke a Claude Code skill directly.

**Decision:** Each lifecycle step is a **delegation** whose system prompt is the step's own
`SKILL.md` when the repo ships it, prefixed by a deterministic `# lifecycle:<skill>` line. The
runner requires an `APPROVE` in the **existing** canonical verdict block, and treats anything else
— REJECT, malformed, missing — as a refusal that stops the run with the skill's reason.

**Reasoning:** Reusing the verdict block avoids inventing a second machine contract, which D010's
strict parser would then have to learn and 031 would have to bless. It also inherits the
fail-closed behaviour for free: an unreadable lifecycle response is a refusal, never a pass. The
runner still never sets a `Status`; the delegated session's owning skill does, which is exactly the
distinction 031 draws.

**Consequences:** A refusing skill leaves the run at `CLOSURE_NOT_PROVEN` (exit 18) with the freeze
preserved, so re-entry resumes into the remaining steps. Against the stub backend no skill actually
runs, so these tests prove the runner's handling of a gate, not the skills' own behaviour — stated
in T014 rather than implied.

---

### D020 - Freeze, allowlist and closure delta, defined

**Date:** 2026-08-31

**Status:** Accepted

**Decision:** Three terms, fixed:

- **Freeze** — the instant the run records the implementation fingerprint every required reviewer
  has approved, plus a per-path content map of the tree. It happens only after every state
  condition holds, after stale approvals are refreshed, and after `final-conformance-reviewer`
  approves. Nothing may be delegated to a lifecycle skill before it.
- **Closure allowlist** — the only paths that may change after the freeze: the generated
  `ORCHESTRATION.md`, `run.jsonl`, `PR_DESCRIPTION.md` and `CALIBRATION.md`; `SPEC.md` **only**
  when the change is confined to its `## Status` section; `TASKS.md` **only** for checkbox
  bookkeeping.
- **Closure delta** — the observed difference between the frozen map and the final tree, each path
  classified with the rule that classified it.

**Reasoning:** The classifier is deliberately asymmetric: it calls something allowed only when it
can name the rule, and everything it cannot classify is unexpected. That is the only direction in
which a mistake is safe.

**Consequences:** A change the allowlist does not cover returns the run to REVIEW (exit 18) naming
the paths. `SPEC.md` and `TASKS.md` are checked at the level of the diff's content, not just the
path, so a lifecycle skill that edits a requirement while updating a status does not slip through.

---

### D021 - The runner marks a converged task's checkbox

**Date:** 2026-08-31

**Status:** Accepted

**Context:** 031's first DONE condition is "every `TASKS.md` item is checked", read from the file.
Its step 2 says the orchestrator *verifies* the claimed checkbox, implying the worker sets it. A
worker that does not touch `TASKS.md` would then make the condition permanently unmeetable.

**Decision:** The runner checks a task's box when it converges — worker `DONE` plus every required
reviewer's APPROVE on the same fingerprint — and unchecks it if a later re-review stales that
approval and rejects.

**Reasoning:** The runner already owns repair-task check-offs (031 FR-007), so not owning ordinary
ones would be inconsistent. And the box has to mean something a re-entry can trust: leaving a task
checked after its approval was withdrawn is what would make a resume skip work that is no longer
done.

**Consequences:** `TASKS.md` checkbox writes are lifecycle bookkeeping, allowed by the closure
allowlist (D020) and excluded from the reviewable fingerprint (D017). The runner sets what 031 asks
it to verify — a real, narrow divergence from the phase-1 division of labour, recorded here rather
than left implicit.

---

### D022 - `git status` needs `-uall`, or new files are invisible to the fingerprint

**Date:** 2026-08-31

**Status:** Accepted (a defect fix, recorded because it changes what the guard can see)

**Context:** Found by T014's stale-approval test, which refused to observe any staleness. `git
status --porcelain` collapses a wholly-untracked directory to a single `?? src/` entry, so a worker
that created `src/` and wrote files into it produced **no fingerprint change at all** — and
`git diff HEAD` does not cover untracked files either.

**Decision:** Every status read that feeds a fingerprint, a tree map or the entry gate's dirty-tree
check passes `-uall`.

**Reasoning:** The bug silently disabled the exact guard this feature exists for: approvals could
never go stale, so a run could close over work no reviewer had ever seen. It was invisible in every
earlier test because the stub backend wrote nothing.

**Consequences:** The entry gate now also sees individual untracked files, which is stricter and
correct. This is the second time a test that mutates the tree found a defect a no-op stub could
not; that is worth remembering when writing the next fixture.

---

### D023 - Spec updated: the exit-code contract now lists all eleven codes

**Date:** 2026-08-31

**Status:** Accepted

**Context:** FR-013 named six non-zero exit codes. The implementation has ten, the four extras
having been added as each task discovered an outcome a scheduler must be able to tell apart:
`15 concurrent-run` and `16 state-unresumable` (T013), `17 not-converged` (T013/T014), and
`18 closure-not-proven` (T014). The spec had fallen behind its own implementation, which is the
quiet way a contract stops being one.

**Decision:** FR-013 lists all eleven codes explicitly and carries a dated amendment note. Nothing
in the code changes.

**Reasoning:** A scheduler branching on the code alone is the point of FR-013, and it cannot branch
on codes the requirement does not name. Folding any of the four into an existing code would have
been worse than adding them: a corrupt state file would then be indistinguishable from a product
question waiting on a human, and the two need opposite responses.

**Consequences:** T023 must document all eleven, not six — its `Verify:` is updated accordingly.
No task is invalidated; this is the spec catching up with observed behaviour.

---

### D024 - Spec updated: AC-007 says what is actually observed about interruption

**Date:** 2026-08-31

**Status:** Accepted

**Context:** AC-007 read "a run killed with SIGTERM mid-delegation". The suite never delivers a
signal: it constructs the state an interruption leaves behind — an `ACTIVE` record whose writing
process is gone — and re-enters from there.

**Decision:** AC-007 now says "interrupted", and states in the criterion itself that the observation
is made against the resulting state rather than by signalling a live run.

**Reasoning:** The state is the thing re-entry actually reads, so testing it is testing the real
mechanism. But the criterion claimed a stronger observation than the evidence supports, and a
criterion that overstates its own evidence is exactly what conformance review exists to catch.
Better to narrow the claim than to let a future reader believe a signal was delivered.

**Consequences:** T013 stays closed — its evidence matches the amended criterion. What remains
unobserved is the path: a real signal arriving between a dispatch and its state write. That is a
residual under R5 and is named there rather than pretended away.

---

### D025 - Spec updated: T011 is reopened; redaction never covered ORCHESTRATION.md

**Date:** 2026-08-31

**Status:** Accepted

**Context:** Found by the final readiness review and reproduced in execution. AC-012 requires the
sentinel absent from `run.jsonl` **and** `ORCHESTRATION.md`. Redaction is applied only in the
`run.jsonl` writer. On the human-gated escalation path the worker's question is copied verbatim
into the `Escalations` section, so a secret an agent echoes lands in the state file in clear:

```
outcome: 11 PAUSED
ORCHESTRATION.md   sentinel present: True
run.jsonl          sentinel present: False
```

T011's `Verify:` asserted only the `run.jsonl` half, so it passed while the criterion it claims to
cover did not.

**Decision:** Reopen T011 with a `Verify:` that matches AC-012 — a run with a human-gated BLOCKED
question carrying the key's value, and the value absent from both files. AC-012's wording is
**unchanged**: the criterion was right and the implementation falls short of it. The fix is not
applied by this update, which is a spec change, not an implementation.

**Reasoning:** Reopening is correct here and was not correct for T013 (D015). The difference is
exactly whether the closed criterion demonstrates what the task claims to cover: T013's did, and
its description merely promised more; T011's did not. A task whose `Verify:` cannot fail when its
`Covers:` is violated was never really closed.

**Consequences:** T011 is `[ ]` and `[NEEDS REVIEW]`. AC-012 is not met, and the SPEC says so in
place rather than only here. This is the **second** time a `Verify:` narrower than its `Covers:`
hid unfinished work, and the first time it hid a credential leak — worth carrying into the
`Verify:` guidance of `specs/_templates/TASKS.md`, which this update deliberately does not change
(that template belongs to spec 033, not to this feature).

---

### D026 - Spec updated: T018 is `not observed` and gates `Done`, not the work

**Date:** 2026-08-31

**Status:** Accepted

**Context:** T018 runs the two E2E scenarios against a real provider. On this machine
`import claude_agent_sdk` raises `ModuleNotFoundError` and `which codex` finds nothing, both
verified 2026-08-31. T022's overnight run inherits the same block.

**Decision:** T018 is marked `[~] NOT OBSERVED` with the environment evidence recorded, and
**gates promotion to `Done` rather than blocking the remaining work**. T022 is marked blocked by
it. No claim is made about behaviour nobody has seen.

**Reasoning:** The precedent is this repository's own: spec 039 stopped at `Implemented` rather
than `Merged` because its symlink ladder could not execute off Windows, and said so. Blocking a
whole feature on a CLI nobody has installed is how DEBT-002 came to exist; reporting the gap and
gating the promotion is how 039 avoided repeating it.

**Consequences:** Three things stay unseen behind this task and must not be implied anywhere: an
`agents/*.md` prompt reaching a real provider, an owning lifecycle skill actually executing, and
`PR_DESCRIPTION.md` appearing on disk. R10 in PLAN.md carries them. The feature can reach
`In Review` and `Implemented`; it cannot reach `Done` until T018 is observed.

---

### D027 - `run.jsonl` is gitignored; `ORCHESTRATION.md` is committed

**Date:** 2026-08-31

**Status:** Accepted

**Context:** T023 had to settle what happens to the two per-run artifacts the runner writes into a
feature folder. Both are new file types for this repository.

**Decision:** `specs/features/*/run.jsonl` is added to `.gitignore`. `ORCHESTRATION.md` is not, and
stays committed as it already is for specs 032 and 033.

**Reasoning:** They answer different questions. `ORCHESTRATION.md` is the durable record of what a
feature's autonomous run decided — the thing a human reads months later, and the thing a re-entry
parses; the repo already keeps two of them. `run.jsonl` is the transcript of one invocation, it is
append-only across re-entries, and it is machine-shaped. Committing it would put unbounded churn in
the spec trail for evidence that is only useful while the run is live or immediately after.

**Consequences:** A run's machine log is local to the machine that produced it. If a specific
`run.jsonl` is ever needed as evidence for a review, it has to be attached deliberately — the
`--out`-style copy is not implemented and is not needed until someone asks. Note this cuts against
one reading of AC-012, whose sentinel grep covers `run.jsonl`: that check runs against the file on
disk during the run, which is unaffected by whether git tracks it.

---

### D028 - Security review findings SEC-001..SEC-004, and how each was answered

**Date:** 2026-08-31

**Status:** Accepted

**Context:** T020's review found four issues. None was remotely exploitable — the runner exposes no
network and takes no end-user input — but three of them punched holes in controls this feature
claims to provide, and one of those is the last gate before `DONE`.

**Decision, per finding:**

- **SEC-001 (Medium) — the closure allowlist matched by basename, repo-wide.** Fixed. An artifact
  is generated because of *where* it is, not what it is called: `GENERATED` names are now allowed
  only inside the feature folder, and a `src/PR_DESCRIPTION.md` or `lib/run.jsonl` is `unexpected`.
- **SEC-002 (Medium) — the recorded allowed-path scope was never checked.** Fixed, narrowly. 031
  FR-008 requires an out-of-scope write to fail closed, and every attempt recorded `[repo]` with no
  comparison, so the field was decorative. The reviewers' own contracts say "Read-only — it never
  modifies code", so their recorded scope is now **empty** and any fingerprint movement during
  their delegation is an unattributed write: `ABORTED`, `resumable: no`, per 031's rule that
  unexplained out-of-scope writes are terminal and provenance is never guessed. Workers and
  lifecycle skills legitimately write and keep the repo scope.
- **SEC-003 (Medium) — the redaction hint list was narrower than real variable names.** Fixed.
  `API_KEY`/`TOKEN`/`SECRET`/`PASSWORD`/`CREDENTIAL`/`AUTH`/`SESSION_KEY` missed `OPENAI_KEY`,
  `DB_PASS`, `GH_PAT`, `PRIVATE_KEY`. Widened to substrings (`KEY`, `PASS`, `PWD`, `PAT`,
  `PRIVATE`, `SIGNATURE`, `SIGNING`, …) with a `SAFE_NAMES` set for the everyday variables that
  collide (`PWD`, `PATH`, `KEYMAP`, …).
- **SEC-004 (Low) — the Codex backend passes the prompt in `argv`**, readable by any process on the
  host. **Not fixed**, documented in `codex.py` where an implementer will meet it. The fix is
  stdin, and whether that CLI accepts stdin is exactly what DEBT-001 says nobody has checked, so it
  lands with that verification rather than on a guess.

**Reasoning:** SEC-001 and SEC-002 are the same failure in two places — a control that records
something and never compares it. SEC-003 is the residual the T011 fix explicitly left behind, and
the asymmetry decides it: a false positive costs one over-redacted string in a maintainer's log,
a false negative costs a credential in clear.

The SEC-002 fix is deliberately narrow. A per-task file allowlist would be a better control and the
spec never defined one; inventing it here would be scope creep. Read-only agents are the case where
the contract is already unambiguous, so that is where enforcement went.

**Consequences:** `[repo]` is still the scope for every writing agent, so **a worker may still
write anywhere in the repository and nothing notices until the closure delta** at the end of the
run. That is a real remaining gap in 031 FR-008 coverage, recorded here rather than implied to be
closed. Nine tests pin the four behaviours; reverting any of the three fixes fails them.

---

### D029 - Python review: four defects fixed, two quality findings accepted

**Date:** 2026-08-31

**Status:** Accepted

**Fixed**, because each is a defect rather than a preference:

- **PY-1** `closure._hash_file` caught `FileNotFoundError`/`IsADirectoryError` and let every other
  `OSError` escape. An unreadable file would raise out of the closure audit — the last gate before
  `DONE` — instead of being classified. It now returns `<unreadable>`, deliberately distinct from
  `<deleted>` so the two cannot be confused.
- **PY-2** `ClaudeBackend.run` wrapped **every** exception as `TransportError`. A `TypeError` in
  that file would have been retried three times under the backoff policy and then reported as a
  provider failure, with the real defect invisible. Programming errors now propagate.
- **PY-3** `state.py` imported the private `log._secret_values` lazily inside a method, with no
  import cycle to justify either the privacy violation or the lateness. Promoted to a public
  `secret_values` and hoisted to the module header.
- **PY-4** dead scaffolding in `test_finalization` (`loop_holder`, assigned and never read).

**Accepted, not fixed:**

- **`loop.py` is 981 lines across 41 methods in one class.** Its own docstring says it is
  "composition only… decides ORDER, not semantics", and it has outgrown that: fingerprinting, state
  persistence, delegation, the task cycle, escalation, findings-to-tasks, finalization, freeze,
  closure and lifecycle now live together. The natural seam is a `Finalizer` holding everything
  from `_state_preconditions` to `_close`, which would take the file under 600 lines.
- **Type annotations stop at the modules written last.** `blocks`, `budget`, `counters`,
  `escalation`, `_miniyaml` and `retry` annotate their public functions; `loop`, `state`, `resume`,
  `closure`, `gate`, `tasks` and `log` have none. The gradient tracks the order they were written,
  which is its own finding about how the later tasks were run.

**Reasoning for not fixing those two:** both are refactors of code that is green and covered, and
this task is a review gate, not a redesign. Doing them here would put a large untested-by-design
diff between the review and its evidence. Recorded so that "nobody noticed" is not available as an
explanation later.

**Consequences:** the two accepted findings belong in a follow-up, not in `KNOWN_DEBT.md` — that
register is for claims the repo makes that nobody has checked, and neither of these is a claim.

---

### D030 - Spec updated: AC-001 and AC-002 downgraded to what this machine can observe

**Date:** 2026-08-31

**Status:** Accepted

**Context:** `/spec-review` returned **Partial** twice. AC-002 had **no** observed evidence at all —
its only coverage was T018 and T022, both blocked because `claude_agent_sdk` is not installed and
`codex` is not on PATH. AC-001 was half observed: its converge/no-commit half passes against the
stub, but *"With the Claude backend"* and *"and a `PR_DESCRIPTION.md`"* had nothing behind them.
Everything implementable here is implemented, tested and reviewed; the gap is an environment, not
unfinished work.

`docs/KNOWN_DEBT.md` states the only legitimate way through: *"A spec may close with an unmet
acceptance criterion only if the criterion is downgraded in its `SPEC.md` (with a decision
recording why) **and** the item lands here."* This is that decision.

**Decision:**

- **AC-001** drops two clauses — the backend name and `PR_DESCRIPTION.md` — and keeps what the stub
  demonstrates: non-interactive exit `0`, unstaged tree on a non-default branch, an
  `ORCHESTRATION.md` matching 031's schema, a `run.jsonl`, and no runner-created commit.
- **AC-002** is rewritten from *"launched from `cron`, exit 0"* to the property the code can
  demonstrate here: no TTY required, stdin never read, nothing ever prompted, and an exit code a
  scheduler can branch on.
- **[[DEBT-009]]** is opened, naming all four unobserved things and stating that the spec may reach
  `In Review` and `Implemented` but **not `Done`** until they are observed.
- **AC-002's downgrade note says the uncomfortable sentence out loud** — *"nobody has watched this
  runner start from `cron`"* — rather than leaving it to be inferred from a narrower criterion.
  A downgrade that reads as if nothing was lost is the failure this whole mechanism exists to stop.
- **Not changed:** every other AC, all 18 FRs, and the spec `Status`, which belongs to
  `/spec-review`.

**Reasoning:** The alternative was leaving two criteria permanently unmet and the spec frozen at
`In Progress` until someone installs an SDK — which does not make the runner more verified, it just
makes the record less legible. Spec 039 set the precedent: it stopped at `Implemented` rather than
`Merged` because its symlink ladder could not execute off Windows, said so, and moved on.

The honest cost of this decision, stated plainly: **this repository now asserts that a phase-2
runner exists while nobody has watched it talk to a provider.** That assertion is only defensible
because DEBT-009 carries it in the register the framework reads, and because `Done` stays blocked.

**Consequences:**

- T018 and T022 stay `[~] NOT OBSERVED` and now cite DEBT-009 as well as D026. Neither is
  over-implemented; neither is abandoned.
- No completed task needs revisiting: nothing was implemented *for* the removed clauses.
- New risk: a reader of `SPEC.md` alone now sees two criteria that look met. The mitigation is that
  both carry their downgrade note inline, `FINAL_CONFORMANCE_REPORT.md` records the original
  verdict, and DEBT-009 is in the register — three places, none of them optional reading.
- `/spec-review` can now return `Pass` on the criteria as written. That is the point of the
  mechanism, and it is also exactly why the downgrade had to be this explicit.

---

### D031 - `--stub-script`: the end-to-end path is observable without a provider

**Date:** 2026-08-31

**Status:** Accepted

**Context:** After D030 downgraded AC-001, its remaining clause — *"runs from a non-interactive
shell with no TTY (`</dev/null`) to exit `0`"* — still had no evidence, because the stub backend
could not be driven from the CLI: `--backend stub` resolved with an empty script and exited 14 on
the first dispatch. So the criterion the downgrade was meant to make observable stayed unobservable,
and the downgrade achieved nothing.

Worse, the same gap had already cost something. Every integration test built `Loop` in process,
skipping argument parsing, the order backends are resolved in, and the exit-code mapping. A
`--dry-run` regression lived in exactly that untested strip through three review passes: the flag
resolved a backend before printing the plan it exists to print, so on a machine with no Agent SDK —
the machine AC-010 says must work — it exited 14 without ever reaching the plan.

**Decision:** Add `--stub-script FILE`, a JSON script of responses for `--backend stub` (a list, or
an object keyed by agent). Add `test_cli_e2e.py`, which spawns `python3 -m sdd_runner` in a real
subprocess with stdin closed. Restore nothing in `SPEC.md`: AC-001 as D030 left it is now met, and
the two clauses D030 removed — the Claude backend and `PR_DESCRIPTION.md` — stay in
[[DEBT-009]] where they belong.

**Reasoning:** The alternative on the table was downgrading AC-001 a second time. Degrading the
same criterion twice to accommodate a limitation with a cheap fix is how a spec ends up describing
whatever happens to be true rather than what was required — and the `--dry-run` finding is the
argument: the only routine nobody covered is precisely where the defect got in.

"No TTY" is now a property of the process rather than a claim about it: the subprocess is spawned
with `stdin` on `/dev/null`, so a runner that read stdin would fail rather than proceed.

**Consequences:**

- New CLI surface, deliberately narrow: `--stub-script` is refused for any backend but `stub`, and
  its loader accepts exactly two shapes, rejecting everything else **before** a run starts. Five
  malformed-input cases are pinned by tests that also assert no `ORCHESTRATION.md` was created.
- AC-001 and AC-002 are now met as written. **[[DEBT-009]] narrows but does not close**: what is
  observed is the CLI converging against a *scripted* backend. A real provider, a real lifecycle
  skill and `PR_DESCRIPTION.md` remain unseen, and `Done` stays blocked on them.
- 186 tests. The eight new ones fail if `--dry-run` resolves a backend again, or if
  `--stub-script` is ignored — both verified by reverting each change.

---

### D032 - QA review: three test gaps, and the one that matters most

**Date:** 2026-08-31

**Status:** Accepted

**Context:** `/qa-review` compared the 14 edge cases SPEC.md declares against what the suite
actually exercises, and checked every module for direct coverage.

**Fixed:**

- **`_miniyaml` had no tests of its own.** Its entire purpose is rejecting YAML features a full
  parser would accept, and it was covered only indirectly through `blocks` — which, by
  construction, sees the shapes that *are* accepted. Nineteen rejection cases added, plus an
  assertion that `MiniYamlError` is the only failure mode, so a malformed document can never reach
  a caller as some other exception type.
- **The PY-2 fix was asserted, not demonstrated.** D029 recorded that programming errors no longer
  get laundered into `TransportError`; nothing tested it. It does now, and reverting the guard
  fails five tests.
- **`--notify` had never been a real command.** Every test passed a Python callable, so the
  declared edge case — the sink exits non-zero, hangs, or does not exist — was unexercised. It now
  runs as a real script through the CLI, including the assertion that agent text never reaches a
  shell.

**Reported, not fixed:** SPEC.md declares *"`TASKS.md` is edited by a human while the run is in
flight"* as an edge case, and **neither the spec nor the code says what should happen**. The runner
re-reads `TASKS.md` at entry and writes repair rows into it mid-run, so a concurrent human edit is
a real lost-update window. Inventing a behaviour here would be inventing protocol; it belongs in a
follow-up with a decision of its own.

**Reasoning:** The second item is the one worth remembering. D029 stated a fix in a decision log
and moved on, and that is precisely the shape of the failure this feature has hit three times now —
T013's description, T011's `Verify:`, and now a decision entry. A claim recorded in prose is not
evidence, whichever document it lives in.

**Consequences:** 202 tests. The `TASKS.md` concurrent-edit window is a known, unspecified gap.
