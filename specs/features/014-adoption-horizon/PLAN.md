# Implementation Plan: adoption-horizon

## Summary

Roadmap Horizon 2 in four independent, commit-sized blocks: TS/Next worked
example (server action + zod + sliding-window rate limiter), README quickstart,
CHANGELOG + v0.5.0 tag, CONTRIBUTING + issue templates.

## Related spec

`specs/features/014-adoption-horizon/SPEC.md`

## Impacted areas

`examples/002-server-action-rate-limiting/` (new) · `examples/README.md` ·
`README.md` (quickstart + example links, surgically staged) · `CHANGELOG.md`
(new) · `CONTRIBUTING.md` (new) · `.github/ISSUE_TEMPLATE/` (new) · git tag.

## Proposed approach

Example mirrors 001's conventions: full SDD artifact set, educational source
fragments (no build files), explicit not-production disclaimers, review
artifact included. Content chosen for security teaching value: zod validation
before work, sliding-window limiter with LRU eviction, client-IP trust
boundary (x-forwarded-for spoofing), fail-closed behavior, constant-shape
responses. README quickstart staged from HEAD to avoid committing the parallel
session's uncommitted counters. Changelog reconstructed from the spec trail
and git history dates. Tag annotated, pushed explicitly.

## Alternatives considered

- SEO-flow example (seo-geo-addon) — rejected for now: that profile is one
  session old and its skills are still settling; rate limiting is
  stack-representative and security-juicy.
- Runnable example app — rejected: example 001 set the fragments convention;
  a buildable app doubles maintenance for little teaching gain.

## Dependencies

None external. Tag push requires the already-configured origin.

## Risks

- Concurrent README edits (mindset-skills session): mitigated by surgical
  staging; their working-tree deltas preserved.
- Example code must survive scrutiny as *teaching* code — review artifact
  includes its own security findings to model honesty.

## Test strategy

Harness + graphify suite + self-test after each block; claim-grep on the new
example; CI validates the pushed README state.

## Rollback strategy

Each block is one revertable commit; the tag can be deleted
(`git push --delete origin v0.5.0`) if the release needs to be pulled.

## PLAN verification checklist

- [x] The plan covers all acceptance criteria.
- [x] The plan avoids behavior outside the spec.
- [x] Risks are documented.
- [x] Test strategy is documented.
- [x] Rollback strategy is documented.
- [x] SPEC.md status is In Progress.
