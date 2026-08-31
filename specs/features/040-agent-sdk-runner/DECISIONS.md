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
