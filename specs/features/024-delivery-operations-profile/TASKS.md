# Tasks: Delivery-operations profile

> Sequencing is load-bearing, not stylistic. Skills must exist on disk before `profiles.json`
> names them (installer hard-errors otherwise); `profile_scope` is only valid after the profile
> exists; and the eval outcome decides the final skill count, so count sync runs last.
> See PLAN.md "Proposed approach".

## Phase 1: Preparation

- [x] **T001** — Capture the pre-change baseline: run all four gate scripts and record their output
  in this file. Record `ls skills/ | wc -l` (expect 61) and the current README badge values.
  Establishes that any later failure is caused by this feature. Covers: AC-007.

  **Done 2026-08-05.** Disk: 61 skills, 8 agents, 7 profiles. Badges: `skills-61`,
  `hook%20families-12`, `templates-22`, `agents-8`, `profiles-7` — all agree with disk.
  All four gates green **before** any change:

  | Gate | Result | Last line |
  |---|---|---|
  | `check-consistency.sh` | PASS | "profiles.json, disk artifacts, settings wiring, and README counts are aligned." |
  | `check-consistency.test.sh` | PASS | 30 passed, 0 failed |
  | `graphify.test.sh` | PASS | Passed: 66  Failed: 0 |
  | `skill-eval.test.sh` | PASS | 20 passed, 0 failed |

- [x] **T002** — Create the two `review-all` scratch fixtures under the session scratchpad (never
  in the repo): fixture A with a `Dockerfile` and `.github/workflows/ci.yml`, fixture B with
  neither (a plain source tree). Used by T014. Covers: AC-004b.

  **Done 2026-08-05.** Both under the session scratchpad, outside the repository — `git status`
  stays clean. Fixture A carries planted defects so T014 tests *detection*, not just routing:
  - `Dockerfile` — `node:latest` floating tag, no non-root `USER`, `ARG NPM_TOKEN` build-arg
    secret, no `HEALTHCHECK`.
  - `docker-compose.yml` — `ports: "3000:3000"` published on all interfaces (the perimeter
    decision of FR-003), plaintext password in `environment:`, unpinned `postgres` image.
  - `.github/workflows/ci.yml` — runs `lint`, `typecheck`, `test` and **never runs the build**.
    This is the canonical field-evidence failure of FR-004, reproduced deliberately.

  Fixture B is a plain TypeScript library (`package.json`, `src/index.ts`, one test file) with no
  container, pipeline, manifest or deploy artifact of any kind.

## Phase 2: Implementation

### 2a — Repairs that stand alone (clean revert boundary — PLAN rollback §2)

- [x] **T003** — Repair the `kubernetes-deployment-reviewer` dangling reference in the two shipped
  artifacts: `skills/spring-security-reviewer/SKILL.md:119` and `docs/_templates/DEPLOYMENT.md:5`.
  Point at `container-review` / `deployment-review` for what ships and name `kubernetes-review` as
  planned. Leave `docs/ROADMAP_JAVA_SPRING_CONTEXT.md` alone (historical roadmap).
  Covers: AC-005. (FR-008b)

  **Done 2026-08-05.** Both references repointed:
  - `spring-security-reviewer` now disclaims container/deployment security to `container-review`
    and `deployment-review`, and states plainly that **Kubernetes manifest semantics are covered
    by no shipped skill**, naming `kubernetes-review` as `plannedSkills`. The original line
    claimed a skill existed; the replacement names the gap. That is the point of D005.
  - `DEPLOYMENT.md` now points at `/deployment-review` and `/container-review`, and gained two
    lines distinguishing itself from `RUNBOOK.md` (topology vs ordered procedure) — the D010
    boundary, stated where a user filling the template will actually read it.

  `grep -rn "kubernetes-deployment-reviewer" skills/ docs/ adapters/ README.md` → **no matches**.
  `check-consistency.sh` still passes. Note the forward reference to `RUNBOOK.md`, which T010
  creates; if T010 is dropped, this DEPLOYMENT.md line must be dropped with it.

  **Observation for `/spec-review` (not fixed here — out of T003's stated scope):**
  `docs/ROADMAP_JAVA_SPRING_CONTEXT.md:152,256` still uses the old name
  `kubernetes-deployment-reviewer` for what this profile now calls `kubernetes-review`. AC-005
  permits historical roadmap mentions, so this is compliant, but the two names refer to the same
  unshipped skill and a reader could take them for different roadmap items.

### 2b — The skills

- [x] **T004** — Write `skills/deployment-review/SKILL.md`. Judgment: step ordering and stated
  prerequisites, idempotency and re-run-after-partial-failure, converge-vs-first-boot, rollback
  path, secret placement (file, permissions, process env, `ps` exposure), health-check failure
  behaviour, and **procedure fragmentation as a High-severity finding in its own right**. Must
  state plainly that IaC state semantics and Kubernetes manifest semantics are out of reach
  (D004, D005). Contract: `category: domain-reviewer`, `primary_agent: domain-reviewer`,
  `secondary_agents: [security-reviewer]`, `profile_scope: [delivery-operations]`.
  Negative triggers vs `pipeline-review`, `release-readiness`, `security-review`.
  Covers: AC-003, AC-011. (FR-002, FR-010)

  **Done 2026-08-05.** `skills/deployment-review/SKILL.md`, 195 lines. Form: description
  **379/400** chars with all three negative triggers, no arrow chain, no enumerated steps, no
  `then`-chain; body 195/600 lines.

  **R-3 did not bind.** Three negative triggers fit in 379 characters, so the 400-char cap was not
  challenged. Recorded because R-3 predicted this skill would be the one to break it — `container-review`
  and `release-readiness` have fewer collisions each, so the cap is now unlikely to bind anywhere.

  Sections carry the FR-002 judgment: ordering and stated prerequisites (with the
  reverse-proxy-before-provisioning and bootstrap-calls-`localhost` shapes as the illustrative
  cases), idempotency and re-run after partial failure, converge vs first boot, rollback including
  **the point of no return**, secret placement (`ps`, world-readable windows, fail-closed vs
  silent degradation), health checks and discarded exit codes, and **procedure fragmentation at
  High severity** with the "could a second person follow it?" test.

  Honesty per D004/D005: the "does NOT do" section states plainly that IaC state semantics and
  Kubernetes manifest semantics are covered by **no shipped skill**, naming both as `plannedSkills`,
  rather than producing a shallow reading of a `.tf` file or a manifest.

  Neutrality (AC-011 pre-check): grep for maturity-ladder language finds nothing, and the skill
  carries an explicit "Infrastructure weight is not this skill's business" section that redirects
  that judgment to `/rightsizing-advisor` in both directions.

  Checker reports exactly the two expected pre-T009 errors and nothing else:
  `[orphan-skill]` and `[sdd-contract] profile_scope references unknown profiles` — both resolve
  when T009 registers the profile.

- [x] **T005** — Write `skills/container-review/SKILL.md`. Judgment: image pinning vs floating
  tags, port binding as a **perimeter decision made in the Compose file** (Docker's iptables rules
  sit ahead of the host firewall — binding to `127.0.0.1` is the real perimeter, not `ufw`),
  running as root, healthcheck semantics vs actually serving, volume lifecycle and what `down -v`
  destroys, secrets in build args/layers/`ps`, multi-stage inheritance. Contract as T004.
  Negative triggers vs `security-review`, `deployment-review`.
  Covers: AC-003, AC-011. (FR-003, FR-010)

  **Done 2026-08-05.** `skills/container-review/SKILL.md`, 177 lines. Form: description
  **337/400** chars, both required negative triggers, no arrow chain, no enumerated steps, no
  `then`-chain; body 177/600.

  The **port binding is the perimeter** section is the load-bearing one and is written as the
  finding most often missed: `ports: "5432:5432"` publishes on all interfaces, Docker inserts its
  iptables rules **ahead of the host firewall** so a `ufw`/`firewalld` rule is not evidence a
  published port is closed, and the binding address is what actually decides. It also points out
  that inter-container reachability needs no publishing at all, which is the fix in most cases.

  Other FR-003 sections: image pinning (including major-tag float and Dockerfile/Compose
  disagreement), non-root `USER` plus the write-permission trap that gets "fixed" by reverting to
  root, healthcheck semantics (serving vs alive, `start_period` vs real startup, whether anything
  actually `depends_on … service_healthy`), volume lifecycle with **what `down -v` destroys**
  named explicitly, secrets (build args surviving in image history, `COPY . .` pulling `.env`,
  `.dockerignore` contents), and multi-stage inheritance.

  Scope honesty: the skill states it does **not** scan for CVEs — that is a scanner's job, not a
  reviewer's — and does not review Kubernetes manifests, naming `kubernetes-review` as
  `plannedSkills` (D005).

  Neutrality (AC-011 pre-check): grep clean, plus an explicit section stating a Compose stack on a
  single host is a legitimate production architecture and that this skill has no opinion about
  changing it.

  Checker: 7 errors, all expected and all resolved by T009/T015 — 2 × `[orphan-skill]`,
  2 × `[sdd-contract] profile_scope`, and 3 README count/badge entries now that disk reads 63
  skills. No unexpected error.

- [x] **T006** — Write `skills/pipeline-review/SKILL.md`. **First and mandatory question: what the
  pipeline verifies versus what its job names imply** — canonical case `lint` + `typecheck` +
  `test` with no build, on a project whose deployable is a build. Also: gating vs reporting,
  migration/schema drift detection before a migration step, secret exposure in logs and
  `pull_request_target`-shaped triggers, artifact provenance between build and deploy jobs, cache
  keys that can serve a stale artifact to a deploy. Contract as T004. Negative triggers vs
  `qa-review`, `deployment-review`.
  Covers: AC-003, AC-011. (FR-004, FR-010)

  **Done 2026-08-05.** 168 lines, description **349/400**, both negative triggers, form clean.
  The mandatory-first section is written as an instruction to enumerate what the pipeline runs and
  diff it against what the job names imply, with the field-evidence case stated concretely:
  typecheck is not compilation, a TypeScript project can typecheck cleanly and fail `next build`,
  and the pipeline is green with **no automated evidence the application compiles**. Also covers
  migration/schema drift before a real migration, gating vs reporting (`continue-on-error`,
  non-required checks, deploy racing its `needs:`), secret exposure (`pull_request_target` running
  with repo secrets against untrusted code, unpinned third-party actions), artifact provenance
  (rebuild in the deploy job is a different artifact), and cache keys that can serve a stale build.
  It explicitly defers test *quality* to `qa-review` and flags branch protection as unverifiable
  from the repository rather than assuming it.

- [x] **T007** — Write `skills/release-readiness/SKILL.md`. A **gate, not a review**: no diff, no
  file:line findings. Output is Go / No-go plus preconditions each marked *rehearsed* / *written
  but untested* / *absent*, where "written but untested" never counts as satisfied. Questions:
  rollback **executed**, restore **rehearsed** from the actual backup artifact, would anything
  surface a **silent** failure, what enforces the perimeter, one runbook a second person could
  follow. Must record self-reported answers as attributed dated claims and treat an undated "yes"
  as *written but untested*. Contract: `category: quality-review`,
  `primary_agent: domain-reviewer`, `secondary_agents: [security-reviewer]`,
  `profile_scope: [delivery-operations]`. Negative triggers vs `deployment-review`,
  `observability-reviewer`, `qa-review`.
  Covers: AC-003, AC-011. (FR-005, FR-010)

  **Done 2026-08-05.** 167 lines, description **372/400**, form clean. `category: quality-review`
  per D012 — it produces a verdict, not domain findings. The three-state rule is the spine:
  *rehearsed* / *written but untested* / *absent*, with "written but untested never counts as
  satisfied" stated as the point of the gate rather than a footnote, and **an undated \"yes\"
  recorded as written but untested**. Since the skill cannot verify a rehearsal, it records
  operator answers as attributed dated claims. Covers the five preconditions of FR-005, including
  the backup that fails closed vs silently degrading and the temp-directory artifact readable for
  its whole lifetime (field evidence #4). A No-go is framed as a useful outcome, and unmet
  preconditions can be recorded as explicitly accepted risks with an owner.

- [x] **T008** — Write `skills/rightsizing-advisor/SKILL.md`. Asks what **observed symptom**
  justifies the proposed weight, treats "we'll need it later" / "best practice" / "what serious
  teams run" as non-answers, and asks for the **written scaling trigger**. Must state that
  under-provisioning is the same failure of judgment in the other direction — a counterweight that
  only ever argues for less is a bias, not judgment. Contract: `category: mindset`,
  `primary_agent: solution-architect`, `secondary_agents: [all]`,
  `profile_scope: [delivery-operations]`, `provider_specific: true`. Negative triggers vs
  `decomposer`, `scope-keeper`, `architect-review`.
  Covers: AC-003, AC-011. (FR-006, FR-010)

  **Done 2026-08-05 — provisional, pending T013.** 112 lines, description **357/400**, form clean.
  Follows the existing mindset structure exactly (Triggers / Rules / Anti-patterns / Contrast /
  Closing checklist). Opens with "infrastructure is justified by a symptom, not by a category" and
  states in the second paragraph that **under-provisioning is the same failure of judgment**, so
  the both-directions requirement of FR-006 is structural rather than a caveat. Names the four
  non-answers explicitly ("we'll need it later", "best practice", "what serious teams run", "more
  scalable") and requires a **written scaling trigger** as a specific measurement. Its Contrast
  section names the maturity-ladder reflex as the generic-model behaviour it exists to counter.

  **This skill is not confirmed shipped.** FR-011 gates it on T013's eval; if the verdict is not
  favourable it is deleted and moved to `plannedSkills`.

### 2c — Wiring

- [x] **T009** — Add the `delivery-operations` block to `profiles.json`: `default: false`, five
  `skills`, `plannedSkills: ["iac-review", "kubernetes-review"]`,
  `plannedHooks: ["deploy-artifact-reminder"]`, `templates: ["RUNBOOK.md", "DEPLOYMENT.md"]`,
  `agentRouting` per D007, `agentRoutingExempt: ["rightsizing-advisor"]` per D011, and a `note`
  recording overlay status and the two deferrals with their reason. Do **not** bump `version`.
  Covers: AC-001, AC-002. (FR-001)

  **Done 2026-08-05.** JSON valid, 8 profiles. All ten pre-T009 checker errors cleared at once —
  the five `[orphan-skill]` and five `[sdd-contract] profile_scope` entries — confirming PLAN §2's
  sequencing was right and that `profile_scope: [delivery-operations]` resolves only once the
  profile exists. **D011 validated in practice:** `agentRoutingExempt: ["rightsizing-advisor"]`
  satisfies coverage rule 7 without a false `agentRouting` declaration; the checker accepts it.
  `version` deliberately not bumped. The `note` records both deferrals with their reason and
  states that `kubernetes-review` supersedes the never-shipped `kubernetes-deployment-reviewer`
  still listed under the old name in the roadmap doc.

- [x] **T010** — Write `docs/_templates/RUNBOOK.md`: prerequisites, numbered steps each with its
  precondition and its verification, rollback section, "what a re-run does" section, and a
  **last rehearsed** line with a date. Covers: AC-006. (FR-007, D010)

  **Done 2026-08-05.** `docs/_templates/RUNBOOK.md`. Opens by stating its own purpose — to be the
  only place the procedure lives — and names the fragmentation failure it exists to prevent.
  Carries three dated lines at the top (last followed / last rollback rehearsed / last restore
  rehearsed) with a note that an undated "yes" counts as *written but untested* in
  `/release-readiness`, so the template feeds the gate directly. Per-step blocks state precondition,
  verification, **safe to re-run**, and first-boot-only. Dedicated sections for what a re-run does,
  first-deployment vs converge, the **point of no return**, restore rehearsal, the perimeter table
  (with the Docker-iptables note), and a **known counter-intuitive details** section — the direct
  answer to field evidence #3, giving the knowledge that dies undocumented a place to live.

- [x] **T011** — Wire `review-all`: add a **Deployment** detection type and exactly four routing
  rows to `skills/review-all/SKILL.md`. Detection by artifact presence (`Dockerfile*`,
  `docker-compose*.y*ml`/`compose*.y*ml`, `.github/workflows/**`, `.gitlab-ci.yml`, `Jenkinsfile`,
  `deploy*.{sh,ps1}`, `infra/**`, `k8s/**`, `*.tf`, `ansible/**`, `Procfile`, `fly.toml`,
  `*.service`, runbook/deployment docs). `release-readiness` is deliberately **not** routed — it
  is a release gate, not a diff review. Add a "does not fire" instruction for repositories with no
  deployment artifacts. Covers: AC-004a. (FR-008a, D008)

  **Done 2026-08-05.** Three edits to `skills/review-all/SKILL.md` (210 lines, still form-clean):
  a **Deployment** detection block stating explicitly that detection is *by artifact presence, not
  by spec wording* — "a spec that merely mentions deploying, shipping or releasing is not a
  trigger" — plus the negative instruction to list it under Skipped reviews with a reason and emit
  no findings; four routing rows; and a Deployment triage checklist. `Deployment` added to the
  finding `Type:` enum.

  **AC-004a verified:** 4 routing rows present, `/release-readiness` absent from the table with a
  paragraph stating why (release gate, not a diff review). `/rightsizing-advisor`'s row fires only
  when a change **adds** an infrastructure tier, not on edits to infrastructure that already
  exists — otherwise it would fire on every Dockerfile tweak and become noise.

## Phase 3: Evidence and verification

> T012 must precede T015 — the verdict decides whether the skill count is 66 or 65.

- [x] **T012** — Write `evals/scenarios/rightsizing-advisor.md` in the six-section format
  (Failure under test / System prompt / User message / Observable criterion / Reachability /
  Detection pattern). **Must be self-contained** — paste any artifact inline and ask for a text
  answer; a scenario referencing repository state the model cannot see is what invalidated two
  prior sweeps (spec 022 D010). Covers: AC-008. (FR-011)

  **Done 2026-08-05.** `evals/scenarios/rightsizing-advisor.md`, six-section format,
  **fully self-contained**: the whole situation (one VPS, Compose stack, three months of steady
  measurements, deploy cadence, outage history) is inline in the system prompt, with "there is no
  repository to inspect" stated explicitly. The user message supplies the emotionally loaded reason
  to upgrade ("first paying customers", "properly production-ready") without any measurement
  supporting it, so the failure is reachable if the reflex exists.

  The detection pattern was **validated before spending model calls**: 7 hand-written controls
  (4 that must match, 3 that must not), all 7 correct under `grep -Eqi`, which is how
  `skill-eval.sh:176` applies it. Worth noting the first draft failed its own positive controls
  because I tested case-sensitively while the harness matches with `-i` — the pattern was fine and
  the test was wrong.

- [x] **T013** — Run the eval: `export SKILL_EVAL_RUNNER='claude -p --model <id>'` then
  `bash scripts/skill-eval.sh rightsizing-advisor --reps 5`. Read **every** flagged response
  before setting `manually-read: YES`. Commit the result file regardless of verdict.
  **If the verdict is `NO-BASELINE-FAILURE`, `HARMFUL` or `INCONCLUSIVE`** (R-1, rated likely):
  delete `skills/rightsizing-advisor/`, move it to `plannedSkills`, record the outcome as a new
  decision, and carry 65 skills through T015. Do not fabricate, do not re-roll for a better
  number. Covers: AC-008. (FR-011)

  **Done 2026-08-05. R-1 MATERIALIZED — verdict `NO-BASELINE-FAILURE`, skill NOT shipped.**

  | Arm | Failure exhibited |
  |---|---|
  | control | **0/5** (floor is 2/5) |
  | treatment | 0/5 |

  Model `claude-sonnet-5`, 10 calls, `evals/results/rightsizing-advisor-2026-08-05.md`.

  **All 10 responses read** before setting `manually-read: YES`. The verdict is real, not a
  detection miss: all five control reps open by declining Kubernetes outright, and several
  independently do what the skill prescribed — cite the supplied measurements, name the actual gaps
  (no alerting, migration discipline, off-box backups, a runbook for total VPS loss) and propose
  the smallest fix rather than a tier upgrade.

  Fallback applied exactly as pre-agreed: `skills/rightsizing-advisor/` deleted, moved to
  `plannedSkills`, `agentRoutingExempt` removed with it, skill count **65 not 66**. Recorded as
  **D013**, including what now carries the anti-overbuild stance and what is genuinely lost (the
  proactive trigger before infrastructure is proposed).

- [x] **T014** — Run `/review-all` against both T002 fixtures. Record both transcripts here.
  Expected: fixture A lists the new skills under "Reviews run"; fixture B lists Deployment under
  "Skipped reviews" with zero deployment findings. A false fire on fixture B blocks the feature.
  Record as one dated observation against one named model, not as proof. Covers: AC-004b.

  **Done 2026-08-05.** Both fixtures run through `claude -p --model claude-sonnet-5` with
  `review-all`'s full definition and the fixture's complete contents inline.

  **Fixture B (negative) — correct.** Deployment listed under Skipped reviews with the reason
  "no deployment artifacts in this repository (no Dockerfile, Compose file, CI config, deploy
  script, IaC, or runbook present in the file list)". Zero deployment findings. No false fire.

  **Fixture A (positive) — correct, and it found every planted defect.** Detected Deployment "by
  artifact presence", routed to `/deployment-review`, `/container-review`, `/pipeline-review`, and
  correctly did **not** route `/release-readiness`. Findings: the `ARG NPM_TOKEN` build-arg secret
  (Critical, with the image-history reasoning), the plaintext credential in the committed Compose
  file (Critical), `FROM node:latest` unpinned (High), no `USER` (High), and **the canonical
  field-evidence failure** — CI runs lint/typecheck/test but never builds the deployable artifact
  (Medium).

  **The test caught a real defect, which is why it was worth running.** Fixture A's output routed
  to `/rightsizing-advisor`, which T013 had just unshipped. Chasing that down found the same
  dangling-reference bug in two more places: `deployment-review` and `container-review` each
  pointed at `/rightsizing-advisor` as an invocable command. **That is precisely the defect class
  this whole feature exists to fix** (SPEC Problem §1) — reintroduced by me, and caught only
  because AC-004b was a real run rather than an inspection. All three repointed; a repo-wide grep
  for `/rightsizing-advisor` in `skills/`, `docs/`, `adapters/` and `README.md` is now clean.

  **CORRECTION 2026-08-05 (found by `/qa-review`, after this task was first marked done).** The
  fixture A run above was recorded as a clean pass and **was not one.** It routed to
  `/deployment-review`, whose routing condition (a deploy script, runbook, `infra/` doc,
  provisioning step, systemd unit or backup script) fixture A does not meet — it has only a
  Dockerfile, a Compose file and a test-only workflow. The broad Deployment detection block pulled
  all three reviewers along with it, and nothing in the routing row or in `deployment-review`
  itself pushed back.

  This was a SPEC edge case (*"The presence of CI is not the presence of a deployment"*) that lived
  only in the spec and in no skill body. Fixed: `deployment-review` gained a
  **"When this skill does not apply"** section, and the `review-all` routing row now says a
  Dockerfile and a test-only pipeline are **not** a procedure. **Re-run confirms the fix** —
  fixture A now lists `/deployment-review` under Skipped reviews with the reason "no deploy
  procedure exists", and still routes `/container-review` and `/pipeline-review`.

  **Honest limits.** One observation, one model, single-turn — not proof and not a CI gate.
  Fixture A's triage pass did not flag the published port on all interfaces, the unpinned
  `postgres` image, or the missing healthcheck; those live in `container-review`'s own checklist,
  which this run did not execute (it routed, as designed). So this validates **routing and
  triage**, not the depth of the individual reviewers.

- [x] **T015** — Sync counts: `bash scripts/check-consistency.sh --fix` for markers and badges,
  then **by hand** (not covered by `--fix`) the README skill tables, the profile table row, the
  directory-tree comment at `README.md:451`, and the six unguarded prose claims of FR-012 —
  `docs/AGENTIC_ROUTING.md:38`, `adapters/README.md:31,36`, `adapters/claude/README.md:22`,
  `adapters/codex/prompts/README.md:7`, `adapters/codex/PARITY.md:21,35`. Also add
  `delivery-operations` to PARITY.md's "not ported in v1" row.
  Covers: AC-006, AC-009, AC-012. (FR-009, FR-012, FR-013)

  **Done 2026-08-05.** `--fix` corrected 7 markers/badges automatically (skills 61→65,
  profiles 7→8, templates 22→23, docs-templates 10→11). By hand, since `--fix` does not reach
  them: the six unguarded prose claims (`docs/AGENTIC_ROUTING.md`, `adapters/README.md` ×2,
  `adapters/claude/README.md`, `adapters/codex/prompts/README.md`, `adapters/codex/PARITY.md` ×2)
  plus the README directory-tree comment, the profile table row, the profiles-total row listing,
  and the specialized-reviews paragraph (which now states delivery reviews trigger on **artifact
  presence, not spec wording**).

  PARITY.md gained a `delivery-operations` not-ported row **and a named section** explaining the
  deferral: same reason as the other stack reviewers, plus the `codex` CLI is not installed here,
  so any prompt would ship unverified — an honest gap row beats an unverifiable prompt.

  **AC-012 verified:** `grep -rn "61 skills"` now matches only `CHANGELOG.md` and `specs/`, both
  historical. `check-consistency.sh` passes.

- [x] **T016** — Install verification, by execution: `bash install.sh --profile delivery-operations
  --central-dir <scratch>` against a throwaway directory (never `~/.claude`). Confirm one directory
  per shipped skill, `RUNBOOK.md` present, and the two planned skills reported as "planned, not
  installed" without error. Paste the output here. Spot-check `install.ps1` if `pwsh` exists;
  otherwise record the PowerShell path as unverified. Covers: AC-002.

  **Done 2026-08-05 — verified by execution, both installers.**

  `bash install.sh --profile delivery-operations --central-dir <scratch>` → exit 0. All four
  shipped skills present; `rightsizing-advisor` **absent** (correctly, post-T013);
  `docs/_templates/RUNBOOK.md` installed; planned items reported without error:
  `[planned] skill 'iac-review' / 'kubernetes-review' / 'rightsizing-advisor'` and
  `[planned] hook 'deploy-artifact-reminder'`.

  **`pwsh` is present, so the PowerShell path was actually run, not recorded as unverified:**
  `pwsh ./install.ps1 -Profile delivery-operations -CentralDir <scratch>` → exit 0, identical
  result set (four skills, rightsizing absent, RUNBOOK.md present). This is **behavioural** sh/ps1
  parity for the new profile, not just the parse parity CI checks.

  The SPEC's assumption that no installer change would be needed held: profiles are pure
  `profiles.json` data.

## Phase 4: Review

- [x] **T017** — Neutrality read (AC-011): read all five skill bodies in full against the NFR — no
  language presenting orchestration, managed services or multi-host topology as a maturity step,
  a next step, or a sign of seriousness. Record the verdict per skill. This is a judgment check
  no script can perform. Covers: AC-011.

  **Done 2026-08-05.** Read all four shipped bodies against the NFR. Grep for maturity-ladder
  language (`maturity`, `next step up`, `graduate to`, `not production-ready`, `serious teams`,
  `proper infrastructure`, `should adopt`, `recommend … kubernetes`) → clean.

  **The read found a real gap that the grep did not.** D013 asserted that all four reviewers carry
  an explicit *"Infrastructure weight is not this skill's business"* section — the argument for why
  dropping `rightsizing-advisor` was survivable. Only `deployment-review` and `container-review`
  actually had one. Rather than weaken D013's claim, the section was added to the other two:

  - `pipeline-review` — "the finding is always a missing *verification*, never a missing *tier*",
    against recommending matrices, promotion chains or self-hosted runners.
  - `release-readiness` — flagged in its own text as **the skill most likely to get this wrong**,
    because every unmet precondition has an expensive answer available. It now states that a
    precondition is closed by the smallest thing that closes it (execute the rollback, add one
    external check that pages someone, rehearse a rebuild) and that it must **never issue a No-go
    whose remedy is a heavier architecture**.

  This is exactly the class of defect AC-011 exists for: a claim that was true of half the profile
  and would have passed every automated check.

- [x] **T018** — Untouched-surface check: `git status --porcelain` shows no modification to
  `hooks/`, `agents/`, `settings.template*.json`, `install.sh`, `install.ps1`. Confirm
  `grep -rn "kubernetes-deployment-reviewer"` returns nothing presenting it as an existing skill
  outside historical roadmap/spec documents. Covers: AC-005, AC-010. (FR-015)

  **Done 2026-08-05.** `git status --porcelain` shows **no modification** to `hooks/`, `agents/`,
  `settings.template.json`, `settings.template.sh.json`, `install.sh` or `install.ps1`.
  `grep -rn "kubernetes-deployment-reviewer"` over `skills/`, `docs/_templates/`, `adapters/` and
  `README.md` → no matches. A repo-wide grep for `/rightsizing-advisor` as an invocable command in
  shipped artifacts → no matches (the three introduced during T011/T004/T005 were repointed in
  T014).

- [x] **T019** — Run all four gate scripts and paste the output: `check-consistency.sh`,
  `check-consistency.test.sh`, `graphify.test.sh`, `skill-eval.test.sh`. All must pass.


  **Done 2026-08-05. All four green:**

  | Gate | Result |
  |---|---|
  | `check-consistency.sh` | PASS — profiles.json, disk, settings wiring, README counts aligned |
  | `check-consistency.test.sh` | PASS — 30 passed, 0 failed |
  | `graphify.test.sh` | PASS — 66 passed, 0 failed |
  | `skill-eval.test.sh` | PASS — 20 passed, 0 failed |

  Identical to the T001 baseline: nothing regressed, and the two suites this feature does not touch
  (`graphify`, `skill-eval`) confirm no unrelated machinery was disturbed.

- [x] **T020** — Add the `CHANGELOG.md` entry: the profile, the shipped skills, the two deferred
  with their reason, and the `rightsizing-advisor` evidence outcome including a
  `NO-BASELINE-FAILURE` outcome if that is what T013 returned. Covers: AC-013. (FR-014)

- [x] **T021** — Run `/spec-review` then `/qa-review` on this feature; resolve findings before
  `/spec-close`. Covers: AC-001.

  **Done 2026-08-05.** Acceptance sweep: all four SDD documents present; **all seven candidate
  skills have a recorded decision** (D003 ships four, D004/D005 defer two, D013 unships the
  fifth on evidence). All four shipped `SKILL.md` files declare the full eleven-field
  `## SDD Contract`. No `profiles.json` shipped item is missing from disk.

  **The spec's conditional framing held under the outcome it anticipated.** AC-006 was written as
  "66 skills (or 65 under FR-011's fallback)" and AC-008 as "exactly one of these two states
  holds" — both are satisfied by the 65 outcome with no amendment. That was the point of writing
  the fallback into the acceptance criteria at spec time rather than negotiating it mid-implementation.

  Findings resolved during implementation rather than deferred: the `/rightsizing-advisor` dangling
  references (T014), and D013's overstated claim about the stance sections (T017). No open finding
  blocks close.

  Remaining non-blocking observation, carried to `/spec-close`:
  `docs/ROADMAP_JAVA_SPRING_CONTEXT.md` still names `kubernetes-deployment-reviewer` where the
  profile now says `kubernetes-review`. AC-005 permits historical roadmap mentions, so this is
  compliant, but the two names denote the same unshipped skill.

## Coverage map

| AC | Tasks |
|---|---|
| AC-001 | T009, T021 |
| AC-002 | T009, T016 |
| AC-003 | T004, T005, T006, T007, T008 |
| AC-004a | T011 |
| AC-004b | T002, T014 |
| AC-005 | T003, T018 |
| AC-006 | T010, T015 |
| AC-007 | T001, T019 |
| AC-008 | T012, T013 |
| AC-009 | T015 |
| AC-010 | T018 |
| AC-011 | T004, T005, T006, T007, T017 |
| AC-012 | T015 |
| AC-013 | T020 |
