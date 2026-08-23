# DECISIONS — 016 Install hooks/lib in profile mode

| # | Decision | Rationale | Status |
|---|---|---|---|
| D1 | Copy `hooks/lib/` unconditionally in profile mode, not model it in profiles.json | It is a shared dependency of the selected hooks, not a selectable item; listing it as a "hook" would imply it can be omitted. | Active |
| D2 | Reuse `copy_tree_safely` / `Copy-TreeSafely` | Inherits new/identical/differs+backup semantics and dry-run handling → AC-03 by construction, no new copy logic to maintain. | Active |
| D3 | Regression test asserts *behavior* (guardrail exit 2), not just file presence | File presence alone would pass even if a future refactor broke sourcing; the exit-2 check pins the actual safety property. | Active |
| D4 | `install.ps1` fixed for code parity, runtime verification deferred to the Windows spot-check backlog | No Windows runtime available in this session (same status as the spec-015 update.ps1 spot-check). | Open (T07) |
| D5 | No commit; branch strategy left to the user | Audit constraint. Current branch `feat/adopt-graphify-skill` carries unrelated in-flight work — recommend a dedicated branch off main. | Active |

---

### D00A - Status section added so the spec is visible to tooling

**Date:** 2026-08-22

**Status:** Accepted

**Context:**

This spec predates the `## Status` convention, so `/spec-status` and every automated sweep skipped
it entirely. A governance audit on 2026-08-22 found it only by grepping for SPECs *lacking* the
section. Being invisible is worse than being stuck: nothing could report the debt.

**Decision:**

Add `## Status: In Progress`. Do not promote further from an audit.

**Reasoning:**

`In Progress` is the lowest value consistent with the evidence, and promotion past it is
`/spec-review`'s job — hand-editing a spec to `In Review` or `Done` is exactly the unverified claim
`sdd-guardrails` section 11 forbids.

The evidence supports the implementation being complete: `hooks/lib/claude-json.sh` ships, both
installers copy it in profile mode, and `scripts/install.test.sh` asserts AC-01, AC-02 and AC-03 —
a suite that, as of spec 034, actually runs in CI (it did not before).

**Consequences:**

- T07 (Windows runtime spot-check) is **not a closure blocker**: AC-04 defers runtime verification
  by its own wording and requires only code parity, which is met.
- T08 ("review + commit") is satisfied in substance — the work is committed and on `main`; it was
  written under an audit constraint that no longer applies.
- Both remain unchecked because only `/spec-review` should retire them.
