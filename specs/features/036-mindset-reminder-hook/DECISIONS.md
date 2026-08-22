# Decisions: mindset-reminder-hook

## Decision log

### D001 - A `PreToolUse` hook, not inlined rules in `CLAUDE.md`

**Date:** 2026-08-22

**Status:** Accepted

**Context:**

Three ways to make an "always in effect" mindset actually present: inline the rules in the global
`CLAUDE.md`, inject them via a `UserPromptSubmit` hook on every turn, or inject them via a
`PreToolUse` hook at the moment they apply.

**Decision:**

`PreToolUse` on `Edit|Write|NotebookEdit`, fired once per session.

**Reasoning:**

The skill's own description names its trigger: *"Use before your first edit."* That is a
deterministic moment the harness can observe, so the delivery mechanism can match the claim instead
of contradicting it.

Inlining costs 641 words on **every** turn — including conversation, search and review turns where
scope discipline is irrelevant — and duplicates content that already lives in the skill file. That
duplication drifts, which is the failure mode this framework keeps having to fix.

`UserPromptSubmit` is deterministic too, but pays the same always-on cost for a rule that only
binds when editing.

**Consequences:**

- Turns that never edit pay nothing.
- Sessions that edit get the rules exactly once, before the first edit.
- The hook is one more shipped artifact to maintain in two languages — accepted, and the reason
  D004 exists.

---

### D002 - Remind, never block

**Date:** 2026-08-22

**Status:** Accepted

**Context:**

`PreToolUse` hooks can block a tool call. Scope discipline is a judgement, not a mechanical rule —
there is no predicate that decides whether an edit is in scope.

**Decision:**

Exit 0 unconditionally. No blocking verdict, ever, whatever happens internally.

**Reasoning:**

A hook that blocked edits on a judgement call would fire on correct work and get switched off
within a day — taking the reminder with it. `graphify-scan-reminder` already made this call
("reinforcement, not enforcement") and is the right precedent.

**Consequences:**

- The hook cannot guarantee scope discipline; it removes the failure mode of *not having the rules
  in context*. Stated in the spec's Non-goals so it is not mistaken for enforcement.
- A malformed payload can never break an edit.

---

### D003 - Once per session, keyed on `session_id`, with a time-based fallback

**Date:** 2026-08-22

**Status:** Accepted

**Context:**

`graphify-scan-reminder` throttles on a 30-minute TTL. For a "before your first edit" rule, the
natural unit is the session, not the clock.

**Decision:**

Throttle on a marker file named from the payload's `session_id`. If that field is missing or
sanitises to empty, fall back to a time-based throttle rather than firing on every edit.

**Reasoning:**

The session is the correct unit — the skill says *first* edit. Depending on `session_id` without a
fallback would make the hook's behaviour hostage to a harness field this spec only assumes exists
(recorded in Assumptions); the fallback keeps the worst case at "throttled by time" instead of
"nags on every edit", which is what gets hooks disabled.

**Consequences:**

- Two racing edits may print twice. Not prevented: locking a nudge costs more than the duplicate.
- The marker lives in the system temp dir (FR-008), so it never appears in the adopter's
  `git status` — a lesson from graphify's marker, which lives inside `.graphify/`.

---

### D004 - The hook carries an excerpt, and a test forbids it drifting

**Date:** 2026-08-22

**Status:** Accepted

**Context:**

The hook must carry some rule text to be useful, but `skills/scope-keeper/SKILL.md` is the source
of truth. Two copies of the same rules is exactly the duplication D001 rejected inlining for.

**Decision:**

The hook carries a deliberately short excerpt of the load-bearing rules, and
`scripts/mindset-hook.test.sh` asserts that the claims in that excerpt still appear in the skill
file (AC-009).

**Reasoning:**

An excerpt is unavoidable — a reminder with no content is not a reminder. What is avoidable is
*silent* drift. Making the test fail when the skill changes turns a duplication hazard into a
maintenance signal, which is the same move spec 034 made with `profileState`.

**Consequences:**

- Editing `scope-keeper`'s load-bearing bullets will fail the suite until the hook is updated.
  Intended: that is the signal.
- The excerpt is short by design; the message points at `/scope-keeper` for the full set.

---

### D005 - The global `CLAUDE.md` keeps text, not just a pointer

**Date:** 2026-08-22

**Status:** Accepted

**Context:**

The adopter's `CLAUDE.md` currently says `Siempre en efecto: /scope-keeper (diff mínimo)` — a
pointer with a three-word gloss. If neither the skill nor the hook loads, nothing survives.

**Decision:**

Carry the two or three load-bearing rules as text in `CLAUDE.md`, and let the hook deliver the rest
at edit time.

**Reasoning:**

Graceful degradation. A bare install on another machine, or a session where the hook is disabled,
should still leave the rules that matter most in context. This is not the full inlining D001
rejected — it is a handful of lines, not 641 words.

**Consequences:**

- A third place mentions scope rules. Bounded deliberately: `CLAUDE.md` carries the *principles*,
  the hook carries the *reminder*, the skill carries the *full manual*.
- The user's global `CLAUDE.md` lives outside this repo, so this part is applied to their machine
  directly and cannot be enforced by CI.
