---
name: release-readiness
description: Release gate asking what was actually rehearsed — executed rollback, restored backup, observability that would catch a silent failure, a stated perimeter, and one runbook a second person could follow. Produces a Go/No-go, not file:line findings. Not a review of deployment artifacts — that is /deployment-review. Not logging-code quality — that is /observability-reviewer.
triggers:
  - Before a first production deployment, or a first paying-customer deployment
  - Before a release that changes deployment, data or perimeter
  - When the user asks "are we ready to ship this?" or "what happens at 3am if this breaks?"
  - After `/deployment-review` and `/container-review` have passed and the question is operational
---

## SDD Contract

```yaml
category: quality-review
inputs: [RUNBOOK.md?, deployment-artifacts, operator-answers]
outputs: [go-no-go-verdict]
side_effects: none
writes_code: false
writes_specs: false
analysis_only: true
primary_agent: domain-reviewer
secondary_agents: [security-reviewer]
profile_scope: [delivery-operations]
provider_specific: false
```

# Release Readiness

## Purpose

This is a **gate, not a review**. It does not read a diff and does not produce file:line findings.
It asks one question in five parts: *if this goes wrong at 3am, does anyone have what they need?*

It exists because reading code does not find the failures that matter here. A rollback that has
never been executed, a backup that has never been restored, and a monitor that would not fire on
a silent failure all look correct on the page. They are only revealed by exercising them.

## The rule that makes this gate worth running

Every precondition is recorded in exactly one of three states:

| State | Means |
|---|---|
| **Rehearsed** | Someone actually did it, on this system, and it worked. Dated. |
| **Written but untested** | It is documented, configured or scripted, and has never been run. |
| **Absent** | It does not exist. |

**"Written but untested" never counts as satisfied.** That is the whole point — it is the state
that reads as done in every other kind of review, and it is the state that fails in production.

You cannot verify a rehearsal yourself. When the answer comes from a person, record it as an
attributed, dated claim: *"restore rehearsed 2026-07-14 — reported by <name>"*. **An undated "yes"
is recorded as written but untested.** Do not upgrade a claim because it was stated confidently.

## The five preconditions

### 1. Rollback — has it been executed?

- Is there a rollback path, and has someone **run it** on this system?
- Does it cover data, or only the application? A rolled-back application against a
  forward-migrated schema is a second outage.
- How long does it take, and who is allowed to trigger it?
- Is there a point after which rollback is impossible, and is that point written down?

### 2. Restore — has a backup been restored, not just configured?

- Do backups exist, and does a **restore** procedure exist?
- Has a restore been performed from a real backup artifact into a usable state? A backup job
  reporting success is not evidence — it proves a file was written, not that it can be read back.
- How old is the newest backup that has actually been restored?
- Does the backup fail **closed**? A backup that silently degrades — skipping encryption when a
  key is missing, or writing a truncated dump on a partial failure — produces an artifact that
  looks like a success and is not one.
- Where does the artifact live while it is being made, and who can read it there? A dump written
  to a shared temporary directory is readable for its entire lifetime, not just at the end.

### 3. Observability — would a *silent* failure surface?

Not "is there logging". The question is whether anything would fire when nothing crashes.

- If the application returned a correct-looking wrong answer, what would notice?
- If a background job stopped running entirely, what would notice, and how long would it take?
- If a downstream dependency started failing 20% of requests, what would notice?
- Is there a signal that someone actually **looks at**, or an alert that actually **reaches a
  person** — and which person, through which channel?
- Are there alerts that fire routinely and get ignored? An alert nobody trusts is absent, not
  present.

### 4. Perimeter — what is exposed, and what enforces it?

- Which services are reachable from outside the host or cluster? Enumerate them.
- **What actually enforces that boundary** — and does the person answering know? A host firewall
  is not the answer when container port publishing bypasses it; the binding address is.
- Are administrative interfaces, metrics endpoints, and databases among the exposed set?
- Who holds the credentials, and what happens on the day that person is unavailable?

### 5. Runbook — could a second person follow it?

- Is there **one** document with the ordered procedure, or is it spread across several?
- Could someone who did not write it deploy, verify, and roll back without asking the author a
  question? This is the test, and the author is not qualified to answer it — ask what happened the
  last time someone else tried.
- Does it state what a re-run does after a partial failure?
- When was it last followed end to end, by whom?

## Not a checklist to pass

A No-go is a useful outcome, not a failure of the release. The purpose is to make the unmet
preconditions **explicit and owned** before the deployment, rather than discovered during it.

Equally: an unmet precondition may be an accepted risk. Record it as accepted, by whom, with the
reason — an accepted risk that is written down is a different thing from one nobody named.

## Infrastructure weight is not this skill's business

**This is the skill most likely to get this wrong**, because every unmet precondition has an
expensive answer available. It does not have one.

An unmet precondition is closed by **the smallest thing that closes it**. "No rollback has been
executed" is answered by executing one, not by adopting blue-green deployment. "Nothing would
catch a silent failure" is answered by one external check that pages someone, not by a monitoring
stack. "One host is a single point of failure" is answered by a rehearsed rebuild procedure and
off-box backups — redundancy is one option among several and is rarely the cheapest.

A single host, a Compose stack and a manual deploy can all pass this gate. What cannot pass is an
untested rollback, an unrehearsed restore, or a runbook only its author can follow. **Never issue
a No-go whose remedy is a heavier architecture** — if that is the only remedy you can think of, the
precondition has been misread.

No shipped skill owns the infrastructure-weight judgment; `rightsizing-advisor` is declared in this
profile's `plannedSkills` and did not ship (spec 024 D013).

## Monorepos

Preconditions are assessed **per deployable being released**, not per repository. A rehearsed
restore for one service says nothing about another. If the release covers several deployables,
state which ones the verdict applies to and give a per-deployable precondition table.

## Output format

```markdown
## Release Readiness — <deployable(s) covered by this release>

**Verdict:** GO | GO WITH ACCEPTED RISKS | NO-GO

### Preconditions

| # | Precondition | State | Evidence / claim | Source |
|---|---|---|---|---|
| 1 | Rollback executed | written but untested | script exists, never run | repo |
| 2 | Restore rehearsed | rehearsed 2026-07-14 | restored to staging, verified | reported by <name> |
| 3 | Silent-failure signal | absent | uptime check only | repo |
| 4 | Perimeter stated | rehearsed | 3 services published, bound to loopback | repo |
| 5 | Single runbook | written but untested | RUNBOOK.md, never followed by a second person | repo |

### Unmet preconditions

- (Each, with what it would take to move it to rehearsed)

### Accepted risks

- (Unmet preconditions the owner has explicitly accepted, with who accepted them and why)

### First deployment

- (If nothing has ever been deployed, every precondition is *absent* rather than failed — this
  section becomes the first-deployment checklist instead of a gate result)
```

## What this skill does NOT do

- Does not review deployment artifacts for defects — ordering, idempotency, secret placement
  (that's `deployment-review`). That skill reviews the artifact; this one asks whether it was ever
  exercised.
- Does not review Dockerfiles or Compose files (that's `container-review`), or CI configuration
  (that's `pipeline-review`).
- Does not review logging, metrics or tracing **code** — structured logging, Micrometer, spans,
  actuator design (that's `observability-reviewer`, Java/Spring). This skill is stack-agnostic and
  asks only whether *some* signal would surface a silent failure; it reads no logging code.
- Does not judge test coverage or quality (that's `qa-review`).
- Does not execute a rollback, run a restore, probe a live system, or verify any claim technically.
  **It cannot confirm a rehearsal happened** — it records claims as claims, attributed and dated.
- Does not run per-diff. It is a release gate, and `review-all` deliberately does not route to it.
- Does not modify code or configuration.

## Context economy

- Read the runbook and deployment artifacts once.
- Ask the operator only for what cannot be read from the repository — rehearsal history, alert
  destinations, credential ownership.
- Do not re-derive `deployment-review`'s findings; if it has run, cite it.
- Always end with the next recommended command.
