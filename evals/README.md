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

Each `evals/scenarios/<skill>.md` states four things:

- **Failure under test** — the specific thing a model does wrong without the skill.
- **System-prompt context** — the realistic context the guidance will live in.
- **User message** — a task that tempts the failure.
- **Observable criterion** — how a response is judged to exhibit the failure. It must be
  checkable by reading the response, without knowing which arm produced it.

If a skill's failure is only reachable across multiple turns, the scenario must **say so** rather
than substituting a weaker single-turn proxy and calling it covered.

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

| Verdict | Meaning |
|---|---|
| `NO-BASELINE-FAILURE` | Control exhibited the failure in fewer than 2 of 5 reps. The skill is not addressing an observed problem. |
| `INCONCLUSIVE` | Treatment results are split. Variance is itself the metric — when guidance lands, reps converge. Never round a split result up to a pass. |
| `EFFECTIVE` | Control exhibited the failure, treatment did not, consistently. |
| `INEFFECTIVE` | Control and treatment both exhibited the failure. |
| `HARMFUL` | Treatment exhibited the failure *more* than control. Prohibition-form guidance applied to an output-shaping failure is the known way to land here. |

## Reading the results is part of the method

Automated counts overstate both failure and success — template echoes and quoted
counter-examples masquerade as hits. **Every flagged match must be read by hand.** The result file
carries a `manually-read:` field; the script records the claim and cannot verify it. An unread
result is not evidence.

A result without a **model identifier** is not evidence either. Results are dated observations
against one named model, not guarantees about production sessions.

## Running it

```bash
export SKILL_EVAL_RUNNER='claude -p --model claude-sonnet-5'
bash scripts/skill-eval.sh verifier --reps 5
```

`$SKILL_EVAL_RUNNER` is any command that reads a prompt on stdin and writes the response to
stdout. The repo vendors no SDK and requires no API key of its own. With the variable unset, the
script prints both arm prompts and instructions instead of guessing a runner.

**Cost.** One skill at the default 5 reps is 10 model calls. A full sweep of the 9 current mindset
skills is **~90 calls**. The script prints the call count before running.

## When you change a skill

A PR that changes the content of a discipline or mindset skill must include an `evals/results/`
file produced **after** the change. See `CONTRIBUTING.md`.
