---
name: container-review
description: Review Dockerfiles and Compose files for image pinning, port binding as a perimeter decision, running as root, healthcheck semantics, volume lifecycle, secrets in build args or layers, and multi-stage hygiene. Not for the deploy procedure itself — that is /deployment-review. Not for application-code security — that is /security-review.
triggers:
  - When a `Dockerfile`, `Containerfile`, `docker-compose*.yml` or `compose*.yml` changes
  - When a base image, published port, volume or container user changes
  - When a service is added to a Compose stack
  - When the user asks "is this container safe to expose?" or "what does `down -v` destroy?"
---

## SDD Contract

```yaml
category: domain-reviewer
inputs: [diff, Dockerfile, compose-files]
outputs: [container-findings]
side_effects: none
writes_code: false
writes_specs: false
analysis_only: true
primary_agent: domain-reviewer
secondary_agents: [security-reviewer]
profile_scope: [delivery-operations]
provider_specific: false
```

# Container Reviewer

## Purpose

Review the image and its runtime posture: what it is built from, what it exposes, who it runs as,
what it persists, and what it leaks.

A container file is short, looks declarative, and hides several decisions that are hard to reverse
once running — most importantly, **where the network perimeter actually is**.

## Extends

Nothing generic. Runs alongside `deployment-review` (the procedure) and `pipeline-review` (what CI
verifies). No ordering dependency between them.

## What this skill checks

### Image pinning

- Is the base image pinned, or does it float? `FROM node:latest` and `FROM postgres` are the same
  defect: the image that passed review is not the image that will run.
- A major-version tag (`node:22`) still floats within that major. Whether that is acceptable is a
  judgment call the project should have made explicitly — a digest pin (`@sha256:…`) is the
  strongest form, a minor-version tag the common compromise.
- Does the same image reference appear in more than one place with different tags — a Dockerfile
  and a Compose file that disagree?

### Port binding is the perimeter

**This is the finding most often missed, and the consequence is a service exposed to the internet
by a file nobody thought of as a firewall rule.**

- `ports: "5432:5432"` publishes on **all interfaces**. `ports: "127.0.0.1:5432:5432"` does not.
  The difference is the entire perimeter for that service.
- On Linux, **Docker inserts its own iptables rules ahead of the host firewall**, so a published
  port is typically reachable even when the host firewall appears to deny it. A `ufw` or
  `firewalld` rule is not evidence that a published port is closed — the binding address is.
- Which services genuinely need to be reachable from outside the host? Databases, caches, queues,
  admin UIs and metrics endpoints usually do not; they need to be reachable from *other containers*,
  which the Compose network already provides without publishing anything.
- `expose:` documents a port to other containers and publishes nothing — check that a
  `ports:` entry was not used where `expose:` was meant.
- Is `network_mode: host` used? It bypasses the whole question and republishes everything.

### Running as root

- Does the final stage set a non-root `USER`? Absent a `USER` line, the container runs as root.
- If a non-root user is set, does it actually own the paths it writes to at runtime — or will the
  container fail on first write and get "fixed" by reverting to root?
- Are capabilities added (`cap_add`), is `privileged: true` set, or is a Docker socket mounted?
  Each of those grants effective host access and needs a stated reason.

### Healthcheck semantics

- Is there a `HEALTHCHECK` / `healthcheck:` at all?
- Does it prove the service is **serving**, or only that the process is alive? A check that the
  port is open, or that `true` exits zero, reports healthy for a process that answers every
  request with a 500.
- Do `start_period`, `interval` and `retries` match how long the service actually takes to become
  ready? A start period shorter than real startup produces a restart loop that looks like a crash.
- Does anything **depend** on the healthcheck? `depends_on` with `condition: service_healthy` uses
  it; a plain `depends_on` waits only for the container to start, not to be usable.

### Data persistence and volume lifecycle

- Is state on a named volume, a bind mount, or the container filesystem? State on the container
  filesystem is destroyed by the next `docker compose up --force-recreate`.
- **What does `docker compose down -v` destroy?** Name it explicitly. It is the command a tired
  operator runs to fix a stuck stack, and it removes named volumes.
- Is any volume mounted read-write that only needs read?
- Are backups taken from the volume, and does the backup path appear anywhere in this stack — or
  is persistence assumed and never verified?

### Secrets

- Are secrets passed as `ARG`? **Build args are visible in the image history** and survive in the
  layer metadata even if the value is later overwritten.
- Does a secret appear in a `RUN` command, and therefore in a layer and in build logs?
- Are secrets in `environment:` inline in the Compose file, which is usually committed? Environment
  variables are also readable from the host for a running container.
- Is a `.env` file referenced, and is it gitignored? Is a secrets file mounted with permissions
  that the container's user cannot over-read?
- Does `COPY . .` pull a `.env`, a private key, or a `.git` directory into the image? Check for a
  `.dockerignore`, and check what it actually excludes.
- Cite the location and the class of secret. **Never quote a discovered secret value.**

### Multi-stage hygiene

- Does the final stage inherit only what it needs, or does it start from the build stage and carry
  the toolchain, the source and the package cache into production?
- Are build-time credentials confined to a stage that is not the final one? A secret in a discarded
  stage is not in the final image — a secret in the final stage's history is.
- Layer ordering: are the least-frequently-changing steps first, so a source change does not
  invalidate the dependency install?

## Infrastructure weight is not this skill's business

Review the containers that exist. A Compose stack on a single host is a legitimate production
architecture, and this skill has no opinion about whether it should be something else — not a
stage to move beyond.

If that question is genuinely on the table, treat it as out of scope: no shipped skill owns it.
`rightsizing-advisor` is declared in this profile's `plannedSkills` and did not ship (spec 024
D013).

## Monorepos

Detection fires **per artifact path, not per repository**. If several services each have their own
`Dockerfile` or Compose stack, review each separately and name which deployable every finding
concerns — the service inventory below is per deployable. A finding that does not say which image
it belongs to is not actionable.

## Output format

```markdown
## Container Review — <deployable, if the repo has more than one>

**Verdict:** PASS | PASS WITH NOTES | FAIL

### Service inventory

| Service | Image (pinned?) | Published ports | Runs as | Healthcheck | Persistent state |
|---|---|---|---|---|---|
| db | postgres:16.3 (minor) | 127.0.0.1:5432 | postgres | pg_isready | volume: pgdata |

### Findings

| # | Severity | File:Line | Finding | Action |
|---|---|---|---|---|

### Exposure summary

- (Which services are reachable from outside the host, and whether that is intended)

### Destroyed by `down -v`

- (Named volumes and what data they hold)
```

## What this skill does NOT do

- Does not review the deploy procedure — ordering, idempotency, rollback, re-run after partial
  failure (that's `deployment-review`).
- Does not review CI/CD configuration, including the job that builds the image (that's
  `pipeline-review`).
- Does not give a release go/no-go (that's `release-readiness`).
- Does not review application-code security — injection, authz, input validation, session handling
  (that's `security-review`). A secret in a build arg is this skill; a secret hardcoded in a source
  file is that one.
- **Does not review Kubernetes manifests** — pod `securityContext`, probes, resource limits, RBAC.
  It reviews the image those manifests would run. `kubernetes-review` is declared in the
  `delivery-operations` profile's `plannedSkills` and ships with no shipped equivalent today.
- Does not build, run, pull or scan images, and does not check published CVEs for a base image —
  that is a scanner's job, not a reviewer's. Static review of the files in the diff.
- Does not modify code or configuration.

## Context economy

- Read the container files and the diff once.
- Do not read application source unless a `COPY` or entrypoint points at it directly.
- Report only findings that change what runs or what is exposed.
- Always end with the next recommended command.
