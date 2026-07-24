# SDD Contract Schema (Phase 2)

Formal schema for the `## SDD Contract` block introduced by T002 (carrier decided in D011).
Defines required fields, enums, and the validation rules `check-consistency` will enforce
(implemented later in T014; defined now so T004–T010 have a stable target). Derived from and
supersedes the informal field table in `SPEC.md`'s "Skill contract model" section — this file is
the authoritative version going forward.

## Carrier

A fenced YAML block under a `## SDD Contract` heading, placed as the **first section
immediately after the YAML frontmatter**, before any other body content:

```markdown
---
name: <skill-name>
description: <...>
---

## SDD Contract

\`\`\`yaml
category: ...
...
\`\`\`

<rest of skill body, unchanged>
```

## Field reference

| Field | Type | Required | Allowed values |
|---|---|---|---|
| `category` | string (enum) | yes | `lifecycle` \| `context-research` \| `domain-reviewer` \| `quality-review` \| `mindset` \| `orchestration` |
| `inputs` | list of strings | yes (non-empty) | free-form tokens/paths; trailing `?` marks an optional input (e.g. `docs/TECH_STACK.md?`) |
| `outputs` | list of strings | yes (non-empty) | free-form tokens/paths |
| `side_effects` | string (enum) | yes | `none` \| `writes-specs` \| `writes-code` \| `writes-scratch` |
| `writes_code` | boolean | yes | `true` \| `false` (strict YAML bool, not string) |
| `writes_specs` | boolean | yes | `true` \| `false` |
| `analysis_only` | boolean | yes | `true` \| `false` |
| `primary_agent` | string (enum) | yes | `codebase-researcher` \| `solution-architect` \| `implementer` \| `security-reviewer` \| `domain-reviewer` \| `final-conformance-reviewer` \| `orchestration-context` \| `any` \| `human` |
| `secondary_agents` | list of strings, or `[all]` | no (default `[]`) | zero or more of the six agent names, **or** the single reserved entry `all` — never mixed |
| `profile_scope` | string `all`, or list of strings | yes | literal `all`, or a list of keys that must exist under `profiles.profiles` in `profiles.json` |
| `provider_specific` | boolean | yes | `true` \| `false` — see D013 (not a provider name/list) |

### `primary_agent` enum, fully defined

- The **six Phase 2 agents**: `codebase-researcher`, `solution-architect`, `implementer`,
  `security-reviewer`, `domain-reviewer`, `final-conformance-reviewer`.
- `orchestration-context` — for router/orchestrator skills that *dispatch* agents rather than
  being dispatched (`sdd`, `sdd-medium`, `sdd-full`, `sdd-orchestrate`, `review-all`), per D010.
- `any` — for skills with no single accountable owner, usable by any of the six
  (`spec-status`, `spec-resume`).
- `human` — for skills that are manual-only / `disable-model-invocation: true` and are not meant
  to be dispatched by an agent at all (`handoff`).

### `secondary_agents: all` representation

`all` is a **reserved sentinel**, valid only as the sole element of the list (`secondary_agents:
[all]`). It expands to the six lifecycle agents (never `orchestration-context`, `any`, or
`human`). It must not be combined with named agents in the same list — a skill either names
specific secondary consumers or declares itself universally secondary-consumable, not both.
Used by the 9 mindset manuals, which are consumed by every agent but owned by none.

### `profile_scope` semantics

- `all` — the skill ships in every profile that installs `core`, or is otherwise
  profile-agnostic (matches skills declared directly under the `core` profile in `profiles.json`).
- A list of profile keys — must be a subset of the keys under `profiles.profiles` in
  `profiles.json` (currently: `core`, `java-spring-backend`, `messaging-event-driven`,
  `payments-fintech`, `next-prisma-web`, `seo-geo-addon`, `blockchain-crypto`). Unknown keys fail
  validation. This is how `check-consistency` cross-checks a skill's declared scope against where
  `profiles.json` actually installs it.

### `provider_specific` — boolean, not a provider list (D013)

Kept as a plain boolean. A list of provider names (e.g. `[claude-code]`) was considered but
rejected as speculative: only one provider exists today, and the SPEC's Non-goals explicitly
reject over-engineering. If a second provider (e.g. Codex) is actually integrated later, this
field can be widened to a list in a follow-up decision — not now.

### `side_effects` vs the three booleans — precedence rule

`side_effects` is a single dominant-effect label; the three booleans are the authoritative,
cross-checked source of truth. Precedence when a skill has more than one true effect (e.g.
`sdd-orchestrate`, which both writes code via `fast-worker` and keeps SPEC docs in sync):

1. If `writes_code: true` → `side_effects` **must** be `writes-code` (highest precedence).
2. Else if `writes_specs: true` → `side_effects` **must** be `writes-specs`.
3. Else → `side_effects` **must** be `none` or `writes-scratch` (author's choice; there is no
   corresponding boolean for scratch-only output, e.g. `handoff`, `prototype`).

## Required vs optional fields

**Required on every skill:** `category`, `inputs`, `outputs`, `side_effects`, `writes_code`,
`writes_specs`, `analysis_only`, `primary_agent`, `profile_scope`, `provider_specific`.

**Optional:** `secondary_agents` — absence is treated as `[]`.

**No unknown keys** — any key outside this table fails validation (catches typos such as
`writes_test` instead of `writes_specs`).

## Validation rules for `check-consistency`

- **VR1 — Presence:** every `skills/*/SKILL.md` contains exactly one `## SDD Contract` section
  with exactly one fenced ` ```yaml ` block, positioned immediately after the frontmatter.
- **VR2 — Parseable:** the block parses as a YAML mapping.
- **VR3 — Required keys:** all required fields (above) are present.
- **VR4 — No unknown keys:** any key not in the schema fails validation.
- **VR5 — `category` enum:** must be one of the six listed values.
- **VR6 — `primary_agent` enum:** must be one of the nine listed values.
- **VR7 — `secondary_agents` shape:** a list; each entry is one of the six agent names, or the
  list is exactly `[all]`.
- **VR8 — `side_effects` enum:** must be one of the four listed values.
- **VR9 — Strict booleans:** `writes_code`, `writes_specs`, `analysis_only`, `provider_specific`
  must be YAML booleans, not strings.
- **VR10 — Side-effect precedence:** enforce the precedence rule above (fails if
  `writes_code: true` but `side_effects != writes-code`, etc.).
- **VR11 — `analysis_only` consistency:** `analysis_only: true` requires `writes_code: false`
  and `writes_specs: false`.
- **VR12 — `profile_scope` resolution:** if not `all`, every entry must match a key under
  `profiles.profiles` in `profiles.json`.
- **VR13 — `inputs`/`outputs` shape:** both must be non-empty lists of strings.
- **VR14 — Agent existence (soft/degrade-gracefully):** if `primary_agent` or any
  `secondary_agents` entry names one of the six lifecycle agents and no `agents/<name>.md`
  exists on disk **and** it is not listed in any profile's `plannedAgents`, emit a **warning**,
  not a hard failure — mirrors the existing `plannedSkills`/`plannedHooks` convention. This is
  what allows T003/T010 (contracts) to be applied independently of T004–T009 (actual agent
  files) in either order.
- **VR15 — External-subagent drift (soft):** if a skill's contract declares
  `primary_agent: domain-reviewer` or `primary_agent: security-reviewer` but the skill body still
  names an external subagent outside the nine-value enum (e.g. `java-spring`, `api-design`),
  emit a **warning** flagging it as pending reroute — tracked by T011, not a hard failure here.

Hard failures: VR1–VR13. Soft warnings (non-blocking): VR14–VR15.

## Self-check against the 6 T002 samples

All six pass every hard rule; `sdd-orchestrate` is the one that exercises the precedence rule
(VR10: `writes_code: true` and `writes_specs: true` both set → `side_effects: writes-code`
correctly wins). `java-spring-reviewer` trips **VR15 as a warning** (body still says "routes to
the `java-spring` subagent") — expected and tracked by T011, not a blocker for T004–T010.
