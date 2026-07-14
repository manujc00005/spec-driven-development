---
status: All tasks completed
created: 2026-07-14
feature: 006-adaptive-project-onboarding-and-graphify
note: 9 tasks completed, ~5 hours total effort. All ACs validated.
approval_date: 2026-07-14
completion_date: 2026-07-14
---

# Task List — Adaptive Project Onboarding + Graphify Integration

## Acceptance Criteria Mapping

| AC | Task | Validation |
|---|---|---|
| AC-001 | A1 (GRAPHIFY.md) | Syntax check, grep for project-specific terms |
| AC-002 | A2 (PROJECT_GRAPH.md) | Syntax check, verify placeholders |
| AC-003 | B1 (sdd-onboard docs) | Doc review |
| AC-004 | B2 (SDD-ORCHESTRATION.md) | Content review |
| AC-005 | B4 (hooks/README.md) | Content review |
| AC-006 | B3 (profiles.json) | Valid JSON |
| AC-007 | A1 + A2 + C1 | Grep for zero proyecto-cumbre terms |
| AC-008 | A1 | Alias syntax validation |
| AC-009 | B5 (skill review) | Doc review, no regressions |
| AC-010 | A1, A2 | No auto-modifications |

---

## Phase A: Create Templates (1.5 hours) ✅ COMPLETED

### A1 — Create docs/_templates/GRAPHIFY.md (1 hour) ✅

**Maps to:** AC-001, AC-007, AC-008, AC-010

Generic Graphify setup guide. Extract patterns from proyecto-cumbre docs; remove all god nodes, specific components, payment providers.

**Output:**
- Intro (what, optional)
- Installation (pointer only)
- Commands (generic: `graphify tree`, `graphify path A B`)
- SDD integration (optional, before /spec-plan)
- Refresh guidelines
- Shell aliases (PowerShell + bash separate sections)
- Use cases (code review, debugging, feature dev — generic)
- Troubleshooting
- Further reading

**Acceptance:**
- [x] File exists at `docs/_templates/GRAPHIFY.md` (270 lines)
- [x] Valid Markdown, all sections present
- [x] Zero: MisaFunnelPage, EmailService, useCartStore, Stripe, Resend, EventFunnelModal, proyecto-cumbre, proycto-cumbre
- [x] PowerShell aliases present and syntactically valid
- [x] Bash aliases present and syntactically valid
- [x] No user shell profiles modified (copy-paste only)

**Status:** COMPLETE

---

### A2 — Create docs/_templates/PROJECT_GRAPH.md (30 minutes) ✅

**Maps to:** AC-002, AC-007, AC-010

Placeholder template for projects to fill with Graphify output.

**Output:**
- Generated date/metadata
- God nodes (placeholder table)
- Communities (placeholder list)
- Module structure (placeholder)
- Critical paths (placeholder)
- Refresh instructions (link to GRAPHIFY.md)

**Acceptance:**
- [x] File exists at `docs/_templates/PROJECT_GRAPH.md` (142 lines)
- [x] Valid Markdown
- [x] Placeholder sections clearly marked
- [x] Zero project-specific code names
- [x] Refresh instructions present

**Status:** COMPLETE

---

## Phase B: Update Skill + Docs (2 hours) ✅ COMPLETED

### B1 — Enhance skills/sdd-onboard/SKILL.md (30 minutes) ✅

**Maps to:** AC-003

Add Graphify detection section (Step 4b):
- If `.graphify/graph.json` OR `.graphify/GRAPH_REPORT.md` exists: scaffold `docs/PROJECT_GRAPH.md`
- If absent: skip silently
- Handle corrupted `.graphify/` gracefully

**Acceptance:**
- [x] Section added to skill docs (Step 4b documented, +17 lines)
- [x] Graphify detection logic documented
- [x] Graceful fallback behavior documented
- [x] No code changes (doc-only)

**Status:** COMPLETE

---

### B2 — Update docs/SDD-ORCHESTRATION.md (30 minutes) ✅

**Maps to:** AC-004

Add optional Graphify note: "Before `/spec-plan`, optionally run `/graphify-context` (if GRAPH_REPORT.md exists)."
Clarify: Graphify is optional and not required.

**Acceptance:**
- [x] Optional Graphify note added (+12 lines)
- [x] Points to GRAPHIFY.md template
- [x] Workflow diagram/text reflects optional nature
- [x] No breaking changes

**Status:** COMPLETE

---

### B3 — Update profiles.json (15 minutes) ✅

**Maps to:** AC-006

Add `GRAPHIFY.md` and `PROJECT_GRAPH.md` to core profile templates array.

**Acceptance:**
- [x] GRAPHIFY.md in core.templates
- [x] PROJECT_GRAPH.md in core.templates
- [x] JSON is valid (validated with PowerShell ConvertFrom-Json)
- [x] No other profiles modified

**Status:** COMPLETE

---

### B4 — Update hooks/README.md (15 minutes) ✅

**Maps to:** AC-005

Clarify `graphify-stale-reminder` is safe (exits 0, never blocks).

**Acceptance:**
- [x] Safety documented (exits 0, reminder-only, "always safe")
- [x] No breaking changes

**Status:** COMPLETE

---

### B5 — Verify existing skills (30 minutes) ✅

**Maps to:** AC-009

Review `graphify-context`, `context-manager`, `graphify-stale-reminder` — confirm graceful degradation is documented. No behavior changes needed.

**Acceptance:**
- [x] graphify-context: optional usage documented (already in SKILL.md)
- [x] context-manager: optional usage + fallback documented (already in SKILL.md)
- [x] stale-reminder: safe behavior verified (already in hooks/README.md, lines 33-34)
- [x] No regressions (existing behavior unchanged)

**Status:** COMPLETE (no changes needed)

---

## Phase C: Validation (1.5 hours) ✅ COMPLETED

### C1 — Syntax & Content Validation (1 hour) ✅

**Maps to:** AC-001, AC-002, AC-006, AC-007

- [x] GRAPHIFY.md: valid Markdown (no syntax errors)
- [x] PROJECT_GRAPH.md: valid Markdown (142 lines)
- [x] profiles.json: valid JSON (validated with PowerShell ConvertFrom-Json)
- [x] Shell scripts: existing hooks syntax valid (no new shell scripts added)
- [x] Grep GRAPHIFY.md + PROJECT_GRAPH.md for zero project-specific terms:
  - [x] "MisaFunnelPage": 0 matches
  - [x] "EmailService": 0 matches
  - [x] "useCartStore": 0 matches
  - [x] "Stripe": 0 matches (generic "payment provider" only)
  - [x] "Resend": 0 matches (generic "email provider" only)
  - [x] "EventFunnelModal": 0 matches
  - [x] "proycto-cumbre", "Proyecto Cumbre": 0 matches
  - [x] No obvious secrets (API_KEY, passwords, tokens): 0 matches

**Status:** COMPLETE

---

### C2 — Alias Syntax Check (30 minutes) ✅

**Maps to:** AC-008

- [x] PowerShell alias section in GRAPHIFY.md is syntactically valid
- [x] Bash alias section in GRAPHIFY.md is syntactically valid
- [x] Both are clearly separated and copy-pasteable
- [x] Safe practices: no auto-modification of user profiles

**Status:** COMPLETE

---

## Summary

| Phase | Task | Effort | Status |
|---|---|---|---|
| A | A1: GRAPHIFY.md | 1h | ✅ COMPLETE |
| A | A2: PROJECT_GRAPH.md | 30m | ✅ COMPLETE |
| B | B1: sdd-onboard docs | 30m | ✅ COMPLETE |
| B | B2: SDD-ORCHESTRATION.md | 30m | ✅ COMPLETE |
| B | B3: profiles.json | 15m | ✅ COMPLETE |
| B | B4: hooks/README.md | 15m | ✅ COMPLETE |
| B | B5: Verify skills | 30m | ✅ COMPLETE (no changes needed) |
| C | C1: Validation (syntax + content) | 1h | ✅ COMPLETE |
| C | C2: Alias check | 30m | ✅ COMPLETE |
| | **TOTAL** | **~5 hours** | **✅ COMPLETED** |

---

## Success Criteria

- [x] All 9 tasks completed
- [x] All AC validations passed
- [x] Zero proyecto-cumbre-specific code names in SDD docs (verified: 0 matches)
- [x] All shells/JSON/Markdown syntax valid (verified)
- [x] No regressions in existing skills/hooks (verified)
- [x] Graphify presence/absence gracefully handled (verified: graceful degradation documented)
