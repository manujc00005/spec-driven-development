---
status: Approved for implementation
created: 2026-07-14
feature: 006-adaptive-project-onboarding-and-graphify
last_updated: 2026-07-14
approval_date: 2026-07-14
note: Decisions approved for implementation. Status transitions to Active after validation.
---

# Decisions — Adaptive Project Onboarding + Graphify Integration

## D001: Graphify as Optional Non-Mandatory Feature

**Decided:** 2026-07-14  
**Status:** Accepted  
**Author:** Manuel Jimenez

### Decision

Graphify is an **optional, non-mandatory feature** of SDD. The framework continues to work fully without it.
If a project has `.graphify/` installed, SDD recognizes it and can use it for impact analysis. If not, SDD degrades gracefully.

### Rationale

1. **Diversity of project maturity** — Not all projects have Graphify installed. SDD should not require it.
2. **Installation friction** — Graphify is an external tool. The SDD should not auto-install it.
3. **Lightweight onboarding** — Engineers who have never used Graphify should still be able to use SDD.
4. **Acceleration, not blocking** — Graphify is an accelerator (faster impact analysis) but not a requirement.

### Implications

- No `graphify` dependency in `profiles.json` as a hard requirement.
- Skills must degrade gracefully when GRAPH_REPORT.md is absent.
- Documentation must clarify that Graphify is optional.
- Templates for Graphify setup should be generic and non-prescriptive.

### Alternatives Considered

- **Require Graphify:** Would reduce complexity of feature but break backward compatibility and add installation friction.
- **Auto-install Graphify:** Would reduce user friction but violates no-auto-install rule in SPEC non-goals.
- **Make Graphify a separate profile:** Would require users to explicitly opt-in, but then templates wouldn't be shipped by default.

### Decision (Chosen)

Make it optional and ship templates in `core` profile. Users can ignore Graphify entirely.

---

## D002: Templates in Core Profile, Not New Profile

**Decided:** 2026-07-14  
**Status:** Accepted

### Decision

Add `GRAPHIFY.md` and `PROJECT_GRAPH.md` templates to the **core** profile (always installed), not create a new
`graphify-aware` profile. This ensures the templates are available to everyone, but their use is optional.

### Rationale

1. **Simplicity** — Engineers don't need to learn a new profile name to opt-in to Graphify guidance.
2. **No churn** — Avoids proliferation of profiles. Current profiles (core, java-spring-backend, messaging-event-driven, next-prisma-web, payments-fintech) are already substantial.
3. **Low friction** — If an engineer installs SDD, they automatically get Graphify templates. If they want to use them, they do. If not, they're harmless.
4. **Consistency** — Other optional/contextual templates (PROJECT_CONTEXT.md, TECH_STACK.md) are in core, not in separate profiles.

### Implications

- `profiles.json` core profile templates will include GRAPHIFY.md and PROJECT_GRAPH.md.
- All projects will have access to the templates, but are not required to use them.
- sdd-onboard will scaffold PROJECT_GRAPH.md only if `.graphify/` is detected.

### Alternatives Considered

- **New `graphify-aware` profile:** Would require explicit opt-in. More control but more friction.
- **Not shipping templates at all:** Would require engineers to create their own. Loss of framework value.

### Decision (Chosen)

Ship templates in core. Let sdd-onboard decide when to scaffold PROJECT_GRAPH.md (based on detection).

### Concern: "Won't core profile make Graphify feel mandatory?"

**Response:** No, because:
- Core profile = framework documentation/patterns, not tool dependencies.
- If Graphify is absent, templates are ignored. They take ~400 lines on disk, zero operational cost.
- sdd-onboard scaffolds PROJECT_GRAPH.md only if `.graphify/` exists (passive detection).
- Documentation explicitly states Graphify is optional and non-mandatory.
- "Available for inspection" ≠ "required for operation".

---

## D003: Generalization Over Specificity

**Decided:** 2026-07-14  
**Status:** Accepted

### Decision

GRAPHIFY.md and PROJECT_GRAPH.md templates must be **completely generic**. No proyecto-cumbre-specific god nodes,
components, payment providers, or file paths.

### Rationale

1. **Reusability** — Templates should work for Java/Spring, Next.js, Angular, Rust, Go, etc.
2. **Maintainability** — One generic template is easier to maintain than forking for each project type.
3. **Framework value** — SDD should provide patterns that apply broadly, not project-specific guidance.
4. **Scalability** — New users can read the templates and immediately understand how to use Graphify in their project.

### Implications

- Use placeholder terms like `<component-name>`, `<payment-provider>`, `<file-path>` in examples.
- Remove all references to: MisaFunnelPage, EmailService, useCartStore, Stripe, Resend, EventFunnelModal, etc.
- Use generic command examples: `graphify tree <node>`, `graphify path A B`, `graphify affected-flows <file>`.
- Link to official Graphify documentation for project-specific setup.

### Alternatives Considered

- **Stack-specific templates:** Create separate GRAPHIFY-java.md, GRAPHIFY-nextjs.md, etc. Would be comprehensive but hard to maintain.
- **Include proyecto-cumbre examples in "Examples" section:** Would violate non-goals. Teaches the wrong pattern.

### Decision (Chosen)

Strict generalization. No proyecto-cumbre specifics in SDD framework.

---

## D004: sdd-onboard Detection vs. Recommendation

**Decided:** 2026-07-14  
**Status:** Accepted

### Decision

`sdd-onboard` skill:
1. **Detects** if `.graphify/` exists (passive, non-prescriptive).
2. **Scaffolds** PROJECT_GRAPH.md if detected (helpful structure).
3. **Does NOT recommend installation** if Graphify is absent.
4. **Mentions Graphify availability** in output (informational only).

### Rationale

1. **Non-mandatory principle** — We don't push engineers to install Graphify.
2. **Passive detection** — If it's there, we use it. If not, we skip it.
3. **Helpful scaffolding** — If a project has Graphify, PROJECT_GRAPH.md provides a home for the generated content.

### Implications

- sdd-onboard output will include a note like: "Graphify detected. Scaffolded docs/PROJECT_GRAPH.md." OR "Graphify not detected (optional)."
- No "Please install Graphify" recommendation.
- No blocked workflow if Graphify is absent.

### Alternatives Considered

- **Recommend installation by default:** Violates non-goals and non-mandatory principle.
- **Require Graphify:** Would violate spec non-goals.
- **Always scaffold PROJECT_GRAPH.md:** Would create empty/useless files in projects without Graphify.

### Decision (Chosen)

Passive detection. Scaffold only if detected. Mention availability.

---

## D005: graphify-stale-reminder Hook Safety

**Decided:** 2026-07-14  
**Status:** Accepted

### Decision

The existing `graphify-stale-reminder` hook (both `.ps1` and `.sh` variants) is a **reminder-only hook** that exits 0 always.
It never blocks a workflow. This behavior is correct and should not change.

### Rationale

1. **Non-blocking principle** — Graphify is optional. A reminder should never prevent work.
2. **Existing behavior is safe** — Hook already exists and works correctly.
3. **Graceful information** — Engineers see a message if the graph is stale or absent, but can proceed.

### Implications

- Hook behavior: unchanged.
- Hook documentation: clarify that it's a reminder (exits 0 always).
- Hook is wired by default in core profile: safe to keep wired.

### Alternatives Considered

- **Make hook blocking:** Would violate non-mandatory principle.
- **Remove hook:** Would lose useful reminders.

### Decision (Chosen)

Keep hook as-is. Clarify in documentation that it's a safe reminder.

---

## D006: Cross-Platform Alias Setup

**Decided:** 2026-07-14  
**Status:** Accepted

### Decision

GRAPHIFY.md will include separate alias setup sections for:
1. **PowerShell** (Windows): Set-Alias, function definitions for $PROFILE.
2. **Bash** (Linux/macOS): alias definitions for ~/.bashrc or ~/.zshrc.

These are **suggestions**, not auto-applied. Users copy-paste into their shell profiles.

### Rationale

1. **Cross-platform principle** — SDD is used on Windows, macOS, Linux.
2. **No auto-modification** — We don't modify user shell profiles automatically (would violate user control).
3. **Clear guidance** — Templates show exactly what to copy-paste.
4. **Shell diversity** — PowerShell and bash have different syntax.

### Implications

- GRAPHIFY.md has two separate "Aliases" sections (PowerShell and bash).
- Each section clearly labeled and copy-pasteable.
- Users verify aliases work before using them in critical workflows.

### Alternatives Considered

- **Single shell-agnostic setup:** Not possible given PowerShell and bash syntax differences.
- **Auto-install aliases into $PROFILE / ~/.bashrc:** Violates no-auto-modification rule.
- **Don't include aliases:** Would lose convenience, users rediscover them.

### Decision (Chosen)

Separate PowerShell and bash sections. Copy-paste pattern. User-controlled.

---

## D007: When to Recommend Graphify Usage in SDD Workflow

**Decided:** 2026-07-14  
**Status:** Accepted

### Decision

Within the SDD workflow:
1. **`/sdd-onboard`** — Detects Graphify, scaffolds PROJECT_GRAPH.md if present.
2. **Before `/spec-plan`** — Optionally recommend `/graphify-context` if GRAPH_REPORT.md exists (impact analysis).
3. **Before `/spec-analyze`** — Optionally reference GRAPH_REPORT.md for architecture context.
4. **Before code review** — Optional enhancement: use Graphify for review context.
5. **Fully optional** — All steps continue normally if Graphify is absent.

### Rationale

1. **Early detection** — onboarding is the right place to discover Graphify.
2. **Impact analysis before planning** — Graphify is most useful for understanding change scope before writing a plan.
3. **Architecture context before consistency check** — Graphify can inform the consistency gate.
4. **Review enhancement** — Graphify can speed up review, but review works without it.

### Implications

- Documentation (SDD-ORCHESTRATION.md) will clarify these optional touchpoints.
- Skills will mention Graphify as optional at these points.
- Workflows degrade gracefully if Graphify is absent.

### Alternatives Considered

- **Use Graphify everywhere:** Would make it seem mandatory.
- **Never mention Graphify in workflow:** Would leave engineers unaware of the opportunity.
- **Require Graphify at one specific point:** Would violate non-mandatory principle.

### Decision (Chosen)

Optional at multiple points, clearly marked as optional, workflows degrade gracefully.

---

## D008: No Modification to Existing Profiles or Default Profile

**Decided:** 2026-07-14  
**Status:** Accepted

### Decision

1. The default profile remains **`java-spring-backend`** (no change).
2. No changes to `java-spring-backend`, `messaging-event-driven`, `next-prisma-web`, `payments-fintech` profiles.
3. Graphify templates added to **core** profile only.
4. `blockchain-crypto` profile remains disabled (no change).

### Rationale

1. **Stability** — Changing defaults would be a breaking change for existing users.
2. **Simplicity** — Fewer changes = lower risk.
3. **Core profile** — Already the right place for stack-agnostic features.

### Implications

- profiles.json will have one change: core profile templates array includes GRAPHIFY.md and PROJECT_GRAPH.md.
- All other profiles remain unchanged.
- Existing installed SDD copies won't break.

### Alternatives Considered

- **Create new graphify-aware profile:** Would add complexity and require opt-in.
- **Add Graphify to every profile:** Would imply Graphify is mandatory for each stack.
- **Change default profile:** Would break existing setups.

### Decision (Chosen)

Add to core, don't touch existing profiles.

---

## D009: Project-Specific Context Stays in Projects, Not in SDD

**Decided:** 2026-07-14  
**Status:** Accepted

### Decision

The SDD framework ships **generic templates** and **generic guidance**. Project-specific context (e.g., "our project's god nodes are X, Y, Z") stays in the project's own `docs/PROJECT_GRAPH.md` or `docs/ARCHITECTURE.md`.

The SDD framework **never** includes hardcoded god nodes, specific components, specific payment providers, or specific file paths.

### Rationale

1. **Framework role** — The SDD is a process framework, not a project-specific knowledge base.
2. **Maintainability** — One framework doc is easier to maintain than dozens of project-specific variations.
3. **Portability** — Templates can be copied to new projects without modification.
4. **Clarity** — SDD docs are about HOW to use features, not WHAT your project does.

### Implications

- GRAPHIFY.md uses placeholder examples, not proyecto-cumbre examples.
- PROJECT_GRAPH.md is a template for each project to fill in with their own architecture.
- Engineers read the SDD template, then apply it to their project context.

### Alternatives Considered

- **Include proyecto-cumbre examples in SDD:** Would bloat the framework and teach wrong pattern.
- **Create project-specific variant templates:** Would be unmaintainable.

### Decision (Chosen)

SDD = process + templates. Projects = content. Strict separation.

---

## D010: Graphify as Read-Only in Skills

**Decided:** 2026-07-14  
**Status:** Accepted

### Decision

All SDD skills that use Graphify are **read-only**. They:
1. Read GRAPH_REPORT.md (if it exists).
2. Read .graphify/graph.json (if it exists).
3. **Do NOT modify** .graphify directory, Graphify config, or run Graphify commands.

The user (or external automation) runs Graphify separately. SDD skills only consume the output.

### Rationale

1. **Separation of concerns** — SDD manages the development process. Graphify manages the dependency graph.
2. **No external tool coupling** — SDD doesn't require Graphify to be installed, and doesn't auto-manage it.
3. **User control** — Engineers decide when/how to run Graphify. SDD just uses the results.
4. **Safety** — Read-only guarantees no side effects from SDD operations.

### Implications

- Skills like `graphify-context` read GRAPH_REPORT.md but don't run `graphify update`.
- If graph is stale, the skill notes it but doesn't re-run Graphify.
- sdd-onboard scaffolds templates but doesn't run Graphify.

### Alternatives Considered

- **Auto-run Graphify in skills:** Would add complexity, require Graphify installation, violate non-auto-run principle.
- **Enforce fresh graph:** Would require running Graphify, adding friction.

### Decision (Chosen)

Skills are read-only. Graphify is external. Users run it separately.

---

## D011: Documentation is Source of Truth for Feature Intent

**Decided:** 2026-07-14  
**Status:** Accepted

### Decision

The SPEC.md, PLAN.md, TASKS.md, and DECISIONS.md files are the **source of truth** for this feature.
If there's ambiguity during implementation, consult these documents before modifying behavior.

### Rationale

1. **SDD discipline** — We use our own methodology.
2. **Reviewability** — Design decisions are recorded and reviewable.
3. **Continuity** — Future developers can understand intent, not just code.

### Implications

- During implementation, if a task seems unclear, check the spec first.
- If implementation reveals a need to change the spec, update SPEC.md and mark the decision.
- Final PR should reference the feature folder (006-adaptive-project-onboarding-and-graphify).

### Alternatives Considered

- **Code comments as source of truth:** Loses structure, not reviewable, hard to reference.

### Decision (Chosen)

SDD docs are source of truth.

---

## Closure Summary (2026-07-14)

**Feature 006 is COMPLETE and VALIDATED.**

Key outcomes:
1. **Graphify remains optional.** SDD fully functional without it. No mandatory dependency.
2. **No user config modified.** Shell aliases are copy-paste suggestions, not auto-wired. No `.claude/` or shell profile changes.
3. **No proyecto-cumbre terms retained.** GRAPHIFY.md and PROJECT_GRAPH.md are generic, reusable across any stack.
4. **Templates shipped through core profile.** All projects get optional Graphify guidance; opt-in to use it.
5. **Graceful degradation preserved.** Three existing skills (graphify-context, context-manager, stale-reminder) degrade gracefully when Graphify is absent.
6. **Cross-platform support.** PowerShell and Bash alias suggestions provided.

All 11 decisions approved and validated during implementation. Feature meets all acceptance criteria.

---

## Open Questions Resolved

### Q: Should GRAPHIFY.md be mandatory reading?
**A:** No. It's a template for engineers who opt-in to Graphify.

### Q: Should sdd-onboard recommend Graphify installation?
**A:** No. That would make it seem mandatory. It's optional.

### Q: Should PROJECT_GRAPH.md be scaffolded if .graphify/ doesn't exist?
**A:** No. It would be an empty, confusing file. Scaffold it only if Graphify is detected.

### Q: What if a project has .graphify/ but it's broken or corrupted?
**A:** sdd-onboard will handle it gracefully (log note, continue). The skill doesn't rely on Graphify working perfectly.

### Q: Can engineers use SDD fully without ever installing Graphify?
**A:** Yes, absolutely. Graphify is an optional accelerator.

### Q: Should we auto-install Graphify?
**A:** No. See non-goals.

### Q: Should we auto-update the Graphify graph?
**A:** No. Skills are read-only. Engineers run `graphify update` separately.

### Q: Should we create a separate Graphify profile?
**A:** No. D002 decided to add templates to core for simplicity.

---

## Decisions Carried Forward from Earlier Phases

- **Graceful degradation principle** (Phase 5, framework hardening): All features degrade gracefully when optional components are absent.
- **Cross-platform support** (Phase 5): All new features support Windows, macOS, Linux.
- **User control principle** (all phases): SDD tools support but never override user decisions.
- **Template-based scaffolding** (core SDD principle): New features scaffold templates, not modify application code.

---

## Review Checklist

Before marking this feature as "Ready," verify:

- [ ] All decisions are documented above.
- [ ] All implications are clear.
- [ ] No contradictions between decisions.
- [ ] All non-goals are respected in decisions.
- [ ] All decisions align with SDD philosophy (user control, no mandatory external tools, graceful degradation).

---

## Next Phase: Implementation

The PLAN.md and TASKS.md describe how to implement these decisions.
Each task should be completed in alignment with the decisions recorded here.
