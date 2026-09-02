# Implementation Plan: multi-profile-routing-and-installation

## Summary

Two halves that share one cause — the framework's single-profile assumption.

**Routing half (documentation-only).** `domain-reviewer` stops resolving "the active profile" and
starts selecting reviewer skills from the changed file paths in the diff, matched against each
skill's `description`. The singular framing is removed from every artifact that carries it, the
review output names which reviewers ran and what selected them, and one new `check-consistency.sh`
rule defends the routing-ownership convention that spec 029 D002 rests on.

**Installation half (shell/PowerShell).** `install.sh` / `install.ps1` gain `--all-profiles` /
`-AllProfiles`, which expands to every non-disabled, non-billable profile; `profiles.json` gains an
additive `billable` key so the installer can act on that distinction instead of guessing from prose;
`update.sh` / `update.ps1` report enabled profiles absent from `.sdd-install.json` without
installing them.

No new agent, no new profile, no new skill, no change to any profile's skill list.

## Related spec

[`SPEC.md`](./SPEC.md) — status `Draft` at the time of writing, promoted to `Ready` by this plan.

## Impacted areas

**Routing half**

| Artifact | Change |
|---|---|
| `agents/domain-reviewer.md` | Frontmatter `description`, Responsibility, Inputs, Method, Allowed actions, When to run, Stop conditions, Output format |
| `agents/README.md:22` | `domain-reviewer` row — "the active profile ships" |
| `docs/AGENTIC_ROUTING.md:127,137,141` | Responsibility / Allowed actions / When it runs |
| `agents/security-reviewer.md:28,62` | Same singular framing — beyond AC-014's literal list, see [D004](./DECISIONS.md) |
| `skills/security-review/SKILL.md:37` | Same, see [D004](./DECISIONS.md) |
| `skills/database-performance-reviewer/SKILL.md` | FR-005 coexistence note with `java-performance-reviewer` |
| 4–6 reviewer `description` lines | FR-004b — name the artifact, stay under the 400-char cap |
| `scripts/check-consistency.sh` (rules 1–7 block, ~L400–510) | One new rule: routed skill's `primary_agent` must equal its routing agent |
| `scripts/check-consistency.test.sh` | One positive + one negative case |

**Installation half**

| Artifact | Change |
|---|---|
| `profiles.json` | `billable: true` on `seo-geo-addon`; `version` 0.4.0 → 0.5.0 |
| `install.sh` (arg loop L84–97, resolver L175–300) | `--all-profiles` flag + resolver expansion |
| `install.ps1` (param block, resolver) | `-AllProfiles` switch, same semantics |
| `scripts/update.sh` (manifest block L116–210) | New-profile report, gated on a manifest that actually parsed |
| `scripts/update.ps1` (L110–170) | Same report — parity, see [D003](./DECISIONS.md) |
| `scripts/update.test.sh` | New-profile case + corrupt-manifest case |
| `docs/INSTALL.md` | Multi-stack flow end to end |

**Not touched:** `.sdd-install.json` schema, any profile's skill list, `adapters/codex/install-codex.sh`
(no profile concept exists there — the spec's Non-goals record this as an honest gap).

## Context budget

### Reading list

Bounded and justified — no whole-repo scan is needed for either half.

- `specs/features/030-multi-profile-routing-and-installation/*` — the feature folder.
- `profiles.json` — full read (366 lines); it is the shared artifact of both halves.
- `install.sh` L84–110 (arg loop) and L175–300 (python resolver). The rest of the 1124-line file
  is copy/link/backup machinery this feature does not touch.
- `install.ps1` param block and its resolver — the PowerShell mirror of the same two regions.
- `scripts/update.sh` L109–210 (manifest read + install args) and `scripts/update.ps1` L110–170.
- `scripts/check-consistency.sh` L338–510 — the SDD Contract + agentRouting block only.
- `scripts/check-consistency.test.sh` L44–95 (the `assert_case` helpers) and one existing mutation
  case as the pattern; `scripts/update.test.sh` L28–64 (`build_env`) and one existing case.
- `agents/domain-reviewer.md`, `agents/README.md`, `docs/AGENTIC_ROUTING.md`,
  `agents/security-reviewer.md` — full reads; all are short.
- Reviewer `description` frontmatter lines only, via grep — **not** the 26 skill bodies. Reading
  the bodies to fix their descriptions would reproduce in the plan the exact cost the NFR forbids
  at review time.
- `skills/review-all/SKILL.md` — the precedent for condition-based routing (spec Assumptions).

Explicitly **out of budget:** other specs' folders, `graph.json`, the skill bodies of the reviewer
catalogue, and the ~800 lines of `install.sh` outside the two named regions.

### Model routing

- **Deep model (`deep-reasoner` / main session):** T004–T007 (the `domain-reviewer` rewrite — this
  is the feature's one genuine design surface, turning a profile lookup into a per-file selection
  rule that must not over- or under-fire); T010 (the checker rule, which must not break
  `secondary_agents`); T013 (the `update.sh` report's degrade-vs-list branch, where AC-010's failure
  mode lives); T023, the AC-003 executed run and the reading of its transcript.
- **Cheap model (`fast-worker`):** the PowerShell mirrors once their bash originals exist (T012,
  T014), the description edits (T008), the doc sweeps (T015, T016, T017), the test cases once the
  rule exists (T018, T019, T020), and the baseline capture/compare (T001, T021).
- **No agent or tool beyond Read/Grep/Edit/Bash is justified anywhere in this feature.** No Graphify
  query is needed: the impacted set is enumerated above from direct inspection, and it is small.

## Proposed approach

**Order matters in exactly one place.** T001 captures the `install.sh --dry-run` baseline **before
any edit lands**, at a fixed `--central-dir` path. Dry-run output was verified deterministic across
runs at identical paths (420 lines, byte-identical), so AC-011 is achievable as a literal byte
comparison — but only against a baseline taken from the pre-change tree. Capture it first or lose
the acceptance criterion.

**Routing half.** Replace the profile lookup with a two-step selection rule stated in
`domain-reviewer.md`: (1) read the changed paths in the diff; (2) select the reviewer skills whose
`description` names those artifacts, from the skills installed on this machine. The installed set
is the ceiling, the diff is the selector, and nothing in between holds "which profiles apply" —
this is FR-015's removal of the concept, not a relocation of it. The stop condition narrows to the
one case that genuinely does not resolve: a changed artifact that no installed reviewer's
description claims **and** that plausibly needs one. Multiple profiles installed is never itself a
stop. The output format loses `# Profile detected` and gains a line naming each reviewer with the
changed files that selected it (FR-016, scoped to this agent alone by [D007](./DECISIONS.md)) — a reviewer that did not fire becomes visible by absence
from a list that says what it was selecting over.

FR-004b makes the `description` a load-bearing routing signal, so the reviewer catalogue is audited
once (T002) and the descriptions that name only a concern — the generic bases `api-review`,
`backend-review`, `frontend-review`, `database-review`, and `release-readiness` /
`microservices-patterns-reviewer` on inspection — gain a file-type anchor. The 400-char cap from
spec 022 is a hard constraint here: the longest description today is 381 characters, so these edits
have single-digit headroom in places and must trade words, not append them.

**Checker rule.** The routing loop at `check-consistency.sh:474` already walks
`profiles[*].agentRouting[<agent>].skills`. The contract parse happens in a separate earlier loop
that discards its result, so the minimal change is to keep a `skill → primary_agent` map from that
first loop and compare it in the second. One rule, one error category (`agent-routing`), consistent
with the existing generic style. Verified against the repository as shipped: **0 mismatches across
29 routed skills**, so the rule lands green with no migration and no grandfathering — OQ-4's claim
re-confirmed independently during planning.

**Installer.** `--all-profiles` sets a flag that the existing python resolver expands: every profile
key that is not `disabled: true` and not `billable: true`, with `core` prepended by the existing
dedupe. The flag never touches the explicit path, so naming a disabled profile still hard-errors
(AC-007) and naming `seo-geo-addon` explicitly still installs it (AC-008). Skipped billable
profiles are named in the output (AC-017) rather than silently dropped.

**Updater.** After the manifest read, compare `profiles.json`'s non-disabled keys against
`MANIFEST_PROFILES` and report the difference with the exact `install.sh --profile <name>` command.
The report is gated on the manifest having parsed: on a missing or corrupt manifest the existing
code leaves `MANIFEST_PROFILES` empty, which would otherwise render every profile as "new" — the
exact wrong answer AC-010 names. That branch prints "cannot compare" instead.

## Alternatives considered

- **`--profile all` instead of a flag.** Rejected in the spec (OQ-1) and re-confirmed: `all` as a
  profile *name* collides silently the day someone adds a real profile called that, whereas the
  installer's current behaviour on an unknown name is a deliberate hard error.
- **Selecting reviewers by `triggers:` frontmatter.** Rejected by FR-004 and by the NFR: `triggers`
  is only visible once the skill file is open, so selecting by it across 71 installed skills means
  opening all 71 to decide which one to open. Zero tooling reads it today.
- **A project-level "active profiles" file** (OQ-6 option b). Rejected: an artifact adopters must
  keep truthful, and a stale one is worse than none.
- **Reading `.sdd-install.json` at review time** (OQ-6 option c). Rejected: it records what this
  *machine* installed, not what this *repository* is.
- **A checker rule for FR-004b** (OQ-8). Rejected — see [D008](./DECISIONS.md); the NFR caps this
  feature at exactly one new rule and a description-prose proxy repeats the false-positive problem
  spec 022 D006 documented.
- **Splitting into two specs.** Genuinely viable — see [D009](./DECISIONS.md) — and rejected on
  cost, not on principle. The tasks are phased so the two halves stay independently committable.

## Dependencies

- `python3` — already a hard requirement of `install.sh` and `update.sh`; no new dependency.
- `pwsh` for the PowerShell spot-check. Installed on this Mac, so T021 is executable locally for
  syntax and dry-run behaviour; a real Windows run remains out of reach and is recorded as such.
- AC-003 needs a repository with **both** `java-spring-backend` and `python-sql-data` installed and
  a diff touching a `.java` and a `.py` file. Constructing that fixture is part of T019, not an
  assumed pre-existing asset.
- No external service, no network, no library.

## Risks

- **R1 — the reviewer-selection rule is prose, and prose is not enforced (high likelihood, medium
  impact).** Nothing structurally prevents `domain-reviewer` from under-firing. The spec is honest
  about this ("no structural enforcement is claimed"), and AC-003's executed run is the only real
  evidence. Mitigation: the run is a task with an attached transcript, not a self-report — the
  repository's own history says a self-report is worth nothing.
- **R2 — description edits break the 400-char cap or a description's own meaning (medium/medium).**
  Six descriptions get edited under a hard cap with little headroom. Mitigation: T008 asserts the
  cap mechanically after editing, and the existing `check-consistency.sh` skill-form rules run.
- **R3 — the AC-011 baseline is captured after an edit lands, silently invalidating it (low/high).**
  It would produce a green comparison that proves nothing. Mitigation: [D005](./DECISIONS.md) fixes the method — T001 is first, writes to the
  scratchpad, and T021 records the capture commit alongside the diff.
- **R4 — `--all-profiles` over-installs on a future profile that is neither disabled nor billable
  but is stack-hostile (low/medium).** The blanket request is by definition unfiltered within the
  enabled set. Accepted: the adopter asked explicitly, and the output names everything it installed.
- **R5 — the new `update.sh` report nags an adopter who deliberately declined a profile
  (medium/low).** Known and accepted by OQ-3; revisit only if it proves annoying in practice.
- **R6 — the two halves land in one commit and a bisect cannot separate them (medium/low).**
  Mitigated by phasing, not by structure; see D009.

## Test strategy

- **Unit — `check-consistency.test.sh`:** a positive case (repository as shipped passes) and a
  negative case built the same way as the existing mutation-on-a-temp-copy cases — move a routed
  skill under a different agent in a temp copy of `profiles.json` and assert exit 1 with the
  `[agent-routing]` marker. (AC-004, AC-005)
- **Unit — `update.test.sh`:** a manifest recording fewer profiles than `profiles.json` declares,
  asserting the profile is named and *not* installed (AC-009, FR-012); and a corrupt manifest,
  asserting "cannot compare" and the absence of a full profile listing (AC-010).
- **Integration — blanket dry-run:** `install.sh --all-profiles --dry-run` asserts every enabled
  profile present, `blockchain-crypto` absent, `seo-geo-addon` absent and named as skipped.
  (AC-006, AC-007, AC-008, AC-017)
- **Integration — single-profile regression:** `install.sh --profile java-spring-backend --dry-run`
  at the same fixed central-dir as T001, diffed byte-for-byte against the pre-change baseline.
  (AC-011)
- **Static:** grep the reviewer catalogue for descriptions naming no artifact (AC-016); grep shipped
  artifacts for `triggers:` presented as the selector (AC-015); grep for surviving "active profile"
  instructions (AC-014).
- **Manual, and the one that matters:** the executed polyglot `domain-reviewer` run with a transcript
  (AC-003). Structural tests cannot substitute for it — they can only confirm the documentation says
  the right thing, which is precisely the evidence the spec refuses to accept.
- **Regression:** `check-consistency.sh`, `check-consistency.test.sh`, `update.test.sh`,
  `graphify.test.sh` all green (AC-013), plus `install.test.sh` since `install.sh` changes.
- **Not tested here:** the Windows PowerShell paths, beyond a local `pwsh` syntax and dry-run
  spot-check. Stated as a gap, not implied as covered.

## Rollback strategy

Every change is additive and revertible in isolation:

- **Checker rule:** delete the rule block; the map it reads is inert without it.
- **`--all-profiles` / `-AllProfiles`:** removing the flag restores the previous arg loop exactly;
  no existing invocation changes shape.
- **`billable` key:** an installer reading a manifest without it sees no billable profiles and
  behaves as today, so the key can be dropped from `profiles.json` independently of the code.
  Reverting the `version` bump is a one-line edit.
- **`update.sh` report:** additive output with no behaviour change — deleting the block restores
  byte-identical behaviour.
- **Documentation and agent files:** plain `git revert`. Nothing on disk depends on their content.

No migration, no data change, no adopter action required to roll back. An adopter who has already
run `--all-profiles` keeps the installed profiles — `install.sh` never deletes, and
`--remove-profile` is the existing path if they want them gone.

## PLAN verification checklist

- [x] The plan covers all acceptance criteria. (AC-001..AC-017 each map to at least one task; see
      the coverage note at the foot of `TASKS.md`.)
- [x] The plan avoids behavior outside the spec. Two deliberate extensions beyond the literal AC
      text are recorded as decisions rather than taken silently: D003 (`update.ps1` parity) and
      D004 (the `security-reviewer` sweep).
- [x] The Context budget section is filled (reading list + model routing).
- [x] Risks are documented (R1–R6).
- [x] Test strategy is documented.
- [x] Rollback strategy is documented.
- [x] SPEC.md status has been updated to `Ready`.
