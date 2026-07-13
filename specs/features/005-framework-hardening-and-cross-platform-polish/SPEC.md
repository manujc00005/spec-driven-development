# Feature Spec: Phase 5 — Framework hardening and cross-platform polish

## Status

Done

> Closed 2026-07-13. All 15 tasks complete: T001–T012 and T014–T015 implemented and
> verified autonomously (see `TASKS.md` → Verification status), and the one gated task,
> T013 (AC-017 live check), was confirmed by the user and **passed** in a fresh Claude Code
> session the same day — closing `004` as well. Every AC (AC-001…AC-010) is met with
> recorded evidence; closure decision in `DECISIONS.md` D008.

## Problem

The framework is functionally complete (skills, hooks, profiles, templates, agents,
multi-model orchestration, professional README, cross-platform installers) but carries a
set of consistency, honesty, and cross-platform gaps that undermine its credibility as a
professional, portfolio-grade open-source repository:

1. **Stale spec lifecycle.** Specs `000`, `001`, `002` sit at `In Review` although their
   work shipped long ago; `000` and `001` have no `TASKS.md`/`DECISIONS.md`, `002` has no
   `TASKS.md`. The framework does not fully honor its own lifecycle on its oldest features.
2. **A latent documented contradiction.** `002`'s `AC-005` states that missing/planned
   skills are *"skipped gracefully"* by the installer — but Phase 4 changed the installer
   to **hard-error** on a missing *shipped* item. The old acceptance criterion now
   contradicts current behavior and was never reconciled.
3. **AC-017 (Phase 4) is unverified live.** Spec `004` is honestly held at `In Review`
   because agent discovery in a fresh Claude Code session was never confirmed after a real
   deploy. There is no reproducible procedure to perform that check and promote it.
4. **Overlapping Java compile hooks.** `maven-compile` and `java-build-test-guard` both run
   `mvnw compile` on `.java` edits. `java-build-test-guard` is a strict superset (Maven +
   Gradle fallback, opt-in fast tests, safe JSON serialization). The Windows template wires
   the weaker `maven-compile`, and the `java-spring-backend` profile installs both.
5. **Windows-only hook-wiring template.** `settings.template.json` ships PowerShell commands
   only. macOS/Linux users must hand-translate every entry — a cross-parity gap for a repo
   that otherwise ships `.ps1` + `.sh` for everything.
6. **Spanish content in a public English repo.** The agents' output-format headings, the
   `/sdd-orchestrate` skill examples, and `docs/SDD-ORCHESTRATION.md` examples are in
   Spanish, inconsistent with the English-facing README and docs.

## Goal

Run a bounded hardening pass that closes these gaps **honestly** — reconciling stale
lifecycle state, resolving the documented contradiction, providing a reproducible live-check
procedure, consolidating the duplicated hook at the wiring level without breaking existing
projects, achieving Windows/Linux template parity, and removing residual Spanish from
public artifacts — without changing any workflow semantics, breaking backward compatibility,
committing, or touching live config (`~/.claude`, `C:\ProgramData\ClaudeConfig`) without
explicit confirmation.

## Non-goals

- Rewriting Git history, force-pushing, committing, pushing, resetting, or changing branches.
- Modifying the user's real configuration (`~/.claude`, `C:\ProgramData\ClaudeConfig`, any
  real `CLAUDE.md`) without explicit confirmation.
- Marking AC-017 (Phase 4) as PASS *live* without observation in a fresh Claude Code session.
- Deleting any existing hook in this phase (deprecation only; physical removal needs its own
  explicit, justified decision in a future phase).
- Changing the default profile (`java-spring-backend` stays default).
- Enabling the `blockchain-crypto` profile.
- Installing any dependency.
- Adding new skills, agents, or profiles.
- Writing the worked `examples/` walkthrough (separate future work).
- Shipping `payments-fintech` content or Prisma/Next.js reviewers.

## Users / Actors

- **Repo maintainer (author)** — runs the prepared live check, reviews and commits.
- **External adopter on macOS/Linux** — installs and wires hooks from the new `.sh` template.
- **External adopter on Windows** — unaffected; existing wiring keeps working.
- **Claude Code (as execution copilot)** — reads the reconciled specs and English agent
  contracts.

## Current behavior

- Specs `000`/`001`/`002` are `In Review`; `003` is `Done`; `004` is `In Review` (AC-017).
- `settings.template.json` wires `maven-compile`; the java profile installs both compile hooks.
- No `.sh` hook-wiring template exists.
- Agent output headings and orchestration examples are Spanish.
- No documented AC-017 live-check procedure exists.

## Desired behavior

- Old specs are either `Done` (with an evidence-backed close summary and any missing
  `TASKS.md`/`DECISIONS.md` backfilled) or explicitly kept `In Review` with a recorded reason.
- `002`'s AC-005 contradiction is reconciled by a recorded superseding decision.
- A reproducible AC-017 live-check procedure exists; `004` advances to `Done` only after it
  passes.
- The templates wire exactly one Java compile hook (`java-build-test-guard`); `maven-compile`
  carries a deprecation header pointing to it; existing wirings keep working.
- A Linux/macOS hook-wiring template exists at command-parity with the Windows one.
- Public agent/orchestration artifacts contain no Spanish.

## Functional requirements

- **FR-001** — Reconcile the lifecycle of specs `000`, `001`, `002`: verify each AC against
  on-disk evidence; backfill missing `TASKS.md`/`DECISIONS.md`; promote to `Done` with a
  close summary **only** where every AC is verifiable, otherwise keep `In Review` with a
  recorded reason.
- **FR-002** — Record a superseding decision reconciling `002` AC-005 ("skipped gracefully")
  with the current hard-error-on-missing-shipped-item installer behavior.
- **FR-003** — Add a reproducible AC-017 live-check procedure (exact commands, expected
  output, pass/fail criteria) to `004`'s docs and to `docs/SDD-ORCHESTRATION.md`. Do **not**
  deploy or promote `004` here.
- **FR-004** — Consolidate Java compile hooks at the wiring level: change
  `settings.template.json` to wire `java-build-test-guard` instead of `maven-compile`; add a
  deprecation header to `maven-compile.ps1`/`.sh` pointing to the canonical hook; keep the
  files and their installation for backward compatibility.
- **FR-005** — Create a Linux/macOS hook-wiring template (`settings.template.sh.json`) at
  command-parity with `settings.template.json` (a `bash <path>.sh` command for every hook the
  Windows template wires), and document it in `hooks/README.md`.
- **FR-006** — Translate to English: the output-format headings and any Spanish prose in
  `agents/deep-reasoner.md` and `agents/fast-worker.md`; the examples and Spanish lines in
  `skills/sdd-orchestrate/SKILL.md`; the Spanish examples/diagram labels in
  `docs/SDD-ORCHESTRATION.md`.
- **FR-007** — Update `README.md`, `hooks/README.md`, and `profiles.json` notes to reflect
  the consolidated wiring and the new template; keep all shipped/planned/disabled and count
  statements accurate.
- **FR-008** — Cross-platform verification: `bash -n` on every `.sh`, PowerShell parse on
  every `.ps1`, confirm every hook family ships both variants, and confirm `.sh` hooks use
  no `jq` and no `python3`.

## Non-functional requirements

- **Compatibility:** No existing project breaks. No skill/hook/agent semantics change beyond
  the documented consolidation and translation.
- **Safety:** No commit/push/reset/branch change. No file deleted without a recorded
  justification. No writes to `~/.claude` or `C:\ProgramData\ClaudeConfig` without explicit
  confirmation. `.sh` hooks remain `jq`-free and `python3`-free.
- **Honesty:** Nothing is marked `Done` unless verified against on-disk evidence or a passed
  runnable check. Structural-only verification is labeled as such.
- **Maintainability:** Changes are minimal, additive where possible, and documented.

## API / Interface changes

- `agents/deep-reasoner.md`, `agents/fast-worker.md`: output-format section headings change
  from Spanish to English (behavioral contract of the agents' report format).
- `settings.template.json`: the wired Java compile hook changes from `maven-compile` to
  `java-build-test-guard`.
- New file `settings.template.sh.json`: Linux/macOS hook-wiring template.
- `maven-compile.ps1`/`.sh`: deprecation header comment (no behavior change).

## Data model changes

None.

## Edge cases

- An existing project that already wires `maven-compile` in its own `settings.json`: must
  keep working (file retained, still installable). Verified by not removing the file.
- A macOS user who copied the Windows template previously: the new `.sh` template is
  additive; the old one is unchanged.
- Translating agent headings must not alter the *number* or *meaning* of the report sections,
  only their language, so downstream expectations stay intact.
- An adopter on a version of Claude Code without model-alias support: unchanged; the
  fallback documentation already covers it.

## Acceptance criteria

- **AC-001** — Each of specs `000`/`001`/`002` is either `Done` with a written close summary
  whose every AC is backed by on-disk evidence, or remains `In Review` with an explicit
  recorded reason. Nothing is `Done` without verification. Missing `TASKS.md`/`DECISIONS.md`
  are backfilled for any spec promoted to `Done`.
- **AC-002** — `002` AC-005's "skipped gracefully" wording is reconciled with the current
  hard-error installer behavior via a recorded superseding decision (in `002/DECISIONS.md`
  and/or `005/DECISIONS.md`), not left as a silent contradiction.
- **AC-003** — A documented, reproducible AC-017 live-check exists (exact commands, expected
  output, pass/fail). `004` is promoted to `Done` **only** after it passes; until then it
  stays `In Review` with the procedure recorded.
- **AC-004** — After this phase, the shipped templates wire exactly one Java compile hook
  (`java-build-test-guard`). `maven-compile.ps1`/`.sh` carry a deprecation header pointing to
  it and remain on disk and installable so existing wirings do not break.
- **AC-005** — `settings.template.sh.json` exists and wires, via `bash <path>.sh`, every hook
  the Windows `settings.template.json` wires; `hooks/README.md` documents it.
- **AC-006** — No Spanish remains in `agents/deep-reasoner.md`, `agents/fast-worker.md`,
  `skills/sdd-orchestrate/SKILL.md`, or `docs/SDD-ORCHESTRATION.md` (verified by grep for
  common Spanish tokens).
- **AC-007** — Every `.sh` passes `bash -n`; every `.ps1` parses; every hook family has both
  a `.ps1` and a `.sh`; no `.sh` hook references `jq` or `python3`.
- **AC-008** — `README.md`, `hooks/README.md`, and `profiles.json` notes reflect the
  consolidated wiring and the new template; all count and shipped/planned/disabled statements
  remain accurate.
- **AC-009** — No commit, push, reset, branch change, or force-push occurred. No file was
  deleted without a recorded justification. No writes to `~/.claude` or
  `C:\ProgramData\ClaudeConfig` occurred without explicit confirmation.
- **AC-010** — No secrets, PII, or hardcoded local paths in any new or modified file.

## Risks

- **Translation drift** — a mistranslated agent heading could silently change the agents'
  report contract. Mitigated by preserving section count/order/meaning and re-checking by grep.
- **Template divergence** — a second settings template can drift from the first over time.
  Mitigated by deriving it mechanically and adding a parity check to the verification gates.
- **Over-eager closure** — promoting an old spec without real evidence would violate the
  honesty rule. Mitigated by per-AC evidence checks (D006) and by labeling structural-only
  verification explicitly.
- **Hidden `maven-compile` reliance** — some project may wire it by absolute path. Mitigated
  by keeping the file shipped and installable; only the template default changes.
- **Environment gaps during validation** — this machine may lack `python3` in bash, limiting
  `install.sh --dry-run` to its fail-clear path. Mitigated by documenting exactly what was and
  wasn't executable here, and providing the exact commands for a Linux/macOS machine.

## Test strategy

- **Static:** `bash -n` on every `.sh` (hooks, lib, installers); PowerShell language-parser
  check on every `.ps1`; JSON parse of `settings.template.sh.json`, `settings.template.json`,
  and `profiles.json`.
- **Behavioral (safe):** `install.ps1 -DryRun` (default, single-profile, multi-profile) — reads
  but never writes; `install.sh --dry-run` where `python3` exists (here: verifies the fail-clear
  error path instead); `link-project` dry-run against a temp directory.
- **Parity:** diff of the hook sets wired by the two settings templates.
- **Grep gates:** no `jq`/`python3` in `.sh` hooks; no Spanish tokens left in the four public
  artifacts; no secrets/PII/personal paths; no destructive commands introduced.
- **Manual (gated):** the AC-017 live check in a fresh Claude Code session, user-confirmed.

## Rollback strategy

All changes are uncommitted working-tree edits: any single file reverts with
`git checkout -- <file>` (run by the user; the agent never runs destructive git). New files
(`settings.template.sh.json`, backfilled `TASKS.md`/`DECISIONS.md`, the 005 folder) are removed
by deleting them. No live configuration is touched in the autonomous part of this phase, so
nothing outside the repo needs rolling back. No commits are made, so history is untouched.

## Test scenarios

- **Static:** `bash -n` on all `.sh`; `[System.Management.Automation.Language.Parser]` parse
  on all `.ps1`; JSON parse of `settings.template.sh.json` and `profiles.json`.
- **Parity:** diff the hook set wired by `settings.template.json` vs `settings.template.sh.json`
  (same hooks, platform-appropriate commands).
- **Grep gates:** no Spanish tokens in the four public artifacts; no `jq`/`python3` in `.sh`
  hooks; no secrets/PII/local paths in the diff.
- **Manual (gated, user-run):** the AC-017 live-check procedure on a real machine.

## Assumptions

- Translating agent output headings to English is a net improvement for a public English
  repo and does not disrupt the user's own Spanish-language interaction (the agents still
  operate in whatever language the session uses; only the fixed report headings change).
- Keeping `maven-compile` as a deprecated shim (vs deleting it) is the backward-compatible
  choice consistent with the "don't break existing projects / don't delete without
  justification" constraints.

## Open questions

- **OQ-1 (gated):** Should the AC-017 live check be *executed now* (requires explicit
  confirmation to deploy agents into the real `~/.claude/agents` and a fresh session), or
  only *prepared* as a documented procedure this phase? Default: prepare only.
- **OQ-2:** Should `maven-compile` be physically removed in a later phase once no known
  project references it, or kept indefinitely as a deprecated alias? Default: keep as
  deprecated for now; revisit later.
