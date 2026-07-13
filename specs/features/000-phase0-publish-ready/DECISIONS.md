# Decisions: Phase 0 — Publish-ready baseline

> **Backfill note (2026-07-13, Phase 5).** This feature shipped before the repo enforced its
> full SDD document set; no contemporaneous decision log was kept. The entries below
> reconstruct the decisions that are evident from the shipped artifacts and commit
> `cdb0f67`. Reconstructed decisions are marked as such — this is a historical record, not
> a claim that the log existed at the time.

## Decision log

### D001 — MIT license (reconstructed)

**Date:** 2026 (Phase 0) · **Status:** Accepted

**Decision:** License the repo MIT rather than Apache-2.0 or a source-available license.

**Reasoning (evident):** Maximum reuse simplicity for a workflow/config repo with no
patent surface; standard for portfolio open-source.

### D002 — profiles.json as a declarative manifest (reconstructed)

**Date:** 2026 (Phase 0) · **Status:** Accepted (extended in later phases: 0.4.0 added
`agents`/`plannedAgents`)

**Decision:** Declare profile membership in a single JSON manifest consumed by both
installers, instead of hardcoding file lists in each script.

**Reasoning (evident):** One source of truth for two installers; later phases confirmed the
choice by extending the schema instead of forking logic.

### D003 — blockchain-crypto ships disabled (reconstructed)

**Date:** 2026 (Phase 0) · **Status:** Accepted

**Decision:** Declare the `blockchain-crypto` profile but mark it `disabled`; the installer
refuses to install it explicitly.

**Reasoning (evident):** Reserve the namespace and make the "off" state explicit and
enforced rather than implicit by absence.
