# Feature Spec: autonomous-adopt-in-flight-feature

## Status

Done

> `Done` 2026-09-02 — `/spec-close`. All 33 tasks closed against their `Verify:` clause or a dated
> amendment; all fourteen acceptance criteria covered by at least one task and met against observed
> evidence. **276 tests** (239 on `main`), `check-consistency.sh` exit 0, installers and manifests
> byte-identical to `main`. Twelve decisions, all Accepted. No open question.
>
> **What `Done` means here.** The adoption entry works and is evidenced: an adopted run caught a
> seeded defect in inherited work before touching a new task, an all-checked adoption reached
> conformance without delegating any implementation, the human-gated path ended `PAUSED` with a real
> worker's verbatim question, and two `codex exec` runs exercised the entry on the other provider.
> The replay against the originating repository was performed and **failed**, which is recorded as
> the finding it was: it exposed two runner defects, fixed as T029 and T030.
>
> **One residual, carried knowingly:** [[DEBT-010]] — the adopted loop has never reached a
> human-gated `PAUSED` against a real feature's task list, only against a fixture feature driven by
> real workers. D012 lifted that from a gate to known debt. Its closing condition is unchanged and
> the next feature adopted by hand pays it off.
>

> `In Review` 2026-09-02 — `/spec-review` **Pass** on the seventh round, against a tree of 32 tasks,
> 275 tests and eight commits. **Superseded in place the same day:** `/qa-review` then found a
> functional hole the seven reading-based rounds had missed — a detached HEAD passed the isolation
> condition — and T033 closed it. Current state: **33 tasks**, **276 tests** (239 on `main`),
> **eleven commits**. The seventh round's certification is unaffected: the delta review confirmed no
> acceptance criterion needed re-evidencing, and `check-consistency.sh` exits 0 with installers and
> manifests still byte-identical to `main`. The status stays `In Review` because that is the stage
> that owns QA findings and their repair.
>
> Six rounds preceded this one and each returned Partial. Rounds 1–3 found a behavioral regression
> each, all in the same blind spot: the gate's CLI callers had no test. Round 4 found two
> documentation defects. Rounds 5 and 6 found no code defect at all — only that the record
> contradicted itself, the second time one document beyond where the first was repaired. That is
> recorded in `CALIBRATION.md` as a named finding, and it is why round 7's repair was a sweep.
>
> ~~`Done` stays gated on [[DEBT-010]] by D011: the adopted loop has never reached a human-gated
> `PAUSED` outside a fixture.~~ **Amended 2026-09-02 by D012:** the maintainer lifted that gate.
> DEBT-010 stays open and tracked as known debt, and no longer blocks closure — the human-gated path
> is proven end to end by T028, what is missing is observation on a real feature rather than the
> mechanism, the escalation code is spec 031's and untouched here, and the runner is experimental and
> `stub`-only, so a residual failure would be a visible, recoverable abort.

> `In Progress` 2026-09-02 — `/spec-implement`, first task (T001, adoption fixture) implemented.
>
> `Ready` 2026-09-02 — `/spec-plan`. PLAN.md, TASKS.md and DECISIONS.md exist; OQ-1, OQ-2 and OQ-3
> resolved as D001, D002 and D003; FR-012/FR-013 and AC-013/AC-014 added for provider parity and
> evidence; every acceptance criterion AC-001…AC-014 is covered by at least one task.
>
> `Draft` 2026-09-01 — `/spec-create`. Number **041**: 040 is the highest slot on `main` and no
> remote branch claims 041 (checked after `git fetch --all`).
>
> Origin: an architecture review on 2026-09-01 of the question "I launched a spec and it keeps
> asking me to run the next command; what does the project lack to run through the gates on its
> own?". Diagnosis: the loop exists (spec 031, `/sdd-orchestrate --autonomous`), but a feature that
> started through the manual chain (`/sdd` → `/spec-implement` → `/spec-review`) can never be handed
> to it. The chosen option was "make the existing loop adoptable", explicitly rejecting a second
> loop inside `/spec-implement`.

## Problem

The SDD framework has two ways to take a feature from `Ready` to a PR-ready tree, and there is no
bridge between them.

1. **The manual chain never chains.** `/spec-implement` implements "only the next unchecked task
   unless explicitly instructed otherwise" and ends with a *Recommended next command* in prose.
   `/spec-review`, `/qa-review` and the specialized reviews do the same. `/sdd` step 4 literally
   says "repeat until all tasks done", and nobody repeats: the maintainer is the scheduler, typing
   the next command after every task and every gate. That is by design for a supervised session,
   but it means a maintainer who started a feature by hand gets no autonomy later.

2. **The autonomous loop cannot adopt a feature in flight.** `/sdd-orchestrate --autonomous`
   ([SKILL.md](../../../skills/sdd-orchestrate/SKILL.md), *Autonomous mode — entry gate*) requires
   on first entry that `SPEC.md` is exactly `Ready`, the working tree is clean, and re-entry is
   authenticated only by an existing `ORCHESTRATION.md`. A feature that is `In Progress` with some
   tasks checked, uncommitted work on disk and no state file fails three conditions at once and is
   refused. The refusal is correct under 031's contract (fail closed, never guess provenance), but
   it leaves the maintainer with one option: throw the feature back to `Ready` or finish by hand.

3. **The phase-2 runner already disagrees with the skill.** `runner/sdd_runner/gate.py` declares
   `READY_STATUSES = ("Ready", "In Progress", "In Review")` on first entry and only refuses dirty
   paths *outside* the feature folder. That is looser than the skill in exactly the direction this
   feature has to decide deliberately. Spec 040 D007 says: where the runner and the skill disagree,
   the runner is wrong. Nobody has decided what "right" is for an in-flight feature, so the drift
   stands unrecorded.

The concrete trigger was `proyecto-cumbre` feature 030: `In Progress`, on the default branch, with
about three thousand uncommitted lines, two human-only tasks open, and the maintainer typing
`/spec-implement` and `/spec-review` by hand.

## Goal

`/sdd-orchestrate --autonomous <feature-path> --adopt` takes a feature that is already
`In Progress` — started and partly implemented outside the loop — and runs it through the same
implement → review → fix → close circuit as a feature entered at `Ready`, with the same caps,
the same durable state, the same escalation rule and the same termination contract. Work done
before adoption is **inherited, never re-implemented, and never trusted unreviewed**: the loop
records exactly what it inherited, reviews the inherited diff through the structured reviewers
before touching a new task, and carries the maintainer's commit as the trusted baseline. The runner
gate is brought back into agreement with the skill.

## Non-goals

- **No second loop.** `/spec-implement` does not gain an `--all`, `--until-review` or similar
  flag. A loop without verdict blocks, caps and durable state is the failure mode 031 was written
  to remove. The manual chain only learns to *point* at adoption (FR-009).
- **No implicit adoption.** An `In Progress` spec without `ORCHESTRATION.md` and without `--adopt`
  keeps being refused exactly as today. Adoption is a deliberate maintainer act.
- **No attribution of a dirty tree.** Uncommitted pre-adoption work is never attributed to the run.
  The maintainer commits it first; the commit is the evidence of ownership. This is 031's
  "never guess provenance" applied to the entry, not relaxed for it.
- **No re-execution of checked tasks.** Adoption does not re-delegate a task the maintainer
  checked. It records the task as inherited and lets the reviewers judge the diff.
- **No change to spec Status ownership** (`sdd-guardrails` section 11). Adoption reads
  `In Progress`; it never writes it, and closure still belongs to `/spec-review` and `/spec-close`.
- **No out-of-session execution.** CI, cron and a real provider backend for the 040 runner remain
  separate work. The runner change here is limited to its entry gate.
- **No new agents, no new verdict schema.** The existing seven agents and the 031 blocks are
  reused unchanged.
- **No adoption from `In Review`, `Draft`, `Done` or `Archived`.** `In Review` means every task is
  checked and `/spec-review` already passed; what remains there is QA and closure, which have owning
  skills. See OQ-2 before widening this.

## Users / Actors

- **Maintainer** — started the feature by hand, commits the pre-adoption work, invokes `--adopt`,
  answers human-gated escalations, reviews the PR.
- **Orchestrator session** (`sdd-orchestrate`) — validates the adoption gate, initializes state
  with the inherited record, runs the unchanged loop.
- **Delegated agents** — `domain-reviewer` and `security-reviewer` (review the inherited diff and
  every later diff), `implementer`/`fast-worker` (remaining tasks and finding tasks),
  `deep-reasoner` (auto-resolvable escalations), `final-conformance-reviewer` (once at the end).
- **Runner** (`runner/`, spec 040, experimental) — must mirror the gate decision; it dispatches
  nothing new here.

## Current behavior

- `--autonomous` on an `In Progress` feature with no state file: `AUTONOMOUS REFUSED`, condition
  *Lifecycle status*, remediation `/spec-plan <feature-path>` — which is wrong advice for a feature
  that is already planned and partly built.
- `--autonomous` on a dirty tree at first entry: refused, condition *Clean working tree*.
- On the default branch: refused, condition *Isolated git location*.
- `/spec-implement` ends every invocation with "next: `/spec-implement <path>`" or
  "next: `/spec-review <path>`". It never mentions the autonomous mode.
- `runner/sdd_runner/gate.py` accepts `In Progress` and `In Review` on first entry and tolerates
  dirty paths inside the feature folder; `test_gate.py` pins that behavior.

## Desired behavior

`/sdd-orchestrate --autonomous <feature-path> --adopt [--max-iterations N] [--max-delegations N]`:

1. **Flag semantics.** `--adopt` is accepted only together with `--autonomous`. It is rejected
   with the other flag errors (unknown flag, duplicate, non-integer cap) before any read or write
   of feature state. When a valid `ORCHESTRATION.md` for the feature already exists, `--adopt` is
   refused with condition *Already adopted or entered* and the remediation "re-enter without
   `--adopt`": an existing run is resumed, never re-adopted. When the spec is `Ready`, `--adopt` is
   refused with condition *Adoption not needed* and the remediation "run without `--adopt`".

2. **Adoption gate.** The six 031 conditions apply with two rewritten and one added:
   - *Lifecycle status* (rewritten): `SPEC.md` must be exactly `In Progress`. Any other status
     refuses and names the owning lifecycle action (`Draft`/`Ready` → not adoptable;
     `In Review` → `/qa-review` then `/spec-close`; `Done`/`Archived` → nothing to run).
   - *No open decisions*: unchanged.
   - *Runnable task queue*: unchanged. A queue where every task is checked is accepted as
     terminal-ready — the loop then goes straight to inherited-diff review and final conformance.
   - *Isolated git location*: unchanged. The remediation for the common case is spelled out:
     `git switch -c feature/<name>` carries uncommitted work onto the new branch.
   - *Clean working tree* (rewritten for adoption): `git status --porcelain` must be empty. There
     is no "attributable dirty path" on adoption because no run exists yet to attribute to. The
     remediation names the exact command: commit the pre-adoption work on the feature branch.
     Stashing is listed as acceptable only if the maintainer wants that work *excluded* from the
     feature.
   - *Green baseline suite*: unchanged, and it must leave the tree clean.
   - *Inherited record is computable* (added): the orchestrator must be able to determine the
     adoption baseline commit (`HEAD`), the merge-base with the default branch, and the set of
     checked tasks in `TASKS.md`. If the merge-base cannot be determined (no default branch
     metadata, unrelated histories), refuse with condition *Inherited diff undetermined* and the
     remediation to set `origin/HEAD` or pass the base explicitly (see OQ-3).

3. **State initialization.** `ORCHESTRATION.md` is created from the canonical scaffold with these
   additions in the header and a new section:

   ```markdown
   - Entry: `adopt`
   - Adopted at: `<ISO-8601>`
   - Adoption baseline commit: `<sha>`
   - Adoption diff base: `<merge-base sha>` (against `<default-branch>`)

   ## Inherited

   | Task | Checked before adoption | Verify clause | Verification observed by this run |
   |---|---|---|---|
   ```

   Every task that was checked at adoption gets one row with `Verification observed by this run:
   no` — the loop did not see it happen. Counters start at zero. `max-delegations` is computed as
   `max(25, 6 × unchecked tasks at adoption)` unless overridden, and the record says "at adoption"
   rather than "at first entry". The adoption baseline commit becomes the run's *trusted baseline*
   in the sense already used by the re-entry recovery rule (a clean worktree may be created from
   it).

4. **Inherited-diff review before any new work.** After state initialization and before the first
   implementation delegation, the orchestrator computes the reviewable fingerprint over the tree
   and runs `domain-reviewer` on the inherited diff (adoption diff base → adoption baseline
   commit), plus `security-reviewer` when that diff or the spec matches the existing Level-3
   triggers. These count as delegations against the budget. Verdicts are parsed and persisted
   exactly as in the circuit: REJECT findings become `(from <finding-id>)` tasks with the next
   available `TNNN`, and no new spec task is implemented while an inherited-diff finding is open at
   `Critical` severity — the closed reviewer vocabulary is `Critical | High | Medium | Low` (lower
   severities interleave under the normal rule). An APPROVE on the
   inherited diff is an approval for that fingerprint and is invalidated by later changes like any
   other.

5. **Loop, escalation, caps, termination, resumability.** Unchanged. After adoption the run is
   indistinguishable from a `Ready` entry except for the `Inherited` section and the header
   fields. Re-entry authenticates through the state file as today; `--adopt` is never passed
   again.

6. **Inherited tasks in final conformance.** The `final-conformance-reviewer` brief includes the
   `Inherited` table. A checked task whose `Verify:` clause was never observed by this run is
   reported by that reviewer as *inherited, verification not observed* — it is evidence the
   maintainer supplied by checking the box, and the report says so instead of claiming the loop
   observed it. This does not block APPROVE by itself; it makes the provenance honest.

7. **Runner gate parity.** `runner/sdd_runner/gate.py` gains the same distinction: without an
   adopt flag, first entry requires `Ready`, and any dirty path refuses (not only paths outside the
   feature folder); with `--adopt`, first entry requires `In Progress` and a fully clean tree, and
   the gate records the adoption baseline and diff base. `In Review` is removed from first-entry
   acceptance in both paths. The runner's `--dry-run` reports the inherited record. Dispatching the
   inherited-diff review stays out of the runner's supported surface, consistent with its
   `stub`-only classification.

8. **Manual chain hand-off.** `/spec-implement`'s *Recommended next command* gains one line: when
   unchecked tasks remain, offer `/sdd-orchestrate --autonomous <path> --adopt` as the way to
   finish without supervision, with the reminder that pre-adoption work must be committed on a
   feature branch. `/sdd`'s step 4 in both workflows gains the same alternative. Nothing else in
   the manual chain changes.

## Functional requirements

- FR-001: `--adopt` is a recognized flag of `--autonomous` only; it is validated with the other
  flags before any feature-state read or write, and rejected outside `--autonomous`, when
  duplicated, or when a valid `ORCHESTRATION.md` for the feature already exists.
- FR-002: The adoption gate accepts only `SPEC.md` `Status: In Progress`; every other status is
  refused with the owning lifecycle action named, and `Ready` is refused with "run without
  `--adopt`".
- FR-003: The adoption gate requires an empty `git status --porcelain`; it never attributes
  pre-existing dirty paths to the run, and its remediation names the commit command.
- FR-004: The adoption gate requires a computable inherited record (baseline commit, diff base
  against the default branch, checked-task set) and refuses with a named remediation when the diff
  base cannot be determined.
- FR-005: State initialization writes `Entry: adopt`, the adoption timestamp, baseline commit and
  diff base in the header, and an `Inherited` section with one row per task checked at adoption,
  each marked as not observed by this run; counters start at zero and the delegation budget is
  computed from unchecked tasks at adoption.
- FR-006: Before the first implementation delegation, the loop runs `domain-reviewer` — and
  `security-reviewer` under the existing Level-3 triggers — on the inherited diff, parses their
  verdict blocks, registers findings and finding tasks under the existing rules, and does not
  delegate a new spec task while an inherited-diff `Critical` finding is open.
- FR-007: Everything after adoption — circuit, caps, escalation, durable state, termination,
  re-entry — is the unchanged 031/032/035 protocol; `--adopt` on re-entry is refused.
- FR-008: The `final-conformance-reviewer` brief carries the `Inherited` table, and its report
  labels inherited checked tasks whose `Verify:` clause the run did not observe as such.
- FR-009: `/spec-implement`'s *Recommended next command* and `/sdd`'s step 4 mention the adoption
  hand-off, including the commit-on-a-feature-branch precondition, and nothing else in those
  skills changes.
- FR-010: `runner/sdd_runner/gate.py` accepts `In Progress` on first entry only under an adopt
  flag, refuses any dirty path in both entry modes, drops `In Review` from first-entry acceptance,
  and records the adoption baseline and diff base; `test_gate.py` is updated to pin the new
  behavior and the README's flag table lists `--adopt`.
- FR-011: `check-consistency.sh` exits 0 after the skill edits, and the install manifests are
  unchanged (no new skill, no new file shipped to adopters).
- FR-012: The adoption entry is discoverable and provider-documented: `docs/SDD-ORCHESTRATION.md`
  documents `--adopt`, its refusal conditions and the inherited-diff review; the runner's flag
  table lists it; `adapters/codex/PARITY.md` documents adoption under the same sequential
  degradation as the parent mode (same gate, same inherited record, same review step, no
  fan-out), and the Codex `sdd-spec-implement` prompt carries the same hand-off line as FR-009.
- FR-013: Behavioral evidence for the adoption entry exists on both providers before closure,
  recorded in this feature's `CALIBRATION.md`; a provider whose run could not execute (missing
  CLI, quota) is recorded as an explicit blocker of `/spec-close`, never as a pass and never
  omitted. This gates `Done`, not `Ready` (D001).

## Non-functional requirements

- Performance: the inherited-diff review adds at most two delegations (domain, security) before
  the first task; adoption itself is local git reads and one file write.
- Security: no permission is weakened; no `git commit`, `git push`, stash or history mutation is
  ever performed by the orchestrator or the runner. Adoption reads history; the maintainer writes
  it.
- Observability: every adoption fact (baseline commit, diff base, inherited tasks, inherited-diff
  verdicts) is in `ORCHESTRATION.md` before the first delegation, so a resumed or audited run can
  reconstruct what was inherited without conversation memory.
- Maintainability: the skill's autonomous protocol grows by one entry variant, not a parallel
  path; the runner change stays inside `gate.py` and its tests.

## API / Interface changes

- `/sdd-orchestrate --autonomous <feature-path> --adopt [--max-iterations N] [--max-delegations N]`
  — new flag.
- New refusal conditions (stable names): *Adoption not needed*, *Already adopted or entered*,
  *Inherited diff undetermined*; and, in the runner only, *status unreadable* — added by T029 after
  the T014 replay, and runner-only by design because the skill path reads any SPEC dialect (D011). Rewritten remediations for *Lifecycle status* and
  *Clean working tree* under `--adopt`.
- `ORCHESTRATION.md` header gains `Entry`, `Adopted at`, `Adoption baseline commit`,
  `Adoption diff base`; new `## Inherited` section. Runs entered at `Ready` write `Entry: ready`
  for symmetry (a missing `Entry` line on existing state files is read as `ready`).
- `runner`: `--adopt` CLI flag; `gate.check(..., adopt=False)` signature; `Refusal` conditions
  mirrored.
- `/spec-implement` and `/sdd`: one additional recommended-next-command line each.

## Data model changes

None outside the feature folder. `ORCHESTRATION.md` schema additions are listed above.

## Edge cases

- Feature is `In Progress` but **every task is checked** and no review ran: adoption proceeds,
  inherited-diff review runs, then final conformance, then the owning lifecycle skills. This is the
  "finish the reviews for me" case and must not be refused as an empty queue.
- Feature is `In Progress` with **zero tasks checked** (status promoted, nothing implemented):
  adoption proceeds with an empty `Inherited` table and an empty inherited diff; the reviewers are
  not invoked on an empty diff, and the run behaves like a `Ready` entry.
- **Inherited diff is empty but tasks are checked** (work committed to the default branch already,
  or checked without code): recorded as-is; the final-conformance reviewer sees checked tasks with
  no diff and reports it. The loop does not "fix" the checkboxes.
- **Checked task without a `Verify:` clause** (pre-033 task list): inherited row shows
  `Verify clause: none`; nothing is executed.
- **Human-only tasks** (a `Verify:` that needs the maintainer, like a visual review or a real-world
  run): not special-cased at adoption; the worker reports `BLOCKED`, the existing escalation rule
  classifies it human-gated, the loop continues on independent tasks and pauses when none remain.
- **Maintainer on the default branch with uncommitted work**: two refusals at once (*Isolated git
  location*, *Clean working tree*); the report lists both and the remediation order is branch
  first, commit second, so the commit lands on the feature branch.
- **Uncommitted work the maintainer does not want in the feature**: the *Clean working tree*
  remediation says stash is acceptable only for exclusion; the loop never stashes.
- **`--adopt` with a stale `ORCHESTRATION.md` from a different feature or an `ABORTED,
  resumable: no` run**: refused as *Already adopted or entered*; the maintainer must preserve the
  audit file under a timestamped name, as the existing recovery rule already requires, before
  adopting.
- **Default branch cannot be resolved** (no `origin/HEAD`, detached checkout): *Inherited diff
  undetermined* with the remediation to set it; the gate never assumes `main`.
- **Inherited-diff reviewer returns a malformed block**: the existing two-attempt
  structured-output rule applies; on failure the run aborts `resumable: yes` before any
  implementation.

## Acceptance criteria

- AC-001: `--autonomous <path> --adopt` on an `In Progress` feature with a clean tree on a
  non-default branch, no open decisions and a green baseline creates `ORCHESTRATION.md` with
  `Entry: adopt`, the baseline commit, the diff base, and one `Inherited` row per checked task,
  and enters the loop without any `AUTONOMOUS REFUSED` line.
- AC-002: The same invocation without `--adopt` is refused with *Lifecycle status* exactly as
  today; with `--adopt` on a `Ready` spec it is refused with *Adoption not needed*; with `--adopt`
  on a feature that already has a valid `ORCHESTRATION.md` it is refused with *Already adopted or
  entered*.
- AC-003: With `--adopt` and one uncommitted path anywhere in the tree, the gate refuses with
  *Clean working tree*, the refusal names the path, and `ORCHESTRATION.md` is not created.
- AC-004: On the default branch with uncommitted work, both *Isolated git location* and *Clean
  working tree* appear in one refusal report, in that order.
- AC-005: On adoption with at least one checked task and a non-empty inherited diff, the first two
  entries in the delegation log are `domain-reviewer` (and `security-reviewer` when a Level-3
  trigger matches) on the inherited diff, before any implementer/fast-worker delegation; a REJECT
  with a `Critical` finding produces a `(from <finding-id>)` task and no spec task is delegated
  until that finding is resolved by a later APPROVE.
- AC-006: On adoption with every task checked, the run performs inherited-diff review, final
  conformance and the owning lifecycle skills without delegating any implementation task, and
  ends `DONE` or names the exact reviewer/skill that stopped it.
- AC-007: Re-entering an adopted run without `--adopt` resumes from `ORCHESTRATION.md` with
  counters preserved; re-entering with `--adopt` is refused.
- AC-008: The `final-conformance-reviewer` report for an adopted run lists every inherited checked
  task and marks the ones whose `Verify:` clause the run did not observe as *inherited,
  verification not observed*.
- AC-009: `runner`: `test_gate.py` proves that first entry without adopt refuses `In Progress` and
  `In Review` and refuses a dirty path inside the feature folder; that first entry with adopt
  accepts `In Progress` only on a clean tree and records baseline commit and diff base; and that
  `--dry-run --adopt` prints the inherited record. The full runner suite stays green.
- AC-010: `/spec-implement` and `/sdd` show the adoption hand-off line; `git diff` on those two
  skills contains no other change.
- AC-011: `scripts/check-consistency.sh` exits 0, and `install.sh`/`install.ps1` manifests are
  byte-identical to `main`.
- AC-012: At every exit of an adopted run, the assertion already required by 031 — no `git commit`,
  `git push`, `git merge`, stash or direct SPEC status write by the loop — holds and is recorded.
- AC-013: `docs/SDD-ORCHESTRATION.md`, `runner/README.md`, `adapters/codex/PARITY.md` and
  `adapters/codex/prompts/sdd-spec-implement.md` each mention the adoption entry; the PARITY
  section names the adoption gate, the inherited record and the inherited-diff review.
- AC-014: `CALIBRATION.md` in this feature folder records one Claude Code run and one Codex run
  of the adoption entry, each as a pass with command and output excerpt or as an explicit
  `/spec-close` blocker; neither provider row is absent.

## Test scenarios

- Unit: `runner/tests/unit/test_gate.py` — status × adopt-flag matrix, dirty-inside-feature-folder
  refusal in both modes, diff-base resolution and its refusal when `origin/HEAD` is absent,
  inherited record shape. `test_state`/`resume` tests for the `Entry` header default (`ready` when
  the line is missing).
- Integration: runner `--dry-run --adopt` on a fixture feature with two checked and two unchecked
  tasks reports the inherited table and a budget of `max(25, 6 × 2)`.
- E2E (calibration run, as 031 T023 / 032 did): in a scratch git repo with a fixture feature
  `In Progress`, two checked tasks with a committed diff, and one seeded defect in that diff,
  `/sdd-orchestrate --autonomous <path> --adopt` runs `domain-reviewer` first, produces a
  `(from …)` task for the seeded defect, fixes it, completes the remaining tasks, and ends `DONE`
  with a `PR_DESCRIPTION.md`. A second invocation with `--adopt` is refused; without it, it resumes
  and reports nothing to do.
- Manual: replay the originating case on a copy of `proyecto-cumbre` feature 030 — branch off
  `main`, commit the pending work, adopt — and confirm the two human-only tasks surface as
  human-gated escalations rather than as loop failures.

## Assumptions

- The default branch is resolved from git metadata (`origin/HEAD` or equivalent), never assumed to
  be `main`, matching the existing *Isolated git location* rule.
- The inherited diff is `merge-base(default-branch, HEAD)..HEAD` at adoption. Work the maintainer
  already merged into the default branch is not part of the feature's reviewable surface.
- Committing the pre-adoption work is a maintainer action performed outside the loop; requiring it
  is acceptable because it is also what makes the tree attributable later.
- The 031 fingerprint rule (tracked diff plus sorted untracked bytes, feature evidence files
  excluded) is unchanged and applies from the adoption commit onward.
- Reviewer briefs already accept an arbitrary diff range; reviewing "the inherited diff" needs no
  new agent capability, only a brief that names the range.
- The runner remains experimental and `stub`-only; parity here is gate-level, not execution-level.

## Open questions

None open. Resolved at planning on 2026-09-02:

- OQ-1 (Codex coverage) → **D001**: covered on the same footing as the parent mode, mirroring 031
  FR-012/AC-013; the adapter documents adoption (FR-012) and a Codex smoke run gates `Done`
  (FR-013). The premise of the question was wrong: the autonomous mode *is* ported to Codex, as a
  documented sequential degradation in `adapters/codex/PARITY.md`.
- OQ-2 (adoption from `In Review`) → **D002**: excluded; the QA and closure skills own that stage.
- OQ-3 (explicit `--base <ref>`) → **D003**: no flag; refusal with the `origin/HEAD` remediation.

## Contracted services

Contracted services not declared → all billable add-ons treated as NOT contracted (conservative
default). Run `/project-init` to declare them.
