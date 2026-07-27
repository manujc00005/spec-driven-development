<!-- See skills/sdd-guardrails/SKILL.md, section 1, for the full decision state machine (Proposed / Accepted / Superseded / Rejected / Deferred). -->

# Decisions: Security agent hardening and self-contained routing

## Decision log

### D001 - Reroute to the shipped security-reviewer; do not create `security`/`gdpr-spain` agents

**Date:** 2026-07-25

**Status:** Accepted

**Context:** `security-review` and `privacy-compliance-review` delegate to `security` and
`gdpr-spain` agents this repo does not ship, so the primary path fails in every self-contained
install ("el agente security no está disponible"). Two options: ship agents with those names, or
reroute to the existing `security-reviewer`.

**Decision:** Reroute both skills to `security-reviewer`. No new agent files.

**Reasoning:** Identical to spec 018 D006 (`java-spring`/`api-design` → `domain-reviewer`): the
framework must not depend on uncontrolled, environment-provided agents. Both skills' `## SDD
Contract` blocks already declare `primary_agent: security-reviewer` — the prose was the only thing
pointing elsewhere. Splitting RGPD into a separate `gdpr-spain` agent would also contradict 018
D008, which made `security-reviewer` the single owner of sensitive-data risk review.

**Consequences:** Delegation now targets an agent that `profiles.json` core ships and the
installers copy. The inline checklists remain as the documented fallback for agent-less sessions
(same graceful degradation as before, now against a real name). The user-level
`software-security-review` stopgap skill in the central config dir becomes unnecessary (kept or
deleted at the user's discretion — it lives outside this repo).

### D002 - RGPD stays a skill consumed by security-reviewer, not a dedicated agent

**Date:** 2026-07-25

**Status:** Accepted

**Context:** RGPD/LOPDGDD/AEPD review needs an accountable owner now that `gdpr-spain` is gone.

**Decision:** `security-reviewer` owns RGPD review by consuming the existing
`privacy-compliance-review` skill; the skill keeps the full legal checklist (RGPD, LOPDGDD,
age-of-consent 14, AEPD guidance), the agent decides when it applies.

**Reasoning:** Skills define how, agents own outcomes (018 D001/D002). The legal checklist is a
capability; accountability for running it on the right diffs belongs with the agent that already
owns sensitive-data risk. A second reviewer agent for privacy would overlap `security-reviewer` on
every PII-touching diff.

**Consequences:** `privacy-compliance-review`'s contract is unchanged
(`primary_agent: security-reviewer` was already true). The agent file now names the RGPD dimension
explicitly so the responsibility is discoverable from the agent side too.

### D003 - Strengthen the agent with a named taxonomy and attack-anticipation method, not tool claims

**Date:** 2026-07-25

**Status:** Accepted

**Context:** The user asked for "el mejor previsor de agujeros" — the best hole-anticipator.
The temptation is to promise scanners, SAST, or autonomous pentesting.

**Decision:** Upgrade `security-reviewer` with (a) an explicit vulnerability taxonomy the review
must walk, (b) an attack-anticipation method (abuse cases per entry point before reading the
implementation, trust-boundary mapping), and (c) explicit RGPD ownership — while keeping
`tools: Read, Grep, Glob` and the analysis-only boundary. No scanner/pentest capability is claimed.

**Reasoning:** The agent's power is bounded by its tools; claiming more would be dishonest (the
same honesty standard the Codex adapter follows). A named taxonomy makes coverage auditable — a
reviewer can check which classes were considered — and the anticipation method operationalizes the
`threat-modeler` mindset the agent already consumes.

**Consequences:** The agent text grows but its permissions and boundaries are unchanged;
`check-consistency` needs no new rules. Findings remain evidence-based (`file:line`), ranked by
exploitability × blast radius.

### D004 - Unify the user-level stopgap skill into the framework, then retire it

**Date:** 2026-07-25

**Status:** Accepted

**Context:** While this spec was being implemented, a downstream project (lead-platform) had
already created a stopgap skill `software-security-review` in the user's central config dir
(`~/.claude-config/skills/`, reachable as `~/.claude/skills/`) to work around the unavailable
`security`/`gdpr-spain` agents. Leaving it would mean two competing security entry points
(`/security-review` and `/software-security-review`) with drifting content — the exact
fragmentation this framework exists to prevent.

**Decision:** Unify: absorb the stopgap's genuinely unique review disciplines into the framework
(agent: source-to-sink Confirmed/Potential rule, structural verification, plausibility filter,
public-token rule, third-party data minimization, erasure propagation, paid-downstream rate
limiting), then retire the stopgap from the central skills dir via a timestamped backup move (not
a hard delete). Its harness-specific advice (delegating investigation to `Explore`/
`general-purpose` agent types) is not absorbed — those are session-harness builtins, not framework
agents, and `security-reviewer` is read-only by design.

**Reasoning:** One accountable owner per concern (018 D002/D008). The stopgap's value was real
content plus self-containment; the routing fix (D001) delivers self-containment properly, so only
the content needed rescuing. A backup move keeps the user's work recoverable.

**Consequences:** `/security-review` is again the single security entry point. The stopgap lives
on in `~/.claude-config/_install-backups/<ts>/skills/software-security-review/` until the user
deletes it. Downstream projects need no change — they never referenced the stopgap by config, only
by invocation.
