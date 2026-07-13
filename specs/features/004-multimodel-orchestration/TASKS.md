# Tasks: Phase 4 — Multi-model orchestration

Status legend: [ ] pending · [x] done

- [x] T001 — Create `agents/deep-reasoner.md` (Opus, read-only tools, fixed report format). → AC-002, AC-004
- [x] T002 — Create `agents/fast-worker.md` (Sonnet, delimited tasks, fixed report format). → AC-003, AC-005
- [x] T003 — Create `agents/README.md` (rationale: copy-not-link, customization, update path). → AC-010, AC-019
- [x] T004 — Create `skills/sdd-orchestrate/SKILL.md` (classification L1–L4, 7 phases, delegation policy, fallback, no-overlap rule, analysis-only mode). → AC-001, AC-006, AC-007, AC-008, AC-015, AC-023
- [x] T005 — Update `profiles.json` (v0.4.0: core `agents`/`plannedAgents`, core skill `sdd-orchestrate`, `$comment`). → AC-009, AC-022
- [x] T006 — Update `install.ps1` (agent profile resolution, integrity check, central copy, per-file user copy under `-LinkUserClaude`). → AC-009, AC-010, AC-011, AC-013
- [x] T007 — Update `install.sh` (mirror of T006 under `--link-user-claude`). → AC-009, AC-010, AC-011, AC-013
- [x] T008 — Update `link-project.ps1` (per-file agent copy into `<project>/.claude/agents`). → AC-009, AC-010
- [x] T009 — Update `link-project.sh` (mirror of T008). → AC-009, AC-010
- [x] T010 — Add managed orchestration block to `CLAUDE.md.example` (`<!-- SDD-ORCHESTRATION:START/END -->`). → AC-001, AC-012
- [x] T011 — Create `docs/SDD-ORCHESTRATION.md` (architecture, responsibilities, classification, costs, install/update, examples, fallback, troubleshooting, rollback, managed files). → AC-019
- [x] T012 — Update `README.md` (command list, repo structure, orchestration section). → AC-021
- [x] T013 — Update `docs/INSTALL.md` (agents in install/link flows, verification, rollback). → AC-019
- [x] T014 — Validation: syntax checks (bash -n, PS parser), YAML frontmatter parse. → AC-016, AC-017, AC-018
- [x] T015 — Validation: temp-dir install ×2 (idempotence), dry-run, exclusion test, pre-existing-user-agent test, link-project test. → AC-011, AC-013, AC-018
- [x] T016 — Update DECISIONS.md with the decisions taken; final report with AC evidence. → AC-024

## Traceability

Every AC-001…AC-024 maps to at least one task above; AC-014/AC-020 are cross-cutting
constraints verified in T014–T016 (no destructive commands added; no commits/push).

## Review outcome

- `/spec-review`: **PASS** — implementation matches SPEC, no scope creep, traceability intact.
- `/qa-review`: **PASS (structural)** — installers (dry-run, idempotence, skip-on-diff,
  Force+backup, no `settings.local.json`/`.env` copy, no real `CLAUDE.md` write), agents
  (deep-reasoner opus/read-only, fast-worker sonnet/delimited), `profiles.json` semantics
  (java-spring default, blockchain disabled, core agents, backward-compat), link-project
  additive agent copy, and CLAUDE.md.example markers all verified. Secret scan and
  destructive-command grep clean.
- **AC-017: PASS structural / NOT RUN live.** Frontmatter/skill format matches the agents
  Claude Code already recognizes, but the agents have NOT been deployed to the real
  `~/.claude/agents` and no new session has confirmed live discovery.

### Pending before Done

SPEC stays **In Review** until this live check passes:

1. Run `install.ps1 -LinkUserClaude` (Windows) / `install.sh --link-user-claude` to deploy
   the agents into `~/.claude/agents` and the skill via the linked `~/.claude/skills`.
2. Open a **new** Claude Code session.
3. Confirm `deep-reasoner`, `fast-worker`, and `/sdd-orchestrate` are recognized (agents in
   the available-agents list; `/sdd-orchestrate` autocompletes).

Only then move SPEC.md `In Review → Done` and run `/spec-close`.
