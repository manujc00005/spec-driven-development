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
6. **Adapters are additive.** SDD Core (the `specs/_templates/` artifacts, the
   workflow, the review gates) is provider-neutral; provider-specific packaging
   lives under `adapters/`. Never move or rename Claude adapter files
   (`skills/`, `agents/`, `hooks/`, the installers) to support another provider —
   a new adapter is a new `adapters/<provider>/` tree with its own `PARITY.md`
   and, if installable, a self-contained copy-only installer. Label anything not
   verified against the provider's real CLI as such. See
   [`docs/PROVIDER_ADAPTERS.md`](docs/PROVIDER_ADAPTERS.md).

## The merge gate

### Enable the pre-push hook first

Git does not pick up shipped hooks on its own. Once per clone:

```bash
git config core.hooksPath .githooks
```

`.githooks/pre-push` runs the fast half of the gate — `check-consistency.sh` plus the two quick
test suites, **about six seconds** — and refuses the push if any of it is red. The slow suites
(`check-consistency.test.sh` at ~86s, the installer tests at minutes) stay in CI on purpose: a
gate slow enough to be annoying gets bypassed with `--no-verify` every time, and then it protects
nothing.

This is not hypothetical hygiene. A skill once shipped with nine contract errors in its own
`SKILL.md`; CI caught it, but CI runs on push-to-`main`, so the baseline was already red on the
default branch — and while `check-consistency.sh` is red, **no `--autonomous` orchestration run
can start anywhere in this repo** (entry-gate condition 6 of `/sdd-orchestrate`). The gate was
documented right here and simply not run.

**Adding or editing a skill is the highest-risk change in this repo** for exactly that reason: a
`SKILL.md` must satisfy the contract schema (required keys, `category` enum, flow-list `outputs`,
the 400-character description cap), and none of that is visible by reading the file.

### The full gate

All of these must pass locally before you open a PR (CI runs them too):

```bash
bash scripts/check-consistency.sh        # manifest/disk/wiring/README alignment
bash scripts/check-consistency.test.sh   # the checker's own mutation suite
bash scripts/graphify.test.sh            # Graphify hooks + setup script (stubbed CLI)
bash scripts/skill-eval.test.sh          # skill-eval harness (stubbed runner, no model calls)
```

`skill-eval.test.sh` is **not** wired into `.github/workflows/consistency.yml` — that file is out
of scope for spec 022 (FR-010), so this one is local-only until a follow-up adds it.

If you changed counts (new skill/hook/template/profile), run
`bash scripts/check-consistency.sh --fix` to sync README markers and badges.

### Changing a discipline or mindset skill

Skills are not prose — they are the product. A PR that changes the **content** of a skill whose
`## SDD Contract` declares `category: mindset` must include an `evals/results/` file produced
**after** the change:

```bash
export SKILL_EVAL_RUNNER="claude -p --setting-sources '' --model <model-id>"
bash scripts/skill-eval.sh <skill> --reps 5
```

The runner must isolate the call from your own agent configuration and pin a model; the harness
refuses to run otherwise. `--setting-sources ''` keeps your plugins, hooks, memory and saved
settings out of **both** arms, and `--model` makes the identifier in the result file traceable to
the command that produced it rather than a claim about it. For Codex, the equivalent is
`codex exec --ignore-user-config --ephemeral --model <model-id>`. A runner the harness does not
recognize needs `--allow-unisolated`, which runs but stamps the result as un-isolated.

> **This gate is not fully in force yet.** Every scenario currently in `evals/scenarios/` is
> marked **superseded** — the corpus describes repository state the model cannot see, so a sweep
> run against it produces tallies that look plausible and mean nothing (spec 022, D010). Until
> spec 023 lands a valid corpus, a result file attached to a PR must come from a scenario that
> meets the **self-contained** rule in `evals/README.md` — write one for the skill you are
> changing rather than reusing the superseded file. If you cannot, say so in the PR instead of
> attaching a result that is not evidence.

Commit the result file and set its `manually-read` field to YES only after reading every
response. Three things make a result worth reading:

- **The control arm is mandatory.** A `NO-BASELINE-FAILURE` verdict means the skill has no
  demonstrated problem to solve — do not read the treatment arm as a success.
- **Split results are `INCONCLUSIVE`, never a pass.** When guidance lands, reps converge.
- **A result without a model identifier is not evidence.**

The static half of this (description length and shape, `SKILL.md` size) is enforced by
`check-consistency.sh` and needs nothing extra from you. See `evals/README.md` for what those
checks do and do not prove.

## Commit conventions

Conventional-commit style, one logical block per commit:
`feat(scope): …`, `fix(scope): …`, `docs(…): …`, `ci: …`, `test(…): …`.
Reference the spec in the body (e.g. "Spec 014"). Never mix unrelated
features in one commit.

## Dev setup

No dependencies beyond `bash`, `python3` (installer/harness), and optionally
`pwsh` for Windows-variant testing. The one exception is `runner/` (spec 040),
maintainer tooling that is not installed anywhere. The package is `sdd_runner`; its `claude` backend needs
`claude-agent-sdk`, declared as an **optional** dependency in `runner/pyproject.toml`
and imported lazily. Its own suite is stdlib only —
`PYTHONPATH=runner python3 -m unittest discover -s runner/tests -t runner` — so the
framework, its installers and every existing suite work unchanged on a machine that
has none of it. `npx -y shellcheck -S error <files>` if you
don't have shellcheck installed. Do NOT run `install.sh` against your real
`~/.claude` while developing — use `--dry-run` or a scratch `--central-dir`.

## Reporting issues

Use the issue templates (bug / feature). For bugs in hooks or the installer,
include OS, shell, and the exact command + output — most hook bugs are
platform-specific.
