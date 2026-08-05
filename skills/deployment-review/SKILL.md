---
name: deployment-review
description: Review deployment procedures — deploy scripts, runbooks, provisioning and bootstrap steps — for step ordering, idempotency, re-run behaviour after a partial failure, rollback paths and secret placement. Not for CI/CD pipeline config — that is /pipeline-review. Not for a release go/no-go — that is /release-readiness. Not for application-code security — that is /security-review.
triggers:
  - When deploy scripts, `Makefile` deploy targets, provisioning or bootstrap steps change
  - When a runbook, `infra/` document or deployment procedure is added or edited
  - When backup, restore or systemd unit files change
  - When the user asks "is this deploy safe to re-run?" or "what happens if this fails halfway?"
---

## SDD Contract

```yaml
category: domain-reviewer
inputs: [diff, deployment-artifacts, RUNBOOK.md?]
outputs: [deployment-findings]
side_effects: none
writes_code: false
writes_specs: false
analysis_only: true
primary_agent: domain-reviewer
secondary_agents: [security-reviewer]
profile_scope: [delivery-operations]
provider_specific: false
```

# Deployment Reviewer

## Purpose

Review the **procedure** that puts software on a machine: its order, its assumptions, and what it
does when it fails halfway.

Deployment knowledge is the kind that lives in one operator's head and gets rediscovered under
pressure. Most of it is counter-intuitive, which is exactly why it dies when it is not written
down. This skill reads the procedure as an artifact and asks the questions the author already
knows the answer to and never wrote.

## Extends

Nothing generic — this is the entry point for deployment artifacts. It runs alongside
`container-review` (the image and its runtime posture) and `pipeline-review` (what CI verifies).
Sequence does not matter; the three do not depend on each other's findings.

## What this skill checks

### Ordering and stated prerequisites

The most common deployment defect is a step that works only because something else already
happened, and does not say so.

- Does each step state its precondition, or does it assume the state left by the step above?
- Is there a step that must run **before** something the reader would naturally do first? A
  reverse proxy that must be up *before* provisioning, not after, is the shape to look for —
  ordering constraints that read as backwards are the ones most likely to be reordered by someone
  tidying up.
- Does any step depend on state that does not exist yet at that point — DNS that has not
  propagated, a certificate not yet issued, a volume not yet created? A bootstrap step that must
  call `localhost` because the public hostname does not resolve yet is a correct-looking oddity
  that someone will "fix" into a failure.
- Are manual steps and automated steps distinguishable, or are they in one undifferentiated list?

### Idempotency and re-run after partial failure

Assume the procedure died at step 4 of 9. This is the normal case, not the edge case.

- What does a re-run do? Resume, restart cleanly, or corrupt?
- Which steps are safe to repeat and which are not? Say so per step, not in a preamble.
- Is there a step that succeeds the first time and fails the second — a `create` that should be a
  `create-or-update`, an append that duplicates, a migration with no guard?
- Is there a step that fails the first time and succeeds the second? That is a hidden ordering
  dependency, not a flake.
- If the procedure is not idempotent, does it say so, and does it say how to get back to a clean
  starting state?

### Converge versus first boot

A procedure written against an empty machine and a procedure run against a live one are different
procedures. Many are written as the first and run as the second.

- Which steps only apply to a first deployment (creating the database, issuing the first
  certificate, seeding an admin user)?
- Which steps are safe on every converge?
- Does a first-boot-only step silently do damage on a converge — reseeding, resetting a password,
  overwriting a config that has since been edited by hand?

### Rollback

- Is there a rollback path, and is it a **path** or a wish? "Restore from backup" is a wish unless
  the restore procedure is written and has been run.
- Does rollback cover the data layer, or only the application? A rolled-back application against a
  forward-migrated schema is a second outage.
- Is there a point in the procedure after which rollback is no longer possible? Name it explicitly
  — that is the moment the operator needs to know about, and it is almost never written down.

### Secret placement

Not whether secrets exist — **where they land**.

- Which file holds each secret, with what permissions, owned by whom?
- Does any secret reach a process argument, and therefore `ps`, or a shell history, or a log line
  at the default log level?
- Is a secret written to a world-readable location, even briefly? A temporary file created before
  its permissions are set is a real window, and a dump written to `/tmp` and deleted on exit is
  readable for its whole lifetime.
- Does the procedure fail **closed** when a secret is missing, or does it silently degrade — an
  encryption step that skips when no key is present, producing an unencrypted artifact that looks
  like a success, is the canonical case.
- Cite the location and the class of secret. **Never quote a discovered secret value.**

### Health checks and failure behaviour

- After each step that starts something, is there a check that it actually works — not that the
  process is running, that it is serving?
- What does the procedure do when a health check fails: stop, continue, retry forever?
- Is there a step whose failure is invisible because its exit code is discarded (`|| true`, an
  unchecked pipeline, a backgrounded command nobody waits for)?

### Procedure fragmentation — a finding in its own right

**If the ordered procedure exists in more than one document and in full in none, that is a High
severity finding**, even when every individual document is correct.

A procedure split across an `infra/` README, a checklist at the end of a closed spec, and a
priority list in an audit note cannot be followed — it has to be reconstructed, and the
reconstruction is done under pressure by whoever is on call. Report it as a defect of the
documentation set, name every location the procedure is scattered across, and recommend one
`RUNBOOK.md` as the single ordered home.

The test: **could a second person, who did not write this, follow it end to end without asking
the author a question?** If reading three files in the right order is required to answer that,
the answer is no.

## Infrastructure weight is not this skill's business

Review the procedure that exists. Do not recommend orchestration, managed services, or a heavier
topology because the current one looks simple — a procedure that is correct, ordered and rehearsed
on one host is a good procedure, not a stage to move beyond.

If what you are looking at is genuinely an infrastructure mismatch rather than a procedural defect,
say so plainly as an observation and stop there: name the symptom and the measurement behind it,
and do not prescribe a tier. No shipped skill owns that judgment — `rightsizing-advisor` is
declared in this profile's `plannedSkills` and did not ship (spec 024 D013).

## Output format

```markdown
## Deployment Review

**Verdict:** PASS | PASS WITH NOTES | FAIL

### Procedure inventory

| Document | Covers | Ordered? | Complete? |
|---|---|---|---|
| infra/README.md | steps 1-4 | partial | no |

### Findings

| # | Severity | File:Line | Finding | Action |
|---|---|---|---|---|

### Re-run behaviour

- (What a re-run after a failure at each risky step actually does)

### Rollback note

- (Is there a path, does it cover data, and where is the point of no return)
```

## When this skill does not apply

**The presence of CI is not the presence of a deployment.** A repository whose only delivery
artifact is a workflow that lints and tests has nothing for this skill to review — there is no
procedure. Say so and stop; do not manufacture findings about a missing runbook for a project that
does not deploy itself. `pipeline-review` applies there; this skill does not.

This skill applies when a **procedure** exists: a deploy script, a `Makefile` deploy target, a
runbook, an `infra/` document, provisioning or bootstrap steps, a systemd unit, or a backup/restore
script — or deploy steps inlined in a workflow. A `Dockerfile` and a test-only pipeline are not a
procedure.

**In a monorepo, findings are scoped per deployable.** Detection fires per artifact path, not per
repository: if three services each have their own deploy path, review each separately and name
which deployable every finding concerns. A finding that does not say which service it belongs to
is not actionable.

## What this skill does NOT do

- Does not review CI/CD pipeline configuration — job graphs, gating, artifact provenance (that's
  `pipeline-review`). When deploy steps are inlined in a workflow file, this skill reviews the
  ordering and idempotency of those steps; `pipeline-review` reviews the gating around them.
- Does not give a release go/no-go, and does not ask whether a rollback was ever *rehearsed*
  (that's `release-readiness`). This skill reviews the artifact; that one gates the release.
- Does not review Dockerfiles or Compose files (that's `container-review`).
- Does not review application-code security — injection, authz, input validation (that's
  `security-review`).
- **Does not review infrastructure-as-code state semantics** — Terraform/Pulumi/Ansible state
  handling, drift, or destructive operations concealed in a plan. No shipped skill covers these;
  `iac-review` is declared in the `delivery-operations` profile's `plannedSkills`. Say so rather
  than producing a shallow reading of a `.tf` file.
- **Does not review Kubernetes manifest semantics** — probes, resource limits, `securityContext`,
  RBAC, disruption budgets. It reviews the rollout *procedure* only. `kubernetes-review` is
  likewise `plannedSkills`.
- Does not execute any part of a deployment, resolve a secret reference, or connect to a host.
  Static review of artifacts only.
- Does not modify code or configuration.

## Context economy

- Read the deployment artifacts and the diff once.
- Do not read application source unless a step references it directly.
- Report only findings that change what an operator would do.
- Always end with the next recommended command.
