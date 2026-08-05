# Decisions: Delivery-operations profile

## Decision log

### D001 - This feature is spec 024, not 023

**Date:** 2026-08-05

**Status:** Accepted

**Context:** The task brief asserted "023 is free — 000–022 exist and there are no unmerged
branches holding a number." The on-disk check agrees: `specs/features/` ends at `022`. But `023`
is **reserved in prose**, in committed artifacts, in three independent places:

- `CONTRIBUTING.md:65` — *"Until spec 023 lands a valid corpus, a result file attached to a PR
  must come from a scenario that meets the self-contained rule."* This is the merge gate's own
  text, promising contributors a specific future spec number.
- `evals/scenarios/README.md:10` — the superseded scenarios are *"kept as the starting point for
  spec 023"*.
- Spec 022's `SPEC.md`, `PLAN.md` and `TASKS.md` name spec 023 **thirty-two times**, moving FR-004,
  FR-007, AC-004, AC-006, T007, T010, T011, OQ-2 and OQ-3 into it by number.

**Decision:** Take **024**. Directory: `specs/features/024-delivery-operations-profile/`.

**Reasoning:** "Free" was checked against the directory listing only. The framework's numbering
rule (`CONTRIBUTING.md` ground rule 1) is about *claiming* a number, and 023 is claimed — by the
contributor-facing gate document, which is a stronger claim than an unmerged branch. Taking 023
for this feature would make `CONTRIBUTING.md` point at a delivery profile when it means the eval
corpus, and would silently orphan every one of spec 022's deferred requirements. Renumbering the
eval work instead would mean editing four committed documents to accommodate a feature that has
no reason to be 023.

**Consequences:** 023 stays reserved for the eval-corpus sweep. No document needs editing. This
decision is recorded here because the brief's premise was explicit and is being overridden.

---

### D002 - Profile named `delivery-operations`, not `delivery-platform`

**Date:** 2026-08-05

**Status:** Accepted — confirmed at planning (OQ-1 closed; the recommended default was taken when
`/spec-plan` was invoked without an objection)

**Context:** The brief's working name was `delivery-platform`, with an invitation to rename if
justifiable. The profile carries a hard constraint: nothing in it may read as pushing teams toward
heavier infrastructure.

**Decision:** `delivery-operations`.

**Reasoning:** "Platform" is not a neutral word in this domain — it names a discipline (platform
engineering) and an artifact (the internal developer platform), both of which presuppose a
platform team and a multi-service estate. A profile called `delivery-platform` would carry the
heavyweight posture in its own name, before a single skill was read, and would sit oddly on the
motivating case: a business running deliberately on Compose on one host. "Operations" describes
what the profile reviews — how software is delivered and operated — and is equally true of one VPS
and of a fleet. Rejected alternatives: `deployment-delivery` (redundant), `delivery-runtime`
(reads as runtime performance), `containers-deployment` (excludes pipelines, which are half the
field evidence).

**Consequences:** Profile key, installer flag and README entries all use `delivery-operations`.
Raised as OQ-1 for the review, since renaming after `profiles.json` lands is more expensive.

---

### D003 - Ship four review artifacts: `deployment-review`, `container-review`, `pipeline-review`, `release-readiness`

**Date:** 2026-08-05

**Status:** Accepted — carried into PLAN.md unchanged

**Context:** Seven candidates were offered as a list to prune. The test applied to each: does it
have a **distinct artifact set**, a **distinct failure mode**, and **judgment a neighbour does not
carry**? Two of three is a merge candidate; one of three is a drop.

**Decision:** These four ship as distinct skills.

**Reasoning, per skill:**

- **`container-review`** — distinct artifacts (`Dockerfile`, Compose), distinct failure modes
  (floating tags, root user, build-arg secrets, volume lifecycle, port publication as a perimeter
  decision), and none of it is reachable from any existing skill. Clearest keep of the seven.
- **`pipeline-review`** — distinct artifacts (`.github/workflows/`, `.gitlab-ci.yml`,
  `Jenkinsfile`) and one piece of judgment nothing else in the repo carries: **the gap between
  what a pipeline verifies and what its job names imply**. The field evidence is the canonical
  instance — `lint` + `typecheck` + `test`, no build, on a project whose deployable is a build.
  `qa-review` reviews whether tests are good; only this reviews whether CI actually runs and gates
  on them.
- **`deployment-review`** — distinct artifacts (deploy scripts, runbooks, `infra/` docs,
  provisioning steps, systemd units) and distinct judgment: **ordering, idempotency, and what a
  re-run does after a partial failure**. Nothing else in the repo reasons about sequence. It also
  owns the "procedure exists in three documents and in full in none" finding, which is a defect of
  the *documentation set*, not of any one file — a shape no other skill can even express.
- **`release-readiness`** — distinct in **kind**, not just in artifacts. The other three read
  files and emit file:line findings. This one asks what was **rehearsed**, and its output is a
  Go/No-go with preconditions marked *rehearsed* / *written but untested* / *absent*. It exists
  because of field evidence #4: three real bugs, including a world-readable plaintext database
  dump left in `/tmp`, were caught by exercising a live stack and would have passed every
  code-reading gate. A profile of file-readers alone would reproduce exactly that blind spot.

**Consequences:** Four skills, each with negative triggers per D008. Profile skill count is four,
or five if D006/FR-011 clears.

---

### D004 - `iac-review` is deferred to `plannedSkills`

**Date:** 2026-08-05

**Status:** Accepted — carried into PLAN.md unchanged

**Context:** Terraform/Pulumi/Ansible review — state handling, drift, destructive operations
hidden in a plan, idempotency, secret material in state. It passes the distinctness test cleanly:
the state file is a concept nothing else in the profile has, and `terraform plan` concealing a
destroy-and-recreate is a failure mode with no analogue in a Dockerfile.

**Decision:** Declare it in `plannedSkills`. Do not ship it in this feature.

**Reasoning:** It fails a different test — **evidence**. The entire motivating case is
Compose-on-a-VPS with GitHub Actions. There is no IaC in it, no audited Terraform state, no
observed drift incident. Everything I would write would be assembled from general industry
knowledge rather than from anything this framework has seen fail. Spec 022 spent its whole scope
establishing that this repository's product is behaviour-shaping prose and that asserting such
prose works without evidence is the defect it was written to fix; shipping a speculative reviewer
two specs later would contradict that directly. `plannedSkills` is the mechanism `profiles.json`
documents for precisely this state — declared for roadmap visibility, reported as "planned, not
installed", no error.

**Consequences:** Teams using Terraform get `container-review` and `pipeline-review` but no state
or drift review. `deployment-review` must say so explicitly in its own body (FR-001 honesty NFR)
rather than half-covering IaC and leaving users to discover the shallowness. Shipping it later
needs a spec, a real IaC codebase to audit, or both.

---

### D005 - `kubernetes-review` is deferred to `plannedSkills`

**Date:** 2026-08-05

**Status:** Accepted — carried into PLAN.md unchanged

**Context:** The brief attached a hard constraint: it reviews Kubernetes for teams already running
it, must never read as a recommendation to adopt it, and no skill in the profile may treat
orchestration as a maturity milestone.

**Decision:** Declare it in `plannedSkills`. Do not ship it in this feature.

**Reasoning:** Three reasons, compounding.

1. **Same evidence problem as D004, worse.** The motivating project deliberately does not run
   Kubernetes and has its scaling trigger written down and not yet met. There is no observed
   manifest failure anywhere in this feature's evidence base.
2. **Shipping it in the profile's first release is itself a signal.** The constraint is about what
   the profile *reads as*, and a v1 that ships a Kubernetes reviewer alongside four
   general-delivery skills says "this is where delivery leads" through its shape, no matter how
   carefully the body is worded. Deferring it says the opposite in the same channel.
3. **It is the largest and most easily botched surface** — probes, resource requests and limits,
   `securityContext`, RBAC scope, secret handling, rollout strategy, disruption budgets, namespace
   isolation. Written without evidence it would be the profile's weakest skill while being the one
   most likely to be misread as an endorsement.

There is also a repair benefit. `kubernetes-deployment-reviewer` is currently a **dangling
reference** in four committed places (SPEC Problem §1), including a shipped skill that hands off
to it and a shipped template that tells users to run it. Moving that promise from prose into
`plannedSkills` converts a broken routing claim into an honest roadmap entry, which is what
`plannedSkills` is for. FR-008b repoints the two shipped references.

**Consequences:** Teams already on Kubernetes get image review (`container-review`) and rollout
**procedure** review (`deployment-review`), and both must state plainly that manifest semantics
are out of reach. The dangling reference is fixed either way.

---

### D006 - `rightsizing-advisor` ships as a profile-scoped mindset skill, gated on evidence

**Date:** 2026-08-05

**Status:** Accepted — confirmed at planning (OQ-2 closed the same way as OQ-1). The counter-argument
stays on record: profile-scoping means the projects most at risk of premature orchestration may not
have the profile installed. Revisit if a user reports that gap.

**Context:** The counterweight skill. Two questions: does it earn a slot, and where does it live?

**Decision:** Ship it as `category: mindset` with `profile_scope: [delivery-operations]`,
**conditional on FR-011's eval**. If the eval does not support it, it moves to `plannedSkills` and
the profile ships four skills.

**Reasoning:** It earns a slot because its trigger is at a different moment from every review
skill in the profile — *before* infrastructure is proposed, not while reviewing what was already
chosen — which is the same structural argument that justifies `decomposer` and `scope-keeper`
against the review skills they sit beside. Folding its judgment into `deployment-review` as a
section would fire it only after the artifacts exist, which is exactly too late: by then the
Kubernetes cluster is in the diff. It is also the profile's ethical load-bearing element. An
infrastructure profile with no counterweight quietly pushes toward heavier infrastructure, which
would contradict `decomposer`, `scope-keeper` and `honest-advisor` — this framework's own stance —
in the framework's own voice.

It is **profile-scoped rather than core**, which is a first: all nine existing mindset skills are
core. Reasoning: core is already 41 skills and every one is a per-session context cost, and the
trigger is specifically an infrastructure-weight decision. The counter-argument is real — overbuild
judgment is not exclusive to projects that already have deployment artifacts, and profile-scoping
means the projects most at risk of adopting Kubernetes prematurely may not have the profile
installed yet. Raised as **OQ-2**; cheapest to change before `profiles.json` lands.

The evidence gate is not negotiable. `CONTRIBUTING.md` requires an `evals/results/` file produced
after the change for any `category: mindset` skill, and requires the scenario to be self-contained
because spec 022 D010 marked the whole existing corpus superseded. The Claude Code CLI is present,
so the run is possible; its outcome is not predictable, and FR-011 states the fallback rather than
assuming a pass.

**Consequences:** Skill count is 66 if the eval clears, 65 if it does not. AC-008 requires exactly
one of the two end states. The skill must also state that under-provisioning is the same failure
of judgment in the other direction — a counterweight that only ever argues for less is a bias, not
judgment.

---

### D007 - No new agent; reuse `domain-reviewer` and `security-reviewer`

**Date:** 2026-08-05

**Status:** Accepted — carried into PLAN.md unchanged

**Context:** `CONTRIBUTING.md` and the brief both treat a new agent as a real cost requiring
justification.

**Decision:** No new agent. Routing:

| Skill | `primary_agent` | `secondary_agents` |
|---|---|---|
| `deployment-review` | `domain-reviewer` | `security-reviewer` |
| `container-review` | `domain-reviewer` | `security-reviewer` |
| `pipeline-review` | `domain-reviewer` | `security-reviewer` |
| `release-readiness` | `domain-reviewer` | `security-reviewer` |
| `rightsizing-advisor` | `solution-architect` | `all` |

**Reasoning:** An agent in this repo is a tool-grant boundary and a responsibility contract, not a
topic label. These four review skills are read-only analysis over repository files — structurally
identical to every other skill `domain-reviewer` already serves across four profiles. Nothing
about a Dockerfile needs a different tool grant than a Spring configuration. `security-reviewer`
sits secondary where the findings are genuinely security findings (secret placement, port
publication as perimeter, secret exposure in CI logs), matching the pattern `payments-fintech`
already uses. `rightsizing-advisor` follows the mindset convention of `secondary_agents: [all]`.

**Amended 2026-08-05 during `/spec-clarify`.** `release-readiness` was originally mapped to
`final-conformance-reviewer`, on the reasoning that both are pre-release gates. Reading
`agents/final-conformance-reviewer.md` shows that is wrong: that agent's entire method is
**document-chain traceability** — SPEC → PLAN → TASKS → diff → tests → prior reviews — its inputs
are the feature's spec documents, its skills consumed are lifecycle skills, and its description
explicitly says *"Do NOT use for domain-specific or security-specific findings."*
`release-readiness` reads none of those documents and asks operational questions (was the rollback
executed, was the restore rehearsed, what enforces the perimeter). Sharing the word "gate" is not
sharing a contract. It maps to `domain-reviewer`, with `security-reviewer` secondary because the
perimeter and secret-placement questions are security findings.

**Consequences:** Agent count stays 8; badges and `count:agents-total` are unchanged.
`agentRouting` in `profiles.json` gains one block. No new agent, and no open verification left
for PLAN on this point.

---

### D008 - Routing collisions resolved explicitly, in both directions

**Date:** 2026-08-05

**Status:** Accepted — carried into PLAN.md unchanged

**Context:** Spec 021 made routing authoritative and required negative triggers against
neighbours. Five collisions exist — three among the new skills, two against existing ones.

**Decision:** These boundaries, each written into both skills' descriptions as negative triggers:

- **`deployment-review` ↔ `pipeline-review`.** The artifact decides. CI/CD **configuration** is
  `pipeline-review`; the **procedure** that puts software on a host is `deployment-review`. When
  deploy steps are inlined in a workflow, both apply on different questions: gating, provenance
  and log exposure to `pipeline-review`; step ordering, idempotency and re-run behaviour to
  `deployment-review`.
- **`deployment-review` ↔ `release-readiness`.** Review versus gate. `deployment-review` reads
  artifacts and finds defects, per diff. `release-readiness` asks whether the operational
  preconditions are met, once before a release, and produces a Go/No-go rather than findings.
- **`container-review` ↔ `security-review`.** Layer. Image and runtime posture — base image, user,
  published ports, build args, volumes — is `container-review`. Application-level risk in code is
  `security-review`. A secret in a build arg is the former; a secret in a source file is the
  latter.
- **`release-readiness` ↔ `observability-reviewer`.** `observability-reviewer` is Java/Spring
  code-level signal quality (structured logging, Micrometer, tracing, actuator). `release-readiness`
  is stack-agnostic and asks one question — would anything surface a **silent** failure — and
  reviews no logging code.
- **`pipeline-review` ↔ `qa-review`.** `qa-review` judges whether the tests are good.
  `pipeline-review` judges whether CI runs them, gates on them, and verifies what its job names
  claim.
- **`rightsizing-advisor` ↔ `decomposer` / `scope-keeper` / `architect-review`.** `decomposer` is
  task decomposition; `scope-keeper` is diff scope; `architect-review` is application architecture.
  `rightsizing-advisor` is infrastructure weight against demonstrated load, and nothing else.

**Reasoning:** Ambiguous routing is the failure mode spec 021 was written to prevent, and the
collision set grows quadratically — resolving it at spec time is far cheaper than discovering it
when two skills produce overlapping findings. Writing each boundary into **both** skills means a
user arriving from either side is redirected, which one-sided negative triggers do not achieve.

**Consequences:** `review-all` gains four routing rows; `release-readiness` is deliberately **not**
one of them, because it is not a diff review (FR-008a). Existing skills' descriptions are **not**
edited to add the reverse clause — the new skills carry both directions in their own text — which
keeps FR-015's untouched-surface promise. If review disagrees, editing `security-review`,
`qa-review` and `observability-reviewer` descriptions becomes a PLAN task.

---

### D009 - Codex parity updated in `PARITY.md` only; no new Codex prompts

**Date:** 2026-08-05

**Status:** Accepted — carried into PLAN.md unchanged

**Context:** Constraint 4 requires adapter parity to be updated or explicitly deferred with a
reason.

**Decision:** Update `adapters/codex/PARITY.md` — correct the skill counts it cites and name
`delivery-operations` in the "Stack-specific reviewers … not ported in v1" gap row. Add no prompt
under `adapters/codex/prompts/`.

**Reasoning:** This is an update, not a deferral, and it needs no caveat: `PARITY.md` already
states that stack-specific reviewers are not ported, so the new profile lands inside a documented
gap rather than creating a new one. The Codex adapter deliberately ships only the 7-prompt
lifecycle spine (spec 019 D004); adding delivery prompts would widen the adapter's scope in a
feature about the Claude adapter's coverage, and — decisively — the `codex` CLI is not installed
in this environment, so any prompt written would be unverified against a real provider CLI and
would have to ship labelled as such. Writing unverifiable content is worse than an honest gap row.

**Consequences:** Codex users get no delivery review. `PARITY.md` says so explicitly rather than
by omission. Porting stays a tracked follow-up, unchanged in status by this feature.

---

### D010 - `RUNBOOK.md` ships as a template; `DEPLOYMENT.md` is repaired, not rewritten

**Date:** 2026-08-05

**Status:** Accepted — carried into PLAN.md unchanged

**Context:** Field evidence #1 is a documentation-shape failure: the ordered procedure existed in
three places and in full in none. `docs/_templates/DEPLOYMENT.md` already ships, is
Java/Kubernetes-flavoured, and contains a dangling `/kubernetes-deployment-reviewer` reference.

**Decision:** Add `docs/_templates/RUNBOOK.md` (templates 22 → 23). Repair `DEPLOYMENT.md`'s
dangling reference (FR-008b) and change nothing else in it.

**Reasoning:** A reviewer that can only say "your runbook is fragmented" and offer no place to put
it is half a fix, and this framework's thesis is that improvisation is replaced by *artifacts*.
`DEPLOYMENT.md` is the wrong home: it describes the deployment **topology** (build, images,
environments, resources) as reference material, while a runbook is an **ordered, rehearsable
procedure** with preconditions, per-step verification, a rollback path and a last-rehearsed date.
Merging them would produce a document that is neither. Rewriting `DEPLOYMENT.md` to be
stack-neutral is out of scope — it is installed by `java-spring-backend` today and changing its
content is a separate concern from this profile's coverage gap.

**Consequences:** `delivery-operations` ships `RUNBOOK.md` and lists `DEPLOYMENT.md` as a shared
template. `count:docs-templates-total` 10 → 11 and `count:templates-total` 22 → 23.

---

### D011 - `rightsizing-advisor` is declared in `agentRoutingExempt`, not routed to an agent

**Date:** 2026-08-05

**Status:** Accepted — discovered at planning

**Context:** Not anticipated by the SPEC. `check-consistency.sh` implements an `agentRouting`
coverage rule (rule 7, spec 018 D014): **every non-core profile skill must appear in the profile's
`agentRouting`, or in its optional `agentRoutingExempt` array.** Core is exempt by design. All nine
existing mindset skills are core, so a profile-scoped mindset skill (D006) is the first to meet
this rule — and it is a hard-fail category, not a warning. Rule 6 additionally restricts
`agentRouting` targets to the six lifecycle agents.

**Decision:** List the four review skills in `agentRouting` per D007, and declare
`agentRoutingExempt: ["rightsizing-advisor"]`.

**Reasoning:** Routing it to `solution-architect` would satisfy the checker — that agent is in the
lifecycle set — but it would be a false declaration. `agentRouting` states which skills a lifecycle
agent *consumes as review input*; a mindset skill is a behavioural constraint on how any agent
works, not a review one of them runs. Its `## SDD Contract` already says so with
`secondary_agents: [all]`. `agentRoutingExempt` exists precisely for skills not meant for
lifecycle-agent consumption, so using it is the accurate declaration and using `agentRouting` would
be gaming a gate to pass it.

**Consequences:** `profiles.json` gains an `agentRoutingExempt` array — the first outside core's
implicit exemption. `primary_agent: solution-architect` stays in the skill's own contract (rule 2
validates it against the lifecycle-agent enum independently of `agentRouting`), so the skill still
declares who owns it. If T013's eval sends the skill to `plannedSkills`, the exempt array is
removed with it.

---

### D012 - Category assignments come from the checker's closed enum

**Date:** 2026-08-05

**Status:** Accepted — discovered at planning

**Context:** `check-consistency.sh:330` restricts `category` to a closed set: `lifecycle`,
`context-research`, `domain-reviewer`, `quality-review`, `mindset`, `orchestration`. "Delivery
review" is not a category and cannot be added without changing the gate this feature is judged by.

**Decision:** `deployment-review`, `container-review` and `pipeline-review` take
`category: domain-reviewer`. `release-readiness` takes `category: quality-review`.
`rightsizing-advisor` takes `category: mindset`.

**Reasoning:** The three artifact reviewers are stack-specific reviews extending generic ones,
which is exactly what every other `domain-reviewer` skill in the repo is. `release-readiness` is
deliberately different: it produces a Go/No-go verdict rather than domain findings, which matches
`quality-review` (the category `qa-review` and `security-review` carry) far better than
`domain-reviewer`. The split is not cosmetic — it is the same review-versus-gate distinction D008
draws between these two skills, expressed in the metadata.

**Consequences:** `category: mindset` on `rightsizing-advisor` is what triggers `CONTRIBUTING.md`'s
eval requirement, and `evals/README.md` resolves the mindset set by parsing this field rather than
from a hardcoded list — so the skill is in scope for the eval gate the day it lands, which is the
intended behaviour and not a side effect to work around.

---

### D013 - `rightsizing-advisor` is NOT shipped — its eval returned NO-BASELINE-FAILURE

**Date:** 2026-08-05

**Status:** Accepted — forced by evidence (T013)

**Context:** FR-011 gated the skill on an eval produced after it was written. R-1 rated this
outcome **likely** at planning time and pre-agreed the fallback, so this is the pre-committed path
rather than a new decision.

The run (`evals/results/rightsizing-advisor-2026-08-05.md`, `claude-sonnet-5`, 5 reps per arm):

| Arm | Failure exhibited |
|---|---|
| control (scenario only) | **0/5** |
| treatment (scenario + skill) | 0/5 |

Verdict `NO-BASELINE-FAILURE` — the control floor is 2/5 and the control was 0/5.

**Decision:** Do not ship it. `skills/rightsizing-advisor/` deleted; the skill moved to the
`delivery-operations` profile's `plannedSkills`. Shipped skill count is **65**, not 66. The
`agentRoutingExempt` array introduced by D011 was removed with it.

**Reasoning:** The verdict is real, not an artefact of a slack detection pattern. All five control
reps open by declining Kubernetes outright, and several independently do what the skill prescribes
— cite the supplied measurements, name the actual gaps (no alerting, migration discipline, off-box
backups, a runbook for total VPS loss) and propose the smallest fix instead of a tier upgrade. The
pattern was validated against seven hand-written controls before the run (four positive, three
negative, all correct), so a false negative is unlikely. Every one of the ten responses was read.

`claude-sonnet-5` has no overbuild reflex on this scenario, so the skill has no demonstrated
problem to solve. Shipping it anyway would mean adding a permanent per-session context cost on an
assertion the repository's own instrument had just contradicted — in the feature immediately after
the one built to stop exactly that.

**What carries the anti-overbuild stance instead** (the question D006 said had to be answered if
this skill were dropped): each of the four shipped reviewers carries an explicit
*"Infrastructure weight is not this skill's business"* section stating that the shape in front of
it — including a Compose stack on a single host — is a legitimate production architecture it has
no opinion about changing. The stance is therefore distributed across the profile rather than
concentrated in one skill, and AC-011's neutrality read (T017) enforces it. What is **lost** is the
proactive trigger: nothing now fires *before* infrastructure is proposed. That is a real reduction
in scope and is recorded as such, not glossed.

**Consequences:**

- Skills 61 → 65. `plannedSkills` for this profile is now three entries.
- The skill body is deleted, not kept dormant — the scenario
  (`evals/scenarios/rightsizing-advisor.md`) and the result file are committed, so the next attempt
  starts from evidence rather than from scratch.
- **This is one scenario, one model, single-turn.** It does not show the reflex is absent under
  multi-turn pressure, under a sunk-cost framing ("we already paid for the cluster"), or in a
  scenario where the heavier option is genuinely closer to justified. A future spec may revive the
  skill on a scenario that does establish a baseline failure; the bar is a control arm ≥ 2/5, not
  a better-worded skill.
- Spec 022's harness has now been used for a real decision for the first time, and it changed the
  outcome. That is the instrument working, and it is worth stating plainly: the framework declined
  to ship its own proposed skill because its own gate said the skill was unnecessary.
