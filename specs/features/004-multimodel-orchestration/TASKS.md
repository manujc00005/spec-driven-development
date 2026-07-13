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
