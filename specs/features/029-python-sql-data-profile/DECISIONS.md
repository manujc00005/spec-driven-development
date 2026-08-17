<!-- See skills/sdd-guardrails/SKILL.md, section 1, for the full decision state machine (Proposed / Accepted / Superseded / Rejected / Deferred). -->

# Decisions: python-sql-data-profile

## Decision log

### D001 - Five separate skills, not one combined reviewer

**Date:** 2026-08-17

**Status:** Accepted

**Context:** The feature could ship as a single `python-sql-reviewer` covering everything, or as
several narrower skills.

**Decision:** Five skills — `python-reviewer`, `sql-query-reviewer`,
`database-performance-reviewer`, `data-pipeline-reviewer`, `python-testing-reviewer`.

**Reasoning:** They have different triggers and different answers. A `.sql` change does not need
the pytest checklist; a test-only change does not need the index checklist; a scheduled-job change
needs the idempotency questions and little else. A combined skill would load whole for every
one-line change, which is exactly the context cost the framework's token-economy principle exists
to avoid. The split also mirrors the review ordering that matters: correctness before cost.

**Consequences:** Five files to maintain instead of one, and five descriptions loading at session
start (each under the 400-char cap). A change touching Python, SQL and a load process runs three
reviews — acceptable, and `/review-all` collects them.

---

### D002 - `security-reviewer` is a secondary agent in the SDD Contract, not a second `agentRouting` target

**Date:** 2026-08-17

**Status:** Accepted

**Context:** Three of the five skills surface security findings: string-interpolated SQL,
credentials in source, personal data in logs and extracts, over-privileged database accounts. The
feature request asked for `security-reviewer` to appear as a second `agentRouting` target listing
`sql-query-reviewer` and `data-pipeline-reviewer` — **if the schema permits a skill in more than
one routing target**.

Mechanically, it does. `check-consistency.sh` collects routed skills into a set
([check-consistency.sh:466-476](../../../scripts/check-consistency.sh:466)) and enforces no
uniqueness rule, so dual-listing would pass CI.

**Decision:** List all five skills under `domain-reviewer` only, and record the secondary
`security-reviewer` consumption in each skill's `secondary_agents` plus a `note` on the routing
entry.

**Reasoning:** Passing the checker is not the test — the semantics are. `README.md` describes
`agentRouting` as "which of its reviewer skills `domain-reviewer` or `security-reviewer` **own**
for that stack", and every shipped profile follows that reading: `next-prisma-web` lists
`nextjs-server-actions-reviewer` under `security-reviewer` **because its contract names
`security-reviewer` as primary**. Dual-listing a skill whose contract says
`primary_agent: domain-reviewer` would assert two owners and contradict the contract it is routed
from. Both precedents for this exact case — `payments-fintech` and `delivery-operations`, whose
reviewers are also `domain-reviewer`-primary with `security-reviewer` secondary — use the note
form. This feature is not the right place to invent a second convention.

**Consequences:** The routing map stays single-owner and the framework keeps one meaning for a
routing entry. The secondary relationship is discoverable in two places (the contract and the
note) rather than in the routing map. If dual-target routing is ever wanted, it should be a
deliberate framework change with a checker rule behind it, not a side effect of one profile.

---

### D003 - Engine-agnostic SQL review, with the engine stated as an assumption

**Date:** 2026-08-17

**Status:** Accepted

**Context:** Several SQL checks depend on engine behaviour: `NULL` ordering, `GROUP BY` strictness,
CTE materialization, window frame defaults, upsert syntax, identifier quoting. The profile must not
assume a specific database.

**Decision:** `sql-query-reviewer` reviews generic relational SQL. Where a finding depends on
engine behaviour it must name the engine it assumed and mark it an assumption, and where the diff
does not state the engine it asks rather than ruling.

**Reasoning:** The alternative is silent vendor assumption, which produces confident findings that
are wrong on the project's actual database — worse than no finding, because a wrong finding costs
the reader time and credibility. Most correctness checks that matter (fan-out, `NOT IN` with
`NULL`, `LEFT JOIN` predicates in `WHERE`, half-open date ranges) are engine-independent anyway.

**Consequences:** Some findings are deferred pending an answer. The review output carries an
"engine assumed" line so the reader knows what the verdict rests on.

---

### D004 - Cost findings are labelled structural or conditional

**Date:** 2026-08-17

**Status:** Accepted

**Context:** `database-performance-reviewer` has no query plan, no table statistics and no row
counts. It reads text.

**Decision:** Every finding is labelled **structural** (true from the text alone — a query in a
loop, an unbounded result set, a transaction spanning a network call) or **conditional** (depends
on volume and distribution). Conditional findings are phrased as "run `EXPLAIN` and check X",
never as "this will be slow".

**Reasoning:** A reviewer that asserts a plan it has not seen is guessing with authority, and the
guesses are indistinguishable from the findings that are actually certain. Separating the two makes
the certain ones trustworthy and turns the uncertain ones into a concrete next action instead of a
vague warning. It also keeps the skill honest about the boundary with `EXPLAIN`, which it does not
replace.

**Consequences:** The output format carries a "Kind" column and a "Run `EXPLAIN` on" section.
Reviews will conclude with open items more often than a tool would — which is accurate.

---

### D005 - No new logic in `check-consistency.sh`

**Date:** 2026-08-17

**Status:** Accepted

**Context:** AC-009 requires the checker to validate that the new skills exist and are correctly
referenced.

**Decision:** Change nothing in `scripts/check-consistency.sh`.

**Reasoning:** Every rule AC-009 asks for already exists and is generic over all profiles:
shipped-skill existence (FR-001, [check-consistency.sh:135](../../../scripts/check-consistency.sh:135)),
routing target must be a lifecycle agent (rule 6, line 469), routed skill must exist on disk
(rule 5, line 476), every non-core profile skill must be covered by `agentRouting` (rule 7, line
485), and `## SDD Contract` validity including the `primary_agent`/`secondary_agents` enums and
`profile_scope` resolution (rules 1-3, lines 383-435). Adding a `python-sql-data`-specific check
would duplicate that logic and give the new profile a privilege no other profile has. The
verification that this holds is empirical, not theoretical: the checker failed on this change
until the manifest and README were correct.

**Consequences:** The profile is validated by the same rules as every other profile, and a future
profile inherits the same coverage for free. Nothing here is protected by a bespoke check, which
is the intended design.

---

### D006 - Reviewer skills ship without a behavioural eval

**Date:** 2026-08-17

**Status:** Accepted

**Context:** Spec 022 built `evals/` and spec 024 refused to ship `rightsizing-advisor` because its
eval returned NO-BASELINE-FAILURE. That raises the question of whether these five need evals.

**Decision:** Ship without evals, and record the unproven-value question as an open question
instead.

**Reasoning:** The eval harness targets **mindset and discipline skills** — `communicator`,
`scope-keeper`, `verifier`, `stopper` and the rest — where the claim is "this skill changes what
the model does" and a control arm is meaningful. These five are reviewer checklists, the same class
as `container-review`, `pipeline-review` and every other shipped domain reviewer, none of which
carries an eval. Inventing an eval requirement for reviewers here would be a framework-wide policy
change smuggled in through one profile.

**Consequences:** Value is asserted by construction, not measured. OQ-2 records that the skills
have not run against a real Python + SQL diff, and the first real use should be treated as a
calibration pass rather than a validation.

---

### D007 - Spec numbered 029, not 025

**Date:** 2026-08-17

**Status:** Accepted

**Context:** The feature was requested as `specs/features/025-python-sql-data-profile/`. That
number is already taken by `025-workspace-sdd-graphify-onboarding`, and 026, 027 and 028 exist too.

**Decision:** `specs/features/029-python-sql-data-profile/`.

**Reasoning:** Reusing 025 would collide with a spec that CI, CHANGELOG and
`check-consistency.sh` comments already reference by number. `git fetch --all` was run before
claiming 029, and the remote carries only `main` — so 029 is free on both sides, not merely free
locally.

**Consequences:** Every reference to this feature — the profile `note`, the CHANGELOG, the skills'
provenance — says 029.

---

### D008 - Not ported to the Codex adapter, recorded as an honest gap

**Date:** 2026-08-17

**Status:** Accepted

**Context:** The framework's standing position is that Codex is first-class and a feature should
not be scoped Claude-Code-only without saying so.

**Decision:** Do not port the five skills to `adapters/codex/`. Add a row to
`adapters/codex/PARITY.md` stating the gap explicitly, alongside the existing rows for the other
stack-specific reviewer families.

**Reasoning:** The Codex adapter ships a curated 7-prompt lifecycle spine (spec 019 D004) and no
stack-specific reviewer — Java/Spring, payments, event-driven, Next/Prisma, SEO/GEO and
delivery/operations are all unported. Porting only this family would be inconsistent, and the
`codex` CLI is still not installed in this environment (spec 019 OQ-1, still open), so any prompt
written for it would ship unverified. An honest gap row is worth more than an unverifiable prompt.

**Consequences:** A Codex user gets the SDD lifecycle but not these reviews, and the parity matrix
says so. Porting stays a tracked follow-up alongside the rest of the reviewer catalogue.

---

### D009 - Stale hardcoded skill counts corrected in passing

**Date:** 2026-08-17

**Status:** Accepted

**Context:** `adapters/codex/PARITY.md`, `adapters/README.md`, `adapters/claude/README.md`,
`adapters/codex/prompts/README.md`, `docs/AGENTIC_ROUTING.md` and one `README.md` directory comment
each hardcode "65 skills". The repository held 66 before this change and 71 after — so five of the
six were **already wrong** before this feature, because `check-consistency.sh` only guards the
`<!-- count: -->` markers and shields badges in `README.md`.

**Decision:** Update all six to 71.

**Reasoning:** Leaving a count that this change makes more wrong is not a defensible scope
boundary. The edit is mechanical and the pre-existing drift is disclosed rather than quietly
absorbed.

**Consequences:** Six one-token edits outside the feature's core scope. The underlying gap — these
counts are unguarded and will drift again — is a real finding this feature does not fix; it belongs
in `docs/KNOWN_DEBT.md` or a checker rule extension, and is reported rather than silently patched.
