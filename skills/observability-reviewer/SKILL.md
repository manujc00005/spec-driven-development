---
name: observability-reviewer
description: Review Java/Spring code for observability quality — structured logging, PII in logs, Micrometer metrics, distributed tracing and correlation IDs, actuator/health endpoint design, and alert-ready signal coverage. Extends backend-review.
triggers:
  - After `/backend-review` on Java/Spring projects
  - When logging, metrics, tracing, actuator, or health-check code changes
  - When a new service, consumer, scheduled job, or external integration is added (it must be observable before it ships)
  - When the user asks "can we debug this in production?" or "what do we alert on?"
---

# Observability Reviewer

## Purpose

Catch features that ship blind: no signal when they break, no trace when they are slow, and logs
that either say nothing or leak PII. This skill **extends** `backend-review` — run that first for
business-logic correctness; this pass only judges whether the code can be operated.

## Extends

- **Skill:** `backend-review`
- **Subagent:** `java-spring` (Spring Boot idioms, Micrometer, actuator)

## What this skill checks (beyond backend-review)

### Logging

- Log statements exist at the decision points that matter: external call failures, retries,
  dropped/skipped work, auth denials — not just happy-path noise.
- Levels are honest: expected conditions are not `ERROR`; real failures are not `DEBUG`.
- **No PII or secrets in logs**: emails, card/account numbers, tokens, full request bodies of
  payment or auth endpoints. Log opaque IDs (`orderId`, `customerId`), never payloads.
- Structured logging (key-value / JSON) over string interpolation for fields you will query.
- Exceptions logged once, with stack trace, at the boundary that handles them — not at every layer.

### Correlation and tracing

- A correlation/trace ID crosses every boundary: HTTP headers in, Kafka message headers out,
  MDC inside (`traceId` present in the log pattern).
- New Kafka producers propagate tracing headers; new consumers restore them into MDC before
  the first log line.
- Spans (Micrometer Tracing / OpenTelemetry) wrap external calls and message handling, named
  after the operation, not the class.

### Metrics

- New critical flows expose a counter or timer (`@Timed`, `Counter`, `Timer`) — a payment path
  without a success/failure counter cannot be alerted on.
- Metric names follow the existing convention and carry low-cardinality tags only (no user IDs,
  no free text as tag values).
- Queue/consumer lag, retry counts, and DLQ sends are counted where applicable.

### Health and actuator

- Health indicators reflect real dependencies (DB, Kafka) — a service that cannot reach its
  broker should not report `UP`.
- Actuator exposure is deliberate: `health`/`info` public at most; `env`, `heapdump`,
  `threaddump` never exposed unauthenticated (overlap with `spring-security-reviewer` — flag,
  don't duplicate its full check).
- Liveness vs readiness distinguished when the platform uses both.

### Alert-readiness

- For each new failure mode ask: which signal fires? If the answer is "someone reads the logs",
  flag it — logs are for diagnosis, metrics are for detection.
- Timeouts and retry exhaustion emit a distinct signal from ordinary errors.

## Output format

```markdown
## Observability Review

**Verdict:** PASS | PASS WITH NOTES | FAIL

### Findings

| # | Category | Severity | File:Line | Finding | Action |
|---|---|---|---|---|---|
| 1 | Logging/PII | Critical | `PaymentService.java:41` | Logs full card payload on failure | Log `paymentId` only |

### Blind spots

- (Failure modes with no metric/trace — what production incident would go undetected)

### Recommendations

- (Non-blocking improvements: naming, levels, span coverage)
```

## What this skill does NOT do

- Does not review business logic correctness (that's `backend-review`).
- Does not review security configuration beyond flagging actuator exposure (that's `spring-security-reviewer`).
- Does not set up Grafana/Prometheus/collector infrastructure — it reviews code-level signal quality.
- Does not modify code.
