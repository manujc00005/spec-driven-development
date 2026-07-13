# Implementation Plan: Phase 5 — Framework hardening and cross-platform polish

## Summary

A bounded, mostly-documentation-and-parity hardening pass. It reconciles the lifecycle of
the three oldest specs, resolves one documented contradiction, adds a reproducible AC-017
live-check procedure (without deploying), consolidates two overlapping Java compile hooks at
the wiring level (without breaking backward compatibility), adds a Linux/macOS hook-wiring
template at parity with the Windows one, and translates residual Spanish out of the
public-facing agent and orchestration artifacts. No workflow semantics change; no commit; no
live-config writes without confirmation.

## Related spec

`specs/features/005-framework-hardening-and-cross-platform-polish/SPEC.md`

## Impacted areas

| Area | Files | Change type |
|---|---|---|
| Old-spec lifecycle | `specs/features/000-*/`, `001-*/`, `002-*/` (add `TASKS.md`/`DECISIONS.md`, update `## Status`, add close summary) | Docs / state |
| Contradiction reconcile | `specs/features/002-phase2-java-spring-profile/DECISIONS.md` (+ cross-ref in `005/DECISIONS.md`) | Docs |
| AC-017 procedure | `specs/features/004-multimodel-orchestration/TASKS.md` (+ `docs/SDD-ORCHESTRATION.md` "Verifying the integration") | Docs |
| Hook consolidation | `settings.template.json`, `hooks/maven-compile.ps1`, `hooks/maven-compile.sh` | Config + deprecation header |
| Linux template | `settings.template.sh.json` (new), `hooks/README.md`, `docs/INSTALL.md` (pointer) | New + docs |
| Translation | `agents/deep-reasoner.md`, `agents/fast-worker.md`, `skills/sdd-orchestrate/SKILL.md`, `docs/SDD-ORCHESTRATION.md` | Content |
| Counts / honesty | `README.md`, `hooks/README.md`, `profiles.json` (`note` fields) | Docs |
| Verification | all `.sh`/`.ps1` (read-only checks) | None (validation) |

## Proposed approach

Execute in dependency order, grouped so no two edits fight over the same file, and so the
gated items (live deploy) are isolated from the autonomously-safe items (reversible, no
commit, no live-config write).

**Group A — Hook consolidation (autonomous).**
`java-build-test-guard` is a strict superset of `maven-compile`. Resolve the overlap at the
*wiring* level rather than by deletion: (1) repoint `settings.template.json`'s PostToolUse
Java entry from `maven-compile.ps1` to `java-build-test-guard.ps1`; (2) add a deprecation
header comment to both `maven-compile` variants pointing to the canonical hook; (3) keep the
files on disk and in the `java-spring-backend` profile so any project already referencing
`maven-compile` keeps working. This satisfies AC-004 without a deletion decision and without
breaking compatibility.

**Group B — Linux/macOS template (autonomous, additive).**
Create `settings.template.sh.json` mirroring `settings.template.json` structure, replacing
each `powershell -NoProfile -File .../<name>.ps1` with `bash ${CLAUDE_PROJECT_DIR}/hooks/<name>.sh`
and wiring `java-build-test-guard.sh` (the consolidated hook, matching Group A). Document it
in `hooks/README.md`'s cross-platform section and add a pointer from `docs/INSTALL.md`.

**Group C — Translation (autonomous).**
Translate the fixed output-format headings and any Spanish prose in `deep-reasoner.md` and
`fast-worker.md` to English, preserving section count/order/meaning. Translate the Spanish
examples, the architecture-diagram labels, and the "When to use / not use" lines in
`skills/sdd-orchestrate/SKILL.md` and `docs/SDD-ORCHESTRATION.md`.

**Group D — Old-spec lifecycle (autonomous, honesty-gated).**
For `000` and `002`: verify each AC against on-disk evidence (files exist, installer behavior,
templates present). Both are structurally verifiable → backfill missing `TASKS.md`
(and `DECISIONS.md` for `000`), add a close summary, promote `## Status` to `Done`. For `001`:
its ACs are mostly structural (skills/hook/templates exist) but include runtime-degradation
behavior that is only structurally (not live) verified → backfill `TASKS.md`/`DECISIONS.md`,
record that its runtime behavior is structurally verified, and promote to `Done` only if that
is judged sufficient; otherwise keep `In Review` with a recorded reason. Reconcile `002` AC-005
with the current installer via a superseding decision (Group A/002 cross-cut).

**Group E — AC-017 live-check procedure (prepare only; deploy is gated).**
Write the exact, reproducible procedure (install → `-LinkUserClaude`/`--link-user-claude`
dry-run then real → new session → confirm agents in the agent list and `/sdd-orchestrate`
autocompletes) with pass/fail criteria, into `004/TASKS.md` and `docs/SDD-ORCHESTRATION.md`.
Do **not** deploy. `004` stays `In Review`. Executing the check is offered to the user as a
gated follow-up (OQ-1).

**Group F — Counts / honesty sweep + verification (autonomous).**
Update README/hooks-README/profiles.json notes for the consolidated wiring and new template.
Run the static/parity/grep verification gates (FR-008/AC-007) and record results.

## Alternatives considered

- **Physically delete `maven-compile`.** Rejected for this phase: it risks breaking projects
  that already wire it, and the user constraints forbid deleting without justification / not
  breaking compat. Deferred as OQ-2.
- **Make `java-build-test-guard` blocking on compile failure.** Rejected: it is a reminder
  hook by design (exit 0); changing that is a semantics change out of scope.
- **Deploy and run the AC-017 check now.** Rejected as a default: touches `~/.claude`, which
  the user's rules require confirming first, and needs a new session the agent cannot start.
  Offered as a gated follow-up instead.
- **Translate the whole repo's Spanish (including this repo's own feature specs).** Rejected:
  the internal `specs/features/*` are dogfooding records, not the public API surface; scope is
  limited to public-facing agent/orchestration artifacts.

## Dependencies

- None external. All work is local file edits + read-only shell verification.
- Group E's *execution* (not its documentation) depends on user confirmation and a Claude
  Code session restart.

## Risks

- **Translation drift** — a mistranslated agent heading could change the report contract.
  Mitigation: preserve section count/order; verify by grep that heading counts match.
- **Template parity mismatch** — the `.sh` template could drift from the `.ps1` one.
  Mitigation: derive it mechanically entry-by-entry and diff the hook sets.
- **Over-eager "Done"** — promoting a spec whose ACs aren't truly verifiable would violate the
  honesty rule. Mitigation: explicit per-AC evidence check; keep `In Review` when in doubt.
- **Hidden `maven-compile` reliance** — a project could depend on the exact `maven-compile`
  wiring. Mitigation: file retained and still installed; only the *template default* changes.

## Test strategy

- **Static:** `bash -n` on all `.sh`; PowerShell parser on all `.ps1`; JSON parse of the new
  template and `profiles.json`.
- **Parity:** compare wired hook sets between the two templates.
- **Grep gates:** Spanish tokens (`Resumen`, `Estado`, `Recomendación`, `Riesgos`, `Tarea`,
  `Archivos`, `Cambios`, `Preguntas`, `Usuario`, `análisis`, `implementa`), `jq`/`python3` in
  `.sh` hooks, secrets/PII/local paths in the diff.
- **Manual (gated):** AC-017 live procedure, user-run.
- **Regression:** confirm no skill/hook/agent semantics changed beyond consolidation +
  translation; confirm existing `maven-compile` still present and installable.

## Rollback strategy

Every change is an uncommitted working-tree edit; `git checkout -- <file>` reverts any single
file (the user runs git, not the agent). New files (`settings.template.sh.json`,
backfilled `TASKS.md`/`DECISIONS.md`) are removed by deleting them. No live config is touched,
so there is nothing to roll back outside the repo. No commit is made, so the branch history is
untouched.

## PLAN verification checklist

- [x] The plan covers all acceptance criteria (AC-001…AC-010 mapped in TASKS.md).
- [x] The plan avoids behavior outside the spec (no new skills/semantics; consolidation is
      wiring-level; deploy is gated).
- [x] Risks are documented.
- [x] Test strategy is documented.
- [x] Rollback strategy is documented.
- [x] SPEC.md status has been updated to `Ready`.
