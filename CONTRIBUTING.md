# Contributing

Thanks for considering a contribution. This repo has one unusual rule that
shapes everything else: **the framework is developed with its own workflow**.
Every non-trivial change carries a spec.

## Ground rules

1. **Features need a spec.** Create `specs/features/<NNN>-<kebab-name>/` with
   at least `SPEC.md`, `PLAN.md`, `TASKS.md`, `DECISIONS.md` (use
   `specs/_templates/`). Small safe fixes (typos, one-line bugs) can skip the
   ceremony — use judgment, and say so in the commit message.
   Check the highest existing `NNN` **including unmerged branches** before
   claiming a number.
2. **sh/ps1 parity.** Every hook and user-facing script ships as a
   `.sh` + `.ps1` pair with identical behavior. CI parses every `.ps1` on
   Windows and shellchecks every `.sh` — but behavioral parity is your job.
3. **Hooks never block by accident.** Advisory hooks exit 0 always, never
   perform network calls or installs, and degrade silently when they don't
   apply. Read `hooks/README.md` before writing one.
4. **Graphify stays optional.** Anything Graphify-aware must work (gracefully
   degraded) without the CLI installed.
5. **No consistency drift.** `profiles.json`, the on-disk artifacts, the
   settings templates, and the README counters/badges must agree.

## The merge gate

All of these must pass locally before you open a PR (CI runs them too):

```bash
bash scripts/check-consistency.sh        # manifest/disk/wiring/README alignment
bash scripts/check-consistency.test.sh   # the checker's own mutation suite
bash scripts/graphify.test.sh            # Graphify hooks + setup script (stubbed CLI)
```

If you changed counts (new skill/hook/template/profile), run
`bash scripts/check-consistency.sh --fix` to sync README markers and badges.

## Commit conventions

Conventional-commit style, one logical block per commit:
`feat(scope): …`, `fix(scope): …`, `docs(…): …`, `ci: …`, `test(…): …`.
Reference the spec in the body (e.g. "Spec 014"). Never mix unrelated
features in one commit.

## Dev setup

No dependencies beyond `bash`, `python3` (installer/harness), and optionally
`pwsh` for Windows-variant testing. `npx -y shellcheck -S error <files>` if you
don't have shellcheck installed. Do NOT run `install.sh` against your real
`~/.claude` while developing — use `--dry-run` or a scratch `--central-dir`.

## Reporting issues

Use the issue templates (bug / feature). For bugs in hooks or the installer,
include OS, shell, and the exact command + output — most hook bugs are
platform-specific.
