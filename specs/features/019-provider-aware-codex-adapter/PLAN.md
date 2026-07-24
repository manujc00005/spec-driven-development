# Implementation Plan: Provider-aware architecture and Codex adapter

## Summary

Add an additive provider-adapter layer that names the SDD Core (provider-neutral) and separates it
from provider packaging, then ship a first, honest, prompt-based Codex adapter. No existing Claude
Code file, installer, or manifest is moved or modified.

## Related spec

`specs/features/019-provider-aware-codex-adapter/SPEC.md`

## Impacted areas

- **New:** `docs/PROVIDER_ADAPTERS.md`; `adapters/` (README + `claude/README.md` +
  `codex/**`); `specs/features/019-*` (this feature's SDD docs).
- **Edited (additive only):** `README.md` (a "Provider adapters" pointer + "Current support" Codex
  row wording); optionally a one-line pointer in `docs/AGENTIC_ROUTING.md`'s "Provider positioning".
- **Untouched (hard):** `profiles.json`, `install.sh`, `install.ps1`, `link-project.*`,
  `scripts/wire-hooks.*`, `scripts/check-consistency.sh`, `settings.template*.json`, all
  `skills/**`, `agents/**`, `hooks/**`.

## Proposed approach

1. **Core doc** — `docs/PROVIDER_ADAPTERS.md`: define SDD Core (the portable list from the request),
   the adapter layer, the honesty principle, and how a new provider maps on.
2. **Registry** — `adapters/README.md`: adapter registry + capability/honesty matrix (core concept →
   Claude mechanism → Codex mechanism → status).
3. **Claude pointer** — `adapters/claude/README.md`: repo root *is* the Claude adapter; nothing
   moved; enumerate where each piece lives.
4. **Codex adapter** — `adapters/codex/`:
   - `README.md` — purpose, verification status, install/use instructions, limitations.
   - `PARITY.md` — Codex-specific capability matrix, including the explicit "does NOT carry over"
     section (hooks, subagents, skill packaging, profile install).
   - `AGENTS.md` — provider-neutral SDD operating guide for Codex (lifecycle, gates, agent
     responsibilities as roles, guardrails as conventions).
   - `prompts/` — lifecycle spine (D004): `sdd-spec-create.md`, `sdd-spec-plan.md`,
     `sdd-spec-analyze.md`, `sdd-spec-implement.md`, `sdd-spec-review.md`, `sdd-spec-close.md`,
     `sdd-guardrails.md`, plus a `README.md` index. Each derived from its core skill.
   - `config.example.toml` — labeled example only.
   - `install-codex.sh` / `install-codex.ps1` — self-contained, copy-only, dry-run, idempotent,
     backups; operate only inside the adapter → target.
5. **README** — add the honest pointer; update the Codex "Current support" row; change no counters.
6. **Verify** — `git status` matches AC-007; `bash scripts/check-consistency.sh` exits 0; dry-run
   and double-run of the installer behave per AC-006.

## Alternatives considered

- **Physically move Claude files under `adapters/claude/`** — rejected (D001): breaks installers,
  renames files, breaks downstream; violates explicit constraints.
- **Add `--provider` to the Claude installers** — rejected: their source-layout assumptions are
  Claude-shaped (per-skill dirs, `agents/<name>.md`, `.claude/settings.json` merge); a second
  provider with different file formats cannot reuse the copy loops, so the flag would be a large,
  risky rewrite. A self-contained Codex installer is safer and honest.
- **Add an `adapters` block to `profiles.json`** — rejected (D003): unvalidated drift surface.
- **Port all 61 skills to Codex prompts** — rejected (D004): unmaintainable + overclaims coverage.

## Dependencies

- Documented Codex conventions (AGENTS.md, `~/.codex/prompts/`, `~/.codex/config.toml`), treated as
  unverified here (D002). No runtime dependency; the deliverables are docs + copy scripts.

## Risks

- **R-1 (Med): Codex path/convention drift.** The advertised prompt path may differ on the current
  Codex release. *Mitigation:* label everything unverified (D002); AGENTS.md is standards-based;
  OQ-1 tracks CLI verification before promoting status.
- **R-2 (Low): overclaiming.** *Mitigation:* PARITY.md's explicit "does NOT carry over" section;
  guardrails-as-conventions (D005); README wording reviewed against the no-parity rule.
- **R-3 (Low): CI drift.** New files could trip orphan checks. *Mitigation:* all new files live
  outside the directories `check-consistency.sh` scans; verify green (AC-008).
- **R-4 (Low): installer safety.** *Mitigation:* copy-only, no network, no CLI exec, no secrets,
  dry-run default-safe, backups before overwrite — mirrors existing installer guarantees.

## Test strategy

- **Integration:** `install-codex.sh --dry-run --target <tmp>` writes nothing; real `--target <tmp>`
  copies; re-run is a no-op; overwriting a modified copy creates a `.bak-<ts>`. Repeat for `.ps1`
  where a shell is available (else document as unverified on this OS).
- **Consistency:** `bash scripts/check-consistency.sh` → exit 0.
- **Constraint audit:** `git status --porcelain` shows only new `adapters/**`, `docs/PROVIDER_ADAPTERS.md`,
  `specs/features/019-**`, and the additive `README.md` edit — nothing else.
- **Manual:** honesty/verification notes present in every adapter doc.

## Rollback strategy

Entirely additive: delete `adapters/` and `docs/PROVIDER_ADAPTERS.md`, and revert the `README.md`
pointer. No installer, manifest, or downstream state to unwind because none was touched.

## PLAN verification checklist

- [x] The plan covers all acceptance criteria.
- [x] The plan avoids behavior outside the spec.
- [x] Risks are documented.
- [x] Test strategy is documented.
- [x] Rollback strategy is documented.
- [x] SPEC.md status has been updated to `Ready` (then `In Progress` as implementation began).
