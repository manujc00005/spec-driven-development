# Implementation Plan: python-sql-data-profile

## Summary

Add one profile object to `profiles.json`, five `SKILL.md` files, one guide under `docs/`, and
short mentions in `README.md`, `CHANGELOG.md` and the Codex parity matrix. No new agent, no
installer change, no checker change.

## Related spec

`specs/features/029-python-sql-data-profile/SPEC.md`

## Impacted areas

| Path | Change |
|---|---|
| `profiles.json` | one new profile object, inserted before `blockchain-crypto` |
| `skills/python-reviewer/SKILL.md` | new |
| `skills/sql-query-reviewer/SKILL.md` | new |
| `skills/database-performance-reviewer/SKILL.md` | new |
| `skills/data-pipeline-reviewer/SKILL.md` | new |
| `skills/python-testing-reviewer/SKILL.md` | new |
| `docs/PYTHON_SQL_PROFILE.md` | new |
| `README.md` | profile table row, current-support row, profile list, count markers/badges |
| `CHANGELOG.md` | `[Unreleased] / Added` entries |
| `adapters/codex/PARITY.md`, `adapters/README.md`, `adapters/claude/README.md`, `adapters/codex/prompts/README.md`, `docs/AGENTIC_ROUTING.md` | honest not-ported gap row + stale hardcoded skill counts |
| `agents/**` | **untouched, by requirement (FR-015)** |
| `scripts/check-consistency.sh` | **untouched** — existing generic rules already cover this (D005) |
| `install.sh`, `install.ps1` | **untouched** — profile resolution is manifest-driven |

## Context budget

### Reading list

- `profiles.json` (the whole manifest — it is the artifact being changed).
- `scripts/check-consistency.sh` — to establish what is already validated generically, which
  decides whether FR-014 needs code.
- One existing profile as a shape reference (`delivery-operations`, the most recent) and one
  existing reviewer skill as a prose reference (`skills/container-review/SKILL.md`).
- `specs/_templates/{SPEC,PLAN,TASKS,DECISIONS}.md`.
- `README.md` only around the profile table, the counts and the support table.
- `CHANGELOG.md` `[Unreleased]` section only.
- `agents/domain-reviewer.md` — read-only, to confirm no change is required there.

Explicitly **not** read: other feature specs, archived specs, `install.sh` / `install.ps1` bodies,
the rest of `skills/`, hooks.

### Model routing

Single-session authoring work: writing prose review checklists and one JSON object. No deep
reasoning phase, no delegation, no subagent. The one judgment call worth thinking about — dual
routing versus a routing note (D002) — is a five-minute read of the checker plus two precedents.

## Proposed approach

1. **Establish the ground rules first.** Read `check-consistency.sh` to learn the contract every
   skill must satisfy (contract keys, enums, description cap, body cap) and what the profile must
   satisfy (routing coverage, routed-skill existence). Authoring against known rules beats
   authoring then fixing.
2. **Write the five skills**, each in the shape the repo already uses: frontmatter with
   `name`/`description`/`triggers`, `## SDD Contract`, purpose, what it checks, an explicit
   "does NOT do" section naming the tools it does not replace, output format, context economy.
3. **Insert the profile** into `profiles.json` before `blockchain-crypto`, with `agentRouting`
   under `domain-reviewer` and a note recording secondary `security-reviewer` consumption.
4. **Run the checker.** Expect it to fail only on README counts — any other failure means the
   skills or routing are wrong, which is the point of running it before writing docs.
5. **Write `docs/PYTHON_SQL_PROFILE.md`**, then the short README and CHANGELOG entries.
6. **Fix counts with `check-consistency.sh --fix`**, which owns the markers and badges.
7. **Sweep for claims** with the exaggerated-claim grep and classify every hit.

Ordering matters in one place: the checker runs **before** the documentation, so documentation is
never written around a manifest that does not validate.

## Alternatives considered

- **One combined `python-sql-reviewer` skill.** Rejected: the five concerns have different
  triggers (a `.py` change is not a `.sql` change is not a scheduled-job change) and different
  owners of the answer. A single skill would be loaded whole for a one-line query change.
- **A dedicated Python or SQL agent.** Rejected by the feature's own constraints, and correctly:
  `domain-reviewer` already exists to be the profile-aware reviewer, and a new agent would need
  its own routing, its own boundaries, and a reason these skills cannot be consumed by the agent
  built for exactly this.
- **Listing security-adjacent skills under both `domain-reviewer` and `security-reviewer` in
  `agentRouting`.** Rejected — see D002.
- **Adding a `python-sql-data` check class to `check-consistency.sh`.** Rejected — see D005.
- **Folding these into the existing `database-review` skill.** Rejected: that skill is about
  schema, migrations and constraints. Query correctness and query cost are different questions
  with a different audience, and merging them would make one large skill worse at both.
- **Shipping a `sqlfluff`/`ruff` config alongside the profile.** Rejected as scope: the profile
  reviews, it does not configure the project's toolchain.

## Dependencies

None. No new external tool, no library, no service. The profile is inert text consumed by an agent.

## Risks

| Risk | Mitigation |
|---|---|
| A reviewer asserts a query plan it cannot know | `database-performance-reviewer` labels every finding structural or conditional, and conditional findings are phrased as "run `EXPLAIN` and check X" (D004) |
| Engine-specific SQL rules applied to the wrong engine | `sql-query-reviewer` states the assumed engine in its output and defers engine-specific rulings when the engine is unknown (D003) |
| The profile reads as data-engineering coverage | Explicit non-goal in SPEC, in the profile `note`, in `data-pipeline-reviewer`, in `docs/PYTHON_SQL_PROFILE.md` and in CHANGELOG |
| A skill is read as a substitute for `ruff`/`mypy`/`pytest`/`sqlfluff`/`EXPLAIN` | Every skill carries a "does NOT replace" section; the guide repeats it; a grep sweep checks for the claim shape |
| Value unproven — the skills have never run on a real diff | Recorded as OQ-2, not hidden. First real use is a calibration pass |
| Live install unverified | Recorded as OQ-1 |
| Duplicate spec number across machines | 025 was already taken locally by `025-workspace-sdd-graphify-onboarding`; the branch list was fetched before claiming 029 |

## Test strategy

- `bash scripts/check-consistency.sh` → exit 0 (the acceptance gate for AC-001..005, AC-009, AC-011).
- `python3 -m json.tool profiles.json` → exit 0 (AC-001).
- `bash scripts/check-consistency.test.sh` → the existing suite must pass unchanged, proving no
  existing profile or check regressed.
- Negative evidence: the checker was observed failing on this very change (README counts) before
  the fix, which is what makes its final pass meaningful.
- `bash install.sh --profile python-sql-data --dry-run` → profile resolves, five skills reported.
- Claim grep across README, `docs/`, `skills/`, `profiles.json`, `CHANGELOG.md` and this spec
  folder, with every hit classified.
- `git status` → nothing under `agents/` (AC-010).

## Rollback strategy

Every change is additive and confined to new files plus small insertions. Rollback is deleting
`skills/{python-reviewer,sql-query-reviewer,database-performance-reviewer,data-pipeline-reviewer,python-testing-reviewer}/`,
`docs/PYTHON_SQL_PROFILE.md` and `specs/features/029-python-sql-data-profile/`, reverting the
`profiles.json` object and the README/CHANGELOG/adapters edits, then running
`scripts/check-consistency.sh --fix` to restore the counts. Nothing is committed by this feature,
so `git checkout` plus removing the untracked files is the whole procedure. No installed project
is affected until someone re-runs the installer.

## PLAN verification checklist

- [x] The plan covers all acceptance criteria.
- [x] The plan avoids behavior outside the spec.
- [x] The Context budget section is filled (reading list + model routing), not left as placeholder.
- [x] Risks are documented.
- [x] Test strategy is documented.
- [x] Rollback strategy is documented.
- [x] SPEC.md status has been updated to `Ready`.
