# Feature Spec: Phase 1 — Context layer + Graphify integration (planned)

## Status

Done

> Closed 2026-07-13 during Phase 5 (`005-framework-hardening-and-cross-platform-polish`).
> ACs verified against on-disk evidence; skill-behavior ACs are **structurally verified**
> (the skills are markdown instructions — their text demonstrably contains the required
> behavior) and validated through dogfooding since Phase 1. See the (backfilled) `TASKS.md`
> Verification section. Note: the "(planned)" in this spec's title referred to the external
> Graphify tool, which remains external and optional — the context layer itself shipped.

## Problem

On medium-to-large codebases (especially multi-module Java/Spring microservices), Claude Code
re-scans the entire repo before every plan/review — burning tokens and losing focus. There is no
structured way to onboard an existing project into SDD, no architecture map to constrain impact
analysis, and no mechanism to detect when context is stale.

## Goal

Provide a **context layer** that:
1. Gives Claude a bounded, pre-digested view of a project (stack, architecture, modules, boundaries).
2. Integrates Graphify as an optional accelerator for impact analysis (graceful degradation if absent).
3. Onboards existing projects into SDD without touching their code.
4. Manages context freshness so stale maps are flagged, not silently trusted.

## Non-goals

- Implementing Graphify itself (external tool — [PLANNED]).
- Running Graphify automatically (the user triggers it manually).
- Replacing file reads or tests with graph data.
- Changing existing skills' internal logic (only adding "read context first" guidance).
- Touching `C:\ProgramData\ClaudeConfig` or making commits.

## Functional requirements

- FR-001: Create `docs/_templates/PROJECT_CONTEXT.md` — purpose, bounded contexts, service map, glossary, ownership.
- FR-002: Create `docs/_templates/TECH_STACK.md` — versions, build tool (Maven default), libs, commands.
- FR-003: Create `docs/_templates/ARCHITECTURE.md` — layers, services, sync/async edges, boundaries, diagram placeholder.
- FR-004: Create `skills/context-manager/SKILL.md` — decides minimal reading list before implementing; compact context.
- FR-005: Create `skills/graphify-context/SKILL.md` — interprets GRAPH_REPORT.md for impact analysis; detects staleness; degrades gracefully.
- FR-006: Create `skills/sdd-onboard/SKILL.md` — onboards existing projects: detect stack, scaffold context docs, no code changes.
- FR-007: Create `hooks/graphify-stale-reminder.ps1` and `.sh` — warns if GRAPH_REPORT.md is stale or absent when planning.

## Acceptance criteria

- AC-001: Each template has all fields listed in the roadmap §7, is stack-aware (Maven/Spring default), and contains no PII or hardcoded paths.
- AC-002: `context-manager` skill reads context docs + active spec and outputs a bounded reading list (max N files).
- AC-003: `graphify-context` skill checks for `GRAPH_REPORT.md`; if present, extracts impacted modules; if absent, prints one-line fallback note and exits cleanly.
- AC-004: `sdd-onboard` skill detects stack from build files (`pom.xml`/`mvnw`/`build.gradle`/`package.json`/`schema.prisma`), generates context doc scaffolds under `docs/`, never modifies application code.
- AC-005: `graphify-stale-reminder` hook compares `GRAPH_REPORT.md` mtime vs newest source; warns if stale; exits 0 (never blocks).
- AC-006: No secrets, PII, or hardcoded local paths in any deliverable.
- AC-007: All `.sh` hooks pass `bash -n` syntax check.
