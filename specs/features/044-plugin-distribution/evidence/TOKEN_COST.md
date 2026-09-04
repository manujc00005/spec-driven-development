# T012 — Projected token cost

Date: 2026-09-04T19:49:47Z · 2.1.259 (Claude Code)

From `claude plugin details sdd` (full output in INVENTORY.md):

```
  Skills (72)  aeo-review, ai-visibility-review, api-review, architect-review, backend-review, communicator, container-review, context-manager, data-pipeline-reviewer, database-performance-reviewer, database-review, debugger, decision-mapping, decomposer, deployment-review, event-driven-reviewer, frontend-review, geo-review, graphify, graphify-context, handoff, honest-advisor, java-performance-reviewer, java-spring-reviewer, microservices-patterns-reviewer, nextjs-server-actions-reviewer, observability-reviewer, payment-idempotency-reviewer, performance-review, pipeline-review, pr-description, prisma-migration-reviewer, privacy-compliance-review, project-init, prototype, python-reviewer, python-testing-reviewer, qa-review, refactor-review, release-readiness, review-all, root-causer, scope-keeper, scout, sdd, sdd-full, sdd-guardrails, sdd-medium, sdd-onboard, sdd-orchestrate, sdd-workspace-init, sdd-workspace-onboarding, security-review, seo-review, spec-analyze, spec-clarify, spec-close, spec-create, spec-implement, spec-plan, spec-resume, spec-review, spec-status, spec-update, spring-boot-api-reviewer, spring-security-reviewer, sql-query-reviewer, stopper, stripe-payments-reviewer, test-engineer, threat-modeler, verifier
  Agents (8)  security-reviewer, domain-reviewer, codebase-researcher, solution-architect, deep-reasoner, fast-worker, final-conformance-reviewer, implementer
  Hooks (4)  PreToolUse, PostToolUse, Stop, SessionStart  (harness-only — no model context cost)
  Always-on:   ~8,336 tok   added to every session
```

Reading: the always-on figure is what every session pays for having the 72 skill and 8 agent descriptions loaded; on-invoke costs are paid only when a skill or agent fires. Hooks add no model-context cost (harness-only). This is the number D001 defers the per-profile split to.
