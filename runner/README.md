# `runner/` — phase-2 executor for the SDD autonomous loop

> **FROZEN at spec 042 (maintainer decision, 2026-09-04).** No new runner specs are opened and no
> runner code changes land on `main` until the freeze is lifted. Spec 043 (`feature/043-real-provider-execution`)
> was `In Progress` on its own branch when the freeze was decided; it is paused, not merged, and its
> uncommitted work stays on that branch. The autonomous path for real work is the prompt in
> [`docs/AUTONOMOUS_SDD_FEATURE_PROMPT.md`](../docs/AUTONOMOUS_SDD_FEATURE_PROMPT.md), which runs
> today against a real provider. `DEBT-009` stays open by decision, not by omission.
>
> **Why:** eight of the last thirteen framework specs went into this package and its only proven
> backend is still `stub`; in the same two months the framework took roughly three commits for every
> one that reached a consumer project. **Unfreeze condition:** three real features delivered through
> the prompt show a concrete need the prompt cannot meet (deterministic resume, token budget,
> fail-closed guarantees), recorded as a spec that names those features.

Specs: [`040-agent-sdk-runner/`](../specs/features/040-agent-sdk-runner/) built it;
[`042-canonical-autonomous-core/`](../specs/features/042-canonical-autonomous-core/) made it the
protocol's authority. Protocol: **spec 031**, corrected by **spec 032**.

**Where this package and `skills/sdd-orchestrate/SKILL.md` disagree, the SKILL is wrong.** That is
the inverse of spec 040 D007 and deliberately so (042 D004): D007 was right while the prose was the
only complete definition and this package transcribed part of it, and stopped being right once the
contract tests began checking nine prose surfaces against this core. The core is the only definition
that cannot drift; deferring to prose would mean deferring to the unverifiable half. Semantic
changes still go through `/spec-update` against 031 — the authority moved, the change process did
not.

## What it is, and what it is not

It is maintainer tooling of *this* repository (D001). It is **not** installed by
`install.sh` / `install.ps1`, is not listed in `profiles.json` or the install
manifest, and no adopter project depends on it. Deleting this folder removes the
feature completely.

## Running it

```bash
PYTHONPATH=runner python3 -m sdd_runner --feature specs/features/<nnn>-<name> --dry-run
```

No TTY is required, stdin is never read, and nothing is ever prompted.

| Flag | Meaning |
|---|---|
| `--feature` | the feature folder to run |
| `--backend` | `stub`, `claude`, or `codex` (default `claude`) |
| `--max-iterations` | non-convergence cap (default 3) |
| `--max-delegations` | hard budget (default `max(25, 6 x unchecked tasks)`) |
| `--baseline` | baseline suite; must be green and must not mutate the tree |
| `--notify` | command run without a shell, event delivered as JSON on stdin |
| `--stub-script` | JSON responses for `--backend stub`: the way to exercise a full run without a provider |
| `--dry-run` | gate + plan + budget, dispatching nothing — and needing no usable backend |
| `--adopt` | first entry on a feature already `In Progress` (spec 041): `Ready` only without it; any dirty path refuses in both modes; `--dry-run --adopt` prints the inherited record (baseline commit, diff base, checked tasks). The runner records the entry and dispatches nothing extra for it (041 D006) |

**A behaviour change from before spec 041.** First entry used to accept `Ready`, `In Progress` and
`In Review`; it now accepts `Ready` only, or `In Progress` under `--adopt`. A run pointed at an
`In Progress` feature without the flag gets exit 10 where it used to proceed. That is deliberate
(spec 041 D004): before adoption existed, accepting a part-implemented feature meant starting a loop
over work nobody had reviewed. `In Review` is not a first-entry status in either mode — QA and
closure have owning skills.
A **detached HEAD** is the other refusal that used to pass: it reported no branch name, so the
isolation check never fired. It now refuses under `default branch` in both modes.

**Re-entry and the dirty tree.** On first entry any dirty path refuses. On re-entry the gate
tolerates the four names its own bookkeeping owns inside the feature folder
(`ORCHESTRATION.md`, `run.jsonl`, `TASKS.md`, and `PR_DESCRIPTION.md` — which this runner never
writes, see *Finalization* below; the name is carried for fingerprint compatibility, so a dirty one
is tolerated although no run produced it) plus anything a caller passes as `attributed` — and nothing passes it today (spec 041
D010). With `--backend stub` that is complete, because the stub writes nothing. With a real backend
an interrupted run whose worker touched source files cannot be resumed here: reconcile those paths
by hand. `--adopt` over an existing state file always refuses *already adopted or entered* (exit
10), whatever that file contains; a re-entry without the flag authenticates it and may exit 15 or 16
instead.

### Exit codes

Each code has a stable machine name as well as a meaning; a scheduler may branch on either, and
`sdd_runner.policy.NAMES` is where both are defined. Names: `0` ok · `10` gate-refused ·
`11` human-escalation · `12` cap-abort · `13` budget-exhausted · `14` backend-precondition ·
`15` concurrent-run · `16` state-unresumable · `17` not-converged · `18` closure-not-proven ·
`70` internal-error.


`0` converged · `10` gate refused (under `--adopt` also *adoption not needed*, *already adopted or
entered*, *inherited diff undetermined*; and *status unreadable* in either mode, when the line under
`## Status` states no lifecycle status — this runner reads the framework's own SPEC form and does not
parse other dialects, while the skill path does) · `11` human-gated escalation · `12` cap abort
· `13` budget exhausted · `14` backend precondition · `15` concurrent run ·
`16` state unresumable · `17` processed but not converged ·
`18` core completion not proven · `70` internal error.

### Finalization, freeze and the hand-off

A converged task list is not a closed run. Before it may say `DONE` the runner
re-checks 031's DONE conditions — no unconverged task, no open finding, no
waiting escalation, a coherent budget, every `TASKS.md` item checked — then
re-reviews any approval a later task's change staled, runs
`final-conformance-reviewer` once, and only then **freezes**: it records the
approved implementation fingerprint together with a per-path content map of the
tree at that instant.

**The freeze is where this runner stops.** It records `CORE-COMPLETE`, the frozen
fingerprint, the verification outcome and the frozen tree map, and exits `0`. It
does **not** dispatch the owning lifecycle skills (`/spec-review`, `/spec-close`,
`/pr-description`), does not compute a closure delta over what they would have
changed, and does not write `PR_DESCRIPTION.md`. It has never written a spec
`Status` and still does not — closing the feature lifecycle stays a human step,
or a follow-up spec's, because doing it here would need a provider that can
actually execute a skill and this spec certifies none.

The frozen tree map is persisted anyway: it is the datum that hand-off compares
against. `closure.py` keeps the delta half for that consumer.

`--baseline` is 031's second DONE condition and is **required**. Declared, it must
exit 0 and must not mutate the tree. Undeclared, the run blocks with exit `18`
instead of closing over a condition nobody checked.

The whole record lives in `ORCHESTRATION.md`'s `## Closure delta` section and is
re-read on re-entry: a run interrupted between the freeze and the terminal write
reuses the freeze without redoing the task work, a corrupt record blocks, and a
frozen fingerprint that no longer matches the tree voids the freeze.

### Re-entry

Re-running against an existing `ORCHESTRATION.md` resumes it (031 FR-011):
completed tasks are not re-delegated, findings are not duplicated, and counters
and the budget carry over without resetting. The runner refuses rather than
guesses — `16` covers a document written by another executor, a corrupt table, a
budget that disagrees with itself, a State section that contradicts the Attempts
table, and a terminal abort.

`ACTIVE` alone does not mean a runner is alive. The document records the writer's
pid and host, so an `ACTIVE` run whose pid is dead **on this host** is an
interrupted run and resumes; one whose pid is alive is refused as concurrent
(`15`); and one recorded on a different host blocks (`16`), because guessing that
a remote pid is dead is how two runners end up in the same worktree.

## Backends

- **stub** — always present, scripted, deterministic. The whole suite runs on it,
  with no provider call and no cost.
- **claude** — Claude Agent SDK, imported lazily. Optional dependency:
  `python3 -m pip install claude-agent-sdk`. Credentials come from the
  environment only.
- **codex** — *Codex backend implementation is present but gated.* Codex
  execution requires local CLI verification. Codex parity is not claimed. It
  refuses to run without `--allow-unverified-backend` because the isolation flag
  set is enforced but unverified — see `docs/KNOWN_DEBT.md`, DEBT-001 and
  DEBT-002.

## Tests

Stdlib only — no pytest, no venv, nothing to install (D009):

```bash
PYTHONPATH=runner python3 -m unittest discover -s runner/tests -t runner
```

`tests/conformance/PROTOCOL_TRANSCRIPTION.md` is the documented clause-by-clause
comparison against spec 031, and `test_transcription.py` keeps that table honest.
Read its "Observed divergence" section before changing severity handling.

## Prohibitions

The runner never runs `git commit`, `git push` or `git merge`, never edits a spec
`Status` line, and never writes outside the feature folder and the delegated
agents' path scope (FR-012).
