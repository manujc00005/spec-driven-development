# Integration Contracts

> Template for `.sdd-workspace/INTEGRATION_CONTRACTS.md`. The shared surface between projects.
> See [`../WORKSPACE_SDD.md`](../WORKSPACE_SDD.md).

**Last updated:** `YYYY-MM-DD`

**The rule this file exists to enforce:** a contract changes **here first**, before any dependent
project implements against it. A silent contract change — one that lands in a producer's code
before it lands in this file — is forbidden by the workspace guardrails. Whichever side ships
first would otherwise define the contract by accident.

Every entry names an **owner** (the project that is authoritative) and its **consumers**. Where
either is unknown, say `Unknown - requires confirmation` rather than guessing.

## REST APIs

| Endpoint | Owner | Consumers | Request | Response | Versioning | Evidence |
|---|---|---|---|---|---|---|
| `POST /v1/leads` | `backend-api` | `widget`, `shared-sdk`, `frontend-admin` | `{email, name, consent}` | `201 {id}` | URI-versioned `/v1` | `backend-api/openapi.yaml:120` |
| `<method> <path>` | `<project>` | `<projects>` | `<shape>` | `<shape>` | `<scheme>` | `<file:line>` |

**Breaking-change policy:** `<what counts as breaking here — new required field, removed field,
narrowed enum, changed status code — and what the deprecation window is.>`

## Events

| Event | Owner (producer) | Consumers | Payload | Schema / registry | Delivery semantics | Evidence |
|---|---|---|---|---|---|---|
| `lead.created` | `backend-api` | `crm-platform` | `{id, email, consent, createdAt}` | `<registry or file>` | at-least-once | `<file:line>` |
| `<name>` | `<project>` | `<projects>` | `<shape>` | `<where defined>` | `<at-least-once / exactly-once effects>` | `<file:line>` |

**Compatibility rule:** `<forward/backward compatibility expectation — e.g. consumers must tolerate
unknown fields; removing a field requires a new event version.>`

## Webhooks

| Webhook | Direction | Owner | Endpoint | Auth / signature | Retry policy | Evidence |
|---|---|---|---|---|---|---|
| `<name>` | outbound / inbound | `<project>` | `<URL or config key>` | `<HMAC header, shared secret ref — never the secret itself>` | `<attempts, backoff>` | `<file:line>` |

> Never record a secret value here. Record the *name* of the config key and where it is set.

## Shared packages

| Package | Owner | Consumers | Version range in use | Published where | Breaking-change signal | Evidence |
|---|---|---|---|---|---|---|
| `@acme/sdk` | `shared-sdk` | `wordpress-plugin`, `widget` | `^2.4.0` | npm (public / private) | `<semver + changelog? contract test?>` | `wp-plugin/package.json:18` |
| `<name>` | `<project>` | `<projects>` | `<range>` | `<registry>` | `<signal>` | `<file:line>` |

## Environment variables

Cross-project configuration only — variables that couple two projects. Names and meanings, never
values.

| Variable | Set in | Read by | Meaning | Must match | Evidence |
|---|---|---|---|---|---|
| `API_BASE_URL` | `widget`, `frontend-admin` | both | Base URL of `backend-api` | `backend-api` public origin | `widget/.env.example:3` |
| `CRM_WEBHOOK_URL` | `backend-api` | `backend-api` | Destination for lead forwarding | `crm-platform` ingest URL | `backend-api/.env.example:7` |

## Auth boundaries

| Boundary | Mechanism | Token issuer | Audience / scope | Trust assumption | Evidence |
|---|---|---|---|---|---|
| `widget` → `backend-api` | Public write key | `backend-api` | `leads:create` | Key is public — endpoint must assume hostile input | `<file:line>` |
| `frontend-admin` → `backend-api` | OIDC bearer | `<issuer>` | `leads:read`, `leads:export` | Session-bound | `<file:line>` |

**Where is the trust boundary actually enforced?** `<name the enforcing project and file. If the
answer is "nowhere confirmed", say Unknown - requires confirmation — that is a finding.>`

## Data ownership

Which project is authoritative for which data. Everything else holds a copy.

| Data | System of record | Replicas / caches | Sync mechanism | Deletion propagation |
|---|---|---|---|---|
| Lead | `backend-api` | `crm-platform` (copy) | event `lead.created` | `Unknown - requires confirmation` — does erasure propagate? |
| `<entity>` | `<project>` | `<projects>` | `<mechanism>` | `<how deletes reach replicas>` |

> Deletion propagation is where privacy obligations usually break. An `Unknown` here is a real
> finding, not a formality.

## Unknowns

- `Unknown - requires confirmation` — `<contract believed to exist but undocumented>`
- `Inferred - requires confirmation` — `<contract inferred from a config key or name match>`
