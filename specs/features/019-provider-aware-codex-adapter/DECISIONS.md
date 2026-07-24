<!-- See skills/sdd-guardrails/SKILL.md, section 1, for the full decision state machine (Proposed / Accepted / Superseded / Rejected / Deferred). -->

# Decisions: Provider-aware architecture and Codex adapter

## Decision log

### D001 - Adapter layer is additive; no Claude file is moved

**Date:** 2026-07-24

**Status:** Accepted

**Context:** The target architecture in the request nests provider adapters under an `adapters/`
tree (`adapters/claude/`, `adapters/codex/`). Taken literally that would relocate `skills/`,
`agents/`, `hooks/`, and the installers under `adapters/claude/`. Those paths are hardcoded in
`install.sh`, `install.ps1`, `link-project.*`, `scripts/wire-hooks.*`, `scripts/check-consistency.sh`,
`profiles.json` resolution, and — critically — in every downstream project that already installed
from this repo.

**Decision:** Introduce `adapters/` as an **additive** layer. The Claude Code adapter stays exactly
where it is (repo root); `adapters/claude/README.md` is a **pointer** documenting that the repo root
*is* the Claude adapter. Only the new Codex adapter gets real files under `adapters/codex/`.

**Reasoning:** The explicit constraints forbid renaming Claude files, breaking the installers, and
touching downstream projects. A physical move would violate all three for zero functional gain — the
separation the request wants is a **conceptual/documentation** boundary, which an additive layer
plus a core doc expresses without moving a byte. "Cleanest as an architect would do" here means the
smallest change that makes the boundary real and enforceable, not the largest reorganization.

**Consequences:** The core-vs-adapter split is expressed in `docs/PROVIDER_ADAPTERS.md` and
`adapters/README.md`, not in the filesystem layout of the Claude adapter. A future maintainer who
wants a physical move can do it as its own tracked, breaking, major-version migration — this
decision deliberately does not.

### D002 - Codex adapter is prompt-based and labeled unverified against a live CLI

**Date:** 2026-07-24

**Status:** Accepted

**Context:** `which codex` returns not-found in this environment; `codex --version` / `codex --help`
cannot be run. The constraints forbid inventing Codex features or claiming Claude-style
skills/agents "unless verified from official CLI/help or actual files."

**Decision:** Build the Codex adapter on **documented Codex conventions** — a project-root
`AGENTS.md` operating guide, custom prompts as markdown under `~/.codex/prompts/`, and
`~/.codex/config.toml` — and label every artifact **prompt-based and unverified against a live Codex
CLI in this environment**. No artifact claims Codex has hooks, native subagents with a `tools:`
grant, or a skill-packaging system.

**Reasoning:** This is the honest, incremental step the request asks for: real, useful,
installable content that does not overclaim. The `AGENTS.md` convention is a genuine cross-tool
standard, so the operating guide is valuable even if a later Codex release moves the prompt path.
Verification against an installed CLI is a tracked follow-up (SPEC OQ-1), exactly the
structural-vs-live distinction the repo already draws for its lifecycle agents.

**Consequences:** `adapters/codex/PARITY.md` carries an explicit "what does NOT carry over" section.
`install-codex.*` are copy-only and never execute the Codex CLI. The adapter can be promoted from
"prompt-based (unverified)" to "verified" in a follow-up once run against a real Codex install.

### D003 - `profiles.json` is not extended with a provider dimension

**Date:** 2026-07-24

**Status:** Accepted

**Context:** Making the framework "provider-aware" invites adding a `providers`/`adapters` block to
`profiles.json`. The user asked for the most optimal, least invasive, cleanest architecture.

**Decision:** Leave `profiles.json` untouched. The adapter registry lives in `adapters/README.md`
(human-authoritative) and the architecture in `docs/PROVIDER_ADAPTERS.md`.

**Reasoning:** `profiles.json` has one job — the Claude installer's profile→skills/hooks/templates/
agents filtering, validated end-to-end by `scripts/check-consistency.sh`. An adapter block there
would be **ignored by the installer and unchecked by CI**, i.e. exactly the "unvalidated drift
surface" this repo's "enforcement over convention" principle exists to avoid (see the shipped-vs-
planned hard distinction). Single-responsibility manifests are the cleaner architecture: profiles =
Claude install filtering; `adapters/README.md` = provider registry. A machine-readable adapter
manifest is deferred until something actually consumes it (YAGNI, consistent with 018 D013).

**Consequences:** No new CI rules are needed and none of `check-consistency.sh`'s invariants change.
If a future adapter installer needs machine-readable adapter metadata, that is a separate spec that
also adds the matching CI validation — not a bare JSON blob added now.

### D004 - Codex prompts cover the portable lifecycle spine only, derived from core skills

**Date:** 2026-07-24

**Status:** Accepted

**Context:** The Claude adapter ships 61 skills. Porting all of them to Codex prompts would be
unmaintainable and would overclaim coverage.

**Decision:** Ship a curated **lifecycle spine**: `spec-create`, `spec-plan`, `spec-analyze`,
`spec-implement`, `spec-review`, `spec-close`, and the `guardrails`/consistency gate. Each prompt is
derived faithfully from its core skill's procedure and carries a header naming its origin and
provider-neutrality.

**Reasoning:** These seven are the provider-neutral portable core the request names (SPEC → PLAN →
TASKS → DECISIONS → REVIEW → evidence → PR-ready). Stack-specific reviewers and Claude-specific
mindset manuals (`provider_specific: true`) are deliberately excluded from v1 — they either depend on
profile routing that Codex has no installer for, or encode Claude-specific behavioral guidance.
Honest incremental coverage beats a shallow full port.

**Consequences:** `adapters/codex/PARITY.md` states which skills are and are not represented. Adding
more prompts later is additive and does not change the core.

### D005 - Guardrails ship as conventions, not enforced hooks, on Codex

**Date:** 2026-07-24

**Status:** Accepted

**Context:** The Claude adapter enforces guardrails (block `git push`, spec-status gating, etc.)
through tool-call hooks wired into `.claude/settings.json`. Codex has no verified equivalent
tool-call hook mechanism in this environment.

**Decision:** On the Codex adapter, guardrails are expressed as **explicit rules in `AGENTS.md` and
the guardrails prompt** that the model is instructed to follow, and are labeled as *conventions, not
deterministic enforcement*. The adapter does not claim hook parity.

**Reasoning:** Overclaiming enforcement would be dishonest and unsafe — a user might assume
`git push` is blocked when it is not. Stating the gap plainly is the correct engineering posture and
matches the repo's existing "hooks are best-effort, not a security boundary" honesty.

**Consequences:** `PARITY.md` marks "deterministic guardrails (hooks)" as **not implemented** for
Codex, with the convention-based mitigation noted. This is the single largest honest gap and is
surfaced, not buried.

### D006 - `install-all` is a thin wrapper, not a change to either installer

**Date:** 2026-07-24

**Status:** Accepted

**Context:** With two independent installers (Claude `install.sh`/`.ps1`, Codex
`adapters/codex/install-codex.*`), a first-time user asked for a single command to install both. The
temptation is to merge them or add a `--provider` flag to the Claude installer.

**Decision:** Ship root-level `install-all.sh` / `install-all.ps1` that **only call** the two
existing installers in order (Claude first, then Codex), forwarding a small set of flags
(`--dry-run`/`--force` to both; `--profile`/`--link-user-claude` to Claude;
`--codex-target`/`--codex-home` to Codex; `--skip-claude`/`--skip-codex`; and `--claude-args`/
`--codex-args` escape hatches). Neither installer is modified or reimplemented.

**Reasoning:** Keeps each installer the single source of truth for its own behavior and safety
guarantees (idempotency, backups, dry-run), honors D001/D003 (no change to the Claude installer or
`profiles.json`), and gives the convenience without coupling. If the Claude step fails, the wrapper
skips Codex and returns that exit code — no partial-state surprise.

**Consequences:** Installing both is now `./install-all.sh` (or `.ps1`); each adapter is still
independently installable and idempotent, so re-running adds only what is missing per installer. The
wrapper adds no new machine-validated surface — `check-consistency.sh` does not scan root scripts, so
CI stays green. The two adapters install to disjoint locations, so ordering has no coupling risk.

### D007 - `AGENTS.md` installs only with an explicit target, never by defaulting to the cwd

**Date:** 2026-07-24

**Status:** Accepted

**Context:** The first real `./install-all.sh` run (no `--codex-target`) defaulted the Codex
`AGENTS.md` target to `$(pwd)`. Run from the framework checkout — the natural place to run the
installer — that wrote `AGENTS.md` **into the framework repo root itself**, an artifact that then got
committed. `AGENTS.md` is inherently per-project and has no safe default location.

**Decision:** `install-codex.{sh,ps1}` install `AGENTS.md` **only when `--target`/`-Target` is
passed explicitly**; without it, `AGENTS.md` is skipped (the prompts still install to the global
`~/.codex/prompts`). Additionally, a hard guard **refuses** to write `AGENTS.md` when the resolved
target is the framework repo root. `install-all` surfaces the same: no `--codex-target` → prompts
install, `AGENTS.md` skipped with a clear message.

**Reasoning:** Matches the repo's "no surprising writes" installer ethos. Prompts have a real global
default (`~/.codex/prompts`); `AGENTS.md` does not, so defaulting it to the cwd is a footgun that
silently pollutes whatever directory the installer is run from — most damagingly the framework repo.
Skipping-with-a-message plus a framework-root refusal is safe by default and self-explanatory.

**Consequences:** The stray committed root `AGENTS.md` is removed (staged deletion; the maintainer
commits it). `--target DIR` is now documented as *required to install `AGENTS.md`* across the codex
README, `docs/INSTALL.md`, and the main README. `adapters/codex/AGENTS.md` (the source) is unchanged.
