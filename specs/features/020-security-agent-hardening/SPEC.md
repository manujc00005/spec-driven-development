# Feature Spec: Security agent hardening and self-contained routing

## Status

In Review

## Problem

Two related failures were observed in a real session:

1. **Unshipped-subagent drift.** `skills/security-review/SKILL.md` instructs "delegate the full
   review to the `security` agent" and, for personal data, to a `gdpr-spain` agent.
   `skills/privacy-compliance-review/SKILL.md` likewise delegates first to `gdpr-spain`. Neither
   agent is shipped by this repo, declared in `profiles.json`, or guaranteed to exist in any
   session. The observed result: "el agente security no está disponible" and a fallback to the
   generic checklist — the skill *worked as written*, but its primary path can never work in a
   self-contained install. This is the exact drift class spec 018 removed for `java-spring` /
   `api-design` (D006): skills must route to agents this repo ships.
2. **The shipped agent is thinner than its mandate.** `agents/security-reviewer.md` covers
   secrets/auth/payments review well, but does not explicitly own vulnerability hunting across a
   named taxonomy, forward-looking attack anticipation ("previsión de agujeros"), or the
   RGPD/LOPDGDD/AEPD compliance dimension that `security-review` and `privacy-compliance-review`
   route to it (both contracts already declare `primary_agent: security-reviewer`).

A user-level stopgap skill (`software-security-review`, in the central config dir, outside this
repo) was created to work around failure 1; the framework itself should not need it.

## Goal

- `security-review` and `privacy-compliance-review` delegate to the **shipped**
  `security-reviewer` agent — never to unshipped `security`/`gdpr-spain` names — with the existing
  inline checklists retained as the documented fallback when no agent registry is available.
- `security-reviewer` is upgraded into the framework's explicit owner of: vulnerability hunting
  (named taxonomy), attack anticipation (abuse-case enumeration before reading the diff), and
  RGPD/LOPDGDD/AEPD review (via the `privacy-compliance-review` skill), while remaining read-only.

## Non-goals

- No new agent files (no `security`, no `gdpr-spain` — D006 precedent: reroute, don't multiply).
- No change to `profiles.json` (routing entries for these skills already point at
  `security-reviewer`), no change to hooks, installers, or any other skill.
- No autonomous scanning/tooling claims: the agent reviews diffs and code it can Read/Grep/Glob;
  it does not run scanners, exploit anything, or claim to replace a pentest.
- No legal-advice claim: RGPD review is engineering-level compliance review, not legal counsel.

## Users / Actors

- Engineer running `/security-review` or `/privacy-compliance-review` in a session with the agent
  registry installed (delegation path) or without it (fallback path).
- The `security-reviewer` agent itself; `implementer` (fixes findings);
  `final-conformance-reviewer` (confirms resolution).

## Current behavior

Delegation targets `security`/`gdpr-spain` → unavailable in every self-contained install → always
falls back to the generic checklist; the shipped `security-reviewer` agent is never named by the
skills' prose.

## Desired behavior

Delegation targets `security-reviewer` (shipped, in `profiles.json` core agents, installed by
`--link-user-claude`/`link-project`); fallback remains for agent-less sessions; the agent's
contract explicitly covers vulnerabilities, attack foresight, and RGPD.

## Functional requirements

- **FR-001:** `skills/security-review/SKILL.md` delegation section names `security-reviewer` as
  its sole delegation target, covers the RGPD trigger list by instructing the same agent to apply
  `privacy-compliance-review`, and keeps the inline checklist as explicit fallback.
- **FR-002:** `skills/privacy-compliance-review/SKILL.md` delegation section names
  `security-reviewer` (consuming this skill) instead of `gdpr-spain`; fallback retained.
- **FR-003:** `agents/security-reviewer.md` gains: (a) a vulnerability taxonomy the review must
  walk (injection, broken authN/authZ incl. IDOR/tenant isolation, SSRF, insecure deserialization,
  XXE, path traversal, file-upload abuse, open redirect, CSRF/CORS/headers, race/TOCTOU,
  secrets/crypto misuse, dependency/supply-chain risk, logging/PII leakage, error-detail leakage,
  rate-limiting/abuse); (b) an attack-anticipation method (per entry point: who can call it, worst
  input, what breaks; trust boundaries; abuse cases before reading the implementation); (c)
  explicit RGPD/LOPDGDD/AEPD ownership via `privacy-compliance-review`; (d) unchanged read-only
  tools and boundaries.
- **FR-004:** No reference to `security` or `gdpr-spain` as agents remains anywhere in `skills/`.
- **FR-005:** `check-consistency.sh` passes unchanged (contracts intact, no manifest edits).
- **FR-006:** The user-level stopgap skill (`software-security-review`, central config dir) is
  **unified** into the framework: its unique review disciplines (source-to-sink Confirmed vs
  Potential, structural verification, plausibility filter, third-party data minimization,
  erasure propagation to third parties, paid-downstream rate limiting, public-token rule) are
  absorbed into `security-reviewer`/`security-review`, and the stopgap is retired from the
  central skills dir with a timestamped backup — leaving `/security-review` as the single entry
  point. Its session-harness-specific advice (spawning `Explore`/`general-purpose` agents) is
  deliberately not absorbed: framework agents cannot depend on harness-provided agent types.

## Non-functional requirements

- Honesty: the agent's text must not claim scanner/pentest capability it lacks.
- Compatibility: skill frontmatter and `## SDD Contract` blocks unchanged (routing prose only).

## API / Interface changes

None (markdown prose in 2 skills + 1 agent).

## Data model changes

None.

## Edge cases

- Session without agent registry (e.g. agents never copied to `~/.claude/agents`): skills fall
  back to their inline checklists — same behavior as today, now stated against a real agent name.
- Diff with no personal data: RGPD portion is skipped by its own trigger list (unchanged).

## Acceptance criteria

- **AC-001:** `grep -rn "gdpr-spain" skills/` returns nothing; no skill instructs delegation to a
  bare `security` agent. (FR-001, FR-002, FR-004)
- **AC-002:** Both skills name `security-reviewer` as delegation target with fallback retained.
  (FR-001, FR-002)
- **AC-003:** `agents/security-reviewer.md` contains the taxonomy, the attack-anticipation method,
  and explicit RGPD/LOPDGDD/AEPD ownership; `tools:` remains `Read, Grep, Glob`. (FR-003)
- **AC-004:** `bash scripts/check-consistency.sh` exits 0. (FR-005)
- **AC-005:** The agent/skill texts contain the absorbed disciplines (Confirmed-vs-Potential
  source-to-sink rule, structural verification, plausibility filter, third-party minimization,
  erasure propagation); the central-dir `software-security-review` skill is moved to a timestamped
  backup, not deleted. (FR-006)

## Test scenarios

- Manual: read both delegation sections and the agent file against AC-001..003.
- Integration: run the consistency harness (AC-004).

## Assumptions

- Agent availability in a live session still requires install (`--link-user-claude` or
  `link-project`) plus a new session — out of scope here, documented to the user.

## Open questions

- None blocking. (Whether to later fold the user's central-dir `software-security-review` stopgap
  into the repo is a separate decision; this spec makes it unnecessary.)

## Contracted services

`specs/SERVICES.md` absent → all billable add-ons treated as NOT contracted. This feature touches
none.
