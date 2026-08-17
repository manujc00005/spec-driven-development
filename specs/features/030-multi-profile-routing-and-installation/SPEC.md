# Feature Spec: multi-profile-routing-and-installation

## Status

Draft

## Problem

The framework assumes **one active profile**. That assumption held while every non-default profile
was a *concern* overlay (`payments-fintech`, `delivery-operations`, `messaging-event-driven`)
layered on a single language stack. Spec 029 broke it: `python-sql-data` is the first profile that
overlaps a **second language stack**, and a repository that is genuinely Java **and** Python at the
same time now has no correct answer.

Four concrete defects, all discovered during the 029 review chain, all sharing that cause:

1. **`domain-reviewer` is written for one profile.** Its method says *"Determine **the** active
   profile"* and its stop condition says *"Stop and ask which profile applies if the project has
   more than one plausible profile"* ([domain-reviewer.md:74](../../../agents/domain-reviewer.md:74)).
   In a polyglot repo the correct answer is **both apply, selected per changed file** — so the
   agent's own instructions push it either to pick one stack and under-review, or to interrupt the
   user on every review. `docs/AGENTIC_ROUTING.md` uses the same singular framing.

2. **The routing/contract ownership convention is unenforced.** Spec 029 D002 chose "an
   `agentRouting` entry means ownership" and rejected dual-listing on that basis. Verified by
   mutation test: setting `primary_agent: security-reviewer` in a skill contract while leaving the
   skill routed under `domain-reviewer` **passes `check-consistency.sh` green**. The convention the
   whole routing model rests on is defended by nothing.

3. **`scripts/update.sh` never delivers a new profile.** It re-installs *only* the profiles
   recorded in `<central-dir>/.sdd-install.json`. An adopter who has been updating correctly for
   months silently never receives a profile added after their last `install.sh` run — they cannot
   discover it, and no output tells them it exists.

4. **There is no way to ask for "everything enabled".** Profiles must be listed by hand.
   `install.sh` deliberately refuses to *"fall back to installing everything unfiltered"*
   ([install.sh:122](../../../install.sh:122)) — correct as a refusal to guess, but it leaves no
   way to say the thing explicitly either.

## Goal

A repository with more than one stack gets reviewed correctly by default: every applicable profile
is active at once, reviewers are selected by what actually changed rather than by picking a winning
profile, an adopter can install all enabled profiles in one explicit command, and `update.sh`
surfaces profiles added since their install.

## Non-goals

- **No new agent.** This changes how `domain-reviewer` selects reviewers; it does not add a router
  agent or split it per stack.
- **No new profile**, and no change to which skills any existing profile ships.
- **No automatic stack detection at install time.** Guessing the stack from repository contents is
  a different feature with its own failure modes; the adopter still names what they want.
- **No change to the shipped/planned distinction** or to the installer's refusal to guess on an
  unknown or disabled profile name.
- **No auto-install of newly added profiles by `update.sh`.** Reporting them is in scope; deciding
  for the adopter is not — that would install unrequested content on a silent update.
- **No change to `profiles.json` schema version** unless a requirement below genuinely needs a new
  key.
- **No Codex adapter port of the installer half.** `adapters/codex/install-codex.sh` has **no
  profile concept at all** (verified: zero occurrences of "profile"), so FR-008..FR-012 have no
  Codex counterpart to change. The routing half is prose in `adapters/codex/AGENTS.md` and is in
  scope only to the extent that its role descriptions carry the same singular framing. Recorded as
  an honest gap, same treatment as spec 029 D008.
- **No downstream project changes.**

## Users / Actors

- **Adopter with a polyglot repository** (the motivating case: Java/Spring services alongside
  Python scripts and SQL).
- **`domain-reviewer` agent**, which must select reviewers across several active profiles.
- **Maintainer running `scripts/update.sh`** on an existing install.
- **`check-consistency.sh`**, which must gain exactly one rule (defect 2) and no more.

## Current behavior

- All 8 agents are installed regardless of profile: `core` is `alwaysInstalled` and is the only
  profile declaring `agents`. **Agent installation is not a defect and needs no change** — this was
  verified on disk before writing this spec.
- Profiles accumulate across `install.sh` runs ([install.sh:661](../../../install.sh:661)) and the
  installer never deletes, so a multi-profile install already *works* — it is only unspoken.
- `.sdd-install.json` records the accumulated profile list; `update.sh` replays exactly that list.
- `domain-reviewer` receives no machine-readable statement of which profiles are active; it infers
  from installed skills or asks.
- `check-consistency.sh` validates that a routed skill exists and that the routing target is a
  lifecycle agent, but never compares the target against the skill contract's `primary_agent`.

## Desired behavior

- **Several profiles are active simultaneously and that is the normal case**, not an ambiguity to
  resolve. `domain-reviewer` selects reviewer skills by the *changed files* in the diff, running
  the Java reviewers on Java files and the Python/SQL reviewers on Python and SQL files in the same
  review.
- The agent stops and asks only when the diff genuinely does not resolve — never merely because
  more than one profile is installed.
- `check-consistency.sh` fails when a profile routes a skill to an agent that is not that skill's
  `primary_agent`.
- `install.sh` accepts an explicit "all enabled profiles" request and refuses to include disabled
  ones.
- `update.sh` reports profiles that exist in `profiles.json` but are absent from the adopter's
  `.sdd-install.json`, with the exact command to add them.

## Functional requirements

- FR-001: `agents/domain-reviewer.md` states that **more than one profile may be active** and
  selects reviewer skills per changed file rather than per project.
- FR-002: its stop condition is narrowed — stop only when the applicable reviewer cannot be
  resolved from the diff, not when several profiles are installed.
- FR-003: `docs/AGENTIC_ROUTING.md` carries the same multi-profile framing, replacing the singular
  "the active profile" language.
- FR-004: reviewer selection is stated in terms of a resolvable signal (changed file paths and
  extensions, plus each skill's `triggers`), not left to unaided inference.
- FR-005: a skill whose scope is genuinely language-neutral (today: `database-performance-reviewer`)
  states how it coexists with a stack-specific sibling that overlaps it (today:
  `java-performance-reviewer` on N+1 and connection pools), so both do not report the same finding
  twice.
- FR-006: `check-consistency.sh` gains **one** rule: for every profile, every skill listed under
  `agentRouting[<agent>]` must declare that same `<agent>` as `primary_agent` in its SDD Contract.
- FR-007: FR-006 has at least one positive and one negative case in
  `scripts/check-consistency.test.sh`.
- FR-008: `install.sh` and `install.ps1` accept an explicit request for every enabled profile.
- FR-009: that request never includes a profile marked `disabled`, and never suppresses the
  existing hard error when a disabled profile is named explicitly.
- FR-010: that request never bypasses the billable-scope rule — a billable add-on
  (`seo-geo-addon`) must not be installed by a blanket request without the adopter opting into it.
- FR-011: `update.sh` compares `profiles.json` against the adopter's `.sdd-install.json` and reports
  every enabled profile absent from it, naming the command that would add it.
- FR-012: `update.sh` does **not** install those profiles by itself.
- FR-013: `docs/INSTALL.md` documents the multi-stack case end to end: install several profiles,
  what `update.sh` will and will not do afterwards.
- FR-014: `agents/README.md` carries the same multi-profile framing as `agents/domain-reviewer.md`
  and `docs/AGENTIC_ROUTING.md` — its `domain-reviewer` row states *"the active profile ships"* in
  the singular today and would otherwise contradict the change.
- FR-015: whatever replaces "the active profile" must be **resolvable inside an adopted project**.
  Today's stated sources do not resolve there: `profiles.json` lives in the framework clone and is
  absent from an adopted repository, and "the project's installed skills" is a symlink to the
  central directory holding **every** installed skill, so it cannot distinguish one profile from
  another. See OQ-6 — this is the requirement the routing half stands or falls on.
- FR-016: the review output names which reviewers ran and which changed files selected them, so a
  reviewer that silently did not fire is visible.

## Non-functional requirements

- **Performance:** reviewer selection must not require reading every installed skill to decide
  which apply — the decision comes from paths, `triggers` and the profile manifest.
- **Security:** FR-010 is the security-adjacent requirement — a blanket install must not silently
  turn on a billable reviewer or any profile the adopter did not ask for.
- **Observability:** the review output must name which profiles were active and which reviewers ran,
  so a missing review is visible rather than silent. `update.sh` must name what it did not install.
- **Maintainability:** exactly one new checker rule (FR-006). Any additional validation is out of
  scope — the existing generic rules are the model, and spec 029 D005 is the precedent for not
  adding profile-specific logic.
- **Backward compatibility:** a single-profile install must behave exactly as it does today. No
  existing profile, skill contract or `.sdd-install.json` may need editing to keep working.

## API / Interface changes

- One new installer flag or sentinel value for "all enabled profiles", on both `install.sh` and
  `install.ps1`. Exact spelling is an open question.
- New reporting output in `update.sh` (additive; no flag, no behaviour change).
- No new slash command. No skill added or removed.

## Data model changes

None expected. `.sdd-install.json` is read as it is; the new report is derived, not stored. If
FR-011 turns out to need a "profiles the adopter declined" marker, that is a schema change and must
be raised as a decision rather than added silently.

## Edge cases

- **A profile is enabled today and disabled later** — a blanket install must not resurrect it, and
  `update.sh` must not keep advertising it.
- **`.sdd-install.json` missing or corrupt** — `install.sh` already discards a corrupt manifest
  silently; the new `update.sh` report must degrade to "cannot compare" rather than claim every
  profile is new.
- **The adopter deliberately does not want a profile.** FR-011 will re-report it on every update.
  Whether that is acceptable nagging or needs a suppression mechanism is an open question.
- **A diff touching a file no profile claims** (a `.md`, a config file) — must not trigger a
  reviewer, and must not trigger the stop condition either.
- **A single file that belongs to two profiles** — e.g. a `.sql` file in a Java/Spring repository
  with both profiles active: `sql-query-reviewer` and `database-review` both apply. Overlap must be
  stated as intended, with distinct questions, not resolved by dropping one.
- **A skill legitimately consumed by two agents** — FR-006 must not make the existing
  `secondary_agents` mechanism unusable; only the *primary* claim is validated.
- **`seo-geo-addon` under a blanket install** — covered by FR-010; the conservative default is to
  exclude it and say so.

## Acceptance criteria

- AC-001: `agents/domain-reviewer.md` no longer instructs the agent to pick a single active profile,
  and its stop condition no longer fires on multiple installed profiles.
- AC-002: `docs/AGENTIC_ROUTING.md` describes multi-profile activation, with no remaining singular
  "the active profile" instruction.
- AC-003: given a diff containing both a `.java` and a `.py` file, a real `domain-reviewer` run
  reports findings from **both** stacks' reviewers in one pass, names which reviewers ran (FR-016),
  and does not ask the user which profile applies. **Verified by an executed run against a real
  polyglot diff, with the transcript attached** — not by asserting that the documentation says so.
  See OQ-7 on whether this also warrants an eval scenario.
- AC-004: `check-consistency.sh` **fails** when a skill is routed under an agent that is not its
  contract `primary_agent`, and passes on the repository as shipped.
- AC-005: `scripts/check-consistency.test.sh` contains a positive and a negative case for AC-004,
  and the full suite passes.
- AC-006: `install.sh` and `install.ps1` install every enabled profile from one explicit request.
- AC-007: that request installs no `disabled` profile, and naming a disabled profile explicitly
  still fails hard.
- AC-008: that request does not install `seo-geo-addon` unless the adopter asks for it explicitly.
- AC-009: `update.sh` on an install predating a newly added profile reports it by name with the
  command to add it, and does not install it.
- AC-010: `update.sh` with a missing or corrupt `.sdd-install.json` reports that it cannot compare,
  rather than listing every profile as new.
- AC-011: a single-profile install produces the same result as before this change, verified by
  diffing `install.sh --profile java-spring-backend --dry-run` output captured **before** the change
  against the same command after it — byte-identical apart from any deliberate new reporting line.
- AC-012: `docs/INSTALL.md` documents the multi-stack flow.
- AC-014: no artifact still instructs an agent to determine a single active profile — checked
  across `agents/domain-reviewer.md`, `agents/README.md` and `docs/AGENTIC_ROUTING.md`.
- AC-013: `bash scripts/check-consistency.sh`, `check-consistency.test.sh`, `update.test.sh` and
  `graphify.test.sh` all pass.

## Test scenarios

- **Unit:** `check-consistency.test.sh` — positive and negative cases for FR-006 (AC-005), built
  the same way as the existing mutation-on-a-temp-copy cases.
- **Unit:** `update.test.sh` — a manifest missing a profile that `profiles.json` declares (AC-009),
  and a corrupt manifest (AC-010).
- **Integration:** `install.sh --dry-run` with the blanket request — asserts every enabled profile
  present, `blockchain-crypto` absent, `seo-geo-addon` absent (AC-006, AC-007, AC-008).
- **Integration:** `install.sh --dry-run` single-profile — output unchanged from today (AC-011).
- **Manual:** a real diff touching a `.java` file and a `.py` file in a repository with both
  profiles installed, reviewed end to end without the agent asking which profile applies (AC-003).
  **This is the acceptance test that matters** — the rest are structural.
- **Manual:** the same PowerShell paths on Windows, which cannot be exercised here.

## Assumptions

- **The mechanism already exists in this repository and does not need inventing.**
  `skills/review-all/SKILL.md` routes to stack-specific reviewers by *condition*, not by profile —
  *"Java/Spring project and Backend was detected"*, *"diff touches `prisma/schema*`"* — and its
  deployment section fires on **artifact presence**, explicitly warning that firing without the
  artifact *"is a defect, not a harmless extra"*. `domain-reviewer` is the outlier that still
  thinks in profiles. FR-004 aligns it with the precedent rather than introducing a second model.
- Reviewer selection can be driven by changed file paths plus each skill's `triggers` frontmatter.
  `triggers` is a repository convention consulted by the agent, **not** a mechanism any tool
  enforces — so this remains guidance the agent follows, at the same strength as every other
  instruction in an agent file. No structural enforcement is claimed.
- `profile_scope` in a skill contract stays advisory. A skill installed on the machine is loadable
  in any repository; this feature narrows *when it is selected*, not *whether it can be loaded*.
- Routing and installation are kept in one spec because they share one cause and one motivating
  user story. If planning shows the two halves do not share artifacts, splitting into two specs is
  a reasonable outcome rather than a failure.
- Agent installation needs no work — verified before writing this spec.
- The overlap in FR-005 is documentation, not code: both reviewers keep their coverage, and the
  fix is stating who reports what.

## Open questions

- OQ-1 **(blocking FR-008 wording only, not the design):** how is "all enabled profiles" spelled —
  `--profile all`, a separate `--all-profiles` flag, or a sentinel in `profiles.json`? `all` as a
  profile name risks colliding with a future real profile of that name.
- OQ-2 **(blocking FR-010):** should a blanket install exclude every billable add-on as a class, or
  only the ones flagged as such in `profiles.json`? There is no `billable` key today —
  `seo-geo-addon` is identified by prose in its `note`. Adding the key is a schema change.
- OQ-3 **(blocking FR-011 scope):** should an adopter be able to permanently decline a profile so
  `update.sh` stops reporting it? That needs somewhere to persist the refusal, which is a
  `.sdd-install.json` schema change.
- ~~OQ-4: does FR-006 hold for every skill shipped today?~~ **Resolved before planning.** Checked
  every routed skill in every profile against its contract's `primary_agent`: **0 mismatches**. The
  suspected candidates were clean — `next-prisma-web` routes `nextjs-server-actions-reviewer` and
  `privacy-compliance-review` under `security-reviewer` because both genuinely declare it as
  primary. FR-006 lands green on the repository as shipped, so it needs no migration and no
  grandfathering clause.
- OQ-5 **(non-blocking):** should the "reviewers run" line of FR-016 be a requirement on
  `domain-reviewer` alone, or on every review skill's output format?
- OQ-6 **(BLOCKING — this is the design question):** where does "which profiles apply" live for an
  adopted project? Verified today: **nowhere**. `agents/domain-reviewer.md:27` names two sources and
  neither resolves inside an adopted repository — `profiles.json` is not shipped to adopters, and
  `.claude/skills` is a symlink to the central directory containing every installed skill. The
  adopted project in front of us (`.claude/` here) holds only `settings.local.json`. Three ways out:
  **(a)** drop "active profile" as a review-time concept entirely and select purely from changed
  files against installed skills' `triggers` — the installed set becomes the ceiling and the diff
  the selector; **(b)** declare applicable profiles in the project, e.g. in `specs/CONSTITUTION.md`
  or a new `.sdd-profiles` file, which adds an artifact adopters must maintain and keep truthful;
  **(c)** read the machine-level `.sdd-install.json`, which is the wrong granularity — it says what
  this *machine* installed, not what this *repository* is. The answer changes FR-001, FR-004 and
  FR-015 materially.
- OQ-7 **(blocking the definition of done, not the design):** AC-003 is a behavioural claim about an
  agent, which is the class the framework says needs an eval — spec 022 built `evals/` for exactly
  this, and spec 024 refused to ship `rightsizing-advisor` on a failed one. Spec 029 D006 exempted
  *reviewer checklists*, not *agent behaviour*. Is one executed polyglot run enough evidence, or
  does this need an `evals/scenarios/` entry with a control arm?

## Contracted services

`specs/SERVICES.md` is absent → all billable add-ons treated as NOT contracted (conservative
default). Run `/project-init` to declare them. This is directly relevant here rather than
boilerplate: FR-010 and OQ-2 exist precisely because a blanket install must not turn on
`seo-geo-addon` while no service declaration exists.
