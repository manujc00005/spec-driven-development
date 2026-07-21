# SPEC — 016 Install hooks/lib in profile mode

## Problem

In profile-filtering mode (the default — a profile is always resolved), both
installers copy hook scripts by base name only:

- `install.sh` (~L446): `for hook_file in "$REPO_ROOT/hooks/$hook_name".*`
- `install.ps1` (~L423): `Get-ChildItem -Filter "$hookName.*"`

Neither ever copies `hooks/lib/`. Five shipped `.sh` hooks source
`lib/claude-json.sh` (`git-guardrails`, `sdd-spec-guard`,
`java-build-test-guard`, `maven-compile`, `spring-config-guard`), so on every
fresh install they crash with exit 1. Claude Code treats PreToolUse exit 1 as
a non-blocking error, so **git-guardrails silently allows every command it was
designed to block** (`git push --force`, `git reset --hard`, …). Found by the
2026-07-21 SDD+Graphify integration audit; worked around manually on this
machine by copying the file into `~/.claude-config/hooks/lib/`.

Not affected: `link-project.sh` (symlinks the whole hooks dir), the
non-filtered `copy_tree_safely` branch (dead code in practice), and the
graphify-* hooks (self-contained, no `lib/` dependency).

## Acceptance criteria

- **AC-01** After `install.sh --profile <any>` into a fresh central dir,
  `<central>/hooks/lib/claude-json.sh` exists.
- **AC-02** From that fresh install, `git-guardrails.sh` exits **2** for
  `{"tool_name":"Bash","tool_input":{"command":"git push --force"}}` on stdin
  and **0** for a benign command — verified by an automated regression test.
- **AC-03** `hooks/lib/` files follow the same safety semantics as every other
  copied file: new → copy, identical → no-op, differs → skip unless
  `--force`/`-Force` (backup first). Re-running is idempotent.
- **AC-04** `install.ps1` receives the equivalent fix (copy `hooks\lib\`
  recursively in the profile branch) — code parity; runtime verification on
  Windows is deferred to the existing Windows spot-check backlog.
- **AC-05** Regression test lives in `scripts/install.test.sh` following the
  existing self-test conventions (hermetic tmp dir, pass/fail counters,
  non-zero exit on failure).

## Out of scope

- `java-build-test-guard` multi-module wrapper detection (separate decision —
  resolved in the target repo by adding a root `mvnw`).
- `setup-graphify.sh` early-exit-on-scope-conflict (separate P1).
- Any commit/push — working tree only; branch handling is the user's call
  (note: `feat/adopt-graphify-skill` is currently checked out with unrelated
  in-flight changes).
