# Tasks: Phase 5 — Framework hardening and cross-platform polish

Status legend: `[ ]` pending · `[x]` done · `[~]` blocked/gated (needs user confirmation)
Execution tag: **[AUTO]** = reversible, no commit, no live-config write — executable now ·
**[GATED]** = needs explicit user confirmation or a session restart the agent cannot do.

## Phase 1: Hook consolidation (Group A)

- [x] T001 **[AUTO]** — Repoint `settings.template.json` PostToolUse Java entry from
      `maven-compile.ps1` to `java-build-test-guard.ps1`. Covers: AC-004.
- [x] T002 **[AUTO]** — Add a deprecation header to `hooks/maven-compile.ps1` and
      `hooks/maven-compile.sh` pointing to `java-build-test-guard` (behavior unchanged; files
      retained for back-compat). Covers: AC-004, AC-009.

## Phase 2: Linux/macOS template parity (Group B)

- [x] T003 **[AUTO]** — Create `settings.template.sh.json` mirroring `settings.template.json`,
      wiring `bash ${CLAUDE_PROJECT_DIR}/hooks/<name>.sh` for every hook, using
      `java-build-test-guard.sh` as the Java compile hook (consistent with T001). Covers: AC-005.
- [x] T004 **[AUTO]** — Document `settings.template.sh.json` in `hooks/README.md`
      (cross-platform section) and add a pointer from `docs/INSTALL.md`. Covers: AC-005, AC-008.

## Phase 3: Translation to English (Group C)

- [x] T005 **[AUTO]** — Translate output-format headings + any Spanish prose in
      `agents/deep-reasoner.md` to English, preserving section count/order/meaning. Covers: AC-006.
- [x] T006 **[AUTO]** — Same for `agents/fast-worker.md`. Covers: AC-006.
- [x] T007 **[AUTO]** — Translate Spanish examples/labels/lines in
      `skills/sdd-orchestrate/SKILL.md`. Covers: AC-006.
- [x] T008 **[AUTO]** — Translate Spanish examples + architecture-diagram labels in
      `docs/SDD-ORCHESTRATION.md`. Covers: AC-006.

## Phase 4: Old-spec lifecycle reconciliation (Group D)

- [x] T009 **[AUTO]** — Verify each AC of spec `000` against on-disk evidence; backfill
      `TASKS.md` + `DECISIONS.md`; add close summary; set `## Status` to `Done` if all ACs
      verified. Covers: AC-001. *(Done — includes the executable-bit fix, D007.)*
- [x] T010 **[AUTO]** — Same verification + backfill for spec `002` (`TASKS.md`); reconcile
      AC-005 ("skipped gracefully" vs current hard-error) via a superseding decision in
      `002/DECISIONS.md`. Covers: AC-001, AC-002. *(Done — 002/D006 recorded.)*
- [x] T011 **[AUTO]** — Verify spec `001`; backfill `TASKS.md` + `DECISIONS.md`; promote to
      `Done` only if its (structural) verification is sufficient, else keep `In Review` with a
      recorded reason. Covers: AC-001. *(Done — promoted with explicit structural labels.)*

## Phase 5: AC-017 live-check procedure (Group E — prepare only)

- [x] T012 **[AUTO]** — Write the reproducible AC-017 live-check procedure (exact commands,
      expected output, pass/fail) into `004/TASKS.md` and `docs/SDD-ORCHESTRATION.md`
      "Verifying the integration". Do not deploy; `004` stays `In Review`. Covers: AC-003.
      *(Done — dry-runs executed and their observed output recorded in the procedure.)*
- [x] T013 **[GATED → EXECUTED]** — Execute the AC-017 live check and, if it passes, promote
      `004` to `Done`. Covers: AC-003. *(Done 2026-07-13: the user confirmed the gate, ran the
      deploy themselves, and verified in a fresh Claude Code session that `deep-reasoner`
      (opus), `fast-worker` (sonnet), and `/sdd-orchestrate` are all recognized. `004`
      promoted to Done — see 004/DECISIONS.md D010.)*

## Phase 6: Honesty sweep + verification (Group F)

- [x] T014 **[AUTO]** — Update `README.md`, `hooks/README.md`, and `profiles.json` `note`
      fields for the consolidated wiring + new template; keep counts and shipped/planned/
      disabled accurate. Covers: AC-008. *(Also updated `docs/INSTALL.md` — new "Wiring hooks"
      section.)*
- [x] T015 **[AUTO]** — Run verification gates. Covers: AC-006, AC-007, AC-008, AC-010.
      **Results recorded below.**

## Traceability

| AC | Tasks |
|---|---|
| AC-001 | T009, T010, T011 |
| AC-002 | T010 |
| AC-003 | T012, T013 (gated) |
| AC-004 | T001, T002 |
| AC-005 | T003, T004 |
| AC-006 | T005, T006, T007, T008, T015 |
| AC-007 | T015 |
| AC-008 | T004, T014, T015 |
| AC-009 | cross-cutting (T002; no commit/delete/live-write anywhere) |
| AC-010 | T015 |

## Verification status (T015 — executed 2026-07-13 on Windows 10 + Git Bash)

| Gate | Result |
|---|---|
| `bash -n` on all 12 hook `.sh` + `lib/claude-json.sh` + `install.sh` + `link-project.sh` | **PASS** (all OK) |
| PowerShell language parser on all 11 hook `.ps1` + `install.ps1` + `link-project.ps1` | **PASS** (0 parse errors) |
| JSON validity: `settings.template.json`, `settings.template.sh.json`, `profiles.json` | **PASS** (all parse) |
| `jq`/`python3` in `.sh` hook code | **PASS** (none — word-boundary grep clean) |
| Template parity (wired hook sets, Windows vs Linux) | **PASS** (identical 7-hook sets: eslint-fix, git-guardrails, java-build-test-guard, prettier-format, project-init-check, sdd-status-banner, ts-check) |
| Spanish tokens in the 4 public artifacts | **PASS** (only false positives: English "Investigate/investigation" matching the `investiga` pattern) |
| Destructive patterns (`rm -rf`, `del /s`, `rd /s`, `Remove-Item -Recurse`, `format`) in shipped scripts | **PASS** (none) |
| Secret/PII scan on new/changed files | **PASS** (clean) |
| `install.ps1 -DryRun` (default) | **PASS** exit 0 — 57 items would be created in central dir (Phases 1–4 content not yet deployed there); 2 central hook copies differ (older versions); no `[ERROR]` |
| `install.ps1 -DryRun -LinkUserClaude` | **PASS** exit 0 — `~/.claude` skills/hooks/CLAUDE.md already correctly linked (no-op); agents correctly report "not present in central dir" |
| `install.ps1 -DryRun -Profile java-spring-backend` | **PASS** exit 0, resolves core+java-spring-backend |
| `install.ps1 -DryRun -Profile java-spring-backend,messaging-event-driven` | **PASS** exit 0, resolves all three |
| `link-project.ps1 -DryRun` against a temp dir | **PASS** exit 0; `settings.local.json` untouched; agents skip correct |
| `./install.sh --dry-run` on this machine | **fail-clear verified** — this machine's Git Bash has no `python3`, and the script emitted exactly its designed error and stopped. Full dry-run behavior on a real Linux/macOS box remains an environment limitation of this validation (commands documented in `docs/INSTALL.md`). |
| Executable bit on tracked `.sh` files | **FIXED** — was `100644` since Phase 0; staged to `100755` via `git add --chmod=+x` (D007) |
| AC-017 live check (T013, gated) | **PASS live 2026-07-13** — user-run deploy + fresh-session confirmation: `deep-reasoner` (opus), `fast-worker` (sonnet), `/sdd-orchestrate` all recognized |

## Gated step (T013) — RESOLVED 2026-07-13

The user confirmed the gate and ran the deploy commands themselves
(`.\install.ps1` + `.\install.ps1 -LinkUserClaude`), then verified all four pass/fail
criteria in a fresh Claude Code session (both agents recognized with the correct models;
`/sdd-orchestrate` available). AC-017 = **PASS live**; `004` closed. Evidence and the
retained procedure: `004-multimodel-orchestration/TASKS.md` and `DECISIONS.md` D010.
