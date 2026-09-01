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

**Status:** Amended by D034 (source remains gated; execution/conformance moves to follow-up)

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

**Status:** Superseded in part by D034 (040 now implements only the retained deterministic core)

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

**Status:** Superseded by D034 for spec 040; retained as provider/finalizer follow-up input

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

**Status:** Superseded by D034 for spec 040; retained as provider/finalizer follow-up input

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

**Status:** Amended by D034 (exit 18 is reassigned to missing core completion evidence)

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

**Status:** Superseded by D034; T018/T022 move out of spec 040

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

**Status:** Superseded for the current acceptance surface by D034; retained as historical evidence

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

---

### D033 - Spec updated: 040 is EXPERIMENTAL, its conformance verdict is PARTIAL

**Date:** 2026-08-31

**Status:** Accepted; audit disposition superseded by D034, classification/verdict retained

**Context:** An architecture review found nine defects. All nine were re-verified against the code
before being recorded here; none was taken on description alone. Two of them are unmet functional
requirements **of this spec**, which three review gates — `/security-review`, `/qa-review` and
`/spec-review` — did not catch. That is the finding behind the findings: those three passes were
performed by the session that wrote the code, and F-3 of the conformance report said so at the time.

**Decision:**

- Spec 040 is classified **EXPERIMENTAL**. A `## Classification` block states it at the top, above
  everything else, because a reader who stops after the status line must not walk away believing
  this is a supported way to run unattended work.
- The final conformance verdict is revised from PASS-as-written to **PARTIAL**.
- The nine findings are recorded as **AUDIT-1..AUDIT-9** in a new SPEC section, each with its
  location and severity. AUDIT-1, AUDIT-2, AUDIT-7 and AUDIT-8 are High.
- **FR-005 is marked NOT MET** and **FR-006 PARTIALLY MET**, in place. AUDIT-2 is not a limitation:
  FR-005 requires the two executors to resume each other's runs, and `resume.inspect` refuses a
  phase-1 document outright.
- **AUDIT-9**: real provider execution, lifecycle delegation and closure automation move to a
  follow-up spec, added to Non-goals. What stays is the deterministic core and the stub; Claude
  stays optional and lazy, Codex stays gated.
- **T018 and T022 are BLOCKED**, not merely unobserved, until the architecture review is approved.
- Eight completed tasks are marked `[NEEDS REVIEW]`. **No task is un-checked and no code changes**:
  this update alters the record, not the runner.
- The lifecycle `Status` stays `In Review`. Only `/spec-review` may move it, and this is not that
  gate — but a re-run against these findings would not return `Pass`.

**Reasoning:** The instinct to fix nine defects immediately is the wrong one here. Four of them —
baseline enforcement, cross-executor resume, fingerprinting across commits, and the provider
session's permissions and timeout — are design questions, not bugs with obvious patches. AUDIT-2 in
particular cannot be "fixed" without deciding whether FR-005's requirement or the runner's
fail-closed refusal is the thing that was wrong. Patching first would encode that decision by
accident.

Blocking T018 and T022 follows from the same reasoning and is worth stating plainly: spending real
tokens now would produce evidence about a configuration nobody intends to ship, and would attach
the word "observed" to a runner that can report `DONE` without verifying anything (AUDIT-1), miss a
commit made mid-delegation (AUDIT-7), and run a provider session with edit permissions and a
timeout that does not fire (AUDIT-8).

**Consequences:**

- Eight tasks carry `[NEEDS REVIEW]`; none is over-implemented, and nothing built for a removed
  requirement. The work stands, its claims do not.
- `FINAL_CONFORMANCE_REPORT.md` is revised to PARTIAL and cites this decision.
- [[DEBT-009]] is unchanged and still open — it is about what has not been observed, while these
  findings are about what has been observed and is wrong.
- The follow-up spec inherits AUDIT-9 plus the four High findings that touch the provider path.
- **New risk:** nine open findings against a codebase with 202 green tests is a specific kind of
  trap — the suite tests what was built, thoroughly, and the audit found what was never questioned.
  Recorded as R12 so the green suite is not mistaken for coverage of these.

---

### D034 - Architecture option A: stabilize the core and move the provider/finalizer boundary

**Date:** 2026-08-31

**Status:** Accepted

**Context:** D033 paused implementation after AUDIT-1…AUDIT-9. The subsequent architecture review
found two recurring causes: controls were recorded without gating completion, and the external
provider boundary was made stricter than spec 031 without an explicit ownership decision. It
recommended option A: keep the tested deterministic core, close the cheap core controls, narrow
the unsafe cross-executor promise, and give provider/lifecycle behavior a separate spec.

This decision is intentionally made before code changes. It answers the ambiguity behind AUDIT-2
and names the code seam behind AUDIT-9, so implementation cannot choose either architecture by
accident.

**Decision:**

1. **Spec 040 ends at deterministic core convergence.** Its supported backend is `stub`. The seam
   is `Loop._finalize`: 040 verifies completion evidence and records its terminal result; a
   follow-up `Finalizer` owns provider-backed lifecycle skills, closure delta and PR description.
2. **A baseline is mandatory for `DONE`/exit `0`, not for every invocation.** Dry-run, inspection
   and resumable work may start without `--baseline`; convergence without a declared green,
   non-mutating baseline returns completion-evidence failure (exit `18`). `NOT DECLARED` is never a
   successful observation. `DONE` is the 040 **core run result** and never means or writes lifecycle
   `Status: Done`; the follow-up finalizer owns that transition.
3. **FR-005 is narrowed to shared readability plus same-executor re-entry.** The runner must parse
   enough of a foreign `ORCHESTRATION.md` to identify its writer and explain the refusal, but it
   must not reconstruct or continue another executor's counters and attempt lifecycle. A versioned
   cross-executor hand-off would require a future compatibility spec.
4. **The core fixes retained by 040 are AUDIT-1, AUDIT-5, AUDIT-6 and the core portion of AUDIT-7.**
   They become T028…T031: baseline gate, contained feature path, atomic ownership and a fingerprint
   containing `git rev-parse HEAD`.
5. **AUDIT-9 becomes an enforceable boundary task (T032).** A 040 stub run emits no lifecycle
   dispatch, closure automation or PR-description evidence. Existing provider/finalization source
   may remain temporarily, but it is not supported or accepted as 040 evidence.
6. **AUDIT-3, AUDIT-4, the provider-attribution half of AUDIT-7, and AUDIT-8 move to the provider
   follow-up.** That spec owns `deep-reasoner` routing, canonical format retry, writing-session path
   scope, attribution and policy for history mutations, Claude tool permissions and timeout,
   observed SDK behavior, Codex verification, lifecycle and closure. Former tasks T018/T022 move
   with it and must not be run as 040 evidence.
7. **Claude remains optional/lazy and Codex remains gated.** Keeping their source does not create a
   functional requirement or a parity claim in 040.
8. **Classification and lifecycle do not change.** Spec 040 remains EXPERIMENTAL, `In Review`, and
   PARTIAL until T028…T032 pass and T033 supplies independent conformance evidence.

**Reasoning:**

- Cross-executor resume cannot be made safe by accepting more Markdown. Writer-specific columns,
  counter reconstruction and attempt provenance need a versioned hand-off; D014's refusal is the
  correct implementation once the requirement stops promising the opposite.
- Baseline, containment, atomic ownership and `HEAD` fingerprinting are deterministic controls
  whose correctness can be proved with local subprocesses and Git. Deferring them with the provider
  work would leave the core unsafe for no architectural benefit.
- Auto-resolution, format retry, writer scope, SDK permissions and lifecycle closure exist only in
  relation to a real provider session. Fixing them in 040 without being able to observe that path
  would repeat the pattern that produced D033.
- Cutting at `_finalize` uses the natural code boundary already identified by the review and gives
  the follow-up one coherent owner instead of scattering provider behavior through core criteria.

**Consequences:**

- SPEC gains AC-015…AC-019 and TASKS gains five implementation tasks plus an independent
  conformance task. No runner code changes in this `/spec-update`.
- The old acceptance and conformance evidence remains historical, but it cannot promote the
  corrected contract. `FINAL_CONFORMANCE_REPORT.md` stays PARTIAL.
- T004's foreign-writer refusal is no longer `[NEEDS REVIEW]`; T008, T018 and T022 are not 040
  conformance evidence; T012/T013/T014 are followed by explicit corrective tasks rather than
  silently reopened.
- The follow-up spec has a bounded input ledger in TASKS.md but is **not created by this update**.
  Creating it is a separate `/spec-create`, so its number, lifecycle and acceptance criteria are
  not invented inside spec 040.
- After this decision the next implementation command may work only T028…T032. It must not repair
  or exercise the real provider path under 040.

---

### D035 - Reconcile the post-D034 audit-fix pass with the current contract

**Date:** 2026-08-31

**Status:** Accepted

**Context:** An implementation pass applied changes for AUDIT-5, AUDIT-6, AUDIT-7 and AUDIT-8, then
appended a second decision and task both numbered `034`/`T028`. It was working from the pre-D034
interpretation: its report said AUDIT-1 and AUDIT-2 still needed a spec decision. The canonical
D034 had already made both decisions — baseline is mandatory for core `DONE`/exit `0`, and FR-005
is narrowed to shared readability plus same-writer re-entry — and had assigned T028…T032.

The implementation itself is preserved. This decision repairs the traceability collision and
grades the evidence against the stronger current ACs rather than against the stale task labels.

**Implementation observed:**

- **AUDIT-7 — the fingerprint now includes `HEAD`.** It was built from `git status --porcelain`
  plus `git diff HEAD`, both of which measure the delta *from* HEAD. Reproduced before fixing: a
  commit made two fingerprints either side of a real change come out byte-identical. Every
  approval, the freeze and the closure delta rest on this value, which is why it was the highest
  priority despite being one line. This implements T031's mechanism, but the new tests exercise
  `fingerprint()` directly; they do not yet prove AC-018's end-to-end fail-closed approval
  invalidation.
- **AUDIT-8 — the session boundary.** `anyio.move_on_after` around a synchronous `anyio.run` is a
  cancel scope outside an event loop: it cancelled nothing, so the timeout never fired and a hung
  session would hang the runner. The deadline is now `anyio.fail_after` inside the coroutine.
  `allowed_tools` is declared (`Read, Grep, Glob, Edit, Write, Bash`, with a read-only variant)
  instead of inherited from whatever the host exposes. `_options` was extracted so the
  configuration is testable without the SDK installed. This is out-of-scope provider hardening
  under D034, not 040 conformance evidence; the backend remains unobserved.
- **AUDIT-6 — the state path is claimed with `O_CREAT|O_EXCL`.** `os.path.exists` followed by a
  write is a race the pid/host check cannot close, because that check only sees a run that already
  wrote its state. The new test proves the exclusive create bites, but not AC-017's synchronized
  two-process race and single-dispatch outcome.
- **AUDIT-5 — `--feature` is checked with `abspath` and `commonpath` against the repository.** This
  blocks absolute and `..` escapes, but it does not satisfy the D034 contract: AC-016 requires
  real-path containment under `specs/features/`, including a symlink escape.

**Found while fixing:** `anyio` was imported directly by the backend and declared nowhere. It is
now in the `claude` extra and in `preflight`, so its absence produces the install hint rather than
a bare `ImportError` mid-run.

**Reconciliation:**

- **AUDIT-1 is decided but not implemented:** T028 and AC-015 remain open.
- **AUDIT-2 is resolved by D034 without a runner patch:** T004 remains complete under the narrowed
  FR-005.
- **T029 remains open** because containment is only partial.
- **T030 and T031 remain open with their mechanisms implemented but current Verify clauses not yet
  met.** Their missing evidence is explicit; neither is closed from the 214-test count alone.
- **AUDIT-8 stays in the follow-up.** The source hardening and new optional `anyio>=4` dependency
  are recorded, but do not pull Claude execution back into 040.
- **AUDIT-3/AUDIT-4 and provider attribution for AUDIT-7 remain follow-up scope; AUDIT-9 remains
  T032 plus the follow-up `Finalizer` boundary.**

**Reasoning:** A mechanism can be correct while its acceptance criterion remains unproved. Closing
T029/T030/T031 from narrower tests would repeat the T011/T013 failure mode that D033 identified.
Renumbering rather than merging the duplicate entry also preserves the order: D034 is the
architecture decision; D035 records what the later implementation actually established.

**Consequences:**

- The duplicate trailing T028 is removed. Canonical T028 remains the baseline gate; T029/T030/T031
  receive implementation-progress notes and stay unchecked; T032/T033 stay pending.
- SPEC's audit table distinguishes implementation progress from accepted closure. AUDIT-5 is
  partial, AUDIT-6/7 have mechanisms but incomplete criterion evidence, and AUDIT-8 is hardened but
  still transferred/unobserved.
- PLAN records `anyio>=4` in the optional Claude extra and the remaining test gaps.
- The full suite is independently rerun after the pass: **214 tests, OK**. Consistency remains a
  separate check and also passes. The implementer's reported per-fix revert checks are retained as
  reported evidence; this spec-update does not modify code to repeat them.
- Status remains `In Review`, classification EXPERIMENTAL and conformance PARTIAL. `/spec-update`
  does not own a lifecycle downgrade, and the incomplete D034 criteria would block promotion
  regardless.

---

### D036 - AUDIT-1: an undeclared verification blocks DONE

> **Renumbered from D035 (2026-08-31).** It was written as D035 while the decision log was being
> revised in parallel, and collided with *"Reconcile the post-D034 audit-fix pass with the current
> contract"*. Two entries shared an ID; this one moved, because the other was already referenced by
> the audit table.

**Date:** 2026-08-31

**Status:** Accepted

**Context:** `_verification()` returned a free-form string with four possible values, and its only
consumer keyed on `startswith("FAILED")` or `startswith("MUTATED")`. `NOT DECLARED` matched neither,
so it fell through to the freeze and the run reached `DONE`. 031's second termination condition — a
green, non-mutating verification — had become a line in the closure record that nothing read.

I had classified this as needing a policy decision. On re-reading, it does not: 031 states the
condition as a **requirement** of DONE, and the repo's own rule in `KNOWN_DEBT.md` calls closing
over an unmet criterion the failure that file exists to prevent. The protocol already answered it;
what was missing was the code obeying it.

**Decision:** Only `VERIFY_PASS` closes a run. An undeclared baseline blocks with exit **18**
(`CLOSURE_NOT_PROVEN`), `PAUSED` and resumable, and the remediation names the flag. The four
outcomes are named constants in `closure.py` and the gate compares against them by equality.

**Reasoning:** The string-versus-enum detail is the whole defect, not an aesthetic point. A gate
that pattern-matches two prefixes of a four-valued string silently permits the two it does not
mention — and the one it let through was the one that matters. Replacing the comparison with an
equality against named constants makes a future fifth outcome fail closed instead of passing.

`--baseline` stays **optional for everything except closing**: the entry gate, the task loop and
`--dry-run` are unaffected. A runner that cannot verify can still do work; it cannot declare it
finished.

**Consequences:**

- 27 tests failed on the first run of this change — every harness that reached `DONE` without
  declaring a verification. That count *is* the finding: the suite had been exercising the defect
  as if it were the contract. All now declare `GREEN_BASELINE = ["true"]`, which passes and mutates
  nothing, so they exercise the real path.
- One existing test asserted the old behaviour by name
  (`test_an_undeclared_verification_is_recorded_as_unobserved_not_as_passed`). It is rewritten as
  the test for the corrected behaviour, alongside two new ones for the green and tree-mutating
  cases.
- `docs/SDD-ORCHESTRATION.md` says `--baseline` is "031's second DONE condition. Declared, it must
  pass… Undeclared, that condition is recorded as unobserved" — **that sentence is now wrong** and
  is corrected in the same change.
- **AUDIT-2 remains open.** FR-005 requires cross-executor resume and `resume.inspect` refuses
  foreign documents; deciding which is wrong belongs to `/spec-update`, not here.

---

### D037 - Spec updated: AUDIT-2 closed by narrowing FR-005, and a decision-ID collision repaired

**Date:** 2026-08-31

**Status:** Accepted for AUDIT-2 and the ID repair; its remaining-work summary is superseded by D038

**Context:** Two things needed reconciling, and only one of them was the task.

The task was AUDIT-2: FR-005 required `ORCHESTRATION.md` to be resumable by either executor, and
`resume.inspect` refuses any document whose `writer` is not `sdd_runner`. Requirement and code
disagreed and nobody had said which was wrong.

The second thing was discovered on opening the files: **`SPEC.md` and `DECISIONS.md` had been
edited outside this session's turns.** FR-005 and FR-006 were already narrowed, a different D034
had replaced the one recording the AUDIT-5/6/7/8 fixes, and its content had been absorbed into a
new D035. This session had meanwhile appended its own D035 for AUDIT-1, so **two entries shared an
ID**.

**Decision:**

- **AUDIT-2 is resolved by narrowing the requirement.** FR-005 as it now stands is the correct
  contract, and it was verified against the code rather than assumed: a foreign document is refused
  with exit `16`, the writer is named in the reason, a remediation is given, and the state file is
  byte-identical afterwards. All four clauses hold. The audit table records AUDIT-2 as RESOLVED
  **by narrowing, not by code**, so the distinction survives.
- **The AUDIT-1 decision is renumbered D035 → D036**, with a note explaining why it moved. The
  other D035 kept the ID because the audit table already referenced it.
- **No code changes.** Nothing needed any.

**Reasoning:** Bidirectional resume was an unsafe promise rather than an implementation gap.
Reconstructing another executor's run means inferring provenance from a document this runner did
not write — the exact thing D014 forbids, and for the exact reason: a resume that guesses produces
caps and a budget nobody can trust. Implementing FR-005 as originally written would have meant
building the unsafe behaviour to satisfy the sentence describing it.

Renumbering rather than merging the two D035s keeps both records intact. A decision log that
silently loses an entry to a collision is worse than one with a visible renumbering note.

**Consequences:**

- No task changes state. The eight `[NEEDS REVIEW]` markers stand; AUDIT-2 no longer contributes
  to the one on T004 and T013, but AUDIT-6 still does for T013.
- **The two edits made outside this session were not reverted or second-guessed.** They are
  consistent with the architecture review and with the code, and re-litigating them would be the
  more disruptive choice. This entry records that they happened, because a decision log that does
  not notice being edited from two directions is not a record.
- Remaining open: AUDIT-3, AUDIT-4 and AUDIT-9, all belonging to the follow-up spec.

---

### D038 - Reconcile D036/D037 with canonical task IDs and acceptance evidence

**Date:** 2026-08-31

**Status:** Accepted

**Context:** The D036 implementation and D037 spec update left a second task numbered `T029` at
the end of `TASKS.md`. That duplicate marked AUDIT-1 complete using focused in-process tests, while
the canonical baseline task is T028 and its `Verify:` explicitly requires four CLI subprocess
cases: missing, failing, mutating and passing. The current CLI E2E suite supplies a green baseline
by default and does not exercise the other three outcomes. D037 also concluded that only
AUDIT-3/4/9 remained, which conflicts with the still-open D034 criteria for containment,
concurrency evidence, committed-mutation invalidation and the `_finalize` boundary.

**Decision:**

- Preserve D036's code decision: only a green, non-mutating baseline may reach `DONE`, and a
  missing baseline fails closed with exit `18`.
- Remove the duplicate trailing T029. Record the implementation under canonical T028 as
  **MECHANISM PRESENT, VERIFY OPEN**; do not mark it complete until all four CLI cases required by
  AC-015 are observed.
- Preserve D037's resolution of AUDIT-2 and its D035→D036 collision repair. Supersede only its
  inaccurate consequences about task state and remaining findings.
- Keep T029 partial, T030/T031 mechanism-present with evidence open, and T032/T033 pending. The
  provider-owned portions remain follow-up scope.
- Make no production-code or lifecycle-status change in this spec update.

**Reasoning:** A mechanism test is valuable progress but is not interchangeable with the
acceptance evidence named by the canonical task. Keeping one unique task ID and attaching progress
to that task preserves SPEC → PLAN → TASKS → TESTS traceability without discarding either the code
change or the stronger criterion. Appending a completed task with a reused ID would make both the
audit log and automation ambiguous.

**Consequences:**

- Task IDs are unique again. No task changes completion state: T028…T033 remain unchecked, with
  progress recorded on T028…T031.
- AUDIT-2 remains resolved by contract narrowing. AUDIT-1/5/6/7 remain owned by 040 at their
  documented evidence levels; AUDIT-9 remains T032's boundary work. AUDIT-3/4/8 and the provider
  half of AUDIT-7 remain follow-up inputs.
- The current full suite was rerun after the external edits: **216 tests, OK**. This validates the
  regression baseline but does not supply the missing CLI, concurrency, in-loop commit or boundary
  scenarios.
- `closure.py` and its test support currently cite D035 for the baseline rule; the next
  implementation pass should update those comments to D036. This traceability cleanup is noted
  rather than performed because `/spec-update` does not modify production code.
- Status stays `In Review`, classification EXPERIMENTAL and conformance PARTIAL.

---

### D039 - AC-015 conflicts with 031 FR-002; T028 stays open

> **Renumbered from D038 (2026-08-31).** Second ID collision in this log: it was written as D038
> while *"Reconcile D036/D037 with canonical task IDs and acceptance evidence"* was being added in
> parallel. This one moved because the other was written first. See D040 on why this keeps
> happening.

**Date:** 2026-08-31

**Status:** Accepted

**Context:** T028's `Verify:` asks for four baseline outcomes through the real CLI subprocess.
Building them surfaced a contradiction that neither the audit nor the task text had noticed.

AC-015 requires that omitting `--baseline`, a non-zero baseline, or a tree-mutating baseline each
return **18**. Two of those three never reach the closure gate: **031 FR-002 lists "red baseline
suite, or a baseline suite that mutates the tree" among the entry-gate refusals**, so the run stops
at exit `10` before any work happens. Observed, not inferred:

```
non-zero  baseline -> 10  [GATE] refused: red baseline suite
mutating  baseline -> 10  [GATE] refused: baseline suite mutates the tree
omitted   baseline -> 18  closure-not-proven
green     baseline ->  0  DONE
```

**Decision:** Implement the tests against the behaviour the code must have, with the conflict named
in the test itself. **Do not check T028.** Do not weaken the entry gate, and do not quietly rewrite
the test to make the code look conformant.

**Reasoning:** Only one of the two requirements can hold, and 031's is both earlier and more
protective: refusing before any delegation is strictly better than discovering the same fact after
a full run. Removing the entry-gate check to satisfy AC-015 would trade a real safety property for
a sentence.

Leaving the task open is the other half. Its `Verify:` **is** met — only the green baseline exits
`0` and records `DONE`, asserted from the CLI. Checking it on that basis while its `Covers:` names
an AC that cannot be met is precisely the failure D025 recorded on T011, and the second time would
be worse than the first: that pattern is now documented in this very log.

**Consequences:**

- T028 unchecked, with the conflict written into its note.
- **AC-015 needs amending** to expect `10` for the two entry-gate cases and `18` for the omitted
  one — `/spec-update`'s call.
- The closure-side `FAILED`/`MUTATED` branch is now near-unreachable through the CLI: it fires only
  if a baseline that was green at entry turns red or unhermetic during the run. Worth keeping —
  that is a real transition — but it is no longer the path AC-015 describes.
- Found while implementing: **the CLI never printed `remediation`.** Every blocking outcome carries
  one and the operator never saw it. Fixed; the omitted-baseline case now asserts the flag is named
  in the output.

---

### D040 - Spec updated: AC-015 amended to the earliest-gate behaviour

**Date:** 2026-08-31

**Status:** Accepted

**Context:** D039 recorded that AC-015 could not be met as written. It required an omitted,
non-zero and tree-mutating baseline to each return `18` from the closure gate, and **031 FR-002
lists a red or tree-mutating baseline among the entry-gate refusals**, so two of the three stop at
`10` before any delegation happens. Observed through the CLI, not inferred:

```
omitted   -> 18   closure-not-proven
non-zero  -> 10   [GATE] refused: red baseline suite
mutating  -> 10   [GATE] refused: baseline suite mutates the tree
green     ->  0   DONE
```

**Decision:** AC-015 now states the property that matters — **only a green, non-mutating baseline
permits exit `0`** — and requires each failure to be refused at the earliest gate that can see it,
naming `18`, `10` and `10`. The entry gate is unchanged. No code changes; the implemented tests
already assert this.

**Reasoning:** The criterion had fixed on a single exit code as though the code were the
requirement. It was not: the requirement is that an unverified run cannot close. Refusing a red
baseline at entry is strictly better than discovering the same fact after a full run, so amending
the criterion is right and weakening the gate would have been wrong.

Writing the amendment as "the earliest gate that can see it" rather than listing three codes is
deliberate. It says *why* the codes differ, so a future reader does not read the list as an
accident and try to normalise it back to one value.

**Consequences:**

- **T028's `Covers:` and `Verify:` now agree**, so it can be closed — by a pass that re-runs the
  four cases, not by this note. It stays unchecked here: `/spec-update` does not close tasks.
- The closure-side `FAILED`/`MUTATED` branch remains reachable only when a baseline that was green
  at entry turns red or unhermetic mid-run. That is a real transition and the branch stays, but it
  is no longer what AC-015 describes.
- No other AC or FR changes. No completed task is affected.

---

### D041 - Decision IDs have now collided twice; how the log is written must change

**Date:** 2026-08-31

**Status:** Accepted

**Context:** Two collisions in one day. D035 was written twice (D037 renumbered mine to D036), and
D038 was written twice (D039 renumbered mine). Both times the cause was identical: this log is
appended to from more than one place, each picking "the next number" from a file that had already
moved underneath it.

**Decision:** Record the pattern rather than repair it a third time in silence. Both renumbering
notes stay in place, naming what moved and why. **The convention that failed is "append with the
next sequential integer", and any fix belongs to `specs/_templates/`, not to this feature** — a
per-feature workaround would leave every other spec with the same trap.

**Reasoning:** The first collision looked like an accident, and repairing it quietly was
defensible. The second one makes it a property of how the log is written, and a decision log that
silently absorbs two ID collisions is exactly the kind of record that reads as trustworthy while
having lost track of itself. Naming it costs one entry; a third collision found by a reader in six
months costs the log's credibility.

**Consequences:**

- Two visible renumbering notes, which is the intended cost.
- The template-level fix — content-addressed or timestamped decision IDs, or an explicit "reserve
  the ID first" rule — is a follow-up against `specs/_templates/`, owned by spec 033's territory,
  and is **not** attempted here.
- Risk if ignored: the third collision will land on an entry that something already references by
  ID, and then the repair is no longer free.

---

### D042 - `--feature` containment is anchored on the spec trail and resolved through symlinks

**Date:** 2026-08-31

**Status:** Accepted

**Context:** T029. The previous check used `abspath` plus `commonpath` against the **repository
root**, which left three holes: a symlink inside `specs/features/` pointing anywhere still looked
contained because `abspath` does not resolve links; any in-repo directory was acceptable; and the
features root itself was acceptable.

**Decision:** `_resolve_feature` resolves the repository root, the `specs/features/` root and the
requested path with `os.path.realpath`, then compares the **resolved** paths with
`os.path.commonpath`. The anchor is the spec trail, not the repository. The features root itself is
refused. The refusal names the requested path, what it resolved to, why it was refused, and the
remediation — the resolved path matters because "the path you typed is fine, the place it lands is
not" is otherwise an invisible failure.

It runs before every write: before the entry gate, before the exclusive claim on
`ORCHESTRATION.md`, before the log is opened.

**Reasoning:** Resolution has to come before comparison or the comparison answers a question about
names rather than locations. `commonpath` rather than `startswith` because a prefix test says
`/repo/specs/features-old` is inside `/repo/specs/features`, which is wrong and is the classic
version of this bug.

**Consequences:**

- **The first version of the tests passed against the unfixed code**, and that is the finding worth
  keeping. The external targets were empty directories, so every refusal came from "SPEC.md
  missing" and the containment check was never reached. They now plant a complete, valid feature
  folder at each external target and assert the refusal names containment. This is the fourth time
  in this feature that a green test proved nothing, and each time it was caught by asking *why* it
  was green rather than by the suite.
- `repo` is now `realpath` rather than `abspath`, so a symlinked repository root does not defeat
  the comparison. On macOS this matters immediately: `/var` is a symlink to `/private/var`, which
  every temporary-directory test path goes through.
- One older assertion in `test_cli_e2e` followed the previous wording and was updated. Coverage
  stays in both modules because T029's `Verify:` names both.

---

### D043 - The concurrency race found a real defect: two owners, unexplained

> **SUPERSEDED 2026-09-01 by [[D044]].** The conclusion below is wrong: `[14,14]` was
> sequential resume, not simultaneous ownership. The entry left in place deliberately —
> a decision log that edits away its own mistaken conclusions cannot be used to check
> anything.

**Date:** 2026-08-31

**Status:** Accepted

**Context:** T030 asked for two subprocesses released from a barrier before state exists. Built and
green — and then the revert check said something uncomfortable: **removing `O_EXCL` leaves the race
test passing.**

The reason is structural, not a test bug. Both contenders clear the barrier together, then each
runs the entry gate — several `git` invocations of variable duration — before reaching the claim.
That work separates them by orders of magnitude more than the window `O_EXCL` protects, so in
practice the loser always arrives after the winner has published a complete document and is refused
by the pid check rather than by the atomic create.

**Then the race caught something worse.** Run repeatedly under load, roughly **one round in twelve
ends with two owners**: two `plan` events in a single `run.jsonl`, both contenders exiting `14`,
neither refused. Reproduced twice at that rate; twenty attempts on an idle machine produced none,
so the instrumented event trail was never captured.

```
intento  5: codes=[14, 14] plans=2   <-- two owners
```

The claim code is correct on inspection — `os.path.exists` guard, `O_CREAT|O_EXCL`, `FileExistsError`
raising `ConcurrentRun` — and both contenders resolve the same `realpath`. The kernel cannot grant
two exclusive creates on one path, so the fault is somewhere else in the ownership path and **I have
not found it**.

**Decision:** Keep both tests and say what each one buys. `test_race.py` proves the observable
contract end to end: one owner, one exit `15`, one worker dispatch, and never a `16`.
`test_resume.TheCreateWindowIsAtomic` forces the window directly and **does** fail without
`O_EXCL`. The limitation is written into the test file's own docstring, not only here.

**Reasoning:** Contesting the window from outside would need a test-only wait hook inside the
runner, immediately before the claim — production code whose only purpose is to make a race
reproducible. That is a real option and it was rejected for now: the primitive is already
discriminated by a deterministic test, and a seam in the ownership path is exactly where a seam is
most dangerous.

What could not be left alone was the belief that the race test was covering the primitive. A test
that cannot fail is not evidence, and a green suite that reads as if it were is the failure mode
this feature has hit repeatedly.

**T030 stays OPEN.** The evidence the task asked for now exists and it says the exclusion does not
hold. Closing it would record "concurrent starts are excluded" as an observed fact when the only
run that observed the contested window observed the opposite.

**This is not a flaky test.** A test that fails one time in twelve because the behaviour is wrong
one time in twelve is doing its job; calling it flaky and quarantining it is how the defect would
have survived. It stays in the suite, and an intermittent red is the correct signal until the
anomaly is explained.

**Consequences:**

- T030 reopened. Two tests cover different halves. Deleting either leaves a real gap, which is
  why the split is recorded in both places.
- **A fifth instance of "a green test proving nothing" in this feature**, and the first where the
  test was correct and merely weaker than it appeared. The revert check caught it again; that
  practice is now the only reason four of these were found at all.
- If the window is ever changed, the deterministic test is the one that must be re-run — the race
  will stay green either way.

---

### D044 - `[14,14]` was sequential resume, not two owners; D043 corrected

**Date:** 2026-09-01

**Status:** Accepted

**Context:** D043 recorded that the concurrency race had found two simultaneous owners and that the
exclusion was unproven. That conclusion rested on two `plan` events in one `run.jsonl` and two
contenders exiting `14`. Neither fact proves overlap, and I treated them as if they did.

Forty rounds, keeping every artifact per round, produced the trace:

```
plan(resumed=false) → finish(14) → resume → plan(resumed=true) → finish(14)
```

The first contender claimed the feature, ran, and exited `14` leaving `ABORTED / resumable: yes`.
The second contender — whose busy-wait had lost by more than the round took — then found that state
and **legitimately resumed it**. Two plans, no overlap, exclusion never violated.

The cause is the harness, not the runner: the barrier released both processes *before the entire
CLI*, and the entry gate's several `git` invocations separated them by orders of magnitude more
than the window the claim protects.

**Decision:** Correct the conclusion in a new entry and mark D043 superseded in place. Do not edit
or delete D043's text.

**Reasoning:** The mistake is worth keeping visible because of its shape: I had two observations
consistent with a frightening explanation and adopted it without capturing the trace that would
distinguish it from the boring one. The instrumentation that settled it took one run. "I could not
reproduce it" was, in hindsight, a signal to keep looking rather than to conclude.

A decision log that quietly rewrites its wrong conclusions is worth less than one that carries them
with a correction attached, because only the second can be audited.

**Consequences:**

- T030's reopening stands as correct procedure even though its stated reason was wrong: the
  evidence at the time did not support closing.
- The race harness was rebuilt around the claim itself (D045). The old one could not have caught a
  real overlap either.
- **A real defect was found in the same investigation** — the partial-publication window — so the
  reopening was right for a reason nobody had stated yet.

---

### D045 - The initial state document is published whole, or not at all

**Date:** 2026-09-01

**Status:** Accepted

**Context:** The claim created an empty `ORCHESTRATION.md` with `O_CREAT|O_EXCL` and wrote the
document afterwards with `doc.save()`. Exclusion was correct — two contenders could not both create
— but a third state was visible in between: **a file that exists and is empty**. A contender
arriving in that window took the resume path, loaded a document with no `writer` field, and exited
`16`, reporting a corrupt state rather than a competing runner.

**Decision:** `Orchestration.create_exclusive` writes the complete document to a temporary name in
the same directory, `fsync`s it, and publishes it with `os.link`. `os.link` fails with
`FileExistsError` when the target exists and **never replaces** it — `os.replace` would be wrong
here for exactly that reason. The path therefore goes from absent to complete in one step, and only
one contender can make it appear.

Dead-owner recovery is unchanged and needs no reclaim protocol: a stale owner's document is
*resumed* by `resume.inspect`, never deleted, so there is no cleanup for two contenders to race
over.

**Reasoning:** Atomicity of the claim and completeness of what is claimed are separate properties,
and the first was solved while the second was assumed. The loser's exit code is the tell: `16` says
"this state is corrupt" when the truth was "another runner is mid-publication", and a wrong
diagnosis at the ownership boundary sends an operator to inspect a file that is fine.

**Consequences:**

- Three independent negative checks, each breaking exactly one control:
  `os.link → os.replace` breaks `TheCreateWindowIsAtomic` **and** the synchronized race;
  restoring the empty-file claim breaks `PartialPublication`;
  letting both contenders proceed breaks the synchronized race (8 failures).
- **The partial window cannot be caught by timing** — it is sub-microsecond, and the race stayed
  green with the old code restored. `test_the_claim_path_never_creates_an_empty_file` asserts the
  mechanism instead: it fails the test if the claim opens the state path with `O_CREAT` at all.
  Racing for an interleaving is not evidence; forbidding the call that opens the window is.
- The race harness uses a two-phase barrier around `_load_or_create_state`, monkeypatched in the
  child process only. **No test hook exists in production code**, which was a hard constraint: a
  seam in the ownership path is where a seam is most dangerous.

### D046 - The core stops at `_finalize`; the closure-delta code stays behind for its successor

**Date:** 2026-09-01

**Status:** Accepted

**Context:**

D034 cut spec 040 at the `_finalize` seam on paper. The code had not moved: `Loop._close` still
delegated `/spec-review`, `/spec-close` and `/pr-description`, required each one's APPROVE, and
audited a closure delta over what they changed. Every one of those steps was proven by a stub
answering `APPROVE` on the skill's behalf — which proves the stub was asked, and nothing about a
skill executing. A spec that certifies no provider cannot certify a lifecycle hand-off.

Implementing the cut raised a second question the task did not answer: `closure.observe`,
`closure.unexpected` and `closure.classify` exist only to compute that delta. Removing the dispatch
leaves them with no production caller.

**Decision:**

`Loop._close` records the terminal core evidence — phase `CORE-COMPLETE`, the frozen fingerprint,
the verification outcome, the frozen tree map — and finishes `DONE` / exit `0`. `LIFECYCLE_STEPS`,
`_lifecycle_step`, `_phase_index` and the `lifecycle:` branch of `_system_prompt` are deleted.

The delta half of `closure.py` is **kept, unreferenced by production, and documented as such in the
module docstring.** It is not dead code that was overlooked; it is the seam AUDIT-9's follow-up
`Finalizer` begins at, and the frozen map this runner still persists is precisely what it will
compare against. It remains directly asserted by the suite.

The phase word is `CORE-COMPLETE`, not `CLOSED`. This runner does not close a feature lifecycle,
and a phase word implying otherwise would reintroduce the claim D034 removed.

**Reasoning:**

The alternative — deleting the delta machinery — is the letter of "code you leave without callers is
yours to remove", but it destroys tested behaviour the immediate successor needs and buys nothing
except a shorter module. The rule exists to stop dead code accumulating unnoticed; a docstring
naming the consumer and the spec that owns it is the opposite of unnoticed. The honest cost is
recorded here rather than hidden: a reviewer will see three uncalled public functions, and this is
why.

**Consequences:**

- Finalization now costs one delegation beyond the task cycle (`final-conformance-reviewer`), not
  four. `tests/support.FINALIZATION_CALLS` drops from 4 to 1 and every count assertion follows.
- `FROZEN` is no longer reachable by starving the budget: nothing is dispatched between the freeze
  and the terminal write. It remains a real on-disk state — a process killed between two writes —
  so the re-entry tests construct it instead of provoking it. What they test is the re-entry.
- The old `LifecycleGate` tests are inverted, not deleted: a refusing `/spec-close` and an unreadable
  `/spec-review` are still scripted, and now assert the run closes because neither is ever asked.
- Exit `18` no longer means "unexpected closure delta or a refusing lifecycle skill". It means the
  core could not prove completion: no declared baseline, or a freeze voided by a later change.
- `docs/SDD-ORCHESTRATION.md`, `CHANGELOG.md`, `CONTRIBUTING.md` and `runner/README.md` state the
  stub-only supported surface and the hand-off. AUDIT-9 closes in 040; T033 is the only open task.
