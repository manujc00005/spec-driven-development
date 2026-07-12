# Deployment

> Copy this template into your project as `docs/DEPLOYMENT.md` and fill it in.
> Claude Code reads this to understand how the application is built, packaged,
> deployed, and rolled back. Essential for /kubernetes-deployment-reviewer and
> /spec-implement when changes touch infrastructure or deployment configs.

## Build and packaging

| Property | Value |
|---|---|
| Build tool | Maven (`./mvnw`) |
| Artifact type | Executable JAR / Docker image |
| Java version | 17 / 21 |
| Base image | `eclipse-temurin:21-jre-alpine` |
| Registry | (container registry URL) |
| Image naming | `registry/team/service:git-sha` |

## Dockerfile

| Stage | Purpose |
|---|---|
| Build | Multi-stage: Maven build, extract layers |
| Runtime | JRE-only, non-root user, health endpoint |

Key settings:
- `JAVA_OPTS` configurable via env var
- Graceful shutdown enabled (`server.shutdown=graceful`)
- Actuator health at `/actuator/health`

## Environments

| Environment | Namespace/Cluster | URL | Purpose |
|---|---|---|---|
| Local | Docker Compose | `localhost:8080` | Development |
| Dev | `dev` namespace | (internal URL) | Integration testing |
| Staging | `staging` namespace | (internal URL) | Pre-prod validation |
| Production | `prod` namespace | (public URL) | Live traffic |

## Kubernetes resources

| Resource | File | Notes |
|---|---|---|
| Deployment | `k8s/deployment.yaml` or Helm `templates/deployment.yaml` | Replicas, resource limits, probes |
| Service | `k8s/service.yaml` | ClusterIP, port mapping |
| Ingress | `k8s/ingress.yaml` | TLS, path routing |
| ConfigMap | `k8s/configmap.yaml` | Non-secret config |
| Secret | External (Vault / Sealed Secrets) | Never in repo |
| HPA | `k8s/hpa.yaml` | Auto-scaling rules |

## Helm chart (if applicable)

| Property | Value |
|---|---|
| Chart location | `helm/service-name/` |
| Values per env | `values-dev.yaml`, `values-staging.yaml`, `values-prod.yaml` |
| Managed by | ArgoCD / Flux / manual `helm upgrade` |

## ArgoCD / GitOps (if applicable)

| Property | Value |
|---|---|
| App manifest | `argocd/application.yaml` |
| Sync policy | Automated with self-heal / Manual |
| Source repo | (infra repo or same repo) |
| Target revision | `main` / `HEAD` / tag |

## Health checks and probes

| Probe | Path | Delay | Period | Threshold |
|---|---|---|---|---|
| Liveness | `/actuator/health/liveness` | 30s | 10s | 3 failures |
| Readiness | `/actuator/health/readiness` | 10s | 5s | 3 failures |
| Startup | `/actuator/health` | 0s | 5s | 30 failures |

## Resource limits

| Resource | Request | Limit |
|---|---|---|
| CPU | 250m | 1000m |
| Memory | 512Mi | 1024Mi |

## Deployment strategy

| Property | Value |
|---|---|
| Strategy | RollingUpdate / Blue-Green / Canary |
| Max unavailable | 0 |
| Max surge | 1 |
| Canary weight (if applicable) | 10% → 50% → 100% |

## Database migrations in deploy

| Property | Value |
|---|---|
| Tool | Flyway / Liquibase |
| Execution | Init container / application startup / separate job |
| Rollback | Backward-compatible migrations only; never drop in same release |

## Rollback procedure

1. **ArgoCD**: Sync to previous healthy revision.
2. **Helm**: `helm rollback <release> <revision>`.
3. **kubectl**: `kubectl rollout undo deployment/<name>`.
4. **DB**: Migrations must be backward-compatible; no DDL rollback needed if forward-only pattern is followed.

## Secrets injection

| Method | Tool | When |
|---|---|---|
| At deploy time | Vault Agent Injector / External Secrets Operator | Pod start |
| At build time | Never (secrets never baked into images) | — |

## CI/CD pipeline overview

| Stage | Tool | Trigger |
|---|---|---|
| Build + Test | GitHub Actions / Jenkins / GitLab CI | Push to any branch |
| Docker build | CI pipeline | Push to `main` / tag |
| Deploy to dev | ArgoCD auto-sync | Image pushed |
| Deploy to staging | Manual approval / auto | After dev green |
| Deploy to prod | Manual approval | After staging sign-off |

## Deployment checklist (for reviews)

- [ ] Dockerfile uses multi-stage build, non-root user.
- [ ] Resource requests and limits defined for all containers.
- [ ] Health probes configured and tested.
- [ ] Graceful shutdown configured (`preStop` hook + `terminationGracePeriodSeconds`).
- [ ] Migrations are backward-compatible with previous application version.
- [ ] No secrets in ConfigMaps, env vars from Vault/Sealed Secrets only.
- [ ] HPA configured if service is latency-sensitive.
- [ ] Rollback tested or documented.
