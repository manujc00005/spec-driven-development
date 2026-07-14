---
status: Implemented
created: 2026-07-14
approval_date: 2026-07-14
implementation_date: 2026-07-14
---

# Implementation Plan — Adaptive Project Onboarding + Graphify Integration

## Overview

This plan breaks the SPEC into three **implementation phases**. Minimal, focused, lean.
Phase A (templates) must complete before B (skill/doc updates). Phase C (validation) runs after both.

## Phase A: Create Generic Templates (1.5 hours)

**Goal:** Create two reusable Markdown templates extracted from proyecto-cumbre docs.

### A1: Create `docs/_templates/GRAPHIFY.md` (1 hour)

Extract generic Graphify patterns from proyecto-cumbre docs. Remove all god nodes, specific components, payment providers.

**Sections:**
- Intro (what, optional)
- Installation (pointer only)
- Common commands (generic: `graphify tree`, `graphify path A B`, etc.)
- SDD integration (optional, before /spec-plan)
- Refresh guidelines
- Shell aliases (PowerShell + bash)
- Use cases (code review, debugging, feature dev — generic)
- Troubleshooting
- Further reading

**Acceptance:** Valid Markdown; zero MisaFunnelPage/EmailService/useCartStore/Stripe/Resend/EventFunnelModal.

### A2: Create `docs/_templates/PROJECT_GRAPH.md` (30 minutes)

Simple placeholder template for projects to fill in with Graphify output.

**Sections:**
- Generated date
- God nodes (placeholder table)
- Communities (placeholder list)
- Module structure (placeholder)
- Critical paths (placeholder)
- Refresh instructions

**Acceptance:** Valid Markdown; clearly marked placeholders.

---

## Phase B: Update Skill + Framework Docs (2 hours)

**Goal:** Update sdd-onboard skill docs and core framework documentation.

### B1: Enhance `skills/sdd-onboard/SKILL.md` (30 minutes)

Add Graphify detection section (Step 4b):
- If `.graphify/graph.json` or `.graphify/GRAPH_REPORT.md` exists: scaffold `docs/PROJECT_GRAPH.md`.
- If not: skip silently.
- Handle corrupted `.graphify/` gracefully.

**Acceptance:** Section documented; behavior clear; no code changes (doc-only).

### B2: Update `docs/SDD-ORCHESTRATION.md` (30 minutes)

Add optional Graphify note: "Before `/spec-plan`, optionally run `/graphify-context` (if GRAPH_REPORT.md exists)."
Clarify: Graphify is optional.

**Acceptance:** Optional nature clear; points to GRAPHIFY.md template.

### B3: Update `profiles.json` (15 minutes)

Add `GRAPHIFY.md` and `PROJECT_GRAPH.md` to core profile templates array.

**Acceptance:** Valid JSON; templates present; no other profiles changed.

### B4: Update `hooks/README.md` (15 minutes)

Clarify `graphify-stale-reminder` is safe (exits 0, never blocks).

**Acceptance:** Safety documented.

### B5: Verify Skills (No changes needed) (30 minutes)

Review `graphify-context`, `context-manager`, `graphify-stale-reminder` — all already document graceful degradation.
No behavior changes. Doc-only clarifications in DECISIONS.md.

---

## Phase C: Validation (1.5 hours)

**Goal:** Verify implementation correctness.

### C1: Syntax & Content Validation (1 hour)

- [ ] GRAPHIFY.md and PROJECT_GRAPH.md: valid Markdown
- [ ] profiles.json: valid JSON (`jq . profiles.json`)
- [ ] Shell scripts: valid syntax (`bash -n hooks/graphify-stale-reminder.sh`)
- [ ] Grep for proyecto-cumbre terms: 0 matches
  - "MisaFunnelPage", "EmailService", "useCartStore", "Stripe", "Resend", "EventFunnelModal"

### C2: Spot-Check Aliases (30 minutes)

- [ ] PowerShell alias section in GRAPHIFY.md: syntactically valid
- [ ] Bash alias section in GRAPHIFY.md: syntactically valid
- [ ] Both are clearly separated and copy-pasteable

---

## Dependency & Execution

```
Phase A (1.5h) — Create templates
  ├─ A1: GRAPHIFY.md (1h)
  └─ A2: PROJECT_GRAPH.md (30m)
       ↓
Phase B (2h) — Update sdd-onboard + docs
  ├─ B1: sdd-onboard/SKILL.md (30m) — depends on A1, A2
  ├─ B2: SDD-ORCHESTRATION.md (30m) — depends on A1
  ├─ B3: profiles.json (15m) — depends on A1, A2
  ├─ B4: hooks/README.md (15m) — no dependency
  └─ B5: Verify existing skills (30m) — no dependency
       ↓
Phase C (1.5h) — Validate
  ├─ C1: Syntax + content check (1h) — depends on A, B
  └─ C2: Spot-check aliases (30m) — depends on A
```

**Total effort: 5 hours (not 18 hours)**
**Tasks: 9 (not 16)**
**Rollback:** Clean at any phase (delete templates, revert docs).

---

## Success Criteria

1. [ ] GRAPHIFY.md and PROJECT_GRAPH.md created; valid Markdown.
2. [ ] Zero proyecto-cumbre-specific code names in new templates.
3. [ ] sdd-onboard behavior documented (Graphify detection).
4. [ ] profiles.json updated; valid JSON.
5. [ ] SDD-ORCHESTRATION.md, hooks/README.md clarify optional Graphify.
6. [ ] Alias examples (PowerShell + bash) are syntactically valid.
7. [ ] No existing skills broken; no regressions.
