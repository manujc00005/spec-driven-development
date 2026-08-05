---
name: pipeline-review
description: Review CI/CD configuration for the gap between what a pipeline verifies and what its job names imply, plus gating versus reporting, migration-drift detection, secret exposure in logs, artifact provenance and cache correctness. Not for whether the tests are good — that is /qa-review. Not for the deploy procedure itself — that is /deployment-review.
triggers:
  - When `.github/workflows/`, `.gitlab-ci.yml`, `Jenkinsfile`, or equivalent CI config changes
  - When a job, step, gate or branch-protection assumption is added or removed
  - When a pipeline gains a deploy, migration or release step
  - When the user asks "does CI actually check that?" or "why did a broken build get merged?"
---

## SDD Contract

```yaml
category: domain-reviewer
inputs: [diff, ci-config]
outputs: [pipeline-findings]
side_effects: none
writes_code: false
writes_specs: false
analysis_only: true
primary_agent: domain-reviewer
secondary_agents: [security-reviewer]
profile_scope: [delivery-operations]
provider_specific: false
```

# Pipeline Reviewer

## Purpose

Review what a pipeline **actually verifies**, as opposed to what its name, its job names and its
green checkmark imply.

A pipeline is a claim about correctness that everyone downstream trusts without reading. When the
claim is narrower than it appears, nothing surfaces the difference — the build is green, the badge
is green, and the gap is discovered in production.

## Extends

Nothing generic. Runs alongside `deployment-review` and `container-review`. It assumes `qa-review`
owns test quality and does not re-litigate it.

## What this skill checks

### First and mandatory: what is verified versus what is implied

**Start here on every review, before any other check.** Enumerate what the pipeline runs, then
compare it against what a reader would assume from the job names.

The canonical failure: a pipeline runs `lint`, `typecheck` and `test`, is named `verify` or `ci`,
and **never runs the build** — on a project whose deployable artifact is a build. Type-checking is
not compilation. A TypeScript project can typecheck cleanly and fail `next build` or `tsc --build`
on a config error, a missing asset, a route-level failure, or anything the bundler does that the
type-checker does not. The pipeline is green and there is **no automated evidence the application
compiles** at the moment it is deployed.

Ask, for each thing the project actually ships:

- Is it **built** in CI, or only checked?
- If it ships as a container image, is the image **built** in CI, or only on the deploy host?
- Are database migrations applied against a throwaway database anywhere before they run against a
  real one?
- Do the tests that run in CI include the layer the change touches, or only the fast unit tier?
- Is there a job whose name promises more than its steps deliver — `e2e` that runs two smoke
  checks, `security` that runs a linter, `verify` that verifies a subset?

Report the delta as a finding, not as a note. Severity scales with what deploys on green.

### Migration and schema drift

- Before any step that runs a migration against a real database, is there a check that the ORM
  schema and the migration files **agree**? Drift between them means the migration applied is not
  the schema the code expects.
- Is the migration step gated on the build and tests passing, or can it run first?
- Is there a dry-run, a plan output, or a review step for destructive operations?

### Gating versus reporting

A check that runs but does not block is documentation, not a gate.

- Which jobs can fail without stopping the merge or the deploy? `continue-on-error`, a
  non-required status check, a step whose failure is swallowed by `|| true`, a job outside the
  required set in branch protection.
- Is branch protection assumed by the pipeline but not verifiable from the repository? Say so —
  it is configuration outside the file being reviewed, and the review cannot confirm it.
- Does the deploy job depend on the verification jobs (`needs:`), or does it run in parallel with
  them and win the race?
- Can the deploy job be triggered manually in a way that skips the gates entirely?

### Secret exposure

- Are secrets echoed, printed on failure, or passed as command-line arguments where they land in
  the log?
- Does a step run with `set -x` or a debug flag that expands secret-bearing variables?
- Are secrets available to jobs triggered by forks? `pull_request_target` and equivalents run with
  repository secrets against **untrusted code** — treat any secret reachable from such a trigger as
  a High finding.
- Are third-party actions pinned to a commit SHA rather than a moving tag? A floating action tag
  has read access to the job's secrets.
- Cite the location and the class of secret. **Never quote a discovered secret value.**

### Artifact provenance

- Is the artifact that is deployed the same one that was tested, or is it rebuilt in the deploy
  job? A rebuild is a different artifact, however deterministic the build claims to be.
- Is the image tagged by commit SHA, or by a moving tag that another build can overwrite between
  test and deploy?
- Are artifacts passed between jobs explicitly, or reconstructed from the source each time?

### Cache correctness

- Can a cache key serve a stale artifact to a build or a deploy? A key that omits the lockfile
  hash, or a `restore-keys` prefix that matches an older entry, can hand a build dependencies it
  did not resolve.
- Is a build output cached under a key that does not include the source revision?
- Does cache restoration fail open — a corrupted or missing cache producing a partial build that
  still reports success?

## Infrastructure weight is not this skill's business

Review the pipeline that exists. A single workflow file that builds, tests and deploys one thing
is a complete pipeline, not a starting point — do not recommend a matrix, a multi-stage promotion
chain, self-hosted runners or a separate release pipeline because the current one looks small. The
finding is always a missing *verification*, never a missing *tier*.

No shipped skill owns the infrastructure-weight judgment; `rightsizing-advisor` is declared in this
profile's `plannedSkills` and did not ship (spec 024 D013).

## Monorepos

Detection fires **per artifact path, not per repository**. A monorepo may have one pipeline
covering several deployables, or one pipeline each. Either way, the "what this pipeline actually
verifies" table is filled in **per deployable** — the central question of this skill (is the thing
we ship actually built and gated?) has a different answer per shipped artifact, and a single
repository-wide verdict hides exactly the gap worth finding.

## Output format

```markdown
## Pipeline Review

**Verdict:** PASS | PASS WITH NOTES | FAIL

### What this pipeline actually verifies

| Deliverable | Built? | Tested? | Gated on? | Notes |
|---|---|---|---|---|
| web app (Next.js) | **no** | unit only | not required | typecheck mistaken for build |

### Findings

| # | Severity | File:Line | Finding | Action |
|---|---|---|---|---|

### Gates that are not gates

- (Checks that run but cannot block a merge or a deploy)

### Outside this file

- (Assumptions about branch protection or repo settings the review cannot confirm)
```

## What this skill does NOT do

- Does not judge whether the tests are good — coverage, edge cases, assertion quality, flakiness
  (that's `qa-review`). This skill asks whether CI **runs** them and **gates** on them.
- Does not review the deploy procedure — step ordering, idempotency, rollback, re-run after
  partial failure (that's `deployment-review`). When deploy steps are inlined in a workflow, this
  skill reviews the gating, provenance and secret exposure around them; `deployment-review` reviews
  the ordering of the steps themselves.
- Does not review Dockerfiles or Compose files, even when CI builds them (that's
  `container-review`).
- Does not give a release go/no-go (that's `release-readiness`).
- Does not review application-code security (that's `security-review`).
- Does not run the pipeline, trigger a workflow, or read CI logs from a provider API. Static review
  of the configuration in the repository.
- Does not modify code or configuration.

## Context economy

- Read the CI configuration and the diff once.
- Read `package.json` scripts (or the equivalent build manifest) once — it is what tells you
  whether a named script is a build or a check.
- Report only findings that change what merges or what deploys.
- Always end with the next recommended command.
