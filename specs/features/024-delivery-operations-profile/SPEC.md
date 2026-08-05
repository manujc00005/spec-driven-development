# Feature Spec: Delivery-operations profile

## Status

Done

## Problem

This framework governs software up to the moment it merges, and then stops.

All 61 skills cover specification, implementation, review or mindset. All 7 profiles cover
language and domain stacks. Nothing covers how reviewed code reaches a machine and stays alive
there: deploy sequencing, containers, CI/CD, release gating, rollback.

Four things make this a defect rather than a missing nice-to-have.

1. **The framework already promises this coverage and does not deliver it.** A skill named
   `kubernetes-deployment-reviewer` is referenced in four committed places and **exists nowhere**:
   - `skills/spring-security-reviewer/SKILL.md:119` — *"Does not review network/infrastructure
     security (that's `kubernetes-deployment-reviewer`, Phase 3)."* This is a shipped skill
     handing off to a skill that does not exist. Spec 021 made routing authoritative; this is a
     live routing dead end inside that authority.
   - `docs/_templates/DEPLOYMENT.md:5` — *"Essential for /kubernetes-deployment-reviewer"*. A
     template installed into user projects tells them to run a command that will not resolve.
   - `docs/ROADMAP_JAVA_SPRING_CONTEXT.md:152,256` — carried as a roadmap row since Phase 3.

   The gap is therefore not "we never thought about deployment". It is "we told users we cover
   deployment, in artifacts we ship, and we do not."

2. **`review-all` makes a false claim.** Its description says it runs "all applicable specialized
   reviews". Its routing table (`skills/review-all/SKILL.md`) has thirteen reviewer rows and not
   one of them fires on a Dockerfile, a workflow file, a deploy script or a runbook. For any
   project that deploys itself the claim is currently false.

3. **A context template exists with no reviewer behind it.** `docs/_templates/DEPLOYMENT.md`
   ships today. The framework's thesis is that improvisation is replaced by *reviewable*
   artifacts; here the artifact exists and nothing reviews it.

4. **This gap costs more in an AI-assisted workflow than in a human one.** Deployment knowledge
   is the kind that lives in one operator's head, is rediscovered under pressure, and is exactly
   what an agent will confidently improvise when nothing constrains it.

### Motivating case (field evidence, not hypothesis)

A production project built with this framework — a multi-tenant sales-automation platform on a
single VPS running per-client Docker Compose stacks — was audited while preparing its first
paying-customer deployment. Four findings, each mapping to a requirement below:

- **The runbook existed in three places and nowhere in full.** The ordered procedure was split
  across `infra/README.md`, an unchecked 7-item checklist at the end of a closed spec's
  `IMPLEMENTATION_SUMMARY.md`, and a priority list in a separate audit document. Reconstructing
  the correct order required reading all three. No skill would have caught this, because no skill
  reads deployment artifacts at all. → FR-002, FR-007.

- **CI verified `lint`, `typecheck` and `test`, and never ran the build.** A Next.js application
  was about to be deployed to production with no automated evidence that it compiles, because
  `typecheck` was mistaken for build coverage. There was also no check for drift between the ORM
  schema and its migrations, immediately before running migrations against a real database. This
  is the canonical *pipeline verifies less than its name implies* failure. → FR-004.

- **The load-bearing infrastructure knowledge was all counter-intuitive** — precisely the
  knowledge that dies when it is not written down. Docker inserts iptables rules ahead of the host
  firewall, so binding to `127.0.0.1` is the real perimeter and `ufw` is not; the reverse proxy
  must be up *before* provisioning, not after; a bootstrap step must call `localhost` even when a
  public URL is configured, because DNS does not resolve yet; the backup script must fail closed
  rather than silently degrade to an unencrypted artifact. → FR-002, FR-003.

- **Three real bugs in that hardening work were found by exercising a live stack, not by reading
  code** — including one that left a world-readable plaintext database dump in `/tmp` on exit. A
  code-reading review gate would have passed all three. This is the reason the profile needs a
  **gate that asks what was rehearsed**, not only reviews that read files. → FR-005.

This is one project's shape. It motivates the profile; it does not define its requirements.
Every requirement below is stated stack-agnostically.

## Goal

- Ship a **`delivery-operations`** profile whose skills review the artifacts that carry software
  onto a machine, and one gate that asks whether it can be operated once there.
- Make `review-all` route to those skills **when deployment artifacts are present in the diff or
  the repository, and stay silent when they are not**.
- Resolve the `kubernetes-deployment-reviewer` dangling reference honestly: repoint what ships,
  and declare what does not as `plannedSkills` rather than as prose promises.
- Keep the framework's existing anti-overbuild stance intact. No skill in this profile may treat
  orchestration as a maturity milestone, and one skill exists specifically to push the other way.
- Ship **four** review skills that each carry judgment a neighbouring skill does not, plus a fifth
  mindset skill **if and only if** an eval demonstrates it works (FR-011) — and **defer two**
  candidates with the reason recorded rather than shipping thin coverage of them. The end state is
  four skills or five; both are successful outcomes, and which one lands is decided by evidence.

## Non-goals

- **Not a deployment tool.** Nothing in this profile executes a deploy, applies a manifest, calls
  a cloud API, or touches a running system. Every skill is `analysis_only: true`, consistent with
  every other reviewer in the repository.
- **No IaC reviewer in this feature.** `iac-review` (Terraform/Pulumi/Ansible) goes to
  `plannedSkills` — D004.
- **No Kubernetes reviewer in this feature.** `kubernetes-review` goes to `plannedSkills` — D005.
- **No new agent.** The profile reuses the existing lifecycle agents — `domain-reviewer` and
  `security-reviewer` for the four review skills, `solution-architect` for `rightsizing-advisor`
  — D007. Agent count stays 8.
- **No new hook.** `deploy-artifact-reminder` is declared in `plannedHooks` only. Hook families
  stay at 12.
- **No live-stack exercising, no runtime probing, no smoke-test harness.** The field evidence
  shows a code-reading gate misses bugs that only a live stack reveals. This feature's answer is
  to make `release-readiness` *ask what was rehearsed* and record the answer, not to build a
  rehearsal harness. Building one is a separate, much larger spec.
- **No change to the existing 61 skills' behaviour**, with two bounded exceptions: `review-all`
  gains routing rows and detection rules, and `spring-security-reviewer`'s dangling handoff line
  is repointed (FR-008). No other `SKILL.md` body is edited.
- **No rewrite of `docs/_templates/DEPLOYMENT.md`.** Its dangling `/kubernetes-deployment-reviewer`
  reference is corrected (FR-008); its Java/Kubernetes-flavoured content is left alone.
- **No secret scanning implementation.** These skills review *where secrets are placed* in
  deployment artifacts; they do not grep for credential patterns and are not a scanner.

## Users / Actors

- **The solo developer or small team** deploying what they just built — the profile's primary
  user, and the one for whom the deployment knowledge currently has nowhere to live.
- **`review-all`** — routes into these skills on artifact detection, and must not fire otherwise.
- **The second person** who has to run a deploy they did not write. `release-readiness` is written
  from their position; a runbook only they can follow is the deliverable.
- **The installer** (`install.sh` / `install.ps1`) — must install this profile by name.
- **CI** (`scripts/check-consistency.sh`) — must see `profiles.json`, disk, settings templates and
  README counts agree after the change.

## Current behavior

- 61 skills, 8 agents, 12 hook families, 22 templates, 7 profiles. `bash
  scripts/check-consistency.sh` passes on the current tree (verified at drafting).
- `skills/review-all/SKILL.md` detects six review types (Database, Security, Performance, API,
  Backend, Frontend) and routes to thirteen stack reviewers. No detection rule and no routing row
  mentions a container, a pipeline, a manifest or a deploy procedure.
- `docs/_templates/DEPLOYMENT.md` is shipped by the `java-spring-backend` profile and names a
  skill that does not exist.
- `skills/spring-security-reviewer/SKILL.md:119` explicitly disclaims infrastructure security and
  hands off to that same non-existent skill.
- No profile lists a container, pipeline, IaC or manifest artifact anywhere.
- `adapters/codex/PARITY.md` states stack-specific reviewers are "not ported in v1" and cites
  "61 skills" in two rows.

## Desired behavior

- `install.sh --profile delivery-operations` (and the `-Profile` PowerShell equivalent) installs
  the profile's skills and templates alongside `core`, exactly like every other optional profile.
- When a diff or repository contains deployment artifacts, `review-all` runs the applicable new
  skills and names them in its "Reviews run" section. When it contains none, they appear under
  "Skipped reviews" with the reason, and no deployment findings are produced.
- Each new skill has an unambiguous negative trigger against every neighbour it could be confused
  with — new and existing — resolving the collisions named in D008.
- `docs/_templates/RUNBOOK.md` gives the ordered deploy procedure a single home, which is the
  direct answer to the "three places and nowhere in full" finding.
- No shipped artifact references `kubernetes-deployment-reviewer` as an existing skill.
- All four merge-gate scripts pass, and README counters, badges and skill tables agree with disk.

## Functional requirements

- **FR-001 — The profile.** `profiles.json` gains a `delivery-operations` profile:
  `default: false`, five entries in `skills`, two in `plannedSkills` (`iac-review`,
  `kubernetes-review`), one in `plannedHooks` (`deploy-artifact-reminder`), `templates:
  ["RUNBOOK.md", "DEPLOYMENT.md"]`, an `agentRouting` block mapping the four review skills to
  `domain-reviewer` and `security-reviewer` per D007, and a `note` recording that it is an
  overlay combinable with any stack profile. Requesting it via `--profile` / `-Profile` installs
  it without error against a scratch `--central-dir`.

- **FR-002 — `deployment-review`.** Reviews the **procedure** that puts software on a machine:
  deploy scripts, `Makefile` deploy targets, runbooks, `infra/` documentation, provisioning and
  bootstrap steps, systemd units, backup and restore scripts. It carries judgment on: step
  **ordering** and stated prerequisites; **idempotency** and what a re-run does after a partial
  failure; **converge versus first-boot** divergence; **rollback path** and whether it is a path
  or a wish; **secret placement** (which file, which permissions, which process environment, and
  whether it reaches `ps` or a log); **health checks** and what the procedure does when one fails;
  and **procedure fragmentation** — an ordered procedure that exists in more than one document and
  in full in none is a finding in its own right, at High severity.

- **FR-003 — `container-review`.** Reviews **Dockerfiles and Compose files**: image pinning versus
  floating tags; **port binding exposure**, including the host-firewall interaction — publishing a
  port is a perimeter decision made in the Compose file, not in the firewall; running as root;
  healthcheck semantics and whether a passing healthcheck means the service is actually serving;
  data persistence and volume lifecycle, specifically what a `down -v` destroys; secrets reaching
  build args, image layers or `ps` output; multi-stage hygiene and what the final stage inherits.

- **FR-004 — `pipeline-review`.** Reviews **CI/CD configuration** (`.github/workflows/`,
  `.gitlab-ci.yml`, `Jenkinsfile`, and equivalents). Its first and mandatory question is **what
  the pipeline actually verifies versus what its name and its job names imply** — the canonical
  case being a pipeline that runs `lint`, `typecheck` and `test` and never runs the build, on a
  project whose deployable artifact is a build. It also covers: whether declared checks are
  actually **gating** or merely reporting; migration/schema **drift detection** before a migration
  step runs against a real database; secret exposure in logs and in `pull_request_target`-shaped
  triggers; artifact provenance between the job that builds and the job that deploys; and cache
  correctness — a cache key that can serve a stale artifact to a deploy.

- **FR-005 — `release-readiness`.** A **gate, not a review**. Run once before a release, not per
  diff. It does not read a diff and does not produce file:line findings; it produces a
  **Go / No-go verdict with an explicit unmet-precondition list**. It asks: is there a rollback
  that has been **executed**, not merely written; has a restore been **rehearsed** from the actual
  backup artifact, not merely configured; would the current observability surface a **silent**
  failure — one where nothing crashes and nothing is served correctly; is there a stated
  **perimeter** and does the person answering know what enforces it; and is there **one** runbook a
  second person could follow without asking the author. Every answer is recorded as
  *rehearsed* / *written but untested* / *absent*, and "written but untested" is never counted as
  satisfied. This requirement is the direct consequence of three real bugs that a code-reading
  gate passed and a live stack caught.

- **FR-006 — `rightsizing-advisor` (`category: mindset`).** The counterweight. Triggers *before*
  infrastructure is proposed or adopted, and asks what **observed symptom** justifies the proposed
  weight — what is failing now, at what measured load, that the current shape cannot carry. It
  treats "we will need it later", "it is best practice" and "it is what serious teams run" as
  non-answers, and asks instead for the **written scaling trigger**: the specific measurement at
  which the heavier shape becomes justified, recorded so the decision can be revisited rather than
  re-argued. It is explicitly **not** an argument that simple is always right — an under-provisioned
  system that loses data is the same failure of judgment in the other direction, and the skill must
  say so.
  **This requirement is conditional on evidence (FR-011).** If the eval does not support shipping
  it, it moves to `plannedSkills` and FR-011's fallback applies.

- **FR-007 — `RUNBOOK.md` template.** `docs/_templates/RUNBOOK.md` ships: a single ordered
  procedure with prerequisites, numbered steps each stating its precondition and its verification,
  a rollback section, a "what a re-run does" section, and a "last rehearsed" line with a date. Its
  purpose is to be the one place the procedure lives. Template count 22 → 23.

- **FR-008 — Routing repair and `review-all` wiring.**
  (a) `skills/review-all/SKILL.md` gains a **Deployment** detection type and four routing rows.
  Detection is by artifact presence: `Dockerfile*`, `docker-compose*.y*ml` / `compose*.y*ml`,
  `.github/workflows/**`, `.gitlab-ci.yml`, `Jenkinsfile`, `deploy*.{sh,ps1}`, `infra/**`,
  `k8s/**`, `*.tf`, `ansible/**`, `Procfile`, `fly.toml`, `*.service`, or a runbook/deployment
  document. `release-readiness` is **not** routed from `review-all` — it is a release gate, not a
  diff review (D008).
  (b) `skills/spring-security-reviewer/SKILL.md:119` and `docs/_templates/DEPLOYMENT.md:5` no
  longer reference `kubernetes-deployment-reviewer` as an existing skill; they point at
  `container-review` / `deployment-review` for what ships, and name `kubernetes-review` as planned.

- **FR-009 — Counts and consistency.** Skills 61 → **66**, profiles 7 → **8**, docs templates
  10 → **11**, templates total 22 → **23**. Agents stay 8; hook families stay 12. README badges,
  `<!-- count:key -->` markers, the skill tables, the profile table and the directory-tree comment
  are updated; `bash scripts/check-consistency.sh` exits 0.

- **FR-010 — Skill form.** Every new `SKILL.md` satisfies the spec-022 `[SKILL-FORM]` rules:
  description ≤ 400 characters with no arrow chain, no enumerated step sequence and no three-clause
  `then` chain; body ≤ 600 lines; a `## SDD Contract` block declaring all eleven fields; and a
  negative-trigger clause in the description for every collision D008 identifies.

- **FR-011 — Mindset evidence (blocking for FR-006).** `rightsizing-advisor` ships **only** with an
  `evals/results/rightsizing-advisor-<date>.md` produced **after** the skill is written, via
  `bash scripts/skill-eval.sh rightsizing-advisor --reps 5`, against a **self-contained** scenario
  written for this skill (the existing corpus is marked superseded by spec 022 D010 and must not be
  reused). If the verdict is `NO-BASELINE-FAILURE`, `HARMFUL` or `INCONCLUSIVE`, or if the run
  cannot be performed, the skill is **not shipped**: it moves to `plannedSkills`, the skill count
  becomes 65, and the reason is recorded in `DECISIONS.md`. No result is fabricated and no
  unproven mindset skill is shipped.

- **FR-012 — Unguarded count claims outside README.** `scripts/check-consistency.sh` validates
  count claims **only** inside `README.md` (markers and five shields.io badges). Six other shipped
  files assert "61 skills" in prose that no gate protects, and all six become false on merge:
  `docs/AGENTIC_ROUTING.md:38`, `adapters/README.md:31,36`, `adapters/claude/README.md:22`,
  `adapters/codex/prompts/README.md:7`, `adapters/codex/PARITY.md:21,35`, and the directory-tree
  comment at `README.md:451`. Every one is corrected to the post-merge count. `CHANGELOG.md`'s
  historical mentions describe past state and are left alone. *(Discovered during
  `/spec-clarify`; see OQ-5 for whether the checker should learn to guard these.)*

- **FR-013 — Codex adapter parity.** `adapters/codex/PARITY.md` is updated: the counts it cites
  are corrected (FR-012), and the "Stack-specific reviewers … not ported in v1" gap row explicitly
  names `delivery-operations`. No new prompt is added under `adapters/codex/prompts/` — D009.

- **FR-014 — CHANGELOG.** `CHANGELOG.md` gains an entry for this feature, matching the convention
  every spec from 017 onward followed (verified by `git log --name-only -- CHANGELOG.md`). It
  states the profile, the skills shipped, the two deferred to `plannedSkills` with their reason,
  and the `rightsizing-advisor` evidence outcome — including a `NO-BASELINE-FAILURE` outcome if
  that is what the eval returned.

- **FR-015 — Untouched.** `hooks/`, `agents/`, `settings.template.json`,
  `settings.template.sh.json`, and `install.sh` / `install.ps1` are not modified. Confirmed
  achievable during `/spec-clarify`: no profile name appears in either installer or either
  settings template, so profiles are pure data in `profiles.json`. `profiles.json`'s `version`
  field is not bumped — the schema does not change, only its data (see Assumptions).

## Non-functional requirements

- **Performance:** no runtime component. Consistency-check cost is unchanged (one more profile,
  five more skill directories to stat).
- **Security:** these skills read repository files and report. They never execute a deploy
  artifact, never resolve a secret reference, and never transmit repository content anywhere. A
  finding must never quote a discovered secret value — it cites the location and the class.
- **Observability:** every skill emits file:line-cited findings, except `release-readiness`, whose
  output is a Go / No-go verdict plus an unmet-precondition list with each precondition marked
  *rehearsed* / *written but untested* / *absent*.
- **Maintainability:** five skills, no new agent, no new hook, no installer change. The profile's
  entire wiring is one `profiles.json` block plus routing rows in `review-all`.
- **Honesty:** the profile must not imply coverage it lacks. `iac-review` and `kubernetes-review`
  are visible in `plannedSkills` — the mechanism `profiles.json` documents for exactly this — and
  `deployment-review` must state in its own body that IaC state semantics and Kubernetes manifests
  are outside its reach, rather than half-covering them.
- **Neutrality on infrastructure weight:** no skill in this profile may describe orchestration,
  managed services or multi-host topology as a maturity milestone, a next step, or a sign of
  seriousness. This is a review constraint on every `SKILL.md` in the profile, not only on
  `rightsizing-advisor`.

## API / Interface changes

- New slash commands: `/deployment-review`, `/container-review`, `/pipeline-review`,
  `/release-readiness`, and `/rightsizing-advisor` (conditional on FR-011).
- New profile name accepted by `install.sh --profile` / `install.ps1 -Profile`:
  `delivery-operations`.
- `review-all` output vocabulary gains a **Deployment** review type.
- New template path: `docs/_templates/RUNBOOK.md`.

## Data model changes

None. Markdown and JSON only.

## Edge cases

- **A repository with no deployment artifacts.** `review-all` must list Deployment under "Skipped
  reviews" with the reason and produce zero deployment findings. A false fire here is a defect,
  not a harmless extra — it is how a reviewer loses credibility. (AC-004b)
- **A repository whose only artifact is `.github/workflows/` running tests, with no deploy job.**
  `pipeline-review` applies; `deployment-review` does not. The presence of CI is not the presence
  of a deployment.
- **The pipeline *is* the deploy procedure** (deploy steps inlined in a workflow). Both apply, on
  different questions: `pipeline-review` on gating, provenance and secret exposure;
  `deployment-review` on the ordering and idempotency of the inlined steps. Each skill's negative
  trigger must make this split explicit rather than leaving it to the caller.
- **Kubernetes manifests present.** `kubernetes-review` is planned, not shipped.
  `container-review` covers the image; `deployment-review` covers the rollout **procedure**;
  neither claims to review manifest semantics (probes, RBAC, `securityContext`, PDBs). Saying so
  plainly is required — silently producing shallow manifest findings would be worse than the gap.
- **A monorepo with several deployables.** Findings must name which deployable they concern.
  Detection fires per artifact path, not per repository.
- **`release-readiness` run on a project that has never deployed.** Every precondition is *absent*
  rather than failed. The verdict is No-go with a first-deployment checklist, not an error.
- **`release-readiness` given only self-reported answers.** It cannot verify a rehearsal happened.
  It must record the claim as a claim, attributed, with the date — and treat an undated "yes" as
  *written but untested*.
- **The eval for `rightsizing-advisor` comes back `NO-BASELINE-FAILURE`.** The honest reading is
  that models do not have the overbuild reflex the skill assumes. FR-011's fallback applies and
  the profile ships four skills.
- **`profile_scope` for a mindset skill.** All nine existing mindset skills are `core`. This one
  is profile-scoped, which is a first (D006).

## Acceptance criteria

- **AC-001:** `specs/features/024-delivery-operations-profile/` contains `SPEC.md`, `PLAN.md`,
  `TASKS.md` and `DECISIONS.md`, and `DECISIONS.md` records a decision for every one of the seven
  candidate skills — including the two dropped, with reasons. (FR-001, D003–D005)
- **AC-002:** `delivery-operations` is registered in `profiles.json` and installing it against a
  **scratch** central directory succeeds, with the run's output captured:
  `bash install.sh --profile delivery-operations --central-dir <scratch>`. The scratch tree
  contains one directory per shipped skill and `RUNBOOK.md`; the planned entries are reported as
  "planned, not installed" without error. Verified by execution, not by reading the installer.
  (FR-001)
- **AC-003:** Each shipped `SKILL.md` has YAML frontmatter with `name` and a `description`
  carrying at least one negative trigger, followed by a `## SDD Contract` block declaring all
  eleven fields, and `bash scripts/check-consistency.sh` reports no `[SKILL-FORM]` finding.
  (FR-010)
- **AC-004a (static, mechanical):** `skills/review-all/SKILL.md` contains a Deployment detection
  rule naming each artifact pattern of FR-008a and exactly four routing rows, each with a "Route
  when" condition stated as an artifact-presence test rather than a topic. `grep` confirms
  `release-readiness` is **not** among them. (FR-008a)
- **AC-004b (behavioural, manual, single observation):** `/review-all` is run against two scratch
  fixtures — one containing a `Dockerfile` plus a workflow file, one containing neither — and the
  transcripts are recorded in `TASKS.md`. Expected: the new skills appear under "Reviews run" in
  the first and under "Skipped reviews" in the second, with no deployment finding emitted.
  *This is a routing behaviour of a prompt, so it is one dated observation against one model, not
  a proof and not a CI gate — the same honesty constraint spec 022 places on eval results. A
  negative result blocks the feature; a positive result is evidence, not a guarantee.* (FR-008a)
- **AC-005:** `grep -rn "kubernetes-deployment-reviewer"` over shipped artifacts (`skills/`,
  `docs/_templates/`) returns nothing that presents it as an existing skill. Roadmap documents may
  retain historical mentions. (FR-008b)
- **AC-006:** `bash scripts/check-consistency.sh` exits 0; README badges and every
  `<!-- count:key -->` marker read 66 skills (or 65 under FR-011's fallback), 8 profiles, 23
  templates, 12 hook families, 8 agents. (FR-009)
- **AC-007:** All four merge-gate scripts pass with output shown:
  `check-consistency.sh`, `check-consistency.test.sh`, `graphify.test.sh`, `skill-eval.test.sh`.
- **AC-008:** `rightsizing-advisor` ships **only** with a committed
  `evals/results/rightsizing-advisor-<date>.md` naming the model, both arms, 5 reps and a verdict,
  produced after the skill was written from a scenario meeting the self-contained rule — or it is
  absent from `skills/`, present in `plannedSkills`, and the reason is in `DECISIONS.md`. Exactly
  one of these two states holds. (FR-006, FR-011)
- **AC-009:** `adapters/codex/PARITY.md` cites the new skill count and names
  `delivery-operations` in its not-ported row. (FR-013)
- **AC-010:** `git status --porcelain` shows no modification to `hooks/`, `agents/`,
  `settings.template*.json`, `install.sh` or `install.ps1`. (FR-015)
- **AC-011:** No shipped `SKILL.md` in this profile contains language presenting orchestration,
  managed services or multi-host topology as a maturity step. Verified by reading all five bodies
  against the NFR, and recorded as done. (NFR: neutrality)
- **AC-012:** `grep -rn "61 skills" --include="*.md" .` returns matches **only** in `CHANGELOG.md`
  (historical) and under `specs/` (historical). No file under `docs/`, `adapters/` or the README
  directory tree still asserts the pre-merge count. (FR-012)
- **AC-013:** `CHANGELOG.md` contains an entry for this feature naming the profile, the shipped
  skills, the two deferred with their reason, and the `rightsizing-advisor` evidence outcome.
  (FR-014)

## Test scenarios

- **Unit:** `scripts/check-consistency.sh` and `check-consistency.test.sh` on the mutated tree —
  the existing suites already cover profile/disk/README alignment and skill form; no new test
  script is required by this feature.
- **Integration:** a real `install.sh --profile delivery-operations --central-dir <scratch>` run
  (AC-002); the same for `install.ps1` if `pwsh` is available, and recorded as unverified if not.
- **E2E:** the two `review-all` fixtures of AC-004b — deployment artifacts present, and absent.
- **Behavioural:** `bash scripts/skill-eval.sh rightsizing-advisor --reps 5` against a new
  self-contained scenario (AC-008).
- **Manual:** read all five bodies for the neutrality NFR (AC-011); read every flagged eval match
  before setting `manually-read: YES`.

## Assumptions

- **Verified during `/spec-clarify`, no longer an assumption:** no profile name appears in
  `install.sh`, `install.ps1`, `install-all.{sh,ps1}`, `settings.template.json` or
  `settings.template.sh.json`, so a new profile is pure `profiles.json` data. Still confirmed by
  an actual install run (AC-002) rather than by reading alone.
- **Verified during `/spec-clarify`:** `check-consistency.sh` auto-derives
  `<profile>-skills|hooks|templates|agents` count keys for every profile in `profiles.json`
  (line ~503), and `REQUIRED_MARKERS` is a fixed set that a new profile does not extend. So a
  `count:delivery-operations-*` marker in the README profile table is valid and optional, and its
  absence is not a checker failure.
- `profiles.json`'s `version` field is not bumped. Historical bumps (0.1.0 → 0.2.0 → 0.4.0)
  accompanied schema changes; this feature adds data under the existing schema, and the checker
  does not read the field. Stated so PLAN does not re-litigate it.
- Copying a skill directory is sufficient to ship it (spec 022 D004 confirmed `install.sh:438`
  calls `copy_tree_safely` on the whole skill directory).
- The Claude Code CLI is present at `/Users/manu/.local/bin/claude`, so `SKILL_EVAL_RUNNER` can be
  configured and FR-011's eval can actually be run. Its result is not predictable in advance.
- The 400-character description cap accommodates the negative-trigger clauses D008 requires. If a
  collision cannot be disambiguated within the cap, the cap is challenged in PLAN rather than a
  clause dropped — the precedent spec 022 set for exactly this case.
- Deployment artifacts are identifiable by path and filename with acceptable precision. This is a
  heuristic; AC-004b's negative fixture is what keeps it honest.

## Open questions

*Resolved at close, 2026-08-05.*

- **OQ-1 — Resolved (D002).** `delivery-operations` was accepted over `delivery-platform`:
  "platform" presupposes a platform team and an internal developer platform, which is the exact
  posture the profile is required not to imply. Shipped, registered and installed under that name
  on both installers.
- **OQ-2 — Moot, not resolved (D013).** Whether `rightsizing-advisor` should be `core` rather than
  profile-scoped never bit, because the skill did not ship. The question returns **intact** if the
  skill is ever revived and must be re-asked then — it has not been settled by this feature.
- **OQ-3 — Deferred.** `release-readiness` reports its verdict to the session and writes no file,
  as proposed. Revisit only if users ask for a committed artifact; doing so would make it the only
  reviewer in the repository with `side_effects` other than `none`.
- **OQ-4 — Deferred.** `deploy-artifact-reminder` remains in `plannedHooks`. Hooks are the
  highest-risk artifact class in this repo and this feature was already wide.
- **OQ-5 — Deferred, and better evidenced than when it was raised.** `check-consistency.sh` guards
  count claims only inside `README.md`. FR-012 fixed **six** unguarded prose claims by hand across
  `docs/` and `adapters/`; nothing prevents a seventh. Extending the checker to a configured file
  list is a small, well-shaped follow-up spec — deliberately not done here, since this feature
  would then be changing the gate that judges it.

### Raised and resolved during implementation

- **Spec numbering.** 023 was free on disk but reserved in `CONTRIBUTING.md`,
  `evals/scenarios/README.md` and thirty-two references across spec 022. Taken as **024** (D001).
- **`agentRouting` coverage rule.** Not anticipated by this SPEC: every non-core profile skill must
  appear in `agentRouting` or `agentRoutingExempt` (spec 018 D014). Resolved by D011, then removed
  with the skill under D013.
- **Contract categories are a closed enum** (D012): the three artifact reviewers are
  `domain-reviewer`; `release-readiness` is `quality-review`, because it produces a verdict rather
  than domain findings.

## Contracted services

`specs/SERVICES.md` is absent → all billable add-ons treated as NOT contracted (conservative
default). This feature touches none; `delivery-operations` is not a billable add-on and is not
gated on `SERVICES.md`, unlike `seo-geo-addon`.
