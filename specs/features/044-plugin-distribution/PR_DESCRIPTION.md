# Pull Request Description

## Summary

The repository root becomes a Claude Code and Codex plugin named `sdd`, and the repository becomes
its own marketplace, so the framework installs with two commands per host and no installer of ours.
The installer stays untouched for now; this PR records the evidence a later retirement spec needs.
It also closes the comparison with `everything-claude-code`: three reviewer checklist lines adopted,
eighteen items rejected with reasons.

## Related spec

`specs/features/044-plugin-distribution/` — status at time of PR: **Done**.

## Acceptance criteria coverage

- AC-001: four manifests exist, valid JSON, none names an individual skill or agent — Covered
- AC-002: `hooks/hooks.json` equals the bash template in event, matcher, hook, timeout, status message — Covered (asserted by the gate)
- AC-003: local marketplace add and install exit 0 on Claude Code — Covered (`evidence/CLAUDE_INSTALL.md`)
- AC-004: inventory 72 skills / 8 agents, nothing from `runner/`, `scripts/`, `specs/`, `evals/`, `adapters/`, `docs/` — Covered (`evidence/INVENTORY.md`)
- AC-005: projected token cost recorded with CLI version — Covered (`evidence/TOKEN_COST.md`, ~8.3k always-on)
- AC-006: disposable project resolves `/spec-create` and `/sdd`, `project-init-check` fires from the plugin — Covered (`evidence/E2E_SESSION.md`, see D010 for the `specs/` and `stream-json` conditions)
- AC-007: Codex marketplace add and plugin add exit 0 — Covered (`evidence/CODEX_INSTALL.md`; skill execution on Codex unobserved by quota, D012)
- AC-008: gate passes clean, fails with one hook removed, passes restored — Covered (`evidence/CONSISTENCY_SUITE.md`, 53/53)
- AC-009: two checklist lines in `security-review`, one in `qa-review`, additions only — Covered (one extra modified line in `security-review` is D009's reference repoint)
- AC-010: rejected `everything-claude-code` items recorded with one reason each — Covered (D004, 18 items)
- AC-011: INSTALL.md plugin section first, Windows statement, double-wiring warning, README link, CHANGELOG line, hooks README sentence — Covered
- AC-012: installer, `profiles.json`, `runner/` untouched — Covered (`evidence/FINAL_GATE.md`, empty diff)

## Changes

| Area | Files | What changed |
|---|---|---|
| Plugin identity | `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `.codex-plugin/plugin.json` | New. Plugin `sdd`, marketplace `spec-driven-development`, `source: "./"`. Directories discovered by convention. |
| Hook wiring | `hooks/hooks.json`, `hooks/README.md` | New third wiring: transcription of `settings.template.sh.json` with `${CLAUDE_PLUGIN_ROOT}`. README names it. |
| Consistency gate | `scripts/check-consistency.sh`, `scripts/check-consistency.test.sh` | `plugin-wiring` check: whole-command canonical-shape match per side, `type` and `statusMessage` compared, unknown hook-entry keys rejected, malformed shapes fail closed. Seven suite cases. |
| Agents layout | `agents/README.md` → `docs/AGENTS.md`, plus 5 reference repoints | The loader registers every `.md` under `agents/`; the README was shipping as a ninth agent (D009). |
| Reviewer checks | `skills/security-review/SKILL.md`, `skills/qa-review/SKILL.md` | Dependency audit + lockfile, licence compatibility, `TODO`/`FIXME` without ticket. |
| Docs | `docs/INSTALL.md`, `README.md`, `CHANGELOG.md`, `docs/AGENTIC_ROUTING.md` | "Install as a plugin" section with five caveats (Windows, double hooks, duplicated skills, in-place loading, what you are trusting); README points to it first. |
| Spec record | `specs/features/044-plugin-distribution/` | SPEC, PLAN, TASKS, DECISIONS (D001–D013), nine evidence files. |

## Decisions made

D001 one plugin at the repo root, per-profile split deferred to the recorded cost · D002 `hooks.json` is a transcription, bash only · D003 installer untouched, retirement is a later spec · D004 what was taken from `everything-claude-code` and what was not · D005 the gate holds the two wirings equivalent · D006 every AC is a recorded observation · D007 number 044 · D008 AC-011 extended at planning · D009 `agents/README.md` moves · D010 hook observation conditions · D011 two caveats after spec-review · D012 Codex skill execution unobserved by quota · D013 security review disposition and the whole-command gate.

## Tests

- Tests added or updated: seven `plugin-wiring` cases in `scripts/check-consistency.test.sh` (hook removed, chained prefix, absolute path, async key, chained suffix, malformed shape, missing file), each with an anti-vacuous guard.
- Tests run: `scripts/check-consistency.sh` on the final tree; `scripts/check-consistency.test.sh` three times across the branch.
- Test results: gate passes; suite 53 passed, 0 failed on the final tree (`evidence/CONSISTENCY_SUITE.md`).
- Manual testing done: local marketplace add and install on both CLIs; `claude plugin details sdd` inventory and cost; two print-mode sessions in a disposable project resolving `/sdd` and `/spec-create`; `SessionStart` hook message and a blocking `PreToolUse` hook observed from the plugin's wiring, attributed through the debug log; the rendered INSTALL.md section read back.

## Reviews

`/spec-review` Pass · `/qa-review` Pass · `/security-review` via the `security-reviewer` agent: Partial (one confirmed Medium, SEC-044-001) → fixed → re-verified **Pass**, with the Low residual also closed (`evidence/SECURITY_REVIEW.md`).

## Risks

- Hooks now run in every project where the plugin is enabled; four of them run project-controlled tooling. Documented, not prevented; `--scope project` recommended for untrusted checkouts.
- A directory-sourced marketplace loads the checkout in place: branch switches in that clone change what every enabled project runs next session. Documented with the separate-clone remedy.
- A machine with `--link-user-claude` and the plugin lists every skill twice. Documented; the retirement spec removes the cause.
- Whole-repo plugin cost: ~8.3k always-on tokens on Claude Code; on Codex, skill descriptions are truncated to fit its budget. Recorded, not acted on.
- Suite runtime grows by five repo copies (DEBT-003 territory).

## Follow-up work

- Repeat the Codex skill-execution check after 2026-09-07 (account quota), D012.
- Decide the per-profile split on the recorded numbers, D001.
- Installer retirement spec: `scripts/update.*`, the install manifest, and the now-dead `agents/README.md` copy branch in `install.sh`/`install.ps1`.
- Observe a `PostToolUse` plugin hook (formatters) once; only `SessionStart` and a blocking `PreToolUse` were observed.

## Checklist

- [x] Implementation matches all acceptance criteria in the spec
- [x] No behavior outside the spec was introduced without a recorded decision (D009–D013)
- [x] Tests were added or updated for changed behavior
- [x] All decisions are documented in DECISIONS.md
- [x] SPEC.md status is up to date (Done)
- [x] Security-sensitive behavior was reviewed
- [ ] Database changes were reviewed — not applicable
- [ ] Performance-sensitive paths were reviewed — not applicable
- [x] No unrelated files were changed
