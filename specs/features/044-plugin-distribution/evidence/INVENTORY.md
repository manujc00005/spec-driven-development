# T012 — Inventory: `claude plugin details sdd`

Date: 2026-09-04T19:49:47Z · 2.1.259 (Claude Code)

```
sdd 0.1.0
  Description: Spec-Driven Development for Claude Code and Codex: lifecycle skills, review gates, agents and guardrail hooks.
  Source: sdd@spec-driven-development

Component inventory
  Skills (72)  aeo-review, ai-visibility-review, api-review, architect-review, backend-review, communicator, container-review, context-manager, data-pipeline-reviewer, database-performance-reviewer, database-review, debugger, decision-mapping, decomposer, deployment-review, event-driven-reviewer, frontend-review, geo-review, graphify, graphify-context, handoff, honest-advisor, java-performance-reviewer, java-spring-reviewer, microservices-patterns-reviewer, nextjs-server-actions-reviewer, observability-reviewer, payment-idempotency-reviewer, performance-review, pipeline-review, pr-description, prisma-migration-reviewer, privacy-compliance-review, project-init, prototype, python-reviewer, python-testing-reviewer, qa-review, refactor-review, release-readiness, review-all, root-causer, scope-keeper, scout, sdd, sdd-full, sdd-guardrails, sdd-medium, sdd-onboard, sdd-orchestrate, sdd-workspace-init, sdd-workspace-onboarding, security-review, seo-review, spec-analyze, spec-clarify, spec-close, spec-create, spec-implement, spec-plan, spec-resume, spec-review, spec-status, spec-update, spring-boot-api-reviewer, spring-security-reviewer, sql-query-reviewer, stopper, stripe-payments-reviewer, test-engineer, threat-modeler, verifier
  Agents (8)  security-reviewer, domain-reviewer, codebase-researcher, solution-architect, deep-reasoner, fast-worker, final-conformance-reviewer, implementer
  Hooks (4)  PreToolUse, PostToolUse, Stop, SessionStart  (harness-only — no model context cost)
  MCP servers (0)
  LSP servers (0)

Projected token cost
  Always-on:   ~8,336 tok   added to every session

Per-component (rounded)
  component                        always-on  on-invoke
  spring-boot-api-reviewer               ~90      ~1.5k
  qa-review                              ~80      ~1.4k
  root-causer                           ~120      ~1.4k
  deployment-review                     ~140      ~3.5k
  prisma-migration-reviewer             ~100      ~1.5k
  spec-resume                            ~40       ~790
  event-driven-reviewer                 ~140      ~4.1k
  sdd-onboard                           ~120        ~2k
  refactor-review                       ~110      ~1.2k
  sdd-orchestrate                       ~100     ~13.9k
  graphify-context                      ~100      ~2.3k
  decomposer                             ~90      ~1.5k
  context-manager                       ~100      ~1.6k
  java-performance-reviewer              ~90      ~1.4k
  performance-review                     ~70      ~1.6k
  honest-advisor                        ~100      ~1.5k
  backend-review                        ~100      ~1.6k
  spec-status                            ~70      ~1.2k
  python-testing-reviewer               ~110      ~3.2k
  handoff                                ~30       ~810
  nextjs-server-actions-reviewer        ~110      ~1.4k
  threat-modeler                        ~120      ~1.4k
  ai-visibility-review                  ~130      ~1.7k
  microservices-patterns-reviewer       ~140      ~3.9k
  frontend-review                       ~100      ~2.2k
  communicator                           ~90      ~1.3k
  architect-review                      ~110      ~1.2k
  spec-analyze                           ~90      ~3.2k
  sdd-full                               ~50      ~1.3k
  spec-update                            ~80      ~1.2k
  scout                                  ~90      ~1.4k
  prototype                              ~70        ~3k
  pr-description                         ~40       ~920
  sdd-workspace-onboarding              ~130      ~4.1k
  aeo-review                            ~110      ~1.4k
  sql-query-reviewer                    ~110      ~2.7k
  sdd-guardrails                        ~140      ~7.1k
  database-review                        ~70      ~1.5k
  payment-idempotency-reviewer          ~120      ~1.5k
  spec-clarify                          ~110      ~1.2k
  container-review                      ~130        ~3k
  pipeline-review                       ~130      ~2.8k
  spec-create                            ~90      ~1.8k
  data-pipeline-reviewer                ~110      ~3.4k
  scope-keeper                          ~110      ~1.4k
  sdd                                    ~90        ~2k
  project-init                          ~120      ~2.6k
  debugger                               ~80      ~2.8k
  verifier                              ~100      ~1.4k
  review-all                             ~90      ~3.2k
  stopper                               ~100      ~1.5k
  spec-plan                              ~80      ~2.2k
  release-readiness                     ~150      ~3.2k
  seo-review                            ~100      ~1.4k
  python-reviewer                       ~120      ~3.4k
  graphify                              ~120      ~4.9k
  privacy-compliance-review             ~130      ~1.9k
  spec-implement                         ~40      ~2.2k
  api-review                             ~80        ~2k
  decision-mapping                       ~50      ~1.4k
  database-performance-reviewer         ~120      ~3.3k
  java-spring-reviewer                   ~90      ~1.3k
  geo-review                            ~120      ~1.6k
  spec-review                            ~80      ~1.4k
  spring-security-reviewer               ~80      ~1.7k
  sdd-workspace-init                    ~130      ~2.3k
  observability-reviewer                 ~90      ~1.4k
  test-engineer                         ~100      ~1.5k
  security-review                        ~90      ~1.8k
  spec-close                             ~60      ~1.1k
  sdd-medium                             ~50        ~1k
  stripe-payments-reviewer               ~90      ~1.5k
  security-reviewer                     ~200      ~3.1k
  domain-reviewer                       ~160      ~2.6k
  codebase-researcher                   ~180      ~1.8k
  solution-architect                    ~160      ~1.4k
  deep-reasoner                         ~200       ~780
  fast-worker                           ~170      ~1.1k
  final-conformance-reviewer            ~160      ~1.6k
  implementer                           ~120      ~1.7k

  On-invoke cost is paid each time a skill or agent fires.
  Token counts are estimates and may differ from actual usage.
[exit 0]
```
