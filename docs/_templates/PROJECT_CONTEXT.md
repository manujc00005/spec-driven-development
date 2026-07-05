# Project Context

> Copy this template into your project as `docs/PROJECT_CONTEXT.md` and fill it in.
> This file gives Claude Code a high-level map of what the project is, who owns what,
> and where the boundaries are — so it doesn't have to re-derive this every session.

## Project name

<!-- e.g. "Order Service", "Payment Gateway", "Admin Portal" -->

## Purpose

<!-- 1-3 sentences: what problem does this project solve and for whom? -->

## Bounded contexts / domains

<!-- List the business domains this project covers. For a microservice, this may be one. -->

| Domain | Responsibility | Key entities |
|---|---|---|
| | | |

## Service map

<!-- For microservice architectures: which services exist and how they communicate. -->
<!-- For monoliths: which modules/packages and their roles. -->

| Service / Module | Responsibility | Upstream deps | Downstream consumers |
|---|---|---|---|
| | | | |

## Communication patterns

<!-- Sync (REST/gRPC), async (Kafka/RabbitMQ), events, scheduled jobs -->

- Sync:
- Async:
- Events:
- Scheduled:

## Data stores

| Store | Type | Owns which data |
|---|---|---|
| | PostgreSQL / Redis / Elasticsearch / ... | |

## External integrations

<!-- Third-party APIs, PSPs, identity providers, cloud services -->

| Integration | Purpose | Protocol | Owner |
|---|---|---|---|
| | | | |

## Glossary

<!-- Domain terms that might be ambiguous. Keep short — 5-15 terms max. -->

| Term | Meaning in this project |
|---|---|
| | |

## Ownership

| Area | Team / Person | Contact |
|---|---|---|
| | | |

## Key constraints

<!-- Non-negotiable constraints: compliance, SLAs, uptime targets, data residency -->

-
