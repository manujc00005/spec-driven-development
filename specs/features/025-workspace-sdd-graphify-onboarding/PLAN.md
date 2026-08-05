# Plan: Workspace SDD — Graphify-aware multi-project onboarding

## Summary

Add a workspace layer above per-project SDD, delivered as **prose artifacts plus two consistency
checks** — no orchestration code, no installer change, no agent.

Four deliverable groups:

1. **Doctrine** — `docs/WORKSPACE_SDD.md`: what a workspace is, why the layer exists, the folder
   contract, the token order, per-project Graphify usage, the cross-project workflow, the
   guardrails.
2. **Templates** — ten files under `docs/_templates/workspace/` that the flow instantiates into a
   user's `.sdd-workspace/`.
3. **Executable flow** — `skills/sdd-workspace-onboarding/SKILL.md` (Claude Code) and
   `adapters/codex/prompts/sdd-workspace-onboarding.md` (prompt-based Codex counterpart).
4. **Enforcement** — new `workspace` check class in `scripts/check-consistency.sh` plus cases in
   `scripts/check-consistency.test.sh`, so the layer cannot silently rot and no future edit can
   introduce a "Graphify is required" or "load graph.json" claim.

## Related spec

`specs/features/025-workspace-sdd-graphify-onboarding/SPEC.md`

## Impacted areas

| Area | Change | Risk |
|---|---|---|
| `docs/WORKSPACE_SDD.md` | New file | None — additive |
| `docs/_templates/workspace/*.md` (10) | New files in a **subdirectory** | Low — the orphan-template check enumerates only top-level files in `docs/_templates/`, so a subdirectory adds no `templates-total` drift |
| `skills/sdd-workspace-onboarding/SKILL.md` | New skill | Medium — must carry a valid `## SDD Contract`, stay under the 400-char / 600-line caps, and be registered in `profiles.json` or CI fails with `orphan-skill` |
| `profiles.json` | One string appended to `core.skills` | Medium — see D012; shifts `skills-total` 65→66 and `core-skills` 41→42 |
| `README.md` | New "Workspace SDD" section, TOC entry, count markers + badge | Low — markers/badge auto-fixed by `check-consistency.sh --fix` |
| `docs/AGENTIC_ROUTING.md` | One paragraph on `codebase-researcher` workspace mode | Low |
| `adapters/codex/prompts/` | New prompt + README table row | Low |
| `CHANGELOG.md` | Unreleased entries | None |
| `scripts/check-consistency.sh` | New `workspace` check class | **Highest risk in this plan** — a claim-detection regex that false-positives blocks CI on existing correct prose |
| `scripts/check-consistency.test.sh` | Four new cases + one negative case | Low |

**Explicitly out of bounds:** `install.sh`, `install.ps1`, `install-all.*`, `hooks/**`,
`settings.template*.json`, `agents/**`, `link-project.*`, every child project's application code.

## Proposed approach

### 1. Doctrine first (`docs/WORKSPACE_SDD.md`)

Written before the skill, because the skill is a procedure and the doc is the reason. Anchored on
one sentence used verbatim in both:

> Graphify maps code-level dependencies. Workspace SDD maps project-level dependencies.

The token-saving section states the reading order as a hard ladder — workspace docs, then
per-project graph reports, then manifests/README/API descriptors, then a bounded reading list, then
concrete files — with "never load `graph.json`" as the standing exclusion at every rung.

### 2. Templates as the contract shape

Each template is the *shape* of an answer, not an example filled with a fictional system. Two
carry enforcement semantics rather than free prose:

- `DEPENDENCY_GRAPH.md` — every relationship block requires `Evidence` and `Confidence`, and the
  confidence vocabulary is closed: `Confirmed` / `Inferred - requires confirmation` /
  `Unknown - requires confirmation`. This is what makes "no invented dependencies" checkable by a
  human reader rather than merely asserted.
- `IMPACT_MAP.md` — carries an **unaffected projects** list, not just an affected one. Naming what
  is out of scope is what turns the map into a boundary an agent can be held to.

### 3. Skill and Codex prompt as one procedure, two packagings

The skill is the source; the Codex prompt is derived from it, exactly as the existing seven
lifecycle prompts derive from their skills. The Codex file makes no native-subagent claim and
sets no global configuration, consistent with `adapters/codex/PARITY.md`.

Contract choice for the skill, mirroring `sdd-onboard` (the closest existing analogue — an
onboarding flow that reads code and writes only documentation):

```yaml
category: lifecycle
side_effects: writes-specs
primary_agent: codebase-researcher
secondary_agents: [solution-architect]
profile_scope: all
provider_specific: false
```

### 4. Enforcement, designed against false positives

Two check families:

**Existence** — straightforward: the doc, the skill, the ten templates, and (conditionally on
`adapters/codex/` existing) the Codex prompt.

**Claims** — the risky one. A naive `grep -i "graph.json"` fires on
`docs/AGENTIC_ROUTING.md`'s existing, *correct* line: "`graph.json` should not be loaded wholesale
into context". Blocking CI on prose that says the right thing is worse than the drift being
guarded against.

The design is therefore **sentence-scoped with negator awareness**: split each scanned document
into sentences, match a narrow set of affirmative claim patterns, and suppress a match when the
same sentence carries a negator (`not`, `never`, `no`, `n't`, `without`, `avoid`, `defeats`,
`rather than`, `instead of`, `optional`). Documented in-script as a heuristic that accepts false
negatives to avoid false positives — the same trade-off spec 022 made for the skill-form proxies.

Scan scope is deliberately narrow: `README.md`, `docs/**/*.md`, `skills/**/SKILL.md`,
`adapters/**/*.md`, `CHANGELOG.md`. Not `specs/**` — a spec must be able to quote a forbidden claim
while forbidding it (this very PLAN does).

## Alternatives considered

| Alternative | Why rejected |
|---|---|
| **One merged workspace Graphify graph** | Defeats the purpose: a super-graph over six repos is larger than any one report and cannot be loaded bounded. Per-project reports compose; a merged graph does not (D002). |
| **Make `.sdd-workspace/` a git-tracked repo of its own** | Adds a repository to manage and a sync problem, for a layer whose whole value is being *next to* the projects. Left as OQ-1. |
| **A dedicated `workspace-researcher` agent now** | Agents are accountability boundaries; adding one before the flow has been used once would encode a guess. `codebase-researcher` already owns bounded research and only needs a documented workspace mode (D013). |
| **Enforce claims with a plain `grep -RniE` in CI** | Fires on correct negated prose already in the tree (verified against `docs/AGENTIC_ROUTING.md:211`). Rejected in favour of sentence-scoped detection. |
| **Skip `profiles.json` as instructed** | `check-consistency.sh` hard-fails with `orphan-skill` for any undeclared `skills/*/SKILL.md`; there is no exemption flag. AC-018 and the instruction are mutually exclusive. Resolved with the user in favour of registration (D012). |
| **Number the spec `024` as requested** | `024` was already in use by the delivery-operations feature. Confirmed with the user; renumbered to `025` (D011). |

## Dependencies

- Spec 010 (`.graphify/GRAPH_REPORT.md` as the canonical path) — this feature consumes that
  contract and must not re-litigate it.
- Spec 018 (`## SDD Contract` schema, `agentRouting`) — the new skill must satisfy the schema; the
  `core` profile's exemption from routing coverage is what keeps the registration to one line.
- Spec 019 (`adapters/codex/`) — the Codex prompt follows that adapter's honesty posture.
- Spec 022 (skill-form caps) — 400-char description, 600-line body.
- No external tool dependency. Graphify is optional by construction.

## Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| **Claim-detection regex false-positives on existing prose** | Medium | High (blocks CI) | Sentence-scoped negator suppression; a dedicated test case (TS-7) asserts the existing `AGENTIC_ROUTING.md` line stays clean |
| Registering the skill drifts README counts | High | Low | `check-consistency.sh --fix` updates markers and badge mechanically |
| Templates in a subdirectory trip the orphan-template check | Low | Medium | Verified: `collect_templates()` enumerates files only, so `docs/_templates/workspace/` is invisible to it. Asserted by running the checker after creation |
| The workspace layer is documented but never used, and rots | Medium | Medium | Enforcement makes rot visible; OQ-1/OQ-2 leave the adoption path open rather than pretending it is settled |
| Doc set implies more capability than shipped | Medium | Medium | Every artifact states this is a design/documentation phase; no orchestration code is claimed |

## Test strategy

No unit-testable product code ships, so verification is structural and adversarial:

1. **Structural** — `bash scripts/check-consistency.sh` exits 0 on the finished tree.
2. **Manifest validity** — `python3 -m json.tool profiles.json` succeeds.
3. **Self-test** — `bash scripts/check-consistency.test.sh` reports 0 failures, including the four
   new failure cases (TS-2..TS-5, TS-6) and the negative case (TS-7).
4. **Adversarial claim sweep** — the `grep -RniE` sweep from the brief, run across README, docs,
   skills, adapters, the spec folder and CHANGELOG, with every hit classified
   *real issue / safe documentation / false positive* and only real issues fixed.

## Rollback strategy

Every change is additive except three edits (`profiles.json` one line, `README.md` section +
counts, `docs/AGENTIC_ROUTING.md` one paragraph, `CHANGELOG.md`, and the two scripts). Rollback is:

1. Delete `docs/WORKSPACE_SDD.md`, `docs/_templates/workspace/`,
   `skills/sdd-workspace-onboarding/`, `adapters/codex/prompts/sdd-workspace-onboarding.md`,
   `specs/features/025-workspace-sdd-graphify-onboarding/`.
2. Revert the `core.skills` entry and re-run `check-consistency.sh --fix` to restore counts.
3. Revert the `workspace` check block in the two scripts.

Nothing is installed, wired or migrated, so there is no runtime state to unwind.

## PLAN verification checklist

- [x] Every FR in SPEC maps to at least one task in `TASKS.md`
- [x] Every AC maps to a task or a validation step
- [x] Out-of-bounds files enumerated (installers, hooks, settings templates, agents)
- [x] The `profiles.json` conflict is recorded as a decision, not silently resolved (D012)
- [x] The spec renumbering is recorded as a decision (D011)
- [x] The highest-risk change (claim detection) has an explicit false-positive mitigation and a
      dedicated negative test
- [x] No commit, push or staging step appears anywhere in this plan
