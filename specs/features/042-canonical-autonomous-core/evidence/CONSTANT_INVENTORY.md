# Constant inventory — T002

Every module-level constant in `runner/sdd_runner/`, its single current definition site, and its
target home. 61 constants across 14 modules, enumerated by an AST walk (module level only, upper-case
names, `_`-prefixed excluded).

## Method, and its known limit

A scan checked each constant's string literals against the eight prose surfaces of FR-012. **The scan
over-reports, and its output is a candidate list, not the classification.** Three demonstrated false
positives:

| Constant | "Matched" | Why it is a coincidence |
|---|---|---|
| `SECRET_ENV_HINTS` | 5 surfaces | Its values are substrings like `key` and `token`, which occur in unrelated prose everywhere. |
| `SAFE_NAMES` | 2 surfaces | Contains `PATH` and `AUTHOR`; both are ordinary English inside a document. |
| `IMPLEMENTATION_OBJECTIVE` | 7 surfaces | Its value is the word `implementation`. Every surface uses that word; none states this constant. |

It also **under**-reports: every `exits` code and both `budget` constants are integers, so a
string scan sees nothing, while `runner/README.md` and `docs/SDD-ORCHESTRATION.md` state all of them
in tables.

This is D005's failure mode appearing inside this feature's own tooling on its first run. It is
recorded here rather than fixed, because it is the concrete evidence T016's over-reach guard exists
to prevent: **a contract test must read the enumerated surface list, never search.**

## Classification

`policy` = the constant is protocol vocabulary a contract test can compare against a surface.
`module` = implementation detail no surface states; it stays where it is.

### → `policy.py` (39, plus the new `PROTOCOL_VERSION`)

| Constant | Current site | Stated by |
|---|---|---|
| `OK`, `GATE_REFUSED`, `HUMAN_ESCALATION`, `CAP_ABORT`, `BUDGET_EXHAUSTED`, `BACKEND_PRECONDITION`, `CONCURRENT_RUN`, `STATE_UNRESUMABLE`, `NOT_CONVERGED`, `CLOSURE_NOT_PROVEN`, `INTERNAL_ERROR`, `NAMES` | `exits.py` | `runner/README.md` exit-code table; `docs/SDD-ORCHESTRATION.md` |
| `SEVERITIES`, `FINDING_KEYS` | `blocks.py` | `SKILL.md`, both reviewer agent files (the closed enum) |
| `FLOOR`, `PER_TASK` | `budget.py` | `max(25, 6 × unchecked)` in `SKILL.md`, `README.md`, `docs/SDD-ORCHESTRATION.md` |
| `HUMAN_GATED` | `escalation.py` | `SKILL.md` — the six human-gated domains |
| `READY_STATUSES`, `ADOPT_STATUSES`, `REENTRY_STATUSES`, `KNOWN_STATUS_WORDS`, `RUN_ARTIFACTS` | `gate.py` | `SKILL.md` entry gate; `README.md`; `PARITY.md` |
| `ADOPTION_NOT_NEEDED`, `ALREADY_ENTERED`, `INHERITED_UNDETERMINED`, `STATUS_UNREADABLE` | `gate.py` | `README.md` exit-code prose; `docs/SDD-ORCHESTRATION.md` |
| `REVIEWERS`, `READ_ONLY_AGENTS`, `CORE_COMPLETE`, `AGENT_FILES`, `SECURITY_TRIGGERS` | `loop.py` | `SKILL.md` review circuit and Level-3 triggers; `README.md` |
| `TERMINAL_RESULTS`, `RECOVERABLE_RESULTS` | `resume.py` | `SKILL.md` termination/abort contract |
| `RUN_RESULTS`, `LIFECYCLE`, `INHERITED_COLUMNS`, `ATTEMPT_COLUMNS`, `FINDING_COLUMNS` | `state.py` | `templates/ORCHESTRATION.md` section shape; `SKILL.md` state contract |
| `FEATURES_ROOT` | `__main__.py` | The containment rule; every surface names `specs/features/` |

### → stays in its module (22)

| Constant | Site | Why it is not policy |
|---|---|---|
| `SECRET_ENV_HINTS`, `SAFE_NAMES`, `REDACTED` | `log.py` | Redaction internals. No surface states which env names are treated as secret; the scan's hits are substring coincidences. |
| `TASK_COMPLETE_OBJECTIVE`, `IMPLEMENTATION_OBJECTIVE`, `REPAIR_OBJECTIVE_PREFIX` | `resume.py` | Internal labels for attempt rows. The surfaces use these English words; none fixes these strings as a contract. |
| `PROGRAMMING_ERRORS`, `INSTALL_HINT` | `backends/claude.py` | Provider-adapter internals, behind the provider seam (FR-015). |
| `ISOLATION_FLAGS`, `PIN_FLAG`, `FLAGS_VERIFIED`, `GATE_MESSAGE` | `backends/codex.py` | Same seam. `PIN_FLAG` is stated by `scripts/skill-eval.sh`'s `PROVIDER_TABLE`, which is **not** one of the nine protocol surfaces — it is [[DEBT-001]]'s surface, and claiming it here would widen this feature's scope into spec 028. |
| `GENERATED`, `ALLOWED`, `UNEXPECTED`, `DELETED`, `UNREADABLE`, `CLOSURE_COLUMNS`, `VERIFY_PASS`, `VERIFY_NOT_DECLARED`, `VERIFY_FAILED`, `VERIFY_MUTATED` | `closure.py` | The **Finalizer's** vocabulary. `PROTOCOL_TRANSCRIPTION.md`'s scope note already records that `closure.classify/observe/unexpected` transcribe no clause this executor honours, and SPEC A-010 keeps them uncalled. Moving them into `policy` would have this core assert ownership of rules it does not execute. They move to `policy` in the Finalizer spec, not here. |

## Consequence for T003

`policy.py` holds 39 moved names plus `PROTOCOL_VERSION` (FR-009), which is new rather than moved:
40 in all. The 22 that stay are not exceptions to AC-001 — AC-001 requires each constant to be
defined **once**, not that every constant lives in `policy`. The single-definition test therefore
walks the whole package, and the surface-coverage tests read only the 39.

**Correction, same day.** An earlier draft of this table said 35 and 26. Both were miscounts of the
same list; 39 + 22 = 61 is the arithmetic that matches the AST walk. `test_policy` asserts
`len >= 39`, so the number is now checked rather than claimed.
