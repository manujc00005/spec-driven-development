# Skill evidence

Evidence that this framework's behaviour-shaping skills actually change what a model does.

Shipped by `specs/features/022-skill-evidence-harness/`. Nothing in this directory is installed
into a user's project: `profiles.json` never lists it, and the installers never copy it.

## The two halves, and why they are separate

**The static half runs in CI.** `scripts/check-consistency.sh` carries a `skill-form` check class
over every `skills/*/SKILL.md`. It is deterministic, free, and it fails the build.

**The behavioural half runs on demand.** `scripts/skill-eval.sh` calls a real model. It is
non-deterministic, costs tokens, and needs the network — so it is never on the CI path. Its output
is a committed, dated artifact that a reviewer reads instead of taking the author's word.

## What the static checks mean (and do not mean)

They enforce **two different things**, and conflating them causes two opposite mistakes.

| Check | Purpose | Applies to |
|---|---|---|
| `description` ≤ 400 chars | **Context economy.** Every description loads at session start, so its length is a standing per-session cost. | Every skill, whatever the text is doing. |
| `SKILL.md` body ≤ 600 lines | Context economy. Heavy reference belongs in linked sibling files. | Every skill. |
| No arrow chain / step sequence / 3+ `then` clauses in `description` | **Workflow-summary detection** — a description that summarises the workflow gets followed *instead of* the skill body. | Every skill. |

A length violation is **not** an accusation of workflow-summarising: `event-driven-reviewer` was
over budget because it enumerates review topics, which is legitimate keyword coverage.

Passing the proxies is **not** evidence a description is well-formed: `sdd-orchestrate`'s
description was a textbook workflow summary — "classify the task … delegate … then review,
validate … and keep SPEC/PLAN/TASKS/DECISIONS in sync" — and no proxy detected it. One `then`,
no arrows, no numbered steps. Only the length cap caught it.

**The proxies are three mechanical shapes, not a judgement engine.** False negatives are certain.
A prose-shaped workflow summary under 400 characters passes CI. That is the honest limit of the
deterministic half, and it is why the behavioural half exists.

## Directory contract

```
evals/
  scenarios/<skill>.md              one per discipline/mindset skill
  results/<skill>-<YYYY-MM-DD>.md   one per run, committed
```

### Scenario format

Each `evals/scenarios/<skill>.md` states five things:

- **Failure under test** — the specific thing a model does wrong without the skill.
- **System-prompt context** — the realistic context the guidance will live in.
- **User message** — a task that tempts the failure.
- **Observable criterion** — how a response is judged to exhibit the failure. It must be
  checkable by reading the response, without knowing which arm produced it.
- **Detection pattern** — one ERE, matched case-insensitively against the response. It flags
  candidates; it does not decide the verdict (see *Reading the results* below).

If a skill's failure is only reachable across multiple turns, the scenario must **say so** rather
than substituting a weaker single-turn proxy and calling it covered.

#### Scenarios must be self-contained

**A scenario may not reference a file, path, or repository state the model cannot see.** Paste the
code, diff, or artifact inline, and ask for a text answer rather than a file edit.

This is not style advice — it is what two discarded sweeps cost. A CLI runner is an *agent*: it
resolves the situation you describe against the situation it is actually in, and reports the
mismatch. Given a scenario about `src/utils/format.ts`, it answered:

> "The described repo and file don't actually exist in this environment — the working directory is
> empty and there's no `src/utils/format.ts` anywhere on disk. I don't want to fabricate the
> existing `formatDate` function or guess at its style…"

Both arms answered about the mismatch, the failure under test never occurred, and the tally was
confidently wrong in a way only reading the responses revealed. Disabling the runner's tools does
not help — it then asks you to paste the file. Self-containment is the only form that survives.

### Which skills need a scenario

Every skill whose `## SDD Contract` declares `category: mindset`. The set is resolved by parsing
that field — never from a hardcoded list, so a new mindset skill is covered the day it lands.

## The control arm is mandatory

Every run has two arms:

- **Control** — the scenario alone, with no guidance.
- **Treatment** — the scenario plus the skill's full `SKILL.md`.

**If the control does not exhibit the failure in at least 2 of 5 reps**, the result is
`NO-BASELINE-FAILURE` and the finding is that *the skill has no demonstrated problem to solve*.
A treatment arm must never be reported as a success in that case. Without a control you are
measuring whether a model can follow instructions, which was never in question.

## Verdicts

**Order matters.** The verdicts are not independent labels — they are a cascade, and the first
matching rule wins:

| # | Verdict | Rule |
|---|---|---|
| 1 | `HARMFUL` | Treatment exhibited the failure *more* than control. Prohibition-form guidance applied to an output-shaping failure is the known way to land here. |
| 2 | `NO-BASELINE-FAILURE` | Control exhibited the failure in fewer than 2 of 5 reps. The skill is not addressing an observed problem. |
| 3 | `EFFECTIVE` | Treatment never exhibited the failure. |
| 4 | `INEFFECTIVE` | Treatment exhibited it exactly as often as control. |
| 5 | `INCONCLUSIVE` | Treatment reduced the failure without eliminating it. Variance is itself the metric — when guidance lands, reps converge. Never round this up to a pass. |

**`HARMFUL` is checked first on purpose, even when the control arm never failed.** A skill whose
treatment arm exhibits a failure the control did not is the single most important thing this
harness can surface, and reporting it as merely "no baseline" buried exactly that signal on a real
run. When both apply, the verdict is `HARMFUL` and its note carries the missing-baseline caveat.

## Reading the results is part of the method

Automated counts overstate both failure and success — template echoes and quoted
counter-examples masquerade as hits. **Every flagged match must be read by hand.** The result file
carries a `manually-read:` field; the script records the claim and cannot verify it. An unread
result is not evidence.

A result without a **model identifier** is not evidence either. Results are dated observations
against one named model, not guarantees about production sessions.

## Running it

```bash
export SKILL_EVAL_RUNNER="claude -p --setting-sources '' --model claude-sonnet-5"
bash scripts/skill-eval.sh verifier --reps 5
```

`$SKILL_EVAL_RUNNER` is any command that reads a prompt on stdin and writes the response to
stdout. The repo vendors no SDK and requires no API key of its own. With the variable unset, the
script prints both arm prompts and instructions instead of guessing a runner.

**The runner must isolate the call and pin a model, or the run is refused before it costs
anything.** For Claude Code that is `--setting-sources ''`; for Codex,
`--ignore-user-config --ephemeral`. Both providers also need `--model <id>`. A runner the harness
does not recognize — a wrapper script, an SDK shim — needs `--allow-unisolated`, which runs but
stamps the result file as un-isolated with an operator-asserted model. That stamp is the point:
an un-isolated result is a weaker artifact and has to be legible as one.

### The runner never runs in this repo

Each call executes in an empty scratch directory, not the working tree. A CLI runner inherits its
working directory, and the first sweep ran inside this repository: the model read the real
filesystem and this project's `CLAUDE.md`, then answered about *this project* instead of the
scenario. Every "hit" in that sweep was a repo filename appearing inside a clarifying question.

**The operator's own configuration is excluded too — enforced, not requested.** The sandbox alone
never handled this: a user-level config still loaded, so every result carried whatever standing
instructions the operator happened to have, in *both* arms. A standing "always answer concisely"
moves the control arm toward the treatment arm and quietly shrinks the delta the harness exists to
measure.

`--setting-sources ''` closes it, and the harness refuses to run without it. Measured on Claude
Code **2.1.223** with a canary instruction in `~/.claude/CLAUDE.md`: present in the response
without the flag, absent with it. Settings, plugins, hooks and user memory are all suppressed.
See spec 028, D007 for the probe.

Read that as the dated observation it is, not a guarantee. It covers one CLI version, and it says
nothing about environment variables or anything a wrapper script injects — which is why an
unrecognized runner is refused rather than assumed clean. The result file now records the
isolation mechanism and the model's provenance alongside the runner command, so a reader can tell
a clean run from an `--allow-unisolated` one without taking the author's word for it.

**Cost.** One skill at the default 5 reps is 10 model calls. A full sweep of the 9 current mindset
skills is **~90 calls**. The script prints the call count before running.

## When you change a skill

A PR that changes the content of a discipline or mindset skill must include an `evals/results/`
file produced **after** the change. See `CONTRIBUTING.md`.
