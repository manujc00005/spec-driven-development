# Tasks: Plugin distribution

<!-- Each task line gains a `Verify:` clause after `Covers:`: the criterion anyone checks to call
     the task done. It may be an executable command or an observable human check — nothing in the
     framework executes it; it is text for a human or an agent to act on, not a runner input. A
     human check must name who checks and against what. -->

<!-- CLOSING A TASK THAT WAS NOT PERFORMED: keep the tick AND state how it was closed on the line
     below, with one of DEFERRED (-> docs/KNOWN_DEBT.md id), SKIPPED (reason) or RESOLVED (where). -->

## Phase 1: Preparation

- [x] T001 - Spike the two open assumptions: write minimal `.claude-plugin/plugin.json` (name `sdd`)
  and `.claude-plugin/marketplace.json` (`source: "./"`), run `claude plugin marketplace add
  "$(pwd)"`, `claude plugin install sdd@spec-driven-development` and `claude plugin details sdd`,
  and save the three transcripts as `evidence/SPIKE.md` with CLI version and exit codes. Read the
  inventory for (a) agents present and (b) anything from `runner/`, `scripts/`, `specs/`, `evals/`,
  `adapters/`, `docs/`. Amend D001 with the two answers. Covers: AC-003, AC-004. Verify:
  `evidence/SPIKE.md` exists, shows exit 0 for all three commands, and D001 carries an "Observed"
  paragraph stating both answers with the inventory lines quoted.

## Phase 2: Implementation

- [x] T002 - Finalise `.claude-plugin/plugin.json`: `name` `sdd`, `version` `0.1.0`, `description`,
  `author`, `repository`, `license` `MIT`, `keywords`; component directory keys only if T001 showed
  they are needed. Covers: AC-001. Verify: `python3 -c 'import json;d=json.load(open(".claude-plugin/plugin.json"));assert d["name"]=="sdd"'`
  exits 0 and `grep -cE '"(spec-create|deep-reasoner|git-guardrails)"' .claude-plugin/plugin.json`
  prints 0.
- [x] T003 - Finalise `.claude-plugin/marketplace.json`: marketplace `spec-driven-development`, owner,
  one plugin entry `sdd` with `source` `./`, description, category `workflow`. Covers: AC-001.
  Verify: `python3 -c 'import json;d=json.load(open(".claude-plugin/marketplace.json"));assert d["name"]=="spec-driven-development" and d["plugins"][0]["name"]=="sdd" and d["plugins"][0]["source"]=="./"'`
  exits 0.
- [x] T004 - Create `.codex-plugin/plugin.json` with the same identity, `"skills": "./skills/"`, and
  an `interface` block (displayName, shortDescription, category, capabilities `["Instructions"]`).
  Covers: AC-001, AC-007. Verify: `python3 -c 'import json;d=json.load(open(".codex-plugin/plugin.json"));assert d["name"]=="sdd" and d["skills"]'`
  exits 0.
- [x] T005 - Create `hooks/hooks.json` by transcribing the `hooks` object of
  `settings.template.sh.json` unchanged except each command prefix rewritten from
  `bash ${CLAUDE_PROJECT_DIR}/.claude/hooks/` to `bash "${CLAUDE_PLUGIN_ROOT}/hooks/` (closing quote
  after `.sh`), plus a top-level `description`. No hook script is edited. Covers: AC-002. Verify:
  `python3` one-liner loads both files and asserts the sorted list of
  `(event, matcher, basename(command), timeout)` tuples is identical; `git status --short hooks/`
  shows only `?? hooks/hooks.json`.
- [x] T006 - Extend `scripts/check-consistency.sh`: call `check_settings_wiring("hooks/hooks.json")`
  after the two template calls, and add a `plugin-wiring` check that loads `hooks/hooks.json` and
  `settings.template.sh.json` as JSON and errors with `[plugin-wiring]` when the multiset of
  `(event, matcher, hook-name, timeout)` differs, naming the first differing tuple. Update the file
  header comment (line 4–6) to mention the third wiring. Covers: AC-002, AC-008. Verify:
  `bash scripts/check-consistency.sh` prints the pass line on the clean tree; after
  `python3 - <<<'...'` removes one hook entry from a temp copy of `hooks/hooks.json`, the checker
  exits 1 with `[plugin-wiring]` in its output.
- [x] T007 - Add two lines to the "Security checklist" list in `skills/security-review/SKILL.md`,
  after "Dependencies or config changes do not introduce obvious risks.": one on running the
  ecosystem's dependency audit and committing the lockfile when a dependency is added or bumped;
  one on a newly integrated library's licence being compatible with the project's distribution.
  Covers: AC-009. Verify: `git diff --numstat main -- skills/security-review/SKILL.md` shows `2 0`,
  and `grep -c -iE 'lockfile|licen[cs]e' skills/security-review/SKILL.md` prints 2.
  **Observed:** `git diff --numstat` shows `3 1`, not `2 0`. The extra `1 1` is D009's repoint of
  `agents/README.md` → `docs/AGENTS.md` on the delegation line, not a checklist change; the two
  checklist lines are pure additions.
- [x] T008 - Add one line to the "Review checklist" list in `skills/qa-review/SKILL.md`, after "Is
  manual testing needed?": whether any new `TODO`/`FIXME` lacks a reference to a spec, task or
  ticket. Covers: AC-009. Verify: `git diff --numstat main -- skills/qa-review/SKILL.md` shows
  `1 0`, and `grep -c 'TODO' skills/qa-review/SKILL.md` prints 1.
- [x] T009 - Add an "Install as a plugin" section to `docs/INSTALL.md` immediately after the title
  and intro (before "Provider adapters"), with the two Claude commands and the two Codex commands,
  the statement that Windows hooks stay on the installer for now, and the double-wiring warning.
  Covers: AC-011. Verify: `grep -n '^## Install as a plugin' docs/INSTALL.md` prints a line number
  lower than that of `^## Provider adapters`, and `grep -c -E 'twice|Windows' docs/INSTALL.md`
  prints at least 2 within the new section.
- [x] T010 - In `README.md`, make the Quickstart (line ~234) and Installation (line ~571) sections
  open with the plugin path linking to `docs/INSTALL.md#install-as-a-plugin`, keeping the installer
  commands below as the alternative. Add one Unreleased line to `CHANGELOG.md` and one sentence to
  `hooks/README.md` naming `hooks/hooks.json` as the plugin wiring. Covers: AC-011. Verify:
  `grep -c 'install-as-a-plugin' README.md` prints at least 2; `grep -c '044' CHANGELOG.md` prints
  at least 1; `grep -c 'hooks.json' hooks/README.md` prints at least 1; `bash scripts/check-consistency.sh`
  still passes (README counts untouched).

## Phase 3: Tests

- [x] T011 - Add two cases to `scripts/check-consistency.test.sh` after the FR-007 case: a fresh copy
  with one hook entry removed from `hooks/hooks.json` must fail with `[plugin-wiring]`; the clean
  control case already present must still pass. Covers: AC-008. Verify:
  `bash scripts/check-consistency.test.sh` reports both new cases as PASS and zero FAIL overall.
- [x] T012 - Re-run the Claude Code path against the final manifests: `claude plugin marketplace
  update spec-driven-development` (or remove and re-add), `claude plugin install
  sdd@spec-driven-development`, `claude plugin details sdd`. Save `evidence/CLAUDE_INSTALL.md`
  (commands, exit codes, CLI version) and `evidence/INVENTORY.md` (the details output) and
  `evidence/TOKEN_COST.md` (the projected token cost line with the CLI version, or the literal
  absence of one). Covers: AC-003, AC-004, AC-005. Verify: skills and agents counts in
  `evidence/INVENTORY.md` equal the `count:skills-total` and `count:agents-total` markers in
  `README.md`, and `grep -cE 'runner/|scripts/|specs/|evals/|adapters/|docs/' evidence/INVENTORY.md`
  prints 0.
- [x] T013 - Run the Codex path: `codex plugin marketplace add "$(pwd)"`, `codex plugin add
  sdd@spec-driven-development`, `codex plugin list`. Save `evidence/CODEX_INSTALL.md` with exit
  codes and `codex --version`. If any command fails, record the exact error there and write the
  narrowing decision D009 before ticking. Covers: AC-007. Verify: `evidence/CODEX_INSTALL.md` shows
  exit 0 for add and list, or shows the error verbatim and `DECISIONS.md` contains D009 narrowing
  AC-007.
- [x] T014 - Drive a session in a disposable project: `d=$(mktemp -d) && cd "$d" && git init -q`
  (no `.claude/`), then `claude -p "Run /sdd and stop after listing what it would do"` and a second
  `claude -p "Run /spec-create for a throwaway feature and stop after naming the folder it would
  create"`, capturing stdout and stderr. Save `evidence/E2E_SESSION.md`. If print mode does not
  surface the `project-init-check` message, Manuel runs one interactive session in that directory
  and pastes the banner and the two skill responses, labelled as a human check. Covers: AC-006.
  Verify: `evidence/E2E_SESSION.md` shows both skills responding as themselves (not "unknown
  command") and contains the `project-init-check` wording ("CONSTITUTION" appears), and states that
  `ls -a "$d"` showed no `.claude/hooks`.

## Phase 4: Review

- [x] T015 - Confirm the contract diff is empty and the gate is green on the final tree:
  `git diff --stat main -- runner/ install.sh install.ps1 install-all.sh install-all.ps1
  link-project.sh link-project.ps1 scripts/update.sh scripts/update.ps1 scripts/wire-hooks.sh
  scripts/wire-hooks.ps1 profiles.json` prints nothing, `bash scripts/check-consistency.sh` passes,
  and D004 lists every rejected `everything-claude-code` item with a reason.
  Covers: AC-010, AC-012. Verify: the three commands' outputs pasted into `evidence/FINAL_GATE.md`, the diff block
  empty, and `grep -c '^- \*\*' DECISIONS.md` in the D004 region is at least 10.
