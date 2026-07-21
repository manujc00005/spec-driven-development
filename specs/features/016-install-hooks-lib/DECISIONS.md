# DECISIONS — 016 Install hooks/lib in profile mode

| # | Decision | Rationale | Status |
|---|---|---|---|
| D1 | Copy `hooks/lib/` unconditionally in profile mode, not model it in profiles.json | It is a shared dependency of the selected hooks, not a selectable item; listing it as a "hook" would imply it can be omitted. | Active |
| D2 | Reuse `copy_tree_safely` / `Copy-TreeSafely` | Inherits new/identical/differs+backup semantics and dry-run handling → AC-03 by construction, no new copy logic to maintain. | Active |
| D3 | Regression test asserts *behavior* (guardrail exit 2), not just file presence | File presence alone would pass even if a future refactor broke sourcing; the exit-2 check pins the actual safety property. | Active |
| D4 | `install.ps1` fixed for code parity, runtime verification deferred to the Windows spot-check backlog | No Windows runtime available in this session (same status as the spec-015 update.ps1 spot-check). | Open (T07) |
| D5 | No commit; branch strategy left to the user | Audit constraint. Current branch `feat/adopt-graphify-skill` carries unrelated in-flight work — recommend a dedicated branch off main. | Active |
