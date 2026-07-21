# Implementation Plan: mindset-skills

## Summary

Add nine "mindset" skill manuals under `skills/` — five new-ground (`verifier`, `scope-keeper`, `communicator`, `stopper`, `honest-advisor`) and four that layer a reasoning stance over an existing process skill (`threat-modeler`→`security-review`, `scout`→`sdd-onboard`/`context-manager`, `decomposer`→`spec-plan`, `root-causer`→`debugger`). Each is a single `SKILL.md` following one shared skeleton (thesis → Triggers → Rules → named Anti-patterns → Contrast → Closing checklist). Register all nine in the `core` profile and reconcile every count/claim in `README.md` so the feature-007 consistency check stays green.

## Related spec

`specs/features/013-mindset-skills/SPEC.md`

## Impacted areas

- `skills/verifier/`, `skills/scope-keeper/`, `skills/communicator/`, `skills/stopper/`, `skills/honest-advisor/`, `skills/threat-modeler/`, `skills/scout/`, `skills/decomposer/`, `skills/root-causer/` — new folders, one `SKILL.md` each.
- `profiles.json` — `core.skills` array gains the nine names (31 → 40).
- `README.md` — new "Mindset skills" grouping in the skill listing; count markers `skills-total` (43 → 52) and `core-skills` (31 → 40); non-marker prose that also states 43 (badge line 15, feature paragraph "all 43 of them" line 192, tree comment line 282, "(43 skills)" line 510).
- No application code, no hooks, no agents, no templates, no settings wiring.

## Proposed approach

1. **Author `verifier` first as the canonical skeleton** (T001). It fixes the exact section order, heading names, the Rules format (behavior + observable trigger), the bad→good anti-pattern format, the Contrast two-column framing, and the ≤7-item checklist. Every later manual is a structural copy with its own content, so getting this one right is the highest-leverage step.
2. **Replicate for the other four tier-1 manuals** (T002–T005), each covering at least its normative rule/anti-pattern set from the spec. `honest-advisor` additionally states the `honest-advisor`↔`stopper` boundary (AC-008).
3. **Author the four tier-2 manuals** (T006–T009). Each opens with the one-line relationship to the process skill it complements (FR-008) and duplicates none of that skill's procedure. `decomposer` states the `decomposer`↔`spec-plan` boundary (AC-008).
4. **Register + reconcile** (T010–T011): add the nine to `profiles.json core.skills`, then update README grouping, count markers, and stale prose in one pass.
5. **Verify + audit** (T012–T013): run `scripts/check-consistency.sh` until green; then a rule-by-rule cross-read for FR-009 (no personality prose) and FR-010 (no contradictions between manuals or with complemented skills).

Writing order follows the user's stated priority (verifier → scope-keeper → communicator → stopper → honest-advisor → tier 2) so the feature degrades gracefully if interrupted: the highest-impact manuals ship first.

## Alternatives considered

- **One combined "mindset" skill instead of nine** — rejected: the spec requires nine independently invocable slash commands (`/verifier`, …) and per-manual auto-load descriptions; a monolith can't be triggered granularly and would blow the ≤150-line budget.
- **Put them in a new dedicated profile (e.g. `mindset`)** — rejected: they are stack-agnostic like `debugger`/`handoff`; `core` (always installed) is where the spec places them, and a separate profile would leave them uninstalled by default.
- **Fold tier-2 mindset content into the existing process skills** (e.g. add attacker-mindset prose to `security-review`) — rejected by non-goals: existing skills must not be modified beyond an optional pointer; mixing "how to think" into "what steps to run" dilutes both.
- **Rename the user's five to their original phrases** (`security-sweep`, `bug-hunter`, …) — rejected: descriptive kebab names avoid collision with `security-review`/`debugger` and match repo convention (no "the-" prefix). See D001.

## Dependencies

- None external. All edits are Markdown + one JSON array. `python3` (already required by the installer and the consistency checker) must be present to run T012.

## Risks

- **Personality-prose creep (primary risk).** The whole value proposition is actionable rules, not vibes. A manual that says "be rigorous" fails FR-009/AC-006. Mitigation: the T013 audit reads every rule and rejects any without an observable trigger or checkable condition; `verifier` sets the format bar in T001.
- **Inter-manual contradiction.** `stopper` ("proceed on reversible actions") vs `honest-advisor` ("push back first"); `decomposer` vs `spec-plan` ownership of the plan artifact. Mitigation: both boundaries are written explicitly into the manuals (AC-008) and checked in T013 (FR-010).
- **Silent doc drift.** The consistency checker only enforces `<!-- count -->` markers; the badge, "all 43 of them", the tree comment and "(43 skills)" are plain prose it won't catch. Mitigation: T011 updates all of them by grep, not just the two markers.
- **Name collision with built-in `verify`.** `verifier` must stay distinct in name and description so auto-load picks the right one. Mitigation: distinct name + the FR-008 one-line relationship statement.

## Test strategy

- **Integration:** `bash scripts/check-consistency.sh` exits 0 with the nine skills registered and README counts updated (AC-004).
- **E2E (manual):** in a fresh session, each of the nine loads by name and is followable without reading any other file (AC-002, spec E2E scenario).
- **Manual dry-run:** run each manual's checklist against a canned failure transcript (turn ending in "should work now"; bugfix adding a bare null-check; sycophantic "great idea!") and confirm the checklist catches it.
- **Audit (T013):** rule-by-rule pass for FR-009; cross-read tier-2 manuals against their complemented skills for FR-010/AC-007; confirm the two boundary statements for AC-008.
- No unit tests — documentation only.

## Rollback strategy

Pure additive change to docs/manifest. To revert: delete the nine `skills/<name>/` folders, remove the nine names from `profiles.json core.skills`, and restore the README counts/prose (43, 31). `git revert` of the feature commit does all of this atomically; the consistency check confirms the revert is clean.

## PLAN verification checklist

- [x] The plan covers all acceptance criteria. (AC-001→T001-T009; AC-002/003→T001-T009+T013; AC-004→T010-T012; AC-005→T011; AC-006→T013; AC-007→T006-T009+T013; AC-008→T005/T008+T013)
- [x] The plan avoids behavior outside the spec. (no code/hooks/agents; existing skills untouched)
- [x] Risks are documented.
- [x] Test strategy is documented.
- [x] Rollback strategy is documented.
- [x] SPEC.md status has been updated to `Ready`.
