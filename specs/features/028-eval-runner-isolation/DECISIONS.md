# Decisions: eval-runner-isolation

## Decision log

### D001 - Missing isolation is a hard error, not a warning

**Date:** 2026-08-06

**Status:** Accepted

**Context:** `skill-eval.sh` currently accepts any runner string. Adding a check raises the
question of what it does when the check fails: refuse to run, or warn and continue. Raised as
blocking question Q2 during spec creation.

**Decision:** Refuse. Exit non-zero before any model call, naming the exact missing flag. The
`--allow-unisolated` opt-out (D003) is the only path past it.

**Reasoning:** A warning is read once and then ignored, and — the decisive point — the artifact it
produces is byte-for-byte indistinguishable from one produced under real isolation. The whole
purpose of this feature is that a reviewer can tell the two apart without trusting the operator.
A warning preserves exactly the failure being removed. Maintainer decision.

**Consequences:** A contributor with a habitual unpinned runner is blocked until they update it.
The error message must therefore carry the corrected invocation, not just the complaint.

---

### D002 - Codex is enforced on the same footing as Claude Code

**Date:** 2026-08-06

**Status:** Accepted

**Context:** Codex isolation flags (`--ignore-user-config --ephemeral`) come from a reviewed
external implementation and are unverified here: the Codex CLI is not installed on the
maintainer's current machine. The alternative was to enforce Claude Code only and route Codex
through the opt-out until someone could run it. Raised as scope question Q3.

**Decision:** Codex is a recognized provider in the table from day one, with the same hard
enforcement as Claude Code. Codex is first-class across this framework — `adapters/codex/`,
profile support, prompt parity — and the eval harness does not treat it as an exception.

**Reasoning:** Maintainer decision, stated as a standing project rule ("Codex siempre entra en
todo"). The concern that shipping an unverified isolation claim reproduces the problem in a new
place was raised and is addressed by FR-011/D008 — verification blocks `Done`, not `Ready` —
rather than by narrowing scope.

**Consequences:** The feature cannot close until someone installs the Codex CLI and runs T013. If
the real flags differ from the table, the row is corrected; the decision to cover Codex is not
reopened.

---

### D003 - The opt-out is a CLI flag, not an environment variable

**Date:** 2026-08-06

**Status:** Accepted

**Context:** FR-003 requires an escape hatch so an unrecognized provider never hard-blocks a
contributor. It could be `--allow-unisolated` on the command line or `SKILL_EVAL_ALLOW_UNISOLATED`
in the environment.

**Decision:** A CLI flag, `--allow-unisolated`. Named after the `--allow-unmetered` flag in the
reference implementation, which solves the structurally identical problem for cost metering.

**Reasoning:** An environment variable is exported once and then silently applies to every
subsequent run, including ones the operator forgot it was set for — the same
set-and-forget failure as a warning (D001). A flag is per-run, visible in shell history, and shows
up in the command a reviewer reads.

**Consequences:** Anyone scripting a sweep repeats the flag per invocation. Acceptable, and
arguably the point.

---

### D004 - Under the opt-out, `SKILL_EVAL_MODEL` stays legal but is recorded as operator-asserted

**Date:** 2026-08-06

**Status:** Accepted

**Context:** FR-005 requires the model identifier to be derivable from the executed command. An
unrecognized runner has no command to derive it from — there is nothing to parse. This is not a
hypothetical: the entire 240-line `skill-eval.test.sh` suite drives a stub runner
(`SKILL_EVAL_RUNNER="bash $stub" SKILL_EVAL_MODEL="stub-model"`), which is by construction
unrecognized and unpinned.

**Decision:** Under `--allow-unisolated`, `$SKILL_EVAL_MODEL` is accepted as the identifier of
record, and the result file states the provenance explicitly: isolation `NONE`, model
`operator-asserted`. For a recognized provider the pin is mandatory and the env variable may only
confirm it.

**Reasoning:** The guarantee that matters is *legibility*, not universal enforcement. A reader
must be able to tell a verified identifier from an asserted one; forbidding assertion outright
would break the test suite and every legitimate wrapper runner without making any result more
trustworthy. This also keeps the change from cascading into a rewrite of the test harness.

**Consequences:** Two classes of result file now exist. `evals/README.md` must say that an
un-isolated result is a weaker artifact, and reviewers must treat it as such.

---

### D005 - Tokenize the runner with `xargs`, never a second `eval`

**Date:** 2026-08-06

**Status:** Accepted

**Context:** Detecting flags requires splitting the runner string into arguments while respecting
quotes. The string is already `eval`'d at `skill-eval.sh:168`, so `eval "set -- $RUNNER"` was the
obvious shortcut.

**Decision:** Split with `printf '%s' "$RUNNER" | xargs -n1`. An unmatched quote makes `xargs`
fail, which becomes a refusal.

**Reasoning:** The spec's security NFR forbids interpolating the runner string into a second shell
context. `xargs` parses quotes without being a shell, so it costs nothing and keeps the executing
`eval` as the single place the string is expanded. Substring matching was the other alternative
and is wrong: it reports `--model` as a pin when the text merely appears inside a quoted prompt
fragment.

**Consequences:** `xargs` quote handling diverges from the shell's for backslashes and `$`
expansion, so an exotic runner can be falsely refused. The opt-out (D003) is the escape, and the
limit is documented.

---

### D006 - The provider table lives in `skill-eval.sh`, not in `adapters/`

**Date:** 2026-08-06

**Status:** Accepted

**Context:** The spec's maintainability NFR says provider knowledge should stay consistent with
`adapters/`, which raised the question of whether the flag table belongs there.

**Decision:** Keep the table in `scripts/skill-eval.sh`.

**Reasoning:** `adapters/codex/` contains prompts, an installer, and parity documentation — no
runtime data consumed by scripts. A table read by exactly one bash script, in a directory that is
never installed into a user project, does not become more discoverable by moving into a tree with
different conventions. Revisit if a second script needs the same table.

**Consequences:** If the runner registry from the deferred cost-metering spec lands, both it and
this table describe providers and must be unified then.

---

### D007 - `--setting-sources ""` does exclude user-level `CLAUDE.md`

**Date:** 2026-08-07

**Status:** Accepted — verified

**Context:** `evals/README.md:142-146` named user-level `CLAUDE.md` as the specific residual
contamination the sandbox does not remove. `--setting-sources ""` is documented as controlling
settings sources; whether it also suppresses user memory was unobserved and version-dependent.
FR-008's wording depends on the answer.

**Decision:** On Claude Code **2.1.223**, `--setting-sources ""` suppresses user-level
`~/.claude/CLAUDE.md`. The README's "stated, not solved" paragraph is replaced rather than merely
narrowed.

**Reasoning:** Measured, not assumed. `~/.claude/CLAUDE.md` did not exist on the test machine, so
a canary was created containing a single instruction — end every response with `ZZQX-CANARY-7` —
and the same prompt was run twice from an empty working directory:

| Arm | Command | Canary in response |
|---|---|---|
| control | `claude -p --model claude-sonnet-5` | **yes** |
| treatment | `claude -p --setting-sources '' --model claude-sonnet-5` | **no** |

The control arm is what makes this evidence: it proves the canary was loadable in the first place,
so the treatment arm's silence is suppression rather than an ineffective probe. Same discipline
the harness itself enforces.

Two earlier probe designs failed and are recorded so nobody repeats them. Pointing
`CLAUDE_CONFIG_DIR` at a scratch directory logs the CLI out — that directory holds credentials as
well as memory, so it cannot be used to fake a config root. Running the sweep on this machine as
originally planned would also have proved nothing: there was no user `CLAUDE.md` to leak, so both
arms would have come back clean and the absence of contamination would have been misread as
isolation working.

**Consequences:** FR-008 can state that the operator's settings, plugins, hooks and user memory
are all excluded. What remains outside the flag's reach is unmeasured and must not be claimed as
covered: environment variables, the `--model` default when unpinned (handled separately by the pin
gate), and anything a wrapper script injects. The result is specific to CLI 2.1.223 and is a dated
observation, not a guarantee — the README must say which version it was measured on.

The canary file was created and deleted inside one command with an `EXIT` trap, and its absence
was verified afterwards. An orphaned `~/.claude/CLAUDE.md` would have silently applied to every
later session on this machine.

---

### D010 - A bare `VAR=value` prefix is a shell assignment, not the provider

**Date:** 2026-08-07

**Status:** Accepted

**Context:** Provider detection skipped `env` and its arguments but nothing else, so the first
token of `FOO=1 claude -p --setting-sources '' --model m` resolved to `FOO=1`. The runner is
`eval`'d, so that invocation is valid shell and genuinely isolated — yet it was refused as
unrecognized, and the only way forward was `--allow-unisolated`, which stamps a clean run as a
weaker artifact. Found in `/spec-review`; a strict reading of AC-002 makes it a violation.

**Decision:** Skip leading tokens matching `[!-]*=*` before resolving the command, whether or not
an `env` preceded them.

**Reasoning:** The alternative — document it and let the operator write `env FOO=1 claude …` — puts
the burden on someone who has no way to guess the rule from the error message. The `[!-]` prefix
keeps an option like `--model=x` out of the branch, so `--model=x claude` still resolves to the
unrecognized `--model=x` and fails closed rather than silently finding a provider behind it. Both
directions are pinned by tests.

**Consequences:** Detection now has two skip rules instead of one. A token that is genuinely a
command containing `=` before any dash would be skipped, which is not a plausible executable name.

---

### D011 - Spec updated: Codex verification becomes declared debt instead of a close gate

**Date:** 2026-08-07

**Status:** Accepted

**Context:** FR-011/AC-011 forbade reaching `Done` on an unverified Codex flag table, and
`/spec-close` correctly refused on that basis. The Codex CLI is not installed on the maintainer's
machine and installing it is out of scope for this session, while every other acceptance criterion
is met and verified. Two ways forward were put to the maintainer: install Codex and close properly,
or downgrade the criterion and close with the debt declared. **The maintainer chose the second.**

**Decision:** FR-011 and AC-011 are downgraded — verification moves from a close-blocking gate to
a tracked debt item (DEBT-001 in `docs/KNOWN_DEBT.md`). Two things are explicitly **not** changed:
D002 stands, so Codex remains enforced on the same footing as Claude Code; and the flag table
ships as written, so the harness still refuses a Codex runner missing those flags.

Added alongside it: FR-012/AC-012, requiring the Codex refusal message to say the flag set is
unverified and to name `--allow-unisolated`.

**Reasoning:** Declaring debt is legitimate; closing over an unmet criterion without saying so is
not — and it would be a strange thing for *this* feature to do, given it exists to stop unverified
claims being recorded as evidence. The downgrade is therefore written into the spec, decided here,
and registered in a document outside the feature folder, so it survives the folder being archived.

FR-012 was **not requested by the maintainer.** It was added because the cost of the downgrade —
a wrong flag hard-blocking the first Codex user — is cheap to soften and expensive to leave. The
gate still fails closed; the operator just gets an error that explains itself. Drop it if the extra
hedge in the message is not wanted.

**Consequences:** T013 becomes `[DEFERRED]` and no longer covers AC-011. T017 is added for FR-012
and is the only implementation work left before close. `PLAN.md` risk R2 and its dependency on the
Codex CLI are restated. `docs/KNOWN_DEBT.md` is new and also absorbs the identical unverified-CLI
debt from spec 019, which until now was visible only inside that spec's open questions.

---

### D008 - Verified Codex isolation flags

**Date:** 2026-08-06

**Status:** Proposed — blocked on T013

**Context:** D002 ships the Codex row enforced but unverified. FR-011 requires a real invocation
before the feature reaches `Done`.

**Decision:** Pending. Record the exact accepted flag spellings from a real `codex exec` run,
including the pin flag (`--model` vs `-m`).

**Reasoning:** Enforcing a flag set that a provider does not accept would turn the gate into a
hard block on a working runner — the opposite of the intent.

**Consequences:** Requires installing the Codex CLI. This is the dependency most likely to hold
the spec in `In Review`.

---

### D009 - A sentinel token is appended before tokenizing, because `xargs` drops a trailing empty argument

**Date:** 2026-08-06

**Status:** Accepted

**Context:** D005 chose `xargs -n1` to tokenize the runner string. Probing it on the target shell
(bash 3.2.57, macOS) showed an empty argument is preserved **only when it is not last**:

```
$ printf '%s' "claude --setting-sources '' -p" | xargs -n1   →  claude / --setting-sources / <empty> / -p
$ printf '%s' "claude --setting-sources ''"    | xargs -n1   →  claude / --setting-sources
```

`export SKILL_EVAL_RUNNER="claude -p --model x --setting-sources ''"` is a natural way to write the
runner, and under the naive implementation its isolation flag is invisible — a correctly isolated
runner refused. That is risk R4 landing on the single most common invocation rather than on an
exotic one.

**Decision:** Append a sentinel token (`__SDD_RUNNER_EOL__`) before piping to `xargs` and strip the
last line afterwards. The empty argument is then never trailing and survives.

**Reasoning:** Considered and rejected: (a) documenting "do not put the isolation flag last" —
a trap that fires silently at the moment the operator is most confident; (b) a tail regex on the
raw string as a fallback — two parsers disagreeing about the same input is how the substring bug
this feature exists to avoid gets reintroduced. The sentinel keeps one parser and one code path.

**Consequences:** A runner string containing the literal text `__SDD_RUNNER_EOL__` as its final
argument would lose it. Not defended against — it is not a plausible runner.

Verified in the same probe: a flag name inside a quoted prompt fragment (`-p 'use --model here'`)
tokenizes as one token, so exact-match comparison already handles that SPEC edge case with no
extra code. An unmatched quote makes `xargs` exit non-zero, which becomes a refusal as intended.
