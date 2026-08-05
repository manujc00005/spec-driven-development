# Tasks: Workspace SDD — Graphify-aware multi-project onboarding

Every task states the files it may touch. `install.sh`, `install.ps1`, `install-all.*`, `hooks/**`,
`settings.template*.json`, `agents/**`, `link-project.*` and every child project's application code
are out of bounds for **all** tasks (FR-012). No task stages, commits or pushes.

## Phase 1: Doctrine

- [x] **T001** — Write `docs/WORKSPACE_SDD.md` with the seven required sections: why workspace-level
  SDD, core idea, folder structure, token-saving strategy, Graphify usage, cross-project feature
  workflow, guardrails. State the core sentence verbatim and state Graphify's optionality
  explicitly.
  *Files: `docs/WORKSPACE_SDD.md`.* Covers: AC-001, AC-005, AC-013, AC-014, AC-016, AC-017.
  **Done 2026-08-05.**

## Phase 2: Templates

- [x] **T002** — Create the four workspace-state templates: `WORKSPACE_CONTEXT.md` (purpose,
  included projects, workflow rules, context strategy, owner notes), `PROJECTS.md` (the seven-column
  table), `DEPENDENCY_GRAPH.md` (relationship block with Evidence/Confidence + Mermaid placeholder),
  `INTEGRATION_CONTRACTS.md` (REST, events, webhooks, shared packages, env vars, auth boundaries,
  data ownership).
  *Files: `docs/_templates/{WORKSPACE_CONTEXT,PROJECTS,DEPENDENCY_GRAPH,INTEGRATION_CONTRACTS}.md`.*
  Covers: AC-007, AC-008, AC-009, AC-010, AC-015. **Done 2026-08-05.**

- [x] **T003** — Create the two governance templates: `SHARED_DECISIONS.md` seeded with D001–D010,
  and `WORKSPACE_GUARDRAILS.md` with the prohibition list and stop conditions.
  *Files: `docs/_templates/{SHARED_DECISIONS,WORKSPACE_GUARDRAILS}.md`.*
  Covers: AC-011, AC-012, AC-014. **Done 2026-08-05.**

- [x] **T004** — Create the four cross-project feature templates: `WORKSPACE_FEATURE_README.md`
  (structure of a cross-project feature folder), `IMPACT_MAP.md` (affected/unaffected projects,
  contracts touched, risks, implementation order, validation plan, bounded reading list),
  `PROJECT_CHANGES.md` (the five-column table), `VALIDATION.md` (per-project, cross-project,
  contract validation, rollback notes).
  *Files: `docs/_templates/{WORKSPACE_FEATURE_README,IMPACT_MAP,PROJECT_CHANGES,VALIDATION}.md`.*
  Covers: AC-013, AC-014. **Done 2026-08-05.**

## Phase 3: The flow

- [x] **T005** — Write `skills/sdd-workspace-onboarding/SKILL.md`: frontmatter (`name`,
  `description` ≤ 400 chars, `triggers`), a valid `## SDD Contract` block, then purpose, inputs,
  workflow (8 steps), token rules, stop conditions, forbidden actions and output format. Body ≤ 600
  lines.
  *Files: `skills/sdd-workspace-onboarding/SKILL.md`.*
  Covers: AC-002, AC-003, AC-004, AC-005, AC-006, AC-013, AC-014, AC-016, AC-017.
  **Done 2026-08-05.**

- [x] **T006** — Write the Codex counterpart `adapters/codex/prompts/sdd-workspace-onboarding.md`:
  same procedure, prompt packaging, no native-agent claim, no global config, Graphify optional, no
  child-project modification without approval. Add its row to `adapters/codex/prompts/README.md`.
  *Files: `adapters/codex/prompts/sdd-workspace-onboarding.md`, `adapters/codex/prompts/README.md`.*
  Covers: FR-003. **Done 2026-08-05.**

## Phase 4: Registration and cross-references

- [x] **T007** — Register the skill: append `"sdd-workspace-onboarding"` to `core.skills` in
  `profiles.json`. One line, no structural change. See D012 for why this overrides the "do not
  modify profiles.json" instruction.
  *Files: `profiles.json`.* Covers: AC-018, FR-015. **Done 2026-08-05.**

- [x] **T008** — Add the `## Workspace SDD` section to `README.md` (5–7 lines + link to
  `docs/WORKSPACE_SDD.md`), a TOC entry, and let `check-consistency.sh --fix` update the
  `skills-total` / `core-skills` markers and the skills badge.
  *Files: `README.md`.* Covers: AC-018. **Done 2026-08-05.**

- [x] **T009** — Add the `codebase-researcher` workspace-mode paragraph to
  `docs/AGENTIC_ROUTING.md`: workspace docs first, then per-project Graphify reports, then bounded
  files.
  *Files: `docs/AGENTIC_ROUTING.md`.* Covers: FR-002 (routing visibility). **Done 2026-08-05.**

- [x] **T010** — Add the Unreleased CHANGELOG entries: Workspace SDD design, the
  `/sdd-workspace-onboarding` skill, the workspace templates, and Graphify per-project usage for
  token-efficient multi-project work.
  *Files: `CHANGELOG.md`.* **Done 2026-08-05.**

> `docs/CONTEXT_PROVIDERS.md` does not exist in this repo — the brief made that update conditional
> on its existence, so no such file was created. The equivalent statement (Graphify per project;
> workspace dependencies are a separate layer) lands in `docs/WORKSPACE_SDD.md` and
> `docs/AGENTIC_ROUTING.md` instead.

## Phase 5: Enforcement

- [x] **T011** — Add the `workspace` check class to `scripts/check-consistency.sh`: existence of
  `docs/WORKSPACE_SDD.md`, `skills/sdd-workspace-onboarding/SKILL.md` and all ten workspace
  templates; existence of the Codex workspace prompt **conditional** on `adapters/codex/` existing.
  *Files: `scripts/check-consistency.sh`.* Covers: FR-013, AC-018. **Done 2026-08-05.**

- [x] **T012** — Add the claim check to the same block: sentence-scoped detection of
  "Graphify is required/mandatory" and "load/read `graph.json` in full" claims, with negator
  suppression so existing correct prohibitions stay clean. Scan `README.md`, `docs/**/*.md`,
  `skills/**/SKILL.md`, `adapters/**/*.md`, `CHANGELOG.md` — **not** `specs/**`, which must be able
  to quote a claim in order to forbid it. Document the heuristic and its accepted false negatives
  in-script.
  *Files: `scripts/check-consistency.sh`.* Covers: AC-006, AC-017, FR-013. **Done 2026-08-05.**

- [x] **T013** — Add five cases to `scripts/check-consistency.test.sh`: missing
  `docs/WORKSPACE_SDD.md` → fail; missing `docs/_templates/WORKSPACE_IMPACT_MAP.md` → fail;
  injected "Graphify is required" → fail; injected "load the full graph.json into context" → fail;
  and a **negative** case asserting the existing negated `AGENTIC_ROUTING.md` prose is not reported.
  *Files: `scripts/check-consistency.test.sh`.* Covers: FR-014, TS-2..TS-5, TS-7.
  **Done 2026-08-05.**

## Phase 6: Validation

- [x] **T014** — Run `bash scripts/check-consistency.sh`, `python3 -m json.tool profiles.json` and
  `bash scripts/check-consistency.test.sh`. All must pass. *Files: none.* Covers: AC-018.
  **Done 2026-08-05.**

- [x] **T015** — Run the adversarial claim sweep across `README.md`, `docs`, `skills`, `adapters`,
  this spec folder and `CHANGELOG.md`. Classify every hit as *real issue*, *safe documentation* or
  *false positive*; fix only real issues. *Files: as needed by real issues only.*
  **Done 2026-08-05.**

## Phase 7: Post-install remediation

- [x] **T016** — Flatten the ten workspace templates to `docs/_templates/WORKSPACE_*.md`, declare
  them in `profiles.json` `core.templates`, and repoint every reference (guide, skill, Codex
  prompt, checker, tests, this spec). Found by running the install for real: the subdirectory
  layout shipped in the repo but never reached an adopter, because `install.sh` copies templates by
  name and does not recurse.
  *Files: `docs/_templates/WORKSPACE_*.md`, `profiles.json`, `README.md`, `docs/WORKSPACE_SDD.md`,
  `skills/sdd-workspace-onboarding/SKILL.md`, `adapters/codex/prompts/sdd-workspace-onboarding.md`,
  `scripts/check-consistency.{sh,test.sh}`, this spec.* Covers: AC-007..AC-012 (for real this
  time), D014. **Done 2026-08-05.**
