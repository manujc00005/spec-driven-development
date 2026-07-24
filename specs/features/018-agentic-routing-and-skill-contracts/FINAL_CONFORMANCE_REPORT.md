# Final Conformance Report

Feature: `specs/features/018-agentic-routing-and-skill-contracts/`
Task: T019 (final closure task)
Method: manual conformance pass applying the `final-conformance-reviewer` agent's own
contract (`agents/final-conformance-reviewer.md`) to this feature, read-only, no code
changes made. No live Claude Code agent-registry dispatch occurred — see "Known
out-of-scope issues."

## Verdict

**PASS** — Ready for PR.

## AC coverage

| AC | Verdict | Evidence | Notes |
|---|---|---|---|
| AC-001 | PASS | `agents/{codebase-researcher,solution-architect,implementer,security-reviewer,domain-reviewer,final-conformance-reviewer}.md` | All six exist with full contracts (responsibility, inputs, outputs, skills consumed, allowed/forbidden, when-to-run). |
| AC-002 | PASS | `TASKS.md` T004–T009 (Phase 2: Implementation) come after T001–T003 (Phase 1: Preparation); `agents/README.md` "How these are installed" | Agents were added during implementation, not before. |
| AC-003 | PASS | Each `agents/*.md` file | Every file follows the same structure: Responsibility / Inputs / Outputs / Skills consumed / Allowed actions / Forbidden actions / When to run. |
| AC-004 | PASS | `ls skills/` = 61 (unchanged count from SPEC's "Current state"); no skill file deleted or moved in commit `9035595`'s diff stat | 61 skills before, 61 after; only `## SDD Contract` blocks and 3 rerouted skill bodies were edited. |
| AC-005 | PASS | `agents/domain-reviewer.md`; `docs/AGENTIC_ROUTING.md` § domain-reviewer; `INVENTORY.md` Skill→Agent matrix; `profiles.json` `agentRouting.domain-reviewer` in 4 of 5 non-core profiles | Documented owner of all 15 domain reviewer skills plus generic bases used for domain review. |
| AC-006 | PASS | `grep -in subagent skills/java-spring-reviewer/SKILL.md skills/spring-boot-api-reviewer/SKILL.md skills/event-driven-reviewer/SKILL.md` → zero matches; each has `primary_agent: domain-reviewer` | External `java-spring`/`api-design` subagent references removed; routing target only was changed (D006). |
| AC-007 | PASS | `check-consistency.sh` PASS (validates every skill's `primary_agent` resolves); direct count: 61/61 `SKILL.md` files contain `## SDD Contract` | — |
| AC-008 | PASS | `profiles.json` `agentRouting` is additive; `skills`/`plannedSkills` arrays unchanged from pre-018 shape; `install.test.sh` (5/5) and `update.test.sh` (7/7) pass | Non-breaking — older installers ignore the unknown `agentRouting` key. |
| AC-009 | PASS | `scripts/check-consistency.sh` lines ~318–487 implement contract-schema validation (Rules 1–3) and `agentRouting` structural + coverage checks (Rules 4–8); `check-consistency.sh` run PASS; `check-consistency.test.sh` 24/24 PASS (includes `missing-shipped-agent`, `orphan-agent` cases) | — |
| AC-010 | PASS | `agents/codebase-researcher.md`; D007; no hook files touched by this feature (confirmed via commit diff stat — `hooks/` absent) | Graphify remains optional; not made mandatory. |
| AC-011 | PASS | Six agent files use standard `name`/`description`/`tools:` frontmatter (no `model:`, by design per `agents/README.md`); `install.ps1`/`install.sh` absent from commit `9035595`'s diff (untouched); `install.test.sh` 5/5 PASS | — |
| AC-012 | PASS | Reviewed all new/changed files — content is generic framework/SDD-lifecycle language, no project-specific or private references | — |
| AC-013 | PASS | Tool grants: `codebase-researcher`, `security-reviewer`, `domain-reviewer`, `final-conformance-reviewer` = `Read, Grep, Glob` only (no Edit/Write/Bash at all); `solution-architect` = adds Edit/Write but Forbidden-actions text confines to `specs/`; `implementer` = only agent with Bash, Forbidden-actions explicitly bar `git commit`/`git push`/`git add .`/secrets/`.env`/`settings.local.json` | Structural (tool grant) + behavioral (Forbidden actions) enforcement, cross-checked in `AGENT_BOUNDARY_WALKTHROUGH.md`. |
| AC-014 | PASS | This report itself; `AGENT_BOUNDARY_WALKTHROUGH.md` item F (prior grounded simulation) | `final-conformance-reviewer`'s contract (`agents/final-conformance-reviewer.md`) was applied for real, against this actual completed feature, producing the verdict below. |
| AC-015 | PASS | `docs/AGENTIC_ROUTING.md` § "Skills vs. agents"; `agents/README.md` § "Skills vs. agents" | — |

## Task coverage

| Task | Status | Evidence |
|---|---|---|
| T001 | Done | `INVENTORY.md` exists, persists Phase 1 matrix |
| T002 | Done | `## SDD Contract` carrier applied (D011) |
| T003 | Done | `CONTRACT_SCHEMA.md` defines the formal schema |
| T004 | Done | `agents/codebase-researcher.md` |
| T005 | Done | `agents/solution-architect.md` |
| T006 | Done | `agents/implementer.md` |
| T007 | Done | `agents/security-reviewer.md` |
| T008 | Done | `agents/domain-reviewer.md` |
| T009 | Done | `agents/final-conformance-reviewer.md` |
| T010 | Done | 61/61 `SKILL.md` files carry `## SDD Contract` |
| T011 | Done | Zero "subagent" references remain in the 3 target skills |
| T012 | Done | `profiles.json` `agentRouting` populated across `core` (`agents` array) + 4 non-core profiles |
| T013 | Done | `agents/README.md` documents all 8 agents (6 lifecycle + 2 model-tier) |
| T014 | Done | `check-consistency.sh` extended (Rules 1–8, lines ~318–487); run confirms PASS |
| T015 | Done | `check-consistency.test.sh` 24/24 PASS; `install.test.sh` 5/5 PASS; `update.test.sh` 7/7 PASS |
| T016 | Done | `AGENT_BOUNDARY_WALKTHROUGH.md` — 8/8 boundary checks PASS |
| T017 | Done | `docs/AGENTIC_ROUTING.md` written |
| T018 | Done | `CHANGELOG.md` `[Unreleased]` entry documents the feature; no project-specific content found |
| T019 | **Done (this pass)** | This report; validations re-run and confirmed green |

No orphan tasks — T001–T019 map sequentially to the four PLAN phases, and every task cites at least one AC. No task is marked done without cited evidence.

## Decision consistency

All D001–D014 are `Accepted`; none `Proposed`/`Deferred`/`Rejected` in a way that blocks implementation.

- **D001–D003:** Skills stay skills; agents are accountable actors; exactly 6 agents shipped. Consistent with `agents/` (6 files) and unchanged `skills/` (61 files).
- **D004 vs. implementation:** No `agents/test-engineer.md` exists (confirmed by directory listing). No contradiction — the `test-engineer` *skill* remains and is consumed per D005's split, which is exactly what's implemented (`solution-architect`, `domain-reviewer`, `final-conformance-reviewer` all list `test-engineer` under skills consumed).
- **D005:** Testing ownership split — verified in all three consuming agents' contracts and in `SPEC.md`'s Test strategy section.
- **D006:** domain-reviewer replaces external subagent coupling — **implemented**, verified by direct grep (zero matches).
- **D007:** Graphify owned by `codebase-researcher`, stays optional — implemented in its contract; no hook changes.
- **D008:** Dedicated `security-reviewer` — exists as a separate file from `domain-reviewer`.
- **D009:** `deep-reasoner`/`fast-worker` unchanged — both files present, untouched by this feature's diff.
- **D010:** `sdd-orchestrate` (and `review-all`/`sdd`/`sdd-medium`/`sdd-full`) remain `orchestration-context`, not dispatched agents — verified via `grep primary_agent` on those five `SKILL.md` files.
- **D011:** `## SDD Contract` YAML block — **implemented and in active use**; `check-consistency.sh` parses it (`SDD_CONTRACT_RE` regex, line 323) and it validated across all 61 skills.
- **D012:** Additive `agentRouting` map — **implemented**; present in `profiles.json` for `java-spring-backend`, `messaging-event-driven`, `payments-fintech`, `next-prisma-web`, `seo-geo-addon`; absent (by design) from `core` and `blockchain-crypto`.
- **D013:** Formal schema (enums, `all` sentinel, side-effect precedence, boolean `provider_specific`) — **implemented**; `check-consistency.sh` enforces required keys, enums, `profile_scope` resolution, and the precedence rule matches `CONTRACT_SCHEMA.md`'s VR1–VR13.
- **D014 (+ addendum):** `agentRouting` coverage rule for non-core/non-disabled profiles — **implemented**; `check-consistency.sh` Rule 7/8 (lines ~479–487) enforces per-profile coverage with an explicit `agentRoutingExempt` escape hatch; `profiles.json` shows the addendum's four additional entries (`api-review`, `backend-review`, `database-review` under `java-spring-backend`; `database-review` under `next-prisma-web`) are present.

No unresolved decision blocks this closure. No contradiction found between D004 and the shipped agent set.

## Implementation evidence

- **Agents (8 total, 6 new + 2 unchanged):** `agents/codebase-researcher.md`, `agents/solution-architect.md`, `agents/implementer.md`, `agents/security-reviewer.md`, `agents/domain-reviewer.md`, `agents/final-conformance-reviewer.md`, `agents/deep-reasoner.md` (unchanged), `agents/fast-worker.md` (unchanged). No `agents/test-engineer.md`.
- **Skill contracts:** 61/61 `SKILL.md` files carry a `## SDD Contract` YAML block (verified by direct grep count, cross-checked by `check-consistency.sh`).
- **Reroute:** `java-spring-reviewer`, `spring-boot-api-reviewer`, `event-driven-reviewer` — zero external-subagent references remain; all three declare `primary_agent: domain-reviewer`.
- **`profiles.json`:** `version` unchanged at `0.4.0` (schema, not release version); `core.agents` lists all 8 agents; `agentRouting` populated additively in 4 non-core profiles per D012/D014.
- **`check-consistency.sh`:** extended with contract-schema validation and `agentRouting` structural/coverage rules (~170 new lines).
- **Docs:** `docs/AGENTIC_ROUTING.md` (new, 236 lines) explains skills vs. agents and the routing model; `agents/README.md` updated to document all 8 agents side by side; `docs/SDD-ORCHESTRATION.md` cross-referenced.
- **`CHANGELOG.md`:** `[Unreleased]` section documents the six agents, the contract rollout, the routing map, the reroute, and honestly notes the agents are "authored and validated... but have not yet been live-installed."

## Validation evidence

| Command | Result |
|---|---|
| `bash scripts/check-consistency.sh` | PASS — "Consistency check passed: profiles.json, disk artifacts, settings wiring, and README counts are aligned." (exit 0) |
| `bash scripts/check-consistency.test.sh` | 24 passed, 0 failed (exit 0) |
| `python3 -m json.tool profiles.json` | Valid JSON (exit 0) |
| `bash scripts/install.test.sh` | 5 passed, 0 failed (exit 0) |
| `bash scripts/update.test.sh` | 7 passed, 0 failed (exit 0) |
| `git status --short` (post-validation) | Clean — no stray files left by test sandboxes |

Environment note: this Windows machine's `python3` on `PATH` resolves to a non-functional Microsoft Store shim; a throwaway wrapper script pointing to the real interpreter (`/c/Python314/python`) was prepended to `PATH` for this session only, to let `check-consistency.sh` run. No repository file was changed to work around this.

`scripts/graphify.test.sh` was **not** rerun, per instruction. No prior "known unrelated failure from `setup-graphify.sh`" classification could be found anywhere in this repo's specs, CHANGELOG, or CONTRIBUTING.md to cite — see "Known out-of-scope issues."

## Known out-of-scope issues

- **`graphify.test.sh` not rerun this pass, and no prior "known unrelated failure" claim could be verified.** The instruction was to skip rerunning it unless the known unrelated failure could be clearly classified; a repo-wide search of `CHANGELOG.md`, `CONTRIBUTING.md`, and all `specs/features/*/` docs found no record of an existing/expected failure in `graphify.test.sh` tied to `setup-graphify.sh`. This feature (018) does not touch Graphify code, hooks, or `setup-graphify.sh` at all (confirmed via the commit's file list), so there is no reason to believe this feature affects that suite either way — but its actual pass/fail state is genuinely unverified in this report.
- **Agents are not live-installed in any Claude Code agent registry.** `agents/*.md` are authored, schema-validated, and confirmed to copy correctly in installer dry-runs (T015, `install.test.sh`), but no `-LinkUserClaude`/`--link-user-claude` or `link-project` run was performed against a real `~/.claude/agents/` or project `.claude/agents/` directory as part of this task. The `Agent` tool's available subagent types in this session do not include any of the six lifecycle agents, confirming they are not currently dispatchable. `AGENT_BOUNDARY_WALKTHROUGH.md` (T016) and this report's own AC-014 verification are both grounded paper simulations against the actual contract files, not live dispatches — consistent with how `CHANGELOG.md` already frames this.

## Risks

- **R-1 (carried from SPEC, Low residual):** Downstream users who relied on the old `java-spring`/`api-design` subagent wording will see a routing-target change on next update. Mitigated: reviewer skill bodies/checklists are untouched; `CHANGELOG.md` documents the change under "Changed."
- **R-2 (Low, informational):** `graphify.test.sh` status is unverified in this pass (see above) — recommend running it before tagging a release, not before this closure.
- **R-3 (Low):** The six lifecycle agents remain unverified against a live Claude Code agent registry. First real install (`-LinkUserClaude` / `link-project`) should be spot-checked before or shortly after release, matching the precedent already set for `deep-reasoner`/`fast-worker` in 0.5.0.

No risk found that blocks this closure.

## Final recommendation

**Ready to commit.** All 15 acceptance criteria PASS, all 19 tasks are complete with cited evidence, all 14 decisions are accepted and consistently implemented, and all requested validations (except the explicitly-skipped `graphify.test.sh`) pass green with a clean working tree afterward.
