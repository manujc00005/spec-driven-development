# Feature Spec: mindset-reminder-hook

## Status

In Review

## Problem

The mindset skills (spec 013) are declared **"always in effect"** but delivered through a
**model-invoked** channel. A skill only enters context if the assistant chooses to call it. So the
claim and the mechanism disagree — the same shape as the defect spec 034 just fixed in the install
manifest: a record asserting a state the delivery mechanism does not guarantee.

The adopter's global instructions say, literally:

> Siempre en efecto: `/scope-keeper` (diff mínimo), `/communicator`, `/stopper`, `/honest-advisor`.

That line is a **pointer**, not content. If the skill file is never loaded, none of its ten rules
are in context — only the one-line summary in `CLAUDE.md`.

Measured, not assumed: across the entire spec 034 implementation session — 25 tasks, ~1.300 lines
changed, dozens of edits — **`/scope-keeper` was never invoked once.** Scope discipline did hold
(an out-of-scope `usage()` fix was flagged rather than smuggled in, and D011 was recorded instead
of quietly widening the diff), but it came from the `CLAUDE.md` pointer and general behaviour, not
from the skill's rules. The rules were never in context at the moment they applied.

`scope-keeper`'s own description names its trigger precisely: *"Use before your first edit."* That
is a deterministic moment the harness can observe. Nothing observes it today.

## Goal

The mindset rules that claim to be always-on are actually present at the moment they apply,
without depending on the assistant choosing to load them, and without paying their token cost on
turns that never edit anything.

## Non-goals

- **No enforcement.** A mindset is judgement, not a mechanical rule. The hook reminds; it never
  blocks an edit and never changes an exit code. Anything else would make `Edit` fail on a
  judgement call.
- **No new skill, and no change to the rules themselves.** `skills/scope-keeper/SKILL.md` is the
  single source of the rules; this feature changes only *when they reach context*.
- **No inlining the full rule set into `CLAUDE.md`.** 641 words on every turn, duplicated from the
  skill file — the duplication would drift, which is the failure this framework keeps fixing.
- **No hook for every mindset skill.** `communicator` fires at message-writing time and `stopper`
  at destructive-action time; neither has a clean `PreToolUse` seam. Only `scope-keeper` has one.
  The others stay as they are.
- **No change to the model-invoked path.** `/scope-keeper` remains callable and the skill keeps its
  description; the hook is additive.

## Users / Actors

- **Any Claude Code session that edits files**, with or without SDD — the hook lives in the
  harness, not the spec lifecycle.
- **Adopters on both platforms**: the hook ships as `.sh` and `.ps1` like every other shipped hook.
- **`check-consistency.sh`**, which validates that every hook declared in `profiles.json` exists on
  disk in both forms.

## Current behavior

- `scope-keeper` is a `category: mindset` skill, loaded only when the assistant calls it.
- The global `CLAUDE.md` line is a pointer with a three-word gloss (`diff mínimo`).
- `settings.template.json` already wires two `PreToolUse` matchers (`Bash`, `Grep|Glob`), so the
  seam and the precedent both exist.
- `hooks/graphify-scan-reminder.sh` is the working exemplar: consumes the tool-call JSON, emits
  `{"systemMessage": ...}`, throttles via a marker file, honours an env kill-switch, exits 0 always.

## Desired behavior

- Before the **first** `Edit`/`Write`/`NotebookEdit` of a session, the session receives the
  load-bearing scope rules as a system message.
- Subsequent edits in the same session are silent — the reminder is a session-opening act, not a
  per-edit nag.
- Turns that never edit pay nothing.
- The hook never blocks, never fails an edit, and is disabled by one env var.
- The adopter's `CLAUDE.md` carries the two or three rules that do the most work **as text**, so
  that behaviour degrades gracefully when the hook is absent (another machine, a bare install)
  instead of degrading to nothing.

## Functional requirements

- FR-001: `hooks/scope-keeper-reminder.sh` and `hooks/scope-keeper-reminder.ps1` emit a
  `systemMessage` carrying the load-bearing scope rules, on `PreToolUse` for `Edit|Write|NotebookEdit`.
- FR-002: the reminder fires **once per session**. The session is identified from the hook's stdin
  JSON (`session_id`); when that field is absent the hook falls back to a time-throttle rather than
  firing on every edit.
- FR-003: the hook **always exits 0** and never emits a blocking verdict, whatever happens
  internally — including a malformed or empty stdin payload.
- FR-004: `SDD_SCOPE_REMINDER=0` disables it.
- FR-005: the message names the skill (`/scope-keeper`) so the full rule set is one call away, and
  states that it is a reminder, not a gate.
- FR-006: the hook is declared under the `core` profile in `profiles.json`, so every adopter gets
  it, SDD workflow or not.
- FR-007: both `settings.template.json` (PowerShell) and `settings.template.sh.json` (bash) wire it
  with a `PreToolUse` matcher of `Edit|Write|NotebookEdit`, matching the existing entries' shape,
  timeout and `statusMessage` conventions.
- FR-008: the marker file lives outside the project tree (temp dir), so the hook never writes into
  the adopter's repository and never appears in their `git status`.
- FR-009: the adopter-facing `CLAUDE.md.example` documents the hook and its kill-switch.

## Non-functional requirements

- **Performance**: the hook runs before every matching tool call. It must do no filesystem work
  beyond one marker `stat`/`touch`, and must complete well inside the 5s timeout the existing
  entries use.
- **Security**: stdin is untrusted tool-call JSON. The hook must not `eval` it, must not interpolate
  any field into a shell command, and must treat a missing or malformed payload as "no session id"
  rather than erroring. The marker path must be built from a sanitised session id — never used raw
  as a path component.
- **Observability**: the message must be identifiable at a glance (`[scope-keeper]` prefix) so an
  adopter can tell where it came from and how to silence it.
- **Maintainability**: the rules live in `skills/scope-keeper/SKILL.md`. The hook carries a
  deliberately short excerpt, and a test asserts that the excerpt's claims still exist in the skill,
  so the two cannot drift silently.

## API / Interface changes

New hook, wired as:

| Event | Matcher | Hook |
|---|---|---|
| `PreToolUse` | `Edit\|Write\|NotebookEdit` | `scope-keeper-reminder` |

New environment variable: `SDD_SCOPE_REMINDER=0` to disable. No CLI surface changes.

## Data model changes

None. One marker file under the system temp dir, named from the session id.

## Edge cases

- **Empty or malformed stdin** → no session id; fall back to the time throttle; exit 0.
- **`session_id` absent from the payload** → same fallback. The hook must not assume the field.
- **A session id containing path separators or `..`** → sanitised to `[A-Za-z0-9_-]` before use as a
  filename; a value that sanitises to empty falls back to the time throttle.
- **Temp dir not writable** → skip the marker, emit the message, exit 0. Never fail an edit because
  a nudge could not be throttled.
- **Two edits racing in the same session** → at worst the message appears twice; it is a reminder,
  so a duplicate is harmless and must not be prevented with locking.
- **The hook is installed but the skill is not** (someone pruned it) → the message still stands on
  its own; it must not depend on the skill file existing.
- **Very long sessions** → still one reminder. Re-nagging is the failure mode this replaces.

## Acceptance criteria

- AC-001: given a `PreToolUse` payload for `Edit` with a `session_id`, the hook prints a JSON object
  containing `systemMessage`, and exits 0.
- AC-002: a second invocation with the **same** `session_id` prints nothing and exits 0.
- AC-003: an invocation with a **different** `session_id` prints the message again.
- AC-004: with `SDD_SCOPE_REMINDER=0`, the hook prints nothing and exits 0.
- AC-005: with empty stdin, malformed JSON, or no `session_id`, the hook exits 0 and never errors.
- AC-006: a `session_id` of `../../etc/passwd` creates no file outside the temp dir, and the hook
  still exits 0.
- AC-007: the hook writes nothing inside the project tree — `git status` is unchanged after a run.
- AC-008: the emitted message contains `[scope-keeper]`, names `/scope-keeper`, and states it is a
  reminder rather than a gate.
- AC-009: the excerpt in the hook is corroborated by `skills/scope-keeper/SKILL.md` — a test fails
  if the skill no longer contains the claims the hook asserts.
- AC-010: `scope-keeper-reminder` is declared in `profiles.json` under `core`, exists as both `.sh`
  and `.ps1`, and `check-consistency.sh` stays green.
- AC-011: both settings templates wire the hook on `PreToolUse` with matcher
  `Edit|Write|NotebookEdit`.
- AC-012: the PowerShell hook satisfies AC-001..AC-008 with identical messages and exit codes.
- AC-013: `shellcheck -S error` is clean and every `.ps1` parses; the full existing suite stays
  green.

## Test scenarios

- **Unit**: n/a (shell + PowerShell) — covered below.
- **Integration**: a new `scripts/mindset-hook.test.sh` driving the hook with crafted stdin payloads
  for every AC, plus a PowerShell counterpart run on the `windows-latest` runner alongside the spec
  034 suites.
- **Regression**: `check-consistency.sh`, `install.test.sh`, `update.test.sh` and both PowerShell
  suites stay green; `shellcheck -S error` clean.
- **Manual**: confirm in a live session that the reminder appears before the first edit and not
  before the second.

## Assumptions

- The `PreToolUse` payload carries `session_id`. FR-002 does not depend on it — the fallback exists
  precisely because this is an assumption about the harness, not a guarantee.
- A `systemMessage` from a `PreToolUse` hook reaches the assistant's context. This is how
  `graphify-scan-reminder` already works, so the mechanism is proven in this repo.
- Reminding once per session is the right cadence. It matches the skill's own trigger ("before your
  first edit") and avoids the nag pattern that gets hooks disabled.

## Open questions

- Non-blocking: should the same treatment eventually cover `threat-modeler` (which has a natural
  seam — editing a handler, parser or endpoint)? Deliberately out of scope here; revisit once this
  hook has real usage.

## Contracted services

Contracted services not declared → all billable add-ons treated as NOT contracted (conservative
default). Run `/project-init` to declare them.

`specs/SERVICES.md` is absent because this is the SDD framework repo itself, not an adopter project.
No billable add-on is touched.
