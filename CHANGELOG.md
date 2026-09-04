# Changelog

All notable changes to the SDD framework. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions are
[SemVer](https://semver.org) git tags. Each release maps to the spec trail
under `specs/features/` — the framework is developed with its own workflow.

> Note: the `version` field in `profiles.json` is the **manifest schema
> version** (installer compatibility), not the release version. Releases are
> tags.

## [Unreleased]

Runner frozen at spec 042 — the autonomous path is the prompt again, until real use says otherwise.
Spec 040 · Agent SDK runner (**experimental**) — the autonomous loop stops being a prompt and
becomes code, up to the point where closing the lifecycle would need a provider nobody has run.
Spec 039 · Windows first-run install fixes — the global instructions that never loaded.
Spec 038 · Portable personal config — the framework restored; the person did not.
Spec 037 · Workspace init — the map alone was never enough; state now generates itself.
Spec 036 · Mindset reminder hook — "always in effect" stops depending on the model remembering.
Spec 034 · Install manifest coherence — the manifest stops claiming a freshness it never verified.
Spec 031 · Autonomous orchestration — the loop closes without a human in the middle.
Spec 029 · Python/SQL/data profile — review coverage for script-and-query work.
Spec 027 · Query-first graph access — the framework's own default was the expensive path.
Spec 025 · Workspace SDD — the first coverage of what happens *between* projects.

### Changed

- **The runner is frozen at spec 042 (maintainer decision, 2026-09-04).** No new runner specs;
  spec 043 is paused on its branch, unmerged. `docs/AUTONOMOUS_SDD_FEATURE_PROMPT.md` is now
  versioned and is the supported path for unattended feature delivery. Spec 042's AC-013 kept
  the file untracked only for the duration of that spec; this is a new, explicit decision.
  Rationale and unfreeze condition: notice at the top of `runner/README.md`.
- **The install manifest records freshness per profile (spec 034).** `.sdd-install.json` moves to
  `schemaVersion: 2`, adding a `profileState` map of `{commit, version, installedAt}` per profile.
  A run only installs files for its **active** profiles, but the manifest stored a single
  top-level `installedCommit` for the whole recorded set — so after
  `./install.sh --force` with no `--profile`, all 8 recorded profiles were stamped at the new
  commit while 6 of them still held older files. Observed in the wild: `python-reviewer` sat 45
  lines behind with nothing reporting it, found only by a hand-run `diff -rq`.
  A run now names every recorded profile it did **not** refresh, with the commit each is stuck at
  and the exact command to refresh them, and `update.sh` computes its "what's new" delta from the
  **oldest** per-profile commit instead of the newest. `schemaVersion: 1` manifests migrate in
  place — no re-install, and a v1 reader still resolves a v2 file, so the change is revertible.

- **`update.sh`/`update.ps1` replay the recorded profile list verbatim, `core` included
  (spec 034).** Stripping `core` left an empty `--profile` set whenever core was all that was
  recorded, and the installer then fell back to `defaults.profile` — silently re-adding a profile
  the adopter had removed. The same fallback is now suppressed for removal-only runs.

- **The graph access ladder is inverted (spec 027).** Every Graphify-aware artifact used to say
  "check `GRAPH_REPORT.md` first" and mention the CLI's scoped queries as an optional refinement.
  Measured on a 1.650-node graph (`graph.json` 3,2 MB, CLI 0.17.1): `graphify summary` costs **354
  tokens**, `review-analysis <file>` 222–262, `review-context <file>` 103–1.057 — against **7.101**
  for reading the report in full. **Orientation via `summary` is 20× cheaper**, because the scoped
  commands resolve the graph file inside the CLI process and it never enters context. Across a
  four-project workspace, four `summary` calls cost ~1.400 tokens against ~18.269 for the four
  reports.
  The ladder is now `summary` → per-file queries → targeted traversal → **full report as the
  documented exception** → never `graph.json`, stated identically in `graphify-context`,
  `context-manager`, `sdd-workspace-onboarding`, `agents/codebase-researcher.md`,
  `docs/WORKSPACE_SDD.md`, `docs/TOKEN_ECONOMY.md` and the Codex prompt.
- **`codebase-researcher` gets a request protocol, not the ladder.** It declares
  `tools: Read, Grep, Glob` and has no Bash tool by design, so it *cannot* run a query. Telling it
  to "query first" would be an instruction violated on every invocation. Instead it names the exact
  command it needs and hands back — and must not silently fall through to reading the report just
  because that is the only thing it can open (spec 027 D002).
- Graphify remains optional at every rung: CLI absent → the report becomes rung 1, both absent →
  `Grep`/`Glob` with the context marked partial. `check-consistency.sh` gains a `graph-ladder`
  presence check over the seven doctrine artifacts, plus three test cases. It asserts the commands
  are *named*, not their order — prose ordering is brittle to match and a false positive blocks CI
  on correct text (D003).

Spec 024 · Delivery-operations profile — the first coverage of what happens after merge.

### Added

- **`runner/` — the phase-2 executor for the autonomous loop** (spec 040). Spec 031 shipped an
  implement→review→fix loop that only exists as a prompt inside an interactive Claude Code
  session: it cannot run from `cron` or CI, its caps and budget are arithmetic a model has to
  re-read after every context compression, and no Claude Code skill can invoke `codex exec`. This
  is the same protocol as **code** — a self-contained Python package (`sdd_runner`) that reads
  `TASKS.md`,
  dispatches one provider session per task or review, parses the verdict blocks with a strict
  fail-closed parser, enforces the caps and the delegation budget before dispatching, resumes
  idempotently from `ORCHESTRATION.md`, runs the repair/re-review cycle, and finalizes by
  freezing the approved implementation (031 FR-013).

  **Where it stops.** At the freeze. The runner proves the core is converged — every task
  checked, no open finding, no waiting escalation, every approval fresh, final conformance
  approved, and a declared baseline green and non-mutating — then records `CORE-COMPLETE` and
  exits `0`. It does not dispatch `/spec-review`, `/spec-close` or `/pr-description`, compute a
  closure delta over what they would have changed, or write `PR_DESCRIPTION.md`. Closing a
  feature lifecycle needs a provider that can execute a skill, and this spec certifies none: a
  stub answering `APPROVE` on `/spec-close`'s behalf would have proved only that the stub was
  asked. A follow-up provider spec picks up at that seam.

  **Maintainer tooling only.** No installer, `profiles.json` or manifest change; no adopter
  project depends on it, and the framework installs and behaves identically on a machine that has
  neither the Agent SDK nor the Codex CLI. Its test suite runs on stdlib `unittest` against a
  deterministic stub backend — 239 tests, no provider call, no cost.

  **What is not claimed.** `stub` is the only supported backend. The `claude` and `codex`
  adapters are **outside** the supported surface: Claude stays optional and lazily imported and
  has never been exercised against a real provider from this repository; Codex is implemented but
  **gated shut** pending DEBT-001/DEBT-002. No parity between them is claimed. The spec is
  classified **EXPERIMENTAL** with a **PARTIAL** conformance verdict, and what has and has not
  been observed is named in [`docs/SDD-ORCHESTRATION.md`](docs/SDD-ORCHESTRATION.md) rather than
  implied.

- **`/sdd-workspace-init` — end-to-end workspace setup** (spec 037). Takes a folder of related
  projects from nothing to fully wired in seven phases: detect and confirm the project list,
  refresh each project's Graphify graph at zero token cost, write the `.sdd-workspace/` map
  (delegating to `/sdd-workspace-onboarding`, which stays usable standalone), install the state
  machinery, link every child project back to the workspace layer, and verify. Copy-if-absent
  throughout: re-running fills gaps and never overwrites local adaptation.

  Ships three deterministic scripts as templates, extracted from a six-project workspace where
  they were built and field-tested rather than designed on paper:

  - `board.mjs` — generates `BOARD.md` from spec headers. Parses the five status formats and two
    task conventions found in real repositories, so adoption requires no migration. Warns on
    unblocked WIP > 1, closed-with-open-tasks, `Merged` with nothing pending, and unparseable
    status.
  - `drift.mjs` — checks whether governance documents still match the files they cite.
    Declarative: contracts are workspace-specific, so it ships as a skeleton with a worked
    example and exits 0 when none are declared.
  - `link-workspace.mjs` — writes an idempotent delimited block into each child project's
    instruction file. This closes the gap that mapping alone leaves: the map lives at the
    workspace root, while most sessions open inside a repository and never see it.

  Also ships `/sdd-status` and `/sdd-workspace-link` as workspace-local skills, a working guide,
  and the `SessionStart` hook wiring.

- **`Merged` / `Live` as distinct closing states.** `Merged` means the code is in `main` with
  zero unchecked tasks; `Live` means the behaviour was verified in production, with a date and
  pasted evidence. Conflating the two is how features accumulate as merged-but-never-activated.

- **Cross-project scoping rule.** A workspace-level parent spec is warranted only when a change
  moves a shared contract or requires ordering between repositories; otherwise the work is
  sibling specs linked by `Blocked-by:`. Independent repositories admit no atomic merge, so a
  single spec spanning all of them can never fully close.

- **`scope-keeper-reminder` hook (spec 036).** The mindset skills are declared *"always in effect"*,
  but a skill is **model-invoked**: its rules only enter context if the assistant chooses to load
  it. Claim and mechanism disagreed — the same shape as the manifest defect below. Measured across
  the whole spec 034 implementation session (25 tasks, ~1.300 lines): `/scope-keeper` was invoked
  **zero times**.
  `scope-keeper`'s own description names a deterministic trigger — *"before your first edit"* — so
  the hook is the harness observing it: a `PreToolUse` nudge on `Edit`/`Write`/`NotebookEdit` that
  emits the load-bearing scope rules **once per session**, then stays quiet. It never blocks (scope
  is a judgement, not a predicate), costs nothing on turns that do not edit, and
  `SDD_SCOPE_REMINDER=0` disables it. The message is a short excerpt; the skill stays the source of
  truth and a test fails if the two drift apart.

- **`--remove-profile` / `-RemoveProfile` (spec 034).** A profile could be adopted but never
  dropped: the manifest's profile list only ever grew, and `update.sh` re-installed whatever it
  found there — so a profile deleted by hand came back on the next update. Removal now deletes the
  items **only** that profile owns (anything still shipped by another recorded profile is kept),
  backs every file up under `_install-backups/<ts>/removed/` before deleting, refuses `core`,
  refuses unknown or path-like names, and supports `--dry-run` to show exactly what would go.

- **Autonomous orchestration mode (spec 031)** — `/sdd-orchestrate --autonomous
  specs/features/<nnn>-<name>` runs an approved feature through the whole implement → review → fix
  circuit and returns only when it is done or genuinely stuck. It refuses to start unless six
  conditions hold (spec `Ready`, no blocking open decision, runnable tasks, a non-default branch, a
  clean tree, and a baseline suite that passes *without* dirtying the tree), and each refusal names
  the condition and its fix. **Status: in progress** — the protocol, agent contracts and calibration have
  landed on both providers; the one remaining closure requirement is a maintainer's real,
  non-seeded run (T023).
  Guide: [`docs/SDD-ORCHESTRATION.md`](docs/SDD-ORCHESTRATION.md).
- **Structured verdict and completion blocks** — `security-reviewer`, `domain-reviewer` and
  `final-conformance-reviewer` now end an autonomous report with a fenced YAML `verdict:
  APPROVE | REJECT` block plus per-finding id/severity/`path:line`/required action, and
  `implementer`/`fast-worker` with `status: DONE | BLOCKED`. Prose stays for the human, but control
  flow reads **only** the block — the same class of mistake `36c3b04` had to undo when `--fix`
  keyed on rendered message text. The schema lives in the orchestrator skill; the agent files
  reference it rather than restating it.
- **`ORCHESTRATION.md` per-feature run state** — attempts, findings registry, delegation log,
  escalations, cap changes and closure delta, written before each step so a compacted or killed
  session resumes from the file instead of from conversation memory. Approvals are bound to a diff
  fingerprint, so any implementation change invalidates every stale approval rather than only the
  rejecting reviewer's.
- **Escalation classifier** — a blocker is resolved autonomously only when it is technical,
  reversible, in scope and outside every human-gated domain (product/UX, money, personal data,
  public contracts, destructive operations, anything contradicting the spec). Autonomous
  resolutions are recorded in `DECISIONS.md` as orchestrator-decided and stay auditable and
  reversible. Independent tasks continue while a question waits.
- **Caps that measure stagnation, not effort (D017)** — a reviewer may review as many times as the
  work requires. What is capped is a reviewer rejecting repeatedly while resolving nothing, and a
  single finding rejected more than `max-iterations` times; the delegation budget, defaulting to
  `max(25, 6 × unchecked tasks)`, is the global ceiling. The first design gated *every* reviewer
  invocation, which aborted any feature with more tasks than the cap — caught in audit before it
  shipped, with the calibration evidence recorded in the spec.
- **`python-sql-data` profile (spec 029)** — an optional overlay for projects built out of Python
  and relational SQL rather than around a framework: internal scripts, scheduled automation,
  reporting extracts, data validation and load processes. Combines with any stack profile
  (`--profile java-spring-backend,python-sql-data`). Ships five review skills and nothing else —
  no hooks, no templates, and **no new agents**: all five are primary-owned by the existing
  `domain-reviewer`, with `security-reviewer` as secondary on the three that surface injection,
  credentials or personal data. Guide: [`docs/PYTHON_SQL_PROFILE.md`](docs/PYTHON_SQL_PROFILE.md).
- **Five review skills** — `python-reviewer` (module structure, logic/IO/config separation,
  failing loudly instead of exiting 0 on partial failure, resource handling, dependency creep),
  `sql-query-reviewer` (join fan-out and duplicate rows, `NULL` semantics, `GROUP BY`/`HAVING`,
  window frames, CTEs, and parameterization versus string interpolation),
  `database-performance-reviewer` (index coverage, N+1, pagination, lock and transaction duration,
  batch size, and the write cost of adding an index), `data-pipeline-reviewer` (idempotency,
  partial failure, retries, incremental watermarks and late-arriving rows, timezone-explicit
  timestamps, file format contracts, traceability, reconciliation), `python-testing-reviewer`
  (pytest determinism and isolation, fixture scope, patch location, parametrization, how scripts
  and SQL get tested at all).
- **Scope stated in the skills, not just the docs.** These are reviews, not tooling: each skill
  carries an explicit "does NOT replace" section for `ruff`, `mypy`, `pytest`, `coverage.py`,
  `sqlfluff`, `EXPLAIN` and database monitoring. `database-performance-reviewer` labels every
  finding **structural** (true from the text) or **conditional** (depends on volume — "run
  `EXPLAIN` and check X"), because a static reviewer has no query plan. `sql-query-reviewer` is
  engine-agnostic and must state engine-specific rulings as assumptions. The profile is **not**
  data-engineering coverage — no orchestration design, data modelling, warehouse architecture,
  lineage or streaming semantics.
- **Workspace SDD design** ([`docs/WORKSPACE_SDD.md`](docs/WORKSPACE_SDD.md)) — a layer above
  per-project SDD for features that cross repositories. Records what each project owns, how the
  projects depend on each other and which contracts bind them, in a `.sdd-workspace/` tree at the
  workspace root. Every relationship carries evidence and a closed-vocabulary confidence marker
  (`Confirmed` / `Inferred - requires confirmation` / `Unknown - requires confirmation`), so an
  inference is never recorded as a fact. Cross-project features start with an `IMPACT_MAP.md`, and
  no project outside that map may be modified. Design and documentation only — no orchestration
  code, no installer change, no new agent.
- **`/sdd-workspace-onboarding`** — detects the projects in a workspace folder (by manifest and
  structure, so monorepos and folders of clones both work), summarises each from bounded sources,
  derives cross-project edges with cited evidence, and writes the `.sdd-workspace/` layer. Stops
  for approval before reading deeply, and never writes inside a child project except a
  user-approved Graphify refresh.
- **Ten workspace templates** under [`docs/_templates/`](docs/_templates/), all `WORKSPACE_`-prefixed
  and declared in `profiles.json` so the installer actually ships them: `WORKSPACE_CONTEXT`,
  `WORKSPACE_PROJECTS`, `WORKSPACE_DEPENDENCY_GRAPH`, `WORKSPACE_INTEGRATION_CONTRACTS`,
  `WORKSPACE_SHARED_DECISIONS` (seeded with the D001–D010 baseline), `WORKSPACE_GUARDRAILS`,
  `WORKSPACE_FEATURE_README`, `WORKSPACE_IMPACT_MAP`, `WORKSPACE_PROJECT_CHANGES`,
  `WORKSPACE_VALIDATION`. They first shipped in a `workspace/` subdirectory, which passed CI and
  reached no adopter — `install.sh` copies templates by name and does not recurse. Caught by running
  the install for real; see spec 025 D014, and note that structural CI cannot detect this class of
  defect.
- **Graphify documented as a per-project accelerator for multi-project work** — the workspace layer
  consumes each project's bounded `.graphify/GRAPH_REPORT.md` rather than reading repositories in
  full, and never the raw graph file. There is no merged workspace-wide graph: a super-graph across
  every repository would be larger than any single report and could not be consumed within a bounded
  context. Graphify stays optional; its absence marks the context *partial* and never blocks.
- **`sdd-workspace-onboarding.md` Codex prompt** ([`adapters/codex/prompts/`](adapters/codex/prompts/))
  — the same procedure in prompt packaging, with no native-agent claim and no global configuration.
- `scripts/check-consistency.sh` gains a **`workspace` check class**: the guide, the skill and all
  ten templates must exist, the Codex workspace prompt must exist whenever `adapters/codex/` does,
  and no shipped document may claim Graphify is required or instruct loading the graph file
  wholesale. Claim detection is sentence-scoped with negator suppression, so existing correct
  prohibitions stay clean — covered by a dedicated negative test.

- **`delivery-operations` profile** (8th profile) — reviews how code reaches a machine and stays
  alive there. Optional overlay, combinable with any stack profile:
  `--profile next-prisma-web,delivery-operations`.
- **`/deployment-review`** — the deploy *procedure*: step ordering and stated prerequisites,
  idempotency and what a re-run does after a partial failure, converge vs first boot, rollback
  including the point of no return, secret placement (`ps` exposure, world-readable windows,
  fail-closed vs silent degradation), and **procedure fragmentation as a High-severity finding** —
  an ordered procedure that exists in three documents and in full in none cannot be followed.
- **`/container-review`** — Dockerfile and Compose: image pinning, running as root, healthcheck
  semantics, volume lifecycle (what `down -v` destroys), build-arg secrets surviving in image
  history, multi-stage inheritance, and **port binding as the real perimeter** — Docker inserts
  iptables rules ahead of the host firewall, so a `ufw` rule is not evidence a published port is
  closed.
- **`/pipeline-review`** — what a pipeline actually verifies versus what its job names imply. The
  canonical case: `lint` + `typecheck` + `test` with no build, on a project whose deployable *is* a
  build. Also gating vs reporting, migration-drift detection, secret exposure in logs and
  `pull_request_target`-shaped triggers, artifact provenance, and cache keys that serve stale
  artifacts.
- **`/release-readiness`** — a Go/No-go gate, not a review. Records every precondition as
  *rehearsed* / *written but untested* / *absent*, where "written but untested" never counts as
  satisfied and an undated "yes" is downgraded. Asks whether the rollback was **executed**, the
  restore **rehearsed**, and whether anything would surface a *silent* failure.
- **`docs/_templates/RUNBOOK.md`** — gives the ordered deploy procedure a single home, with dated
  last-followed/last-rehearsed lines that feed `/release-readiness` directly, plus a
  **known counter-intuitive details** section for the knowledge that dies when undocumented.
- `review-all` now detects **Deployment by artifact presence, not spec wording**, and routes to the
  three artifact reviewers. Verified both ways against scratch fixtures: it fires on a repository
  with a Dockerfile and a workflow, and stays silent on one with neither.

### Fixed

- **`~/.claude/CLAUDE.md` was never linked on a first install (spec 039).** Both installers linked
  it *before* restoring the personal layer — but this repo only ships `CLAUDE.md.example`, and the
  personal import is what creates the real `<central-dir>/CLAUDE.md`. So a fresh machine printed
  `CLAUDE.md link skipped`, created the central file seconds later, and never retried: the user's
  global instructions silently did not load. The link step is now retried after the import, and the
  "does not exist yet" message is deferred to that retry so it only prints when it is true. Found
  by a real Windows 11 install, not by the eval suite — every installer test ran with `--skip-link`.

- **`install.ps1` suggested refresh commands with the wrong `-CentralDir` (spec 039).**
  `Report-UnrefreshedProfiles` decided whether the flag was needed by comparing against the *bash*
  default (`$HOME/.claude-config`), which is backwards in both directions on Windows: an install at
  the PowerShell default got a redundant flag, and one at `$HOME\.claude-config` lost the flag
  exactly where the command is wrong without it. The documented default,
  `C:\ProgramData\ClaudeConfig`, is unchanged.

- **`link-project.ps1` and `scripts/wire-hooks.ps1` could not find an install away from the Windows
  default (spec 039).** Both stopped at `C:\ProgramData\ClaudeConfig` and exited 1 with "Run
  install.ps1 first" — false advice about an installer that had already succeeded at
  `$HOME\.claude-config`. They now fall back to that location when the default is absent, and when
  they genuinely find nothing they name every path they checked. An explicitly passed `-CentralDir`
  is still honoured as given, never silently swapped.

- **An unprivileged Windows install gave up on the `CLAUDE.md` link (spec 039).** `New-Item
  -ItemType SymbolicLink` needs Administrator or Developer Mode; on corporate Windows it fails and
  the installer simply warned and moved on, leaving no `~/.claude/CLAUDE.md` at all. It now steps
  down symlink → hard link → copy, warning at each downgrade about exactly what the weaker
  mechanism costs — a hard link drifts silently if the central file is replaced by rename, and a
  copy is a snapshot that is not kept in sync. Unchanged on macOS/Linux, where `ln -s` needs no
  privilege and there is no failure to fall back from.

- **`agents/README.md` and `hooks/README.md` were write-once (spec 034).** Both were copied only
  when absent, so `--force` never refreshed them and they sat frozen at whatever commit first
  created them, with `installedCommit` implicitly vouching for content it had never written. They
  now go through the same backup-then-overwrite path as every other shipped file.

- **`install.ps1` never produced a byte-identical manifest on a no-op re-run (spec 034).**
  PowerShell 7's `ConvertFrom-Json` parses ISO-8601 strings into `[datetime]`, and interpolating
  one back rendered it in the current culture (`08/21/2026 16:25:52`), so spec 015's idempotence
  guarantee held on bash only. Every timestamp read out of a manifest is now normalised. Found by
  the new PowerShell suite — exactly the class of divergence a parse-only Windows gate cannot see.

- **`kubernetes-deployment-reviewer` was referenced in shipped artifacts and never existed.**
  `skills/spring-security-reviewer/SKILL.md` handed off to it and `docs/_templates/DEPLOYMENT.md`
  told users to run it. Both repointed; the Kubernetes gap is now named honestly rather than
  promised.
- Six unguarded "61 skills" claims in `docs/AGENTIC_ROUTING.md`, `adapters/README.md`,
  `adapters/claude/README.md`, `adapters/codex/prompts/README.md` and `adapters/codex/PARITY.md`.
  `check-consistency.sh` guards count claims only inside `README.md`, so these had no gate —
  extending the checker is recorded as a follow-up (spec 024 OQ-5).

### Not shipped, deliberately

- **`rightsizing-advisor` — the eval said no.** The planned mindset counterweight was written, then
  measured with `scripts/skill-eval.sh` per `CONTRIBUTING.md`: **control 0/5** on
  `claude-sonnet-5`, verdict `NO-BASELINE-FAILURE`. Every control rep declined the unjustified
  Kubernetes upgrade unprompted, so the skill had no demonstrated problem to solve. It moved to
  `plannedSkills`; the scenario and result are committed
  (`evals/results/rightsizing-advisor-2026-08-05.md`). This is spec 022's harness used for a real
  decision for the first time — and it changed the outcome.
- **`iac-review` and `kubernetes-review`** — declared `plannedSkills`. Neither had an evidence base
  in this feature, and a Kubernetes reviewer in the profile's first release would read as an
  endorsement regardless of wording. The four shipped reviewers state plainly that IaC state
  semantics and manifest semantics are covered by no shipped skill.

### Counts

Skills 61 → 65 · Profiles 7 → 8 · Templates 22 → 23 · Agents 8 (unchanged, no new agent) ·
Hook families 12 (unchanged).

Specs 016–021 · Installer hooks/lib fix, planned skills shipped, agentic routing layer,
provider-adapter layer and a first Codex adapter, security-agent hardening, skill-routing
and spec-status authority.

### Added
- **Spec Status Authority** (spec 021) — `sdd-guardrails` section 11 now states the
  `SPEC.md` status machine as an authority table: each transition has exactly one
  authorized performer (`/spec-plan` → `Ready`, `/spec-implement` → `In Progress`,
  `/spec-review` → `In Review`, `/spec-close` → `Done`) with the precondition each must
  verify. No other skill, agent, or ad-hoc edit may promote a status, and writing the
  status string is explicitly not the same as passing the gate it represents — a
  hand-written `In Review` silently defeats `/spec-close`'s own precondition check. The
  rule is mirrored into the four owning skills, into `spec-create`/`spec-clarify`/
  `spec-analyze`/`sdd-orchestrate` as a prohibition, and into
  `agents/solution-architect.md`'s forbidden actions. Documented honestly as a convention:
  a tool-call hook can see a `Status` line change but cannot tell which skill drove it, so
  nothing enforces this mechanically (spec 021 D001).
- **Negative triggers on confusable skills** (spec 021) — 21 skill descriptions gained a
  one-sentence `Not for … — use /…` clause naming the correct sibling, covering the pairs
  that actually overlap at routing time (`spec-create`/`spec-clarify`/`spec-update`,
  `spec-plan`/`spec-analyze`/`architect-review`, `spec-review`/`qa-review`/`review-all`,
  `debugger`/`root-causer`, `security-review`/`threat-modeler`, `verifier`/`qa-review`,
  `scope-keeper`/`refactor-review`, `context-manager`/`graphify-context`,
  `sdd`/`sdd-orchestrate`). Bounded to documented pairs rather than all 61 skills, since
  every description is a standing per-session context cost (D003), and kept to one calm
  sentence rather than block-style ALL-CAPS warnings (D002).
- **Hardened `security-reviewer` agent** (spec 020) — now the framework's explicit owner of
  vulnerability hunting (named taxonomy: injection, broken authN/authZ and tenant isolation,
  SSRF/CSRF, deserialization, file handling, race/TOCTOU, secrets/crypto, supply chain,
  information exposure, abuse resistance), attack anticipation (abuse cases per entry point
  and trust-boundary mapping *before* reading the implementation), and RGPD/LOPDGDD/AEPD
  review via the `privacy-compliance-review` skill. Review discipline: source-to-sink
  tracing separates **Confirmed** from **Potential** findings, structural verification is
  preferred over call-site spot-checks, and a plausibility filter keeps inapplicable
  findings out. Read-only tools and boundaries unchanged; no scanner/pentest capability is
  claimed.
- **Provider-adapter layer** (spec 019) — `docs/PROVIDER_ADAPTERS.md` and an `adapters/`
  tree separating the provider-neutral **SDD Core** (SPEC/PLAN/TASKS/DECISIONS lifecycle,
  review gates, skill contracts, agent responsibility model, guardrail intent) from
  per-provider packaging. `adapters/README.md` is the adapter registry + capability/honesty
  matrix; `adapters/claude/README.md` is a pointer — the Claude Code adapter remains the
  repository root, and no file was moved.
- **Codex adapter** (spec 019) — a first, **prompt-based** adapter under `adapters/codex/`:
  an `AGENTS.md` operating guide, a curated lifecycle-spine of prompts (create → plan →
  analyze → implement → review → close, plus a guardrails/consistency pass) derived from the
  core skills, an example config, and a self-contained, **copy-only** `install-codex.{sh,ps1}`.
  Honest by design — guardrails are conventions (not enforced hooks), the six roles are
  personas (not native subagents with a `tools:` grant), only the lifecycle spine is ported
  (not all 61 skills), and it is **unverified against a live Codex CLI**. The gaps are
  enumerated in `adapters/codex/PARITY.md`.
- **`install-all.{sh,ps1}`** (spec 019) — a thin convenience wrapper that installs both
  adapters by *calling* each installer in order; it does not modify or reimplement
  `install.sh`/`install.ps1`. `--codex-target` installs the per-project `AGENTS.md`; without
  it the Codex prompts still install globally and `AGENTS.md` is skipped — it is never written
  into the current directory or the framework repo itself (a hard guard refuses the latter).
- **Six lifecycle agents** (spec 018) giving the framework's skills an accountable
  consumer: `codebase-researcher` (bounded research, Graphify-first, read-only),
  `solution-architect` (SPEC/PLAN/TASKS/DECISIONS, pre-implementation test strategy,
  specs-only writes), `implementer` (executes approved TASKS within explicit file
  boundaries, the only lifecycle agent that edits application code), `security-reviewer`
  (auth/secrets/payments risk findings, read-only), `domain-reviewer` (stack/domain
  reviewer skills by active profile, read-only), and `final-conformance-reviewer`
  (SPEC → PLAN → TASKS → DIFF → TESTS → REVIEW traceability verdict, read-only). These
  are a separate, independent layer from the existing `deep-reasoner`/`fast-worker`
  model-tier agents (unchanged) — see `docs/AGENTIC_ROUTING.md`.
- `## SDD Contract` metadata block on all 61 skills (`category`, `primary_agent`,
  `secondary_agents`, `profile_scope`, `writes_code`/`writes_specs`/`analysis_only`,
  `side_effects`, `provider_specific`) — every skill now declares which agent owns it.
  Schema documented in `specs/features/018-agentic-routing-and-skill-contracts/CONTRACT_SCHEMA.md`.
- Additive `agentRouting` map in `profiles.json` for the five non-core, non-disabled
  profiles — declares which reviewer skills `domain-reviewer` or `security-reviewer`
  own for that stack. Ignored by older installers (unknown key, no schema break).
- `docs/AGENTIC_ROUTING.md` — the skills-vs-agents explainer and routing model reference.
- `check-consistency.sh` now validates: every skill's `## SDD Contract` parses with
  required fields and known enums; every `primary_agent`/`secondary_agents` entry
  resolves; every `agentRouting` target and routed skill is real; every non-core profile
  skill is covered by `agentRouting` (or explicitly exempted); `blockchain-crypto` stays
  disabled and unrouted; no `test-engineer` agent exists; `deep-reasoner`/`fast-worker`
  keep their declared models.
- 8 skills promoted from planned to shipped (spec 017), completing every
  `plannedSkills` entry in `profiles.json`:
  `observability-reviewer` (java-spring-backend);
  `stripe-payments-reviewer` + `payment-idempotency-reviewer`
  (payments-fintech — the profile ships content for the first time);
  `prisma-migration-reviewer` + `nextjs-server-actions-reviewer`
  (next-prisma-web); `aeo-review` + `geo-review` + `ai-visibility-review`
  (seo-geo-addon — full SEO family, all gated on `specs/SERVICES.md`
  contracts with the upsell-log fallback).
- Stack-specific reviewer routing table in `/review-all` and profile-gated
  detection lines in `/sdd` — the pre-existing stack reviewers
  (java-spring, event-driven, …) are now routed there too, not only the new ones.
- `scripts/install.test.sh` — regression test for the installer (spec 016):
  fresh-install hooks/lib presence, git-guardrails exit-2 blocking behavior,
  idempotent re-run.

### Changed
- Documentation repositioned as **provider-aware** rather than Claude-specific (spec 019):
  the README header, "What is this?", and `docs/AGENTIC_ROUTING.md`'s "Provider positioning"
  now frame SDD as a provider-neutral core with Claude Code as the primary adapter and Codex
  as a second, prompt-based adapter. No overclaiming — Claude/Codex parity is explicitly
  disclaimed. Count markers and validated badges are unchanged.
- `java-spring-reviewer`, `spring-boot-api-reviewer`, and `event-driven-reviewer` (spec
  018) no longer name external, unshipped `java-spring`/`api-design` subagents as their
  routing target — they now route through the repo's own `domain-reviewer` agent. Review
  logic and checklists are unchanged; only the ownership/routing wording changed.

### Fixed
- `security-review` and `privacy-compliance-review` (spec 020) delegated to `security` /
  `gdpr-spain` subagents this repo never shipped — in any self-contained install the primary
  path could not work and every run fell back to the generic checklist ("el agente security
  no está disponible"). Both skills now delegate to the shipped `security-reviewer` agent
  (their `## SDD Contract` blocks already declared it as `primary_agent`); the inline
  checklists remain as the documented fallback for agent-less sessions. Same drift class,
  same fix as spec 018 D006 (`java-spring`/`api-design` → `domain-reviewer`). A user-level
  stopgap skill created downstream (`software-security-review`) was unified back into the
  agent and retired with a backup (spec 020 D004).
- `install.sh` / `install.ps1` never copied `hooks/lib/` in profile mode,
  leaving every lib-sourcing hook (git-guardrails, sdd-spec-guard,
  java-build-test-guard, maven-compile, spring-config-guard) crashing with
  exit 1 on fresh installs — git-guardrails silently stopped blocking
  dangerous git commands (spec 016, found by the 2026-07-21 integration audit).

### Notes
- Skills remain reusable capabilities; agents are the accountable actors that consume
  them — no skill was converted into an agent, and no skill was deleted or renamed.
- Claude Code compatibility is preserved: all agent files use the same standard
  frontmatter (`name`, `description`, `tools`, and `model` only where already used);
  installers already copied `profiles[*].agents` generically and needed no changes.
- The six lifecycle agents are authored and validated (schema, routing, dry-run installs
  across all profiles) but have not yet been live-installed into a real Claude Code agent
  registry as part of this change — that remains a follow-up verification step, the same
  distinction this changelog already draws for `deep-reasoner`/`fast-worker` in 0.5.0.
- Graphify remains an optional accelerator, never a requirement — `codebase-researcher`
  degrades gracefully when no graph report exists, exactly as `context-manager` and
  `graphify-context` already did.
- The spec-019 provider-adapter layer is **purely additive**: `profiles.json`, the Claude
  installers (`install.sh`/`install.ps1`), the hook scripts, the settings templates, and
  every `skills/`/`agents/`/`hooks/` file were left untouched. The Codex adapter is honest
  about its limits (prompt-based, no enforced hooks, no native subagents, no profile-filtered
  install) and remains unverified against a live Codex CLI — a tracked follow-up, mirroring
  the structural-vs-live distinction this changelog already draws for the lifecycle agents.

## [0.5.0] — 2026-07-17

Specs 010–012, 014 · Graphify first-class, audit closure, adoption horizon.

### Added
- `scripts/setup-graphify.{sh,ps1}` — one-step Graphify adoption: consented
  CLI install, graph generation (version-tolerant scope fallback), gitignore,
  curated docs scaffolding, and automatic hook wiring into the project.
- `graphify-scan-reminder` hook (PreToolUse on Grep/Glob): throttled
  graph-first nudge when a dependency graph exists; `SDD_GRAPHIFY_NUDGE=0`
  opt-out.
- Background graph auto-refresh in `graphify-stale-reminder` (SessionStart):
  detached, lock-protected, `SDD_GRAPHIFY_AUTO=0` opt-out.
- Second worked example: `examples/002-server-action-rate-limiting/`
  (TypeScript/Next.js) — sliding-window rate limiting, x-forwarded-for trust
  boundary with attack tests, zod validation, enumeration-resistant responses,
  and a security review whose real finding (SEC-001) is preserved in the trail.
- CI hardening: graphify test suite (66 cases), shellcheck (severity error),
  and a Windows job parsing every `.ps1` — sh/ps1 parity is machine-checked.
- README badges enforced by the consistency harness (`readme-badge` category,
  auto-synced by `--fix`); self-test counts read dynamically instead of
  hardcoded.
- `scripts/graphify.test.sh` — sandboxed suite for the Graphify layer (stubbed
  CLI, no npm needed).
- CHANGELOG.md, CONTRIBUTING.md, and GitHub issue templates.

### Fixed
- Graphify report detection: consumers looked for `GRAPH_REPORT.md` at the
  project root while the CLI writes `.graphify/GRAPH_REPORT.md` — hooks and
  skills now resolve the canonical path with a legacy fallback. The
  `graphify-stale-reminder` hook is now actually wired in both settings
  templates (docs claimed it; no template registered it).
- Race conditions: hook lock deletion between check and stat; `read` on closed
  stdin in `setup-graphify.sh`.
- Worked example renumbered `002` → `001` (no gap); spec 006 status normalized
  to the standard section format.

### Changed
- Graph-first token doctrine: `context-manager` and `graphify-context` derive
  reading lists from the graph (CLI queries preferred) before any repo-wide
  scan; documented across SDD-ORCHESTRATION, GRAPHIFY template, and
  CLAUDE.md.example.

## [0.4.0] — 2026-07-16

Specs 007–009 · CI, scaffolding parity, hook wiring.

### Added
- `scripts/check-consistency.sh` + self-test + GitHub Actions workflow:
  profiles.json ↔ disk ↔ settings templates ↔ README counters drift detection
  (`--fix` auto-corrects README markers).
- `scripts/wire-hooks.{sh,ps1}` — additive, idempotent hook wiring into a
  project's `.claude/settings.json` with timestamped backups;
  `settings.template.sh.json` for macOS/Linux.
- Per-project specs support templates (SPECS-README, SDD-GUARDRAILS,
  CLAUDE-SDD); `/project-init` scaffolds the full `specs/` structure and
  `/sdd` gates on it.

## [0.3.0] — 2026-07-14

Specs 004–006 · Orchestration, onboarding, first example.

### Added
- Multi-model orchestration: `deep-reasoner` (Opus) and `fast-worker` (Sonnet)
  agents + `/sdd-orchestrate` skill with cost-control doctrine.
- `/sdd-onboard` — adaptive onboarding of existing projects (read-only
  analysis, context docs scaffolding) with optional Graphify detection.
- First worked example: payment webhook idempotency (Java/Spring).
- Framework hardening: macOS bash 3.2 compatibility, cross-platform polish,
  corrected hook wiring paths.

## [0.2.0] — 2026-07-13

Specs 002–003 · Stack profiles.

### Added
- `java-spring-backend` profile: JPA/transactions, Spring REST, Spring
  Security, JVM performance reviewers + build/config guard hooks.
- `messaging-event-driven` profile: event-driven and microservices-patterns
  reviewers, messaging templates.

## [0.1.0] — 2026-07-05

Specs 000–001 · Foundation.

### Added
- Core SDD lifecycle skills (`/spec-create` → `/spec-plan` → `/spec-analyze`
  → `/spec-implement` → `/spec-review` → `/spec-close`) with specialized
  reviews (QA, security, database, performance, API).
- Guardrail hooks (git-guardrails, sdd-spec-guard, status banner) in sh/ps1
  parity; profile-aware installer with dry-run and central-config model.
- Graphify-aware context layer (`context-manager`, `graphify-context`) with
  graceful degradation.

Versions 0.1.0–0.4.0 are retrospective milestones reconstructed from the spec
trail and commit history; v0.5.0 is the first tagged release.

[0.5.0]: https://github.com/manujc00005/spec-driven-development/releases/tag/v0.5.0
