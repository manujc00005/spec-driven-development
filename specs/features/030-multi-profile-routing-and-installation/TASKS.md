# Tasks: multi-profile-routing-and-installation

<!-- Each task carries a `Verify:` clause after `Covers:` — the criterion anyone checks to call the
     task done. Nothing in the framework executes it; it is text for a human or an agent to act on.
     A human check names who checks and against what. -->

<!-- CLOSING A TASK THAT WAS NOT PERFORMED: `[x]` means "closed out of this spec", not always "the
     work was done". A task closed without being performed keeps the tick AND states how, on the
     line below — DEFERRED / SKIPPED (both need a DEBT id) or RESOLVED (nothing pending). -->

**Commit boundary (D009):** the routing half is T002, T004–T010, T015, T016, T018, T022, T023;
the installation half is T001, T003, T011–T014, T017, T019, T020, T021. T024–T026 close both. Land
the two halves as separate commits — they share only `profiles.json` and the suite run.

## Phase 1: Preparation

- [x] T001 - Capture the `install.sh --dry-run` regression baseline **before any other task edits a
  file**: `./install.sh --profile java-spring-backend --dry-run --central-dir
  "$SCRATCH/ac011/central" --claude-home "$SCRATCH/ac011/home" --skip-link > "$SCRATCH/ac011/baseline.txt"`.
  Record the HEAD SHA it was captured at. Covers: AC-011. Verify: `baseline.txt` is 420 lines, and
  `git log -1 --format=%H` at capture time is written into the file's first comment line or
  alongside it; re-running the identical command immediately reproduces it byte-for-byte
  (`diff` exits 0).

- [x] T002 - Audit all 26 reviewer skills routed to `domain-reviewer` and list which `description`
  lines name no artifact or file type. Do it by grepping the `description:` frontmatter lines only,
  not by opening skill bodies. Covers: AC-016, FR-004b. Verify: the audit output names each
  non-compliant skill with its current character count, and the count of compliant skills plus
  non-compliant equals 26.

## Phase 2: Implementation

- [x] T003 - Add `"billable": true` to `seo-geo-addon` in `profiles.json` and bump `version` from
  `0.4.0` to `0.5.0`. No other profile gains the key. Covers: FR-010, AC-008. Verify:
  `python3 -c "import json;d=json.load(open('profiles.json'));print(d['version'],[k for k,v in d['profiles'].items() if v.get('billable')])"`
  prints `0.5.0 ['seo-geo-addon']`.

- [x] T004 - Rewrite the frontmatter `description`, `## Responsibility` and `## Inputs` of
  `agents/domain-reviewer.md` so none of them names "the active profile"; `## Inputs` names the diff
  and the installed skill set, and no longer names `profiles.json` as a review-time input.
  Covers: AC-001, AC-014, FR-001, FR-015. Verify: `grep -n "active profile" agents/domain-reviewer.md`
  returns nothing in those three sections, and the frontmatter description is no longer than the
  456-character original (the 400-char cap in `check-consistency.sh` applies to `skills/`, not to
  `agents/` — but an agent description still loads at session start, so it must not grow).

- [x] T005 - Replace step 1 of `## Method` with the two-step per-file selection rule: read the
  changed paths in the diff, then select the reviewer skills whose `description` names those
  artifacts, from the skills installed on this machine. State that several profiles being installed
  is the normal case, and that the installed set is the ceiling while the diff is the selector.
  Covers: AC-001, FR-001, FR-004, FR-015, FR-015b. Verify: the Method section contains no
  instruction to determine a profile, and a reader given a diff of one `.java` and one `.py` file
  can name from the text alone which reviewers run, without consulting `profiles.json`.

- [x] T006 - Narrow `## Stop conditions` to fire only when a changed artifact is claimed by no
  installed reviewer's description **and** plausibly needs one — never because more than one profile
  is installed. State explicitly that a changed file no reviewer claims (a `.md`, a config file) is
  not a stop. Covers: AC-001, FR-002, and the "diff touching a file no profile claims" edge case.
  Verify: the stop condition text contains no reference to profile count or profile ambiguity, and
  names the no-reviewer-claims case as a non-stop.

- [x] T007 - Rewrite `## Output format`: drop `# Profile detected`, and make `# Reviewers applied`
  name each reviewer with the changed files that selected it. Add a sentence stating that selection
  uses skill `description` text and explicitly not `triggers:`. Covers: AC-015, FR-016. Verify: the
  output format lists no profile heading, and `grep -n "triggers" agents/domain-reviewer.md` shows
  the word only in the sentence that rules it out as the selector.

- [x] T008 - Edit the `description` of each skill T002 flagged so it names the artifact or file type
  it applies to, trading words rather than appending. Covers: AC-016, FR-004b. Verify: every edited
  description is ≤ 400 characters (assert mechanically over all 26 routed skills), and re-running
  T002's audit reports zero non-compliant skills.

- [x] T009 - Add a coexistence note to `skills/database-performance-reviewer/SKILL.md` stating how it
  divides N+1 and connection-pool findings with `java-performance-reviewer` when both are installed,
  so the same finding is not reported twice. Covers: FR-005, and the "single file belonging to two
  profiles" edge case. Verify: the note names both skills and states which question each answers;
  a reader can decide from it alone which of the two reports a JPA N+1 finding.

- [x] T010 - Add the FR-006 rule to `scripts/check-consistency.sh`: retain a `skill → primary_agent`
  map while parsing contracts (rule 1 loop, ~L403) and, in the `agentRouting` loop (~L474), error
  when a routed skill's `primary_agent` is not the agent it is routed under. Error category
  `agent-routing`. `secondary_agents` must remain unvalidated by this rule. Covers: AC-004, FR-006,
  and the "skill consumed by two agents" edge case. Verify: `bash scripts/check-consistency.sh`
  exits 0 on the repository as shipped (0 mismatches across 29 routed skills was confirmed during
  planning), and a hand-made mutation moving one routed skill under a different agent exits 1 naming
  that skill.

- [x] T011 - Add `--all-profiles` to `install.sh`: a flag in the arg loop (~L89) passed into the
  python resolver (~L193), expanding to every profile key that is neither `disabled: true` nor
  `billable: true`. The explicit `--profile` path is untouched. Print the billable profiles skipped,
  by name. Covers: AC-006, AC-007, AC-008, AC-017, FR-008, FR-009, FR-010. Verify:
  `./install.sh --all-profiles --dry-run --central-dir <tmp> --skip-link` exits 0, its
  `Active profiles:` line contains all seven enabled non-billable profiles plus `core`, contains
  neither `blockchain-crypto` nor `seo-geo-addon`, and the output names `seo-geo-addon` as skipped
  for being billable.

- [x] T012 - Mirror T011 in `install.ps1` as `-AllProfiles` with identical semantics and identical
  skipped-profile output. Covers: AC-006, AC-007, AC-008, AC-017, FR-008. Verify:
  `pwsh -File install.ps1 -AllProfiles -DryRun -CentralDir <tmp> -SkipLink` resolves the same
  profile set as T011's bash run — compare the two `Active profiles:` lines and confirm they list
  the same names.

- [x] T013 - Add the new-profile report to `scripts/update.sh`, after the manifest block (~L170):
  compare the non-disabled keys of `profiles.json` against `MANIFEST_PROFILES` and print each absent
  profile with the exact `install.sh --profile <name>` command. Gate it on the manifest having
  parsed — on a missing or unreadable manifest print that it cannot compare, and list nothing.
  Install nothing. Covers: AC-009, AC-010, FR-011, FR-012. Verify: against a manifest recording only
  `core,java-spring-backend`, the run names the missing profiles with their add commands and the
  installed skill set on disk is unchanged afterwards; against a truncated manifest it prints the
  cannot-compare line and names no profile.

- [x] T014 - Mirror T013 in `scripts/update.ps1` (~L120–170), same gating and same wording.
  Covers: FR-011, FR-012, D003. Verify: `pwsh -File scripts/update.ps1` against the same
  two fixtures as T013 produces the same two outcomes — profiles named on a short manifest, a
  cannot-compare line on a corrupt one.

- [x] T015 - Remove the singular framing from `docs/AGENTIC_ROUTING.md` (L127, L137, L141) and
  `agents/README.md:22`, matching the language T004–T007 settled on. Covers: AC-002, AC-014,
  FR-003, FR-014. Verify: `grep -rn "active profile" docs/AGENTIC_ROUTING.md agents/README.md`
  returns nothing, and both describe selection by changed files.

- [x] T016 - Remove the same framing from `agents/security-reviewer.md` (L28, L62) and
  `skills/security-review/SKILL.md:37`, per D004. Covers: FR-015, AC-014 (extended). Verify:
  `grep -rn --include='*.md' "active profile" agents skills docs` returns nothing across the whole
  shipped tree.

- [x] T017 - Document the multi-stack flow in `docs/INSTALL.md`: installing several profiles at once,
  `--all-profiles` and what it excludes and why, and what `update.sh` will and will not do about a
  profile added later. Note D001's consequence — a new profile is blanket-installable by default.
  Covers: AC-012, FR-013. Verify: a reader following only `docs/INSTALL.md` can install a Java+Python
  setup and can state, without reading any script, why `seo-geo-addon` was not installed.

## Phase 3: Tests

- [x] T018 - Add a positive and a negative case for the FR-006 rule to
  `scripts/check-consistency.test.sh`, built as mutation-on-a-temp-copy like the existing cases.
  Covers: AC-005, FR-007. Verify: `bash scripts/check-consistency.test.sh` passes with two more
  cases than before, and the negative case fails with exit 1 and an `[agent-routing]` marker naming
  the mis-routed skill.

- [x] T019 - Add two cases to `scripts/update.test.sh`: a manifest recording fewer profiles than
  `profiles.json` declares (asserts the profile is named, the add command is printed, and nothing is
  installed) and a corrupt manifest (asserts the cannot-compare line and that no profile is listed
  as new). Covers: AC-009, AC-010. Verify: `bash scripts/update.test.sh` passes, and inverting each
  assertion makes exactly that case fail.

- [x] T020 - Add the blanket dry-run integration assertion to `scripts/install.test.sh`: every
  enabled profile present, `blockchain-crypto` absent, `seo-geo-addon` absent and reported as
  skipped. Covers: AC-006, AC-007, AC-008, AC-017. Verify: `bash scripts/install.test.sh` passes,
  and a run that names `seo-geo-addon` explicitly still installs it (asserted in the same file).

- [x] T021 - Re-run T001's exact command at the same fixed paths and diff against the stored
  baseline. Covers: AC-011. Verify: `diff "$SCRATCH/ac011/baseline.txt" <new run>` is empty, or
  differs only in deliberate new reporting lines that the reviewer can name one by one; the baseline
  SHA from T001 is confirmed to be an ancestor of the current HEAD (`git merge-base --is-ancestor`).

- [x] T022 - Run the static sweeps: no shipped artifact presents `triggers:` as the selection
  mechanism (AC-015), every routed reviewer description names an artifact (AC-016), and no artifact
  instructs an agent to determine a single active profile (AC-014). Covers: AC-014, AC-015, AC-016.
  Verify: all three greps return the expected empty or explained result, and each is recorded in the
  task's closing note with the command used.

## Phase 4: Review

- [x] T029 - **Found by `/qa-review`:** an unreadable `profiles.json` fell into the "no new
  profiles" branch, reporting every profile as already recorded — a false reassurance on an error,
  AC-010's failure mode on the other input. Fixed in both updaters. Covers: AC-010 (extended).
  Verify: with a corrupt `profiles.json`, the run says it cannot compare and never says "none";
  regression case in `update.test.sh`.
- [x] T030 - **Found by `/qa-review`:** the report pointed at `--all-profiles` without saying it
  re-adds profiles the adopter removed on purpose — the trap D011's error message names for the
  combined-flag case. Warning added in both updaters. Covers: FR-011, FR-012. Verify: the report's
  suggestion carries the re-add warning; regression case in `update.test.sh`.

- [x] T027 - **Found by `/spec-review`:** refuse `--all-profiles` combined with `--remove-profile`
  in both installers, and cover it in `install.test.sh`. Covers: FR-009 (regression against spec 034
  D010). Verify: the combination exits 1 changing nothing, plain `--remove-profile` still removes,
  and reverting the guard makes exactly those two cases fail — all three observed.
- [x] T028 - **Found by `/spec-review`:** extend the AC-016 audit to the 3 reviewer skills routed to
  `security-reviewer`, which FR-004b covers and T002 did not. Covers: AC-016, FR-004b. Verify: all
  29 routed skills audited, none naming no artifact, none over the 400-char cap.

- [x] T023 - Execute a real `domain-reviewer` run against a diff containing both a `.java` and a
  `.py` file, in a repository with both profiles installed, and attach the transcript. Building the
  fixture repository and diff is part of this task. Covers: AC-003, FR-016. Verify: the transcript
  shows findings from both stacks' reviewers in one pass, a `Reviewers applied` section naming each
  reviewer and the files that selected it, and no question to the user about which profile applies.
  A documentation reading is not acceptable evidence for this task.

- [x] T024 - Run the full regression suite: `bash scripts/check-consistency.sh`,
  `bash scripts/check-consistency.test.sh`, `bash scripts/update.test.sh`,
  `bash scripts/graphify.test.sh`, `bash scripts/install.test.sh`. Covers: AC-013. Verify: all five
  exit 0, with the output of each recorded — a summary line asserting "suite green" is not evidence.

- [x] T025 - Spot-check the PowerShell paths locally with `pwsh`: `install.ps1 -AllProfiles -DryRun`
  and `update.ps1` against both manifest fixtures. Covers: AC-006, FR-008, FR-011 (PowerShell half).
  Verify: both scripts parse and produce the expected output under `pwsh` on this Mac; the Windows
  runtime gap is stated explicitly in the closing note rather than left implied.

- [x] T026 - Run `/spec-review` on this feature, then `/qa-review`. Covers: all ACs.
  Both ran. `/spec-review` returned **Fail** on the first pass (the `--all-profiles` /
  `--remove-profile` regression, plus AC-016's narrow audit) and **Pass** after T027/T028.
  `/qa-review` found two further defects on error paths, fixed as T029/T030, and returned **Pass**.
  D003 and D004's deliberate extensions were acknowledged rather than reported as scope creep.
  Verify: the reviewer confirms every AC-001..AC-017 maps to observed evidence in the diff and the
  attached transcripts, and D003/D004's deliberate extensions beyond the literal AC text are
  acknowledged rather than reported as scope creep.

---

## Acceptance criteria coverage

| AC | Tasks |
|---|---|
| AC-001 | T004, T005, T006 |
| AC-002 | T015 |
| AC-003 | T023 |
| AC-004 | T010 |
| AC-005 | T018 |
| AC-006 | T011, T012, T020, T025 |
| AC-007 | T011, T012, T020 |
| AC-008 | T003, T011, T012, T020 |
| AC-009 | T013, T019 |
| AC-010 | T013, T019 |
| AC-011 | T001, T021 |
| AC-012 | T017 |
| AC-013 | T024 |
| AC-014 | T004, T015, T016, T022 |
| AC-015 | T007, T022 |
| AC-016 | T002, T008, T022 |
| AC-017 | T011, T012, T020 |

Every acceptance criterion is covered by at least one task, and every task maps back to at least one
criterion or to a functional requirement the criteria assume.
