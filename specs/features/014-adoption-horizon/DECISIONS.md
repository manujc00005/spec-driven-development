# Decisions: adoption-horizon

## Decision log

### D001 - Rate-limiting example over SEO example

**Date:** 2026-07-17

**Status:** Accepted

**Context:** Two candidates for the TS example: seo-geo-addon flow or a server
action with validation + rate limiting.

**Decision:** Server action + rate limiting.

**Reasoning:** Stack-representative for `next-prisma-web`, rich in security
teaching moments (trust boundaries, spoofable headers, fail-open vs
fail-closed), and independent of the one-session-old seo-geo-addon profile.

**Consequences:** The seo-geo-addon profile remains without a worked example
(future candidate).

### D002 - Educational fragments, not a runnable app

**Date:** 2026-07-17

**Status:** Accepted

**Context:** Example 001 ships source fragments without build files.

**Decision:** Example 002 follows the same convention: `src/` fragments +
vitest-style tests, no package.json/tsconfig.

**Reasoning:** Consistency between examples; a buildable app doubles
maintenance surface for no additional teaching value — the artifact set and
the pattern are the product.

**Consequences:** Tests are read, not executed, by visitors; stated up front.

### D003 - Releases are git tags; profiles.json version stays a schema version

**Date:** 2026-07-17

**Status:** Accepted

**Context:** `profiles.json` carries `version: 0.4.0`, documented as the
manifest/schema compatibility marker.

**Decision:** Repo releases use annotated git tags + CHANGELOG.md; v0.5.0 is
the first tag; profiles.json is not bumped by releases.

**Reasoning:** Conflating manifest schema compatibility with release cadence
would force schema bumps on every release. Also avoids touching a file the
parallel session currently holds dirty.

**Consequences:** Two version axes exist; CHANGELOG explains the distinction.

### D004 - Surgical README staging (repeat of the 011 maneuver)

**Date:** 2026-07-17

**Status:** Accepted

**Context:** A parallel session holds uncommitted README counter edits (52
skills) whose folders are untracked; committing them would break CI.

**Decision:** Stage README as HEAD + quickstart overlay; restore the combined
working-tree version (theirs + mine) after committing.

**Reasoning:** Keeps CI green and each feature's diff attributable.

**Consequences:** One more manual overlay; documented here for traceability.
