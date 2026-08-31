# `runner/` — phase-2 executor for the SDD autonomous loop

Spec: [`specs/features/040-agent-sdk-runner/`](../specs/features/040-agent-sdk-runner/).
Protocol: **spec 031**, corrected by **spec 032**. This package transcribes that
protocol; it does not define it. Where this runner and
`skills/sdd-orchestrate/SKILL.md` disagree, **this runner is wrong** (D007).

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

### Exit codes

`0` converged · `10` gate refused · `11` human-gated escalation · `12` cap abort
· `13` budget exhausted · `14` backend precondition · `15` concurrent run ·
`16` state unresumable · `17` processed but not converged · `18` closure not proven ·
`70` internal error.

### Finalization, freeze and closure delta

A converged task list is not a closed run. Before it may say `DONE` the runner
re-checks 031's DONE conditions — no unconverged task, no open finding, no
waiting escalation, a coherent budget, every `TASKS.md` item checked — then
re-reviews any approval a later task's change staled, runs
`final-conformance-reviewer` once, and only then **freezes**: it records the
approved implementation fingerprint together with a per-path content map of the
tree at that instant.

After the freeze it delegates the owning lifecycle skills (`/spec-review`,
`/spec-close`, `/pr-description`) and requires each one's APPROVE. It never
writes a spec `Status` itself. Finally it compares the tree against the frozen
map: generated artifacts, a `SPEC.md` change confined to its `## Status` section
and `TASKS.md` checkbox bookkeeping are **allowed**; anything else is
**unexpected** and returns the run to REVIEW with the paths named.

`--baseline` is 031's second DONE condition. Declared, it must pass and must not
mutate the tree. Undeclared, the closure record says
`NOT DECLARED - condition 2 of 031's termination contract is unobserved`, and so
does the run's reason line.

The whole record lives in `ORCHESTRATION.md`'s `## Closure delta` section and is
re-read on re-entry: a run interrupted after the freeze resumes into the
lifecycle steps without redoing the task work, a corrupt record blocks, and a
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
