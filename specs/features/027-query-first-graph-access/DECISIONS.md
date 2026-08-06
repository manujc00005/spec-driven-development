# Decisions: Query-first graph access

## Decision log

### D001 — The scoped query is the default; reading `GRAPH_REPORT.md` is the exception

**Date:** 2026-08-06 · **Status:** Accepted

**Context:** Every Graphify-aware artifact said "check the report first" and named the CLI's scoped
queries as an optional refinement. Nobody had measured the two paths.

Measured on `lead-platform` (1.650 nodes, 5.242 edges, `graph.json` 3,2 MB), CLI 0.17.1:
`graphify summary` = 354 tokens; `review-analysis <file>` = 222–262; `review-context <file>` =
103–1.057; the full report = 7.101; `graph.json` = 859.376.

**Decision:** Invert it. `summary` → per-file queries → targeted traversal → report → never
`graph.json`. Reading the report in full is a documented exception with a stated condition.

**Reasoning:** Orientation via `summary` is **20× cheaper** than the report, and the gap compounds:
across the measured four-project workspace, reports total 18.269 tokens against ~1.400 for four
`summary` calls. The scoped commands read `graph.json` inside the CLI process, so the model never
pays for it. Keeping the expensive path as the default contradicted `docs/TOKEN_ECONOMY.md` in the
one mechanism built to serve it.

**Consequences:** Six artifacts state the same ladder. The report keeps a real role — genuinely
global questions, and every case where the CLI is unavailable.

---

### D002 — `codebase-researcher` gets a request protocol, not the ladder

**Date:** 2026-08-06 · **Status:** Accepted

**Context:** The agent declares `tools: Read, Grep, Glob`. It has no Bash tool, by design (spec
018) — its read-only guarantee is structural, not behavioural. It **cannot** run `graphify summary`.

**Decision:** Its contract states the ladder as context but gives it a different rule: name the
exact command the orchestrating session should run, and hand back. It must not fall through to
reading the report as a silent default.

**Reasoning:** Writing "run the query first" into a contract for an agent that cannot run anything
would produce an instruction violated on every invocation — actively worse than report-first,
because it teaches the agent its own contract is advisory. The agent already has exactly this
protocol for graph *generation*; this extends it to graph *querying*.

**Consequences:** Two audiences, two rules, one ladder. Granting the agent Bash was rejected: its
isolation is worth more than the tokens.

---

### D003 — Enforcement asserts presence of the commands, not their order

**Date:** 2026-08-06 · **Status:** Accepted

**Context:** The strongest possible check would verify `summary` appears before `GRAPH_REPORT.md` in
each doctrine file.

**Decision:** `check-consistency.sh` asserts only that each artifact names the scoped-query
commands. Order is not checked.

**Reasoning:** Prose ordering is brittle to match — a heading, a table or a quoted counter-example
flips the result — and a false positive blocks CI on correct text. Same trade-off spec 022 D006 took
for the skill-form proxies and spec 025 D014 took for the claim guard: accept false negatives to
avoid false positives. Presence still catches the realistic regression, which is an edit dropping
the commands entirely.

**Consequences:** A file could name the commands and still describe them last. Recorded as OQ-1.

---

### D004 — The measurement lives in the SPEC, not in `evals/`

**Date:** 2026-08-06 · **Status:** Accepted

**Context:** This repo has a measurement culture (spec 022) and an `evals/` harness that killed a
skill on evidence (spec 024's `rightsizing-advisor`). The obvious move is to file this measurement
there.

**Decision:** Record it in `SPEC.md` with project, date, graph size and per-command output.

**Reasoning:** `evals/` measures whether a skill changes **model behaviour**, using a control arm
and repeated model calls. This is the **output size of a CLI** — deterministic, no model involved,
no control arm meaningful. Filing it under `evals/results/` would misrepresent what was measured and
dilute what that directory means. `docs/TOKEN_ECONOMY.md` refuses telemetry; a one-off measurement
with its method stated is evidence, not a meter.

**Consequences:** Re-measuring is a manual act, tracked as OQ-2. The SPEC states the method so the
numbers can be reproduced rather than believed.

---

### D005 — Graphify stays optional, and the ladder says so at every rung

**Date:** 2026-08-06 · **Status:** Accepted

**Context:** Promoting a CLI command to "the default first step" is exactly how an optional tool
becomes a de facto requirement.

**Decision:** Every statement of the ladder carries the condition **"CLI absent → the report is
rung 1; both absent → `Grep`/`Glob`, and say the context is partial."**

**Reasoning:** Spec 025 D006 and the README's standing claim both hold that Graphify never blocks.
An ordering change must not quietly repeal that. The existing `workspace-claim` guard in
`check-consistency.sh` still runs over these files and would fail on a "Graphify is required" claim.

**Consequences:** The ladder is slightly longer everywhere it appears. Worth it.
