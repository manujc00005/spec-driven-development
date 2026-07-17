# Feature Spec: adoption-horizon

## Status

Done

## Problem

The audit's roadmap Horizon 2: the repo is solid but the adoption barrier is
high. The only worked example is Java/Spring (the `next-prisma-web` profile has
no demonstration); the README explains the *what* well but time-to-first-spec
requires reading all of INSTALL.md; there are no releases or changelog (looks
like an experiment, not a maintained project); and there is no contributor
entry point.

## Goal

Four blocks, one commit each:

1. **Second worked example** (`examples/002-server-action-rate-limiting/`):
   a Next.js server action with zod validation and an in-memory sliding-window
   rate limiter — TypeScript counterpart to the Java example, exercising the
   `next-prisma-web` profile's domain. Full SDD artifact set + educational src.
2. **Quickstart** at the top of README.md: clone → install → link → wire-hooks
   → `/project-init` → first spec, copy-pasteable in under 5 minutes.
3. **Releases**: CHANGELOG.md (Keep a Changelog format) + annotated tag
   `v0.5.0` pushed.
4. **Contributing**: CONTRIBUTING.md + GitHub issue templates (bug, feature).

## Non-goals

- Asciinema/GIF recording (needs a real terminal session; roadmap polish).
- A runnable Next.js project (the example ships educational source fragments,
  same convention as example 001 — no package.json/tsconfig).
- Redis/durable rate-limit store in the example (documented as the production
  swap point, deliberately out of scope).
- Bumping `profiles.json` `version` — that field is the manifest schema
  version, not the release version; releases are git tags.

## Functional requirements

- FR-001: Example 002 ships SPEC, PLAN, TASKS, DECISIONS, README,
  IMPLEMENTATION_SUMMARY, REVIEW_REPORT plus `src/` (server action, zod schema,
  sliding-window limiter, client-IP helper) and vitest-style tests covering
  validation, window boundaries, and header-spoofing cases. Educational
  disclaimers equivalent to example 001's ("pattern walkthrough, not a
  production system").
- FR-002: `examples/README.md` lists both examples; main `README.md` example
  references and the "one worked example" limitation line are updated.
- FR-003: README.md gains a Quickstart section near the top with the five
  copy-pasteable steps (macOS/Linux and Windows variants) and a link to
  INSTALL.md for depth. The staged README change must not include the parallel
  session's uncommitted counter edits.
- FR-004: CHANGELOG.md documents releases from the first commit to v0.5.0
  (grouped by the spec trail, Keep a Changelog format); annotated tag `v0.5.0`
  created and pushed.
- FR-005: CONTRIBUTING.md covers: dev setup, the SDD dogfooding rule (features
  need a spec), the consistency harness + test suites as the merge gate,
  sh/ps1 parity requirement, and commit conventions.
  `.github/ISSUE_TEMPLATE/bug_report.md` + `feature_request.md` exist.

## Acceptance criteria

- AC-001: Example 002 artifacts complete; consistency harness and both test
  suites still pass; no "production-ready" claims (grep clean).
- AC-002: Quickstart present; committed README contains no uncommitted
  parallel-session counters (README markers/badges still consistent in CI).
- AC-003: `git tag -l v0.5.0` shows the tag locally and on origin; CHANGELOG.md
  covers 0.1.0 → 0.5.0 with dates from git history.
- AC-004: CONTRIBUTING.md + two issue templates exist and are linked from
  README's contributing section.

## Edge cases

- README is concurrently modified by another session (uncommitted 52-skills
  counters): stage from HEAD + quickstart overlay, keep working-tree overlay
  intact (same maneuver as the 011 cherry-pick).
- Example rate limiter must not be presentable as secure-by-default: README and
  DECISIONS must state the in-memory store resets on deploy/restart and is
  per-instance (not distributed).

## Test scenarios

- Harness + graphify suite + self-test after each block.
- grep for forbidden claims in the new example.
- CI on push validates README counters were not polluted.

## Assumptions

- Educational-fragments convention (no build files) matches example 001 and is
  what `examples/README.md` already documents.
- v0.5.0 is the right first tag: 0.x signals pre-1.0; the spec trail (000→012)
  maps to 0.1.0–0.5.0 milestones in the changelog.
- The GitHub Release object can be created later from the pushed tag via the
  web UI (no gh CLI on this machine).

## Open questions

- None.
