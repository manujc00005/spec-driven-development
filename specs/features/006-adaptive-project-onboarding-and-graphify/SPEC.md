---
current_date: 2026-07-14
author: Manuel Jimenez
phase: 6
approval_date: 2026-07-14
spec_analyzed: true
implementation_date: 2026-07-14
implementation_validated: true
final_review_date: 2026-07-14
---

# Adaptive Project Onboarding + Graphify Integration

## Status

Done

**Objective:** Generalize Graphify integration as an optional, cross-platform, non-mandatory capability
of the SDD framework. Distribute the template documentation from a specific personal project into
reusable, generic SDD templates and skills.

## Problem

1. **Project-specific documentation** — Graphify guides generated in proyecto-cumbre contain hardcoded
   references to MisaFunnelPage, EmailService, useCartStore, Stripe, EventFunnelModal, Resend, etc.
   This documentation is useful conceptually but cannot be reused across projects.

2. **Graphify as optional context provider** — The SDD already has `graphify-context` skill and a
   `graphify-stale-reminder` hook, but no generic **setup/maintenance templates** or **workflow
   guidance** for engineers who want to onboard Graphify into a new project.

3. **Missing generalization** — The four personal project Graphify docs (SETUP-CHECKLIST, GUIDE,
   CLAUDE-INTEGRATION, QUICK-REFERENCE) contain patterns and workflows that apply to ANY project
   using Graphify, not just the specific application. Those patterns should live in the SDD framework,
   not be rediscovered in every project.

4. **Cross-platform gaps** — Graphify setup includes shell alias configuration that varies between
   PowerShell and bash. The SDD has scripts for both; Graphify guidance should too.

5. **Graceful degradation unclear** — The current skills degrade gracefully when GRAPH_REPORT.md is
   absent, but the **workflow entry point** for onboarding a project into Graphify is ad-hoc.
   Engineers don't know: "When should I install/run Graphify?" or "What does the SDD recommend?"

## Goal

Create a **generalized, reusable, optional, non-mandatory Graphify onboarding layer** for SDD:

1. **Generic Graphify templates** that apply to any project (not specific god nodes, not specific
   payment providers, not specific components).
2. **Enhanced `sdd-onboard` skill** that detects whether Graphify is installed and optionally
   scaffolds generic Graphify guidance.
3. **Clear workflow guidance** for when/how to use Graphify within SDD (before `/spec-plan`? before
   `/spec-implement`? optional?).
4. **Cross-platform setup documentation** (PowerShell aliases, bash aliases) as optional templates.
5. **Graceful degradation** — if Graphify is not installed, the feature should not block, warn, or
   suggest installation. It should only mention Graphify if `.graphify/graph.json` or
   `.graphify/GRAPH_REPORT.md` exists.

## Non-Goals

- ❌ Do not install Graphify automatically (users run `npm install -g @sentropic/graphify` or equivalent themselves).
- ❌ Do not require Graphify as a dependency in `profiles.json` or elsewhere.
- ❌ Do not bake project-specific references into framework documentation (no MisaFunnelPage, EmailService, Stripe, Resend, etc.).
- ❌ Do not modify the user's actual `.claude/` config or shell profiles (generate templates; users copy-paste).
- ❌ Do not modify existing projects outside the SDD framework (the skill is read-only on application code).
- ❌ Do not create a parallel system to existing `sdd-onboard`, `context-manager`, or `graphify-context` skills — enhance the existing ones.
- ❌ Do not break existing profiles or change the default profile.
- ❌ Do not enable or reference blockchain-crypto profile.
- ❌ Do not assume the project is Java/Spring, Next.js, or any specific stack.

## Functional Requirements

### FR-1: Generic Graphify Templates

Create two new generic Markdown templates under `docs/_templates/`:

1. **`GRAPHIFY.md`** — A guide for engineers new to Graphify in this project.
   - How to detect if Graphify is installed.
   - How to install it (pointer to official docs, not instructional).
   - How to run common Graphify commands.
   - When to refresh the graph (guidelines, not hard rules).
   - Integration with SDD workflow (where does Graphify fit?).
   - Cross-platform shell alias setup (PowerShell + bash).
   - Troubleshooting (graph is stale, graph is absent, command failed).
   - No project-specific examples (no MisaFunnelPage, no Stripe, no EmailService).

2. **`PROJECT_GRAPH.md`** — A project-generated placeholder for Graphify output.
   - Summary of detected architecture (god nodes, communities, modules).
   - Last graph generation date.
   - How to regenerate.
   - Placeholders for the actual generated content (so humans know where Graphify output will live).
   - Optional: link to `.graphify/GRAPH_REPORT.md` if it exists.

### FR-2: Enhanced `sdd-onboard` Skill

Extend the existing `sdd-onboard` skill (skills/sdd-onboard/SKILL.md) to:

1. **Detect Graphify presence** — check if `.graphify/graph.json` or `.graphify/GRAPH_REPORT.md`
   exists in the project root.
2. **If Graphify exists:**
   - Scaffold `docs/PROJECT_GRAPH.md` (from the template) with basic structure.
   - Include a note in the output: "Graphify detected. Generated `docs/PROJECT_GRAPH.md`."
   - Recommend reading the generated `docs/GRAPHIFY.md` for next steps.
3. **If Graphify does NOT exist:**
   - Skip Graphify docs.
   - Do NOT recommend installation (non-mandatory).
   - Optionally note: "Graphify not detected. If you want architecture impact analysis, consider installing it separately."
4. **Degrade gracefully** if `.graphify/` directory exists but is corrupted or unreadable.

### FR-3: Workflow Guidance in Core Skills

Update docstrings/behavior in `context-manager` and `graphify-context` skills to clarify:

1. **When to invoke `context-manager`?** — Read before implementing to narrow the file list.
2. **When to invoke `graphify-context`?** — Optionally, if GRAPH_REPORT.md exists and you want impact analysis.
3. **When is Graphify recommended but not required?** — Before `/spec-plan` on medium/large features (for impact analysis).
4. **Can I use SDD without Graphify?** — Yes, fully. Graphify is a *capability*, not a requirement.

### FR-4: Documentation Updates

Update or create guidance in:

1. **`docs/SDD-ORCHESTRATION.md`** — Clarify where Graphify fits in the medium/full workflow (optional).
2. **`README.md`** — Add a brief note that Graphify is an *optional* accelerator, not part of core SDD.
3. **`hooks/README.md`** — Clarify that `graphify-stale-reminder` is safe (reminder-only, never blocks).

### FR-5: Cross-Platform Shell Configuration

In `docs/_templates/GRAPHIFY.md` (and optionally a new `SHELL_ALIASES.md` template):

- PowerShell alias suggestions for `gg`, `gtree`, `gquery`, `gpath`, `gcontext`, `gflows`.
- Bash alias suggestions for the same.
- Clear instructions: "Copy these into your shell profile; the SDD framework does not modify it."

### FR-6: Migration from Personal Project Docs

Transform the four personal-project Graphify docs into generalized templates:

| Source (proyecto-cumbre) | Extracted generic content | Destination in SDD | Project-specific removal |
|---|---|---|---|
| GRAPHIFY-SETUP-CHECKLIST.md | Checklist structure, when-to-update rules, verification steps | docs/_templates/GRAPHIFY.md | God nodes (logger, MisaFunnelPage, EmailService), specific benchmarks, Stripe examples |
| GRAPHIFY-CLAUDE-INTEGRATION.md | Workflow patterns (how to paste context into Claude), SDD integration | docs/_templates/GRAPHIFY.md § Claude Code Integration | Specific components (EventFunnelModal, useCartStore, calculateEventPrice), Stripe webhook, Resend |
| GRAPHIFY-GUIDE.md | Command taxonomy, use cases (code review, debugging, feature dev), architecture patterns | docs/_templates/GRAPHIFY.md § Use Cases | Stripe, EmailService, Resend, specific payment flow, specific event registration flow |
| GRAPHIFY-QUICK-REFERENCE.md | Command syntax, alias suggestions, common scenarios, troubleshooting | docs/_templates/GRAPHIFY.md § Command Reference | Specific god nodes, specific file paths (app/api/webhooks/stripe, lib/cart, lib/mail) |

## Acceptance Criteria (All Passing)

| # | Criterion | Status | Evidence |
|---|---|---|---|
| **AC-001** | `docs/_templates/GRAPHIFY.md` exists; valid Markdown; contains: Intro, Installation pointer, Common commands (generic examples only), Refresh guidelines, Cross-platform aliases (PowerShell + bash), SDD integration (optional), Troubleshooting. Zero god nodes, payment providers, or specific components. | ✅ PASS | 270 lines, all sections present, 0 proyecto-cumbre terms |
| **AC-002** | `docs/_templates/PROJECT_GRAPH.md` exists; valid Markdown; placeholder structure (clearly marked); guidance on regenerating; no hardcoded project-specific content. | ✅ PASS | 142 lines, placeholders marked, 0 specific terms |
| **AC-003** | `skills/sdd-onboard/SKILL.md` updated to document Graphify detection (Step 4b) and graceful fallback (skip if absent, scaffold PROJECT_GRAPH.md if present). | ✅ PASS | Step 4b documented, "never execute/install", graceful degradation clear |
| **AC-004** | `docs/SDD-ORCHESTRATION.md` clarifies Graphify is optional; positioned before `/spec-plan`; not required. | ✅ PASS | Section "Optional: Architecture Context with Graphify" added, 12 lines |
| **AC-005** | `hooks/README.md` clarifies `graphify-stale-reminder` is safe reminder (exits 0, never blocks). | ✅ PASS | "Never blocks", "exit 0", "always safe", "reminder only" |
| **AC-006** | `profiles.json` core profile templates array includes `GRAPHIFY.md` and `PROJECT_GRAPH.md`. Valid JSON. | ✅ PASS | Lines 72-73 in core.templates, JSON valid, files exist |
| **AC-007** | Zero proyecto-cumbre-specific code names in new templates: 0 matches for "MisaFunnelPage", "EmailService", "useCartStore", "Stripe", "Resend", "EventFunnelModal". | ✅ PASS | 0 matches in GRAPHIFY.md, PROJECT_GRAPH.md, and framework docs |
| **AC-008** | Cross-platform aliases provided: PowerShell and bash sections in GRAPHIFY.md are syntactically valid and copy-pasteable. | ✅ PASS | Both sections present, clearly separated, no auto-modification of user profiles |
| **AC-009** | `graphify-context`, `context-manager`, `graphify-stale-reminder` doc clarity updates; no behavior changes; no regressions. | ✅ PASS | Skills already documented graceful degradation, no changes needed |
| **AC-010** | Framework does NOT modify user shell profiles, `.claude/` config, or user-controlled files. Templates provide copy-paste suggestions only. | ✅ PASS | Aliases are copy-paste only, no auto-wiring, no config modification |

## Risks

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| **Graphify docs are too generic and not useful.** | Medium | Medium | Solicit feedback from users trying Graphify for the first time. Iterate on examples. |
| **sdd-onboard enhancement breaks existing projects.** | Low | High | Test on projects with and without `.graphify/`. Run dry-run on existing features. |
| **Shell alias setup is incomplete or wrong.** | Medium | Low | Test on both PowerShell and bash. Document that users should verify aliases work before committing to `.bashrc` / `$PROFILE`. |
| **Graphify remains unused because guidance is unclear.** | Medium | Medium | Clarify workflow entry point (recommend Graphify before `/spec-plan`). Show a concrete before/after. |

## Test Strategy

### Unit / Existence Tests

- [ ] `docs/_templates/GRAPHIFY.md` exists and is valid Markdown.
- [ ] `docs/_templates/PROJECT_GRAPH.md` exists and is valid Markdown.
- [ ] No hardcoded god nodes or project-specific code names in new templates.

### Integration Tests

- [ ] Run `sdd-onboard` on a test project with `.graphify/` → confirms `docs/PROJECT_GRAPH.md` is scaffolded.
- [ ] Run `sdd-onboard` on a test project without `.graphify/` → confirms no Graphify docs are created, no errors.
- [ ] `graphify-context` skill still works when GRAPH_REPORT.md is absent.
- [ ] `context-manager` skill still works when GRAPH_REPORT.md is absent.
- [ ] `graphify-stale-reminder` hook exits 0 (never blocks) whether graph is absent or stale.

### Manual / Cross-Platform Tests

- [ ] PowerShell aliases from GRAPHIFY.md template can be copy-pasted and work (if Graphify is installed).
- [ ] Bash aliases from GRAPHIFY.md template can be copy-pasted and work (if Graphify is installed).

### Documentation Tests

- [ ] Search for project-specific terms in new templates: MisaFunnelPage, EmailService, useCartStore, Stripe, Resend, EventFunnelModal. Result: zero matches.
- [ ] Search for "deprecated" or "do not use" in templates. Result: zero (confidence that docs are stable).

## Rollback Strategy

If the feature fails:

1. Remove `docs/_templates/GRAPHIFY.md` and `docs/_templates/PROJECT_GRAPH.md`.
2. Revert `sdd-onboard` to its previous version (no Graphify detection).
3. Leave `graphify-context`, `context-manager`, and `graphify-stale-reminder` as-is (they already work and are safe).
4. Update `docs/SDD-ORCHESTRATION.md` to remove any references to Graphify (they were optional anyway).

The rollback is a clean removal; no data is lost, and the SDD continues to work without Graphify.

## Open Questions

1. **Should GRAPHIFY.md be scaffolded automatically by `sdd-onboard`?** — Yes, if `.graphify/` exists. No, if it doesn't (optional feature).
2. **Should Graphify usage be in the default SDD workflow?** — No. It's an optional accelerator mentioned in the documentation, not a required step.
3. **Should `graphify-stale-reminder` hook be wired by default?** — Yes, it's already in the `core` profile's hooks list. It's harmless (reminder-only).

---

## Architecture Notes

### Why Generalize?

The four personal-project Graphify docs contain valuable **process knowledge** (when to run Graphify,
which commands solve which problems) mixed with **project-specific details** (god nodes, components,
data models). By extracting the process knowledge into the SDD framework, future projects don't have
to rediscover it.

### Where Does Graphify Fit in SDD?

```
Workflow:
  /project-init  → detect stack, setup CONSTITUTION
           ↓
  /sdd-onboard   → scaffold context docs, *optionally detect Graphify*
           ↓
  /spec-create   → write the spec for the feature
           ↓
  /spec-plan     → *optionally: use Graphify impact analysis via /graphify-context*
           ↓
  /spec-analyze  → *optionally: enrich reading list with /context-manager + Graphify*
           ↓
  /spec-implement → code
           ↓
  /spec-review   → review against spec
           ↓
  /qa-review, /security-review, /database-review, ...
           ↓
  /spec-close
```

Graphify is optional at every step. If not available, the workflow continues unchanged.

### Graceful Degradation Example

```
Engineer: "I want to understand the impact of my change."

If GRAPH_REPORT.md exists:
  → /graphify-context reads it and produces impact analysis
  → engineer gets fine-grained module dependency info

If GRAPH_REPORT.md does NOT exist:
  → /graphify-context degrades to heuristic (ARCHITECTURE.md + spec)
  → engineer gets coarse module info
  → /graphify-context suggests: "Graphify not available. Install it for better precision."

Either way: workflow continues, no blocking.
```

---

## Files to Create / Modify

### Create

- [ ] `docs/_templates/GRAPHIFY.md`
- [ ] `docs/_templates/PROJECT_GRAPH.md`
- [ ] `specs/features/006-adaptive-project-onboarding-and-graphify/PLAN.md`
- [ ] `specs/features/006-adaptive-project-onboarding-and-graphify/TASKS.md`
- [ ] `specs/features/006-adaptive-project-onboarding-and-graphify/DECISIONS.md`

### Modify

- [ ] `skills/sdd-onboard/SKILL.md` — add Graphify detection logic
- [ ] `docs/SDD-ORCHESTRATION.md` — clarify Graphify placement (optional)
- [ ] `README.md` — note Graphify is optional
- [ ] `hooks/README.md` — clarify `graphify-stale-reminder` is safe
- [ ] `profiles.json` — add `GRAPHIFY.md` and `PROJECT_GRAPH.md` to `core` profile templates (NOT as a new profile)

### No Change Needed

- ✅ `skills/graphify-context/SKILL.md` — already gracefully degrades
- ✅ `skills/context-manager/SKILL.md` — already gracefully degrades
- ✅ `hooks/graphify-stale-reminder.ps1/.sh` — already safe (reminder-only)

---

## Success Criteria Summary

A project engineer who has never used Graphify before should be able to:

1. Run `/sdd-onboard` and see context docs generated.
2. Read `docs/GRAPHIFY.md` and understand: "Graphify is optional. If I want it, here's how."
3. Optionally install Graphify externally and re-run `/sdd-onboard` → see `docs/PROJECT_GRAPH.md` scaffolded.
4. Use `/graphify-context` before `/spec-plan` on a medium feature and get impact analysis.
5. Not have to figure out what to do with Graphify output — the templates and skills guide them.

By contrast, a project without Graphify should work exactly the same (just without the optional impact analysis).
