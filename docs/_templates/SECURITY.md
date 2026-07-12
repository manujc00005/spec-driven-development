# Security

> Copy this template into your project as `docs/SECURITY.md` and fill it in.
> Claude Code reads this to understand the project's IAM model, secret management,
> and security boundaries before reviewing or implementing security-sensitive features.

## Authentication model

| Property | Value |
|---|---|
| Method | OAuth2 / OIDC / Keycloak / Form login / API key |
| Token type | JWT / Opaque / Session |
| Identity provider | Keycloak / Auth0 / Cognito / Custom |
| Issuer URI | (config property reference, not the actual URL) |
| Audience validation | yes / no |
| Token lifetime | (access / refresh) |

## Authorization model

| Property | Value |
|---|---|
| Role source | Keycloak realm roles / client roles / custom claim / DB |
| Role hierarchy | (if applicable) |
| Enforcement | `@PreAuthorize` / SecurityFilterChain / both |
| Multi-tenancy | Tenant isolation via: (schema / row-level / service) |

## Roles and permissions

| Role | Access level | Example endpoints |
|---|---|---|
| `ADMIN` | Full | All |
| `USER` | Own resources | `GET/PUT /api/v1/orders/{own}` |
| `SERVICE` | Service-to-service | Internal APIs |

## Secret management

| Secret type | Storage | Access method |
|---|---|---|
| DB credentials | HashiCorp Vault | Spring Cloud Vault |
| API keys (external) | Vault / K8s Secrets | Env vars |
| JWT signing key | Keycloak-managed | N/A (asymmetric, public key fetched) |
| Local dev secrets | `application-local.yml` (gitignored) | Direct |

## Sensitive data (PII)

| Data | Classification | Storage | Access control |
|---|---|---|---|
| Email | PII | Encrypted column / plain | Role-based |
| Payment info | PCI | Never stored / tokenized via PSP | N/A |

## Security boundaries

<!-- What is public, what requires auth, what requires specific roles -->

| Path pattern | Access |
|---|---|
| `/api/public/**` | Anonymous |
| `/api/v1/**` | Authenticated |
| `/api/admin/**` | ADMIN role |
| `/actuator/health` | Anonymous |
| `/actuator/**` | ADMIN or separate port |

## CORS policy

| Property | Value |
|---|---|
| Allowed origins | (list or config reference) |
| Credentials | true / false |
| Methods | GET, POST, PUT, DELETE |
| Headers | Authorization, Content-Type |

## Rate limiting

| Endpoint pattern | Limit | Window | Implementation |
|---|---|---|---|
| `/api/auth/login` | 5 req | per minute per IP | (Gateway / Spring filter / Resilience4j) |
| `/api/v1/**` | 100 req | per minute per user | |

## Security checklist (for reviews)

- [ ] No secrets in version control (check `application*.yml`, `.env`).
- [ ] All endpoints require authentication unless explicitly public.
- [ ] Role checks at service layer, not just controller (defense in depth).
- [ ] Actuator restricted in non-local profiles.
- [ ] CORS not wildcard in production.
- [ ] Input validation on all user-facing DTOs.
- [ ] SQL injection: parameterized queries only (JPA handles this unless native queries).
- [ ] Audit logging for admin actions.
