# Decisions: mindset-skills

## Decision log

### D001 - Descriptive kebab names for the user's five manuals (resolves OQ-003)

**Date:** 2026-07-17

**Status:** Accepted

**Context:** The user described five manuals by role ("security sweep", "setup", "planner", "bug hunter", "honest advisor"). Two of those roles collide conceptually with existing skills (`security-review`, `debugger`). Skill names are the public slash-command interface (`/name`) and are hard to change once installed and documented.

**Decision:** Name them `threat-modeler`, `scout`, `decomposer`, `root-causer`, `honest-advisor` — descriptive of the *mindset*, plain kebab-case, no "the-" article (repo convention: `debugger`, not `the-debugger`).

**Reasoning:** Descriptive names auto-load better (FR-007) and avoid ambiguity with the process skills they complement. This is the most expensive-to-reverse decision in the feature (names propagate to profiles.json, README, and every install), so it is fixed up front.

**Consequences:** README/profiles use these names. If the user prefers their original phrasing, rename before any adopter installs; after that, renaming is a breaking change to the slash-command surface.

### D002 - All nine ship in the `core` profile

**Date:** 2026-07-17

**Status:** Accepted

**Context:** Skills must be declared in some profile or the consistency check flags them as orphans. The mindset manuals are stack-agnostic.

**Decision:** Add all nine to `core.skills` (always installed), like `debugger` and `handoff`.

**Reasoning:** They apply regardless of stack; a dedicated profile would leave them uninstalled by default, defeating the purpose.

**Consequences:** `core-skills` marker 31 → 40; `skills-total` 43 → 52. README markers and prose must move in lockstep (T011).

### D003 - Two-tier structure; tier-2 manuals complement, never duplicate

**Date:** 2026-07-17

**Status:** Accepted

**Context:** Four of the manuals overlap the *topic* of an existing process skill (security, onboarding, planning, debugging) but not its *function*. The non-goals forbid modifying or duplicating those skills.

**Decision:** Split into tier 1 (new ground) and tier 2 (mindset layer). Each tier-2 manual opens with a one-line statement of its relationship to the process skill it complements and repeats none of that skill's procedure (FR-008).

**Reasoning:** Keeps "how to think" (manual) separate from "what steps to run" (process skill), so neither dilutes the other and the existing skills stay untouched.

**Consequences:** Reviewer must cross-read each tier-2 manual against its counterpart for contradictions (T013). The relationship line is a required, checkable artifact (AC-007).

### D004 - Manuals stay decoupled from `spec-implement`/`spec-review` (resolves OQ-001)

**Date:** 2026-07-17

**Status:** Accepted

**Context:** The manuals could be wired into lifecycle skills via one-line pointers ("apply `verifier` before marking a task complete").

**Decision:** Do not add pointers in this feature; the manuals are standalone and user-invocable.

**Reasoning:** Keeps this feature purely additive and low-risk; wiring is a separable follow-up that can be designed once the manuals exist.

**Consequences:** No edits to existing lifecycle skills. Pointer wiring becomes a candidate follow-up feature.

### D005 - `verifier` authored first as the canonical skeleton; user priority order otherwise (resolves OQ-002)

**Date:** 2026-07-17

**Status:** Accepted

**Context:** All nine share one skeleton; getting the skeleton right once avoids nine divergent formats. The user also gave a priority order and `honest-advisor` was separately noted as highest-behavioral-impact.

**Decision:** Author `verifier` first to lock the skeleton, then follow the user's stated order (scope-keeper → communicator → stopper → honest-advisor → tier 2). Do not promote `honest-advisor` ahead of the user's order.

**Reasoning:** The skeleton is the reusable asset; `verifier` is first in the user's list anyway. Respecting the user's ordering keeps the graceful-degradation property they asked for.

**Consequences:** If interrupted, the highest-priority manuals exist first. The skeleton established in T001 is normative for T002–T009.

### D006 - "No personality prose" (FR-009) is the primary acceptance gate

**Date:** 2026-07-17

**Status:** Accepted

**Context:** The failure mode these manuals must avoid is becoming vibes ("be rigorous, be honest") instead of behavior a model can self-check against its transcript.

**Decision:** Every rule must contain an observable trigger or checkable condition; the T013 audit rejects any rule that is a bare adjective. This gate outranks stylistic preferences.

**Reasoning:** Actionable rules are the entire value over a generic system prompt; without the gate the feature reduces to tone.

**Consequences:** Review (T013) is mandatory, not optional. Rules may read more mechanically than typical prose — that is intended.
