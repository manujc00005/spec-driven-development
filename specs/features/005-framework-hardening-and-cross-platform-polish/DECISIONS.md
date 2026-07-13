<!-- See skills/sdd-guardrails/SKILL.md, section 1, for the full decision state machine. -->

# Decisions: Phase 5 — Framework hardening and cross-platform polish

## Decision log

### D001 — Consolidate Java compile hooks at the wiring level, not by deletion

**Date:** 2026-07-13

**Status:** Accepted

**Context:** `hooks/maven-compile` and `hooks/java-build-test-guard` both run `mvnw compile`
on `.java` edits. `java-build-test-guard` is a strict superset (Maven-first + Gradle fallback,
opt-in fast unit tests, safe JSON serialization of the systemMessage). `settings.template.json`
currently wires the weaker `maven-compile`; the `java-spring-backend` profile installs both.

**Decision:** Resolve the overlap at the *wiring* level. Repoint the Windows template to
`java-build-test-guard`, add a deprecation header to both `maven-compile` variants pointing to
the canonical hook, and **keep** `maven-compile` on disk and in the profile.

**Reasoning:** Deleting `maven-compile` could break any project that already wires it by path,
violating the "don't break existing projects" and "don't delete without justification"
constraints. Wiring-level consolidation removes the double-compile risk for new adopters (the
template wires exactly one hook) while preserving backward compatibility. Physical removal is
deferred (see OQ-2) to a future phase with its own deletion decision.

**Consequences:** Hook-family count stays 11. The template default changes behavior for new
copies (one canonical Java hook). A stale `maven-compile` file remains installed until a future
removal phase.

---

### D002 — Provide a Linux/macOS hook-wiring template rather than only documenting the translation

**Date:** 2026-07-13

**Status:** Accepted

**Context:** `settings.template.json` ships PowerShell commands only. `hooks/README.md` explains
how to hand-translate them to `bash <name>.sh`, but no ready-to-copy `.sh` template exists —
a cross-parity gap for a repo that ships `.ps1` + `.sh` for every hook.

**Decision:** Add `settings.template.sh.json` as a first-class, ready-to-copy template at
command-parity with the Windows one, wiring the consolidated Java hook (`java-build-test-guard.sh`).

**Reasoning:** Parity should be shippable, not a manual exercise left to the reader. It matches
the repo's existing `.ps1`/`.sh` pairing philosophy and lowers adoption friction on macOS/Linux.

**Consequences:** Two templates to keep in sync going forward; the documentation must point to
both and explain when to use which.

---

### D003 — Translate public-facing agent/orchestration artifacts to English; leave internal specs as-is

**Date:** 2026-07-13

**Status:** Accepted

**Context:** The agents' fixed output-format headings, the `/sdd-orchestrate` examples, and
`docs/SDD-ORCHESTRATION.md` examples are in Spanish, inconsistent with the English README/docs
and with the repo's public/portfolio positioning. The internal `specs/features/*` documents are
also partly Spanish but are dogfooding records, not the public API surface.

**Decision:** Translate the public-facing agent and orchestration artifacts to English,
preserving each report's section count/order/meaning. Do **not** rewrite the internal historical
feature specs.

**Reasoning:** English is the public contract surface a recruiter/adopter reads and the agents'
report headings are part of that contract. Internal dogfooding specs are historical records;
churning them adds risk and noise without public benefit. The agents still operate in whatever
language the session uses — only the fixed headings change.

**Consequences:** The agents' report headings become English; any external tooling that keyed on
the Spanish headings (none known) would need updating. Internal specs remain bilingual by history.

---

### D004 — AC-017 live check is prepared this phase, executed only on explicit confirmation

**Date:** 2026-07-13

**Status:** Accepted

**Context:** Spec `004` is honestly held at `In Review` because live agent discovery after a real
deploy was never confirmed. Executing that check requires deploying agents into the real
`~/.claude/agents` and restarting the Claude Code session — both of which the user's standing
rules gate behind explicit confirmation, and the latter the agent cannot perform itself.

**Decision:** This phase *documents* a reproducible AC-017 live-check procedure and leaves `004`
at `In Review`. Actually running it (and promoting `004` to `Done`) is a gated follow-up
requiring explicit user confirmation.

**Reasoning:** Honors the "no live-config writes without confirmation" and "nothing marked Done
without verification" rules simultaneously. "Prepare correctly" was an explicitly acceptable
outcome in the request.

**Consequences:** `004` stays `In Review` until a human runs the procedure. The framework gains a
repeatable verification recipe regardless.

---

### D005 — Reconcile 002 AC-005 ("skipped gracefully") with the current hard-error installer

**Date:** 2026-07-13

**Status:** Accepted

**Context:** Spec `002` AC-005 asserts the installer skips missing/planned skills *gracefully*.
Phase 4 (feature `004`) changed the installer to **hard-error** on a missing *shipped* item and
to skip only *planned* items. The old AC now contradicts current behavior.

**Decision:** Record a superseding decision (in `002/DECISIONS.md`, cross-referenced here): the
"skipped gracefully" behavior applied to the pre-`profiles.json`-0.4.0 installer; it was
deliberately superseded by the shipped-vs-planned integrity model, where *planned* items are
skipped gracefully and *missing shipped* items are a hard error. `002`'s close summary notes AC-005
as met-as-superseded, not silently contradicted.

**Reasoning:** The honesty rule requires the contradiction to be surfaced and explained, not
papered over. The current behavior is the intended, more-correct one.

**Consequences:** `002` can close honestly with an explicit note that one AC was superseded by a
later, recorded decision.

---

### D006 — Old-spec promotion is per-AC evidence-gated, not bulk

**Date:** 2026-07-13

**Status:** Accepted

**Context:** Specs `000`/`001`/`002` are stale at `In Review`; some lack `TASKS.md`/`DECISIONS.md`.
It is tempting to bulk-promote them to `Done`.

**Decision:** Promote each spec to `Done` only after verifying every one of its ACs against
on-disk evidence and backfilling the missing lifecycle documents. Any AC that is only
*structurally* (not *live*) verifiable is labeled as such in the close summary. If a spec has an
AC that cannot be honestly verified, it stays `In Review` with a recorded reason.

**Reasoning:** Directly enforces the "nothing Done without verification" rule and the framework's
own lifecycle discipline on its own history.

**Consequences:** Closure is more work than a status flip, but the result is defensible and
matches what the framework preaches.

---

### D007 — Fix the missing executable bit on all `.sh` files via a staged mode change

**Date:** 2026-07-13

**Status:** Accepted

**Context:** During closure verification of spec `000` (AC-003 requires `git-guardrails.sh`
to be executable), all 14 tracked `.sh` files (11 hooks, `hooks/lib/claude-json.sh`,
`install.sh`, `link-project.sh`) were found tracked as mode `100644` — on a Linux/macOS
clone, none would be executable without a manual `chmod +x`. Windows working trees cannot
represent the bit, so it must be set in the git index.

**Decision:** Set the bit for all 14 files with `git add --chmod=+x` (a staged, reviewable,
uncommitted index change — content unchanged, no commit made, consistent with the no-commit
rule). Record in `000/TASKS.md` that AC-003's executable-bit claim was only true from this
fix onward.

**Reasoning:** This is a genuine cross-platform hardening defect squarely in this phase's
scope; documenting it without fixing it would ship a known broken bit. Staging is the only
way to fix it from Windows, and it stays fully under the user's review before any commit.

**Consequences:** `git status` shows the 14 files as staged mode changes. Fresh Linux/macOS
clones (after the user commits) get executable scripts out of the box; the `chmod +x` advice
in the docs becomes a belt-and-suspenders note instead of a requirement.

---

### D008 — Phase 5 closed: all ACs met, gated live check confirmed by the user

**Date:** 2026-07-13

**Status:** Accepted

**Context:** All autonomous tasks were implemented and verified the same day; the only open
item was T013, gated on the user deploying to live config and confirming discovery in a
fresh session (D004).

**Decision:** Close Phase 5 as `Done`. The user confirmed the gate, ran
`install.ps1` + `install.ps1 -LinkUserClaude` themselves, and verified in a fresh Claude
Code session that `deep-reasoner` (model: opus), `fast-worker` (model: sonnet), and
`/sdd-orchestrate` are recognized — AC-017 PASS live, which also closed Phase 4 (004/D010).

**Reasoning:** With T013 resolved, every task is done and every AC (AC-001…AC-010) has
recorded evidence: specs 000/001/002 closed per-AC (D006), the AC-005 contradiction
superseded (D005 + 002/D006), hooks consolidated at wiring level (D001), Linux/macOS
template shipped (D002), public artifacts translated (D003), cross-platform gates all PASS
(TASKS.md verification table), and the executable-bit defect fixed (D007). The honesty
rule is satisfied: the only live-verification claim made (AC-017) is backed by an observed
fresh-session check.

**Consequences:** Every feature in `specs/features/` is now `Done` (000–005). The remaining
known gaps are roadmap items, not open specs: the worked `examples/` walkthrough, a real
Linux-box run of `install.sh --dry-run` (fail-clear path verified on Windows Git Bash;
full-path run recommended on the user's Mac after commit/push), and the deferred physical
removal of the deprecated `maven-compile` (OQ-2).
