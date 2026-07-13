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
- **AC-017: PASS live (2026-07-13).** Initially PASS structural / NOT RUN live; the live
  check was executed on 2026-07-13 after the real deploy (`install.ps1` +
  `install.ps1 -LinkUserClaude`, run by the user). Evidence — confirmed by the user in a
  **fresh Claude Code session**: `deep-reasoner` available with `model: opus`,
  `fast-worker` available with `model: sonnet`, `/sdd-orchestrate` available. All four
  pass criteria met.

### AC-017 live-check procedure — EXECUTED AND PASSED 2026-07-13

**Result: PASS.** The user ran the deploy (Step 1) and confirmed all four pass/fail
criteria (Step 4) in a fresh Claude Code session on 2026-07-13. SPEC.md advanced
`In Review → Done`. The procedure below is kept for reproducibility (re-verify after
future `git pull` + reinstall cycles):

**Step 0 — dry-run preview (verified 2026-07-13, exit 0, read-only):**

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\install.ps1 -DryRun
powershell -NoProfile -ExecutionPolicy Bypass -File .\install.ps1 -DryRun -LinkUserClaude
```

Observed on the author's machine: 57 items would be created in the central dir (Phases 1–4
content not yet deployed there); `~/.claude/skills`, `~/.claude/hooks`, and `~/.claude/CLAUDE.md`
are already correctly linked (no-op); agents correctly report "not present in central dir —
run the install step first". No `[ERROR]` lines.

**Step 1 — real deploy (requires explicit user confirmation — touches
`C:\ProgramData\ClaudeConfig` and `~/.claude`):**

```powershell
.\install.ps1                     # populate central dir (incl. agents/)
.\install.ps1 -LinkUserClaude     # copy agents into ~/.claude/agents (links are already OK)
```

macOS/Linux equivalent: `./install.sh` then `./install.sh --link-user-claude` (needs python3).

**Step 2 — verify files landed:**

```powershell
Get-ChildItem "$env:USERPROFILE\.claude\agents\deep-reasoner.md", "$env:USERPROFILE\.claude\agents\fast-worker.md"
Get-ChildItem "$env:USERPROFILE\.claude\skills\sdd-orchestrate"
```

**Step 3 — open a NEW Claude Code session** (agent/skill discovery happens at session start;
an existing session will not see them).

**Step 4 — pass/fail criteria (all four must hold):**

- `deep-reasoner` appears in the available-agents list, with `model: opus`.
- `fast-worker` appears in the available-agents list, with `model: sonnet`.
- `/sdd-orchestrate` autocompletes / is listed as an available skill.
- Delegating a trivial probe to each agent succeeds (e.g. ask `deep-reasoner` to read one
  file — it must not attempt an edit; ask `fast-worker` a no-op read — it responds in its
  fixed report format).

**PASS →** set SPEC.md `In Review → Done` and run `/spec-close`, recording the session date
and Claude Code version. **FAIL →** record symptoms in DECISIONS.md and consult
`docs/SDD-ORCHESTRATION.md` → Troubleshooting. Never mark AC-017 PASS live without Step 3–4
observed in a fresh session.
