# Implementation Plan: Plugin distribution

## Summary

Add four declarative files that make the repository root a Claude Code and Codex plugin and the
repository its own marketplace: `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`,
`.codex-plugin/plugin.json` and `hooks/hooks.json`. Teach `scripts/check-consistency.sh` that
`hooks/hooks.json` is a third hook wiring that must stay equivalent to `settings.template.sh.json`.
Prove installation from the local checkout on both CLIs and in a disposable project, recording every
command output under `evidence/`. Add three one-line reviewer checks taken from
`everything-claude-code` and close that comparison in `DECISIONS.md`. Touch no installer, no
`profiles.json`, no `runner/`.

## Related spec

`specs/features/044-plugin-distribution/SPEC.md`

## Impacted areas

- New: `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `.codex-plugin/plugin.json`,
  `hooks/hooks.json`, `specs/features/044-plugin-distribution/evidence/`.
- Modified: `scripts/check-consistency.sh` (one new check family, `plugin-wiring`),
  `scripts/check-consistency.test.sh` (two cases), `skills/security-review/SKILL.md` (two lines),
  `skills/qa-review/SKILL.md` (one line), `docs/INSTALL.md` (one section), `README.md` (install
  section pointer), `CHANGELOG.md` (one Unreleased line), `hooks/README.md` (one sentence naming
  the third wiring).
- Untouched by contract (AC-012): every installer script, `profiles.json`, `runner/`.

## Context budget

### Reading list

- `specs/features/044-plugin-distribution/{SPEC,PLAN,TASKS,DECISIONS}.md`
- Reference plugin on this machine, read-only:
  `~/.claude/plugins/cache/claude-plugins-official/ralph-loop/1.0.0/{.claude-plugin/plugin.json,hooks/hooks.json}`
  and `~/.claude/plugins/known_marketplaces.json` (directory-sourced marketplace shape).
- `settings.template.sh.json` (whole file, 90 lines) and `hooks/README.md` lines 1–12.
- `scripts/check-consistency.sh` lines 194–292 and `scripts/check-consistency.test.sh` lines 1–60
  and 165–180.
- `skills/security-review/SKILL.md` lines 67–86; `skills/qa-review/SKILL.md` lines 41–57.
- `docs/INSTALL.md` lines 1–20 and 69–86; `README.md` lines 234–275 and 571–612;
  `CHANGELOG.md` lines 1–30.
- Nothing else. In particular not `install.sh`, not `runner/`, not other specs, not
  `everything-claude-code` (its evaluation is finished and recorded in D004).

### Model routing

Every task is mechanical once the spike (T001) has answered the two open assumptions: JSON files
copied from a known shape, a Python check mirroring an existing one, one-line Markdown edits,
recorded CLI runs. Route everything to the cheap tier (`fast-worker`). No deep-reasoning phase.
The only judgement calls are in T001's interpretation of the inventory (does `agents/` load, does
anything outside the conventional directories load) and they are yes/no readings of CLI output,
recorded as evidence and decided in `DECISIONS.md`.

## Proposed approach

1. **Spike first, on the riskiest assumption.** Create the two Claude manifests in their minimal
   form, add the checkout as a local marketplace, install, and read `claude plugin details sdd`.
   That single output answers both assumptions the spec left open (conventional discovery of
   `agents/`; nothing outside `skills/`, `agents/`, `hooks/` loaded). Record it before writing
   anything else. If `agents/` does not load, add explicit directory keys to `plugin.json`; if
   non-content directories load, find the loader's exclusion mechanism. Either outcome lands in
   `DECISIONS.md` as an amendment to D001.
2. **Finish the manifests.** Identity `sdd`, version `0.1.0`, marketplace `spec-driven-development`
   with `source: "./"`. Codex manifest with the same identity and `"skills": "./skills/"`.
3. **`hooks/hooks.json` by transcription, not by hand.** Take `settings.template.sh.json`, keep the
   `hooks` object byte-for-byte, and rewrite each command prefix
   `bash ${CLAUDE_PROJECT_DIR}/.claude/hooks/` to `bash "${CLAUDE_PLUGIN_ROOT}/hooks/`. Add the
   `description` field plugins carry. No hook script changes.
4. **Make the gate watch the third wiring.** In `check-consistency.sh`, call the existing
   `check_settings_wiring` on `hooks/hooks.json` (reference existence and the deprecated pair), and
   add a `plugin-wiring` check that parses both JSON files and asserts the multiset of
   `(event, matcher, hook-name, timeout)` is identical. Two test cases: one hook removed from
   `hooks/hooks.json` must fail with `[plugin-wiring]`; the clean copy must still pass.
5. **Three checklist lines.** Two under "Security checklist" in `security-review`, one under
   "Review checklist" in `qa-review`, each in the imperative or interrogative voice of its
   neighbours.
6. **Docs.** A "Install as a plugin" section at the top of `docs/INSTALL.md`, before the installer;
   the README quickstart points at it first and keeps the installer as the alternative; one
   Unreleased line in `CHANGELOG.md`; one sentence in `hooks/README.md` naming `hooks/hooks.json`
   as the plugin wiring.
7. **Evidence.** Re-run the Claude install after the final manifests, run the Codex install,
   drive a session in a disposable project, and store every transcript under `evidence/` with the
   command, exit code and CLI version.

## Alternatives considered

- **One plugin per profile.** Rejected for this feature: it requires either restructuring `skills/`
  into per-profile directories, which breaks every installer path, or a build step that generates
  plugin directories from `profiles.json`, which is a new installer. The token-cost figure this
  feature records is what decides whether the split is ever worth it (D001).
- **Retire the installer in the same feature.** Rejected: the installer is the only Windows path
  and the only path anyone has used; retiring it before the plugin has evidence is the failure mode
  spec 042 was written to stop (D003).
- **Hand-write `hooks/hooks.json` with a different, "cleaner" hook set.** Rejected: any difference
  from the template is drift the gate would have to special-case; equivalence is the property that
  keeps three wirings honest (D002, D005).
- **Adopt more from `everything-claude-code`.** Rejected item by item in D004.

## Dependencies

- Claude Code CLI with `claude plugin marketplace add`, `claude plugin install`, `claude plugin
  details` (present on this Mac; version recorded in evidence).
- `codex-cli 0.152.1` with `codex plugin marketplace add` and `codex plugin add` (present).
- `bash` on the host for hooks (macOS/Linux; Windows is a Non-goal).
- No network, no new libraries, no changes to CI workflows (the existing `consistency.yml` runs
  `check-consistency.sh` and picks up the new check automatically).

## Risks

- **`agents/` is not discovered by convention.** Mitigation: T001 detects it before anything else
  is written; fallback is explicit directory keys, recorded in D001's amendment.
- **Non-content directories load into the plugin.** Mitigation: same spike; fallback is the
  loader's exclusion mechanism or, failing that, a recorded decision to move the manifests into a
  subdirectory whose `source` is a curated tree, which would reopen the layout question and stop
  this feature for a spec update.
- **Double firing when a project wires hooks manually and enables the plugin.** Not prevented by
  code; documented (FR-015). Throttled hooks self-limit; formatters are idempotent; guardrails
  block twice harmlessly.
- **Codex rejects the manifest.** Mitigation: FR-009 path, exact error recorded, AC-007 narrowed by
  decision, Codex remains first-class and the gap stays visible in `docs/KNOWN_DEBT.md`.
- **`claude plugin details` has no token-cost figure on this CLI version.** Mitigation: record the
  actual output and version; AC-005 becomes an open debt item with the version noted.
- **Consistency gate false positive on `hooks/hooks.json`.** The orphan-hook scan skips non-`.sh`/
  `.ps1` files, so `hooks.json` is not an orphan; verified by reading lines 208–216 of the checker.

## Test strategy

- **Unit:** two cases added to `scripts/check-consistency.test.sh`, following the existing
  `assert_case` pattern: `plugin-wiring-hook-removed` (exit 1, `[plugin-wiring]` in output) and the
  unmodified control case still passing.
- **Integration:** recorded CLI runs for both hosts (AC-003, AC-007) and the inventory and token
  cost (AC-004, AC-005).
- **E2E:** a session in a disposable project outside the repository, with the plugin installed and
  no `.claude/hooks/`, observing `/spec-create` and `/sdd` resolution and the `project-init-check`
  `SessionStart` message (AC-006). Executable first through `claude -p` in that directory; if the
  print mode does not surface hook messages, Manuel runs one interactive session and the transcript
  is pasted into evidence, named as a human check.
- **Manual:** read the rendered `docs/INSTALL.md` section and follow its four commands from a
  second terminal (AC-011).
- **Regression:** `scripts/check-consistency.sh` green on the final tree; `git diff --stat main --`
  on the installer files and `runner/` empty (AC-012).

## Rollback strategy

Delete the four new files and revert the three doc edits and the checker extension; nothing else
changed. An installed plugin is removed with `claude plugin uninstall sdd` and `codex plugin remove
sdd`; the marketplace with `claude plugin marketplace remove spec-driven-development`. No state of
ours is written anywhere: no manifest, no `.sdd-install.json` change, no settings edit. The
installer path is untouched throughout, so a rollback leaves every existing install exactly as it
was.

## PLAN verification checklist

- [x] The plan covers all acceptance criteria.
- [x] The plan avoids behavior outside the spec.
- [x] The Context budget section is filled (reading list + model routing), not left as placeholder.
- [x] Risks are documented.
- [x] Test strategy is documented.
- [x] Rollback strategy is documented.
- [x] SPEC.md status has been updated to `Ready`.
