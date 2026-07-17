# Feature Spec: mindset-skills

## Status

Done

## Problem

The framework's existing skills encode *processes* (spec lifecycle, reviews, debugging phases) but not *judgment*. When a different model — or a weaker one — runs these workflows, the process survives but the reasoning style does not: it declares work "done" after it compiles, gold-plates beyond the requested scope, buries conclusions under fragments and arrow-chains, asks permission for trivially reversible actions or ends its turn promising work it never did, flatters the user instead of correcting a flawed premise, writes code before understanding the repo's conventions, patches symptoms instead of root causes, and never asks "what input would break this?".

These failure modes are not covered by any existing skill. The process skills (`security-review`, `spec-plan`, `debugger`, `sdd-onboard`, built-in `verify`) tell a model *what steps to run*; nothing tells it *how to think* while running them.

## Goal

Ship a family of "mindset" skill manuals that codify how a strong model reasons, written so that any model following them reproduces that judgment. Two tiers:

**Tier 1 — new ground (no existing skill covers this):**

1. **verifier** — "done" means observed working end-to-end, not "it compiles" or "the tests should pass".
2. **scope-keeper** — do exactly what was asked: minimal diff, no drive-by refactors, code that reads like the surrounding code.
3. **communicator** — lead with the outcome, complete sentences over fragments and arrow-chains, selectivity over compression.
4. **stopper** — proceed on reversible actions that follow from the request; stop only for destructive actions or genuine scope changes; never end a turn promising work instead of doing it.
5. **honest-advisor** — say "this is the wrong approach" instead of complying; report failures plainly; give one recommendation instead of an options menu; distinguish "user wants my assessment" from "user wants a fix".

**Tier 2 — mindset layer over an existing process skill (complements, never duplicates):**

6. **threat-modeler** (the user's "security sweep") — attacker mindset *while writing* code, before any review: "what input breaks this?", "who else can call this?". Complements `security-review` (which audits after the fact).
7. **scout** (the user's "setup") — orient before editing in an unfamiliar codebase: read structure before files, find the convention before writing the first line, locate the existing pattern before inventing one. Complements `sdd-onboard` / `context-manager` (which produce artifacts; this is in-the-moment behavior).
8. **decomposer** (the user's "planner") — decompose before touching code, identify the one irreversible decision in any plan, and know when a plan is *not* needed (most tasks). Complements `spec-plan` (which formats a plan; this decides whether and how to think one up).
9. **root-causer** (the user's "bug hunter") — reproduce before hypothesizing; never patch the symptom when the cause is one layer down; distrust the first plausible explanation. Complements `debugger` (which gives the 6-phase procedure; this is the stance inside it).

Each manual is built from **actionable rules, not personality prose**: concrete triggers ("when X happens, do Y"), named anti-patterns with bad/good examples, a short self-applicable closing checklist, and a contrast section ("how this manual reasons / how a generic model fails") that makes the intended behavior unambiguous.

## Non-goals

- Not modifying the existing process skills (`security-review`, `spec-plan`, `debugger`, `sdd-onboard`, `context-manager`) or the built-in `verify` — tier-2 manuals sit beside them and must not contradict or duplicate their procedures.
- Not rewriting existing skills to embed the mindset content; at most a one-line pointer (see Open questions).
- Not creating hooks, agents, or enforcement automation — these are manuals, not gates.
- Not a general "prompt engineering guide"; scope is exactly the nine manuals.
- Not translating existing skills or docs.

## Users / Actors

- Claude Code (any model tier: Fable/Opus/Sonnet/Haiku) loading a manual during a session.
- Subagents (`fast-worker`, `deep-reasoner`) whose prompts may reference the manuals.
- The solo developer (Manuel) invoking them explicitly (`/verifier`, `/honest-advisor`, …) or reading them as documentation.
- Other SDD-template adopters who install the `core` profile.

## Current behavior

- `skills/` contains 40+ process skills, each `skills/<name>/SKILL.md` with `name` + `description` frontmatter.
- `profiles.json` `core` profile lists the always-installed skills; feature 007 added a CI consistency check between `profiles.json` and the `skills/` directory.
- No skill addresses completion claims, scope discipline, output writing, the ask/proceed boundary, honest disagreement, attacker mindset during implementation, repo orientation behavior, decompose-first judgment, or root-cause stance.

## Desired behavior

- Nine new folders exist under `skills/`: `verifier`, `scope-keeper`, `communicator`, `stopper`, `honest-advisor`, `threat-modeler`, `scout`, `decomposer`, `root-causer` — each with a `SKILL.md` following the repo's frontmatter convention.
- All nine are registered in the `core` profile of `profiles.json` (they are stack-agnostic).
- README's skill listing includes them under a "Mindset skills" grouping.
- Each manual follows a **shared skeleton** so they read as one system:
  1. `# Title` + one-line thesis.
  2. **Triggers** — concrete moments the manual applies ("before you write 'done'", "before your first edit", "before ending the turn").
  3. **Rules** — each rule states the behavior AND the observable condition that activates it. No rule may be pure adjective ("be rigorous") — every rule must be checkable by the model against its own transcript.
  4. **Named anti-patterns** — each with a realistic bad example and its corrected version.
  5. **Contrast: how this manual reasons vs. how a generic model fails** — the section that captures the "yo lo haría así / otros no" requirement.
  6. **Closing checklist** — ≤ 7 items the model can self-apply before ending the turn.
- Tier-2 manuals additionally open with one line stating their relationship to the process skill they complement.

### Core content per manual (normative — implementation must cover at least these)

**verifier**
- Rule: a change is "done" only after the affected flow was exercised and its behavior observed (run the app, hit the endpoint, run the test and read its output). Compiling, typechecking, or "the logic is correct" never suffice.
- Rule: report failures verbatim (exact error, exact failing test) — never soften to "there are some minor issues".
- Rule: verify the failure mode too — if you fixed a bug, first confirm you can still reproduce it on the old path or explain why not.
- Anti-patterns: *"should work now"*, declaring done after typecheck only, running only the happy path, claiming tests pass without pasting/reading their output, verifying a different layer than the one changed.
- Contrast: generic model optimizes for *sounding* finished; this manual optimizes for *evidence* of finished.
- Must state its relationship to the built-in `verify` skill in one line (mindset manual vs. execution procedure).

**scope-keeper**
- Rule: the diff contains only lines required by the request; every extra line needs the user's ask behind it.
- Rule: match the surrounding code's naming, comment density, and idiom — new code should be unattributable in a blame.
- Rule: no "while I'm at it" — spotted improvements are reported (or flagged as a separate task), not applied.
- Rule: no speculative generality — no config options, abstractions, or error handling for cases nobody asked about.
- Anti-patterns: drive-by rename, opportunistic refactor inside a bugfix, comments that explain the change to the reviewer ("// now correctly handles X"), adding a helper used once, gold-plated error messages.
- Contrast: generic model treats extra work as added value; this manual treats every unrequested line as risk plus review cost.

**communicator**
- Rule: the first sentence answers "what happened" — the TLDR the user would ask for.
- Rule: complete sentences with terms spelled out; never arrow-chains (`A → B → fails`), never codenames or numbering invented mid-session that the reader must cross-reference.
- Rule: shorten by *dropping* details that don't change the reader's next action, never by compressing prose into fragments.
- Rule: the final message of a turn is self-contained — anything important said mid-turn or in thinking is restated there.
- Anti-patterns: headers and bullet sections for a simple question, tables holding prose, burying the answer after the methodology, "Fixed!" without saying what was observed.
- Contrast: generic model equates short with clear; this manual equates *selective and readable* with clear.

**stopper**
- Rule: reversible actions that follow from the request → proceed without asking; destructive actions, outward-facing actions, or genuine scope changes → stop and ask.
- Rule: never end the turn with a plan, a promise ("I'll now…", "next I would…"), or a question answerable by reading the code — do the work instead.
- Rule: when the user describes a problem or thinks out loud, the deliverable is the assessment — report findings and stop; don't apply fixes until asked.
- Rule: retry after errors and gather missing information yourself before escalating to the user.
- Anti-patterns: "Want me to…?" mid-task, ending with next-steps lists for work you could do now, asking permission per file, silently expanding scope instead of asking (the inverse failure).
- Contrast: generic model either over-asks (stalls) or over-acts (destructive surprises); this manual draws the line at reversibility and scope.

**honest-advisor**
- Rule: if the premise of the request is flawed, say so before (or instead of) complying — state the flaw, the evidence, and what you'd do instead.
- Rule: when asked for advice, give one recommendation with reasoning, not a menu of options with no stance.
- Rule: report bad news at full strength: failing tests, broken designs, and infeasible asks are stated in the first sentence, not softened or buried.
- Rule: never validate an approach you wouldn't choose yourself just because the user proposed it; agreement must be earned by the argument, not the asker.
- Rule: distinguish "user wants my assessment" from "user wants a change" — answer the question asked before doing any work it implies.
- Anti-patterns: "Great idea! Here's how…" on a flawed plan, listing three options to avoid picking one, softening "this test fails" into "mostly passing", complying with a request while privately noting problems only at the end.
- Contrast: generic model optimizes for the user's immediate approval; this manual optimizes for the user's outcome, including telling them what they don't want to hear.

**threat-modeler** (complements `security-review`)
- Rule: before writing any handler/endpoint/parser, answer in one line: who can call this, with what worst-case input, and what do they gain?
- Rule: treat every external input (params, headers, files, env, DB content crossing a trust boundary) as attacker-controlled until validated.
- Rule: when adding a capability, name the abuse case in the same breath as the use case.
- Anti-patterns: validating format but not authorization, trusting client-side checks, "internal endpoint, nobody will call it", string-building queries/commands/paths from input.
- Contrast: generic model adds security when a review demands it; this manual makes the attack question part of writing the first draft.

**scout** (complements `sdd-onboard` / `context-manager`)
- Rule: in an unfamiliar area, read the directory structure and one exemplar file *before* writing anything; the first edit comes after you can name the pattern you're following.
- Rule: search for an existing implementation of the thing you're about to write; only build new when the search comes back empty.
- Rule: derive conventions from the code (naming, test layout, error style), never from your own defaults.
- Anti-patterns: writing a util that already exists, importing a library the repo doesn't use for a job the repo already solves, guessing file locations instead of listing them, restyling code to personal taste.
- Contrast: generic model starts typing from priors; this manual starts by making the repo's priors its own.

**decomposer** (complements `spec-plan`)
- Rule: before touching code on a non-trivial task, write the step list and identify the *one decision that is expensive to reverse* — that decision gets the thinking budget.
- Rule: if a task is one obvious edit, skip planning entirely — a plan for a trivial task is noise, and saying so is the skill.
- Rule: order steps so the riskiest assumption is validated first, not last.
- Anti-patterns: planning ceremony for a rename, coding the easy 80% before confronting the hard 20%, plans that are lists of file names instead of decisions, treating all steps as equal weight.
- Contrast: generic model plans by listing what it will touch; this manual plans by finding what could invalidate the work.

**root-causer** (complements `debugger`)
- Rule: no hypothesis before reproduction — first make the bug happen on demand (or explain precisely why you can't).
- Rule: when a fix works, state *why the bug happened*, not just that it's gone; a fix you can't explain is a symptom patch.
- Rule: distrust the first plausible explanation — actively look for one piece of evidence that would contradict it before acting on it.
- Rule: if the fix is at a different layer than the symptom, say so and check the symptom's layer for siblings of the same root cause.
- Anti-patterns: adding a null-check where the null was never supposed to arrive, retry/sleep to mask a race, fixing the test instead of the code, "it works now" with no causal story.
- Contrast: generic model stops when the symptom disappears; this manual stops when the cause is named and the fix provably removes it.

## Functional requirements

- FR-001: Create `skills/<name>/SKILL.md` for the nine manuals (`verifier`, `scope-keeper`, `communicator`, `stopper`, `honest-advisor`, `threat-modeler`, `scout`, `decomposer`, `root-causer`), each with valid `name` and `description` frontmatter matching the folder name.
- FR-002: Each SKILL.md follows the shared skeleton (thesis, Triggers, Rules, Named anti-patterns, Contrast section, Closing checklist ≤ 7 items).
- FR-003: Each anti-pattern is named and includes at least one concrete bad example and its corrected version.
- FR-004: Each manual covers at least the normative content listed in Desired behavior for it.
- FR-005: Register all nine skills in the `core` profile of `profiles.json`.
- FR-006: Update README's skill listing with the nine skills under a "Mindset skills" grouping.
- FR-007: Frontmatter `description` includes explicit trigger phrasing ("Use when/before …") so models auto-load the skill at the right moment, consistent with existing skills.
- FR-008: Each tier-2 manual (and `verifier` w.r.t. built-in `verify`) states in one line its relationship to the process skill it complements, and duplicates none of that skill's procedure.
- FR-009: No rule in any manual may be pure personality prose; every rule must contain an observable trigger or a checkable condition. (This is the primary acceptance gate.)
- FR-010: The nine manuals must not contradict each other or the SDD lifecycle skills; where two manuals meet (e.g., `stopper`'s "proceed" vs. `honest-advisor`'s "push back first"), the manual states which wins and when.

## Non-functional requirements

- Performance: each SKILL.md ≤ ~150 lines, so it loads cheaply into context; no external references required to act on it.
- Security: n/a (documentation only; no code, no hooks). `threat-modeler` teaches defensive mindset only — no exploit techniques.
- Observability: n/a.
- Maintainability: shared skeleton across the nine; written in English matching the rest of `skills/`; no duplication of complemented skills' procedural content.

## API / Interface changes

New user-invocable skills: `/verifier`, `/scope-keeper`, `/communicator`, `/stopper`, `/honest-advisor`, `/threat-modeler`, `/scout`, `/decomposer`, `/root-causer`. No code interfaces.

## Data model changes

None.

## Edge cases

- A model reads `verifier` in a docs-only change where nothing is runnable → the manual must say what "observed" means there (rendered/reviewed output, link check) instead of demanding tests.
- `scope-keeper` vs. a genuinely necessary adjacent fix (the requested change cannot work without touching neighboring code) → rule must distinguish "required by the change" from "improvement".
- `stopper` under explicit user autonomy ("do whatever it takes") → standing authorization changes the ask/proceed line; the manual must say how.
- `honest-advisor` vs. `stopper`: pushing back on a flawed premise must not become stalling — disagree once with evidence, then either proceed as directed or stop, per the user's call.
- `decomposer` vs. `spec-plan`: on a task already inside the SDD lifecycle, the plan artifact belongs to `spec-plan`; `decomposer` only governs the judgment (skip/depth/risk-first ordering).
- `communicator` in a non-English conversation → rules are language-agnostic; manual must not assume English output.
- Skill name collisions: harness has built-in `verify`; repo has `debugger`, `security-review`, `context-manager`. Names and descriptions must keep each manual distinct enough that auto-loading picks the right one.

## Acceptance criteria

- AC-001: `ls skills/` shows the nine new folders, each containing exactly one `SKILL.md` with frontmatter whose `name` equals the folder name.
- AC-002: Every SKILL.md contains all six skeleton sections; the closing checklist has ≤ 7 items; the file is ≤ ~150 lines.
- AC-003: Every SKILL.md contains a "Contrast" section explicitly comparing intended reasoning vs. generic-model failure, and at least 3 named anti-patterns each with a bad→good example pair.
- AC-004: `profiles.json` `core.skills` includes the nine names, and the repo's CI consistency check (feature 007 script) passes.
- AC-005: README lists the nine skills under a "Mindset skills" grouping with one-line descriptions matching the frontmatter.
- AC-006: A rule-by-rule audit finds zero rules that are pure adjectives with no observable trigger/condition (FR-009).
- AC-007: Each tier-2 manual and `verifier` contain the one-line relationship statement to their complemented skill, and a cross-read against that skill finds no contradiction (FR-008, FR-010).
- AC-008: The `honest-advisor`/`stopper` and `decomposer`/`spec-plan` boundaries are stated explicitly in the respective manuals (edge cases above).

## Test scenarios

- Unit: n/a (documentation).
- Integration: run the feature-007 consistency script → passes with the nine new skills registered.
- E2E: in a fresh session, invoke each of the nine skills by name → each loads and its instructions are followable without reading any other file.
- Manual: dry-run each manual against a canned failure transcript (e.g., a turn ending in "should work now"; a bugfix that adds a bare null-check; a sycophantic "great idea!" reply) and confirm the checklist catches it; verify README rendering.

## Assumptions

- Manuals are written in English, matching every existing skill in `skills/`, even though the user converses in Spanish; the rules themselves are language-agnostic.
- Name mapping from the user's list: "security sweep" → `threat-modeler`, "setup" → `scout`, "planner" → `decomposer`, "bug hunter" → `root-causer`, "honest advisor" → `honest-advisor`. Repo convention is plain kebab-case without the "the-" article (`debugger`, not `the-debugger`).
- All nine belong in the `core` profile because they are stack-agnostic, like `debugger` and `handoff`.
- They live in the repo's `skills/` directory (the framework's source of truth), not `.claude/skills/` — the installer distributes them like every other skill.
- The manuals are standalone and user-invocable; no hook auto-injects them.
- Authoring/priority order: `verifier` → `scope-keeper` → `communicator` → `stopper` (user's stated order), then `honest-advisor`, then tier 2 (`threat-modeler`, `scout`, `decomposer`, `root-causer`). The feature can ship partially in this order if interrupted.

## Open questions

- OQ-001: Should `spec-implement` and `spec-review` gain a one-line pointer to the relevant mindset manuals (e.g., "apply `verifier` before marking a task complete"), or should the manuals stay fully decoupled in this feature? **Status: Deferred** (per D004 — manuals stay decoupled this feature; pointer wiring is a candidate follow-up, reinforced by the QA adoption note that tier-2 manuals compete with their process-skill counterparts for auto-load).
- OQ-002: `honest-advisor` was originally recommended as the highest-impact manual — confirm whether to promote it to first in authoring order. **Status: Resolved** (per D005 — kept the user's stated order; `honest-advisor` authored fifth, all nine shipped so ordering had no delivery impact).
- OQ-003: Are the proposed names for the user's five acceptable (`threat-modeler`, `scout`, `decomposer`, `root-causer`, `honest-advisor`), or does the user prefer keeping their original phrasing as names (e.g., `security-sweep`, `bug-hunter`)? **Status: Resolved** (per D001 — proposed descriptive names adopted; they avoid collision with `security-review`/`debugger` and follow repo convention. Renameable now, breaking after adopters install.)
