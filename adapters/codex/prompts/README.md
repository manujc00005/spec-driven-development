# Codex lifecycle prompts

The **portable lifecycle spine** of SDD Core, packaged as Codex prompts. Each file is derived from
its Claude Code skill counterpart under [`../../../skills/`](../../../skills/) — the *procedure* is
the same; only the packaging differs (a Codex prompt instead of a `SKILL.md` slash command).

> **Curated spine, not the full catalogue.** The Claude adapter ships 65 skills. This adapter ports
> only the provider-neutral core lifecycle (see `PARITY.md` and DECISIONS D004). Stack-specific
> reviewers and Claude-specific mindset manuals are intentionally not included in v1.

| Prompt | Derived from skill | Purpose |
|---|---|---|
| `sdd-spec-create.md` | `skills/spec-create` | Create `SPEC.md` before implementation. |
| `sdd-spec-plan.md` | `skills/spec-plan` | Turn an approved SPEC into PLAN + TASKS + DECISIONS. |
| `sdd-spec-analyze.md` | `skills/spec-analyze` | Consistency gate across the four documents. |
| `sdd-spec-implement.md` | `skills/spec-implement` | Implement one task at a time, test-driven. |
| `sdd-spec-review.md` | `skills/spec-review` + `qa-review` | Review the diff against SPEC/PLAN/TASKS. |
| `sdd-spec-close.md` | `skills/spec-close` | Resolve open questions, confirm coverage, close. |
| `sdd-guardrails.md` | `skills/sdd-guardrails` | Detect contradictions / obsolete plans before proceeding. |
| `sdd-workspace-onboarding.md` | `skills/sdd-workspace-onboarding` | Map a folder of related projects into `.sdd-workspace/` before cross-project work. |

## Installing these as Codex prompts

The documented Codex convention is markdown prompt files under `~/.codex/prompts/`. Install them
with the adapter's copy-only script:

```bash
# from the repo root
./adapters/codex/install-codex.sh --dry-run     # preview — writes nothing
./adapters/codex/install-codex.sh               # copy AGENTS.md (project root) + prompts (~/.codex/prompts)
```

See [`../README.md`](../README.md) for targets, flags, and the **unverified-against-a-live-CLI**
status. If your Codex release reads custom prompts from a different location, copy the files there
manually — they are plain markdown with no Codex-version-specific syntax.

## Using a prompt

Open the prompt in your Codex session (or invoke it as a slash command if your install exposes
`~/.codex/prompts/` that way) and provide the feature path. Each prompt states its own inputs,
outputs, and the guardrails it must honor. All of them assume the shared, provider-neutral templates
in [`../../../specs/_templates/`](../../../specs/_templates/).
