---
name: java-performance-reviewer
description: Review Java/Spring code for JVM and Spring-specific performance issues — JPA N+1, connection pool sizing, thread pool starvation, blocking-in-reactive, caching misuse, and allocation hot paths. Extends performance-review.
triggers:
  - After `/performance-review` on Java/Spring projects
  - When data-heavy queries, thread pools, caches, or async processing change
  - When the user asks to "check performance" or "find N+1 queries"
  - Triggered automatically by `/review-all` on performance-sensitive features in Spring Boot projects
---

## SDD Contract

```yaml
category: domain-reviewer
inputs: [diff, performance-review-findings]
outputs: [jvm-performance-findings]
side_effects: none
writes_code: false
writes_specs: false
analysis_only: true
primary_agent: domain-reviewer
secondary_agents: []
profile_scope: [java-spring-backend]
provider_specific: false
```

# Java Performance Reviewer

## Purpose

Catch JVM and Spring-specific performance pitfalls that generic `performance-review` (algorithm/caching/
bundle-size focused) misses. This skill **extends** `performance-review` — run that first for general
complexity and caching analysis.

## Extends

- **Skill:** `performance-review`
- **Subagent:** `java-spring` (JPA, Spring context)

## What this skill checks (beyond performance-review)

### JPA / Hibernate N+1

- `@OneToMany` / `@ManyToOne` with `FetchType.EAGER` on collections (almost always wrong).
- Lazy-loaded collections accessed in a loop without `@EntityGraph` or `JOIN FETCH`.
- Repository methods returning entities with unfetched associations that will be accessed in the service layer.
- Missing `@BatchSize` or `@Fetch(FetchMode.SUBSELECT)` for known collection-access patterns.
- `findAll()` on tables with >10K rows without pagination.

### Connection pool (HikariCP)

- `maximumPoolSize` too low for the number of concurrent requests (thread starvation).
- `maximumPoolSize` too high (wasting DB connections, hitting DB max_connections).
- Missing `connectionTimeout` / `idleTimeout` tuning for the workload.
- Multiple `@Transactional` services called sequentially holding a connection each (pool exhaustion under load).
- Long-running transactions holding connections open during external HTTP calls.

### Thread pools and async

- `@Async` with default `SimpleAsyncTaskExecutor` (creates unbounded threads).
- Custom `ThreadPoolTaskExecutor` with unbounded queue (memory pressure under burst).
- Blocking calls (JDBC, HTTP synchronous) inside a reactive pipeline or virtual thread pool.
- `CompletableFuture` chains without proper exception handling (silent failures).
- Fork-join pool misuse for I/O-bound work.

### Caching

- `@Cacheable` on methods with side effects or non-deterministic results.
- Cache keys using mutable objects or objects without proper `equals`/`hashCode`.
- Missing `@CacheEvict` — data changes but cached response stays stale.
- Caching large objects (entities with associations) instead of DTOs.
- No TTL configured — cache grows unbounded.

### Query and data access

- Native queries without pagination on large tables.
- `SELECT *` via JPA when only 2-3 fields are needed (use projections/DTOs).
- Missing database indexes for frequently-filtered columns (check `@Column` + query patterns).
- `LIKE '%...%'` patterns that prevent index usage.
- Multiple sequential queries that could be a single JOIN.

### Allocation and GC pressure

- Creating large intermediate collections in stream pipelines (prefer lazy evaluation).
- String concatenation in loops instead of `StringBuilder` or `String.join`.
- Autoboxing in hot paths (int ↔ Integer in collections).
- Large objects allocated per-request that could be pooled or reused.

## Output format

```markdown
## Java Performance Review

**Verdict:** PASS | PASS WITH NOTES | FAIL

### Hot paths identified

| # | Category | Severity | File:Line | Finding | Estimated impact | Action |
|---|---|---|---|---|---|---|
| 1 | N+1 | High | `OrderService.java:67` | `order.getItems()` in loop without JOIN FETCH | O(n) queries per request | Add `@EntityGraph` or JOIN FETCH |

### Recommendations

- (Non-blocking perf improvements)

### Benchmarking suggestions

- (If applicable: what to measure before/after)
```

## What this skill does NOT do

- Does not review general algorithmic complexity (that's `performance-review`).
- Does not review frontend rendering or bundle size.
- Does not profile or run benchmarks — it identifies patterns statically.
- Does not modify code.
