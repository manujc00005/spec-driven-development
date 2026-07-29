# Decisions: Skill evidence harness

## Decision log

### D001 - Harness invokes a pluggable runner shim, not a vendored API client

**Date:** 2026-07-28

**Status:** Accepted

**Context:**

SPEC OQ-1, marked blocking for PLAN: what actually runs the model calls in `skill-eval.sh` — the
Claude Code Agent tool via a documented manual invocation, a direct API call requiring a key, or a
provider-agnostic shim? The answer determines whether the harness is runnable under the Codex
adapter and whether CI could ever opt in.

Measured on this machine (2026-07-28): `claude` is installed at 2.1.220 and supports both
`-p/--print` (headless) and `--model`. `codex` is **not** installed.

**Decision:**

`skill-eval.sh` shells out to the command in `$SKILL_EVAL_RUNNER`, which must read a prompt on
stdin and write the response to stdout. The documented default is the Claude Code CLI in headless
mode (`claude -p --model <id>`). When `$SKILL_EVAL_RUNNER` is unset, the script prints both arm
prompts and instructions rather than failing silently or guessing a runner. No SDK is vendored, no
API key is required by the repository, and no network call is made by repository code.

**Reasoning:**

A direct API client would add a key requirement and network code to a repo whose whole install
story is zero-dependency, and would hard-bind the harness to one provider inside a project that
ships a provider-adapter layer and a per-skill `provider_specific` flag. The shim reaches the same
models through a CLI the maintainer already has, and keeps the Codex path open as documentation
rather than as an unverified claim — the same honesty posture `adapters/codex/PARITY.md` already
takes.

**Consequences:**

- The Codex runner ships as documentation only and is **not** claimed to work; `codex` is not
  installed here and no one has run it. It stays unverified until someone does.
- Results depend on the runner's own defaults (system prompt, tools, session settings), so the
  result file must name the model — a result without a model identifier is not evidence (FR-006).
- CI opt-in remains possible later without redesign: a workflow would only need to set
  `$SKILL_EVAL_RUNNER`. It stays out of scope here.

---

### D002 - Check category string is `skill-form` (lowercase)

**Date:** 2026-07-28

**Status:** Accepted

**Context:**

SPEC FR-001 and AC-001/AC-002 name the new check class `[SKILL-FORM]`. Every existing category in
`check-consistency.sh` is lowercase and hyphenated: `shipped-skill`, `planned-drift`,
`orphan-skill`, `hook-parity`, `settings-wiring`, `sdd-contract`, `graphify`.

**Decision:**

Use `skill-form`. The checker's `err()` helper renders it as `[skill-form] <item> — <message>`.
AC-001 and AC-002 are read case-insensitively against this string.

**Reasoning:**

Matching the house convention matters more than matching the SPEC's incidental capitalisation, and
introducing the repo's first upper-case category to satisfy a typo would be the wrong trade.

**Consequences:** Cosmetic mismatch between SPEC text and shipped string; noted here rather than
spending a `/spec-update` cycle on it. Any grep-based assertion in tests must use the lowercase
form.

---

### D003 - The mindset skill set is derived from the SDD Contract, never hardcoded

**Date:** 2026-07-28

**Status:** Accepted

**Context:**

The sweep (T007/T010) and the CONTRIBUTING gate (T008) both need to know which skills are
discipline/mindset skills. `check-consistency.sh` already defines
`CATEGORY_ENUM = {... "mindset" ...}` and every skill declares `category:` in its
`## SDD Contract` block. Nine skills currently declare `mindset`.

**Decision:**

Resolve the set by parsing `category: mindset` from the contract block. Do not hardcode a list in
the harness, the scenarios' index, or `CONTRIBUTING.md`.

**Reasoning:**

Spec 021's FR-004 had to be widened mid-flight precisely because a hardcoded set (one agent
instead of all three write-capable ones) left a gap. The contract field already carries the
information; duplicating it into a second list guarantees drift.

**Consequences:** A tenth mindset skill is covered by the gate the day it lands, and immediately
owes a scenario — which is the intent. The count "9" in the SPEC and PLAN is a measurement dated
2026-07-28, not a constant.

---

### D004 - graphify's extracted reference lives in `skills/graphify/references/`

**Date:** 2026-07-28

**Status:** Accepted

**Context:**

SPEC edge case, left open: extracting `graphify`'s body into sibling files changes the skill's
shipped file set, and FR-010 forbids touching the installer to accommodate it. Verified at
`install.sh:438`: the installer calls `copy_tree_safely "$skill_dir" "$CENTRAL_DIR/skills/$skill_name"`
— it copies the whole skill **directory**, not an enumerated file list. `profiles.json` lists
skill names, not files within a skill.

**Decision:**

Extract per-command sections to `skills/graphify/references/<command>.md`, linked from a table in
`SKILL.md`. No installer change, no `profiles.json` change.

**Reasoning:**

The directory-copy behaviour means siblings ride along for free; this is the same pattern
`skills/using-superpowers/references/` uses in the project analysed as reference, and it matches
this repo's existing `docs/_templates/` and `adapters/codex/prompts/` layout.

**Consequences:** The edge case is closed, not deferred. Skill *count* is unchanged (the checker
counts directories containing `SKILL.md`), so README count markers do not move. A future
`--scope`-style installer that enumerates files would break this and must be checked against it.

---

### D005 - Thresholds are 400 chars / 600 lines, and they are conventions

**Date:** 2026-07-28

**Status:** Accepted

**Context:**

Measured 2026-07-28 on the post-021 tree: descriptions range ~60–524 chars, with exactly two over
400 (`sdd-guardrails` 524, `sdd-orchestrate` 492); bodies range ~100–1.559 lines, with exactly one
over 600 (`graphify`). One further description carries an arrow chain (`graphify`).

**Decision:**

Set the caps at 400 characters and 600 lines. Record them as chosen conventions, not findings.

**Reasoning:**

They bind exactly the four known outliers without forcing churn across the other 58 skills. No
evidence establishes an optimal length; claiming one would be inventing precision.

**Consequences:** T001 re-measures before the caps are fixed. If a spec-021 negative-trigger clause
cannot survive at 400, the threshold rises rather than the clause being deleted — the clause has a
spec behind it, the number does not.

---

### D006 - The lint detects proxies for workflow summaries, not workflow summaries

**Date:** 2026-07-28

**Status:** Accepted

**Context:**

The failure being targeted — a `description` that summarises the workflow gets followed instead of
the skill body — is a judgement call. Regex cannot decide it.

**Decision:**

CI checks three mechanical proxies only: arrow chains, enumerated step sequences, and
three-or-more `then`-chained clauses. The judgement call stays a manual review item, documented in
`evals/README.md`. Likewise, FR-006's "every flagged match was manually read" flag is
author-entered; the script records the claim and cannot verify it.

**Reasoning:**

A lint that claims to detect workflow summaries and misses most of them is worse than one that
claims to detect three specific shapes and does — the first invites "CI passed, therefore the
description is fine."

**Consequences:** False negatives are certain and stated up front. The proxies happen to bind
`graphify` today; a prose-shaped summary with no arrows would pass. This is the honest limit of
the deterministic half, and it is why the behavioural half exists.

---

### D007 - Corrected violation count: five, not four; thresholds unchanged

**Date:** 2026-07-28

**Status:** Accepted

**Context:**

T001 re-measured every skill with a real frontmatter parser (handling quoted, folded and
multi-line YAML) rather than the first-line `awk` used when the SPEC was drafted. Results across
61 skills:

- Descriptions over 400 chars: **three** — `sdd-guardrails` 522, `sdd-orchestrate` 490,
  **`event-driven-reviewer` 418**. FR-002 originally claimed two; `event-driven-reviewer` was
  present in the raw measurement and was not counted when the requirement was written.
- Bodies over 600 lines: one — `graphify`, 1.559 (`wc -l`).
- Lint-proxy hits: one — `graphify` (arrow chain).
- Distribution: descriptions min 86 / median 237 / max 522; bodies min 60 / median 118 / max 1.560.
- Nearest to the caps below them: `privacy-compliance-review` 367 and `graphify` 356 chars; no
  body between 500 and 600 lines.
- 22 descriptions carry a spec-021 negative-trigger clause; the longest is `sdd-orchestrate` at 490.

The 2-char deltas against the SPEC's original figures (524→522, 492→490) are the `awk` parse not
stripping the YAML quotes.

**Decision:**

Correct FR-002 and AC-002 to five violations with the measured figures. Keep both thresholds at
**400 chars / 600 lines** — unchanged.

**Reasoning:**

T001 authorised raising a threshold only if a spec-021 negative-trigger clause could not survive
at 400. Exactly one over-cap description carries such a clause (`sdd-orchestrate`), and it reaches
≤ 400 with the clause intact: roughly 260 of its 490 characters are the workflow summary that
FR-001 targets, so the required cut and the desired cut are the same cut. No clause is at risk, so
no threshold moves. The caps also retain a comfortable margin above the rest of the corpus
(next-highest description 367, no body between 500 and 600).

**Consequences:**

- T004 fixes **three** descriptions, not two; PLAN's impacted-areas table and AC-002's
  `git diff` assertion are updated to match.
- The correction was made in place during implementation rather than through `/spec-update`: it
  restates a measurement the SPEC itself dates and scopes, and adds no behaviour. Flagged in the
  T001 report so the maintainer can formalise it if preferred.
- **T003 must define its line-counting rule explicitly.** `wc -l` reports 1.559 for `graphify`
  while a `split("\n")` count reports 1.560; at the 600 boundary that off-by-one decides a
  verdict. The lint and its tests must use one stated convention.

---

### D008 - The length cap and the summary proxies serve different purposes

**Date:** 2026-07-28

**Status:** Accepted

**Context:**

T001 surfaced two facts that pull apart what the SPEC's problem statement had merged:

1. `sdd-orchestrate`'s description is a textbook workflow summary — "classify the task … delegate
   … then review, validate … and keep SPEC/PLAN/TASKS/DECISIONS in sync" — and **no proxy detects
   it**: one `then`, no arrows, no enumerated steps. Only the length cap catches it.
2. `event-driven-reviewer` (418) is **not** a workflow summary. Its length is an enumeration of
   review topics — legitimate keyword coverage for discovery — yet the cap binds it.

**Decision:**

Treat the two rules as serving distinct, separately-justified purposes, and document it in
`evals/README.md` (T002):

- **The length cap enforces context economy** — every description loads at session start, so it
  is a standing per-session cost. It applies uniformly, whatever the text is doing.
- **The proxies target the workflow-summary failure** — the evidence-backed one — and are weak by
  construction (D006).

**Reasoning:**

Conflating them invites two opposite errors: reading a cap violation as an accusation of
workflow-summarising (unfair to `event-driven-reviewer`), and reading proxy-clean as evidence a
description is well-formed (false for `sdd-orchestrate`). Naming the purposes separately makes
both violations defensible on their own terms.

**Consequences:**

- `event-driven-reviewer` is trimmed on context-economy grounds, and T004 must not claim it was a
  workflow summary. Some keyword coverage is lost; that is the cost of the budget.
- Fixing `sdd-orchestrate` is the clearest available demonstration that the deterministic half
  cannot stand alone — a point the behavioural half (T010) exists to cover.

---

### D009 - The runner executes in an empty sandbox, never in the repo

**Date:** 2026-07-29

**Status:** Accepted

**Context:**

The first full T010 sweep produced nine result files that were all invalid, and the tallies looked
plausible enough to have been believed. A CLI runner inherits its working directory, so
`claude -p` executed **inside this repository**: it read the real filesystem and this project's
`CLAUDE.md`, and answered about *this project* rather than the scenario. The `scope-keeper`
control arm, scored 5/5 "failure exhibited", actually read:

> "The file `src/utils/format.ts` doesn't exist in this repo — this appears to be a hypothetical
> scenario, not the actual `spec-driven-development` codebase, which is a docs/skills framework
> rather than a TypeScript application. Do you want me to create it…?"

Every "hit" was the word `formatDate` appearing inside a clarifying question. The failure under
test never occurred in either arm.

**Decision:**

`skill-eval.sh` runs the runner inside an empty scratch directory
(`( cd "$SANDBOX" && eval "$RUNNER" )`), created per invocation and destroyed with the rest of the
work directory. The first sweep's results are discarded and re-run.

**Reasoning:**

A scenario is a claim about behaviour in a described situation. If the runner can see a real,
different situation, it will reasonably answer about that one instead — and the scenario measures
nothing. Isolation is what makes the scenario the only context the model has.

**Consequences:**

- Verified after the fix: zero references to this repository in a re-run response.
- **Residual contamination remains and is not fixed here.** A user-level config (for Claude Code,
  `~/.claude/CLAUDE.md`) still loads, so results carry whatever standing instructions the operator
  has. The result file records the runner command verbatim, but cannot capture the operator's
  global config. Two runs on different machines are therefore not strictly comparable — stated in
  `evals/README.md` rather than solved.
- This is the first finding the harness produced about *itself*, and it argues for the feature:
  the tallies were confidently wrong, and only reading the responses caught it.
